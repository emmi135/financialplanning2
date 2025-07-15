import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import datetime

# 🔐 API Secrets
CHAT_API_ID = st.secrets["botpress"]["chat_api_id"]
BOTPRESS_TOKEN = st.secrets["botpress"]["token"]
genai.configure(api_key=st.secrets["gemini"]["api_key"])
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# 📄 Streamlit Config
st.set_page_config(page_title="💸 Budget & Investment Planner", layout="wide")
st.title("💼 Your AI-Powered Budget & Investment Planner")

# 📝 Input: Monthly Budget
income = st.number_input("💰 Monthly Income ($)", min_value=0)
expenses = st.number_input("💸 Monthly Expenses ($)", min_value=0)
savings = st.number_input("🏦 Current Savings ($)", min_value=0)

# 🧠 Budget Health Feedback
if income > 0:
    ratio = expenses / income
    if ratio > 0.9:
        st.warning("⚠️ You're spending over 90% of your income. Consider reducing expenses.")
    elif ratio > 0.7:
        st.info("💡 Try saving a bit more to build wealth over time.")
    else:
        st.success("✅ Great job keeping your expenses low!")

# 📈 Investment Suggestion via Gemini
if st.button("📊 Get AI Investment Advice (Gemini)"):
    prompt = f"My income is {income}, expenses are {expenses}, and I have {savings} in savings. What should I do to invest wisely?"
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.markdown("### 🤖 Gemini Advice")
        st.write(response.text)
    except Exception as e:
        st.error(f"Gemini error: {e}")

# 🧠 DeepSeek Reasoning via OpenRouter
if st.button("🧠 Get AI Recommendation (DeepSeek)"):
    try:
        openrouter_prompt = f"""You are a financial advisor. A user earns ${income}/month, spends ${expenses}, and has ${savings} in savings. What should they prioritize: reducing expenses, increasing income, or investing? Suggest 3 practical steps."""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": openrouter_prompt}]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        reply = res.json()["choices"][0]["message"]["content"]
        st.markdown("### 🧠 DeepSeek Suggestion")
        st.write(reply)
    except Exception as e:
        st.error(f"DeepSeek error: {e}")

# 🧠 Embedded Botpress Assistant
st.markdown("---")
st.markdown("### 💬 Talk to Your Assistant")

st.components.v1.iframe(
    f"https://chat.botpress.cloud/app/{CHAT_API_ID}?token={BOTPRESS_TOKEN}",
    height=550,
    width=700,
    scrolling=True,
)
