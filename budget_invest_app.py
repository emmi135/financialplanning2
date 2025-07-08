import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# Load API keys
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Budget + Investment Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

# Get Monthly Return from Alpha Vantage
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
st.sidebar.header("📊 Income")
income = st.sidebar.number_input("Monthly income (before tax, $)", value=5000.0, step=100.0)
tax_rate = st.sidebar.slider("Tax rate (%)", 0, 50, 20)

st.sidebar.header("📌 Expenses")
housing = st.sidebar.number_input("Housing / Rent", 0.0, 5000.0, 1200.0, 50.0)
food = st.sidebar.number_input("Food / Groceries", 0.0, 5000.0, 500.0, 50.0)
transport = st.sidebar.number_input("Transport", 0.0, 5000.0, 300.0, 50.0)
utilities = st.sidebar.number_input("Utilities", 0.0, 5000.0, 200.0, 50.0)
entertainment = st.sidebar.number_input("Entertainment", 0.0, 5000.0, 200.0, 50.0)
others = st.sidebar.number_input("Other expenses", 0.0, 5000.0, 200.0, 50.0)

st.sidebar.header("📈 Investments")
stocks = st.sidebar.number_input("Stocks", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds", 0.0, 5000.0, 300.0, 100.0)
real_estate = st.sidebar.number_input("Real estate", 0.0, 5000.0, 0.0, 100.0)
crypto = st.sidebar.number_input("Crypto", 0.0, 5000.0, 0.0, 100.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit", 0.0, 5000.0, 0.0, 100.0)

months = st.sidebar.slider("Projection (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Target net worth ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# Returns
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r, crypto_r, fd_r = 0.004, 0.02, 0.003

after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# Projection
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
        "Month": m,
        "Balance": bal,
        "Stocks": stock_val,
        "Bonds": bond_val,
        "RealEstate": real_val,
        "Crypto": crypto_val,
        "FixedDeposit": fd_val,
        "NetWorth": net_worth
    })
df = pd.DataFrame(rows)

# Summary
st.subheader("📋 Summary")
st.metric("Gross Income", f"${income:,.2f}")
st.metric("After Tax Income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# Charts
st.subheader("📈 Net Worth Over Time")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"],
              markers=True, title="Net Worth Projection")
fig.add_hline(y=savings_target, line_dash="dash", line_color="red", annotation_text="Target")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Expense Breakdown")
exp_data = pd.Series({
    "Housing": housing, "Food": food, "Transport": transport,
    "Utilities": utilities, "Entertainment": entertainment, "Others": others
})
st.plotly_chart(px.pie(names=exp_data.index, values=exp_data.values, title="Expense Breakdown"), use_container_width=True)

st.subheader("💼 Investment Breakdown")
inv_data = pd.Series({
    "Stocks": stocks, "Bonds": bonds, "RealEstate": real_estate,
    "Crypto": crypto, "FixedDeposit": fixed_deposit
})
st.plotly_chart(px.pie(names=inv_data.index, values=inv_data.values, title="Investment Breakdown"), use_container_width=True)

# Final Prompt
prompt = f"""
💵 Financial Summary:
- Gross income: ${income}
- Tax rate: {tax_rate}%
- After-tax income: ${after_tax_income}
- Monthly expenses: ${total_exp}
- Monthly investments: ${total_inv}
- Net cash flow: ${net_flow}/mo
- Savings target: ${savings_target}
- Projected net worth: ${df['NetWorth'].iloc[-1]}

🎯 Provide smart, specific suggestions to manage high expenses, rebalance investments, and meet the savings target.
"""

# Botpress AI Integration
if st.button("Ask Botpress AI"):
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
            "payload": {"type": "text", "text": prompt},
            "conversationId": st.session_state["conversation_id"]
        }
        msg_resp = requests.post(msg_url, headers=headers, json=payload)

        if msg_resp.ok and msg_resp.headers.get("Content-Type", "").startswith("application/json"):
            response = msg_resp.json()
            if response.get("responses"):
                st.success(response["responses"][0]["payload"]["text"])
            else:
                st.warning("No reply. Check Botpress AI agent flow.")
        else:
            st.error(f"Botpress API error:\n{msg_resp.text}")

    except Exception as e:
        st.error(f"❌ Botpress error: {e}")
