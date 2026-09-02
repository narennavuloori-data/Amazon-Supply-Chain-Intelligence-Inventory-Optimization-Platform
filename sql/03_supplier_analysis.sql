USE AmazonSupplyChainAnalytics;
GO

SELECT
    supplier_id,
    supplier_name,
    average_lead_time_days,
    ROUND(on_time_delivery_rate * 100, 2) AS on_time_delivery_rate_pct,
    ROUND(defect_rate * 100, 2) AS defect_rate_pct,
    reliability_score,
    supplier_risk_score
FROM dbo.supplier_features
ORDER BY supplier_risk_score DESC;
GO

SELECT TOP 20
    supplier_id,
    supplier_name,
    average_lead_time_days
FROM dbo.supplier_features
ORDER BY average_lead_time_days DESC;
GO

SELECT TOP 20
    supplier_id,
    supplier_name,
    ROUND(on_time_delivery_rate * 100, 2) AS on_time_delivery_rate_pct,
    actual_late_delivery_rate
FROM dbo.supplier_features
ORDER BY on_time_delivery_rate ASC;
GO

SELECT TOP 20
    supplier_id,
    supplier_name,
    ROUND(defect_rate * 100, 2) AS defect_rate_pct,
    quality_rating,
    quality_risk_flag
FROM dbo.supplier_features
ORDER BY defect_rate DESC;
GO

SELECT TOP 20
    supplier_id,
    supplier_name,
    reliability_score,
    supplier_risk_score,
    late_delivery_flag,
    quality_risk_flag
FROM dbo.supplier_features
ORDER BY supplier_risk_score DESC;
GO

SELECT
    supplier_status,
    COUNT(*) AS supplier_count,
    ROUND(AVG(supplier_risk_score), 2) AS average_risk_score
FROM dbo.supplier_features
GROUP BY supplier_status
ORDER BY average_risk_score DESC;
GO
