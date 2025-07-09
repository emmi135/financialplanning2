import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# Load secrets
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])

st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

# Helper
def get_alpha_vantage_monthly_return(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json().get("Monthly Adjusted Time Series", {})
    closes = [float(v["5. adjusted close"]) for v in data.values()]
    return (closes[0] - closes[1]) / closes[1] if len(closes) >= 2 else 0.01

# User Inputs
st.sidebar.header("📊 Monthly Income")
income = st.sidebar.number_input("Monthly income ($)", 0.0, 50000.0, 5000.0, 100.0)
tax_rate = st.sidebar.slider("Tax rate (%)", 0, 50, 20)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing ($)", 0.0, 5000.0, 1200.0)
food = st.sidebar.number_input("Food ($)", 0.0, 5000.0, 500.0)
transport = st.sidebar.number_input("Transport ($)", 0.0, 5000.0, 300.0)
utilities = st.sidebar.number_input("Utilities ($)", 0.0, 5000.0, 200.0)
entertainment = st.sidebar.number_input("Entertainment ($)", 0.0, 5000.0, 200.0)
others = st.sidebar.number_input("Other expenses ($)", 0.0, 5000.0, 200.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks ($)", 0.0, 5000.0, 500.0)
bonds = st.sidebar.number_input("Bonds ($)", 0.0, 5000.0, 300.0)
real_estate = st.sidebar.number_input("Real estate ($)", 0.0, 5000.0, 0.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0, 5000.0, 0.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit ($)", 0.0, 5000.0, 0.0)
months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target ($)", 0.0, 1_000_000.0, 10000.0)

# Rates
stock_r = get_alpha_vantage_monthly_return("SPY")
bond_r = get_alpha_vantage_monthly_return("AGG")
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

# Calculations
after_tax = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax - total_exp - total_inv

bal, rows = 0, []
for m in range(1, months + 1):
    bal += net_flow
    row = {
        "Month": m,
        "Balance": bal,
        "Stocks": stocks * ((1 + stock_r)**m - 1) / stock_r,
        "Bonds": bonds * ((1 + bond_r)**m - 1) / bond_r,
        "RealEstate": real_estate * ((1 + real_r)**m - 1) / real_r,
        "Crypto": crypto * ((1 + crypto_r)**m - 1) / crypto_r,
        "FixedDeposit": fixed_deposit * ((1 + fd_r)**m - 1) / fd_r
    }
    row["NetWorth"] = sum(row.values()) - m  # remove Month count
    rows.append(row)
df = pd.DataFrame(rows)

# Summary
st.subheader("📋 Summary")
st.metric("After-tax income", f"${after_tax:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Flow", f"${net_flow:,.2f}/mo")

# Charts
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"])
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

# Pie Charts
st.subheader("🧾 Expense Breakdown")
st.plotly_chart(px.pie(values=[housing, food, transport, utilities, entertainment, others],
                       names=["Housing", "Food", "Transport", "Utilities", "Entertainment", "Others"]))

st.subheader("💼 Investment Breakdown")
st.plotly_chart(px.pie(values=[stocks, bonds, real_estate, crypto, fixed_deposit],
                       names=["Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit"]))

# Botpress Chat
st.subheader("💬 Ask for Budgeting Advice")
if "conversation_id" not in st.session_state:
    try:
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }
        resp = requests.post(f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/conversations", headers=headers, json={})
        st.session_state["conversation_id"] = resp.json()["conversation"]["id"]
    except Exception as e:
        st.error(f"❌ Could not start conversation: {e}")

msg = st.chat_input("💬 Ask your assistant anything about your budget...")
if msg:
    try:
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }
        prompt = f"""
Here's my budget:
Income: ${income}, Tax rate: {tax_rate}%
Expenses: Housing={housing}, Food={food}, Transport={transport}, Utilities={utilities}, Entertainment={entertainment}, Others={others}
Investments: Stocks={stocks}, Bonds={bonds}, RealEstate={real_estate}, Crypto={crypto}, FixedDeposit={fixed_deposit}
Net cash flow: ${net_flow}/mo

User's question: {msg}
"""
        payload = {
            "payload": {"type": "text", "text": prompt},
            "conversationId": st.session_state["conversation_id"]
        }
        response = requests.post(f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/messages", headers=headers, json=payload)
        reply = response.json()["responses"][0]["payload"]["text"]
        st.chat_message("user").write(msg)
        st.chat_message("assistant").write(reply)
    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
