# -----------------------------
# Standard Python imports
# -----------------------------
# Import standard libraries needed for the chatbot.
# - os: for operating system operations like file paths.
# - streamlit: to build the web app interface.
# - json: for structured data handling and storing results.
# These imports are essential for session management and UI rendering.
import os
import streamlit as st
import json

# -----------------------------
# Import OpenAI and SerpAPI
# -----------------------------
# Attempt to import OpenAI client to interact with GPT models.
# Attempt to import SerpAPI client to perform web searches.
# If these packages are not installed, provide informative errors.
# Ensures graceful failure and user guidance on missing dependencies.
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
# Retrieve API keys from Streamlit's secure secrets manager.
# The OpenAI key allows GPT model calls.
# The SerpAPI key allows performing web searches.
# If keys are missing, stop the app and prompt the user to configure them.
openai_api_key = st.secrets.get("OPENAI_API_KEY")
serpapi_key = st.secrets.get("SERPAPI_KEY")

if not openai_api_key:
    st.error("OpenAI API key not found. Add it to Streamlit secrets.")
    st.stop()

# -----------------------------
# Initialize OpenAI client
# -----------------------------
# Create an OpenAI client using the provided API key.
# This client will be used to send prompts and receive GPT responses.
# Centralizes GPT calls and handles authentication.
client = OpenAI(api_key=openai_api_key)

# -----------------------------
# Chat session state
# -----------------------------
# Initialize or retrieve the chat session history stored in Streamlit.
# This allows the chatbot to maintain conversation context across messages.
# If this is the first interaction, start with a friendly assistant message.
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! Paste a URL or ask a question."}]

# Display existing messages in the chat interface
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Helper: Web search using SerpAPI
# -----------------------------
# Defines a function to search the web for a given query using SerpAPI.
# Returns a list of top search results containing title, link, and snippet.
# Handles missing API keys and exceptions gracefully, providing informative feedback.
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
# Wraps the credibility scoring function from assess_credibility.py.
# Returns a dictionary with a score (0–1) and a textual explanation.
# Handles exceptions and returns default score if analysis fails.
def assess_url(url: str):
    try:
        from assess_credibility import assess_url_credibility
        return assess_url_credibility(url)
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error analyzing URL: {e}"}

# -----------------------------
# Main interaction with intent detection
# -----------------------------
# Handles user input and decides whether to perform:
# 1. URL credibility scoring
# 2. Skip web search for trivial greetings or casual chat
# 3. Web search + credibility scoring + GPT for questions
# Uses a hybrid approach: keyword list for trivial messages + GPT intent check for other inputs.
if prompt := st.chat_input("Ask a question or enter a URL"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # -----------------------------
    # Step 1: Check if input is a URL
    # -----------------------------
    # If user input starts with "http", we assume it's a URL.
    # Evaluate the credibility of the URL and display results.
    if prompt.startswith("http"):
        with st.spinner("🔍 Assessing credibility..."):
            result = assess_url(prompt)
        st.json(result)
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(result)})

    else:
        # -----------------------------
        # Step 2: Check for trivial messages
        # -----------------------------
        # Compare input to a predefined list of greetings or casual chat phrases.
        # If input matches, skip web search and provide a direct response.
        NO_SEARCH_KEYWORDS = [
            "hello", "hi", "hey", "good morning", "good afternoon",
            "thanks", "thank you", "how are you"
        ]
        prompt_clean = prompt.lower().strip()

        if any(kw in prompt_clean for kw in NO_SEARCH_KEYWORDS):
            msg = "Hello! How can I help you today?"
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)

        else:
            # -----------------------------
            # Step 3: Optional GPT intent classification
            # -----------------------------
            # Ask GPT whether the input requires a web search.
            # Only perform web search if GPT returns "SEARCH"; otherwise, skip.
            try:
                intent_prompt = f"""
                Classify the following message:
                '{prompt}'

                Reply with either:
                - SEARCH: if the message is a question that requires web lookup
                - NO_SEARCH: if it's a greeting, thanks, or casual chat
                Only reply with SEARCH or NO_SEARCH.
                """

                intent_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": intent_prompt}]
                )

                intent = intent_response.choices[0].message.content.strip()
            except Exception:
                intent = "SEARCH"

            if intent == "NO_SEARCH":
                msg = "Hello! How can I help you?"
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message("assistant").write(msg)

            else:
                # -----------------------------
                # Step 4: Web search + credibility scoring + GPT response
                # -----------------------------
                # Perform web search, assess credibility for each result,
                # construct context for GPT, and generate final answer.
                with st.spinner("🌎 Searching the web..."):
                    web_results = search_web(prompt)

                if not web_results:
                    st.warning("No search results found.")
                    st.stop()

                # Assess credibility for each result (used only for GPT context)
                for r in web_results:
                    score = assess_url(r["link"]) if r["link"] else {"score": 0.0, "explanation": "No link"}
                    r["credibility_score"] = score.get("score", 0)
                    r["credibility_explanation"] = score.get("explanation", "")

                # Prepare context for GPT without displaying individual sources
                context = "\n\n".join(
                    [f"Source: {r['link']}\nSnippet: {r['snippet']}\nCredibility Score: {r['credibility_score']}" 
                     for r in web_results]
                )

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
                            model="gpt-4o-mini",
                            messages=messages
                        )
                    msg = response.choices[0].message.content
                except Exception as e:
                    msg = f"Error with OpenAI API: {e}"

                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message("assistant").write(msg)
