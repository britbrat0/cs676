from openai import OpenAI
import streamlit as st
from assess_credibility import assess_url_credibility

# -----------------------------
# Streamlit UI setup
# -----------------------------
st.set_page_config(page_title="Credibility Chatbot", page_icon="💬")
st.title("💬 Credibility Chatbot")
st.caption("🚀 Chat with an AI that can assess the credibility of online articles")

# Sidebar for OpenAI API key
with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key", key="chatbot_api_key", type="password"
    )
    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
    st.markdown("[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)")

# Initialize chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! Send me a URL to evaluate."}
    ]

# Display previous chat messages
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Handle user input
# -----------------------------
if prompt := st.chat_input("Enter a URL or ask a question..."):
    # Append user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # -----------------------------
    # If input is a URL → credibility assessment
    # -----------------------------
    if prompt.startswith("http"):
        result = assess_url_credibility(prompt)
        msg = f"**Credibility Score:** {result['score']}\n\n**Explanation:** {result['explanation']}"
    
    # -----------------------------
    # Otherwise → use OpenAI for general chatbot response
    # -----------------------------
    else:
        if not openai_api_key:
            st.info("Please add your OpenAI API key in the sidebar to continue.")
            st.stop()

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state["messages"]
        )
        msg = response.choices[0].message.content

    # Append assistant response
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
