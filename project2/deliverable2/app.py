import streamlit as st
import openai
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# -------------------------
# API Setup
# -------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------
# Load Personas
# -------------------------
def load_personas():
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                st.warning("⚠️ personas.json is empty.")
            return data
    except FileNotFoundError:
        st.error("❌ personas.json not found. Please upload it to your repo.")
        return []
    except json.JSONDecodeError:
        st.error("⚠️ personas.json is not valid JSON.")
        return []

persona_data = load_personas()

def get_persona_by_id(pid):
    for p in persona_data:
        if p["id"] == pid:
            return p
    return None

# -------------------------
# Color and Formatting Helpers
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
    highlight = detect_insight_or_concern(text)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"  # green
    elif highlight == "concern":
        background = "background-color: #f8d7da;"  # red
    return f'<div style="color:{color};{background}padding:4px;margin:2px 0;border-left:4px solid {color};white-space:pre-wrap;">{text}</div>'

def detect_insight_or_concern(text):
    lower_text = text.lower()
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', lower_text):
        return "insight"
    if re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', lower_text):
        return "concern"
    return None

# -------------------------
# GPT Simulation
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history=None):
    persona_descriptions = "\n".join([
        f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
        for p in personas
    ])
    feature_description = "\n".join([f"{k}: {v}" for k, v in feature_inputs.items()])
    prompt = f"""
Personas:
{persona_descriptions}

Feature:
{feature_description}

Simulate a realistic conversation between these personas about this feature.
Each persona should:
- Speak in turn
- Give a Response, Reasoning, Confidence (High/Medium/Low), and a Suggested follow-up
"""
    if conversation_history:
        prompt += "\nPrevious conversation:\n" + conversation_history
    return prompt.strip()

def generate_response(feature_inputs, personas, conversation_history=None):
    prompt = build_prompt(personas, feature_inputs, conversation_history)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=700
    )
    return response.choices[0].message.content.strip()

# -------------------------
# Feedback Report
# -------------------------
def generate_feedback_report(conversation_history):
    """Analyze simulated feedback and generate insights, metrics, and visuals."""
    insights = re.findall(r'(?i)(?:great|improve|helpful|benefit|like)', conversation_history)
    concerns = re.findall(r'(?i)(?:concern|problem|issue|difficult|worry)', conversation_history)

    acceptance_rate = round((len(insights) / (len(insights) + len(concerns) + 1)) * 100, 1)
    usage_likelihood = min(100, acceptance_rate + 10)

    report_text = f"""
### 🧭 Feedback Report

**Key Metrics**
- Acceptance Rate: {acceptance_rate}%
- Usage Likelihood: {usage_likelihood}%

**Insights**
{len(insights)} positive themes identified (e.g., {', '.join(insights[:5])}).

**Concerns**
{len(concerns)} areas of hesitation or challenge (e.g., {', '.join(concerns[:5])}).

**Recommendations**
- Address top usability issues mentioned in concerns.
- Reinforce key benefits appreciated by multiple personas.
- Prioritize changes that balance ease of use with perceived value.
"""

    st.markdown(report_text)

    # Visualization
    st.subheader("📊 Sentiment Breakdown")
    labels = ['Positive', 'Concerns']
    values = [len(insights), len(concerns)]
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    st.pyplot(fig)

# -------------------------
# Streamlit UI
# -------------------------
st.title("💬 AI-Powered Persona Feedback Simulator")

# Tabs for feature inputs
tabs = st.tabs([
    "Text Description", "Wireframes", "Visual Elements",
    "Functional Specs", "Interaction Flows", "Contextual Info"
])

with tabs[0]:
    text_desc = st.text_area("Enter a textual description of the feature")

with tabs[1]:
    wireframes = st.file_uploader("Upload wireframes or mockups", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

with tabs[2]:
    visuals = st.file_uploader("Upload visuals or design elements", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

with tabs[3]:
    functional_spec = st.text_area("Enter functional specifications")

with tabs[4]:
    interaction_flow = st.text_area("Describe interaction flows")

with tabs[5]:
    contextual_info = st.text_area("Provide any contextual information")

# Collect inputs
feature_inputs = {
    "Text Description": text_desc,
    "Wireframes": [f.name for f in wireframes] if wireframes else [],
    "Visual Elements": [f.name for f in visuals] if visuals else [],
    "Functional Specs": functional_spec,
    "Interaction Flows": interaction_flow,
    "Contextual Info": contextual_info
}

# Persona selection
if persona_data:
    persona_options = [f"{p['name']} ({p['occupation']})" for p in persona_data]
    selected_personas = st.multiselect("Select Personas", persona_options)
    personas = [p for p in persona_data if f"{p['name']} ({p['occupation']})" in selected_personas]
else:
    personas = []

# Conversation controls
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

user_question = st.text_input("Enter your question for the personas")

col1, col2 = st.columns(2)
with col1:
    if st.button("Ask Personas"):
        if not personas:
            st.warning("Please select at least one persona.")
        elif not user_question:
            st.warning("Please enter a question.")
        else:
            st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
            response = generate_response(feature_inputs, personas, st.session_state.conversation_history)
            st.session_state.conversation_history += response + "\n"

with col2:
    if st.button("Generate Report"):
        generate_feedback_report(st.session_state.conversation_history)

st.markdown("---")
st.markdown("### 💬 Conversation History")

# Display conversation
if st.session_state.conversation_history:
    for line in st.session_state.conversation_history.split("\n"):
        for p in personas:
            if line.startswith(p["name"]):
                st.markdown(format_response_line(line, p["name"]), unsafe_allow_html=True)
                break
        else:
            if line.startswith("User:"):
                st.markdown(f"**{line}**")
            elif line.strip():
                st.markdown(line)

if st.button("Clear Conversation"):
    st.session_state.conversation_history = ""
    st.experimental_rerun()
