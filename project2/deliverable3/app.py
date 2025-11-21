# app.py
import streamlit as st
import os
from typing import List, Dict
import json

from config import MODEL_CHOICES, DEFAULT_MODEL, DEFAULT_PERSONA_PATH
from utils import (
    get_personas,
    format_response_line,
    detect_insight_or_concern,
    extract_persona_response,
    build_sentiment_summary,
    build_heatmap_chart,
    save_personas,
)
from ai_helpers import generate_response_with_retry, generate_feedback_report

# -------------------------
# Page config & state
# -------------------------
st.set_page_config(page_title="Persona Feedback Simulator", page_icon="💬", layout="wide")

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# -------------------------
# Sidebar: API key, model, personas upload
# -------------------------
st.sidebar.header("🔑 API Configuration")
api_env = os.getenv("OPENAI_API_KEY", "")
api_key_input = st.sidebar.text_input("OpenAI API Key (or set OPENAI_API_KEY variable)", type="password", value=st.session_state.api_key or api_env)
if api_key_input:
    st.session_state.api_key = api_key_input
    import openai
    openai.api_key = api_key_input
else:
    st.sidebar.info("Enter OpenAI API key to enable generation.")

model_choice = st.sidebar.selectbox("Model", MODEL_CHOICES, index=MODEL_CHOICES.index(DEFAULT_MODEL))

st.sidebar.markdown("---")
st.sidebar.header("👥 Personas")
uploaded = st.sidebar.file_uploader("Upload personas.json (optional)", type=["json"])
personas = get_personas(uploaded, path=DEFAULT_PERSONA_PATH)
st.sidebar.metric("Total Personas", len(personas))

# -------------------------
# Main UI - Feature input
# -------------------------
st.title("💬 Persona Feedback Simulator")
st.header("📝 Feature Description")
tabs = st.tabs(["Text", "Files"])
with tabs[0]:
    text_desc = st.text_area("Describe your feature", height=160)
with tabs[1]:
    uploaded_files = st.file_uploader("Upload wireframes / mockups", accept_multiple_files=True, type=["png","jpg","jpeg","pdf"])

feature_inputs = {
    "Text": text_desc or "",
    "Files": [f.name for f in (uploaded_files or [])]
}
st.markdown("---")

# -------------------------
# Persona selection
# -------------------------
st.header("👥 Choose Personas")
if not personas:
    st.warning("No personas available. Create personas in the sidebar or upload a personas.json.")
    selected_personas: List[Dict] = []
else:
    labels = [f"{p['name']} ({p.get('occupation','')})" for p in personas]
    defaults = labels[:3]
    selected_labels = st.multiselect("Select personas:", labels, default=defaults)
    selected_personas = [p for p in personas if f"{p['name']} ({p.get('occupation','')})" in selected_labels]

# -------------------------
# Ask / Report / Clear controls
# -------------------------
st.header("💭 Ask Your Question")
question = st.text_input("Question to personas")
c1, c2, c3 = st.columns([2, 2, 1])
ask_btn = c1.button("🎯 Ask")
report_btn = c2.button("📊 Generate Report")
clear_btn = c3.button("🗑️ Clear")

if ask_btn:
    if not st.session_state.api_key:
        st.warning("Please set your OpenAI API key in the sidebar or via OPENAI_API_KEY.")
    elif not selected_personas:
        st.warning("Please select at least one persona.")
    elif not (question or feature_inputs["Text"]):
        st.warning("Enter a question or feature description.")
    else:
        if question:
            st.session_state.conversation_history += f"\n**User:** {question}\n"
        with st.spinner("Generating persona responses..."):
            try:
                resp = generate_response_with_retry(feature_inputs, selected_personas, st.session_state.conversation_history, model_choice)
                st.session_state.conversation_history += resp + "\n"
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate response: {e}")

if report_btn:
    if not st.session_state.conversation_history.strip():
        st.warning("Nothing to analyze yet.")
    else:
        with st.spinner("Generating feedback report..."):
            try:
                report = generate_feedback_report(st.session_state.conversation_history, model_choice)
                st.markdown("## 📊 Feedback Report")
                st.markdown(report)
                st.download_button("⬇️ Download Report", report, "persona_report.md")
            except Exception as e:
                st.error(f"Failed to generate report: {e}")

if clear_btn:
    st.session_state.conversation_history = ""
    st.rerun()

st.markdown("---")

# -------------------------
# Conversation display + heatmap
# -------------------------
st.header("💬 Conversation History")
if st.session_state.conversation_history.strip() and selected_personas:
    lines = [ln for ln in st.session_state.conversation_history.split("\n") if ln.strip()]

    # Display conversation lines with persona formatting
    for line in lines:
        matched = False
        log.info(f"[LINE] raw conversation line = {line}")

        for p in selected_personas:
            if line.startswith(p["name"]):
                response_text = extract_persona_response(line)
                hl = detect_insight_or_concern(response_text)
    
                log.info(
                    f"[PARSE] persona={p['name']} | extracted='{response_text}' | highlight={hl}"
                )
    
                st.markdown(format_response_line(line, p["name"], hl), unsafe_allow_html=True)
                matched = True
                break
        if not matched:
            st.markdown(line)


    st.info("💡 Continue the discussion using the **question field above** to ask another question.")

    # Build & show heatmap
    df_summary = build_sentiment_summary(lines, selected_personas)
    chart = build_heatmap_chart(df_summary)
    st.markdown("## 🔥 Persona Sentiment Heatmap")
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("💡 No conversation yet. Ask your personas a question to get started!")

# -------------------------
# Sidebar persona creation (persist)
# -------------------------
st.sidebar.markdown("---")
st.sidebar.header("➕ Create Persona")
with st.sidebar.form("new_persona_form"):
    name = st.text_input("Name*")
    occupation = st.text_input("Occupation*")
    location = st.text_input("Location")
    tech = st.selectbox("Tech Proficiency", ["Low", "Medium", "High"])
    traits = st.text_area("Behavioral traits (comma-separated)")
    submit = st.form_submit_button("Add Persona")
    if submit:
        if not name or not occupation:
            st.sidebar.error("Name and Occupation required.")
        else:
            new_p = {
                "id": f"p{len(personas)+1}",
                "name": name.strip(),
                "occupation": occupation.strip(),
                "location": location.strip() or "Unknown",
                "tech_proficiency": tech,
                "behavioral_traits": [t.strip() for t in traits.split(",") if t.strip()]
            }
            personas.append(new_p)
            if save_personas(personas, path=DEFAULT_PERSONA_PATH):
                st.sidebar.success("✅ Persona added and saved.")
            else:
                st.sidebar.error("❌ Persona added but failed to save.")
            st.rerun()

st.sidebar.metric("Total Personas", len(personas))
