import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# API Keys
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Botpress Working Version)")

# Functions
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
income = st.sidebar.number_input("Monthly income ($)", value=5000.0, step=100.0)
tax_rate = st.sidebar.slider("Tax rate (%)", 0, 50, 20)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing ($)", 1200.0)
food = st.sidebar.number_input("Food ($)", 500.0)
transport = st.sidebar.number_input("Transport ($)", 300.0)
utilities = st.sidebar.number_input("Utilities ($)", 200.0)
entertainment = st.sidebar.number_input("Entertainment ($)", 200.0)
others = st.sidebar.number_input("Other expenses ($)", 200.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks ($)", 500.0)
bonds = st.sidebar.number_input("Bonds ($)", 300.0)
real_estate = st.sidebar.number_input("Real Estate ($)", 0.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0)
fixed_deposit = st.sidebar.number_input("Fixed Deposit ($)", 0.0)

months = st.sidebar.slider("Projection (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Target Savings ($)", 10000.0)

# Financial Calculations
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# Projections
bal = 0
rows = []
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

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
    row["NetWorth"] = sum(row.values()) - row["Month"]
    rows.append(row)

df = pd.DataFrame(rows)

# Visualizations
st.subheader("📋 Summary")
st.metric("After-tax income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Flow", f"${net_flow:,.2f}/mo")

st.subheader("📈 Net Worth Projection")
fig = px.line(df, x="Month", y=["NetWorth"], title="Net Worth Over Time")
fig.add_hline(y=savings_target, line_dash="dash", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

# Chat-style Botpress Interaction
st.subheader("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")
user_msg = st.chat_input("Ask your question...")

if user_msg:
    with st.chat_message("user"):
        st.markdown(user_msg)

    try:
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }

        if "conversation_id" not in st.session_state:
            conv_url = f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/conversations"
            conv_resp = requests.post(conv_url, headers=headers, json={})
            conv_resp.raise_for_status()
            st.session_state["conversation_id"] = conv_resp.json()["conversation"]["id"]

        msg_url = f"https://chat.botpress.cloud/v1/{CHAT_API_ID}/messages"
        payload = {
            "payload": {"type": "text", "text": user_msg},
            "conversationId": st.session_state["conversation_id"]
        }

        msg_resp = requests.post(msg_url, headers=headers, json=payload)
        msg_resp.raise_for_status()
        msg_data = msg_resp.json()

        if "replies" in msg_data and msg_data["replies"]:
            with st.chat_message("assistant"):
                st.markdown(msg_data["replies"][0]["payload"]["text"])
        else:
            st.warning("🤖 Botpress did not return a reply.")

    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
