import streamlit as st
import requests

st.set_page_config(page_title="Budgeting Advisor", layout="centered")

st.title("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Chat history setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
user_msg = st.chat_input("💬 Ask your budgeting question...")

# Webhook details
BOTPRESS_WEBHOOK_URL = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

if user_msg:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Prepare payload
    payload = {
        "type": "text",
        "payload": {
            "text": user_msg
        }
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(BOTPRESS_WEBHOOK_URL, headers=headers, json=payload)
        if response.status_code == 200:
            bot_reply = response.json().get("payload", {}).get("text", "⚠️ No reply received.")
        else:
            bot_reply = f"❌ Botpress error: {response.status_code} - {response.reason}"
    except Exception as e:
        bot_reply = f"❌ Exception: {e}"

    # Show bot reply
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
