USE AmazonSupplyChainAnalytics;
GO

SELECT
    order_year,
    order_month,
    SUM(net_units_sold) AS units_sold,
    ROUND(SUM(net_sales), 2) AS net_sales
FROM dbo.sales_features
GROUP BY order_year, order_month
ORDER BY order_year, order_month;
GO

SELECT
    p.is_seasonal,
    SUM(s.net_units_sold) AS units_sold,
    ROUND(SUM(s.net_sales), 2) AS net_sales
FROM dbo.sales_features s
JOIN dbo.products_features p
    ON s.product_id = p.product_id
GROUP BY p.is_seasonal
ORDER BY p.is_seasonal DESC;
GO

SELECT TOP 20
    s.product_id,
    p.product_name,
    SUM(s.net_units_sold) AS units_sold,
    ROUND(SUM(s.net_sales), 2) AS net_sales
FROM dbo.sales_features s
JOIN dbo.products_features p
    ON s.product_id = p.product_id
GROUP BY s.product_id, p.product_name
ORDER BY units_sold DESC;
GO

SELECT TOP 20
    product_id,
    ROUND(STDEV(CAST(outbound_units AS FLOAT)), 2) AS demand_volatility
FROM dbo.inventory_features
GROUP BY product_id
HAVING COUNT(*) > 1
ORDER BY demand_volatility DESC;
GO

SELECT
    forecast_horizon_days,
    ROUND(AVG(ABS(forecast_error)), 2) AS average_absolute_error,
    ROUND(AVG(mape), 2) AS average_mape,
    ROUND(AVG(forecast_accuracy), 2) AS average_forecast_accuracy
FROM dbo.forecast_features
GROUP BY forecast_horizon_days
ORDER BY forecast_horizon_days;
GO

SELECT TOP 20
    f.product_id,
    p.product_name,
    ROUND(AVG(f.forecast_accuracy), 2) AS average_forecast_accuracy,
    ROUND(AVG(f.mape), 2) AS average_mape
FROM dbo.forecast_features f
JOIN dbo.products_features p
    ON f.product_id = p.product_id
WHERE f.forecast_accuracy IS NOT NULL
GROUP BY f.product_id, p.product_name
ORDER BY average_forecast_accuracy ASC;
GO
