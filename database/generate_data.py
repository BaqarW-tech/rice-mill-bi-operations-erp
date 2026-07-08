"""
Generates 12 months of internally-consistent synthetic data for the
Rice Mill Business Intelligence System, writes CSVs to /data, and
loads everything into a SQLite database (rice_mill.db) using schema.sql.

Run:  python database/generate_data.py
"""
import numpy as np
import pandas as pd
import sqlite3
import os
from datetime import date, timedelta

np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "database", "rice_mill.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
os.makedirs(DATA_DIR, exist_ok=True)

START_DATE = date(2025, 7, 1)
END_DATE = date(2026, 6, 30)
ALL_DAYS = pd.date_range(START_DATE, END_DATE, freq="D")

REGIONS = ["Qassim", "Al-Ahsa", "Hail", "Jazan", "Riyadh"]
VARIETIES = ["Basmati Paddy", "Sella Paddy", "Long Grain Paddy", "Broken-Prone Paddy"]

# ---------------------------------------------------------------- SUPPLIERS
N_SUPPLIERS = 18
suppliers = pd.DataFrame({
    "supplier_id": range(1, N_SUPPLIERS + 1),
    "supplier_name": [f"{r} Grain Traders {i}" for i, r in enumerate(
        np.random.choice(REGIONS, N_SUPPLIERS), start=1)],
    "region": np.random.choice(REGIONS, N_SUPPLIERS),
    "contact_phone": [f"+9665{np.random.randint(10000000,99999999)}" for _ in range(N_SUPPLIERS)],
    "onboarding_date": [START_DATE - timedelta(days=int(np.random.randint(30, 900))) for _ in range(N_SUPPLIERS)],
    "payment_terms_days": np.random.choice([7, 15, 30], N_SUPPLIERS),
    "is_active": 1,
})
# give each supplier a hidden "quality tier" that drives moisture/rejects/delay
supplier_quality = np.random.uniform(0.5, 1.0, N_SUPPLIERS)  # 1.0 = excellent

# ---------------------------------------------------------------- PURCHASES
purchase_rows = []
pid = 1
for d in ALL_DAYS:
    n_deliveries = np.random.poisson(2.2)
    for _ in range(n_deliveries):
        sup_idx = np.random.randint(N_SUPPLIERS)
        sup_id = sup_idx + 1
        q = supplier_quality[sup_idx]
        qty = max(500, np.random.normal(8000, 2500))
        price = np.random.normal(2.35, 0.15)  # SAR per kg paddy
        moisture = np.clip(np.random.normal(16 - 3 * q, 1.2), 10, 22)
        rejected = max(0, int(np.random.poisson((1 - q) * 6)))
        delay = max(0, int(np.random.normal((1 - q) * 4, 1)))
        purchase_rows.append([
            pid, d.date(), sup_id, np.random.choice(VARIETIES),
            round(qty, 1), round(price, 2), round(moisture, 1), rejected, delay
        ])
        pid += 1
purchases = pd.DataFrame(purchase_rows, columns=[
    "purchase_id", "purchase_date", "supplier_id", "paddy_variety",
    "quantity_kg", "price_per_kg", "moisture_pct", "rejected_bags", "delivery_delay_days"
])
purchases["total_amount"] = (purchases.quantity_kg * purchases.price_per_kg).round(2)

# ---------------------------------------------------------------- PRODUCTS
products = pd.DataFrame([
    (1, "Premium Basmati Rice", "Basmati", 3.10, 4.60, 8000),
    (2, "Sella Rice",           "Sella",   2.70, 4.00, 8000),
    (3, "Long Grain White Rice","Long Grain", 2.50, 3.60, 10000),
    (4, "Broken Rice",          "Broken",  1.60, 2.30, 6000),
    (5, "Rice Bran",            "By-product", 0.70, 1.20, 4000),
    (6, "Husk (fuel-grade)",     "By-product", 0.20, 0.45, 5000),
], columns=["product_id", "product_name", "category", "unit_cost", "unit_price", "min_stock_kg"])

