from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILES = {
    "products": PROCESSED_DIR / "products.csv",
    "suppliers": PROCESSED_DIR / "suppliers.csv",
    "inventory": PROCESSED_DIR / "inventory_snapshots.csv",
    "sales_orders": PROCESSED_DIR / "sales_orders.csv",
    "sales_items": PROCESSED_DIR / "sales_order_items.csv",
    "purchase_orders": PROCESSED_DIR / "purchase_orders.csv",
    "forecasts": PROCESSED_DIR / "demand_forecasts.csv",
}

OUTPUT_FILES = {
    "products": PROCESSED_DIR / "products_features.csv",
    "inventory": PROCESSED_DIR / "inventory_features.csv",
    "sales": PROCESSED_DIR / "sales_features.csv",
    "suppliers": PROCESSED_DIR / "supplier_features.csv",
    "purchase_orders": PROCESSED_DIR / "purchase_order_features.csv",
    "forecasts": PROCESSED_DIR / "forecast_features.csv",
}


def check_files():
    missing = [str(path) for path in INPUT_FILES.values() if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Missing processed file(s):\n" + "\n".join(missing)
        )


def load_data():
    # loading the cleaned tables used for feature engineering
    products = pd.read_csv(
        INPUT_FILES["products"],
        parse_dates=["launch_date"],
    )

    suppliers = pd.read_csv(INPUT_FILES["suppliers"])

    sales_orders = pd.read_csv(
        INPUT_FILES["sales_orders"],
        parse_dates=[
            "order_date",
            "delivery_promised_date",
            "delivery_actual_date",
        ],
    )

    sales_items = pd.read_csv(INPUT_FILES["sales_items"])

    purchase_orders = pd.read_csv(
        INPUT_FILES["purchase_orders"],
        parse_dates=[
            "order_date",
            "expected_delivery_date",
            "actual_delivery_date",
        ],
    )

    forecasts = pd.read_csv(
        INPUT_FILES["forecasts"],
        parse_dates=["forecast_date"],
    )

    return (
        products,
        suppliers,
        sales_orders,
        sales_items,
        purchase_orders,
        forecasts,
    )


def build_sales_features(sales_orders, sales_items):
    order_columns = [
        "order_id",
        "order_date",
        "warehouse_id",
        "customer_region",
        "order_channel",
        "priority",
        "order_status",
    ]

    sales = sales_items.merge(
        sales_orders[order_columns],
        on="order_id",
        how="left",
        validate="many_to_one",
    )

    # calculating sales before discounts and returns
    sales["gross_sales"] = (
        sales["quantity"] * sales["unit_selling_price"]
    ).round(2)

    sold_ratio = np.where(
        sales["quantity"] > 0,
        (sales["quantity"] - sales["returned_quantity"]) / sales["quantity"],
        0,
    )

    cancelled = sales["order_status"].eq("Cancelled")

    # calculating revenue after discounts, returns and cancellations
    sales["net_sales"] = (
        sales["sales_amount"] * sold_ratio
    ).where(~cancelled, 0).round(2)

    sales["net_cost"] = (
        sales["cost_amount"] * sold_ratio
    ).where(~cancelled, 0).round(2)

    sales["gross_margin"] = (
        sales["net_sales"] - sales["net_cost"]
    ).round(2)

    sales["net_units_sold"] = (
        sales["quantity"] - sales["returned_quantity"]
    ).where(~cancelled, 0).astype("int64")

    # extracting calendar fields for trend analysis
    sales["order_month"] = sales["order_date"].dt.month.astype("int16")
    sales["order_week"] = (
        sales["order_date"].dt.isocalendar().week.astype("int16")
    )
    sales["order_year"] = sales["order_date"].dt.year.astype("int16")

    sales.to_csv(OUTPUT_FILES["sales"], index=False)

    return sales


