# -----------------------------
# Standard Python imports
# -----------------------------
# Import essential libraries: os for environment operations,
# streamlit for building the web app, and json for structured data handling.
# These are foundational for the chatbot interface and storing results.
import os
import streamlit as st
import json

# -----------------------------
# Import OpenAI and SerpAPI
# -----------------------------
# Attempt to import the OpenAI client and SerpAPI client.
# If these packages are not installed, provide a clear error message.
# This ensures the app fails gracefully if dependencies are missing.
try:
    from openai import OpenAI
except ModuleNotFoundError:
    print("OpenAI package not installed. Check requirements.txt.")
    raise

try:
    from serpapi.google_search import GoogleSearch
except ModuleNotFoundError:
    print("google-search-results package not installed. Check requirements.txt.")
    raise


# -----------------------------
# API Keys from Streamlit Secrets
# -----------------------------
# Retrieve the OpenAI and SerpAPI keys from Streamlit's secrets manager.
# Keys are required for API access; if missing, the app stops and prompts the user.
openai_api_key = st.secrets.get("OPENAI_API_KEY")
serpapi_key = st.secrets.get("SERPAPI_KEY")

if not openai_api_key:
    st.error("OpenAI API key not found. Add it to Streamlit secrets.")
    st.stop()

# -----------------------------
# Initialize OpenAI client
# -----------------------------
# Create an OpenAI client instance using the API key.
# This client will be used to call GPT models for chat responses.
client = OpenAI(api_key=openai_api_key)

# -----------------------------
# Chat session state
# -----------------------------
# Initialize the chat session state in Streamlit to store conversation history.
# If this is the first interaction, start with a welcome message.
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! Paste a URL or ask a question."}]

# Display existing messages in the chat interface
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Helper: Web search using SerpAPI
# -----------------------------
# Define a function to search the web for a query using SerpAPI.
# Returns a list of top search results with title, link, and snippet.
# Handles exceptions and missing API keys gracefully.
def search_web(query: str):
    if not serpapi_key:
        return []
    try:
        params = {"q": query, "api_key": serpapi_key, "num": 3}
        search = GoogleSearch(params)
        results = search.get_dict()
        snippets = []
        if "organic_results" in results:
            for r in results["organic_results"][:3]:
                snippets.append({
                    "title": r.get("title", "No title"),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", "")
                })
        return snippets
    except Exception as e:
        return [{"title": "Error", "snippet": str(e), "link": ""}]

# -----------------------------
# Helper: Assess URL credibility
# -----------------------------
# Wrap the credibility scoring function from assess_credibility.py.
# Returns a JSON-like dictionary with score and explanation.
# Handles exceptions and returns a default 0 score if analysis fails.
def assess_url(url: str):
    try:
        from assess_credibility import assess_url_credibility
        return assess_url_credibility(url)
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error analyzing URL: {e}"}

# -----------------------------
# Main interaction
# -----------------------------
# Main chat input handler. Determines whether the input is a URL or general query.
# For URLs: run credibility scoring.
# For questions: perform web search, assess credibility of results, then query GPT.
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
        # General question → web search + credibility scoring + GPT
        with st.spinner("🌎 Searching the web..."):
            web_results = search_web(prompt)

        if not web_results:
            st.warning("No search results found.")
            st.stop()

        # Assess credibility for each result
        st.subheader("Credibility of Sources")
        for r in web_results:
            score = assess_url(r["link"]) if r["link"] else {"score": 0.0, "explanation": "No link"}
            st.write(f"**{r['title']}**")
            st.write(f"🔗 {r['link']}")
            st.write(f"🧭 Credibility Score: {score.get('score', 0):.2f}")
            st.caption(score.get("explanation", ""))
            st.divider()
            r["credibility_score"] = score.get("score", 0)
            r["credibility_explanation"] = score.get("explanation", "")

        # Prepare context for GPT
        context = "\n\n".join(
            [f"Source: {r['link']}\nSnippet: {r['snippet']}\nCredibility Score: {r['credibility_score']}" for r in web_results]
        )

        # System message to instruct GPT to use web results and credibility scores
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the web results and their credibility scores to answer the user's question. "
                "Give preference to highly credible sources.\n\n"
                f"{context}"
            )
        }

        messages = [system_message] + st.session_state.messages

        # Generate GPT response
        try:
            with st.spinner("🤖 Generating answer..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # smaller + faster than full GPT-4
                    messages=messages
                )
            msg = response.choices[0].message.content
        except Exception as e:
            msg = f"Error with OpenAI API: {e}"

        # Append GPT response to chat session and display
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
