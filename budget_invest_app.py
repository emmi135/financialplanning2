import streamlit as st
import requests

st.set_page_config(page_title="💸 Budget Assistant", layout="centered")

st.title("💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Store messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user input
if user_input := st.chat_input("Type your budgeting question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Send to Botpress
    url = "https://webhook.botpress.cloud/a6b81594-2894-47fa-bdb6-db9ae173fa61"

    payload = {
        "messages": [
            {"type": "text", "text": user_input}
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        bp_reply = res.json()["responses"][0]["text"]
    except Exception as e:
        bp_reply = "❌ Botpress error: " + str(e)

    st.session_state.messages.append({"role": "assistant", "content": bp_reply})
    with st.chat_message("assistant"):
        st.markdown(bp_reply)
