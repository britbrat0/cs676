try:
    from google_search_results import GoogleSearch
    st.write("✅ GoogleSearch imported successfully!")
except ModuleNotFoundError:
    st.error("❌ google-search-results not installed. Check requirements.txt.")
    st.stop()
    
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
    from google_search_results import GoogleSearch
except ModuleNotFoundError:
    st.error("google-search-results package not installed. Check requirements.txt.")
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
            return [r.get("snippet", "") for r in results["organic_results"][:3]]
    except Exception as e:
        return [f"Search error: {e}"]
    return ["No results found."]

# -----------------------------
# Helper: Assess URL credibility
# -----------------------------
def assess_url(url: str):
    try:
        from assess_credibility import assess_url_credibility
        return assess_url_credibility(url)
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error analyzing URL: {e}"}

# -----------------------------
# Main interaction
# -----------------------------
if prompt := st.chat_input("Ask a question or enter a URL"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if prompt.startswith("http"):
        # URL → credibility scoring
        with st.spinner("🔍 Assessing credibility..."):
            result = assess_url(prompt)
        st.json(result)
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(result)})
    else:
        # General question → web search + GPT
        with st.spinner("🌎 Searching the web..."):
            snippets = search_web(prompt)
        context = "\n".join(snippets)
        system_message = {"role": "system", "content": f"Use the following web results to answer the user's question:\n{context}"}
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
