import streamlit as st
import openai
import json
import re
import pandas as pd
import altair as alt

from config import MODEL_CHOICES, DEFAULT_MODEL, PERSONA_COLORS, OPENAI_DEFAULTS, REPORT_DEFAULTS, DEFAULT_PERSONA_PATH
from utils import (
    get_personas,
    validate_persona,
    save_personas,
    get_color_for_persona,
    format_response_line,
    detect_insight_or_concern
)

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="Persona Feedback Simulator", page_icon="💬", layout="wide")

# -------------------------
# Session State
# -------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# -------------------------
# Sidebar – API Key & Model
# -------------------------
st.sidebar.header("🔑 API Configuration")
api_key_input = st.sidebar.text_input(
    "Enter OpenAI API Key",
    type="password",
    value=st.session_state.api_key,
    help="Your API key is not stored permanently"
)

if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input
    st.sidebar.success("✅ API Key Set")
else:
    st.sidebar.warning("⚠️ Enter your OpenAI API key to proceed")

model_choice = st.sidebar.selectbox("Select Model", MODEL_CHOICES, index=MODEL_CHOICES.index(DEFAULT_MODEL))

# -------------------------
# Personas
# -------------------------
st.sidebar.header("👥 Personas")
uploaded_persona_file = st.sidebar.file_uploader("Upload personas.json", type=["json"])
personas = get_personas(uploaded_persona_file)

if not personas:
    st.sidebar.error("⚠️ No personas loaded. Add personas.json or upload a file.")
else:
    st.sidebar.success(f"Loaded {len(personas)} personas.")

# -------------------------
# Persona Colors Helpers
# -------------------------
def get_color_for_persona(name):
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]

def format_response_line(text, name, highlight=None):
    color = get_color_for_persona(name)
    bg = ""
    if highlight == "insight":
        bg = "background-color: #d4edda;"
    elif highlight == "concern":
        bg = "background-color: #f8d7da;"
    return f"<div style='color:{color}; {bg} padding:6px; margin:4px 0; border-left:4px solid {color}; border-radius:4px;'>{text}</div>"

def detect_insight_or_concern(text):
    t = text.lower()
    if re.search(r'\b(think|improve|great|helpful|excellent|love)\b', t):
        return "insight"
    if re.search(r'\b(worry|concern|problem|issue|hard|frustrated)\b', t):
        return "concern"
    return None

def extract_persona_response(line):
    """
    Remove persona name and metadata, return the actual response text.
    Example:
    "John: - Response: I think this is great" -> "I think this is great"
    """
    # Remove persona prefix
    parts = re.split(r":\s*-?\s*Response:?", line, maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip()
    else:
        # fallback to full line
        return line


# -------------------------
# Prompt Builder
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history=""):
    persona_block = "\n".join(
        f"- {p['name']} ({p['occupation']}, {p.get('location','')}, Tech: {p['tech_proficiency']})"
        for p in personas
    )
    feature_block = ""
    for k, v in feature_inputs.items():
        vtxt = ", ".join(v) if isinstance(v, list) else v
        feature_block += f"{k}:\n{vtxt}\n\n"
    prompt = f"""
Personas:
{persona_block}

Features:
{feature_block}

Simulate a realistic persona conversation:
- Each persona speaks in 2–3 sentences.
- Format:

[Persona Name]:
- Response:
- Reasoning:
- Confidence:
- Suggested follow-up:

"""
    if conversation_history:
        prompt += f"\nPrevious conversation:\n{conversation_history}\nContinue naturally."
    return prompt.strip()

# -------------------------
# GPT API Calls
# -------------------------
def generate_response(feature_inputs, personas, history, model):
    if not st.session_state.api_key:
        st.error("API key missing.")
        return ""
    prompt = build_prompt(personas, feature_inputs, history)
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Simulate multi-persona UX research feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=OPENAI_DEFAULTS["temperature"],
            max_tokens=OPENAI_DEFAULTS["max_tokens"]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ {e}")
        return ""

def generate_feedback_report(conversation, model):
    prompt = f"""
Analyze the conversation and produce a structured UX research report.

Conversation:
{conversation}

Sections:
- Executive Summary
- Patterns & Themes
- Consensus Points
- Disagreements & Concerns
- Persona Insights
- Actionable Recommendations
- Quantitative Metrics (acceptance %, likelihood per persona, priority)
- Risk Assessment
"""
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert product analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=REPORT_DEFAULTS["temperature"],
            max_tokens=REPORT_DEFAULTS["max_tokens"]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ {e}")
        return ""

# -------------------------
# Main UI
# -------------------------
st.title("💬 Persona Feedback Simulator")

if not st.session_state.api_key:
    st.stop()

# --- Feature Input
st.header("📝 Feature Description")
tabs = st.tabs(["Text Description", "File Upload"])
with tabs[0]:
    text_desc = st.text_area("Describe your feature", height=150)
with tabs[1]:
    uploaded_files = st.file_uploader("Upload wireframes/mockups", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)

feature_inputs = {
    "Text": text_desc,
    "Files": [f.name for f in uploaded_files] if uploaded_files else []
}

st.markdown("---")

