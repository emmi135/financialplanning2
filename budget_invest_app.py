import streamlit as st
import requests
import uuid

# Page Config
st.set_page_config(page_title="💬 Budget Assistant")
st.title("💬 Ask for Budgeting Advice")
st.caption("Talk to your financial assistant powered by Botpress!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Enter your budgeting question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Botpress Webhook
    webhook_url = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

    # Construct Botpress-compatible payload
    payload = {
        "messages": [
            {
                "type": "text",
                "text": user_input
            }
        ],
        "user": {
            "id": str(uuid.uuid4())
        },
        "session": {
            "id": str(uuid.uuid4())
        }
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        reply_data = response.json()

        if "responses" in reply_data and reply_data["responses"]:
            reply_text = reply_data["responses"][0].get("text", "🤖 (No response text)")
        else:
            reply_text = "🤖 No reply received from Botpress."

    except Exception as e:
        reply_text = f"❌ Botpress error: {e}"

    # Show reply
    with st.chat_message("assistant"):
        st.markdown(reply_text)
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
