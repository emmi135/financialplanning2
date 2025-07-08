import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import json

# Load secrets
genai_key = st.secrets["gemini"]["api_key"]
openrouter_key = st.secrets["openrouter"]["api_key"]
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]  # This is your Botpress Bot ID
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Webhook-Based Botpress AI)")

# Alpha Vantage return fetcher
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
    return (closes[0] - closes[1]) / closes[1]

# Sidebar inputs
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income (before tax, $)", 0.0, 50000.0, 5000.0, 100.0)
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

# Return assumptions
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

# Core calculations
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# Projection loop
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
        "Month": m, "Balance": bal, "Stocks": stock_val, "Bonds": bond_val,
        "RealEstate": real_val, "Crypto": crypto_val, "FixedDeposit": fd_val,
        "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# Display summary
st.subheader("📋 Summary")
st.metric("Gross Income", f"${income:,.2f}")
st.metric("After-tax Income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

if total_exp > 0.7 * after_tax_income:
    st.warning("High expenses detected!")
if stocks > 0.7 * total_inv or crypto > 0.5 * total_inv:
    st.info("Consider diversifying your investments.")

st.subheader("📈 Net Worth Projection")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"])
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
st.plotly_chart(px.pie(names=["Housing", "Food", "Transport", "Utilities", "Entertainment", "Others"],
                       values=[housing, food, transport, utilities, entertainment, others]), use_container_width=True)

st.subheader("💼 Investment Allocation")
st.plotly_chart(px.pie(names=["Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit"],
                       values=[stocks, bonds, real_estate, crypto, fixed_deposit]), use_container_width=True)

# Compose LLM prompt
prompt = f"""
Financial Summary:
• Gross Income: ${income}
• Tax Rate: {tax_rate}%
• After-Tax Income: ${after_tax_income}
• Total Expenses: ${total_exp}
• Total Investments: ${total_inv}
• Net Cash Flow: ${net_flow}/mo
• Savings Target: ${savings_target}
• Projected Net Worth: ${df['NetWorth'].iloc[-1]}
Please provide financial advice to optimize expenses and investments.
"""

# Botpress Webhook Call (Webhook ID = "test")
if st.button("💬 Ask Botpress (via webhook: test)"):
    try:
        webhook_url = f"https://webhook.botpress.cloud/{CHAT_API_ID}/test"
        headers = {"Content-Type": "application/json"}
        payload = {"text": prompt}

        resp = requests.post(webhook_url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()

        if isinstance(result, dict) and "text" in result:
            reply = result["text"]
        elif isinstance(result, str):
            reply = result
        else:
            reply = json.dumps(result)

        st.success("Botpress replied via webhook:")
        st.markdown(f"> {reply}")

    except Exception as e:
        st.error(f"Botpress webhook error: {e}")
