from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

FILES = [
    "products.csv",
    "suppliers.csv",
    "warehouses.csv",
    "inventory_snapshots.csv",
    "sales_orders.csv",
    "sales_order_items.csv",
    "purchase_orders.csv",
    "demand_forecasts.csv",
]

DATE_COLUMNS = {
    "products.csv": ["launch_date"],
    "inventory_snapshots.csv": ["snapshot_date"],
    "sales_orders.csv": [
        "order_date",
        "delivery_promised_date",
        "delivery_actual_date",
    ],
    "purchase_orders.csv": [
        "order_date",
        "expected_delivery_date",
        "actual_delivery_date",
    ],
    "demand_forecasts.csv": ["forecast_date"],
}

NUMERIC_COLUMNS = {
    "products.csv": [
        "unit_cost",
        "selling_price",
        "standard_lead_time_days",
        "minimum_order_quantity",
        "shelf_life_days",
    ],
    "suppliers.csv": [
        "quality_rating",
        "reliability_score",
        "payment_terms_days",
        "average_lead_time_days",
        "on_time_delivery_rate",
        "defect_rate",
        "capacity_units_per_month",
    ],
    "warehouses.csv": [
        "storage_capacity_units",
        "daily_processing_capacity",
        "operating_cost_per_day",
    ],
    "inventory_snapshots.csv": [
        "opening_inventory_units",
        "inbound_units",
        "outbound_units",
        "adjustment_units",
        "damaged_units",
        "ending_inventory_units",
        "stockout_flag",
        "inventory_value",
    ],
    "sales_orders.csv": ["total_order_value"],
    "sales_order_items.csv": [
        "quantity",
        "unit_selling_price",
        "discount_percent",
        "sales_amount",
        "cost_amount",
        "returned_quantity",
    ],
    "purchase_orders.csv": [
        "ordered_units",
        "received_units",
        "unit_cost",
        "purchase_value",
    ],
    "demand_forecasts.csv": [
        "forecast_horizon_days",
        "forecast_demand_units",
        "actual_demand_units",
        "forecast_lower_bound",
        "forecast_upper_bound",
    ],
}


def load_file(file_name):
    path = RAW_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def convert_data_types(df, file_name):
    for column in DATE_COLUMNS.get(file_name, []):
        df[column] = pd.to_datetime(df[column], errors="coerce")

    for column in NUMERIC_COLUMNS.get(file_name, []):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def remove_duplicate_rows(df):
    return df.drop_duplicates().copy()


def fill_missing_values(df, file_name):
    # keeping meaningful missing dates and shelf-life values
    if file_name == "sales_orders.csv":
        df["delivery_actual_date"] = df["delivery_actual_date"].where(
            df["delivery_actual_date"].notna(), pd.NaT
        )

    if file_name == "purchase_orders.csv":
        df["actual_delivery_date"] = df["actual_delivery_date"].where(
            df["actual_delivery_date"].notna(), pd.NaT
        )

    if file_name == "products.csv":
        df["shelf_life_days"] = df["shelf_life_days"].where(
            df["shelf_life_days"].notna(), pd.NA
        )

    return df


def remove_invalid_values(df, file_name):
    numeric_columns = NUMERIC_COLUMNS.get(file_name, [])

    if numeric_columns:
        valid_rows = ~(df[numeric_columns] < 0).any(axis=1)
        df = df.loc[valid_rows].copy()

    return df


def handle_outliers(df, file_name):
    # keeping valid business extremes instead of deleting them
    if "discount_percent" in df.columns:
        df["discount_percent"] = df["discount_percent"].clip(0, 35)

    if "quality_rating" in df.columns:
        df["quality_rating"] = df["quality_rating"].clip(1, 5)

    if "reliability_score" in df.columns:
        df["reliability_score"] = df["reliability_score"].clip(0, 100)

    if "on_time_delivery_rate" in df.columns:
        df["on_time_delivery_rate"] = df[
            "on_time_delivery_rate"
        ].clip(0, 1)

    if "defect_rate" in df.columns:
        df["defect_rate"] = df["defect_rate"].clip(0, 1)

    if "returned_quantity" in df.columns and "quantity" in df.columns:
        df["returned_quantity"] = df["returned_quantity"].clip(
            lower=0
        )
        df["returned_quantity"] = df[["returned_quantity", "quantity"]].min(
            axis=1
        )

    if "received_units" in df.columns and "ordered_units" in df.columns:
        df["received_units"] = df["received_units"].clip(lower=0)
        df["received_units"] = df[["received_units", "ordered_units"]].min(
            axis=1
        )

    return df


def fix_invalid_dates(df, file_name):
    if file_name == "sales_orders.csv":
        order_date = df["order_date"]

        df.loc[
            df["delivery_promised_date"] < order_date,
            "delivery_promised_date",
        ] = pd.NaT

        df.loc[
            df["delivery_actual_date"] < order_date,
            "delivery_actual_date",
        ] = pd.NaT

    if file_name == "purchase_orders.csv":
        order_date = df["order_date"]

        df.loc[
            df["expected_delivery_date"] < order_date,
            "expected_delivery_date",
        ] = pd.NaT

        df.loc[
            df["actual_delivery_date"] < order_date,
            "actual_delivery_date",
        ] = pd.NaT

    return df


