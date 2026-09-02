USE AmazonSupplyChainAnalytics;
GO

SELECT
    ROUND(SUM(inventory_value), 2) AS current_inventory_value
FROM dbo.inventory_features
WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
);
GO

SELECT
    warehouse_id,
    ROUND(SUM(inventory_value), 2) AS inventory_value
FROM dbo.inventory_features
WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
)
GROUP BY warehouse_id
ORDER BY inventory_value DESC;
GO

SELECT
    warehouse_id,
    ROUND(AVG(inventory_turnover), 2) AS average_inventory_turnover
FROM dbo.inventory_features
WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
)
GROUP BY warehouse_id
ORDER BY average_inventory_turnover DESC;
GO

SELECT
    warehouse_id,
    ROUND(AVG(days_of_inventory), 2) AS average_days_of_inventory
FROM dbo.inventory_features
WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
)
AND days_of_inventory IS NOT NULL
GROUP BY warehouse_id
ORDER BY average_days_of_inventory DESC;
GO

SELECT
    warehouse_id,
    ROUND(100.0 * SUM(stockout_flag) / COUNT(*), 2) AS stockout_rate_pct
FROM dbo.inventory_features
GROUP BY warehouse_id
ORDER BY stockout_rate_pct DESC;
GO

SELECT
    warehouse_id,
    ROUND(100.0 * SUM(overstock_flag) / COUNT(*), 2) AS overstock_rate_pct
FROM dbo.inventory_features
GROUP BY warehouse_id
ORDER BY overstock_rate_pct DESC;
GO

SELECT TOP 20
    i.product_id,
    p.product_name,
    i.warehouse_id,
    i.ending_inventory_units,
    i.inventory_value,
    i.days_of_inventory,
    i.inventory_turnover,
    i.overstock_flag,
    i.low_stock_flag
FROM dbo.inventory_features i
JOIN dbo.products_features p
    ON i.product_id = p.product_id
WHERE i.snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
)
ORDER BY i.inventory_value DESC;
GO
