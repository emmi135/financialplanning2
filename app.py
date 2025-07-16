import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import google.generativeai as genai

# 🔐 Secrets
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
API_KEY = st.secrets["alpha_vantage"]["api_key"]

# 📄 App config
st.set_page_config(page_title="💸 Multi-LLM Budget Planner", layout="wide")
st.title("💸 Budgeting & Investment Planner")

# 📊 Input form
with st.form("budget_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        income = st.number_input("💰 Monthly Income", min_value=0)
    with col2:
        expenses = st.number_input("📉 Monthly Expenses", min_value=0)
    with col3:
        savings = st.number_input("🏦 Current Savings", min_value=0)
    submitted = st.form_submit_button("Analyze")

if submitted:
    balance = income - expenses
    st.metric("💵 Monthly Balance", f"${balance}")

    warning_messages = []
    if balance < 0:
        warning_messages.append("⚠️ You're spending more than you earn!")
    if savings < 1000:
        warning_messages.append("📉 Your savings are too low for emergencies!")
    if income > 0 and savings / income < 1:
        warning_messages.append("💡 Consider saving more of your income!")

    for msg in warning_messages:
        st.warning(msg)

    st.subheader("📈 Investment Suggestions (AI)")
    prompt = f"My monthly income is ${income}, expenses are ${expenses}, and I have ${savings} in savings. Give investment advice."

    # Gemini call
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.success("🤖 Gemini's Advice:")
        st.markdown(response.text)
    except Exception as e:
        st.error(f"❌ Gemini error: {e}")

    # DeepSeek AI via OpenRouter
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://yourapp.streamlit.app",
            "X-Title": "Budget Planner"
        }
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a financial advisor."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        ai_text = response.json()["choices"][0]["message"]["content"]
        st.success("🔍 DeepSeek Advice:")
        st.markdown(ai_text)
    except Exception as e:
        st.error(f"❌ DeepSeek error: {e}")

# 💬 Embedded Botpress Chat
st.markdown("### 💬 Ask Our AI Financial Assistant")
iframe_code = f'''
<iframe
  src="https://chat.botpress.cloud/{CHAT_API_ID}/embed"
  width="100%"
  height="500"
  frameborder="0"
></iframe>
'''
st.components.v1.html(iframe_code, height=500)
