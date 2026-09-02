USE AmazonSupplyChainAnalytics;
GO

DECLARE @OrderingCost FLOAT = 50;
DECLARE @HoldingRate FLOAT = 0.20;
DECLARE @ServiceFactor FLOAT = 1.65;

DROP TABLE IF EXISTS #DemandStats;
DROP TABLE IF EXISTS #InventoryCalc;

SELECT
    warehouse_id,
    product_id,
    STDEV(CAST(outbound_units AS FLOAT)) AS weekly_demand_std
INTO #DemandStats
FROM dbo.inventory_features
GROUP BY warehouse_id, product_id;

SELECT
    i.warehouse_id,
    i.product_id,
    p.product_name,
    i.ending_inventory_units AS current_inventory,
    i.average_daily_demand,
    p.standard_lead_time_days AS lead_time_days,
    i.stockout_flag,
    i.low_stock_flag,
    i.overstock_flag,
    i.days_of_inventory,
    i.inventory_value,
    ROUND(
        @ServiceFactor
        * ISNULL(d.weekly_demand_std, 0)
        * SQRT(p.standard_lead_time_days / 7.0),
        0
    ) AS safety_stock,
    ROUND(
        SQRT(
            (
                2.0
                * (i.average_daily_demand * 365)
                * @OrderingCost
            )
            / NULLIF(p.unit_cost * @HoldingRate, 0)
        ),
        0
    ) AS eoq
INTO #InventoryCalc
FROM dbo.inventory_features i
JOIN dbo.products_features p
    ON i.product_id = p.product_id
LEFT JOIN #DemandStats d
    ON i.warehouse_id = d.warehouse_id
    AND i.product_id = d.product_id
WHERE i.snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM dbo.inventory_features
);

SELECT
    warehouse_id,
    product_id,
    product_name,
    current_inventory,
    ROUND(average_daily_demand, 2) AS average_daily_demand,
    lead_time_days,
    safety_stock,
    ROUND(
        average_daily_demand * lead_time_days + safety_stock,
        0
    ) AS reorder_point,
    eoq,
    CASE
        WHEN current_inventory <=
             average_daily_demand * lead_time_days + safety_stock
        THEN 1
        ELSE 0
    END AS reorder_flag,
    CASE
        WHEN stockout_flag = 1 THEN 'Critical'
        WHEN current_inventory <=
             average_daily_demand * lead_time_days
        THEN 'High'
        WHEN current_inventory <=
             average_daily_demand * lead_time_days + safety_stock
        THEN 'Medium'
        ELSE 'Low'
    END AS stockout_risk,
    CASE
        WHEN current_inventory <=
             average_daily_demand * lead_time_days + safety_stock
        THEN
            CASE
                WHEN eoq >
                     average_daily_demand * lead_time_days
                     + safety_stock
                     - current_inventory
                THEN eoq
                ELSE ROUND(
                    average_daily_demand * lead_time_days
                    + safety_stock
                    - current_inventory,
                    0
                )
            END
        ELSE 0
    END AS recommended_order_quantity,
    CASE
        WHEN stockout_flag = 1 THEN 'REORDER NOW'
        WHEN current_inventory <=
             average_daily_demand * lead_time_days
        THEN 'REORDER NOW'
        WHEN current_inventory <=
             average_daily_demand * lead_time_days + safety_stock
        THEN 'REORDER SOON'
        WHEN overstock_flag = 1 THEN 'REDUCE INVENTORY'
        WHEN days_of_inventory > 60 THEN 'MONITOR'
        ELSE 'HOLD'
    END AS inventory_action
FROM #InventoryCalc
ORDER BY
    CASE
        WHEN stockout_flag = 1 THEN 1
        WHEN current_inventory <=
             average_daily_demand * lead_time_days
        THEN 2
        WHEN current_inventory <=
             average_daily_demand * lead_time_days + safety_stock
        THEN 3
        WHEN overstock_flag = 1 THEN 4
        ELSE 5
    END,
    inventory_value DESC;

DROP TABLE #DemandStats;
DROP TABLE #InventoryCalc;
GO
