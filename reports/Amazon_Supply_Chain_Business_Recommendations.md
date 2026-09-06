# Amazon Supply Chain Intelligence & Inventory Optimization Platform
## Business Recommendations

**Dataset:** Completely synthetic Amazon-style supply-chain simulation  
**Latest inventory snapshot:** 28 December 2026  
**Decision level:** SKU × Warehouse  
**Purpose:** Convert analytical findings into practical supply-chain actions.

---

## 1. Executive Summary

The analysis indicates that the largest opportunity is **inventory rebalancing and excess-stock reduction**, not simply increasing replenishment.

At the latest inventory snapshot, the platform contains approximately **8.42 million** in inventory value across **60,000 SKU–warehouse combinations**. The optimization engine classifies a large share of inventory positions as medium/high overstock risk, while a smaller group faces immediate or near-term stockout risk.

The recommended operating strategy is therefore:

1. **Reduce excess inventory before placing new purchase orders wherever possible.**
2. **Transfer stock between warehouses when the same SKU is overstocked in one location and at risk in another.**
3. **Prioritize replenishment for high-value and A-class SKUs that fall below reorder thresholds.**
4. **Intervene with high-risk suppliers and warehouses with weak delivery performance.**
5. **Use forecasting as a planning input, but continue improving forecast accuracy before relying on it as the sole replenishment signal.**

---

## 2. Key Analytical Findings

### Inventory Position

| Metric | Result |
|---|---:|
| Latest inventory value | 8.42M |
| SKU–warehouse combinations | 60,000 |
| Current stockout positions | 1,520 |
| Current stockout rate | 2.53% |
| Average inventory turnover | 1.93x |
| Median inventory turnover | 0.75x |
| Median days of inventory | 202.78 days |
| Average days of inventory | 399.78 days |
| Current overstock flag rate | 37.76% |
| No-demand stock rate | 31.05% |

The median inventory coverage of about **203 days** suggests that substantial working capital is tied up in inventory for long periods.

The high no-demand-stock rate is also important. Inventory that has stock on hand but no recorded demand should be reviewed separately from normal overstock because it may represent inactive, poorly allocated, newly launched, or genuinely slow-moving products.

---

## 3. Optimization Engine Results

The inventory optimization engine generated the following actions:

| Recommended Action | SKU–Warehouse Positions |
|---|---:|
| REDUCE INVENTORY | 43,209 |
| REORDER SOON | 7,051 |
| TRANSFER STOCK | 3,801 |
| HOLD | 3,667 |
| MONITOR | 2,270 |
| REORDER NOW | 2 |

### Risk Distribution

| Stockout Risk | Positions |
|---|---:|
| Critical | 1,520 |
| High | 2,283 |
| Medium | 7,051 |
| Low | 49,146 |

| Overstock Risk | Positions |
|---|---:|
| High | 46,192 |
| Medium | 3,023 |
| Low | 10,785 |

The model therefore shows a **two-sided inventory imbalance**:

- some warehouses have too much stock,
- while other warehouses carry the same or similar demand exposure with insufficient stock.

This supports using **inventory transfers and rebalancing before supplier replenishment**.

---

# 4. Recommendation 1 — Reduce Excess Inventory

### Finding

Approximately **7.75M of current inventory value** is associated with medium/high overstock-risk positions in the optimization output.

This is an **exposure value**, not guaranteed cash savings. Not all of this inventory can or should be eliminated.

### Recommended Actions

- Freeze or reduce new replenishment for high-overstock SKUs.
- Prioritize C-class and slow-moving products for inventory reduction.
- Review SKUs with more than 120 days of inventory.
- Review products with inventory but no recent recorded demand.
- Use promotions, markdowns, bundling, or demand-generation campaigns for suitable slow-moving products.
- Reduce future purchase quantities for products consistently classified as overstocked.
- Review minimum order quantities where supplier agreements create unnecessarily large replenishment batches.

### Business Objective

Reduce excess working capital while protecting service levels for high-priority products.

