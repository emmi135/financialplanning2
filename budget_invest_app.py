import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# --- Load secrets ---
API_KEY = st.secrets["alpha_vantage"]["api_key"]
BOTPRESS_CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# --- Page config ---
st.set_page_config(page_title="💸 Budget + Investment Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Chat-style AI)")

# --- Alpha Vantage monthly return helper ---
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
stocks = st.sidebar.number_input("Stocks investment ($)", 0.0, 5000.0, 500.0, 100.0)
bonds = st.sidebar.number_input("Bonds investment ($)", 0.0, 5000.0, 300.0, 100.0)
real_estate = st.sidebar.number_input("Real estate ($)", 0.0, 5000.0, 0.0, 100.0)
crypto = st.sidebar.number_input("Crypto ($)", 0.0, 5000.0, 0.0, 100.0)
fixed_deposit = st.sidebar.number_input("Fixed deposit ($)", 0.0, 5000.0, 0.0, 100.0)

months = st.sidebar.slider("Projection period (months)", 1, 60, 12)
savings_target = st.sidebar.number_input("Savings target at end of period ($)", 0.0, 1_000_000.0, 10000.0, 500.0)

# --- Calculations ---
after_tax_income = income * (1 - tax_rate / 100)
total_exp = housing + food + transport + utilities + entertainment + others
total_inv = stocks + bonds + real_estate + crypto + fixed_deposit
net_flow = after_tax_income - total_exp - total_inv

# --- Monthly growth calculations ---
stock_r = get_alpha_vantage_monthly_return("SPY") or 0.01
bond_r = get_alpha_vantage_monthly_return("AGG") or 0.003
real_r = 0.004
crypto_r = 0.02
fd_r = 0.003

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

# --- Summary ---
st.subheader("📋 Summary")
st.metric("Income (gross)", f"${income:,.2f}")
st.metric("After-tax income", f"${after_tax_income:,.2f}")
st.metric("Expenses", f"${total_exp:,.2f}")
st.metric("Investments", f"${total_inv:,.2f}")
st.metric("Net Cash Flow", f"${net_flow:,.2f}/mo")

# --- Visualizations ---
st.subheader("📈 Net Worth Growth")
fig = px.line(df, x="Month", y=["Balance", "Stocks", "Bonds", "RealEstate", "Crypto", "FixedDeposit", "NetWorth"],
              markers=True, title="Net Worth & Investments Over Time")
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
    "Bonds": bonds,
    "RealEstate": real_estate,
    "Crypto": crypto,
    "FixedDeposit": fixed_deposit
})
st.plotly_chart(px.pie(names=inv_s.index, values=inv_s.values, title="Investment Breakdown"), use_container_width=True)

# --- CHAT MODE ---
st.subheader("🤖 Ask Botpress for Advice")

if "conversation_id" not in st.session_state:
    try:
        conv_url = f"https://chat.botpress.cloud/v1/{BOTPRESS_CHAT_API_ID}/conversations"
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }
        conv_resp = requests.post(conv_url, headers=headers, json={"botId": BOTPRESS_CHAT_API_ID})
        conv_resp.raise_for_status()
        st.session_state["conversation_id"] = conv_resp.json()["conversation"]["id"]
    except Exception as e:
        st.error(f"❌ Failed to create conversation: {e}")

# Chat input
user_msg = st.chat_input("💬 Ask for budgeting advice...")

if user_msg:
    st.chat_message("user").write(user_msg)

    try:
        prompt = f"""
        User input: {user_msg}
        Current financials:
        After-tax income: ${after_tax_income}, Expenses: ${total_exp}, Investments: ${total_inv}, Net cash flow: ${net_flow}/mo.
        Projected net worth after {months} months: ${df['NetWorth'].iloc[-1]}, Target: ${savings_target}
        """

        payload = {
            "conversationId": st.session_state["conversation_id"],
            "payload": {"type": "text", "text": prompt}
        }
        headers = {
            "Authorization": f"Bearer {BOTPRESS_TOKEN}",
            "Content-Type": "application/json"
        }
        msg_url = f"https://chat.botpress.cloud/v1/{BOTPRESS_CHAT_API_ID}/messages"
        msg_resp = requests.post(msg_url, headers=headers, json=payload)

        if msg_resp.status_code == 200:
            data = msg_resp.json()
            if "messages" in data:
                for m in data["messages"]:
                    st.chat_message("assistant").write(m["payload"]["text"])
            else:
                st.warning("🤖 Botpress did not return any messages.")
        else:
            st.error(f"❌ Botpress error: {msg_resp.status_code} - {msg_resp.text}")

    except Exception as e:
        st.error(f"Botpress error: {e}")