def build_product_features(products, sales):
    product_sales = (
        sales.groupby("product_id", as_index=False)
        .agg(
            total_net_sales=("net_sales", "sum"),
            total_units_sold=("net_units_sold", "sum"),
        )
    )

    product_features = products.merge(
        product_sales,
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    product_features["total_net_sales"] = (
        product_features["total_net_sales"].fillna(0).round(2)
    )
    product_features["total_units_sold"] = (
        product_features["total_units_sold"].fillna(0).astype("int64")
    )

    # calculating ABC classes from cumulative net sales contribution
    abc = product_features[
        ["product_id", "total_net_sales"]
    ].sort_values("total_net_sales", ascending=False).copy()

    total_sales = abc["total_net_sales"].sum()

    if total_sales > 0:
        abc["cumulative_sales_pct"] = (
            abc["total_net_sales"].cumsum() / total_sales
        )

        abc["ABC_class"] = np.select(
            [
                abc["cumulative_sales_pct"] <= 0.80,
                abc["cumulative_sales_pct"] <= 0.95,
            ],
            ["A", "B"],
            default="C",
        )
    else:
        abc["ABC_class"] = "C"

    product_features = product_features.merge(
        abc[["product_id", "ABC_class"]],
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    positive_units = product_features.loc[
        product_features["total_units_sold"] > 0,
        "total_units_sold",
    ]

    if positive_units.empty:
        fast_cutoff = 0
        slow_cutoff = 0
    else:
        fast_cutoff = positive_units.quantile(0.75)
        slow_cutoff = positive_units.quantile(0.25)

    # identifying fast and slow moving products from sales volume
    product_features["fast_moving_flag"] = (
        product_features["total_units_sold"] >= fast_cutoff
    ).astype("int8")

    product_features["slow_moving_flag"] = (
        product_features["total_units_sold"] <= slow_cutoff
    ).astype("int8")

    category_cost_cutoff = (
        product_features.groupby("category")["unit_cost"]
        .transform(lambda values: values.quantile(0.75))
    )

    # identifying high-value products within each category
    product_features["high_value_flag"] = (
        product_features["unit_cost"] >= category_cost_cutoff
    ).astype("int8")

    product_features.to_csv(OUTPUT_FILES["products"], index=False)

    return product_features


def build_purchase_order_features(purchase_orders):
    po_features = purchase_orders.copy()

    delivered = po_features["actual_delivery_date"].notna()

    # identifying supplier deliveries that arrived after the expected date
    po_features["late_delivery_flag"] = (
        delivered
        & (
            po_features["actual_delivery_date"]
            > po_features["expected_delivery_date"]
        )
    ).astype("int8")

    po_features["delivery_delay_days"] = (
        po_features["actual_delivery_date"]
        - po_features["expected_delivery_date"]
    ).dt.days

    po_features["partial_delivery_flag"] = (
        po_features["received_units"].gt(0)
        & po_features["received_units"].lt(po_features["ordered_units"])
    ).astype("int8")

    po_features.to_csv(OUTPUT_FILES["purchase_orders"], index=False)

    return po_features


def build_supplier_features(suppliers, po_features):
    delivered_po = po_features[
        po_features["actual_delivery_date"].notna()
    ].copy()

    supplier_delivery = (
        delivered_po.groupby("supplier_id", as_index=False)
        .agg(
            completed_po_count=("purchase_order_id", "count"),
            late_po_count=("late_delivery_flag", "sum"),
            partial_po_count=("partial_delivery_flag", "sum"),
        )
    )

    supplier_delivery["actual_late_delivery_rate"] = (
        supplier_delivery["late_po_count"]
        / supplier_delivery["completed_po_count"]
    )

    supplier_delivery["partial_delivery_rate"] = (
        supplier_delivery["partial_po_count"]
        / supplier_delivery["completed_po_count"]
    )

    supplier_features = suppliers.merge(
        supplier_delivery,
        on="supplier_id",
        how="left",
        validate="one_to_one",
    )

    fill_zero = [
        "completed_po_count",
        "late_po_count",
        "partial_po_count",
        "actual_late_delivery_rate",
        "partial_delivery_rate",
    ]

    supplier_features[fill_zero] = supplier_features[fill_zero].fillna(0)

    supplier_features[
        ["completed_po_count", "late_po_count", "partial_po_count"]
    ] = supplier_features[
        ["completed_po_count", "late_po_count", "partial_po_count"]
    ].astype("int64")

    # flagging suppliers with a meaningful late-delivery pattern
    supplier_features["late_delivery_flag"] = (
        supplier_features["actual_late_delivery_rate"] > 0.20
    ).astype("int8")

    # flagging suppliers with weak quality or high defect rates
    supplier_features["quality_risk_flag"] = (
        supplier_features["quality_rating"].le(2)
        | supplier_features["defect_rate"].ge(0.05)
    ).astype("int8")

    reliability_risk = 100 - supplier_features["reliability_score"]

    on_time_risk = (
        (1 - supplier_features["on_time_delivery_rate"]) * 100
    ).clip(0, 100)

    defect_risk = (
        supplier_features["defect_rate"] / 0.08 * 100
    ).clip(0, 100)

    late_risk = (
        supplier_features["actual_late_delivery_rate"] * 100
    ).clip(0, 100)

    quality_risk = (
        (5 - supplier_features["quality_rating"]) / 4 * 100
    ).clip(0, 100)

    # combining reliability, delivery and quality into one risk score
    supplier_features["supplier_risk_score"] = (
        reliability_risk * 0.30
        + on_time_risk * 0.25
        + defect_risk * 0.20
        + late_risk * 0.15
        + quality_risk * 0.10
    ).clip(0, 100).round(2)

    supplier_features.to_csv(OUTPUT_FILES["suppliers"], index=False)

    return supplier_features


def build_forecast_features(forecasts):
    forecast_features = forecasts.copy()

    # calculating signed and absolute forecast errors
    forecast_features["forecast_error"] = (
        forecast_features["actual_demand_units"]
        - forecast_features["forecast_demand_units"]
    )

    absolute_error = forecast_features["forecast_error"].abs()
    actual = forecast_features["actual_demand_units"]

    forecast_features["mape"] = np.where(
        actual > 0,
        absolute_error / actual * 100,
        np.where(
            forecast_features["forecast_demand_units"].eq(0),
            0,
            np.nan,
        ),
    )

    # converting row-level MAPE into an easy-to-read accuracy percentage
    forecast_features["forecast_accuracy"] = (
        100 - forecast_features["mape"]
    ).clip(lower=0, upper=100)

    forecast_features["mape"] = forecast_features["mape"].round(2)
    forecast_features["forecast_accuracy"] = (
        forecast_features["forecast_accuracy"].round(2)
    )

    forecast_features.to_csv(OUTPUT_FILES["forecasts"], index=False)

    return forecast_features


def calculate_inventory_averages():
    group_parts = []

    # calculating average inventory value without loading the full file at once
    for chunk in pd.read_csv(
        INPUT_FILES["inventory"],
        usecols=["warehouse_id", "product_id", "inventory_value"],
        chunksize=250_000,
    ):
        grouped = (
            chunk.groupby(
                ["warehouse_id", "product_id"],
                as_index=False,
            )
            .agg(
                inventory_value_sum=("inventory_value", "sum"),
                snapshot_count=("inventory_value", "count"),
            )
        )

        group_parts.append(grouped)

    combined = pd.concat(group_parts, ignore_index=True)

    inventory_average = (
        combined.groupby(
            ["warehouse_id", "product_id"],
            as_index=False,
        )
        .agg(
            inventory_value_sum=("inventory_value_sum", "sum"),
            snapshot_count=("snapshot_count", "sum"),
        )
    )

    inventory_average["average_inventory_value"] = (
        inventory_average["inventory_value_sum"]
        / inventory_average["snapshot_count"]
    )

    return inventory_average[
        ["warehouse_id", "product_id", "average_inventory_value"]
    ]


def build_inventory_metrics(sales, products):
    sales_2026 = sales[
        sales["order_year"].eq(2026)
        & ~sales["order_status"].eq("Cancelled")
    ].copy()

    annual_demand = (
        sales_2026.groupby(
            ["warehouse_id", "product_id"],
            as_index=False,
        )
        .agg(
            annual_demand_units=("quantity", "sum"),
            annual_cogs=("net_cost", "sum"),
        )
    )

    launch_dates = products[["product_id", "launch_date"]].copy()
    launch_dates["launch_date"] = pd.to_datetime(
        launch_dates["launch_date"], errors="coerce"
    )

    start_2026 = pd.Timestamp("2026-01-01")
    end_2026 = pd.Timestamp("2026-12-31")

    launch_dates["active_start_2026"] = launch_dates["launch_date"].clip(
        lower=start_2026
    )
    launch_dates["active_days_2026"] = (
        end_2026 - launch_dates["active_start_2026"]
    ).dt.days.add(1).clip(lower=1)

    annual_demand = annual_demand.merge(
        launch_dates[["product_id", "active_days_2026"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    annual_demand["average_daily_demand"] = (
        annual_demand["annual_demand_units"]
        / annual_demand["active_days_2026"]
    )

    inventory_average = calculate_inventory_averages()

    metrics = inventory_average.merge(
        annual_demand,
        on=["warehouse_id", "product_id"],
        how="left",
        validate="one_to_one",
    )

    metrics[
        ["annual_demand_units", "annual_cogs", "average_daily_demand"]
    ] = metrics[
        ["annual_demand_units", "annual_cogs", "average_daily_demand"]
    ].fillna(0)

    metrics["inventory_turnover"] = np.where(
        metrics["average_inventory_value"] > 0,
        metrics["annual_cogs"] / metrics["average_inventory_value"],
        np.nan,
    )

    product_columns = products[
        ["product_id", "unit_cost", "standard_lead_time_days"]
    ]

    metrics = metrics.merge(
        product_columns,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    return metrics


def build_inventory_features(inventory_metrics):
    input_path = INPUT_FILES["inventory"]
    output_path = OUTPUT_FILES["inventory"]

    if output_path.exists():
        output_path.unlink()

    first_chunk = True
    total_rows = 0

    # processing inventory features in chunks to keep memory use low
    for chunk in pd.read_csv(
        input_path,
        parse_dates=["snapshot_date"],
        chunksize=250_000,
    ):
        chunk = chunk.merge(
            inventory_metrics,
            on=["warehouse_id", "product_id"],
            how="left",
            validate="many_to_one",
        )

        # recalculating inventory value from cleaned stock and product cost
        chunk["inventory_value"] = (
            chunk["ending_inventory_units"] * chunk["unit_cost"]
        ).round(2)

        chunk["days_of_inventory"] = np.where(
            chunk["average_daily_demand"] > 0,
            chunk["ending_inventory_units"]
            / chunk["average_daily_demand"],
            np.nan,
        )

        chunk["inventory_turnover"] = (
            chunk["inventory_turnover"].round(3)
        )
        chunk["days_of_inventory"] = (
            chunk["days_of_inventory"].round(2)
        )
        chunk["average_daily_demand"] = (
            chunk["average_daily_demand"].round(3)
        )

        # recalculating the stockout flag from ending inventory
        chunk["stockout_flag"] = (
            chunk["ending_inventory_units"].eq(0)
        ).astype("int8")

        # separating stocked items with no recorded demand
        chunk["no_demand_stock_flag"] = (
            chunk["ending_inventory_units"].gt(0)
            & chunk["average_daily_demand"].eq(0)
        ).astype("int8")

        # flagging stock that exceeds about six months of demand
        chunk["overstock_flag"] = (
            chunk["ending_inventory_units"].gt(0)
            & chunk["average_daily_demand"].gt(0)
            & chunk["days_of_inventory"].gt(180)
        ).astype("int8")

        lead_time_demand = (
            chunk["average_daily_demand"]
            * chunk["standard_lead_time_days"]
        )

        # flagging stock below expected demand during supplier lead time
        chunk["low_stock_flag"] = (
            chunk["stockout_flag"].eq(0)
            & chunk["average_daily_demand"].gt(0)
            & chunk["ending_inventory_units"].le(lead_time_demand)
        ).astype("int8")

        chunk.drop(
            columns=[
                "unit_cost",
                "standard_lead_time_days",
                "average_inventory_value",
            ],
            inplace=True,
        )

        chunk.to_csv(
            output_path,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )

        total_rows += len(chunk)
        first_chunk = False

    return total_rows


def main():
    check_files()

    (
        products,
        suppliers,
        sales_orders,
        sales_items,
        purchase_orders,
        forecasts,
    ) = load_data()

    print("FEATURE ENGINEERING")
    print("-" * 52)

    sales = build_sales_features(sales_orders, sales_items)
    print(f"{'sales_features.csv':<32}{len(sales):>12,} rows")

    product_features = build_product_features(products, sales)
    print(
        f"{'products_features.csv':<32}"
        f"{len(product_features):>12,} rows"
    )

    po_features = build_purchase_order_features(purchase_orders)
    print(
        f"{'purchase_order_features.csv':<32}"
        f"{len(po_features):>12,} rows"
    )

    supplier_features = build_supplier_features(
        suppliers,
        po_features,
    )
    print(
        f"{'supplier_features.csv':<32}"
        f"{len(supplier_features):>12,} rows"
    )

    forecast_features = build_forecast_features(forecasts)
    print(
        f"{'forecast_features.csv':<32}"
        f"{len(forecast_features):>12,} rows"
    )

    inventory_metrics = build_inventory_metrics(sales, products)
    inventory_rows = build_inventory_features(inventory_metrics)
    print(
        f"{'inventory_features.csv':<32}"
        f"{inventory_rows:>12,} rows"
    )

    print("-" * 52)
    print(f"Feature files saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
