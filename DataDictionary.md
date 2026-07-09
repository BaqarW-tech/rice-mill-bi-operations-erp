# Data Dictionary
## Rice Mill Business Intelligence System

13 tables. Primary keys in **bold**. Generated columns are computed automatically by SQLite and never written directly.

---

### suppliers
| Column | Type | Description |
|---|---|---|
| **supplier_id** | INTEGER | Unique supplier identifier |
| supplier_name | TEXT | Supplier / trading name |
| region | TEXT | Supplier region (Qassim, Al-Ahsa, Hail, Jazan, Riyadh) |
| contact_phone | TEXT | Contact number |
| onboarding_date | DATE | Date the supplier relationship began |
| payment_terms_days | INTEGER | Standard payment terms offered to this supplier |
| is_active | BOOLEAN | Whether the supplier is currently active |

### purchases
| Column | Type | Description |
|---|---|---|
| **purchase_id** | INTEGER | Unique purchase transaction identifier |
| purchase_date | DATE | Date of delivery |
| supplier_id | INTEGER (FK → suppliers) | Supplier who delivered the paddy |
| paddy_variety | TEXT | Paddy variety delivered |
| quantity_kg | REAL | Quantity delivered, in kg |
| price_per_kg | REAL | Agreed price per kg (SAR) |
| moisture_pct | REAL | Moisture % measured at intake |
| rejected_bags | INTEGER | Number of bags rejected on quality grounds |
| delivery_delay_days | INTEGER | Days late vs. agreed delivery schedule |
| *total_amount* | REAL (generated) | `quantity_kg × price_per_kg` |

### production
| Column | Type | Description |
|---|---|---|
| **production_id** | INTEGER | Unique production run identifier |
| production_date | DATE | Date of the milling run |
| paddy_input_kg | REAL | Paddy fed into the mill |
| rice_output_kg | REAL | Whole rice produced |
| bran_output_kg | REAL | Bran by-product produced |
| husk_output_kg | REAL | Husk by-product produced |
| broken_rice_kg | REAL | Broken rice produced |
| *recovery_pct* | REAL (generated) | `rice_output_kg × 100 / paddy_input_kg` — the core milling efficiency KPI |
| shift | TEXT | Day / Night shift |
| machine_id | TEXT | Mill machine used (MILL-01 / MILL-02) |

### products
| Column | Type | Description |
|---|---|---|
| **product_id** | INTEGER | Unique product identifier |
| product_name | TEXT | Product name |
| category | TEXT | Basmati / Sella / Long Grain / Broken / By-product |
| unit_cost | REAL | Standard cost per kg (SAR) |
| unit_price | REAL | Standard selling price per kg (SAR) |
| min_stock_kg | REAL | Reorder / minimum stock threshold |

### inventory
| Column | Type | Description |
|---|---|---|
| **inventory_id** | INTEGER | Unique snapshot row identifier |
| snapshot_date | DATE | Date of the stock snapshot (weekly cadence) |
| product_id | INTEGER (FK → products) | Product being snapshotted |
| quantity_on_hand_kg | REAL | Stock on hand at snapshot date |
| warehouse | TEXT | Storage location |

### customers
| Column | Type | Description |
|---|---|---|
| **customer_id** | INTEGER | Unique customer identifier |
| customer_name | TEXT | Customer / company name |
| customer_type | TEXT | Wholesaler / Retailer / Exporter |
| region | TEXT | Customer region |
| credit_limit | REAL | Approved credit limit (SAR) |
| payment_terms_days | INTEGER | Agreed payment terms |

### sales
| Column | Type | Description |
|---|---|---|
| **sale_id** | INTEGER | Unique sale transaction identifier |
| sale_date | DATE | Date of sale |
| customer_id | INTEGER (FK → customers) | Buying customer |
| product_id | INTEGER (FK → products) | Product sold |
| quantity_kg | REAL | Quantity sold, in kg |
| selling_price_per_kg | REAL | Price charged per kg (SAR) |
| cost_price_per_kg | REAL | Cost basis per kg (SAR) |
| amount_paid | REAL | Amount collected so far (SAR) |
| *total_amount* | REAL (generated) | `quantity_kg × selling_price_per_kg` |
| *profit* | REAL (generated) | `quantity_kg × (selling_price_per_kg − cost_price_per_kg)` |
| *outstanding* | REAL (generated) | `total_amount − amount_paid` |

### employees
| Column | Type | Description |
|---|---|---|
| **employee_id** | INTEGER | Unique employee identifier |
| employee_name | TEXT | Full name |
| role | TEXT | Job title |
| department | TEXT | Production / Finance / Sales / Inventory / Purchasing |
| monthly_salary | REAL | Monthly salary (SAR) |
| hire_date | DATE | Date hired |

### expenses
| Column | Type | Description |
|---|---|---|
| **expense_id** | INTEGER | Unique expense record identifier |
| expense_date | DATE | Date incurred (monthly cadence in this dataset) |
| category | TEXT | Electricity / Diesel / Labour / Packaging / Maintenance / Transport |
| amount | REAL | Amount (SAR) |
| notes | TEXT | Free-text description |

### machine_logs
| Column | Type | Description |
|---|---|---|
| **log_id** | INTEGER | Unique log entry identifier |
| log_date | DATE | Date of the log |
| machine_id | TEXT | Machine identifier |
| running_hours | REAL | Hours the machine ran |
| downtime_hours | REAL | Hours the machine was down |
| downtime_reason | TEXT | Reason for downtime, if any |
| maintenance_cost | REAL | Maintenance cost incurred that day (SAR) |

### accounts
| Column | Type | Description |
|---|---|---|
| **account_id** | INTEGER | Unique account identifier |
| account_code | TEXT | Chart-of-accounts code (e.g. 1000) |
| account_name | TEXT | Account name |
| account_type | TEXT | Asset / Liability / Equity / Revenue / Expense |

### journal_entries (CSV: `accounting.csv`)
| Column | Type | Description |
|---|---|---|
| **entry_id** | INTEGER | Unique journal line identifier |
| entry_date | DATE | Posting date |
| account_id | INTEGER (FK → accounts) | Account being debited/credited |
| debit | REAL | Debit amount (SAR) |
| credit | REAL | Credit amount (SAR) |
| description | TEXT | Line description |
| reference_type | TEXT | Sale / Purchase / Expense / Manual |
| reference_id | INTEGER | ID of the source transaction |

### forecasts
| Column | Type | Description |
|---|---|---|
| **forecast_id** | INTEGER | Unique forecast record identifier |
| forecast_date | DATE | Date being forecast |
| metric | TEXT | production_kg / sales_kg / revenue / cash_flow |
| predicted_value | REAL | Point forecast |
| lower_bound | REAL | Lower confidence bound |
| upper_bound | REAL | Upper confidence bound |
| model_used | TEXT | Model that produced the forecast (e.g. Prophet, Linear) |

*(This table is seeded empty in the demo dataset — the Forecasting page generates predictions live rather than persisting them, but the schema supports write-back for a production deployment.)*

---

### Entity Relationships

```
suppliers 1──∞ purchases
products  1──∞ inventory
products  1──∞ sales
customers 1──∞ sales
accounts  1──∞ journal_entries
```