### Primary KPIs

- Excess Inventory Value
- Days of Inventory
- Inventory Turnover
- Overstock Rate
- No-Demand Stock Count

---

# 5. Recommendation 2 — Rebalance Inventory Between Warehouses

### Finding

The engine identified **3,801 SKU–warehouse positions** where stock transfer is preferable to immediate external replenishment.

### Recommended Actions

Before issuing a new purchase order:

1. Check whether the same SKU has medium/high overstock at another warehouse.
2. Compare transfer quantity with destination reorder-point requirements.
3. Transfer only enough inventory to restore the receiving warehouse to a healthy level.
4. Preserve adequate safety stock at the source warehouse.
5. Track transfer lead time and transfer cost in a future version of the model.

### Business Logic

A stock transfer can be superior to a supplier order when:

**Receiving Warehouse = Stockout / High Risk**

and

**Source Warehouse = Excess Stock**

This can simultaneously reduce:

- stockout exposure,
- excess stock,
- procurement spend,
- inventory imbalance.

### Limitation

The current synthetic dataset does not contain inter-warehouse transportation cost or transfer lead-time data. Therefore, the engine identifies transfer opportunities but does not perform a full transportation-cost optimization.

---

# 6. Recommendation 3 — Prioritize Replenishment by Business Importance

### Finding

The model identifies:

- **1,520 critical stockout positions**
- **2,283 high-risk positions**
- **7,051 medium-risk positions**

The model also recommends approximately **330,177 units** of replenishment across applicable positions.

Estimated replenishment value based on product unit cost is approximately **3.35M**.

This should be treated as a planning requirement generated from the model assumptions, not an approved purchasing budget.

### Recommended Priority

#### Priority 1
A-class SKU + Critical/High Stockout Risk

Action:

**REORDER NOW or TRANSFER STOCK**

#### Priority 2
A/B-class SKU + Medium Stockout Risk

Action:

**REORDER SOON**

#### Priority 3
C-class SKU + Medium Risk

Action:

Review business value before automatically replenishing.

### Why

Not every stockout has the same business impact.

A stockout on an A-class fast-moving product is more important than a stockout on a low-revenue C-class product.

### Primary KPIs

- Reorder Point
- Safety Stock
- Recommended Order Quantity
- ABC Class
- Stockout Risk
- Replenishment Value

---

# 7. Recommendation 4 — Protect Against Stockout Exposure

### Finding

Using the gap between reorder point and current stock multiplied by unit cost, the model estimates approximately **246K of inventory-value exposure** across Critical and High stockout-risk positions.

This is a **stockout exposure proxy**, not an estimate of lost revenue or lost profit.

### Recommended Actions

- Review Critical risk daily.
- Review High risk at least several times per week.
- Increase safety stock selectively for volatile A-class products.
- Shorten supplier lead times for repeatedly exposed SKUs.
- Use forecast demand when it exceeds historical demand.
- Separate chronic stockout problems from one-time promotional spikes.

### Business Objective

Maintain availability without solving stockouts by simply increasing inventory everywhere.

---

# 8. Recommendation 5 — Focus Supplier Management on the Highest-Risk Suppliers

### Supplier Portfolio Summary

| Metric | Result |
|---|---:|
| Average supplier on-time rate | 90.44% |
| Average supplier lead time | 28.04 days |
| Average defect rate | 2.50% |
| Average supplier risk score | 22.16 |
| Suppliers with risk score ≥ 50 | 10 |

The highest-risk suppliers in the model include suppliers with combinations of:

- low reliability,
- high defect rate,
- long lead time,
- weak on-time delivery,
- low quality ratings.

### Highest-Risk Examples

| Supplier | Risk Score | Reliability | Lead Time | Defect Rate |
|---|---:|---:|---:|---:|
| Ashgrove Ltd. (3) | 63.85 | 13.1 | 37 days | 7.43% |
| Harborlight Corporation | 60.57 | 15.2 | 21 days | 6.28% |
| Calderon Enterprises | 59.06 | 17.2 | 27 days | 6.19% |

