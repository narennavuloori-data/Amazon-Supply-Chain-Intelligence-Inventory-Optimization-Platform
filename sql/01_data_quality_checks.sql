USE AmazonSupplyChainAnalytics;
GO

SELECT 'products_features' AS table_name, COUNT(*) AS row_count
FROM dbo.products_features
UNION ALL
SELECT 'supplier_features', COUNT(*) FROM dbo.supplier_features
UNION ALL
SELECT 'warehouses', COUNT(*) FROM dbo.warehouses
UNION ALL
SELECT 'inventory_features', COUNT(*) FROM dbo.inventory_features
UNION ALL
SELECT 'sales_orders', COUNT(*) FROM dbo.sales_orders
UNION ALL
SELECT 'sales_features', COUNT(*) FROM dbo.sales_features
UNION ALL
SELECT 'purchase_order_features', COUNT(*) FROM dbo.purchase_order_features
UNION ALL
SELECT 'forecast_features', COUNT(*) FROM dbo.forecast_features;
GO

SELECT product_id, COUNT(*) AS duplicate_count
FROM dbo.products_features
GROUP BY product_id
HAVING COUNT(*) > 1;

SELECT supplier_id, COUNT(*) AS duplicate_count
FROM dbo.supplier_features
GROUP BY supplier_id
HAVING COUNT(*) > 1;

SELECT warehouse_id, COUNT(*) AS duplicate_count
FROM dbo.warehouses
GROUP BY warehouse_id
HAVING COUNT(*) > 1;

SELECT order_id, COUNT(*) AS duplicate_count
FROM dbo.sales_orders
GROUP BY order_id
HAVING COUNT(*) > 1;

SELECT order_item_id, COUNT(*) AS duplicate_count
FROM dbo.sales_features
GROUP BY order_item_id
HAVING COUNT(*) > 1;

SELECT purchase_order_id, COUNT(*) AS duplicate_count
FROM dbo.purchase_order_features
GROUP BY purchase_order_id
HAVING COUNT(*) > 1;

SELECT snapshot_date, warehouse_id, product_id, COUNT(*) AS duplicate_count
FROM dbo.inventory_features
GROUP BY snapshot_date, warehouse_id, product_id
HAVING COUNT(*) > 1;

SELECT forecast_date, warehouse_id, product_id, forecast_horizon_days,
       COUNT(*) AS duplicate_count
FROM dbo.forecast_features
GROUP BY forecast_date, warehouse_id, product_id, forecast_horizon_days
HAVING COUNT(*) > 1;
GO

SELECT COUNT(*) AS products_with_missing_keys
FROM dbo.products_features
WHERE product_id IS NULL
   OR sku IS NULL
   OR supplier_id IS NULL;

SELECT COUNT(*) AS suppliers_with_missing_keys
FROM dbo.supplier_features
WHERE supplier_id IS NULL;

SELECT COUNT(*) AS warehouses_with_missing_keys
FROM dbo.warehouses
WHERE warehouse_id IS NULL;

SELECT COUNT(*) AS inventory_with_missing_keys
FROM dbo.inventory_features
WHERE snapshot_date IS NULL
   OR warehouse_id IS NULL
   OR product_id IS NULL;

SELECT COUNT(*) AS sales_with_missing_keys
FROM dbo.sales_features
WHERE order_item_id IS NULL
   OR order_id IS NULL
   OR product_id IS NULL;

SELECT COUNT(*) AS purchase_orders_with_missing_keys
FROM dbo.purchase_order_features
WHERE purchase_order_id IS NULL
   OR supplier_id IS NULL
   OR warehouse_id IS NULL;

SELECT COUNT(*) AS forecasts_with_missing_keys
FROM dbo.forecast_features
WHERE forecast_date IS NULL
   OR warehouse_id IS NULL
   OR product_id IS NULL;
GO

