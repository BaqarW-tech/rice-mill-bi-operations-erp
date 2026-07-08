import streamlit as st
import plotly.express as px
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, fmt_kg, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Purchase Dashboard", page_icon="📥", layout="wide")
st.title("📥 Purchase Dashboard")
st.caption("Paddy intake, pricing and supplier delivery trends")

purchases = load_csv("purchases")
suppliers = load_csv("suppliers")
merged = purchases.merge(suppliers, on="supplier_id")

# ---------------------------------------------------------------- FILTERS
with st.sidebar:
    st.markdown("### Filters")
    date_min, date_max = purchases["purchase_date"].min(), purchases["purchase_date"].max()
    date_range = st.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)
    varieties = st.multiselect("Paddy variety", sorted(purchases["paddy_variety"].unique()),
                                default=sorted(purchases["paddy_variety"].unique()))

if len(date_range) == 2:
    start, end = date_range
    merged = merged[(merged["purchase_date"].dt.date >= start) & (merged["purchase_date"].dt.date <= end)]
merged = merged[merged["paddy_variety"].isin(varieties)]

# ---------------------------------------------------------------- KPIs
total_purchases = merged["quantity_kg"].sum()
avg_price = merged["price_per_kg"].mean()
by_supplier_price = merged.groupby("supplier_name")["price_per_kg"].mean()
best_supplier = by_supplier_price.idxmin() if not by_supplier_price.empty else "—"
worst_supplier = by_supplier_price.idxmax() if not by_supplier_price.empty else "—"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Purchases", fmt_kg(total_purchases))
c2.metric("Average Price", f"SAR {avg_price:.2f}/kg" if avg_price == avg_price else "—")
c3.metric("Best Priced Supplier", best_supplier)
c4.metric("Highest Priced Supplier", worst_supplier)

st.markdown("---")

# ---------------------------------------------------------------- CHARTS
row1c1, row1c2 = st.columns(2)
with row1c1:
    st.markdown("##### Monthly Purchases (kg)")
    m = merged.copy()
    m["month"] = m["purchase_date"].dt.to_period("M").astype(str)
    monthly = m.groupby("month")["quantity_kg"].sum().reset_index()
    fig = px.bar(monthly, x="month", y="quantity_kg", template=PLOTLY_TEMPLATE,
                 color_discrete_sequence=[PRIMARY], labels={"quantity_kg": "kg", "month": "Month"})
    st.plotly_chart(fig, use_container_width=True)

with row1c2:
    st.markdown("##### Supplier Ranking by Volume")
    rank = merged.groupby("supplier_name")["quantity_kg"].sum().nlargest(10).reset_index()
    fig2 = px.bar(rank, x="quantity_kg", y="supplier_name", orientation="h", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[ACCENT], labels={"quantity_kg": "kg", "supplier_name": ""})
    fig2.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig2, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Average Purchase Price Trend")
    price_trend = m.groupby("month")["price_per_kg"].mean().reset_index()
    fig3 = px.line(price_trend, x="month", y="price_per_kg", markers=True, template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[PRIMARY], labels={"price_per_kg": "SAR/kg", "month": "Month"})
    st.plotly_chart(fig3, use_container_width=True)

with row2c2:
    st.markdown("##### Moisture % Distribution")
    fig4 = px.box(merged, y="moisture_pct", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT],
                  labels={"moisture_pct": "Moisture %"})
    st.plotly_chart(fig4, use_container_width=True)

row3c1, row3c2 = st.columns(2)
with row3c1:
    st.markdown("##### Purchase Trend (Daily)")
    daily = merged.groupby("purchase_date")["quantity_kg"].sum().reset_index()
    fig5 = px.area(daily, x="purchase_date", y="quantity_kg", template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[PRIMARY], labels={"quantity_kg": "kg", "purchase_date": "Date"})
    st.plotly_chart(fig5, use_container_width=True)

with row3c2:
    st.markdown("##### Purchase by Variety")
    variety_agg = merged.groupby("paddy_variety")["quantity_kg"].sum().reset_index()
    fig6 = px.pie(variety_agg, names="paddy_variety", values="quantity_kg", hole=0.45,
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")
st.markdown("##### Raw Purchase Records")
st.dataframe(merged.sort_values("purchase_date", ascending=False), use_container_width=True, height=300)
