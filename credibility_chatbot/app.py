from openai import OpenAI
import streamlit as st
from src.credibility_chatbot.assess_credibility import assess_url_credibility

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
    st.markdown("[View source](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)")

st.title("💬 Credibility Chatbot")
st.caption("🚀 Chat with an AI that can assess article credibility")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! Send me an article URL, and I’ll evaluate its credibility."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Enter a URL or ask a question..."):
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    if prompt.startswith("http"):
        result = assess_url_credibility(prompt)
        msg = f"**Credibility Score:** {result['score']}\n\n**Explanation:** {result['explanation']}"
    else:
        client = OpenAI(api_key=openai_api_key)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,
        )
        msg = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
