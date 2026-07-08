import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, PRIMARY, ACCENT, DANGER, PLOTLY_TEMPLATE

st.set_page_config(page_title="Machine Dashboard", page_icon="🛠️", layout="wide")
st.title("🛠️ Machine Dashboard")
st.caption("Running hours, downtime, maintenance cost and utilization")

logs = load_csv("machine_logs")
logs["total_hours"] = logs["running_hours"] + logs["downtime_hours"]
logs["utilization_pct"] = (logs["running_hours"] / logs["total_hours"].replace(0, pd.NA) * 100)

with st.sidebar:
    st.markdown("### Filters")
    machines = st.multiselect("Machine", sorted(logs["machine_id"].unique()),
                               default=sorted(logs["machine_id"].unique()))

df = logs[logs["machine_id"].isin(machines)]

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Running Hours", f"{df['running_hours'].sum():,.0f} hrs")
c2.metric("Total Downtime Hours", f"{df['downtime_hours'].sum():,.0f} hrs")
c3.metric("Maintenance Cost", fmt_sar(df["maintenance_cost"].sum()))
c4.metric("Avg Utilization %", f"{df['utilization_pct'].mean():.1f}%")

st.markdown("---")

left, right = st.columns(2)
with left:
    st.markdown("##### Running Hours by Machine")
    by_machine = df.groupby("machine_id")["running_hours"].sum().reset_index()
    fig = px.bar(by_machine, x="machine_id", y="running_hours", template=PLOTLY_TEMPLATE,
                 color_discrete_sequence=[PRIMARY], labels={"running_hours": "Hours", "machine_id": "Machine"})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("##### Downtime Reasons")
    reasons = df.dropna(subset=["downtime_reason"]).groupby("downtime_reason")["downtime_hours"].sum().reset_index()
    fig2 = px.pie(reasons, names="downtime_reason", values="downtime_hours", hole=0.45,
                  template=PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig2, use_container_width=True)

row2c1, row2c2 = st.columns(2)
with row2c1:
    st.markdown("##### Utilization % Trend")
    dtrend = df.copy()
    dtrend["month"] = dtrend["log_date"].dt.to_period("M").astype(str)
    monthly_util = dtrend.groupby(["month", "machine_id"])["utilization_pct"].mean().reset_index()
    fig3 = px.line(monthly_util, x="month", y="utilization_pct", color="machine_id", markers=True,
                   template=PLOTLY_TEMPLATE, labels={"utilization_pct": "Utilization %", "month": "Month"})
    st.plotly_chart(fig3, use_container_width=True)

with row2c2:
    st.markdown("##### Maintenance Cost by Machine")
    maint = df.groupby("machine_id")["maintenance_cost"].sum().reset_index()
    fig4 = px.bar(maint, x="machine_id", y="maintenance_cost", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[DANGER], labels={"maintenance_cost": "SAR", "machine_id": "Machine"})
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("##### Daily Downtime Hours")
fig5 = px.area(df.sort_values("log_date"), x="log_date", y="downtime_hours", color="machine_id",
               template=PLOTLY_TEMPLATE, labels={"downtime_hours": "Hours", "log_date": "Date"})
st.plotly_chart(fig5, use_container_width=True)

st.markdown("##### Raw Machine Logs")
st.dataframe(df.sort_values("log_date", ascending=False), use_container_width=True, height=300)
