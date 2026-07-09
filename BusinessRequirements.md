# Business Requirements Document (BRD)
## Rice Mill Business Intelligence System

---

### 1. Project Overview

This project digitizes and analyzes the end-to-end operations of a mid-sized rice mill — from paddy procurement through milling, inventory, sales, and financial reporting — replacing a traditional, paper/spreadsheet-based process with a single integrated BI platform.

### 2. Business Problem

Rice mills in the region (data modeled on Saudi supplier regions — Qassim, Al-Ahsa, Hail, Jazan, Riyadh) typically run on disconnected systems: paper delivery notes, manual weighbridge logs, Excel-based sales ledgers, and hand-written cashbooks. This creates specific, costly problems:

- **No real-time visibility** into stock levels, leading to either stockouts or overstocking of the six product lines (rice grades, bran, husk).
- **No supplier accountability** — moisture content, rejected bags, and delivery delays are recorded on paper and never aggregated, so underperforming suppliers keep getting business.
- **No production efficiency tracking** — recovery % (rice output ÷ paddy input) is the single most important KPI in milling economics, yet it's rarely measured systematically.
- **Manual bookkeeping** — journals, ledgers, and trial balances are compiled by hand at month-end, delaying financial visibility by weeks.
- **No forecasting** — purchasing and staffing decisions are made reactively rather than from a demand/production forecast.

### 3. Current Traditional Process

1. Supplier delivers paddy → weighbridge slip written by hand → moisture checked with a handheld meter, noted on paper.
2. Paddy queued and milled in batches; output weights recorded in a logbook, rarely reconciled against input.
3. Finished product moved to warehouse; stock ledger updated manually, often days later.
4. Sales orders taken by phone/in person; invoices handwritten or built in ad-hoc Excel sheets.
5. Expenses (electricity, diesel, labour, packaging, maintenance, transport) tracked in a physical cashbook.
6. At month-end, an accountant manually compiles a trial balance and P&L from all of the above.

### 4. Proposed Digital Solution

A relational database (13 tables covering suppliers → purchases → production → inventory → sales → accounting) feeding a multi-page Streamlit analytics application, with:

- Automated KPI calculation (recovery %, turnover, margins, utilization) instead of manual computation.
- Supplier and customer scorecards computed from transaction history rather than memory/reputation.
- An auto-generated general ledger and trial balance from double-entry postings triggered by every purchase, sale, and expense.
- A forecasting module (Prophet, with a linear-trend fallback) for production, sales, revenue, and cash flow.
- A SQL Explorer so non-technical stakeholders can self-serve ad-hoc questions without writing code.

### 5. Stakeholders

| Stakeholder | Interest |
|---|---|
| Mill Owner / General Manager | Overall profitability, strategic decisions |
| Mill Manager | Production efficiency, machine utilization |
| Procurement Officer | Supplier performance, purchase pricing |
| Accountant | Accurate, timely financial statements |
| Sales Executives | Customer performance, receivables |
| Warehouse Supervisor | Stock accuracy, reorder alerts |

### 6. Functional Requirements

- FR1: System shall record every paddy purchase with supplier, quantity, price, moisture %, rejects, and delivery delay.
- FR2: System shall record every production run with paddy input and rice/bran/husk/broken outputs, and calculate recovery % automatically.
- FR3: System shall maintain a running inventory balance by product and warehouse.
- FR4: System shall record every sale with customer, product, quantity, price, and payment received, and calculate profit and outstanding balance automatically.
- FR5: System shall auto-post every purchase, sale, and expense to a double-entry journal.
- FR6: System shall generate a Trial Balance, Profit & Loss statement, and Balance Sheet on demand from journal data.
- FR7: System shall forecast production, sales, revenue, and cash flow over a user-selected horizon.
- FR8: System shall allow ad-hoc SQL querying of the underlying database through a guarded, read-only interface.

### 7. Non-Functional Requirements

- NFR1: Dashboards must load in under 3 seconds for a 12-month dataset (~10,000+ transaction rows).
- NFR2: The application must run on Streamlit Community Cloud with no paid infrastructure.
- NFR3: The SQL Explorer must reject any non-SELECT statement to prevent accidental data modification.
- NFR4: All financial calculations must reconcile — i.e., trial balance debits must always equal credits.

