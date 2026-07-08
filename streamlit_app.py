import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.data_loader import load_all, fmt_sar, fmt_kg, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(
    page_title="Rice Mill BI System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- STYLE
st.markdown(f"""
<style>
    .kpi-card {{
        background: white; border-radius: 10px; padding: 1.1rem 1.3rem;
        border-left: 5px solid {PRIMARY}; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .kpi-label {{ font-size: 0.82rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }}
    .kpi-value {{ font-size: 1.65rem; font-weight: 700; color: #1f2937; margin-top: .15rem; }}
    .section-header {{ margin-top: 1.8rem; margin-bottom: .5rem; }}
</style>
""", unsafe_allow_html=True)

data = load_all()
purchases, production, sales, inventory = data["purchases"], data["production"], data["sales"], data["inventory"]
products, expenses = data["products"], data["expenses"]

# ---------------------------------------------------------------- HEADER
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("### 🌾")
with col_title:
    st.title("Rice Mill Business Intelligence System")
    st.caption("End-to-end operational, financial & supply-chain analytics — Purchasing → Milling → Inventory → Sales → Accounting")

st.markdown("---")

# ---------------------------------------------------------------- EXECUTIVE SUMMARY KPIs
total_revenue = sales["total_amount"].sum()
total_cogs = (sales["quantity_kg"] * sales["cost_price_per_kg"]).sum()
total_profit = sales["profit"].sum()

latest_snapshot = inventory["snapshot_date"].max()
current_inv = inventory[inventory["snapshot_date"] == latest_snapshot].merge(products, on="product_id")
current_stock_kg = current_inv["quantity_on_hand_kg"].sum()
inventory_value = (current_inv["quantity_on_hand_kg"] * current_inv["unit_cost"]).sum()

avg_recovery = production["recovery_pct"].mean()
latest_prod_date = production["production_date"].max()
today_production = production[production["production_date"] == latest_prod_date]["rice_output_kg"].sum()

st.markdown("#### Executive Summary")
c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, "Total Revenue", fmt_sar(total_revenue)),
    (c2, "Total Profit", fmt_sar(total_profit)),
    (c3, "Inventory Value", fmt_sar(inventory_value)),
    (c4, "Current Stock", fmt_kg(current_stock_kg)),
    (c5, "Avg Recovery %", f"{avg_recovery:.1f}%"),
    (c6, "Latest Day Output", fmt_kg(today_production)),
]
for col, label, value in kpis:
    with col:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div></div>""", unsafe_allow_html=True)

st.markdown("<div class='section-header'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- REVENUE & PRODUCTION TRENDS
left, right = st.columns(2)

with left:
    st.markdown("##### Monthly Revenue & Profit")
    monthly = sales.copy()
    monthly["month"] = monthly["sale_date"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby("month")[["total_amount", "profit"]].sum().reset_index()
    fig = px.bar(monthly_agg, x="month", y=["total_amount", "profit"], barmode="group",
                 template=PLOTLY_TEMPLATE, color_discrete_sequence=[PRIMARY, ACCENT],
                 labels={"value": "SAR", "month": "Month", "variable": ""})
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02), height=360, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Daily Recovery % Trend (30-day rolling avg)")
    prod_trend = production.sort_values("production_date").copy()
    prod_trend["rolling_recovery"] = prod_trend["recovery_pct"].rolling(30, min_periods=5).mean()
    fig2 = px.line(prod_trend, x="production_date", y="rolling_recovery",
                    template=PLOTLY_TEMPLATE, color_discrete_sequence=[PRIMARY],
                    labels={"production_date": "Date", "rolling_recovery": "Recovery %"})
    fig2.add_hline(y=66, line_dash="dot", line_color=ACCENT, annotation_text="Industry benchmark ~66%")
    fig2.update_layout(height=360, margin=dict(t=30))
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------- OPERATIONS SNAPSHOT
st.markdown("##### Cost Breakdown (Latest Month)")
last_month = expenses["expense_date"].dt.to_period("M").max()
last_month_exp = expenses[expenses["expense_date"].dt.to_period("M") == last_month]
fig3 = px.pie(last_month_exp, names="category", values="amount", hole=0.45,
              template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
fig3.update_layout(height=360, margin=dict(t=10))
st.plotly_chart(fig3, use_container_width=True)

st.info("Use the sidebar to navigate to Purchase, Supplier, Production, Inventory, Sales, Customer, Cost, "
        "Machine, Financial, Forecasting and SQL Explorer dashboards.")
