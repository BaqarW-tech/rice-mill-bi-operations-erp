import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, fmt_kg, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Sales Dashboard", page_icon="💰", layout="wide")
st.title("💰 Sales Dashboard")
st.caption("Revenue, margins, customer mix and receivables")

sales = load_csv("sales")
customers = load_csv("customers")
products = load_csv("products")
merged = sales.merge(customers, on="customer_id").merge(products, on="product_id")

with st.sidebar:
    st.markdown("### Filters")
    date_min, date_max = sales["sale_date"].min(), sales["sale_date"].max()
    date_range = st.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)

if len(date_range) == 2:
    start, end = date_range
    merged = merged[(merged["sale_date"].dt.date >= start) & (merged["sale_date"].dt.date <= end)]

# ---------------------------------------------------------------- KPIs
total_revenue = merged["total_amount"].sum()
avg_price = merged["selling_price_per_kg"].mean()
margin_pct = (merged["profit"].sum() / total_revenue * 100) if total_revenue else 0
outstanding = merged["outstanding"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", fmt_sar(total_revenue))
c2.metric("Avg Selling Price", f"SAR {avg_price:.2f}/kg")
c3.metric("Profit Margin", f"{margin_pct:.1f}%")
c4.metric("Outstanding Receivables", fmt_sar(outstanding))

st.markdown("---")

row1c1, row1c2 = st.columns(2)
with row1c1:
    st.markdown("##### Monthly Revenue")
    m = merged.copy()
    m["month"] = m["sale_date"].dt.to_period("M").astype(str)
    monthly = m.groupby("month")["total_amount"].sum().reset_index()
    fig = px.bar(monthly, x="month", y="total_amount", template=PLOTLY_TEMPLATE,
                 color_discrete_sequence=[PRIMARY], labels={"total_amount": "SAR", "month": "Month"})
    st.plotly_chart(fig, use_container_width=True)

with row1c2:
    st.markdown("##### Sales by Product (Variety)")
    by_product = merged.groupby("product_name")["quantity_kg"].sum().reset_index()
    fig2 = px.pie(by_product, names="product_name", values="quantity_kg", hole=0.45,
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig2, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Top 10 Customers by Revenue")
    top_cust = merged.groupby("customer_name")["total_amount"].sum().nlargest(10).reset_index()
    fig3 = px.bar(top_cust, x="total_amount", y="customer_name", orientation="h",
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT],
                  labels={"total_amount": "SAR", "customer_name": ""})
    fig3.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig3, use_container_width=True)

with row2c2:
    st.markdown("##### Sales by Customer Type")
    by_type = merged.groupby("customer_type")["total_amount"].sum().reset_index()
    fig4 = px.bar(by_type, x="customer_type", y="total_amount", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"total_amount": "SAR", "customer_type": ""})
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("##### Profit Margin Trend")
m["profit_margin_pct"] = None
monthly_margin = m.groupby("month").apply(
    lambda d: d["profit"].sum() / d["total_amount"].sum() * 100 if d["total_amount"].sum() else 0
).reset_index(name="margin_pct")
fig5 = px.line(monthly_margin, x="month", y="margin_pct", markers=True, template=PLOTLY_TEMPLATE,
               color_discrete_sequence=[PRIMARY], labels={"margin_pct": "Margin %", "month": "Month"})
st.plotly_chart(fig5, use_container_width=True)

st.markdown("##### Raw Sales Records")
st.dataframe(merged.sort_values("sale_date", ascending=False)
             [["sale_date","customer_name","product_name","quantity_kg","selling_price_per_kg","total_amount","profit","outstanding"]],
             use_container_width=True, height=300)
