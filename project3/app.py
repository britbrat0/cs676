import streamlit as st
import pandas as pd

from agents.orchestrator import run_agent
from utils.state import init_state

st.set_page_config(page_title="Agentic ML App", layout="wide")

st.title("🤖 Agentic Machine Learning Assistant")

init_state()

uploaded_file = st.file_uploader("Upload a CSV dataset", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.session_state.df = df

    st.success("Dataset loaded successfully!")
    st.write("Preview:", df.head())

st.divider()

# Chat interface
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Ask about your dataset or choose a model...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    response = run_agent(user_input)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    st.chat_message("assistant").write(response)
