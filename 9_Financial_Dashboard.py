import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_csv, fmt_sar, PRIMARY, ACCENT, DANGER, PLOTLY_TEMPLATE

st.set_page_config(page_title="Financial Dashboard", page_icon="🏦", layout="wide")
st.title("🏦 Financial Dashboard")
st.caption("Automatically generated from double-entry journal postings — Journal, Ledger, Trial Balance, P&L, Balance Sheet, Cash Flow")

journal = load_csv("accounting")  # journal_entries
accounts = load_csv("accounts")
journal = journal.merge(accounts, on="account_id")

tab_journal, tab_ledger, tab_tb, tab_pl, tab_bs, tab_cf = st.tabs(
    ["📓 Journal", "📒 Ledger", "⚖️ Trial Balance", "📈 P&L", "🧾 Balance Sheet", "💵 Cash Flow"]
)

# ---------------------------------------------------------------- JOURNAL
with tab_journal:
    st.markdown("##### General Journal (chronological entries)")
    ref_filter = st.multiselect("Reference type", sorted(journal["reference_type"].unique()),
                                 default=sorted(journal["reference_type"].unique()))
    jf = journal[journal["reference_type"].isin(ref_filter)].sort_values("entry_date", ascending=False)
    st.dataframe(
        jf[["entry_date", "account_name", "debit", "credit", "description", "reference_type"]].head(500),
        use_container_width=True, height=450
    )
    st.caption(f"Showing latest 500 of {len(jf):,} entries.")

# ---------------------------------------------------------------- LEDGER
with tab_ledger:
    st.markdown("##### General Ledger — select an account")
    acct_name = st.selectbox("Account", sorted(accounts["account_name"].unique()))
    ledger = journal[journal["account_name"] == acct_name].sort_values("entry_date").copy()
    ledger["running_balance"] = (ledger["debit"] - ledger["credit"]).cumsum()
    fig = px.line(ledger, x="entry_date", y="running_balance", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"running_balance": "SAR", "entry_date": "Date"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(ledger[["entry_date", "debit", "credit", "running_balance", "description"]],
                 use_container_width=True, height=350)

# ---------------------------------------------------------------- TRIAL BALANCE
with tab_tb:
    st.markdown("##### Trial Balance")
    tb = journal.groupby(["account_name", "account_type"]).agg(
        total_debit=("debit", "sum"), total_credit=("credit", "sum")
    ).reset_index()
    tb["balance"] = tb["total_debit"] - tb["total_credit"]
    st.dataframe(tb.round(2), use_container_width=True, height=350)
    diff = tb["total_debit"].sum() - tb["total_credit"].sum()
    if abs(diff) < 0.01:
        st.success(f"✅ Trial balance is balanced (debits = credits = {fmt_sar(tb['total_debit'].sum())})")
    else:
        st.error(f"⚠️ Trial balance does not balance — difference of {fmt_sar(diff)}")

# ---------------------------------------------------------------- P&L
with tab_pl:
    st.markdown("##### Profit & Loss Statement")
    revenue = journal[journal["account_name"] == "Sales Revenue"]["credit"].sum() - journal[journal["account_name"] == "Sales Revenue"]["debit"].sum()
    cogs = journal[journal["account_name"] == "Cost of Goods Sold"]["debit"].sum() - journal[journal["account_name"] == "Cost of Goods Sold"]["credit"].sum()
    opex = journal[journal["account_name"] == "Operating Expenses"]["debit"].sum() - journal[journal["account_name"] == "Operating Expenses"]["credit"].sum()
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", fmt_sar(revenue))
    c2.metric("COGS", fmt_sar(cogs))
    c3.metric("Gross Profit", fmt_sar(gross_profit))
    c4.metric("Net Profit", fmt_sar(net_profit))

    waterfall = pd.DataFrame({
        "stage": ["Revenue", "COGS", "Gross Profit", "OpEx", "Net Profit"],
        "value": [revenue, -cogs, gross_profit, -opex, net_profit],
    })
    fig2 = px.bar(waterfall, x="stage", y="value", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"value": "SAR", "stage": ""})
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Monthly P&L Trend")
    jm = journal.copy()
    jm["month"] = jm["entry_date"].dt.to_period("M").astype(str)
    monthly_rev = jm[jm["account_name"] == "Sales Revenue"].groupby("month")["credit"].sum()
    monthly_cogs = jm[jm["account_name"] == "Cost of Goods Sold"].groupby("month")["debit"].sum()
    monthly_opex = jm[jm["account_name"] == "Operating Expenses"].groupby("month")["debit"].sum()
    pl_trend = pd.DataFrame({"revenue": monthly_rev, "cogs": monthly_cogs, "opex": monthly_opex}).fillna(0)
    pl_trend["net_profit"] = pl_trend["revenue"] - pl_trend["cogs"] - pl_trend["opex"]
    pl_trend = pl_trend.reset_index()
    fig3 = px.line(pl_trend, x="month", y=["revenue", "net_profit"], markers=True, template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[PRIMARY, ACCENT], labels={"value": "SAR", "month": "Month"})
    st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------- BALANCE SHEET
with tab_bs:
    st.markdown("##### Balance Sheet Snapshot")
    bs = journal.groupby("account_type").apply(lambda d: d["debit"].sum() - d["credit"].sum()).reset_index(name="net_balance")
    assets = bs[bs["account_type"] == "Asset"]["net_balance"].sum()
    liabilities = -bs[bs["account_type"] == "Liability"]["net_balance"].sum()
    equity_and_earnings = assets - liabilities  # plug for retained earnings

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assets", fmt_sar(assets))
    c2.metric("Total Liabilities", fmt_sar(liabilities))
    c3.metric("Equity (incl. retained earnings)", fmt_sar(equity_and_earnings))

    detail = journal.groupby(["account_type", "account_name"]).apply(
        lambda d: d["debit"].sum() - d["credit"].sum()).reset_index(name="balance")
    detail = detail[detail["account_type"].isin(["Asset", "Liability"])]
    fig4 = px.bar(detail, x="account_name", y="balance", color="account_type", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY, DANGER], labels={"balance": "SAR", "account_name": ""})
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("Equity is presented as a balancing plug (Assets − Liabilities) since this synthetic ledger doesn't seed opening capital.")

# ---------------------------------------------------------------- CASH FLOW
with tab_cf:
    st.markdown("##### Cash Flow (Cash & Bank account movements)")
    cash = journal[journal["account_name"] == "Cash & Bank"].sort_values("entry_date").copy()
    cash["net_flow"] = cash["debit"] - cash["credit"]
    cash["month"] = cash["entry_date"].dt.to_period("M").astype(str)
    monthly_cf = cash.groupby("month")["net_flow"].sum().reset_index()
    monthly_cf["cumulative"] = monthly_cf["net_flow"].cumsum()

    fig5 = px.bar(monthly_cf, x="month", y="net_flow", template=PLOTLY_TEMPLATE,
                  color_discrete_sequence=[PRIMARY], labels={"net_flow": "SAR", "month": "Month"})
    st.plotly_chart(fig5, use_container_width=True)

    fig6 = px.line(monthly_cf, x="month", y="cumulative", markers=True, template=PLOTLY_TEMPLATE,
                   color_discrete_sequence=[ACCENT], labels={"cumulative": "Cumulative SAR", "month": "Month"})
    st.plotly_chart(fig6, use_container_width=True)
