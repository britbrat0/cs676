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
def load_personas():
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if data else []
    except FileNotFoundError:
        st.error("❌ personas.json not found. Please upload it to your repo.")
        return []
    except json.JSONDecodeError:
        st.error("⚠️ personas.json is not valid JSON.")
        return []

# Initialize personas in session_state
if "personas" not in st.session_state:
    loaded_personas = load_personas()
    st.session_state.personas = loaded_personas
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

def get_persona_by_id(pid):
    for p in st.session_state.personas:
        if p["id"] == pid:
            return p
    return None

# -------------------------
# Sidebar: Create Persona
# -------------------------
with st.sidebar.expander("Create New Persona"):
    new_name = st.text_input("Name")
    new_occupation = st.text_input("Occupation")
    new_location = st.text_input("Location")
    new_tech = st.selectbox("Tech Proficiency", ["Low", "Medium", "High"])
    new_traits = st.text_area("Behavioral Traits (comma separated)")
    if st.button("Add Persona"):
        if new_name.strip():
            new_persona = {
                "id": f"p{len(st.session_state.personas)+1}",
                "name": new_name.strip(),
                "occupation": new_occupation.strip(),
                "location": new_location.strip(),
                "tech_proficiency": new_tech,
                "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
            }
            st.session_state.personas.append(new_persona)
            st.success(f"Persona '{new_name}' added!")
            st.experimental_rerun()
        else:
            st.error("Name is required.")

# -------------------------
# Colors and formatting
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
            v_text = ", ".join([f for f in v]) if v else "None"
        else:
            v_text = v.strip() if v else "None"
        feature_description += f"{k}:\n{v_text}\n\n"
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

# -------------------------
# Feedback Report
# -------------------------
def generate_feedback_report(conversation_history):
    insights = re.findall(r'(?i)(?:great|improve|helpful|benefit|like)', conversation_history)
    concerns = re.findall(r'(?i)(?:concern|problem|issue|difficult|worry)', conversation_history)
    acceptance_rate = round((len(insights) / (len(insights) + len(concerns) + 1)) * 100, 1)
    usage_likelihood = min(100, acceptance_rate + 10)

    st.markdown(f"### 🧭 Feedback Report")
    st.markdown(f"**Key Metrics**\n- Acceptance Rate: {acceptance_rate}%\n- Usage Likelihood: {usage_likelihood}%")
    st.markdown(f"**Insights** ({len(insights)} positive themes): {', '.join(insights[:5])}")
    st.markdown(f"**Concerns** ({len(concerns)} issues): {', '.join(concerns[:5])}")
    st.markdown(f"**Recommendations**\n- Address top usability issues mentioned in concerns.\n- Reinforce benefits noted by personas.\n- Prioritize changes that balance ease of use and value.")

    st.subheader("📊 Sentiment Breakdown")
    labels = ['Positive', 'Concerns']
    values = [len(insights), len(concerns)]
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=['#28a745', '#dc3545'])
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
    wireframes = st.file_uploader("Upload wireframes/mockups", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)
with tabs[2]:
    visuals = st.file_uploader("Upload visuals or design elements", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)
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
if st.session_state.personas:
    persona_options = [f"{p['name']} ({p['occupation']})" for p in st.session_state.personas]
    selected_personas = st.multiselect("Select Personas", options=persona_options)
    personas = [p for p in st.session_state.personas if f"{p['name']} ({p['occupation']})" in selected_personas]
else:
    personas = []
    st.warning("No personas available. Add some in the sidebar.")

# Conversation
user_question = st.text_input("Enter your question for the personas")

col1, col2 = st.columns(2)
with col1:
    if st.button("Ask Personas"):
        if not personas:
            st.warning("Select at least one persona.")
        elif not user_question:
            st.warning("Enter a question.")
        else:
            st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
            response = generate_response(feature_inputs, personas, st.session_state.conversation_history)
            st.session_state.conversation_history += response + "\n"

with col2:
    if st.button("Generate Report"):
        if st.session_state.conversation_history:
            generate_feedback_report(st.session_state.conversation_history)
        else:
            st.warning("No conversation to generate a report from.")

st.markdown("---")
st.markdown("### 💬 Conversation History")
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
