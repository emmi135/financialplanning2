import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# Configuration
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

# Monthly return helper
def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    ts = r.json().get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in ts.values()]
    return (closes[0] - closes[1]) / closes[1] if len(closes) >= 2 else None

# Sidebar inputs
st.sidebar.header("📊 Income & Expenses")
income = st.sidebar.number_input("Monthly Income (before tax)", 0.0, 20000.0, 5000.0, 100.0)
tax_rate = st.sidebar.slider("Tax Rate (%)", 0, 50, 20)
expenses = {
    "Housing": st.sidebar.number_input("Housing", 0.0, 5000.0, 1200.0, 50.0),
    "Food": st.sidebar.number_input("Food", 0.0, 5000.0, 500.0, 50.0),
    "Transport": st.sidebar.number_input("Transport", 0.0, 5000.0, 300.0, 50.0),
    "Utilities": st.sidebar.number_input("Utilities", 0.0, 5000.0, 200.0, 50.0),
    "Entertainment": st.sidebar.number_input("Entertainment", 0.0, 5000.0, 200.0, 50.0),
    "Others": st.sidebar.number_input("Others", 0.0, 5000.0, 200.0, 50.0)
}
st.sidebar.header("📈 Investments")
investments = {
    "Stocks": st.sidebar.number_input("Stocks", 0.0, 5000.0, 500.0, 100.0),
    "Bonds": st.sidebar.number_input("Bonds", 0.0, 5000.0, 300.0, 100.0),
    "RealEstate": st.sidebar.number_input("Real Estate", 0.0, 5000.0, 0.0, 100.0),
    "Crypto": st.sidebar.number_input("Crypto", 0.0, 5000.0, 0.0, 100.0),
    "FixedDeposit": st.sidebar.number_input("Fixed Deposit", 0.0, 5000.0, 0.0, 100.0)
}
months = st.sidebar.slider("Projection Period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Target Net Worth ($)", 0.0, 1000000.0, 10000.0, 500.0)

# Calculate
after_tax = income * (1 - tax_rate / 100)
total_exp = sum(expenses.values())
total_inv = sum(investments.values())
net_cash = after_tax - total_exp - total_inv

# Warnings
if total_exp > 0.7 * after_tax:
    st.warning("⚠️ Expenses are too high!")
if total_inv < 0.1 * after_tax:
    st.info("💡 Consider increasing your investments.")

# Investment returns
returns = {
    "Stocks": get_alpha_vantage_monthly_return("SPY") or 0.01,
    "Bonds": get_alpha_vantage_monthly_return("AGG") or 0.003,
    "RealEstate": 0.004,
    "Crypto": 0.02,
    "FixedDeposit": 0.003
}

# Simulation
balance = 0
rows = []
for m in range(1, months + 1):
    balance += net_cash
    future = {
        k: v * ((1 + returns[k])**m - 1) / returns[k] if returns[k] else 0
        for k, v in investments.items()
    }
    net_worth = balance + sum(future.values())
    rows.append(dict(Month=m, Balance=balance, NetWorth=net_worth, **future))
df = pd.DataFrame(rows)

# Summary
st.subheader("📋 Summary")
st.metric("Net Monthly Cash Flow", f"${net_cash:,.2f}")
st.metric("Total Expenses", f"${total_exp:,.2f}")
st.metric("Total Investments", f"${total_inv:,.2f}")

# Charts
st.subheader("📈 Net Worth Projection")
fig = px.line(df, x="Month", y=["NetWorth", "Balance"] + list(investments.keys()), markers=True)
fig.add_hline(y=savings_target, line_color="red", line_dash="dot", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Expense Breakdown")
st.plotly_chart(px.pie(names=expenses.keys(), values=expenses.values(), title="Expenses"), use_container_width=True)

st.subheader("📊 Investment Breakdown")
st.plotly_chart(px.pie(names=investments.keys(), values=investments.values(), title="Investments"), use_container_width=True)

# Botpress prompt
prompt = f"""
💬 Budget Overview:
After-tax: ${after_tax}
Expenses: ${total_exp}
Investments: ${total_inv}
Cash Flow: ${net_cash}/mo
Target Net Worth: ${savings_target}
Projected: ${df['NetWorth'].iloc[-1]:.2f}

Give actionable advice to optimize expenses, investments, and help reach the goal.
"""

# Botpress interaction
if st.button("🤖 Get Advice from Botpress"):
    try:
        if "conversation_id" not in st.session_state:
            conv_url = f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/conversations"
            headers = {"Authorization": f"Bearer {BOTPRESS_TOKEN}", "Content-Type": "application/json"}
            conv = requests.post(conv_url, headers=headers).json()
            st.session_state["conversation_id"] = conv["conversation"]["id"]

        msg_url = f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/messages"
        payload = {
            "conversationId": st.session_state["conversation_id"],
            "payload": {"type": "text", "text": prompt}
        }
        r = requests.post(msg_url, headers=headers, json=payload)
        r.raise_for_status()
        st.success("✅ Message sent!")
        if 'application/json' in r.headers.get('Content-Type', ''):
            st.json(r.json())
        else:
            st.write(r.text)
    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
