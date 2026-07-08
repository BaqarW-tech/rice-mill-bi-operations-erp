import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Cost Dashboard", page_icon="🧮", layout="wide")
st.title("🧮 Cost Dashboard")
st.caption("Operating cost breakdown, cost per ton, profit per ton and variance")

expenses = load_csv("expenses")
production = load_csv("production")
sales = load_csv("sales")

expenses["month"] = expenses["expense_date"].dt.to_period("M").astype(str)
production["month"] = production["production_date"].dt.to_period("M").astype(str)
sales["month"] = sales["sale_date"].dt.to_period("M").astype(str)

monthly_cost = expenses.groupby(["month", "category"])["amount"].sum().reset_index()
monthly_cost_total = expenses.groupby("month")["amount"].sum().reset_index()
monthly_tons = production.groupby("month")["rice_output_kg"].sum().reset_index()
monthly_tons["tons"] = monthly_tons["rice_output_kg"] / 1000
monthly_profit = sales.groupby("month")["profit"].sum().reset_index()

cost_per_ton_df = monthly_cost_total.merge(monthly_tons, on="month")
cost_per_ton_df["cost_per_ton"] = cost_per_ton_df["amount"] / cost_per_ton_df["tons"]

profit_per_ton_df = monthly_profit.merge(monthly_tons, on="month")
profit_per_ton_df["profit_per_ton"] = profit_per_ton_df["profit"] / profit_per_ton_df["tons"]

# ---------------------------------------------------------------- KPIs
total_cost = expenses["amount"].sum()
avg_cost_per_ton = cost_per_ton_df["cost_per_ton"].mean()
avg_profit_per_ton = profit_per_ton_df["profit_per_ton"].mean()
top_category = expenses.groupby("category")["amount"].sum().idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Operating Cost", fmt_sar(total_cost))
c2.metric("Avg Cost / Ton", f"SAR {avg_cost_per_ton:,.0f}")
c3.metric("Avg Profit / Ton", f"SAR {avg_profit_per_ton:,.0f}")
c4.metric("Largest Cost Category", top_category)

st.markdown("---")

left, right = st.columns(2)
with left:
    st.markdown("##### Cost Breakdown by Category")
    by_cat = expenses.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
    fig = px.bar(by_cat, x="category", y="amount", template=PLOTLY_TEMPLATE,
                 color_discrete_sequence=[PRIMARY], labels={"amount": "SAR", "category": ""})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Cost Composition")
    fig2 = px.pie(by_cat, names="category", values="amount", hole=0.45,
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("##### Monthly Cost Trend by Category")
fig3 = px.bar(monthly_cost, x="month", y="amount", color="category", template=PLOTLY_TEMPLATE,
              barmode="stack", labels={"amount": "SAR", "month": "Month", "category": "Category"})
st.plotly_chart(fig3, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Cost per Ton Trend")
    fig4 = px.line(cost_per_ton_df, x="month", y="cost_per_ton", markers=True, template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[PRIMARY], labels={"cost_per_ton": "SAR/ton", "month": "Month"})
    st.plotly_chart(fig4, use_container_width=True)

with row2c2:
    st.markdown("##### Profit per Ton Trend")
    fig5 = px.line(profit_per_ton_df, x="month", y="profit_per_ton", markers=True, template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[ACCENT], labels={"profit_per_ton": "SAR/ton", "month": "Month"})
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("##### Month-over-Month Cost Variance by Category")
pivot = monthly_cost.pivot(index="month", columns="category", values="amount").fillna(0)
variance = pivot.pct_change().round(3) * 100
st.dataframe(variance.style.format("{:+.1f}%", na_rep="—"), use_container_width=True, height=300)
st.caption("Positive values = cost increased vs. prior month.")
