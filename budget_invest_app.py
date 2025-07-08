import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import json

# Load secrets
genai_key = st.secrets["gemini"]["api_key"]
openrouter_key = st.secrets["openrouter"]["api_key"]
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

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

# Sidebar Inputs
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
stocks = st.sidebar.number_input("Stocks investment ($)", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds investment ($)", 0.0, 5000.0, 300.0, 100.0)
real_estate = st.sidebar.number_input("Real estate ($)", 0.0, 5000.0, 0.0, 100.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0, 5000.0, 0.0, 100.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit ($)", 0.0, 5000.0, 0.0, 100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# Assumed returns
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

# Calculations
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# Projections
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

# Output Summary
st.subheader("📋 Summary")
st.metric("Gross Income", f"${income:,.2f}")
st.metric("After-tax Income", f"${after_tax_income:,.2f}")
st.metric("Total Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

if total_exp > 0.7 * after_tax_income:
    st.warning("🚨 High expenses detected!")
if stocks > 0.7 * total_inv or crypto > 0.5 * total_inv:
    st.info("📌 Consider diversifying your investments.")

# Charts
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

# Prompt for Botpress
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
Please advise on controlling expenses, rebalancing investments, and achieving the savings goal.
"""

# Botpress Button
if st.button("💬 Ask Botpress for Advice"):
    try:
        conv_url = f"https://chat.botpress.cloud/api/v1/bots/{CHAT_API_ID}/conversations"
        headers = {"Authorization": f"Bearer {BOTPRESS_TOKEN}", "Content-Type": "application/json"}
        conv_resp = requests.post(conv_url, headers=headers)
        conv_resp.raise_for_status()
        conversation_id = conv_resp.json()["id"]

        msg_url = f"https://chat.botpress.cloud/api/v1/bots/{CHAT_API_ID}/messages"
        msg_payload = {"conversationId": conversation_id, "payload": {"type": "text", "text": prompt}}
        requests.post(msg_url, headers=headers, json=msg_payload).raise_for_status()

        time.sleep(2)
        history_url = f"https://chat.botpress.cloud/api/v1/bots/{CHAT_API_ID}/conversations/{conversation_id}/messages"
        history_resp = requests.get(history_url, headers=headers)
        history_resp.raise_for_status()
        messages = history_resp.json()

        bot_replies = [m for m in messages if not m.get("incoming", True)]
        if bot_replies:
            payload = bot_replies[-1].get("payload", {})
            reply = payload.get("text", "🤖 Bot replied but no text was found.")
        else:
            reply = "🤖 No reply received from Botpress."

        st.success("✅ Botpress replied:")
        st.markdown(f"> {reply}")

    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
