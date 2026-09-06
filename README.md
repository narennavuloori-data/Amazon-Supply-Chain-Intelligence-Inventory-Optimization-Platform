# Amazon Supply Chain Intelligence & Inventory Optimization Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-Analytics-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SQL%20Server-Analytics-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white" />
  <img src="https://img.shields.io/badge/Power%20BI-Control%20Tower-F2C811?style=for-the-badge&logo=powerbi&logoColor=black" />
  <img src="https://img.shields.io/badge/scikit--learn-Forecasting-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" />
</p>

<p align="center">
  <b>End-to-end Operations Analytics + Inventory Optimization portfolio project</b><br>
  Synthetic e-commerce supply-chain data -> validation -> cleaning -> SQL analytics -> forecasting -> optimization -> Power BI decision support
</p>

> **Important:** This project uses a completely **synthetic Amazon-style dataset** for portfolio and learning purposes. It is not Amazon internal data, is not affiliated with Amazon, and should not be presented as real Amazon operational or financial information.

---

## Executive Overview

This project simulates a large e-commerce supply-chain network and converts operational data into **actionable inventory decisions**. The goal is not only to describe what happened, but to answer business questions such as:

- Which SKUs are at risk of stockout?
- Which products and warehouses are overstocked?
- Which suppliers create operational risk?
- Which warehouses have weak fulfillment or delivery performance?
- How accurate are demand forecasts?
- When should inventory be reordered?
- How much should be ordered?
- Can stock be transferred between warehouses before purchasing more?

The final output is a **5-page Power BI Supply Chain Control Tower** supported by Python, SQL Server, forecasting models, and an inventory optimization engine.

---

## Dashboard Preview

### Executive Supply Chain Overview

![Executive Supply Chain Overview](power-bi/screenshots/Executive%20Supply%20Chain%20Overview.png)

### Inventory Intelligence

![Inventory Intelligence](power-bi/screenshots/Inventory%20Intelligence.png)

### Supplier & Warehouse Performance

![Supplier & Warehouse Performance](power-bi/screenshots/Supplier%20%26%20Warehouse%20Performance.png)

### Demand & Forecast Intelligence

![Demand & Forecast Intelligence](power-bi/screenshots/Demand%20%26%20Forecast%20Intelligence.png)

### Inventory Optimization Control Tower

![Inventory Optimization Control Tower](power-bi/screenshots/Inventory%20Optimization%20Control%20Tower.png)

---

## Project Highlights

| Area | Implementation |
|---|---|
| Dataset | 8 interconnected synthetic supply-chain tables, ~4.2M records |
| Validation | Row counts, nulls, duplicate IDs, foreign keys, dates, quantities, price and inventory checks |
| Cleaning | Missing-value handling, duplicates, dates, types, outliers and invalid-record handling |
| Feature Engineering | Inventory, sales, supplier, forecast and product-level business features |
| SQL Analytics | Data quality, inventory, suppliers, warehouses, demand and optimization |
| Forecasting | Moving Average, Exponential Smoothing and Random Forest comparison |
| Optimization | Safety Stock, Reorder Point, EOQ, risk classification and recommended actions |
| Dashboard | 5-page Power BI operations control tower |
| Business Output | Action plan for overstock, stockouts, transfers, suppliers, warehouses and forecasting |

---

## Dataset

The synthetic operating timeline covers **2025-01-01 through 2026-12-31** for sales activity, with weekly inventory snapshots throughout 2026. The dataset is designed to include seasonality, promotional periods, stockouts, overstock, supplier variation, warehouse imbalance and forecast error.

| Table | Purpose | Approx. Rows |
|---|---|---:|
| `products.csv` | Product / SKU master | 5,000 |
| `suppliers.csv` | Supplier master | 300 |
| `warehouses.csv` | Warehouse master | 12 |
| `inventory_snapshots.csv` | Weekly inventory positions | 3,120,000 |
| `sales_orders.csv` | Customer orders | 300,000 |
| `sales_order_items.csv` | Product-level order lines | 570,122 |
| `purchase_orders.csv` | Supplier replenishment orders | 60,000 |
| `demand_forecasts.csv` | Demand forecast records | 149,986 |

