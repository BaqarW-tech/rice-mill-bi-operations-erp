# Rice Mill Business Intelligence System

![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-portfolio%20demo-lightgrey)

An end-to-end Business Intelligence (BI) platform for rice mill operations — paddy procurement, milling, inventory, sales, and accounting — built on a 13-table relational data model with automated double-entry bookkeeping and time-series forecasting.

Note on badges: this repository doesn't yet have a CI pipeline or a test-coverage report, so I'm not shipping build-status or coverage badges — adding those honestly would require actually wiring up GitHub Actions and pytest first (see [Contributing](#contributing)).

---
# Live Demo

(https://rice-mill-bi-operations-erp-3ey3rwdszjadztctpdd6um.streamlit.app/) 

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Why This Over Alternatives?](#why-this-over-alternatives)
- [Known Gotchas](#known-gotchas)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **12-page Streamlit application** covering Purchasing, Supplier Analytics, Production, Inventory, Sales, Customers, Cost, Machine, Financial statements, Forecasting, and a SQL Explorer.
- **Automated double-entry bookkeeping** — every purchase, sale, and expense posts to a journal automatically; the Trial Balance always reconciles (debits = credits, verified programmatically).
- **Supplier and customer scorecards** computed from transaction history (moisture %, reject rate, delivery delay for suppliers; collection rate and risk score for customers), not manual ratings.
- **Recovery % as a generated SQL column** (`rice_output_kg × 100 / paddy_input_kg`) — the core efficiency metric in milling economics, calculated at the database layer rather than in application code.
- **Forecasting with graceful degradation** — uses Prophet by default; if Prophet fails to install (which does happen on constrained platforms), it falls back automatically to a linear-trend model with a confidence band, rather than crashing the page.
- **SQL Explorer** with 8 preset analytical queries and a guarded free-text box that rejects any statement that isn't a `SELECT`.
- **Synthetic-but-consistent dataset**: a data generator (`database/generate_data.py`) produces 12 months of data where every number reconciles — paddy purchased ties to paddy milled, inventory never goes negative, journal entries balance to zero.

## Demo

This is a portfolio project, not a hosted product — there's no live demo link to share yet. To see it running, follow [Quick Start](#quick-start) below; it takes under two minutes to get the full app running locally with sample data already generated.

## Prerequisites

- Python 3.12 (pinned in `runtime.txt` for Streamlit Community Cloud; other 3.x versions will likely work locally but aren't tested)
- pip 23+
- ~50 MB free disk space (dataset + SQLite database)
- No external API keys or paid services required

## Quick Start

```bash
git clone https://github.com/<your-username>/rice-mill-business-intelligence-system.git
cd rice-mill-business-intelligence-system

pip install -r requirements.txt

# Generate the synthetic dataset (12 months of data) and build the SQLite DB
python database/generate_data.py
```

Real output from running the generator:

```
Done.
{'suppliers': 18, 'purchases': 874, 'production': 365, 'products': 6,
 'inventory': 312, 'customers': 25, 'sales': 1686, 'employees': 8,
 'expenses': 72, 'machine_logs': 730, 'accounts': 9, 'accounting': 8636,
 'forecast': 0}
```

```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501` with the Home page's executive summary — total revenue, profit, inventory value, current stock, average recovery %, and latest-day output — followed by 11 more pages accessible from the sidebar.

## Usage

### Running a query directly against the data

The database is plain SQLite, so you can query it with nothing but the standard library:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("database/rice_mill.db")

df = pd.read_sql("""
    SELECT MIN(recovery_pct), MAX(recovery_pct), AVG(recovery_pct)
    FROM production
""", conn)
print(df)
```

Output (from the shipped sample dataset):

```
   MIN(recovery_pct)  MAX(recovery_pct)  AVG(recovery_pct)
0           53.49            65.51              60.17
```

### Regenerating the dataset with different parameters

`database/generate_data.py` seeds `numpy` with `np.random.seed(42)` for reproducibility. Change the seed or the date range (`START_DATE` / `END_DATE` near the top of the file) to produce a different — but still internally consistent — dataset, then re-run it. It rebuilds `data/*.csv` and `database/rice_mill.db` from scratch each time.

### Exploring ad-hoc questions without writing code

Open the **SQL Explorer** page in the app, pick a preset (e.g. "Customer Profitability (Top 10)") or write your own `SELECT` statement, and export the result as CSV.

## Why This Over Alternatives?

**Vs. a single-page sales dashboard tutorial project:** most portfolio dashboard projects visualize one flat CSV. This project models the full operational chain — a purchase affects inventory, a sale affects both inventory and the ledger, an expense affects the trial balance — so the numbers on every page are actually connected to each other, the way they'd need to be in a real business.

**Vs. Power BI / Tableau:** those are visualization layers over data you already have modeled elsewhere. This repository includes the data model itself (schema, relationships, generated columns, double-entry logic), which is usually the harder and less-often-demonstrated part of a BI project.

**Vs. a full ERP (Odoo, SAP Business One):** an ERP is the right tool for actually running a mill day-to-day, but it's overkill to stand up for a portfolio piece or a quick internal analytics need, and most aren't free to self-host at production scale. This project intentionally stays at "one SQLite file and one Python app" so it deploys for free on Streamlit Community Cloud with no infrastructure.

**Honest limitation:** the data here is synthetic, generated to be internally consistent rather than pulled from a real mill. If you're evaluating this as a hiring signal, treat it as a demonstration of data modeling, SQL, and Streamlit ability — not as a claim of production deployment experience.

## Known Gotchas

1. **Streamlit Community Cloud Python version mismatches.** Streamlit Cloud sometimes defaults to a newer Python than this project was built against. `runtime.txt` pins `python-3.12` for that reason — if you fork this and see dependency build failures on deploy, check that file first before anything else.
2. **Prophet installation can fail silently on some platforms** (missing C++ build tools, `pystan` issues). The Forecasting page catches this with a `try/except ImportError` and falls back to a linear-trend model automatically — you'll see which model actually ran in an info banner at the top of the page, so it's never ambiguous which one produced the numbers you're looking at.
3. **Generated SQL columns require SQLite ≥ 3.31** (the `GENERATED ALWAYS AS ... STORED` syntax used for `recovery_pct`, `total_amount`, `profit`, and `outstanding`). This ships with Python 3.9+, but if you're on an unusually old Python/SQLite bundle, table creation in `schema.sql` will fail — upgrading Python resolves it.

## Documentation

Deeper reference material lives in [`/docs`](docs/):

- [Business Requirements Document](docs/BusinessRequirements.md) — problem statement, functional/non-functional requirements, SWOT, risk register
- [Process Mapping](docs/ProcessMapping.md) — current-state vs. future-state process flows
- [Data Dictionary](docs/DataDictionary.md) — every table and column, with types and descriptions
- [KPI Definitions](docs/KPI_Definitions.md) — formula and business meaning for every metric shown in the app
- `sql/` — the query library organized by domain (inventory, suppliers, production, customers, accounting, forecasting)

## Contributing

This started as a portfolio project, but issues and pull requests are welcome — particularly around adding a real test suite and CI pipeline, since neither exists yet (see the badge note above). If you're proposing a feature, open an issue first describing the use case; for bug fixes, a PR with a short description of what broke and why the fix is correct is enough.

## License

Released under the [MIT License](LICENSE).
