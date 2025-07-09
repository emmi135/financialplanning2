import streamlit as st
import requests

st.set_page_config(page_title="Budgeting Assistant", layout="centered")

st.title("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Initialize session messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input field
user_input = st.chat_input("Type your question here...")

# Botpress webhook endpoint
BOTPRESS_WEBHOOK_URL = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

if user_input:
    # Show user's message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Build correct payload
    payload = {
        "type": "text",
        "payload": {
            "text": user_input
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(BOTPRESS_WEBHOOK_URL, headers=headers, json=payload)
        if res.status_code == 200:
            bot_reply = res.json().get("payload", {}).get("text", "🤖 No reply received.")
        else:
            bot_reply = f"❌ Botpress error: {res.status_code} - {res.text}"
    except Exception as e:
        bot_reply = f"❌ Exception: {str(e)}"

    # Show bot's response
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
