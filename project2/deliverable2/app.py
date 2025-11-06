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
# Initialize session state
# -------------------------
if "personas" not in st.session_state:
    # Load personas.json if exists
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            st.session_state.personas = json.load(f)
    except FileNotFoundError:
        st.session_state.personas = []
    except json.JSONDecodeError:
        st.session_state.personas = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

# -------------------------
# Helper Functions
# -------------------------
def get_persona_by_id(pid):
    for p in st.session_state.personas:
        if p["id"] == pid:
            return p
    return None

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

def detect_insight_or_concern(text):
    lower_text = text.lower()
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', lower_text):
        return "insight"
    if re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', lower_text):
        return "concern"
    return None

def format_response_line(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    highlight = detect_insight_or_concern(text)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return f'<div style="color:{color};{background}padding:4px;margin:2px 0;border-left:4px solid {color};white-space:pre-wrap;">{text}</div>'

# -------------------------
# GPT Simulation
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history=None):
    persona_descriptions = "\n".join([
        f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
        for p in personas
    ])
    feature_description = ""
    for k, v in feature_inputs.items():
        if isinstance(v, list):
            v_text = ", ".join(v) if v else "None"
        else:
            v_text = v.strip() if v else "None"
        feature_description += f"{k}: {v_text}\n"
    prompt = f"""
Personas:
{persona_descriptions}

Feature Inputs:
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

def generate_feedback_report(conversation):
    insights = re.findall(r'(?i)(?:great|improve|helpful|benefit|like)', conversation)
    concerns = re.findall(r'(?i)(?:concern|problem|issue|difficult|worry)', conversation)
    total = len(insights) + len(concerns) + 1
    acceptance_rate = round((len(insights) / total) * 100, 1)
    usage_likelihood = min(100, acceptance_rate + 10)

    st.subheader("🧭 Feedback Report")
    st.markdown(f"""
**Key Metrics**
- Acceptance Rate: {acceptance_rate}%
- Usage Likelihood: {usage_likelihood}%

**Insights**
{len(insights)} positive themes identified (e.g., {', '.join(insights[:5])}).

**Concerns**
{len(concerns)} areas of hesitation (e.g., {', '.join(concerns[:5])}).

**Recommendations**
- Address top usability issues mentioned in concerns.
- Reinforce key benefits appreciated by multiple personas.
- Prioritize changes that balance ease of use with perceived value.
""")
    st.subheader("📊 Sentiment Breakdown")
    fig, ax = plt.subplots()
    ax.bar(['Positive', 'Concerns'], [len(insights), len(concerns)], color=['green', 'red'])
    st.pyplot(fig)

# -------------------------
# UI
# -------------------------
st.title("💬 AI-Powered Persona Feedback Simulator")

# Feature input tabs
tabs = st.tabs([
    "Text Description", "Wireframes", "Visual Elements",
    "Functional Specs", "Interaction Flows", "Contextual Info"
])

with tabs[0]:
    text_desc = st.text_area("Enter a textual description of the feature")
with tabs[1]:
    wireframes = st.file_uploader("Upload wireframes or mockups", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)
with tabs[2]:
    visuals = st.file_uploader("Upload visuals or design elements", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)
with tabs[3]:
    functional_spec = st.text_area("Enter functional specifications")
with tabs[4]:
    interaction_flow = st.text_area("Describe interaction flows")
with tabs[5]:
    contextual_info = st.text_area("Provide any contextual information")

# Collect feature inputs
feature_inputs = {
    "Text Description": text_desc,
    "Wireframes": [f.name for f in wireframes] if wireframes else [],
    "Visual Elements": [f.name for f in visuals] if visuals else [],
    "Functional Specs": functional_spec,
    "Interaction Flows": interaction_flow,
    "Contextual Info": contextual_info
}

# Persona selection
def get_persona_options():
    return [f"{p['name']} ({p['occupation']})" for p in st.session_state.personas]

selected_personas_str = st.multiselect("Select Personas", options=get_persona_options(), key="persona_selector")
selected_personas = [p for p in st.session_state.personas if f"{p['name']} ({p['occupation']})" in selected_personas_str]

# Sidebar: Create persona
with st.sidebar.expander("Create New Persona"):
    new_name = st.text_input("Name")
    new_occupation = st.text_input("Occupation")
    new_location = st.text_input("Location")
    new_tech = st.selectbox("Tech Proficiency", ["Low","Medium","High"])
    new_traits = st.text_area("Behavioral Traits (comma separated)")
    if st.button("Add Persona"):
        if new_name.strip():
            new_id = f"p{len(st.session_state.personas)+1}"
            new_persona = {
                "id": new_id,
                "name": new_name.strip(),
                "occupation": new_occupation.strip(),
                "location": new_location.strip(),
                "tech_proficiency": new_tech,
                "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
            }
            st.session_state.personas.append(new_persona)
            # Save back to JSON
            with open("personas.json", "w", encoding="utf-8") as f:
                json.dump(st.session_state.personas, f, indent=2)
            st.success(f"Persona '{new_name}' added!")
            # Reset multiselect to refresh options
            st.session_state.persona_selector = []
            st.experimental_rerun()
        else:
            st.error("Name is required.")

# User question input
user_question = st.text_input("Enter your question for the personas")

col1, col2 = st.columns(2)
with col1:
    if st.button("Ask Personas"):
        if not selected_personas:
            st.warning("Select at least one persona.")
        elif not user_question.strip():
            st.warning("Enter a question.")
        else:
            st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
            response = generate_response(feature_inputs, selected_personas, st.session_state.conversation_history)
            st.session_state.conversation_history += response + "\n"

with col2:
    if st.button("Generate Report"):
        if st.session_state.conversation_history.strip():
            generate_feedback_report(st.session_state.conversation_history)
        else:
            st.warning("No conversation yet to generate report.")

st.markdown("---")
st.markdown("### 💬 Conversation History")
if st.session_state.conversation_history:
    for line in st.session_state.conversation_history.split("\n"):
        matched = False
        for p in selected_personas:
            if line.startswith(p["name"]):
                st.markdown(format_response_line(line, p["name"]), unsafe_allow_html=True)
                matched = True
                break
        if not matched:
            if line.startswith("User:"):
                st.markdown(f"**{line}**")
            elif line.strip():
                st.markdown(line)

if st.button("Clear Conversation"):
    st.session_state.conversation_history = ""
    st.experimental_rerun()
