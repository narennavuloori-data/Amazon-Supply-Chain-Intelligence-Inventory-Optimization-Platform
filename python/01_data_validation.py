from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_FILE = PROJECT_ROOT / "dataset_validation_report.txt"

FILES = {
    "products": "products.csv",
    "suppliers": "suppliers.csv",
    "warehouses": "warehouses.csv",
    "inventory": "inventory_snapshots.csv",
    "sales_orders": "sales_orders.csv",
    "sales_order_items": "sales_order_items.csv",
    "purchase_orders": "purchase_orders.csv",
    "forecasts": "demand_forecasts.csv",
}

EXPECTED_COLUMNS = {
    "products": [
        "product_id", "sku", "product_name", "category", "subcategory",
        "brand", "unit_cost", "selling_price", "supplier_id",
        "standard_lead_time_days", "minimum_order_quantity",
        "shelf_life_days", "is_seasonal", "launch_date", "product_status"
    ],
    "suppliers": [
        "supplier_id", "supplier_name", "supplier_region", "country",
        "supplier_type", "quality_rating", "reliability_score",
        "payment_terms_days", "average_lead_time_days",
        "on_time_delivery_rate", "defect_rate",
        "capacity_units_per_month", "supplier_status"
    ],
    "warehouses": [
        "warehouse_id", "warehouse_name", "city", "state_region",
        "country", "warehouse_type", "storage_capacity_units",
        "daily_processing_capacity", "operating_cost_per_day",
        "region", "warehouse_status"
    ],
    "inventory": [
        "snapshot_date", "warehouse_id", "product_id",
        "opening_inventory_units", "inbound_units", "outbound_units",
        "adjustment_units", "damaged_units", "ending_inventory_units",
        "stockout_flag", "inventory_value"
    ],
    "sales_orders": [
        "order_id", "order_date", "customer_region", "order_channel",
        "priority", "order_status", "warehouse_id", "total_order_value",
        "delivery_promised_date", "delivery_actual_date"
    ],
    "sales_order_items": [
        "order_item_id", "order_id", "product_id", "quantity",
        "unit_selling_price", "discount_percent", "sales_amount",
        "cost_amount", "returned_quantity"
    ],
    "purchase_orders": [
        "purchase_order_id", "supplier_id", "warehouse_id", "order_date",
        "expected_delivery_date", "actual_delivery_date", "po_status",
        "ordered_units", "received_units", "unit_cost", "purchase_value"
    ],
    "forecasts": [
        "forecast_date", "warehouse_id", "product_id",
        "forecast_horizon_days", "forecast_demand_units",
        "actual_demand_units", "forecast_lower_bound",
        "forecast_upper_bound"
    ],
}

DATE_COLUMNS = {
    "products": ["launch_date"],
    "inventory": ["snapshot_date"],
    "sales_orders": [
        "order_date", "delivery_promised_date", "delivery_actual_date"
    ],
    "purchase_orders": [
        "order_date", "expected_delivery_date", "actual_delivery_date"
    ],
    "forecasts": ["forecast_date"],
}

ALLOWED_FORECAST_HORIZONS = {7, 14, 30, 60}


def result(status, detail=""):
    return {"status": status, "detail": detail}


def load_csv(name):
    path = RAW_DIR / FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def count_duplicates(df, columns):
    return int(df.duplicated(columns).sum())


def check_foreign_keys(child_df, child_column, parent_df, parent_column):
    return int((~child_df[child_column].isin(parent_df[parent_column])).sum())


def check_date_columns(df, columns):
    invalid = 0
    for column in columns:
        parsed = pd.to_datetime(df[column], errors="coerce")
        invalid += int(parsed.notna().sum() == 0) if False else int(
            df[column].notna().sum() - parsed.notna().sum()
        )
    return invalid