# ---------------------------------------------------------------- PRODUCTION
# Daily production driven by prior days' purchases (simple 3-day lag pool)
prod_rows = []
prid = 1
paddy_pool = 0.0
daily_purchase_totals = purchases.groupby("purchase_date").quantity_kg.sum()
for d in ALL_DAYS:
    paddy_pool += daily_purchase_totals.get(d.date(), 0.0)
    if paddy_pool < 1000:
        continue
    process_today = min(paddy_pool, max(3000, np.random.normal(9500, 1800)))
    paddy_pool -= process_today
    recovery = np.clip(np.random.normal(0.66, 0.02), 0.58, 0.70)  # 66% typical rice recovery
    rice_out = process_today * recovery
    bran_out = process_today * np.random.uniform(0.08, 0.10)
    husk_out = process_today * np.random.uniform(0.18, 0.22)
    broken_out = rice_out * np.random.uniform(0.05, 0.12)
    rice_out -= broken_out
    shift = np.random.choice(["Day", "Night"])
    machine = np.random.choice(["MILL-01", "MILL-02"])
    prod_rows.append([prid, d.date(), round(process_today,1), round(rice_out,1),
                       round(bran_out,1), round(husk_out,1), round(broken_out,1), shift, machine])
    prid += 1
production = pd.DataFrame(prod_rows, columns=[
    "production_id", "production_date", "paddy_input_kg", "rice_output_kg",
    "bran_output_kg", "husk_output_kg", "broken_rice_kg", "shift", "machine_id"
])
production["recovery_pct"] = (production.rice_output_kg / production.paddy_input_kg * 100).round(2)

# ---------------------------------------------------------------- CUSTOMERS
N_CUSTOMERS = 25
customers = pd.DataFrame({
    "customer_id": range(1, N_CUSTOMERS + 1),
    "customer_name": [f"{t} {i}" for i, t in enumerate(
        np.random.choice(["Al Rajhi Foods", "Jeddah Wholesale", "Riyadh Mart", "Gulf Exporters", "Local Retail Co"], N_CUSTOMERS), start=1)],
    "customer_type": np.random.choice(["Wholesaler", "Retailer", "Exporter"], N_CUSTOMERS, p=[0.5, 0.3, 0.2]),
    "region": np.random.choice(REGIONS + ["Jeddah", "Dammam"], N_CUSTOMERS),
    "credit_limit": np.random.choice([50000, 100000, 200000, 300000], N_CUSTOMERS),
    "payment_terms_days": np.random.choice([15, 30, 45, 60], N_CUSTOMERS),
})
customer_risk = np.random.uniform(0.4, 1.0, N_CUSTOMERS)  # payment reliability

# ---------------------------------------------------------------- SALES
sales_rows = []
sid = 1
finished_products = products[products.category != "By-product"]["product_id"].tolist() + products["product_id"].tolist()
for d in ALL_DAYS:
    n_orders = np.random.poisson(4.5)
    for _ in range(n_orders):
        cust_idx = np.random.randint(N_CUSTOMERS)
        cust_id = cust_idx + 1
        rel = customer_risk[cust_idx]
        prod_row = products.sample(1).iloc[0]
        qty = max(200, np.random.normal(3500, 1500))
        sell_price = prod_row.unit_price * np.random.uniform(0.96, 1.06)
        cost_price = prod_row.unit_cost * np.random.uniform(0.97, 1.03)
        total = qty * sell_price
        paid = total * np.clip(np.random.normal(rel, 0.15), 0.2, 1.0)
        sales_rows.append([sid, d.date(), cust_id, int(prod_row.product_id),
                            round(qty,1), round(sell_price,2), round(cost_price,2), round(paid,2)])
        sid += 1
sales = pd.DataFrame(sales_rows, columns=[
    "sale_id","sale_date","customer_id","product_id","quantity_kg",
    "selling_price_per_kg","cost_price_per_kg","amount_paid"
])
sales["total_amount"] = (sales.quantity_kg * sales.selling_price_per_kg).round(2)
sales["profit"] = (sales.quantity_kg * (sales.selling_price_per_kg - sales.cost_price_per_kg)).round(2)
sales["outstanding"] = (sales.total_amount - sales.amount_paid).round(2)

