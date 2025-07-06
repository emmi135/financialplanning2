import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="💸 Budget & Investment App", layout="wide")
st.title("💸 Budgeting + Investment Planner (with Savings Target)")

API_KEY = "ZGX1F29EUR1W6A6X"

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

# --- Inputs
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income ($)", min_value=0.0, value=5000.0, step=100.0)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing / Rent ($)", 0.0, 5000.0, 1200.0, 50.0)
food = st.sidebar.number_input("Food / Groceries ($)", 0.0, 5000.0, 500.0, 50.0)
transport = st.sidebar.number_input("Transport ($)", 0.0, 5000.0, 300.0, 50.0)
utilities = st.sidebar.number_input("Utilities ($)", 0.0, 5000.0, 200.0, 50.0)
entertainment = st.sidebar.number_input("Entertainment ($)", 0.0, 5000.0, 200.0, 50.0)
others = st.sidebar.number_input("Other expenses ($)", 0.0, 5000.0, 200.0, 50.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks investment ($)", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds investment ($)", 0.0, 5000.0, 300.0, 100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target at end of period ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# --- Get returns
st.sidebar.header("📡 Fetching returns...")
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
st.sidebar.write(f"Stocks monthly return: {stock_r:.2%}")
st.sidebar.write(f"Bonds monthly return: {bond_r:.2%}")

# --- Compute
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds
net_flow = income - total_exp - total_inv

bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r if stock_r else stocks * m
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r if bond_r else bonds * m
    net_worth = bal + stock_val + bond_val
    rows.append({
        "Month": m,
        "Balance": bal,
        "Stocks": stock_val,
        "Bonds": bond_val,
        "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# --- Display summary
st.subheader("📋 Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Income", f"${income:,.2f}")
col2.metric("Expenses", f"${total_exp:,.2f}")
col3.metric("Investments", f"${total_inv:,.2f}")
col4.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Emoticons
if net_flow > 0:
    st.image("https://i.imgur.com/3GvwNBf.png", width=100, caption="✅ You're saving money!")
else:
    st.image("https://i.imgur.com/8z9uX5j.png", width=100, caption="⚠ You're overspending!")

# --- Savings target check
final_net = df["NetWorth"].iloc[-1]
gap = savings_target - final_net
st.subheader("🎯 Savings Target Check")
st.write(f"Target: ${savings_target:,.2f}")
st.write(f"Projected Net Worth: ${final_net:,.2f}")
if gap > 0:
    st.warning(f"⚠ You are ${gap:,.2f} below your target.")
    st.image("https://i.imgur.com/8z9uX5j.png", width=80)
else:
    st.success(f"✅ You will exceed your target by ${-gap:,.2f}!")
    st.image("https://i.imgur.com/3GvwNBf.png", width=80)

# --- Charts
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "NetWorth"], markers=True,
              title="Balance + Investment + Net Worth Growth")
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
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
st.plotly_chart(px.pie(names=exp_s.index, values=exp_s.values, title="Expense Breakdown"), use_container_width=True)

st.subheader("💼 Investment Breakdown")
inv_s = pd.Series({
    "Stocks": stocks,
    "Bonds": bonds
})
st.plotly_chart(px.pie(names=inv_s.index, values=inv_s.values, title="Investment Breakdown"), use_container_width=True)
