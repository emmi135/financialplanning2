import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="💸 Budget & Investment App", layout="wide")
st.title("💸 Budgeting + API-Powered Investment Planner")

# --- Alpha Vantage API key (you can replace with your own)
API_KEY = "ZGX1F29EUR1W6A6X"

# --- Helper: Fetch monthly return
def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    ts = data.get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in ts.values()]
    if len(closes) < 2:
        return None
    monthly_return = (closes[0] - closes[1]) / closes[1]
    return monthly_return

# --- Sidebar inputs
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income ($)", min_value=0.0, value=5000.0, step=100.0)

st.sidebar.header("📌 Monthly Expenses")
housing = st.sidebar.number_input("Housing / Rent ($)", min_value=0.0, value=1200.0, step=50.0)
food = st.sidebar.number_input("Food / Groceries ($)", min_value=0.0, value=500.0, step=50.0)
transport = st.sidebar.number_input("Transport ($)", min_value=0.0, value=300.0, step=50.0)
utilities = st.sidebar.number_input("Utilities ($)", min_value=0.0, value=200.0, step=50.0)
entertainment = st.sidebar.number_input("Entertainment ($)", min_value=0.0, value=200.0, step=50.0)
others = st.sidebar.number_input("Other expenses ($)", min_value=0.0, value=200.0, step=50.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks investment ($)", min_value=0.0, value=500.0, step=100.0)
bonds = st.sidebar.number_input("Bonds investment ($)", min_value=0.0, value=300.0, step=100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)

# --- Fetch returns
st.sidebar.header("📡 Fetching market data...")
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003

st.sidebar.write(f"📈 Estimated Stock Monthly Return: {stock_r:.2%}")
st.sidebar.write(f"📈 Estimated Bond Monthly Return: {bond_r:.2%}")

# --- Projection
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds
net_flow = income - total_exp - total_inv

bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r if stock_r else stocks * m
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r if bond_r else bonds * m
    rows.append({
        "Month": m,
        "Balance": bal,
        "Stocks": stock_val,
        "Bonds": bond_val
    })
df = pd.DataFrame(rows)

# --- Display summary
st.subheader("📋 Summary")
st.metric("Income", f"${income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Charts
st.subheader("📈 Projection Chart")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds"], markers=True,
              title="Balance + Investment Growth")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
exp_s = pd.Series({
    "Housing": housing,
    "Food": food,
    "Transport": transport,
    "Utilities": utilities,
    "Entertainment": entertainment,
    "Others": others
})
fig2 = px.pie(names=exp_s.index, values=exp_s.values)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("💼 Investment Breakdown")
inv_s = pd.Series({
    "Stocks": stocks,
    "Bonds": bonds
})
fig3 = px.pie(names=inv_s.index, values=inv_s.values)
st.plotly_chart(fig3, use_container_width=True)
