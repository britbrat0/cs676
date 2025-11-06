import streamlit as st
import openai
import json
import re
import matplotlib.pyplot as plt

# -------------------------
# API Setup
# -------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------
# Load Personas
# -------------------------
if "personas" not in st.session_state:
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            st.session_state.personas = json.load(f)
    except FileNotFoundError:
        st.session_state.personas = []

# -------------------------
# Persona Selection
# -------------------------
persona_options = [f"{p['name']} ({p['occupation']})" for p in st.session_state.personas]
selected_personas_str = st.multiselect(
    "Select Personas",
    options=persona_options,
    key="selected_personas"
)

selected_personas = [
    p for p in st.session_state.personas
    if f"{p['name']} ({p['occupation']})" in selected_personas_str
]

# -------------------------
# Define Colors for Personas
# -------------------------
PERSONA_COLORS = {
    "Sophia Martinez": "#E6194B",
    "Jamal Robinson": "#3CB44B",
    "Eleanor Chen": "#FFE119",
    "Diego Alvarez": "#4363D8",
    "Anita Patel": "#F58231",
    "Robert Klein": "#911EB4",
    "Nia Thompson": "#46F0F0",
    "Marcus Green": "#F032E6",
    "Aisha Mbatha": "#BCF60C",
    "Owen Gallagher": "#FABEBE",
}

def format_response_line(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    return f'<div style="color:{color};padding:4px;margin:2px 0;border-left:4px solid {color};white-space:pre-wrap;">{text}</div>'

# -------------------------
# Tabs for Input
# -------------------------
tabs = st.tabs(["Text Description", "File Upload"])

with tabs[0]:
    text_desc = st.text_area("Enter a textual description of the feature", height=150)

with tabs[1]:
    uploaded_files = st.file_uploader(
        "Upload files (images, PDFs, etc.)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True
    )

# -------------------------
# Collect Inputs
# -------------------------
feature_inputs = {
    "Text Description": text_desc,
    "Files": [f.name for f in uploaded_files] if uploaded_files else []
}

# -------------------------
# User Question
# -------------------------
user_question = st.text_input("Enter your question for the personas")

# -------------------------
# Conversation History
# -------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

col1, col2 = st.columns(2)
with col1:
    if st.button("Ask Personas"):
        if not selected_personas:
            st.warning("Please select at least one persona.")
        elif not user_question:
            st.warning("Please enter a question.")
        else:
            st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
            
            # Build GPT prompt
            persona_descriptions = "\n".join([
                f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
                for p in selected_personas
            ])
            feature_description = "\n".join([f"{k}: {v}" for k,v in feature_inputs.items()])
            prompt = f"""
Personas:
{persona_descriptions}

Feature:
{feature_description}

Simulate a realistic conversation between these personas about this feature.
Each persona should speak in turn.
User question: {user_question}
"""
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=700
            )
            reply_text = response.choices[0].message.content.strip()
            st.session_state.conversation_history += reply_text + "\n"

with col2:
    if st.button("Clear Conversation"):
        st.session_state.conversation_history = ""

# -------------------------
# Display Conversation
# -------------------------
st.markdown("---")
st.markdown("### 💬 Conversation History")
for line in st.session_state.conversation_history.split("\n"):
    for p in selected_personas:
        if line.startswith(p["name"]):
            st.markdown(format_response_line(line, p["name"]), unsafe_allow_html=True)
            break
    else:
        if line.startswith("User:"):
            st.markdown(f"**{line}**")
        elif line.strip():
            st.markdown(line)
