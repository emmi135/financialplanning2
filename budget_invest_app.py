import streamlit as st

# Set page config
st.set_page_config(page_title="Ask for Budgeting Advice", layout="centered")

# Page title
st.markdown("## 💬 Ask for Budgeting Advice")
st.markdown("Talk to your financial assistant powered by Botpress!")

# Embed Botpress WebChat using iframe
botpress_iframe_url = (
    "https://cdn.botpress.cloud/webchat/v3.0/shareable.html?"
    "configUrl=https://files.bpcontent.cloud/2025/07/02/02/20250702020605-VDMFG1YB.json"
)

# Display the iframe
st.markdown(
    f"""
    <iframe
        src="{botpress_iframe_url}"
        width="100%"
        height="600"
        style="border: none; margin-top: 20px;"
        allow="microphone">
    </iframe>
    """,
    unsafe_allow_html=True
)
