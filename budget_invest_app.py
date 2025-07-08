import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# Load secrets
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]

API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

# Alpha Vantage API
def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    ts = data.get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in ts.values()]
    return (closes[0] - closes[1]) / closes[1] if len(closes) > 1 else None

# --- Sidebar Inputs ---
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income (before tax, $)", min_value=0.0, value=5000.0, step=100.0)
tax_rate = st.sidebar.slider("Tax rate (%)", 0, 50, 20)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing / Rent ($)", 0.0, 5000.0, 1200.0, 50.0)
food = st.sidebar.number_input("Food / Groceries ($)", 0.0, 5000.0, 500.0, 50.0)
transport = st.sidebar.number_input("Transport ($)", 0.0, 5000.0, 300.0, 50.0)
utilities = st.sidebar.number_input("Utilities ($)", 0.0, 5000.0, 200.0, 50.0)
entertainment = st.sidebar.number_input("Entertainment ($)", 0.0, 5000.0, 200.0, 50.0)
others = st.sidebar.number_input("Other expenses ($)", 0.0, 5000.0, 200.0, 50.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks ($)", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds ($)", 0.0, 5000.0, 300.0, 100.0)
real_estate = st.sidebar.number_input("Real estate ($)", 0.0, 5000.0, 0.0, 100.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0, 5000.0, 0.0, 100.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit ($)", 0.0, 5000.0, 0.0, 100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# --- Assumptions ---
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# --- Financial Projection ---
bal = 0
rows = []
for m in range(1, months + 1):
    bal += net_flow
    stock_val = stocks * ((1 + stock_r)**m - 1) / stock_r
    bond_val = bonds * ((1 + bond_r)**m - 1) / bond_r
    real_val = real_estate * ((1 + real_r)**m - 1) / real_r
    crypto_val = crypto * ((1 + crypto_r)**m - 1) / crypto_r
    fd_val = fixed_deposit * ((1 + fd_r)**m - 1) / fd_r
    net_worth = bal + stock_val + bond_val + real_val + crypto_val + fd_val
    rows.append({
        "Month": m, "Balance": bal,
        "Stocks": stock_val, "Bonds": bond_val,
        "RealEstate": real_val, "Crypto": crypto_val,
        "FixedDeposit": fd_val, "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# --- Main Outputs ---
st.subheader("📋 Summary")
st.metric("Gross Income", f"${income:,.2f}")
st.metric("After-tax Income", f"${after_tax_income:,.2f}")
st.metric("Total Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Expense Warning ---
if total_exp > after_tax_income * 0.7:
    st.warning("🚨 Your expenses exceed 70% of your after-tax income. Consider cutting costs!")

# --- Investment Diversification Warning ---
if stocks > total_inv * 0.7 or crypto > total_inv * 0.7:
    st.info("💡 Tip: Diversify your investments to manage risk better.")

# --- Visuals ---
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"])
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
st.plotly_chart(px.pie(names=["Housing", "Food", "Transport", "Utilities", "Entertainment", "Others"],
                       values=[housing, food, transport, utilities, entertainment, others]), use_container_width=True)

st.subheader("💼 Investment Breakdown")
st.plotly_chart(px.pie(names=["Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit"],
                       values=[stocks, bonds, real_estate, crypto, fixed_deposit]), use_container_width=True)

# --- Message to Botpress ---
prompt = f"""
Financial Summary:
• Gross Income: ${income}
• Tax Rate: {tax_rate}%
• After-Tax Income: ${after_tax_income}
• Total Expenses: ${total_exp}
• Total Investment: ${total_inv}
• Net Cash Flow: ${net_flow}/mo
• Savings Target: ${savings_target}
• Projected Net Worth: ${df['NetWorth'].iloc[-1]}
Suggest: How to reduce high expenses and rebalance investment for goal attainment.
"""

import requests

WEBHOOK_URL = "https://webhook.botpress.cloud/<your-bot-id>/test"  # ✅ Match 'test' from Botpress

headers = {
    "Content-Type": "application/json"
    # Optional: "x-bp-secret": "your-secret"  if you set one in Botpress
}

payload = {
    "text": "Financial summary: income=5000, expenses=3000, goal=10000"
}

response = requests.post(WEBHOOK_URL, headers=headers, json=payload)
print(response.status_code)
print(response.json())



