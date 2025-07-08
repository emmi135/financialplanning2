import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Load secrets
genai_key = st.secrets["gemini"]["api_key"]
openrouter_key = st.secrets["openrouter"]["api_key"]
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]

st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting + Investment Planner (Multi-LLM AI Suggestions)")

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

# Calculations
after_tax_income = income * (1 - tax_rate / 100)
total_expenses = housing + food + transport + utilities + entertainment + others
total_investments = stocks + bonds + real_estate
surplus = after_tax_income - total_expenses - total_investments

st.subheader("📋 Summary")
st.metric("After-tax income", f"${after_tax_income:,.2f}")
st.metric("Total expenses", f"${total_expenses:,.2f}")
st.metric("Total investments", f"${total_investments:,.2f}")
st.metric("Surplus / Deficit", f"${surplus:,.2f}")

# Pie Chart
data = {
    "Category": ["Housing", "Food", "Transport", "Utilities", "Entertainment", "Others", "Stocks", "Bonds", "Real Estate"],
    "Amount": [housing, food, transport, utilities, entertainment, others, stocks, bonds, real_estate]
}
df = pd.DataFrame(data)
fig = px.pie(df, names="Category", values="Amount", title="Expense & Investment Breakdown")
st.plotly_chart(fig)

# Botpress Chat API Integration
st.subheader("🤖 Ask Botpress for Suggestions")

def call_botpress_api(message):
    base_url = f"https://api.botpress.cloud/v1/chat/{CHAT_API_ID}"
    headers = {
        "Authorization": f"Bearer {BOTPRESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Step 1: Start conversation
    try:
        conv_resp = requests.post(f"{base_url}/conversations", headers=headers)
        conv_resp.raise_for_status()
        conversation_id = conv_resp.json()["id"]
    except Exception as e:
        return f"❌ Error starting conversation: {e}"

    # Step 2: Send message
    try:
        msg_url = f"{base_url}/messages"
        payload = {
            "conversationId": conversation_id,
            "payload": {
                "type": "text",
                "text": message
            }
        }
        msg_resp = requests.post(msg_url, headers=headers, json=payload)
        msg_resp.raise_for_status()
        data = msg_resp.json()
        return data.get("messages", [{}])[0].get("payload", {}).get("text", "🤖 No reply received.")
    except Exception as e:
        return f"❌ Error sending message: {e}"

# Construct AI prompt
user_prompt = f"""
Income: ${income}, Tax Rate: {tax_rate}%
Expenses - Housing: ${housing}, Food: ${food}, Transport: ${transport}, Utilities: ${utilities}, Entertainment: ${entertainment}, Others: ${others}
Investments - Stocks: ${stocks}, Bonds: ${bonds}, Real Estate: ${real_estate}
Suggest improvements in budgeting or investing.
"""

if st.button("💬 Ask Botpress"):
    with st.spinner("Waiting for Botpress..."):
        reply = call_botpress_api(user_prompt)
        st.markdown(f"**🧠 Botpress says:**\n\n> {reply}")
