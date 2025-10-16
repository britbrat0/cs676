import os
import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import json

# -----------------------------
# Load .env locally (if available)
# -----------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass  # .env not available, likely running on Streamlit Cloud

# -----------------------------
# Get API keys from .env or Streamlit Secrets
# -----------------------------
openai_api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY"))
serpapi_key = os.getenv("SERPAPI_KEY", st.secrets.get("SERPAPI_KEY"))

if not openai_api_key:
    st.error("OpenAI API key not found. Set OPENAI_API_KEY in .env or Streamlit Secrets.")
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
    """Retrieve short summaries from top search results."""
    if not serpapi_key:
        return ["No SerpAPI key configured."]
    try:
        params = {"q": query, "api_key": serpapi_key, "num": 3}
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" in results:
            return [r.get("snippet", "") for r in results["organic_results"][:3]]
    except Exception as e:
        return [f"Search error: {e}"]
    return ["No results found."]

# -----------------------------
# Helper: Assess URL credibility
# -----------------------------
def assess_url_credibility(url: str):
    try:
        from assess_credibility import assess_url_credibility as ac
        result = ac(url)
        return result
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error analyzing URL: {e}"}

# -----------------------------
# Main interaction
# -----------------------------
if prompt := st.chat_input("Ask a question or enter a URL"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Case 1: URL → Credibility scoring
    if prompt.startswith("http"):
        with st.spinner("🔍 Assessing credibility..."):
            result = assess_url_credibility(prompt)
        st.json(result)
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(result)})

    # Case 2: General question → Web search + GPT
    else:
        with st.spinner("🌎 Searching the web..."):
            snippets = search_web(prompt)
        context = "\n".join(snippets)

        system_message = {
            "role": "system",
            "content": f"Use the following web results to answer the user's question:\n{context}"
        }

        messages = [system_message] + st.session_state.messages

        try:
            with st.spinner("🤖 Generating answer..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
            msg = response.choices[0].message.content
        except Exception as e:
            msg = f"Error with OpenAI API: {e}"

        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