### Core Relationships

```text
Products -> Suppliers
Inventory -> Products + Warehouses
Sales Items -> Orders + Products
Sales Orders -> Warehouses
Purchase Orders -> Suppliers + Warehouses
Forecasts -> Products + Warehouses
```

---

## End-to-End Architecture

```text
Synthetic Supply Chain Data
          |
          v
Data Validation
          |
          v
Data Cleaning
          |
          v
Feature Engineering
          |
          +------------------+
          |                  |
          v                  v
     SQL Analytics      Demand Forecasting
          |                  |
          +--------+---------+
                   v
        Inventory Optimization
                   |
                   v
          Power BI Control Tower
                   |
                   v
        Business Recommendations
```

---

## Repository Structure

```text
Amazon-Supply-Chain-Intelligence-Inventory-Optimization/
|
|-- data/
|   |-- raw/
|   `-- processed/
|
|-- sql/
|   |-- 01_data_quality_checks.sql
|   |-- 02_inventory_analysis.sql
|   |-- 03_supplier_analysis.sql
|   |-- 04_warehouse_analysis.sql
|   |-- 05_demand_analysis.sql
|   `-- 06_inventory_optimization.sql
|
|-- python/
|   |-- 01_data_validation.py
|   |-- 02_data_cleaning.py
|   |-- 03_feature_engineering.py
|   |-- 04_demand_forecasting.py
|   `-- 05_inventory_optimization.py
|
|-- power-bi/
|   |-- amazon_supply_chain_dashboard.pbix
|   `-- screenshots/
|       |-- Executive Supply Chain Overview.png
|       |-- Inventory Intelligence.png
|       |-- Supplier & Warehouse Performance.png
|       |-- Demand & Forecast Intelligence.png
|       `-- Inventory Optimization Control Tower.png
|
|-- reports/
|   |-- Amazon_Supply_Chain_Analytics_Report.pdf
|   `-- Amazon_Supply_Chain_Business_Recommendations.md
|
|-- README.md
|-- requirements.txt
`-- .gitignore
```

---

## Python Pipeline

### 1. Data Validation - `python/01_data_validation.py`

Checks:

- row counts
- missing values
- duplicate IDs
- foreign-key integrity
- negative quantities
- invalid dates
- product price consistency
- sales / PO calculations
- inventory balance and stockout logic

The large inventory table is processed in chunks to keep memory usage practical.

### 2. Data Cleaning - `python/02_data_cleaning.py`

Performs:

- missing-value treatment
- duplicate removal
- date standardization
- numeric type conversion
- domain-based outlier handling
- invalid-record handling

Cleaned files are saved to `data/processed/`.

### 3. Feature Engineering - `python/03_feature_engineering.py`

Creates business-ready fields including:

**Inventory**

- `inventory_value`
- `average_daily_demand`
- `days_of_inventory`
- `inventory_turnover`
- `stockout_flag`
- `overstock_flag`
- `low_stock_flag`
- `no_demand_stock_flag`

**Sales**

- `gross_sales`
- `net_sales`
- `net_cost`
- `gross_margin`
- `net_units_sold`
- `order_month`
- `order_week`
- `order_year`

**Products**

- `ABC_class`
- `fast_moving_flag`
- `slow_moving_flag`
- `high_value_flag`

**Suppliers**

- `supplier_risk_score`
- `late_delivery_flag`
- `quality_risk_flag`

**Forecasts**

- `forecast_error`
- `MAPE`
- `forecast_accuracy`

---

## SQL Analytics

The SQL layer is built for **Microsoft SQL Server / SSMS** using database:

```sql
AmazonSupplyChainAnalytics
```

| SQL File | Purpose |
|---|---|
| `01_data_quality_checks.sql` | SQL-side integrity and business-rule checks |
| `02_inventory_analysis.sql` | Inventory value, turnover, days inventory, stockout and overstock analysis |
| `03_supplier_analysis.sql` | Supplier lead time, on-time rate, defects, reliability and risk |
| `04_warehouse_analysis.sql` | Orders, inventory, stockouts, fulfillment and delivery performance |
| `05_demand_analysis.sql` | Demand trends, seasonality, top products, volatility and forecast accuracy |
| `06_inventory_optimization.sql` | Safety stock, reorder point, EOQ and inventory action logic |

---

## Demand Forecasting

`python/04_demand_forecasting.py` compares three business-friendly approaches for the top 50 high-volume Product x Warehouse combinations:

1. **Moving Average**
2. **Exponential Smoothing**
3. **Random Forest**

A time-based split is used: the final **8 weeks** are held out for testing instead of randomly shuffling time-series data.

### Model Comparison

| Model | Avg. MAE | Avg. RMSE |
|---|---:|---:|
| Moving Average | 8.39 | 10.29 |
| Exponential Smoothing | 8.39 | 10.34 |
| Random Forest | 8.46 | 10.41 |

The models performed similarly, demonstrating an important business lesson: **a more complicated model is not automatically a better model**.

Outputs:

- `data/processed/demand_model_performance.csv`
- `data/processed/demand_forecast_results.csv`

---

## Inventory Optimization Engine

`python/05_inventory_optimization.py` is the centerpiece of the project. It evaluates inventory at **SKU x Warehouse** level and calculates:

- average / planning demand
- demand variability
- lead time
- safety stock
- reorder point
- EOQ (Economic Order Quantity)
- current inventory and value
- stockout risk
- overstock risk
- recommended order quantity
- transfer opportunity
- recommended inventory action

### Core Logic

**Reorder Point**

```text
Reorder Point = Planning Daily Demand x Lead Time + Safety Stock
```

**EOQ**

```text
EOQ = sqrt((2 x Annual Demand x Ordering Cost) / Annual Holding Cost per Unit)
```

### Business Assumptions

| Assumption | Value |
|---|---:|
| Approx. service level | 95% |
| Service factor / Z-score | 1.65 |
| Ordering cost | 50 per order |
| Annual holding rate | 20% of unit cost |

### Possible Actions

```text
REORDER NOW
REORDER SOON
TRANSFER STOCK
REDUCE INVENTORY
MONITOR
HOLD
```

---

## Key Findings

At the latest inventory snapshot (**28 December 2026**):

| KPI | Result |
|---|---:|
| Current inventory value | 8.42M |
| SKU-warehouse combinations | 60,000 |
| Current stockout positions | 1,520 |
| Current stockout rate | 2.53% |
| Average inventory turnover | 1.93x |
| Median days of inventory | 202.78 days |
| Current overstock flag rate | 37.76% |
| No-demand stock rate | 31.05% |

### Optimization Actions

| Action | Positions |
|---|---:|
| REDUCE INVENTORY | 43,209 |
| REORDER SOON | 7,051 |
| TRANSFER STOCK | 3,801 |
| HOLD | 3,667 |
| MONITOR | 2,270 |
| REORDER NOW | 2 |

### Decision-Support Indicators

| Indicator | Modeled Value |
|---|---:|
| Medium/high overstock inventory value | 7.75M |
| Recommended replenishment value | 3.35M |
| Stockout exposure proxy | 246K |
| Transfer-stock opportunities | 3,801 positions |

These figures are **model outputs from a synthetic simulation**, not real Amazon savings, losses, budgets or financial results.

---

## Power BI Dashboard

The report is intentionally limited to five pages so that each page has a clear operational purpose.

### Page 1 - Executive Supply Chain Overview

KPIs and trends for inventory value, stockouts, turnover, days inventory, supplier service and forecast performance.

### Page 2 - Inventory Intelligence

ABC analysis, fast/slow movers, inventory efficiency and a decision matrix showing current stock, demand, reorder point, risk and recommended action.

### Page 3 - Supplier & Warehouse Performance

Supplier risk, reliability, lead time, defect rate, warehouse volume, fulfillment and delivery performance.

### Page 4 - Demand & Forecast Intelligence

Actual demand, forecast demand, seasonal patterns, forecast error, demand volatility and growing products.

### Page 5 - Inventory Optimization Control Tower

The decision-support page showing immediate-action SKUs, stockout and overstock risk, transfer opportunities and recommended replenishment.

---

## Business Recommendations

The strongest overall recommendation is **not to solve inventory risk by increasing inventory everywhere**.

The analysis supports the following actions:

1. **Reduce excess inventory first**, especially C-class, slow-moving and no-demand stock.
2. **Transfer inventory between warehouses** when one location has excess stock and another has a shortage.
3. **Protect A-class products** with targeted safety stock and priority replenishment.
4. **Intervene with high-risk suppliers** instead of permanently compensating for supplier problems with extra inventory.
5. **Improve weak warehouse delivery performance** using operational benchmarking.
6. **Build inventory ahead of seasonal peaks**, then reduce temporary safety stock after demand normalizes.
7. **Continue improving forecast accuracy** before using forecasts as fully automated purchasing signals.

See the detailed business recommendations in:

```text
reports/Amazon_Supply_Chain_Business_Recommendations.md
```

---

## How to Run the Project

### Prerequisites

- Python 3.10+
- VS Code or another Python IDE
- Microsoft SQL Server
- SQL Server Management Studio (SSMS)
- Power BI Desktop

### 1. Clone or download the repository

Open a terminal inside the project folder:

```bash
cd Amazon-Supply-Chain-Intelligence-Inventory-Optimization
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Python packages

