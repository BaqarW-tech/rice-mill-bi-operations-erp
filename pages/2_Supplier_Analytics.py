import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Supplier Analytics", page_icon="🚚", layout="wide")
st.title("🚚 Supplier Analytics")
st.caption("Quality scoring, reliability and price comparison across the supplier base")

purchases = load_csv("purchases")
suppliers = load_csv("suppliers")
merged = purchases.merge(suppliers, on="supplier_id")

# ---------------------------------------------------------------- SCORECARD
scorecard = merged.groupby("supplier_name").agg(
    avg_moisture=("moisture_pct", "mean"),
    total_rejected=("rejected_bags", "sum"),
    deliveries=("purchase_id", "count"),
    avg_delay=("delivery_delay_days", "mean"),
    avg_price=("price_per_kg", "mean"),
    total_volume=("quantity_kg", "sum"),
).reset_index()
scorecard["reject_rate"] = scorecard["total_rejected"] / scorecard["deliveries"]

# Composite score: lower moisture/reject/delay -> higher score (0-100 scale, min-max normalized)
def normalize_inverse(s):
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(100, index=s.index)
    return 100 * (1 - (s - s.min()) / rng)

scorecard["moisture_score"] = normalize_inverse(scorecard["avg_moisture"])
scorecard["reject_score"] = normalize_inverse(scorecard["reject_rate"])
scorecard["delay_score"] = normalize_inverse(scorecard["avg_delay"])
scorecard["supplier_score"] = (
    0.4 * scorecard["moisture_score"] + 0.3 * scorecard["reject_score"] + 0.3 * scorecard["delay_score"]
).round(1)
scorecard = scorecard.sort_values("supplier_score", ascending=False)

top_supplier = scorecard.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Top-Scoring Supplier", top_supplier["supplier_name"], f"{top_supplier['supplier_score']:.1f}/100")
c2.metric("Avg Moisture (fleet)", f"{scorecard['avg_moisture'].mean():.1f}%")
c3.metric("Avg Delivery Delay", f"{scorecard['avg_delay'].mean():.1f} days")
c4.metric("Total Rejected Bags", f"{int(scorecard['total_rejected'].sum())}")

st.markdown("---")

left, right = st.columns([1, 1])
with left:
    st.markdown("##### Supplier Ranking by Composite Score")
    fig = px.bar(scorecard.head(15), x="supplier_score", y="supplier_name", orientation="h",
                 template=PLOTLY_TEMPLATE, color="supplier_score", color_continuous_scale="Greens",
                 labels={"supplier_score": "Score /100", "supplier_name": ""})
    fig.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Radar: Top 5 Suppliers")
    top5 = scorecard.head(5)
    categories = ["Moisture Score", "Reject Score", "Delay Score"]
    fig2 = go.Figure()
    for _, row in top5.iterrows():
        fig2.add_trace(go.Scatterpolar(
            r=[row["moisture_score"], row["reject_score"], row["delay_score"]],
            theta=categories, fill="toself", name=row["supplier_name"]
        ))
    fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        template=PLOTLY_TEMPLATE, height=420, showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=-0.1))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("##### Price Comparison by Supplier")
fig3 = px.box(merged, x="supplier_name", y="price_per_kg", template=PLOTLY_TEMPLATE,
              color_discrete_sequence=[PRIMARY], labels={"price_per_kg": "SAR/kg", "supplier_name": ""})
fig3.update_layout(xaxis_tickangle=-45, height=420)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("##### Full Performance Table")
display_cols = ["supplier_name", "supplier_score", "avg_moisture", "reject_rate", "avg_delay", "avg_price", "total_volume", "deliveries"]
st.dataframe(
    scorecard[display_cols].round(2).rename(columns={
        "supplier_name": "Supplier", "supplier_score": "Score", "avg_moisture": "Avg Moisture %",
        "reject_rate": "Reject Rate (bags/delivery)", "avg_delay": "Avg Delay (days)",
        "avg_price": "Avg Price (SAR/kg)", "total_volume": "Total Volume (kg)", "deliveries": "Deliveries"
    }),
    use_container_width=True, height=400
)