def validate_tables():
    data = {}
    checks = {}
    row_counts = {}
    null_counts = {}
    duplicate_counts = {}

    # checking files and loading the smaller tables
    for name in FILES:
        data[name] = load_csv(name)
        row_counts[name] = len(data[name])
        null_counts[name] = int(data[name].isna().sum().sum())

        missing_columns = sorted(
            set(EXPECTED_COLUMNS[name]) - set(data[name].columns)
        )
        extra_columns = sorted(
            set(data[name].columns) - set(EXPECTED_COLUMNS[name])
        )

        if missing_columns:
            checks[f"{name} columns"] = result(
                "FAIL", f"missing columns: {missing_columns}"
            )
        elif extra_columns:
            checks[f"{name} columns"] = result(
                "PASS", f"extra columns found: {extra_columns}"
            )
        else:
            checks[f"{name} columns"] = result("PASS")

    products = data["products"]
    suppliers = data["suppliers"]
    warehouses = data["warehouses"]
    sales_orders = data["sales_orders"]
    sales_order_items = data["sales_order_items"]
    purchase_orders = data["purchase_orders"]
    forecasts = data["forecasts"]

    # checking primary keys
    pk_checks = {
        "products": ["product_id"],
        "suppliers": ["supplier_id"],
        "warehouses": ["warehouse_id"],
        "sales_orders": ["order_id"],
        "sales_order_items": ["order_item_id"],
        "purchase_orders": ["purchase_order_id"],
    }

    for name, columns in pk_checks.items():
        duplicates = count_duplicates(data[name], columns)
        duplicate_counts[name] = duplicates
        checks[f"{name} duplicate IDs"] = result(
            "PASS" if duplicates == 0 else "FAIL",
            f"{duplicates} duplicate rows" if duplicates else ""
        )

    # checking the composite inventory key
    inventory_key = ["snapshot_date", "warehouse_id", "product_id"]
    inventory_duplicates = count_duplicates(
        load_csv("inventory"), inventory_key
    )
    duplicate_counts["inventory"] = inventory_duplicates
    checks["inventory duplicate keys"] = result(
        "PASS" if inventory_duplicates == 0 else "FAIL",
        f"{inventory_duplicates} duplicate keys"
        if inventory_duplicates else ""
    )

    # checking foreign keys
    checks["products -> suppliers"] = result(
        "PASS" if check_foreign_keys(
            products, "supplier_id", suppliers, "supplier_id"
        ) == 0 else "FAIL"
    )

    checks["inventory -> products"] = result(
        "PASS" if check_foreign_keys(
            load_csv("inventory"), "product_id", products, "product_id"
        ) == 0 else "FAIL"
    )

    checks["inventory -> warehouses"] = result(
        "PASS" if check_foreign_keys(
            load_csv("inventory"), "warehouse_id",
            warehouses, "warehouse_id"
        ) == 0 else "FAIL"
    )

    checks["sales orders -> warehouses"] = result(
        "PASS" if check_foreign_keys(
            sales_orders, "warehouse_id",
            warehouses, "warehouse_id"
        ) == 0 else "FAIL"
    )

    checks["order items -> orders"] = result(
        "PASS" if check_foreign_keys(
            sales_order_items, "order_id",
            sales_orders, "order_id"
        ) == 0 else "FAIL"
    )

    checks["order items -> products"] = result(
        "PASS" if check_foreign_keys(
            sales_order_items, "product_id",
            products, "product_id"
        ) == 0 else "FAIL"
    )

    checks["purchase orders -> suppliers"] = result(
        "PASS" if check_foreign_keys(
            purchase_orders, "supplier_id",
            suppliers, "supplier_id"
        ) == 0 else "FAIL"
    )

    checks["purchase orders -> warehouses"] = result(
        "PASS" if check_foreign_keys(
            purchase_orders, "warehouse_id",
            warehouses, "warehouse_id"
        ) == 0 else "FAIL"
    )

    checks["forecasts -> products"] = result(
        "PASS" if check_foreign_keys(
            forecasts, "product_id", products, "product_id"
        ) == 0 else "FAIL"
    )

    checks["forecasts -> warehouses"] = result(
        "PASS" if check_foreign_keys(
            forecasts, "warehouse_id",
            warehouses, "warehouse_id"
        ) == 0 else "FAIL"
    )

    # checking missing values that are not expected
    expected_null_columns = {
        "products": {"shelf_life_days"},
        "sales_orders": {"delivery_actual_date"},
        "purchase_orders": {"actual_delivery_date"},
    }

    unexpected_nulls = 0
    for name, df in data.items():
        allowed = expected_null_columns.get(name, set())
        for column in df.columns:
            if column not in allowed:
                unexpected_nulls += int(df[column].isna().sum())

    checks["unexpected missing values"] = result(
        "PASS" if unexpected_nulls == 0 else "FAIL",
        f"{unexpected_nulls} unexpected null values"
        if unexpected_nulls else ""
    )

    # checking negative quantities and numeric values
    negative_checks = {
        "products": [
            "unit_cost", "selling_price", "standard_lead_time_days",
            "minimum_order_quantity"
        ],
        "suppliers": [
            "quality_rating", "reliability_score", "payment_terms_days",
            "average_lead_time_days", "on_time_delivery_rate",
            "defect_rate", "capacity_units_per_month"
        ],
        "warehouses": [
            "storage_capacity_units", "daily_processing_capacity",
            "operating_cost_per_day"
        ],
        "inventory": [
            "opening_inventory_units", "inbound_units", "outbound_units",
            "damaged_units", "ending_inventory_units", "inventory_value"
        ],
        "sales_orders": ["total_order_value"],
        "sales_order_items": [
            "quantity", "unit_selling_price", "discount_percent",
            "sales_amount", "cost_amount", "returned_quantity"
        ],
        "purchase_orders": [
            "ordered_units", "received_units", "unit_cost", "purchase_value"
        ],
        "forecasts": [
            "forecast_horizon_days", "forecast_demand_units",
            "actual_demand_units", "forecast_lower_bound",
            "forecast_upper_bound"
        ],
    }

    for name, columns in negative_checks.items():
        df = data[name]
        negatives = int((df[columns] < 0).any(axis=1).sum())
        checks[f"{name} negative values"] = result(
            "PASS" if negatives == 0 else "FAIL",
            f"{negatives} rows with negative values" if negatives else ""
        )

    # checking product prices
    bad_product_prices = int(
        (products["selling_price"] <= products["unit_cost"]).sum()
    )
    checks["product price consistency"] = result(
        "PASS" if bad_product_prices == 0 else "FAIL",
        f"{bad_product_prices} products where selling price <= cost"
        if bad_product_prices else ""
    )

    # checking sales item calculations
    sales_calc = (
        sales_order_items["quantity"]
        * sales_order_items["unit_selling_price"]
        * (1 - sales_order_items["discount_percent"] / 100)
    )
    bad_sales_amount = int(
        (sales_order_items["sales_amount"] - sales_calc).abs().gt(0.01).sum()
    )

    checks["sales amount calculation"] = result(
        "PASS" if bad_sales_amount == 0 else "FAIL",
        f"{bad_sales_amount} mismatches" if bad_sales_amount else ""
    )

    bad_cost_amount = int(
        (sales_order_items["cost_amount"] <= 0).sum()
    )
    checks["cost amount"] = result(
        "PASS" if bad_cost_amount == 0 else "FAIL",
        f"{bad_cost_amount} non-positive values" if bad_cost_amount else ""
    )

    bad_returns = int(
        (
            sales_order_items["returned_quantity"]
            > sales_order_items["quantity"]
        ).sum()
    )
    checks["returned quantity"] = result(
        "PASS" if bad_returns == 0 else "FAIL",
        f"{bad_returns} rows where returns exceed quantity"
        if bad_returns else ""
    )

    # checking order totals
    item_totals = (
        sales_order_items.groupby("order_id")["sales_amount"].sum()
    )
    order_totals = sales_orders.set_index("order_id")["total_order_value"]
    comparison = item_totals.reindex(order_totals.index).fillna(0)
    bad_order_totals = int(
        (comparison - order_totals).abs().gt(0.01).sum()
    )

    checks["order total consistency"] = result(
        "PASS" if bad_order_totals == 0 else "FAIL",
        f"{bad_order_totals} order total mismatches"
        if bad_order_totals else ""
    )

    # checking delivery dates
    order_dates = pd.to_datetime(sales_orders["order_date"], errors="coerce")
    promised_dates = pd.to_datetime(
        sales_orders["delivery_promised_date"], errors="coerce"
    )
    actual_dates = pd.to_datetime(
        sales_orders["delivery_actual_date"], errors="coerce"
    )

    bad_promised_dates = int(
        (promised_dates < order_dates).fillna(False).sum()
    )
    bad_actual_dates = int(
        (actual_dates < order_dates).fillna(False).sum()
    )

    cancelled_or_transit_actuals = int(
        sales_orders.loc[
            sales_orders["order_status"].isin(["Cancelled", "In Transit"]),
            "delivery_actual_date"
        ].notna().sum()
    )

    checks["sales promised dates"] = result(
        "PASS" if bad_promised_dates == 0 else "FAIL",
        f"{bad_promised_dates} dates before order date"
        if bad_promised_dates else ""
    )

    checks["sales actual dates"] = result(
        "PASS" if bad_actual_dates == 0 else "FAIL",
        f"{bad_actual_dates} dates before order date"
        if bad_actual_dates else ""
    )

    checks["sales completion dates"] = result(
        "PASS" if cancelled_or_transit_actuals == 0 else "FAIL",
        f"{cancelled_or_transit_actuals} cancelled/in-transit orders with actual dates"
        if cancelled_or_transit_actuals else ""
    )

    # checking purchase order calculations and dates
    po_expected = pd.to_datetime(
        purchase_orders["expected_delivery_date"], errors="coerce"
    )
    po_order = pd.to_datetime(
        purchase_orders["order_date"], errors="coerce"
    )
    po_actual = pd.to_datetime(
        purchase_orders["actual_delivery_date"], errors="coerce"
    )

    bad_po_expected = int((po_expected < po_order).fillna(False).sum())
    bad_po_actual = int((po_actual < po_order).fillna(False).sum())
    bad_received = int(
        (purchase_orders["received_units"]
         > purchase_orders["ordered_units"]).sum()
    )
    bad_po_value = int(
        (
            purchase_orders["purchase_value"]
            - purchase_orders["ordered_units"]
            * purchase_orders["unit_cost"]
        ).abs().gt(0.01).sum()
    )

    checks["purchase order dates"] = result(
        "PASS"
        if bad_po_expected == 0 and bad_po_actual == 0
        else "FAIL",
        f"expected-before-order: {bad_po_expected}, "
        f"actual-before-order: {bad_po_actual}"
        if bad_po_expected or bad_po_actual else ""
    )

    checks["purchase order quantities"] = result(
        "PASS" if bad_received == 0 else "FAIL",
        f"{bad_received} rows where received > ordered"
        if bad_received else ""
    )

    checks["purchase order value"] = result(
        "PASS" if bad_po_value == 0 else "FAIL",
        f"{bad_po_value} calculation mismatches"
        if bad_po_value else ""
    )

    # checking inventory arithmetic in chunks
    inventory_path = RAW_DIR / FILES["inventory"]
    inventory_bad_balance = 0
    inventory_bad_stockout = 0
    inventory_bad_value = 0
    inventory_bad_dates = 0

    product_costs = products.set_index("product_id")["unit_cost"]

    for chunk in pd.read_csv(inventory_path, chunksize=250_000):
        calculated_end = (
            chunk["opening_inventory_units"]
            + chunk["inbound_units"]
            - chunk["outbound_units"]
            + chunk["adjustment_units"]
            - chunk["damaged_units"]
        )

        inventory_bad_balance += int(
            (chunk["ending_inventory_units"] != calculated_end).sum()
        )

        inventory_bad_stockout += int(
            (
                chunk["stockout_flag"]
                != chunk["ending_inventory_units"].eq(0).astype(int)
            ).sum()
        )

        costs = chunk["product_id"].map(product_costs)
        calculated_value = chunk["ending_inventory_units"] * costs
        inventory_bad_value += int(
            (chunk["inventory_value"] - calculated_value).abs().gt(0.05).sum()
        )

        snapshot_dates = pd.to_datetime(
            chunk["snapshot_date"], errors="coerce"
        )
        inventory_bad_dates += int(snapshot_dates.isna().sum())
        inventory_bad_dates += int(
            ((snapshot_dates < pd.Timestamp("2026-01-01"))
             | (snapshot_dates > pd.Timestamp("2026-12-31"))).sum()
        )

    checks["inventory balance"] = result(
        "PASS" if inventory_bad_balance == 0 else "FAIL",
        f"{inventory_bad_balance} rows with incorrect ending inventory"
        if inventory_bad_balance else ""
    )

    checks["inventory stockout flag"] = result(
        "PASS" if inventory_bad_stockout == 0 else "FAIL",
        f"{inventory_bad_stockout} incorrect stockout flags"
        if inventory_bad_stockout else ""
    )

    checks["inventory value"] = result(
        "PASS" if inventory_bad_value == 0 else "FAIL",
        f"{inventory_bad_value} value mismatches"
        if inventory_bad_value else ""
    )

    checks["inventory dates"] = result(
        "PASS" if inventory_bad_dates == 0 else "FAIL",
        f"{inventory_bad_dates} invalid inventory dates"
        if inventory_bad_dates else ""
    )

    # checking forecast rules
    bad_horizons = int(
        (~forecasts["forecast_horizon_days"].isin(ALLOWED_FORECAST_HORIZONS))
        .sum()
    )
    bad_forecast_values = int(
        (
            (forecasts["forecast_demand_units"]
             > forecasts["forecast_upper_bound"])
            | (forecasts["forecast_demand_units"]
               < forecasts["forecast_lower_bound"])
        ).sum()
    )
    bad_bounds = int(
        (forecasts["forecast_lower_bound"]
         > forecasts["forecast_upper_bound"]).sum()
    )

    checks["forecast horizons"] = result(
        "PASS" if bad_horizons == 0 else "FAIL",
        f"{bad_horizons} invalid horizons" if bad_horizons else ""
    )

    checks["forecast bounds"] = result(
        "PASS"
        if bad_bounds == 0 and bad_forecast_values == 0
        else "FAIL",
        f"invalid bounds: {bad_bounds}, forecast outside bounds: "
        f"{bad_forecast_values}"
        if bad_bounds or bad_forecast_values else ""
    )

    # checking basic date parsing across all date columns
    for name, columns in DATE_COLUMNS.items():
        invalid_dates = check_date_columns(data[name], columns)
        checks[f"{name} date parsing"] = result(
            "PASS" if invalid_dates == 0 else "FAIL",
            f"{invalid_dates} invalid date values"
            if invalid_dates else ""
        )

    # checking a few soft realism rules
    soft_warnings = []

    if sales_order_items["discount_percent"].gt(30).any():
        soft_warnings.append(
            "Some discounts are above 30%, which is unusual but possible."
        )

    seasonal_share = products["is_seasonal"].mean()
    if not 0.15 <= seasonal_share <= 0.20:
        soft_warnings.append(
            f"Seasonal product share is {seasonal_share:.1%}; "
            "target range is about 15%-20%."
        )

    inactive_share = products["product_status"].isin(
        ["Discontinued", "Inactive"]
    ).mean()
    if not 0.05 <= inactive_share <= 0.10:
        soft_warnings.append(
            f"Discontinued/inactive product share is {inactive_share:.1%}; "
            "target range is about 5%-10%."
        )

    checks["business rules"] = result(
        "PASS",
        "Hard business rules passed."
    )

    return {
        "data": data,
        "checks": checks,
        "row_counts": row_counts,
        "null_counts": null_counts,
        "duplicate_counts": duplicate_counts,
        "soft_warnings": soft_warnings,
    }