```bash
pip install -r requirements.txt
```

### 4. Place the synthetic raw CSV files in

```text
data/raw/
```

### 5. Run the Python pipeline

```bash
python python/01_data_validation.py
python python/02_data_cleaning.py
python python/03_feature_engineering.py
python python/04_demand_forecasting.py
python python/05_inventory_optimization.py
```

### 6. Create the SQL Server database

```sql
CREATE DATABASE AmazonSupplyChainAnalytics;
```

Import the final analytical tables into SQL Server and run the scripts in `sql/` from `01` through `06`.

### 7. Open the Power BI report

```text
power-bi/amazon_supply_chain_dashboard.pbix
```

If the report was created on a different machine, update the SQL Server / local CSV data-source paths in Power BI before refreshing.

---

## Skills Demonstrated

- Python data validation and cleaning
- Pandas / NumPy data transformation
- Feature engineering
- SQL Server / SSMS analytics
- Data quality and referential-integrity checks
- Time-series forecasting
- Random Forest regression
- Forecast evaluation using MAE, RMSE and MAPE
- Inventory management concepts
- Safety stock and reorder-point calculation
- EOQ modeling
- ABC inventory classification
- Supplier risk analysis
- Warehouse performance analysis
- Power BI data modeling and DAX
- Dashboard design
- Business recommendations and decision support

---

## Limitations & Future Improvements

This is a portfolio simulation rather than a production planning system. Important limitations include:

- purchase orders do not contain SKU-level `product_id` linkage
- inter-warehouse transfer cost is not available
- transfer lead time is not available
- lost-sales cost is not available
- supplier contract constraints are not modeled
- warehouse labor scheduling is outside scope
- ordering cost and holding rate are modeling assumptions
- future versions could add rolling cross-validation, promotion variables and richer SKU-level procurement logic

---

## Project Report

A concise analytical report is included at:

```text
reports/Amazon_Supply_Chain_Analytics_Report.pdf
```

---

## Why This Project Matters

This project goes beyond a standard dashboard by demonstrating the complete analytics chain:

```text
Business Problem
      -> Raw Operational Data
      -> Data Quality
      -> Feature Engineering
      -> SQL Analysis
      -> Forecasting
      -> Inventory Optimization
      -> Power BI Decision Support
      -> Business Recommendations
```

The centerpiece is the transition from **descriptive analytics** to **prescriptive decision support**: identifying not only where inventory risk exists, but also recommending what action should be taken.

---

<p align="center"><b>Operations Analytics | Supply Chain Intelligence | Inventory Optimization | Forecasting | Power BI</b></p>
