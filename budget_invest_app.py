import streamlit as st
import requests
import uuid

# Set Streamlit page config
st.set_page_config(page_title="💰 Budget & Investment Planner", layout="centered")

# Title and description
st.title("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_msg = st.chat_input("Type your question here...")

if user_msg:
    # Append user's message to chat history
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Send message to Botpress webhook
    botpress_url = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

    # Payload must match Botpress expected format
    payload = {
        "type": "text",
        "text": user_msg,
        "channel": "webchat",
        "conversationId": str(uuid.uuid4())  # A random conversation ID
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(botpress_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        if "responses" in data and data["responses"]:
            bot_reply = data["responses"][0].get("text", "🤖 Botpress gave no reply.")
        else:
            bot_reply = "🤖 No messages returned."
    except Exception as e:
        bot_reply = f"❌ Botpress error: {str(e)}"

    # Show bot reply
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
