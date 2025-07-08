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

# Summary Calculations
after_tax_income = income * (1 - tax_rate / 100)
total_expenses = housing + food + transport + utilities + entertainment + others
total_investments = stocks + bonds + real_estate
surplus = after_tax_income - total_expenses - total_investments

st.subheader("📋 Summary")
st.write(f"**After-tax income:** ${after_tax_income:,.2f}")
st.write(f"**Total expenses:** ${total_expenses:,.2f}")
st.write(f"**Total investments:** ${total_investments:,.2f}")
st.write(f"**Surplus / Deficit:** ${surplus:,.2f}")

# Pie Chart
data = {
    "Category": ["Housing", "Food", "Transport", "Utilities", "Entertainment", "Others", "Stocks", "Bonds", "Real Estate"],
    "Amount": [housing, food, transport, utilities, entertainment, others, stocks, bonds, real_estate]
}
df = pd.DataFrame(data)
fig = px.pie(df, names="Category", values="Amount", title="Expense & Investment Breakdown")
st.plotly_chart(fig)

# AI Suggestion Section
st.subheader("📬 AI Suggestions (via Botpress)")

def call_botpress_api(message):
    url = f"https://api.botpress.cloud/v1/chat/{CHAT_API_ID}/webhook/test"
    headers = {
        "Authorization": f"Bearer {BOTPRESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"message": message}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("responses", [{}])[0].get("payload", {}).get("text", "🤖 No bot reply received.")
    except Exception as e:
        return f"Botpress webhook error: {e}"

user_prompt = f"""My income is ${income}, tax is {tax_rate}%. 
Expenses: housing=${housing}, food=${food}, transport=${transport}, utilities=${utilities}, entertainment=${entertainment}, others=${others}. 
Investments: stocks=${stocks}, bonds=${bonds}, real_estate=${real_estate}. 
Suggest improvements in budgeting or investment."""

if st.button("🧠 Get Suggestions from Botpress"):
    with st.spinner("Contacting Botpress..."):
        bot_reply = call_botpress_api(user_prompt)
        st.markdown(f"> {bot_reply}")