# ---------------------------------------------------------------- INVENTORY (running balance snapshots)
inv_rows = []
iid = 1
stock = {pid_: 0.0 for pid_ in products.product_id}
daily_prod = production.set_index("production_date")
daily_sales = sales.groupby(["sale_date","product_id"]).quantity_kg.sum()

for d in ALL_DAYS:
    dd = d.date()
    if dd in daily_prod.index:
        row = daily_prod.loc[dd]
        stock[1] += row.rice_output_kg * 0.5   # split rice output into basmati/sella/longgrain roughly
        stock[2] += row.rice_output_kg * 0.3
        stock[3] += row.rice_output_kg * 0.2
        stock[4] += row.broken_rice_kg
        stock[5] += row.bran_output_kg
        stock[6] += row.husk_output_kg
    for pid_ in products.product_id:
        sold = daily_sales.get((dd, pid_), 0.0)
        stock[pid_] = max(0.0, stock[pid_] - sold)
    # weekly snapshot to keep file size reasonable
    if d.weekday() == 0:
        for pid_ in products.product_id:
            inv_rows.append([iid, dd, int(pid_), round(stock[pid_],1), "Main Warehouse"])
            iid += 1
inventory = pd.DataFrame(inv_rows, columns=[
    "inventory_id","snapshot_date","product_id","quantity_on_hand_kg","warehouse"
])

# ---------------------------------------------------------------- EMPLOYEES
employees = pd.DataFrame([
    (1,"Faisal Al-Otaibi","Mill Manager","Production",12000,date(2022,3,1)),
    (2,"Sara Al-Qahtani","Accountant","Finance",9000,date(2023,1,15)),
    (3,"Mohammed Al-Harbi","Machine Operator","Production",6000,date(2021,6,1)),
    (4,"Abdullah Al-Shammari","Machine Operator","Production",6000,date(2022,9,1)),
    (5,"Noura Al-Dossari","Sales Executive","Sales",7000,date(2023,5,1)),
    (6,"Khalid Al-Ghamdi","Warehouse Supervisor","Inventory",6500,date(2022,1,10)),
    (7,"Layla Al-Mutairi","Procurement Officer","Purchasing",6800,date(2023,2,20)),
    (8,"Yousef Al-Zahrani","Maintenance Technician","Production",5800,date(2021,11,5)),
], columns=["employee_id","employee_name","role","department","monthly_salary","hire_date"])

# ---------------------------------------------------------------- EXPENSES
exp_categories = {
    "Electricity": (18000, 3000), "Diesel": (9000, 2000), "Labour": (46300, 500),
    "Packaging": (7000, 1500), "Maintenance": (4000, 2500), "Transport": (6000, 1800),
}
exp_rows = []
eid = 1
for d in pd.date_range(START_DATE, END_DATE, freq="MS"):
    for cat, (mean, std) in exp_categories.items():
        amt = max(500, np.random.normal(mean, std))
        exp_rows.append([eid, d.date(), cat, round(amt,2), f"{cat} - {d.strftime('%B %Y')}"])
        eid += 1
expenses = pd.DataFrame(exp_rows, columns=["expense_id","expense_date","category","amount","notes"])

# ---------------------------------------------------------------- MACHINE LOGS
machine_rows = []
mlid = 1
downtime_reasons = ["Scheduled Maintenance","Power Outage","Mechanical Fault","Operator Break","Belt Replacement"]
for d in ALL_DAYS:
    for m in ["MILL-01", "MILL-02"]:
        running = np.clip(np.random.normal(14, 2.5), 0, 20)
        downtime = np.clip(24 - running - np.random.uniform(2,6), 0, 10)
        reason = np.random.choice(downtime_reasons) if downtime > 1 else None
        maint_cost = round(np.random.uniform(0,400),2) if reason == "Mechanical Fault" else 0
        machine_rows.append([mlid, d.date(), m, round(running,1), round(downtime,1), reason, maint_cost])
        mlid += 1
machine_logs = pd.DataFrame(machine_rows, columns=[
    "log_id","log_date","machine_id","running_hours","downtime_hours","downtime_reason","maintenance_cost"
])

