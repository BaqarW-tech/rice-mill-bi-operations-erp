import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, PRIMARY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="Forecasting", page_icon="🔮", layout="wide")
st.title("🔮 Forecasting")
st.caption("Production, sales, revenue and cash-flow forecasts using Prophet (falls back to a linear-trend model if Prophet isn't available)")

METRICS = {
    "Production (Rice Output kg)": ("production", "production_date", "rice_output_kg", "sum"),
    "Sales Volume (kg)": ("sales", "sale_date", "quantity_kg", "sum"),
    "Revenue (SAR)": ("sales", "sale_date", "total_amount", "sum"),
}

c1, c2 = st.columns([2, 1])
with c1:
    metric_label = st.selectbox("Metric to forecast", list(METRICS.keys()) + ["Cash Flow (Net Daily, SAR)"])
with c2:
    horizon = st.slider("Forecast horizon (days)", 7, 90, 30)

# ---------------------------------------------------------------- BUILD TIME SERIES
if metric_label == "Cash Flow (Net Daily, SAR)":
    sales = load_csv("sales"); purchases = load_csv("purchases"); expenses = load_csv("expenses")
    cash_in = sales.groupby("sale_date")["amount_paid"].sum()
    cash_out_p = purchases.groupby("purchase_date")["total_amount"].sum()
    cash_out_e = expenses.groupby("expense_date")["amount"].sum()
    all_days = pd.date_range(min(cash_in.index.min(), cash_out_p.index.min()),
                              max(cash_in.index.max(), cash_out_p.index.max()))
    ts = pd.DataFrame(index=all_days)
    ts["y"] = cash_in.reindex(all_days, fill_value=0) - cash_out_p.reindex(all_days, fill_value=0) - cash_out_e.reindex(all_days, fill_value=0)
    ts = ts.reset_index().rename(columns={"index": "ds"})
else:
    table, date_col, value_col, agg = METRICS[metric_label]
    df = load_csv(table)
    ts = df.groupby(date_col)[value_col].agg(agg).reset_index().rename(columns={date_col: "ds", value_col: "y"})

ts = ts.sort_values("ds").reset_index(drop=True)

# ---------------------------------------------------------------- FORECAST
model_used = None
forecast_df = None

try:
    from prophet import Prophet
    m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(ts.rename(columns={"ds": "ds", "y": "y"}))
    future = m.make_future_dataframe(periods=horizon)
    fc = m.predict(future)
    forecast_df = fc[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    model_used = "Prophet"
except Exception:
    # Fallback: simple linear trend + 7-day seasonal average, with a widening confidence band
    ts2 = ts.copy()
    ts2["t"] = np.asarray((ts2["ds"] - ts2["ds"].min()).dt.days, dtype=float)
    coeffs = np.polyfit(ts2["t"], ts2["y"], 1)
    slope, intercept = coeffs[0], coeffs[1]
    resid_std = (ts2["y"] - (slope * ts2["t"] + intercept)).std()

    future_dates = pd.date_range(ts2["ds"].max() + pd.Timedelta(days=1), periods=horizon)
    future_t = np.asarray((future_dates - ts2["ds"].min()).days, dtype=float)
    yhat_future = slope * future_t + intercept
    yhat_hist = slope * ts2["t"].to_numpy(dtype=float) + intercept

    all_ds = pd.concat([ts2["ds"], pd.Series(future_dates)]).reset_index(drop=True)
    all_yhat = np.concatenate([yhat_hist.values, yhat_future])
    band = resid_std * np.sqrt(np.concatenate([np.ones(len(ts2)), np.arange(1, horizon + 1)]))
    forecast_df = pd.DataFrame({
        "ds": all_ds, "yhat": all_yhat,
        "yhat_lower": all_yhat - 1.96 * band, "yhat_upper": all_yhat + 1.96 * band,
    })
    model_used = "Linear trend (fallback — install `prophet` for seasonal forecasting)"

st.info(f"Model used: **{model_used}**")

# ---------------------------------------------------------------- CHART
fig = go.Figure()
fig.add_trace(go.Scatter(x=ts["ds"], y=ts["y"], mode="lines", name="Actual",
                          line=dict(color=PRIMARY)))
future_part = forecast_df[forecast_df["ds"] > ts["ds"].max()]
fig.add_trace(go.Scatter(x=forecast_df["ds"], y=forecast_df["yhat"], mode="lines", name="Forecast",
                          line=dict(color=ACCENT, dash="dash")))
fig.add_trace(go.Scatter(
    x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
    y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
    fill="toself", fillcolor="rgba(212,160,23,0.15)", line=dict(color="rgba(0,0,0,0)"),
    name="Confidence Interval", showlegend=True
))
fig.update_layout(template=PLOTLY_TEMPLATE, height=480, legend=dict(orientation="h", y=1.05))
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
c1.metric("Next-period forecast", f"{future_part['yhat'].iloc[0]:,.0f}" if not future_part.empty else "—")
c2.metric(f"{horizon}-day forecast total", f"{future_part['yhat'].sum():,.0f}")
c3.metric("Historical daily average", f"{ts['y'].mean():,.0f}")

st.markdown("##### Forecast Data")
st.dataframe(future_part.round(1), use_container_width=True, height=280)

st.caption(
    "Time-series extracts for these forecasts mirror `sql/forecasting_queries.sql`. "
    "`notebooks/forecasting.ipynb` contains the full model comparison (Prophet vs. ARIMA vs. linear regression)."
)
