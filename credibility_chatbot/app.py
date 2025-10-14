# app.py
from openai import OpenAI
import streamlit as st
from assess_credibility import assess_url_credibility
import validators

st.set_page_config(page_title="Credibility Chatbot", page_icon="💬")
st.title("💬 Credibility Chatbot")
st.caption("🚀 Chat with an AI that can assess the credibility of online articles")

# Sidebar: OpenAI API key
with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key", key="chatbot_api_key", type="password"
    )
    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
    st.markdown("[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)")

# Initialize chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! Send me a URL to evaluate or ask a question."}
    ]

# Display previous messages
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
if prompt := st.chat_input("Enter a URL or ask a question..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # -----------------------------
    # URL detection using validators
    # -----------------------------
    if validators.url(prompt):
        result = assess_url_credibility(prompt)
        msg = f"**Credibility Score:** {result['score']}\n\n**Explanation:** {result['explanation']}"
    else:
        # General chatbot via OpenAI
        if not openai_api_key:
            st.info("Please add your OpenAI API key in the sidebar to continue.")
            st.stop()
        client = OpenAI(api_key=openai_api_key)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state["messages"]
            )
            msg = response.choices[0].message.content
        except Exception as e:
            msg = f"Error with OpenAI API: {e}"

    st.session_state["messages"].append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