# ---------------------------------------------------------------- ACCOUNTS (Chart of Accounts)
accounts = pd.DataFrame([
    (1,"1000","Cash & Bank","Asset"),
    (2,"1100","Accounts Receivable","Asset"),
    (3,"1200","Inventory","Asset"),
    (4,"2000","Accounts Payable","Liability"),
    (5,"3000","Owner's Equity","Equity"),
    (6,"4000","Sales Revenue","Revenue"),
    (7,"5000","Cost of Goods Sold","Expense"),
    (8,"5100","Operating Expenses","Expense"),
    (9,"5200","Salaries Expense","Expense"),
], columns=["account_id","account_code","account_name","account_type"])

# ---------------------------------------------------------------- JOURNAL ENTRIES (derived from sales/purchases/expenses)
je_rows = []
jid = 1
for _, r in sales.iterrows():
    je_rows.append([jid, r.sale_date, 2, r.total_amount, 0, f"Sale #{r.sale_id}", "Sale", r.sale_id]); jid+=1
    je_rows.append([jid, r.sale_date, 6, 0, r.total_amount, f"Sale #{r.sale_id}", "Sale", r.sale_id]); jid+=1
    je_rows.append([jid, r.sale_date, 7, r.quantity_kg*r.cost_price_per_kg, 0, f"COGS #{r.sale_id}", "Sale", r.sale_id]); jid+=1
    je_rows.append([jid, r.sale_date, 3, 0, r.quantity_kg*r.cost_price_per_kg, f"COGS #{r.sale_id}", "Sale", r.sale_id]); jid+=1
for _, r in purchases.iterrows():
    je_rows.append([jid, r.purchase_date, 3, r.total_amount, 0, f"Purchase #{r.purchase_id}", "Purchase", r.purchase_id]); jid+=1
    je_rows.append([jid, r.purchase_date, 4, 0, r.total_amount, f"Purchase #{r.purchase_id}", "Purchase", r.purchase_id]); jid+=1
for _, r in expenses.iterrows():
    je_rows.append([jid, r.expense_date, 8, r.amount, 0, r.notes, "Expense", r.expense_id]); jid+=1
    je_rows.append([jid, r.expense_date, 1, 0, r.amount, r.notes, "Expense", r.expense_id]); jid+=1
journal_entries = pd.DataFrame(je_rows, columns=[
    "entry_id","entry_date","account_id","debit","credit","description","reference_type","reference_id"
])

# ---------------------------------------------------------------- FORECASTS (placeholder — real models run in notebooks/forecasting.ipynb)
forecasts = pd.DataFrame(columns=["forecast_id","forecast_date","metric","predicted_value","lower_bound","upper_bound","model_used"])

# ---------------------------------------------------------------- WRITE CSVs
tables = {
    "suppliers": suppliers, "purchases": purchases, "production": production,
    "products": products, "inventory": inventory, "customers": customers,
    "sales": sales, "employees": employees, "expenses": expenses,
    "machine_logs": machine_logs, "accounts": accounts,
    "accounting": journal_entries, "forecast": forecasts,
}
for name, df in tables.items():
    df.to_csv(os.path.join(DATA_DIR, f"{name}.csv"), index=False)

# ---------------------------------------------------------------- LOAD SQLITE
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
conn = sqlite3.connect(DB_PATH)
with open(SCHEMA_PATH) as f:
    conn.executescript(f.read())

table_map = {
    "suppliers": suppliers, "purchases": purchases.drop(columns=["total_amount"]),
    "production": production.drop(columns=["recovery_pct"]), "products": products,
    "inventory": inventory, "customers": customers,
    "sales": sales.drop(columns=["total_amount","profit","outstanding"]),
    "employees": employees, "expenses": expenses, "machine_logs": machine_logs,
    "accounts": accounts, "journal_entries": journal_entries, "forecasts": forecasts,
}
for name, df in table_map.items():
    df.to_sql(name, conn, if_exists="append", index=False)
conn.commit()
conn.close()

print("Done.")
print({k: len(v) for k, v in tables.items()})
