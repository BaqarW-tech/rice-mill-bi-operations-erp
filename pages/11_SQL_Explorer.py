import streamlit as st
import pandas as pd
import sqlite3
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import get_db_connection, PLOTLY_TEMPLATE

st.set_page_config(page_title="SQL Explorer", page_icon="🔎", layout="wide")
st.title("🔎 SQL Explorer")
st.caption("Run the platform's real analytical queries directly against the SQLite database")

PRESETS = {
    "Top Suppliers by Volume": """
        SELECT s.supplier_name, s.region, SUM(p.quantity_kg) AS total_quantity_kg,
               ROUND(AVG(p.price_per_kg), 2) AS avg_price_per_kg, COUNT(*) AS delivery_count
        FROM purchases p JOIN suppliers s ON s.supplier_id = p.supplier_id
        GROUP BY s.supplier_id
        ORDER BY total_quantity_kg DESC
        LIMIT 20;
    """,
    "Monthly Revenue": """
        SELECT strftime('%Y-%m', sale_date) AS month, ROUND(SUM(quantity_kg * selling_price_per_kg), 2) AS revenue
        FROM sales
        GROUP BY month
        ORDER BY month;
    """,
    "Inventory Value (Latest Snapshot)": """
        SELECT pr.product_name, i.quantity_on_hand_kg, pr.unit_cost,
               ROUND(i.quantity_on_hand_kg * pr.unit_cost, 2) AS inventory_value
        FROM inventory i JOIN products pr ON pr.product_id = i.product_id
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
        ORDER BY inventory_value DESC;
    """,
    "Customer Profitability (Top 10)": """
        SELECT c.customer_name, ROUND(SUM(s.quantity_kg * (s.selling_price_per_kg - s.cost_price_per_kg)), 2) AS total_profit
        FROM sales s JOIN customers c ON c.customer_id = s.customer_id
        GROUP BY c.customer_id
        ORDER BY total_profit DESC
        LIMIT 10;
    """,
    "Machine Downtime Summary": """
        SELECT machine_id, ROUND(SUM(running_hours),1) AS total_running_hours,
               ROUND(SUM(downtime_hours),1) AS total_downtime_hours,
               ROUND(SUM(maintenance_cost),2) AS total_maintenance_cost
        FROM machine_logs
        GROUP BY machine_id;
    """,
    "Highest Cost Centers": """
        SELECT category, ROUND(SUM(amount),2) AS total_amount
        FROM expenses
        GROUP BY category
        ORDER BY total_amount DESC;
    """,
    "Trial Balance": """
        SELECT a.account_name, a.account_type, ROUND(SUM(je.debit),2) AS total_debit, ROUND(SUM(je.credit),2) AS total_credit
        FROM journal_entries je JOIN accounts a ON a.account_id = je.account_id
        GROUP BY a.account_id
        ORDER BY a.account_code;
    """,
    "Supplier Quality Scorecard": """
        SELECT s.supplier_name, ROUND(AVG(p.moisture_pct),2) AS avg_moisture_pct,
               SUM(p.rejected_bags) AS total_rejected_bags, ROUND(AVG(p.delivery_delay_days),1) AS avg_delay_days
        FROM purchases p JOIN suppliers s ON s.supplier_id = p.supplier_id
        GROUP BY s.supplier_id
        ORDER BY avg_moisture_pct ASC;
    """,
}

choice = st.selectbox("Choose a preset query — or pick 'Custom Query' to write your own", ["Custom Query"] + list(PRESETS.keys()))

if choice == "Custom Query":
    default_sql = "SELECT * FROM sales LIMIT 20;"
    st.warning("Only SELECT statements are allowed — this is a read-only explorer.")
else:
    default_sql = PRESETS[choice].strip()

query = st.text_area("SQL Query", value=default_sql, height=180)

run = st.button("▶ Run Query", type="primary")

if run:
    stripped = query.strip().rstrip(";").strip()
    if not stripped.lower().startswith("select"):
        st.error("Only SELECT statements are permitted in this explorer.")
    else:
        try:
            conn = get_db_connection()
            result = pd.read_sql(stripped, conn)
            st.success(f"Returned {len(result):,} rows")
            st.dataframe(result, use_container_width=True, height=420)
            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Download results as CSV", csv, "query_results.csv", "text/csv")
        except Exception as e:
            st.error(f"Query failed: {e}")

st.markdown("---")
st.markdown("##### Schema Reference")
with st.expander("View available tables and columns"):
    conn = get_db_connection()
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;", conn)["name"].tolist()
    for t in tables:
        cols = pd.read_sql(f"PRAGMA table_info({t});", conn)
        st.markdown(f"**{t}**  —  {', '.join(cols['name'].tolist())}")
