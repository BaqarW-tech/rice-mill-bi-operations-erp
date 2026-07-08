"""
Shared utilities for the Rice Mill BI Streamlit app:
- cached CSV loaders (fast, no DB round-trips per page)
- a cached SQLite connection for the SQL Explorer page
- small KPI/formatting helpers reused across dashboards
"""
import os
import sqlite3
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "database", "rice_mill.db")

PRIMARY = "#1B5E3A"      # deep rice-green
ACCENT = "#D4A017"       # paddy-gold
DANGER = "#B3261E"
NEUTRAL = "#5A6B57"

PLOTLY_TEMPLATE = "plotly_white"


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{name}.csv")
    df = pd.read_csv(path)
    for col in df.columns:
        if col.endswith("_date") or col == "snapshot_date":
            df[col] = pd.to_datetime(df[col])
    return df


@st.cache_resource(show_spinner=False)
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def run_sql(query: str) -> pd.DataFrame:
    conn = get_db_connection()
    return pd.read_sql(query, conn)


def fmt_sar(x: float) -> str:
    if x is None or pd.isna(x):
        return "SAR 0"
    if abs(x) >= 1_000_000:
        return f"SAR {x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"SAR {x/1_000:,.1f}K"
    return f"SAR {x:,.0f}"


def fmt_kg(x: float) -> str:
    if x is None or pd.isna(x):
        return "0 kg"
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:,.2f}M kg"
    if abs(x) >= 1_000:
        return f"{x/1_000:,.1f}K kg"
    return f"{x:,.0f} kg"


def load_all():
    """Convenience loader for the Home page executive summary."""
    return {
        "suppliers": load_csv("suppliers"),
        "purchases": load_csv("purchases"),
        "production": load_csv("production"),
        "products": load_csv("products"),
        "inventory": load_csv("inventory"),
        "customers": load_csv("customers"),
        "sales": load_csv("sales"),
        "employees": load_csv("employees"),
        "expenses": load_csv("expenses"),
        "machine_logs": load_csv("machine_logs"),
        "accounting": load_csv("accounting"),
    }
