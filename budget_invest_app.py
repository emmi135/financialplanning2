import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# === CONFIGURATION ===
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

st.set_page_config(page_title="💸 Budget Planner + Botpress AI", layout="wide")
st.title("💸 Budget + Investment Planner with AI Advice")

# === FUNCTION TO FETCH RETURNS ===
def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    ts = r.json().get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in ts.values()]
    if len(closes) < 2:
        return None
    return (closes[0] - closes[1]) / closes[1]

# === SIDEBAR INPUTS ===
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

# === CALCULATIONS ===
after_tax = income * (1 - tax_rate / 100)
total_exp = sum(expenses.values())
total_inv = sum(investments.values())
net_cash = after_tax - total_exp - total_inv

# === WARNINGS ===
if total_exp > 0.7 * after_tax:
    st.warning("⚠️ Expenses are too high compared to income!")
if total_inv < 0.1 * after_tax:
    st.info("💡 Consider increasing your investments to grow wealth.")

# === RETURNS ASSUMPTIONS ===
returns = {
    "Stocks": get_alpha_vantage_monthly_return("SPY") or 0.01,
    "Bonds": get_alpha_vantage_monthly_return("AGG") or 0.003,
    "RealEstate": 0.004,
    "Crypto": 0.02,
    "FixedDeposit": 0.003
}

# === SIMULATION ===
balance = 0
rows = []
for m in range(1, months + 1):
    balance += net_cash
    future = {k: v * ((1 + returns[k])**m - 1) / returns[k] if returns[k] else 0 for k, v in investments.items()}
    net_worth = balance + sum(future.values())
    rows.append(dict(Month=m, Balance=balance, NetWorth=net_worth, **future))
df = pd.DataFrame(rows)

# === DISPLAY METRICS ===
st.subheader("📋 Summary")
st.metric("Net Monthly Cash Flow", f"${net_cash:,.2f}")
st.metric("Total Expenses", f"${total_exp:,.2f}")
st.metric("Total Investments", f"${total_inv:,.2f}")

# === CHARTS ===
st.subheader("📈 Net Worth Projection")
fig = px.line(df, x="Month", y=["NetWorth", "Balance"] + list(investments.keys()), markers=True)
fig.add_hline(y=savings_target, line_color="red", line_dash="dot", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Expense Breakdown")
st.plotly_chart(px.pie(names=expenses.keys(), values=expenses.values(), title="Expenses"), use_container_width=True)

st.subheader("📊 Investment Breakdown")
st.plotly_chart(px.pie(names=investments.keys(), values=investments.values(), title="Investments"), use_container_width=True)

# === PROMPT TO BOTPRESS ===
prompt = f"""
💬 Budget Summary:
After-tax income: ${after_tax}
Expenses: ${total_exp}
Investments: ${total_inv}
Net monthly savings: ${net_cash}
Target net worth after {months} months: ${savings_target}
Projected net worth: ${df['NetWorth'].iloc[-1]:.2f}

Give tips to reduce expenses, improve savings, and rebalance investments.
"""

# === BOTPRESS INTERACTION ===
if st.button("🤖 Get Advice from Botpress"):
    try:
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }

        if "conversation_id" not in st.session_state:
            conv_url = f"https://chat.botpress.cloud/api/v1/bots/{CHAT_API_ID}/conversations"
            conv_resp = requests.post(conv_url, headers=headers)
            conv_resp.raise_for_status()
            conv_data = conv_resp.json()
            conversation_id = conv_data.get("id") or conv_data.get("conversation", {}).get("id")
            if not conversation_id:
                st.error(f"❌ Unexpected Botpress response: {conv_data}")
                st.stop()
            st.session_state["conversation_id"] = conversation_id

        msg_url = f"https://chat.botpress.cloud/api/v1/bots/{CHAT_API_ID}/messages"
        payload = {
            "conversationId": st.session_state["conversation_id"],
            "payload": {"type": "text", "text": prompt}
        }
        msg_resp = requests.post(msg_url, headers=headers, json=payload)
        msg_resp.raise_for_status()

        if 'application/json' in msg_resp.headers.get('Content-Type', ''):
            reply_json = msg_resp.json()
            st.success("✅ Botpress response received")
            st.json(reply_json)
        else:
            st.warning("⚠️ Non-JSON response from Botpress")
            st.text(msg_resp.text)

    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