def clean_regular_file(file_name):
    df = load_file(file_name)
    original_rows = len(df)

    df.columns = [column.strip() for column in df.columns]

    df = convert_data_types(df, file_name)
    df = remove_duplicate_rows(df)
    df = fill_missing_values(df, file_name)
    df = remove_invalid_values(df, file_name)
    df = handle_outliers(df, file_name)
    df = fix_invalid_dates(df, file_name)

    output_path = PROCESSED_DIR / file_name
    df.to_csv(output_path, index=False)

    return original_rows, len(df)


def clean_inventory():
    input_path = RAW_DIR / "inventory_snapshots.csv"
    output_path = PROCESSED_DIR / "inventory_snapshots.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Missing file: {input_path}")

    products = pd.read_csv(RAW_DIR / "products.csv", usecols=["product_id"])
    warehouses = pd.read_csv(
        RAW_DIR / "warehouses.csv", usecols=["warehouse_id"]
    )

    valid_products = set(products["product_id"])
    valid_warehouses = set(warehouses["warehouse_id"])

    if output_path.exists():
        output_path.unlink()

    first_chunk = True
    seen_keys = set()
    original_rows = 0
    written_rows = 0
    removed_rows = 0

    # processing the large inventory file in smaller pieces
    for chunk in pd.read_csv(input_path, chunksize=250_000):
        original_rows += len(chunk)

        chunk.columns = [column.strip() for column in chunk.columns]
        chunk["snapshot_date"] = pd.to_datetime(
            chunk["snapshot_date"], errors="coerce"
        )

        for column in NUMERIC_COLUMNS["inventory_snapshots.csv"]:
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce")

        before = len(chunk)
        chunk = chunk.drop_duplicates()
        removed_rows += before - len(chunk)

        invalid_dates = (
            chunk["snapshot_date"].isna()
            | chunk["snapshot_date"].lt(pd.Timestamp("2026-01-01"))
            | chunk["snapshot_date"].gt(pd.Timestamp("2026-12-31"))
        )

        invalid_keys = (
            ~chunk["product_id"].isin(valid_products)
            | ~chunk["warehouse_id"].isin(valid_warehouses)
        )

        negative_columns = [
            "opening_inventory_units",
            "inbound_units",
            "outbound_units",
            "damaged_units",
            "ending_inventory_units",
            "inventory_value",
        ]

        negative_values = (chunk[negative_columns] < 0).any(axis=1)

        invalid_balance = (
            chunk["ending_inventory_units"]
            != (
                chunk["opening_inventory_units"]
                + chunk["inbound_units"]
                - chunk["outbound_units"]
                + chunk["adjustment_units"]
                - chunk["damaged_units"]
            )
        )

        invalid_stockout = (
            chunk["stockout_flag"]
            != chunk["ending_inventory_units"].eq(0).astype(int)
        )

        bad_rows = (
            invalid_dates
            | invalid_keys
            | negative_values
            | invalid_balance
            | invalid_stockout
        )

        chunk = chunk.loc[~bad_rows].copy()
        removed_rows += int(bad_rows.sum())

        # removing keys that appear more than once across chunks
        key_columns = ["snapshot_date", "warehouse_id", "product_id"]
        keys = list(
            zip(
                chunk["snapshot_date"].astype(str),
                chunk["warehouse_id"],
                chunk["product_id"],
            )
        )

        keep_mask = []
        for key in keys:
            if key in seen_keys:
                keep_mask.append(False)
            else:
                seen_keys.add(key)
                keep_mask.append(True)

        chunk = chunk.loc[keep_mask].copy()

        if "inventory_value" in chunk.columns:
            chunk["inventory_value"] = chunk["inventory_value"].round(2)

        chunk.to_csv(
            output_path,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )

        written_rows += len(chunk)
        first_chunk = False

    return original_rows, written_rows, removed_rows


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("DATA CLEANING")
    print("-" * 40)

    regular_files = [
        file_name
        for file_name in FILES
        if file_name != "inventory_snapshots.csv"
    ]

    total_removed = 0

    for file_name in regular_files:
        original_rows, cleaned_rows = clean_regular_file(file_name)
        removed = original_rows - cleaned_rows
        total_removed += removed

        print(
            f"{file_name:<28}"
            f"{original_rows:>10,} -> {cleaned_rows:>10,}"
            f"   removed: {removed:,}"
        )

    original_rows, cleaned_rows, inventory_removed = clean_inventory()
    total_removed += inventory_removed

    print(
        f"{'inventory_snapshots.csv':<28}"
        f"{original_rows:>10,} -> {cleaned_rows:>10,}"
        f"   removed: {inventory_removed:,}"
    )

    print("-" * 40)
    print(f"Total rows removed: {total_removed:,}")
    print(f"Processed files saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
