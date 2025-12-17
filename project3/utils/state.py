import streamlit as st

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! Upload a dataset and I’ll help you "
                    "analyze it and train ML models."
                )
            }
        ]

    if "df" not in st.session_state:
        st.session_state.df = None

    if "target" not in st.session_state:
        st.session_state.target = None

    if "task_type" not in st.session_state:
        st.session_state.task_type = None

    if "model_results" not in st.session_state:
        st.session_state.model_results = {}
