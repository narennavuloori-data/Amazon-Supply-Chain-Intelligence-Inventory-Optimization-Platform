from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INVENTORY_FILE = PROCESSED_DIR / "inventory_features.csv"
PRODUCTS_FILE = PROCESSED_DIR / "products_features.csv"
FORECAST_FILE = PROCESSED_DIR / "demand_forecast_results.csv"

OUTPUT_FILE = PROCESSED_DIR / "inventory_optimization_results.csv"

SERVICE_LEVEL_Z = 1.65
ORDERING_COST = 50
HOLDING_RATE = 0.20


def check_files():
    missing = []

    if not INVENTORY_FILE.exists():
        missing.append(str(INVENTORY_FILE))

    if not PRODUCTS_FILE.exists():
        missing.append(str(PRODUCTS_FILE))

    if missing:
        raise FileNotFoundError(
            "Missing file(s):\n" + "\n".join(missing)
        )


def load_products():
    # loading product cost and lead time
    products = pd.read_csv(
        PRODUCTS_FILE,
        usecols=[
            "product_id",
            "product_name",
            "unit_cost",
            "standard_lead_time_days",
            "ABC_class",
        ],
    )

    return products


def load_latest_inventory():
    # finding the latest inventory date
    dates = pd.read_csv(
        INVENTORY_FILE,
        usecols=["snapshot_date"],
        parse_dates=["snapshot_date"],
    )

    latest_date = dates["snapshot_date"].max()

    parts = []

    # loading only the latest inventory snapshot
    for chunk in pd.read_csv(
        INVENTORY_FILE,
        parse_dates=["snapshot_date"],
        chunksize=250_000,
    ):
        current = chunk[
            chunk["snapshot_date"] == latest_date
        ].copy()

        if not current.empty:
            parts.append(current)

    inventory = pd.concat(parts, ignore_index=True)

    return inventory, latest_date


def calculate_demand_variability():
    parts = []

    # calculating weekly demand variation for each SKU and warehouse
    for chunk in pd.read_csv(
        INVENTORY_FILE,
        usecols=[
            "warehouse_id",
            "product_id",
            "outbound_units",
        ],
        chunksize=250_000,
    ):
        grouped = (
            chunk.groupby(
                ["warehouse_id", "product_id"],
                as_index=False,
            )
            .agg(
                demand_sum=("outbound_units", "sum"),
                demand_count=("outbound_units", "count"),
                demand_sum_sq=(
                    "outbound_units",
                    lambda x: (x.astype(float) ** 2).sum(),
                ),
            )
        )

        parts.append(grouped)

    combined = pd.concat(parts, ignore_index=True)

    totals = (
        combined.groupby(
            ["warehouse_id", "product_id"],
            as_index=False,
        )
        .agg(
            demand_sum=("demand_sum", "sum"),
            demand_count=("demand_count", "sum"),
            demand_sum_sq=("demand_sum_sq", "sum"),
        )
    )

    numerator = (
        totals["demand_sum_sq"]
        - (totals["demand_sum"] ** 2 / totals["demand_count"])
    )

    denominator = totals["demand_count"] - 1

    totals["demand_variability"] = np.sqrt(
        np.where(
            denominator > 0,
            numerator.clip(lower=0) / denominator,
            0,
        )
    )

    return totals[
        [
            "warehouse_id",
            "product_id",
            "demand_variability",
        ]
    ]


def load_forecast_demand():
    if not FORECAST_FILE.exists():
        return pd.DataFrame(
            columns=[
                "warehouse_id",
                "product_id",
                "forecast_daily_demand",
            ]
        )

    forecasts = pd.read_csv(FORECAST_FILE)

    forecast_demand = (
        forecasts.groupby(
            ["warehouse_id", "product_id"],
            as_index=False,
        )
        .agg(
            average_weekly_forecast=(
                "forecast_units",
                "mean",
            )
        )
    )

    forecast_demand["forecast_daily_demand"] = (
        forecast_demand["average_weekly_forecast"] / 7
    )

    return forecast_demand[
        [
            "warehouse_id",
            "product_id",
            "forecast_daily_demand",
        ]
    ]


