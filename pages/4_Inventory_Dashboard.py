import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, fmt_kg, PRIMARY, ACCENT, DANGER, PLOTLY_TEMPLATE

st.set_page_config(page_title="Inventory Dashboard", page_icon="📦", layout="wide")
st.title("📦 Inventory Dashboard")
st.caption("Stock levels, valuation, turnover and dead-stock detection")

inventory = load_csv("inventory")
products = load_csv("products")
sales = load_csv("sales")

latest_date = inventory["snapshot_date"].max()
current = inventory[inventory["snapshot_date"] == latest_date].merge(products, on="product_id")
current["inventory_value"] = current["quantity_on_hand_kg"] * current["unit_cost"]
current["below_min"] = current["quantity_on_hand_kg"] < current["min_stock_kg"]

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Stock", fmt_kg(current["quantity_on_hand_kg"].sum()))
c2.metric("Inventory Value", fmt_sar(current["inventory_value"].sum()))
c3.metric("Products Below Min Stock", int(current["below_min"].sum()))
c4.metric("Snapshot Date", latest_date.strftime("%d %b %Y"))

st.markdown("---")

# ---------------------------------------------------------------- STOCK ALERTS
alerts = current[current["below_min"]][["product_name", "quantity_on_hand_kg", "min_stock_kg"]]
if not alerts.empty:
    alerts = alerts.assign(shortfall_kg=lambda d: d["min_stock_kg"] - d["quantity_on_hand_kg"])
    st.warning(f"⚠️ {len(alerts)} product(s) below minimum stock threshold")
    st.dataframe(alerts.round(1), use_container_width=True)
else:
    st.success("✅ All products are above their minimum stock threshold")

left, right = st.columns(2)
with left:
    st.markdown("##### Current Stock by Product")
    fig = px.pie(current, names="product_name", values="quantity_on_hand_kg", hole=0.45,
                 template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Inventory Value by Product")
    fig2 = px.bar(current.sort_values("inventory_value"), x="inventory_value", y="product_name",
                  orientation="h", template=PLOTLY_TEMPLATE, color_discrete_sequence=[PRIMARY],
                  labels={"inventory_value": "SAR", "product_name": ""})
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------- TURNOVER & DEAD STOCK
st.markdown("##### Stock Level Trend (Last 90 Days)")
window_start = latest_date - pd.Timedelta(days=90)
trend = inventory[inventory["snapshot_date"] >= window_start].merge(products, on="product_id")
fig3 = px.line(trend, x="snapshot_date", y="quantity_on_hand_kg", color="product_name",
               template=PLOTLY_TEMPLATE, labels={"quantity_on_hand_kg": "kg", "snapshot_date": "Date"})
st.plotly_chart(fig3, use_container_width=True)

st.markdown("##### Inventory Turnover Ratio (last 90 days) & Dead Stock")
tc1, tc2 = st.columns(2)
with tc1:
    cutoff = sales["sale_date"].max() - pd.Timedelta(days=90)
    recent_sales = sales[sales["sale_date"] >= cutoff]
    cogs_90d = (recent_sales["quantity_kg"] * recent_sales["cost_price_per_kg"]).sum()
    avg_inv_value = current["inventory_value"].sum()  # snapshot proxy
    turnover = cogs_90d / avg_inv_value if avg_inv_value else 0
    st.metric("Inventory Turnover Ratio (90d)", f"{turnover:.2f}x")
    st.caption("COGS (last 90 days) ÷ current inventory value. Higher = faster-moving stock.")

with tc2:
    sold_recent_ids = set(sales[sales["sale_date"] >= (sales["sale_date"].max() - pd.Timedelta(days=30))]["product_id"])
    dead = current[(~current["product_id"].isin(sold_recent_ids)) & (current["quantity_on_hand_kg"] > 0)]
    st.metric("Dead Stock Items (no sales in 30 days)", len(dead))
    if not dead.empty:
        st.dataframe(dead[["product_name", "quantity_on_hand_kg"]].round(1), use_container_width=True)

st.markdown("##### Full Inventory Table (Latest Snapshot)")
st.dataframe(
    current[["product_name", "category", "quantity_on_hand_kg", "min_stock_kg", "inventory_value", "warehouse"]]
    .round(1).sort_values("inventory_value", ascending=False),
    use_container_width=True, height=300
)
