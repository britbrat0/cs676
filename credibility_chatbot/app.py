import os
import streamlit as st
import json

# -----------------------------
# Import OpenAI and SerpAPI
# -----------------------------
try:
    from openai import OpenAI
except ModuleNotFoundError:
    st.error("OpenAI package not installed. Check requirements.txt.")
    st.stop()

try:
    from serpapi import GoogleSearch
except ModuleNotFoundError:
    st.error("SerpAPI package not installed. Check requirements.txt.")
    st.stop()

# -----------------------------
# API Keys from Streamlit Secrets
# -----------------------------
openai_api_key = st.secrets.get("OPENAI_API_KEY")
serpapi_key = st.secrets.get("SERPAPI_KEY")

if not openai_api_key:
    st.error("OpenAI API key not found. Add it to Streamlit secrets.")
    st.stop()

# -----------------------------
# Initialize OpenAI client
# -----------------------------
client = OpenAI(api_key=openai_api_key)

# -----------------------------
# Chat session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! Paste a URL or ask a question."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Helper: Web search using SerpAPI
# -----------------------------
def search_web(query: str):
    if not serpapi_key:
        return ["No SerpAPI key configured."]
    try:
        params = {"q": query, "api_key": serpapi_key, "num": 3}
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" in results:
            return [r.get("sni]()