### Recommended Actions

- Put the highest-risk suppliers on performance-improvement plans.
- Establish minimum on-time-delivery and defect-rate thresholds.
- Review alternative suppliers for A-class products supplied by high-risk vendors.
- Increase safety stock only where supplier risk cannot be reduced economically.
- Review supplier performance monthly using a scorecard.

### Business Objective

Reduce supply variability at the source instead of compensating for poor suppliers with permanently higher inventory.

---

# 9. Recommendation 6 — Improve Warehouse Delivery Performance

Warehouse fulfillment rates are relatively similar, but on-time delivery performance varies materially.

### Lowest On-Time Delivery Warehouses

| Warehouse | On-Time Delivery Rate |
|---|---:|
| Phoenix Distribution Center | 57.63% |
| Queretaro Sortation Center | 57.86% |
| Hyderabad Fulfillment Center | 63.72% |
| Los Angeles Fulfillment Center | 64.67% |

The strongest warehouse in the simulation is Seattle Fulfillment Center at approximately **75.94% on-time delivery**.

### Recommended Actions

For lower-performing warehouses:

- compare order volumes against daily processing capacity,
- review staffing and processing bottlenecks,
- investigate priority-order handling,
- compare late-delivery rates by order channel and priority,
- identify whether delays occur inside the warehouse or after dispatch,
- benchmark processes against higher-performing warehouses.

### Business Objective

Improve service performance without adding unnecessary inventory.

---

# 10. Recommendation 7 — Prepare for Seasonal Demand Peaks Earlier

The sales data shows stronger demand during periods such as:

- July–August,
- November,
- December.

December 2025 generated the highest monthly unit volume in the processed sales data, followed by other summer and year-end periods.

### Recommended Actions

For known peak periods:

- build inventory before demand peaks rather than reacting during them,
- increase replenishment frequency for fast-moving products,
- review supplier capacity before peak periods,
- monitor stockout risk more frequently,
- adjust reorder points using forecast demand,
- avoid carrying peak-period safety stock permanently after demand normalizes.

### Business Objective

Use temporary inventory buildup for seasonal demand rather than maintaining excessive stock all year.

---

# 11. Recommendation 8 — Improve Forecast Accuracy Before Expanding Automation

The forecasting layer compared:

- Moving Average
- Exponential Smoothing
- Random Forest

for the top 50 Product × Warehouse combinations using an 8-week holdout period.

### Model Comparison

| Model | Average MAE | Average RMSE |
|---|---:|---:|
| Moving Average | 8.39 | 10.29 |
| Exponential Smoothing | 8.39 | 10.34 |
| Random Forest | 8.46 | 10.41 |

The three approaches performed very similarly. The more complex Random Forest did not materially outperform the simpler baselines.

This is an important business finding.

### Recommendation

Use the **simplest model that performs adequately** rather than adding complexity without measurable improvement.

### Next Improvements

- forecast at category/SKU segments with different demand behavior,
- add promotional-event variables,
- add seasonality features,
- separate intermittent-demand products,
- incorporate supplier and inventory constraints,
- use rolling time-series cross-validation,
- measure weighted forecast accuracy for high-value SKUs.

### Business Objective

Increase forecast reliability before allowing forecast outputs to automatically trigger purchasing decisions.

---

# 12. Recommendation 9 — Use Different Policies for ABC Classes

ABC classification should drive inventory policy.

### A-Class Products

Recommended policy:

- highest service level,
- tighter monitoring,
- stronger safety-stock protection,
- frequent replenishment,
- priority supplier management.

### B-Class Products

Recommended policy:

- moderate safety stock,
- normal replenishment frequency,
- exception-based monitoring.

### C-Class Products

Recommended policy:

- lower inventory targets,
- less frequent ordering,
- stronger overstock controls,
- avoid automatic replenishment for low-demand items.

### Important Finding

A large number of `REDUCE INVENTORY` recommendations occur in C-class products.

This makes C-class inventory a strong starting point for working-capital reduction.

