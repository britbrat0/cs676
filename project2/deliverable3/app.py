import streamlit as st
import openai
import json
import re
import pandas as pd
import altair as alt
import logging
import time
from config import MODEL_CHOICES, DEFAULT_MODEL, PERSONA_COLORS, OPENAI_DEFAULTS, REPORT_DEFAULTS, DEFAULT_PERSONA_PATH
from utils import get_personas, validate_persona, save_personas, get_color_for_persona, format_response_line, detect_insight_or_concern

# -------------------------
# Logging
# -------------------------
logging.basicConfig(filename="app.log", level=logging.INFO)

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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# -------------------------
# Optional Password Protection
# -------------------------
PASSWORD_PROTECT = False
PASSWORD = "YOUR_SECRET_PASSWORD"  # Change to your desired password

if PASSWORD_PROTECT and not st.session_state.authenticated:
    pw = st.text_input("Enter password to access app", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
    else:
        st.stop()

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
# Load Personas
# -------------------------
st.sidebar.header("👥 Personas")
uploaded_persona_file = st.sidebar.file_uploader("Upload personas.json", type=["json"])
personas = get_personas(uploaded_persona_file)
if not personas:
    st.sidebar.error("⚠️ No personas loaded. Add personas.json or upload a file.")
else:
    st.sidebar.success(f"Loaded {len(personas)} personas.")

# -------------------------
# Utility Functions
# -------------------------
def extract_persona_response(line):
    parts = re.split(r":\s*-?\s*Response:?", line, maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else line

def generate_response_with_retry(feature_inputs, personas, history, model, retries=3):
    for attempt in range(retries):
        try:
            return generate_response(feature_inputs, personas, history, model)
        except Exception as e:
            logging.error(f"OpenAI API call failed (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
    st.error("Failed to generate response after multiple attempts.")
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
            resp = generate_response_with_retry(feature_inputs, selected_personas, st.session_state.conversation_history, model_choice)
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

# --- Conversation Display & Sentiment Heatmap
st.header("💬 Conversation History")
if st.session_state.conversation_history.strip():
    lines = st.session_state.conversation_history.split("\n")
    for line in lines:
        matched = False
        for p in selected_personas:
            if line.startswith(p["name"]):
                hl = detect_insight_or_concern(line)
                st.markdown(format_response_line(line, p["name"], hl), unsafe_allow_html=True)
                matched = True
                break
        if not matched:
            st.markdown(line)

    st.info("💡 Continue the discussion using the **question field above** to ask another question.")

    # --- Sentiment Heatmap ---
    sentiment_data = []
    for line in lines:
        for p in selected_personas:
            if line.startswith(p["name"]):
                response_text = extract_persona_response(line)
                sentiment = detect_insight_or_concern(response_text)
                score = 1 if sentiment == "insight" else -1 if sentiment == "concern" else 0
                sentiment_data.append({"Persona": p["name"], "Sentiment": score})

    if sentiment_data:
        df_sentiment = pd.DataFrame(sentiment_data)
        df_summary = df_sentiment.groupby("Persona")["Sentiment"].mean().reset_index()
        st.markdown("## 🔥 Persona Sentiment Heatmap")
        heatmap_chart = alt.Chart(df_summary).mark_bar().encode(
            x=alt.X("Persona", sort="-y"),
            y=alt.Y("Sentiment", title="Average Sentiment Score"),
            color=alt.Color(
                "Sentiment",
                scale=alt.Scale(domain=[-1,0,1], range=["#F94144","#FFC300","#3CB44B"]),
                legend=None
            ),
            tooltip=["Persona", "Sentiment"]
        ).properties(height=200)
        st.altair_chart(heatmap_chart, use_container_width=True)

else:
    st.info("💡 No conversation yet. Ask your personas a question to get started!")

# --- Sidebar Persona Management & Auto Backup
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
            save_personas(personas)  # saves to DEFAULT_PERSONA_PATH
            st.sidebar.success("Added and backed up!")
            st.rerun()

st.sidebar.metric("Total Personas", len(personas))
