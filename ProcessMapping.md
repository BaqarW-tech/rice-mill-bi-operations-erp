# Process Mapping
## Rice Mill Business Intelligence System

---

### End-to-End Value Chain

```
SUPPLIER
   │  paddy delivery, moisture check, weighbridge
   ▼
PURCHASE
   │  quantity, price, variety, quality metrics recorded
   ▼
PRODUCTION (Milling)
   │  paddy input → rice + bran + husk + broken rice
   │  recovery % calculated automatically
   ▼
INVENTORY
   │  finished goods stocked by product, warehouse
   ▼
SALES
   │  customer order → invoice → payment (full or partial)
   ▼
ACCOUNTING
   │  every purchase / sale / expense auto-posts to the journal
   ▼
FINANCIAL STATEMENTS
      Trial Balance → P&L → Balance Sheet → Cash Flow
```

### Current (Manual) Process — Swimlane Summary

| Step | Actor | Tool Used | Latency |
|---|---|---|---|
| Record delivery | Procurement Officer | Paper weighbridge slip | Same day |
| Check moisture/quality | Procurement Officer | Handheld meter, paper log | Same day |
| Log production run | Machine Operator | Logbook | End of shift |
| Update stock ledger | Warehouse Supervisor | Excel (manual) | 1–3 days lag |
| Record sale | Sales Executive | Handwritten invoice / Excel | Same day |
| Record expense | Accountant | Physical cashbook | Weekly batch |
| Compile trial balance | Accountant | Manual ledger reconciliation | Month-end only |

**Key friction points:** data lives in 4+ disconnected places; recovery % and supplier quality are never aggregated; financial visibility lags actual operations by up to a month.

### Future (Digital) Process — Swimlane Summary

| Step | Actor | Tool Used | Latency |
|---|---|---|---|
| Record delivery | Procurement Officer | `purchases` table entry | Real-time |
| Quality auto-scored | System | Composite supplier score (recalculated on load) | Real-time |
| Log production run | Machine Operator | `production` table entry | Real-time |
| Stock auto-updates | System | `inventory` snapshot logic | Real-time |
| Record sale | Sales Executive | `sales` table entry | Real-time |
| Expense recorded | Accountant | `expenses` table entry | Real-time |
| Journal auto-posts | System | Double-entry logic on every transaction | Real-time |
| Trial balance / P&L | Accountant | Financial Dashboard | On-demand |

**Key improvement:** every downstream report (KPIs, scorecards, financial statements) is now a query against live data rather than a separate manual compilation step.

### Data Flow Diagram (Entity Relationships)

```
Supplier ──< Purchase >── Production ──< Inventory >── Sale >── Customer
                                                          │
                                                          ▼
                                                   Journal Entry ──> Account
                                                          │
                                              (also posted from) Expense
```

### Process Improvement Summary

| Before | After |
|---|---|
| Supplier chosen on reputation | Supplier chosen on composite score (moisture, rejects, delay) |
| Recovery % rarely checked | Recovery % tracked per run, trended, benchmarked at 66% |
| Stock counted physically, periodically | Stock balance always current from transaction log |
| Trial balance built once a month | Trial balance available on-demand, always reconciled |
| No forecasting | 7–90 day forecasts for production, sales, revenue, cash flow |
