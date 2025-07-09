import streamlit as st
import requests
import uuid

st.set_page_config(page_title="💬 Budget Bot", layout="centered")
st.title("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Your Botpress Chat API endpoint
CHAT_API_URL = "https://chat.botpress.cloud/v1/chat"
BOT_ID = "a6b81594-2894-47fa-bdb6-db9ae173fa61"

# Create or reuse a user ID
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
user_input = st.chat_input("Type your question here...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare headers and payload
    headers = {
        "Content-Type": "application/json",
        "x-bot-id": BOT_ID
    }

    payload = {
        "userId": st.session_state.user_id,
        "messages": [
            {
                "type": "text",
                "payload": {
                    "text": user_input
                }
            }
        ]
    }

    try:
        res = requests.post(CHAT_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        responses = res.json().get("messages", [])

        # Handle all responses from Botpress
        for r in responses:
            bot_reply = r.get("payload", {}).get("text", "🤖 No response.")
            st.chat_message("assistant").markdown(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        err_msg = f"❌ Error talking to Botpress: {str(e)}"
        st.chat_message("assistant").markdown(err_msg)
        st.session_state.messages.append({"role": "assistant", "content": err_msg})
