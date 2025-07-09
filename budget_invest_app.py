import streamlit as st
import requests
import uuid

# -- Page Setup --
st.set_page_config(page_title="💬 Budget Assistant", layout="centered")
st.title("💬 Ask for Budgeting Advice")
st.caption("Talk to your financial assistant powered by Botpress!")

# -- Store Chat History --
if "messages" not in st.session_state:
    st.session_state.messages = []

# -- Display Previous Messages --
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -- Input Box --
user_input = st.chat_input("Enter your budgeting question here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # -- Botpress Webhook Endpoint --
    botpress_url = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

    # -- Required Botpress Format for Autonomous Node --
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
        response = requests.post(botpress_url, json=payload)
        response.raise_for_status()
        bot_data = response.json()

        if "responses" in bot_data and bot_data["responses"]:
            reply = bot_data["responses"][0].get("text", "🤖 No message from Botpress.")
        else:
            reply = "🤖 Botpress gave no reply."

    except Exception as e:
        reply = f"❌ Botpress error: {e}"

    # -- Display Bot's Reply --
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
