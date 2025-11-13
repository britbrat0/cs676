import streamlit as st
import openai
import json
import re
import pandas as pd
import altair as alt
import os

# -------------------------
# App Config
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
# Sidebar – API Key
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
    st.sidebar.warning("⚠️ Please enter your OpenAI API key to use the app")

model_choice = st.sidebar.selectbox(
    "Select Model",
    ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    index=0
)

# -------------------------
# Personas (clean unified flow)
# -------------------------
from utils import get_personas

st.sidebar.markdown("---")
st.sidebar.header("👥 Personas")

uploaded_persona_file = st.sidebar.file_uploader("Upload personas.json", type=["json"])
personas = get_personas(uploaded_persona_file)

if not personas:
    st.sidebar.error("⚠️ No personas found. Add personas.json to the repo or upload a file.")
else:
    st.sidebar.success(f"Loaded {len(personas)} personas.")

# -------------------------
# Persona Visualization Colors
# -------------------------
PERSONA_COLORS = {}

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

# -------------------------
# Prompt Construction
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history):
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
# GPT Response
# -------------------------
def generate_response(feature_inputs, personas, history, model):
    if not st.session_state.api_key:
        st.error("API key missing.")
        return ""

    try:
        prompt = build_prompt(personas, feature_inputs, history)
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You simulate multi-persona UX research feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ {e}")
        return ""

# -------------------------
# Feedback Report
# -------------------------
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
            max_tokens=2500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(str(e))
        return ""

# -------------------------
# Main UI
# -------------------------
st.title("💬 Persona Feedback Simulator")

if not st.session_state.api_key:
    st.stop()

# Feature input
st.header("📝 Feature Description")
tabs = st.tabs(["Text Description", "File Upload"])

with tabs[0]:
    text_desc = st.text_area("Describe your feature", height=150)

with tabs[1]:
    uploaded_files = st.file_uploader(
        "Upload wireframes/mockups",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True
    )

feature_inputs = {
    "Text": text_desc,
    "Files": [f.name for f in uploaded_files] if uploaded_files else []
}

st.markdown("---")

# Persona selection
st.header("👥 Choose Personas")

if not personas:
    st.warning("No personas available.")
    selected_personas = []
else:
    option_labels = [f"{p['name']} ({p['occupation']})" for p in personas]
    default_selection = option_labels[:3]
    selected_labels = st.multiselect("Select personas:", option_labels, default=default_selection)

    selected_personas = [
        p for p in personas
        if f"{p['name']} ({p['occupation']})" in selected_labels
    ]

# Ask a question
st.header("💭 Ask Your Question")
question = st.text_input("Your question to the personas")

col1, col2, col3 = st.columns([2,2,1])
ask_btn = col1.button("🎯 Ask")
report_btn = col2.button("📊 Generate Report")
clear_btn = col3.button("🗑️ Clear")

# --- Handle Ask Personas
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

# --- Handle Report
if report_btn:
    if not st.session_state.conversation_history.strip():
        st.warning("Nothing to analyze yet.")
    else:
        with st.spinner("Generating report..."):
            report = generate_feedback_report(st.session_state.conversation_history, model_choice)
            st.markdown("## 📊 Feedback Report")
            st.markdown(report)
            st.download_button("Download Report", report, "report.md")

# --- Handle Clear
if clear_btn:
    st.session_state.conversation_history = ""
    st.rerun()

# -------------------------
# Conversation Display
# -------------------------
st.header("💬 Conversation History")

if st.session_state.conversation_history.strip():
    lines = st.session_state.conversation_history.split("\n")
    for line in lines:
        if any(line.startswith(p["name"]) for p in selected_personas):
            persona = next(p for p in selected_personas if line.startswith(p["name"]))
            hl = detect_insight_or_concern(line)
            st.markdown(format_response_line(line, persona["name"], hl), unsafe_allow_html=True)
        else:
            st.markdown(line)
else:
    st.info("No conversation yet.")

# -------------------------
# Sidebar – Persona Management
# -------------------------
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
            with open("personas.json", "w", encoding="utf-8") as f:
                json.dump(personas, f, indent=2)
            st.sidebar.success("Added!")
            st.rerun()

st.sidebar.metric("Total Personas", len(personas))