# --- Persona Selection
st.header("👥 Choose Personas")
if not personas:
    st.warning("No personas available.")
    selected_personas = []
else:
    option_labels = [f"{p['name']} ({p['occupation']})" for p in personas]
    default_selection = option_labels[:3]
    selected_labels = st.multiselect("Select personas:", option_labels, default=default_selection)
    selected_personas = [p for p in personas if f"{p['name']} ({p['occupation']})" in selected_labels]

# --- Ask Question
st.header("💭 Ask Your Question")
question = st.text_input("Your question to the personas")
col1, col2, col3 = st.columns([2,2,1])
ask_btn = col1.button("🎯 Ask")
report_btn = col2.button("📊 Generate Report")
clear_btn = col3.button("🗑️ Clear")

if ask_btn:
    if not selected_personas:
        st.warning("Select at least one persona.")
    else:
        if question:
            st.session_state.conversation_history += f"\n**User:** {question}\n"
        with st.spinner("Thinking..."):
            resp = generate_response(feature_inputs, selected_personas, st.session_state.conversation_history, model_choice)
            if resp:
                st.session_state.conversation_history += resp + "\n"
                st.rerun()

if report_btn:
    if st.session_state.conversation_history.strip():
        with st.spinner("Generating report..."):
            report = generate_feedback_report(st.session_state.conversation_history, model_choice)
            st.markdown("## 📊 Feedback Report")
            st.markdown(report)
            st.download_button("Download Report", report, "report.md")
    else:
        st.warning("Nothing to analyze yet.")

if clear_btn:
    st.session_state.conversation_history = ""
    st.rerun()

# --- Conversation Display with Live Sentiment Heatmap
st.header("💬 Conversation History")
if st.session_state.conversation_history.strip():
    conversation_container = st.container()
    
    with conversation_container:
        lines = st.session_state.conversation_history.split("\n")
        for line in lines:
            # Check if line belongs to a persona
            matched = False
            for p in selected_personas:
                if line.startswith(p["name"]):
                    highlight = detect_insight_or_concern(line)
                    st.markdown(format_response_line(line, p["name"], highlight), unsafe_allow_html=True)
                    matched = True
                    break
            # If not matched, treat as user question or neutral text
            if not matched:
                if line.startswith("**User:**") or line.startswith("User:"):
                    st.markdown(f"**{line}**")
                else:
                    st.markdown(line)
    
    st.info("💡 Continue the discussion using the **question field above** to ask another question.")

    # --- Live Persona Sentiment Heatmap ---
    # --- Live Persona Sentiment Heatmap ---
if st.session_state.conversation_history.strip() and selected_personas:
    sentiment_data = []

    for line in st.session_state.conversation_history.split("\n"):
        for p in selected_personas:
            if line.startswith(p["name"]):
                response_text = extract_persona_response(line)
                sentiment = detect_insight_or_concern(response_text)
                score = 1 if sentiment == "insight" else -1 if sentiment == "concern" else 0
                sentiment_data.append({"Persona": p["name"], "Sentiment": score})

    if sentiment_data:
        df_sentiment = pd.DataFrame(sentiment_data)
        # Ensure every persona appears even if score=0
        df_summary = df_sentiment.groupby("Persona")["Sentiment"].mean().reset_index()

        st.markdown("## 🔥 Persona Sentiment Heatmap")
        heatmap_chart = alt.Chart(df_summary).mark_bar().encode(
            x=alt.X("Persona", sort="-y"),
            y=alt.Y("Sentiment", title="Average Sentiment Score", scale=alt.Scale(domain=[-1,1])),
            color=alt.Color(
                "Sentiment",
                scale=alt.Scale(domain=[-1,0,1], range=["#F94144","#FFC300","#3CB44B"]),
                legend=None
            ),
            tooltip=["Persona", "Sentiment"]
        ).properties(height=200)

        st.altair_chart(heatmap_chart, use_container_width=True)

    else:
        st.info("No sentiment data yet for the heatmap.")
else:
    st.info("💡 No conversation yet. Ask your personas a question to get started!")



# --- Sidebar Persona Management
st.sidebar.markdown("---")
st.sidebar.header("➕ Create Persona")
with st.sidebar.form("new_persona_form"):
    name = st.text_input("Name*")
    occupation = st.text_input("Occupation*")
    location = st.text_input("Location")
    tech = st.selectbox("Tech Level", ["Low","Medium","High"])
    traits = st.text_area("Traits (comma-separated)")
    submit = st.form_submit_button("Add Persona")
    if submit:
        if not name or not occupation:
            st.sidebar.error("Name and Occupation required.")
        else:
            new_p = {
                "id": f"p{len(personas)+1}",
                "name": name,
                "occupation": occupation,
                "location": location or "Unknown",
                "tech_proficiency": tech,
                "behavioral_traits": [t.strip() for t in traits.split(",") if t.strip()]
            }
            personas.append(new_p)
            with open(DEFAULT_PERSONA_PATH, "w", encoding="utf-8") as f:
                json.dump(personas, f, indent=2)
            st.sidebar.success("Added!")
            st.rerun()

st.sidebar.metric("Total Personas", len(personas))