---

# 13. Recommendation 10 — Turn the Dashboard into an Operating Review

The Power BI Control Tower should not only be viewed as a reporting dashboard.

It should support a repeatable operating process.

### Daily Review

Focus on:

- Critical Stockout Risk
- REORDER NOW
- TRANSFER STOCK
- major warehouse stockouts

### Weekly Review

Focus on:

- REORDER SOON
- overstock movement
- replenishment value
- forecast accuracy
- warehouse performance

### Monthly Review

Focus on:

- supplier risk,
- inventory turnover,
- days of inventory,
- ABC-class policy,
- slow/no-demand stock,
- forecast-model performance.

This turns the dashboard into an **operations management system** rather than a static visualization project.

---

# 14. Prioritized Action Plan

## Immediate — 0 to 30 Days

1. Review all Critical and High stockout-risk SKUs.
2. Execute valid warehouse-transfer opportunities before placing new orders.
3. Stop/reduce replenishment for severe overstock positions.
4. Focus first on A-class products.
5. Review the 10 highest-risk suppliers.

## Near Term — 30 to 60 Days

1. Reduce C-class and slow-moving inventory.
2. Review no-demand inventory.
3. Investigate Phoenix, Queretaro, Hyderabad and Los Angeles delivery performance.
4. Calibrate safety-stock and reorder-point assumptions.
5. Create supplier and warehouse performance scorecards.

## Medium Term — 60 to 90 Days

1. Improve forecasting by demand segment.
2. Add promotional and seasonal variables.
3. Add transfer cost and transfer lead time.
4. Add product-level purchase-order linkage in the data model.
5. Build scenario analysis for service level, holding cost and ordering cost.

---

# 15. Estimated Decision-Support Opportunities

| Area | Model Indicator |
|---|---:|
| Current inventory value | 8.42M |
| Medium/high overstock inventory value | 7.75M |
| Recommended replenishment value | 3.35M |
| Stockout exposure proxy | 246K |
| Transfer-stock opportunities | 3,801 positions |
| Critical stockouts | 1,520 positions |

These values are **analytical indicators from a synthetic simulation**.

They should not be described as actual Amazon savings, losses, budgets, or financial results.

---

# 16. Important Assumptions and Limitations

This project uses a completely synthetic dataset and should never be presented as real Amazon internal data.

The inventory optimization engine also uses business assumptions including:

- approximately 95% service level,
- service factor / Z-score of 1.65,
- ordering cost of 50 per order,
- annual holding rate of 20% of unit cost.

The current model does not include:

- real transportation cost,
- inter-warehouse transfer lead time,
- lost-sales cost,
- product-level purchase-order linkage,
- supplier contract constraints,
- warehouse labor scheduling,
- actual Amazon policies.

Therefore, the recommendations demonstrate **analytical decision-support logic**, not production-ready automated purchasing decisions.

---

# 17. Final Business Recommendation

The strongest overall recommendation from the project is:

> **Do not solve inventory risk by increasing inventory everywhere. First rebalance excess stock across warehouses, aggressively control slow-moving and no-demand inventory, protect A-class SKUs with targeted safety stock and replenishment, improve high-risk suppliers and weak warehouse operations, and use demand forecasts as one input into a disciplined inventory decision process.**

This approach simultaneously targets:

- working-capital efficiency,
- product availability,
- supplier reliability,
- warehouse performance,
- forecast quality,
- operational decision speed.

---

## Interview Summary

A concise way to explain the recommendations:

> “The analysis showed that the simulated network had both overstock and stockout problems at the same time. I used SKU–warehouse level inventory, demand, lead time, safety stock, reorder points, EOQ and forecast demand to generate operational actions. My main recommendation was to rebalance inventory between warehouses before purchasing more stock, reduce slow-moving and C-class excess inventory, prioritize replenishment for high-value products, improve high-risk suppliers and weak warehouses, and continuously improve forecast accuracy. This converted the project from descriptive reporting into a decision-support system.”

