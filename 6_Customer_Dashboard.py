import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, PRIMARY, ACCENT, DANGER, PLOTLY_TEMPLATE

st.set_page_config(page_title="Customer Dashboard", page_icon="🧾", layout="wide")
st.title("🧾 Customer Dashboard")
st.caption("Ranking, payment behavior, purchase frequency and risk")

sales = load_csv("sales")
customers = load_csv("customers")
merged = sales.merge(customers, on="customer_id")

# ---------------------------------------------------------------- CUSTOMER SCORECARD
span_days = (merged.groupby("customer_id")["sale_date"].max() - merged.groupby("customer_id")["sale_date"].min()).dt.days.clip(lower=1)
agg = merged.groupby(["customer_id", "customer_name", "customer_type"]).agg(
    total_revenue=("total_amount", "sum"),
    total_profit=("profit", "sum"),
    total_outstanding=("outstanding", "sum"),
    total_paid=("amount_paid", "sum"),
    order_count=("sale_id", "count"),
    first_order=("sale_date", "min"),
    last_order=("sale_date", "max"),
).reset_index()
agg["span_days"] = (agg["last_order"] - agg["first_order"]).dt.days.clip(lower=1)
agg["orders_per_month"] = agg["order_count"] / agg["span_days"] * 30
agg["pct_collected"] = (agg["total_paid"] / agg["total_revenue"] * 100).round(1)
agg["risk_score"] = (100 - agg["pct_collected"]).round(1)
agg = agg.sort_values("total_revenue", ascending=False)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Customers", len(agg))
c2.metric("Total Outstanding", fmt_sar(agg["total_outstanding"].sum()))
c3.metric("Avg Collection Rate", f"{agg['pct_collected'].mean():.1f}%")
c4.metric("Highest-Risk Customer", agg.sort_values('risk_score', ascending=False).iloc[0]["customer_name"])

st.markdown("---")

left, right = st.columns(2)
with left:
    st.markdown("##### Customer Ranking by Revenue")
    top15 = agg.head(15)
    fig = px.bar(top15, x="total_revenue", y="customer_name", orientation="h",
                 template=PLOTLY_TEMPLATE, color_discrete_sequence=[PRIMARY],
                 labels={"total_revenue": "SAR", "customer_name": ""})
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Profit Contribution by Customer")
    top_profit = agg.nlargest(15, "total_profit")
    fig2 = px.bar(top_profit, x="total_profit", y="customer_name", orientation="h",
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT],
                  labels={"total_profit": "SAR", "customer_name": ""})
    fig2.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig2, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Outstanding Balance by Customer")
    outstanding_sorted = agg[agg["total_outstanding"] > 0].nlargest(15, "total_outstanding")
    fig3 = px.bar(outstanding_sorted, x="customer_name", y="total_outstanding", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[DANGER], labels={"total_outstanding": "SAR", "customer_name": ""})
    fig3.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)

with row2c2:
    st.markdown("##### Purchase Frequency (orders/month)")
    freq_sorted = agg.nlargest(15, "orders_per_month")
    fig4 = px.bar(freq_sorted, x="customer_name", y="orders_per_month", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"orders_per_month": "Orders/Month", "customer_name": ""})
    fig4.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("##### Risk Score Distribution (Collection Risk)")
fig5 = px.bar(agg.sort_values("risk_score", ascending=False).head(15), x="customer_name", y="risk_score",
              template=PLOTLY_TEMPLATE, color="risk_score", color_continuous_scale="Reds",
              labels={"risk_score": "Risk Score (0-100)", "customer_name": ""})
fig5.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
st.plotly_chart(fig5, use_container_width=True)

st.markdown("##### Full Customer Scorecard")
st.dataframe(
    agg[["customer_name","customer_type","total_revenue","total_profit","total_outstanding",
         "pct_collected","orders_per_month","risk_score"]].round(1).rename(columns={
        "customer_name":"Customer","customer_type":"Type","total_revenue":"Revenue (SAR)",
        "total_profit":"Profit (SAR)","total_outstanding":"Outstanding (SAR)",
        "pct_collected":"Collected %","orders_per_month":"Orders/Month","risk_score":"Risk Score"
    }), use_container_width=True, height=350
)
