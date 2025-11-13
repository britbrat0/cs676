import streamlit as st
import openai
import json

from config import MODEL_CHOICES, DEFAULT_MODEL, OPENAI_DEFAULTS, REPORT_DEFAULTS, DEFAULT_PERSONA_PATH
from utils import (
    get_personas,
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

model_choice = st.sidebar.selectbox(
    "Select Model",
    MODEL_CHOICES,
    index=MODEL_CHOICES.index(DEFAULT_MODEL)
)

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
    uploaded_files = st.file_uploader(
        "Upload wireframes/mockups",
        type=["png","jpg","jpeg","pdf"],
        accept_multiple_files=True
    )

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

# --- Conversation Display
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
            save_personas(personas)
            st.sidebar.success("Added!")
            st.rerun()

st.sidebar.metric("Total Personas", len(personas))
