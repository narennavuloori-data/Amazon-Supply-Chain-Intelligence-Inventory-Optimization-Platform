USE AmazonSupplyChainAnalytics;
GO

SELECT
    warehouse_id,
    COUNT(*) AS orders_processed
FROM dbo.sales_orders
GROUP BY warehouse_id
ORDER BY orders_processed DESC;
GO

SELECT
    warehouse_id,
    ROUND(SUM(inventory_value), 2) AS current_inventory_value
FROM dbo.inventory_features
WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
)
GROUP BY warehouse_id
ORDER BY current_inventory_value DESC;
GO

SELECT
    warehouse_id,
    SUM(stockout_flag) AS stockout_records,
    ROUND(100.0 * SUM(stockout_flag) / COUNT(*), 2) AS stockout_rate_pct
FROM dbo.inventory_features
GROUP BY warehouse_id
ORDER BY stockout_rate_pct DESC;
GO

SELECT
    warehouse_id,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
    ROUND(
        100.0 * SUM(CASE WHEN order_status = 'Delivered' THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS fulfillment_rate_pct
FROM dbo.sales_orders
GROUP BY warehouse_id
ORDER BY fulfillment_rate_pct DESC;
GO

SELECT
    warehouse_id,
    COUNT(*) AS delivered_orders,
    SUM(
        CASE
            WHEN delivery_actual_date <= delivery_promised_date THEN 1
            ELSE 0
        END
    ) AS on_time_orders,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN delivery_actual_date <= delivery_promised_date THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_delivery_rate_pct
FROM dbo.sales_orders
WHERE order_status = 'Delivered'
AND delivery_actual_date IS NOT NULL
GROUP BY warehouse_id
ORDER BY on_time_delivery_rate_pct DESC;
GO

SELECT
    w.warehouse_id,
    w.warehouse_name,
    COUNT(o.order_id) AS orders_processed,
    ROUND(AVG(CAST(o.total_order_value AS FLOAT)), 2) AS average_order_value
FROM dbo.warehouses w
LEFT JOIN dbo.sales_orders o
    ON w.warehouse_id = o.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name
ORDER BY orders_processed DESC;
GO