def calculate_optimization(
    inventory,
    products,
    variability,
    forecast_demand,
):
    data = inventory.merge(
        products,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    data = data.merge(
        variability,
        on=["warehouse_id", "product_id"],
        how="left",
        validate="one_to_one",
    )

    data = data.merge(
        forecast_demand,
        on=["warehouse_id", "product_id"],
        how="left",
        validate="one_to_one",
    )

    data["demand_variability"] = (
        data["demand_variability"].fillna(0)
    )

    data["forecast_daily_demand"] = (
        data["forecast_daily_demand"].fillna(
            data["average_daily_demand"]
        )
    )

    # using the higher demand estimate for safer planning
    data["planning_daily_demand"] = data[
        [
            "average_daily_demand",
            "forecast_daily_demand",
        ]
    ].max(axis=1)

    # calculating safety stock from demand variation and lead time
    data["safety_stock"] = (
        SERVICE_LEVEL_Z
        * data["demand_variability"]
        * np.sqrt(
            data["standard_lead_time_days"] / 7
        )
    ).round(0)

    # calculating the inventory level that should trigger replenishment
    data["reorder_point"] = (
        data["planning_daily_demand"]
        * data["standard_lead_time_days"]
        + data["safety_stock"]
    ).round(0)

    annual_demand = (
        data["planning_daily_demand"] * 365
    )

    annual_holding_cost = (
        data["unit_cost"] * HOLDING_RATE
    )

    # calculating EOQ from annual demand, ordering cost and holding cost
    data["eoq"] = np.sqrt(
        (
            2
            * annual_demand
            * ORDERING_COST
        )
        / annual_holding_cost.replace(0, np.nan)
    ).fillna(0).round(0)

    data["current_inventory"] = (
        data["ending_inventory_units"]
    )

    data["current_inventory_value"] = (
        data["inventory_value"]
    )

    data["stockout_risk"] = np.select(
        [
            data["current_inventory"] == 0,
            data["current_inventory"]
            <= (
                data["planning_daily_demand"]
                * data["standard_lead_time_days"]
            ),
            data["current_inventory"]
            <= data["reorder_point"],
        ],
        [
            "Critical",
            "High",
            "Medium",
        ],
        default="Low",
    )

    data["overstock_risk"] = np.select(
        [
            (
                data["planning_daily_demand"] == 0
            )
            & (
                data["current_inventory"] > 0
            ),
            data["days_of_inventory"] > 120,
            data["days_of_inventory"] > 90,
        ],
        [
            "High",
            "High",
            "Medium",
        ],
        default="Low",
    )

    shortage = (
        data["reorder_point"]
        - data["current_inventory"]
    ).clip(lower=0)

    data["recommended_order_quantity"] = np.where(
        data["current_inventory"]
        <= data["reorder_point"],
        np.maximum(
            shortage,
            data["eoq"],
        ),
        0,
    ).round(0)

    return data


def find_transfer_options(data):
    transfer_lookup = (
        data[
            data["overstock_risk"].isin(["High", "Medium"])
        ]
        .sort_values(
            "current_inventory",
            ascending=False,
        )
        .drop_duplicates("product_id")
        .set_index("product_id")["warehouse_id"]
        .to_dict()
    )

    data["transfer_from_warehouse"] = (
        data["product_id"].map(transfer_lookup)
    )

    same_warehouse = (
        data["transfer_from_warehouse"]
        == data["warehouse_id"]
    )

    data.loc[
        same_warehouse,
        "transfer_from_warehouse",
    ] = pd.NA

    return data


def assign_actions(data):
    data["inventory_action"] = "HOLD"

    data.loc[
        data["overstock_risk"].eq("Medium"),
        "inventory_action",
    ] = "MONITOR"

    data.loc[
        data["overstock_risk"].eq("High"),
        "inventory_action",
    ] = "REDUCE INVENTORY"

    reorder_soon = (
        data["stockout_risk"].eq("Medium")
    )

    data.loc[
        reorder_soon,
        "inventory_action",
    ] = "REORDER SOON"

    reorder_now = (
        data["stockout_risk"].isin(["Critical", "High"])
    )

    data.loc[
        reorder_now,
        "inventory_action",
    ] = "REORDER NOW"

    transfer = (
        reorder_now
        & data["transfer_from_warehouse"].notna()
    )

    data.loc[
        transfer,
        "inventory_action",
    ] = "TRANSFER STOCK"

    return data


def prepare_output(data, latest_date):
    data["snapshot_date"] = latest_date

    output_columns = [
        "snapshot_date",
        "product_id",
        "product_name",
        "warehouse_id",
        "ABC_class",
        "current_inventory",
        "current_inventory_value",
        "average_daily_demand",
        "forecast_daily_demand",
        "planning_daily_demand",
        "demand_variability",
        "standard_lead_time_days",
        "safety_stock",
        "reorder_point",
        "eoq",
        "stockout_risk",
        "overstock_risk",
        "recommended_order_quantity",
        "transfer_from_warehouse",
        "inventory_action",
    ]

    output = data[output_columns].copy()

    numeric_columns = [
        "current_inventory_value",
        "average_daily_demand",
        "forecast_daily_demand",
        "planning_daily_demand",
        "demand_variability",
    ]

    output[numeric_columns] = (
        output[numeric_columns].round(2)
    )

    return output


def main():
    check_files()

    print("INVENTORY OPTIMIZATION")
    print("-" * 55)

    products = load_products()
    inventory, latest_date = load_latest_inventory()
    variability = calculate_demand_variability()
    forecast_demand = load_forecast_demand()

    data = calculate_optimization(
        inventory,
        products,
        variability,
        forecast_demand,
    )

    data = find_transfer_options(data)
    data = assign_actions(data)

    output = prepare_output(
        data,
        latest_date,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(f"Snapshot date: {latest_date.date()}")
    print(f"SKU/warehouse combinations: {len(output):,}")
    print()
    print(output["inventory_action"].value_counts().to_string())
    print()
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