SELECT COUNT(*) AS products_with_missing_supplier
FROM dbo.products_features p
LEFT JOIN dbo.supplier_features s
    ON p.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL;

SELECT COUNT(*) AS inventory_with_missing_product
FROM dbo.inventory_features i
LEFT JOIN dbo.products_features p
    ON i.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS inventory_with_missing_warehouse
FROM dbo.inventory_features i
LEFT JOIN dbo.warehouses w
    ON i.warehouse_id = w.warehouse_id
WHERE w.warehouse_id IS NULL;

SELECT COUNT(*) AS sales_with_missing_order
FROM dbo.sales_features s
LEFT JOIN dbo.sales_orders o
    ON s.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS sales_with_missing_product
FROM dbo.sales_features s
LEFT JOIN dbo.products_features p
    ON s.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS purchase_orders_with_missing_supplier
FROM dbo.purchase_order_features po
LEFT JOIN dbo.supplier_features s
    ON po.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL;

SELECT COUNT(*) AS purchase_orders_with_missing_warehouse
FROM dbo.purchase_order_features po
LEFT JOIN dbo.warehouses w
    ON po.warehouse_id = w.warehouse_id
WHERE w.warehouse_id IS NULL;

SELECT COUNT(*) AS forecasts_with_missing_product
FROM dbo.forecast_features f
LEFT JOIN dbo.products_features p
    ON f.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS forecasts_with_missing_warehouse
FROM dbo.forecast_features f
LEFT JOIN dbo.warehouses w
    ON f.warehouse_id = w.warehouse_id
WHERE w.warehouse_id IS NULL;
GO

SELECT COUNT(*) AS invalid_product_prices
FROM dbo.products_features
WHERE unit_cost < 0
   OR selling_price <= unit_cost;

SELECT COUNT(*) AS invalid_sales_rows
FROM dbo.sales_features
WHERE quantity < 0
   OR unit_selling_price < 0
   OR discount_percent < 0
   OR returned_quantity < 0
   OR returned_quantity > quantity
   OR sales_amount < 0
   OR cost_amount < 0;

SELECT COUNT(*) AS invalid_purchase_orders
FROM dbo.purchase_order_features
WHERE ordered_units < 0
   OR received_units < 0
   OR received_units > ordered_units
   OR unit_cost < 0
   OR purchase_value < 0
   OR expected_delivery_date < order_date
   OR actual_delivery_date < order_date;

SELECT COUNT(*) AS invalid_inventory_rows
FROM dbo.inventory_features
WHERE opening_inventory_units < 0
   OR inbound_units < 0
   OR outbound_units < 0
   OR damaged_units < 0
   OR ending_inventory_units < 0
   OR inventory_value < 0
   OR ending_inventory_units <>
      opening_inventory_units
      + inbound_units
      - outbound_units
      + adjustment_units
      - damaged_units
   OR stockout_flag <>
      CASE WHEN ending_inventory_units = 0 THEN 1 ELSE 0 END;

SELECT COUNT(*) AS invalid_forecast_rows
FROM dbo.forecast_features
WHERE forecast_demand_units < 0
   OR actual_demand_units < 0
   OR forecast_lower_bound < 0
   OR forecast_upper_bound < 0
   OR forecast_lower_bound > forecast_upper_bound
   OR forecast_horizon_days NOT IN (7, 14, 30, 60);
GO

SELECT COUNT(*) AS invalid_sales_dates
FROM dbo.sales_orders
WHERE delivery_promised_date < order_date
   OR delivery_actual_date < order_date;

SELECT COUNT(*) AS invalid_order_totals
FROM dbo.sales_orders o
LEFT JOIN (
    SELECT order_id, ROUND(SUM(sales_amount), 2) AS item_total
    FROM dbo.sales_features
    GROUP BY order_id
) s
    ON o.order_id = s.order_id
WHERE ABS(o.total_order_value - ISNULL(s.item_total, 0)) > 0.01;
GO