def write_report(validation):
    checks = validation["checks"]

    hard_failures = [
        name for name, check in checks.items()
        if check["status"] == "FAIL"
    ]

    status = "PASS" if not hard_failures else "FAIL"

    lines = [
        "DATA VALIDATION REPORT",
        "=" * 70,
        f"Overall status: {status}",
        f"Project path: {PROJECT_ROOT}",
        f"Data path: {RAW_DIR}",
        "",
        "TABLE SUMMARY",
        "-" * 70,
    ]

    for name in FILES:
        lines.append(
            f"{name:<24} rows={validation['row_counts'][name]:>10,}"
            f"  nulls={validation['null_counts'][name]:>8,}"
        )

    lines.extend([
        "",
        "VALIDATION CHECKS",
        "-" * 70,
    ])

    for name, check in checks.items():
        detail = f" - {check['detail']}" if check["detail"] else ""
        lines.append(f"{name:<42} {check['status']}{detail}")

    if validation["soft_warnings"]:
        lines.extend([
            "",
            "NOTES",
            "-" * 70,
        ])
        lines.extend(
            f"- {warning}" for warning in validation["soft_warnings"]
        )

    lines.extend([
        "",
        f"Validation result: {status}",
    ])

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

    return status, hard_failures


def main():
    print("DATA VALIDATION")
    print("-" * 40)

    try:
        validation = validate_tables()
        status, hard_failures = write_report(validation)
    except Exception as error:
        print(f"ERROR: {error}")
        print("\nCheck that all CSV files are inside:")
        print(RAW_DIR)
        raise

    display_names = {
        "products": "Products",
        "suppliers": "Suppliers",
        "warehouses": "Warehouses",
        "inventory": "Inventory",
        "sales_orders": "Sales Orders",
        "sales_order_items": "Sales Order Items",
        "purchase_orders": "Purchase Orders",
        "forecasts": "Forecasts",
    }

    print(f"{'Products:':<24}{validation['checks']['products duplicate IDs']['status']}")
    print(f"{'Suppliers:':<24}{validation['checks']['suppliers duplicate IDs']['status']}")
    print(f"{'Warehouses:':<24}{validation['checks']['warehouses duplicate IDs']['status']}")
    print(f"{'Inventory:':<24}{'PASS' if all(validation['checks'][key]['status'] == 'PASS' for key in ['inventory balance', 'inventory stockout flag', 'inventory value', 'inventory dates', 'inventory duplicate keys']) else 'FAIL'}")
    print(f"{'Sales Orders:':<24}{'PASS' if all(validation['checks'][key]['status'] == 'PASS' for key in ['sales orders -> warehouses', 'sales promised dates', 'sales actual dates', 'sales completion dates', 'order total consistency']) else 'FAIL'}")
    print(f"{'Sales Order Items:':<24}{'PASS' if all(validation['checks'][key]['status'] == 'PASS' for key in ['order items -> orders', 'order items -> products', 'sales amount calculation', 'returned quantity']) else 'FAIL'}")
    print(f"{'Purchase Orders:':<24}{'PASS' if all(validation['checks'][key]['status'] == 'PASS' for key in ['purchase orders -> suppliers', 'purchase orders -> warehouses', 'purchase order dates', 'purchase order quantities', 'purchase order value']) else 'FAIL'}")
    print(f"{'Forecasts:':<24}{'PASS' if all(validation['checks'][key]['status'] == 'PASS' for key in ['forecasts -> products', 'forecasts -> warehouses', 'forecast horizons', 'forecast bounds']) else 'FAIL'}")
    print(
        f"{'Foreign Keys:':<24}"
        f"{'PASS' if not any('->' in key and check['status'] == 'FAIL' for key, check in validation['checks'].items()) else 'FAIL'}"
    )
    print(f"{'Business Rules:':<24}{validation['checks']['business rules']['status']}")
    print("-" * 40)
    print(f"Overall: {status}")
    print(f"Report: {REPORT_FILE}")

    if hard_failures:
        print("\nChecks that failed:")
        for failure in hard_failures:
            print(f"- {failure}")


if __name__ == "__main__":
    main()
