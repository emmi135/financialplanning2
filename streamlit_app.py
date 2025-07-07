import streamlit as st
from botpress_client import BotpressClient

st.set_page_config(page_title="💬 Botpress Chat", layout="wide")
st.title("💬 Botpress-Streamlit Chatbot")

client = BotpressClient(
    api_id=st.secrets["CHAT_API_ID"],
    user_key=st.secrets["USER_KEY"]
)

# Initialize conversation
if "conversation_id" not in st.session_state:
    conv = client.create_conversation()
    st.session_state.conversation_id = conv["conversation"]["id"]
    st.session_state.messages = []

conversation_id = st.session_state.conversation_id

# Load previous messages if needed
if "messages" not in st.session_state or not st.session_state.messages:
    messages = client.list_messages(conversation_id)
    user_id = messages["messages"][0]["userId"] if messages["messages"] else ""
    for msg in messages["messages"]:
        role = "user" if msg["userId"] == user_id else "assistant"
        st.session_state.messages.append({"role": role, "content": msg["payload"]["text"]})

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Type your message"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    client.create_message(user_input, conversation_id=conversation_id)

    # Stream response
    with st.chat_message("assistant"):
        stream = client.listen_conversation(conversation_id)
        response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