### 8. Use Cases

- **UC1 — Reject an underperforming supplier**: Procurement officer opens Supplier Analytics, filters by composite score, identifies suppliers below a quality threshold, and reduces future allocation.
- **UC2 — Investigate a recovery % drop**: Mill manager notices a dip in the Production heatmap, drills into daily records to isolate the shift/machine responsible.
- **UC3 — Chase receivables**: Sales team opens Customer Dashboard, sorts by outstanding balance and risk score, and prioritizes collection calls.
- **UC4 — Month-end close**: Accountant opens Financial Dashboard, confirms the trial balance is in balance, and exports the P&L.
- **UC5 — Plan next month's purchasing**: Owner opens Forecasting, selects Sales Volume, and reviews the 30-day forecast to plan procurement volumes.

### 9. Pain Points → Solved By

| Pain Point | Solved By |
|---|---|
| No visibility into stock levels | Inventory Dashboard with live stock alerts |
| Supplier quality not tracked | Composite supplier scorecard + radar chart |
| Recovery % not measured | Auto-calculated `recovery_pct` generated column on every production run |
| Slow, manual bookkeeping | Auto-posted double-entry journal → instant Trial Balance/P&L/Balance Sheet |
| No forecasting | Prophet-based forecasting page with graceful fallback |
| Ad-hoc questions require a developer | SQL Explorer with presets + guarded free-text query box |

### 10. Gap Analysis

| Capability | Current State | Target State | Gap |
|---|---|---|---|
| Stock visibility | Manual, days-old | Real-time dashboard | Digitize inventory snapshots |
| Supplier evaluation | Informal/reputational | Data-driven composite score | Build scoring model |
| Financial reporting | Manual, month-end only | On-demand, auto-generated | Automate journal posting |
| Forecasting | None | Model-based, 7–90 day horizon | Introduce Prophet/linear models |

### 11. SWOT Analysis

**Strengths** — Single integrated data model spanning the full value chain; automated double-entry bookkeeping; free-tier deployable.
**Weaknesses** — Synthetic/demo data for portfolio purposes; no multi-user auth or role-based access yet.
**Opportunities** — Extend to multi-site mills; add mobile data capture at the weighbridge; integrate real ERP/accounting systems.
**Threats** — Manual re-entry errors if not integrated with real weighbridge/POS hardware; data quality dependent on discipline of daily entry.

### 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Inconsistent daily data entry | Medium | High | Add input validation and mandatory-field enforcement |
| Streamlit Cloud resource limits on large datasets | Low | Medium | Cache aggressively (`st.cache_data`), pre-aggregate in SQL |
| Forecast model unavailable at deploy time (Prophet install failure) | Medium | Low | Automatic linear-trend fallback already implemented |
| Trial balance drift from bad journal logic | Low | High | Automated reconciliation check surfaced on the Financial Dashboard |

### 13. Project Scope

**In scope:** Purchasing, production, inventory, sales, customers, expenses, machine logs, accounting, forecasting, SQL access layer, 12-page Streamlit application, full SQL query library, documentation set.

**Out of scope (see FutureImprovements.md):** Multi-user authentication, real-time hardware integration (weighbridge/POS), multi-currency, multi-site consolidation, mobile app.

### 14. Requirements Traceability Matrix

| Req ID | Description | Delivered In |
|---|---|---|
| FR1 | Purchase recording | `database/schema.sql` (purchases table), Purchase Dashboard |
| FR2 | Production recovery calc | `production` table generated column, Production Dashboard |
| FR3 | Inventory balance | `inventory` table, Inventory Dashboard |
| FR4 | Sales profit/outstanding calc | `sales` table generated columns, Sales Dashboard |
| FR5 | Auto journal posting | `database/generate_data.py` journal-entry generation logic |
| FR6 | Financial statements | Financial Dashboard (6 tabs) |
| FR7 | Forecasting | Forecasting page (Prophet + fallback) |
| FR8 | SQL access | SQL Explorer page |
