import streamlit as st
import plotly.express as px
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_kg, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Production Dashboard", page_icon="⚙️", layout="wide")
st.title("⚙️ Production Dashboard")
st.caption("Milling throughput, output composition and recovery efficiency")

production = load_csv("production")

# ---------------------------------------------------------------- FILTERS
with st.sidebar:
    st.markdown("### Filters")
    date_min, date_max = production["production_date"].min(), production["production_date"].max()
    date_range = st.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)
    machines = st.multiselect("Machine", sorted(production["machine_id"].unique()),
                               default=sorted(production["machine_id"].unique()))

df = production.copy()
if len(date_range) == 2:
    start, end = date_range
    df = df[(df["production_date"].dt.date >= start) & (df["production_date"].dt.date <= end)]
df = df[df["machine_id"].isin(machines)]

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Paddy Input", fmt_kg(df["paddy_input_kg"].sum()))
c2.metric("Rice Output", fmt_kg(df["rice_output_kg"].sum()))
c3.metric("Bran Output", fmt_kg(df["bran_output_kg"].sum()))
c4.metric("Husk Output", fmt_kg(df["husk_output_kg"].sum()))
c5.metric("Avg Recovery %", f"{df['recovery_pct'].mean():.1f}%")

st.markdown("---")

row1c1, row1c2 = st.columns(2)
with row1c1:
    st.markdown("##### Daily Production (Rice Output)")
    fig = px.line(df.sort_values("production_date"), x="production_date", y="rice_output_kg",
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=[PRIMARY],
                  labels={"rice_output_kg": "kg", "production_date": "Date"})
    st.plotly_chart(fig, use_container_width=True)

with row1c2:
    st.markdown("##### Weekly Production")
    wk = df.copy()
    wk["week"] = wk["production_date"].dt.to_period("W").astype(str)
    weekly = wk.groupby("week")[["rice_output_kg", "bran_output_kg", "husk_output_kg"]].sum().reset_index()
    fig2 = px.bar(weekly, x="week", y=["rice_output_kg", "bran_output_kg", "husk_output_kg"],
                  template=PLOTLY_TEMPLATE, barmode="stack",
                  color_discrete_sequence=[PRIMARY, ACCENT, "#8B8B8B"],
                  labels={"value": "kg", "week": "Week", "variable": "Output"})
    fig2.update_layout(xaxis=dict(tickangle=-45))
    st.plotly_chart(fig2, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Monthly Production")
    mo = df.copy()
    mo["month"] = mo["production_date"].dt.to_period("M").astype(str)
    monthly = mo.groupby("month")["rice_output_kg"].sum().reset_index()
    fig3 = px.bar(monthly, x="month", y="rice_output_kg", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"rice_output_kg": "kg", "month": "Month"})
    st.plotly_chart(fig3, use_container_width=True)

with row2c2:
    st.markdown("##### Recovery % Trend (7-day rolling)")
    rt = df.sort_values("production_date").copy()
    rt["rolling"] = rt["recovery_pct"].rolling(7, min_periods=2).mean()
    fig4 = px.line(rt, x="production_date", y="rolling", template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[ACCENT], labels={"rolling": "Recovery %", "production_date": "Date"})
    fig4.add_hline(y=66, line_dash="dot", line_color=PRIMARY, annotation_text="Benchmark 66%")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("##### Recovery % Heatmap — Month × Weekday")
hm = df.copy()
hm["month"] = hm["production_date"].dt.to_period("M").astype(str)
hm["weekday"] = hm["production_date"].dt.day_name().str[:3]
weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
pivot = hm.pivot_table(index="weekday", columns="month", values="recovery_pct", aggfunc="mean").reindex(weekday_order)
fig5 = px.imshow(pivot, color_continuous_scale="Greens", template=PLOTLY_TEMPLATE, aspect="auto",
                  labels=dict(color="Recovery %"))
fig5.update_layout(height=380)
st.plotly_chart(fig5, use_container_width=True)

st.markdown("##### Raw Production Records")
st.dataframe(df.sort_values("production_date", ascending=False), use_container_width=True, height=300)
