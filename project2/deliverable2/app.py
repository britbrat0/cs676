import streamlit as st
import json
import re
import openai

# -------------------------
# Load Personas
# -------------------------
try:
    with open("personas.json", "r", encoding="utf-8") as f:
        persona_data = json.load(f)
except FileNotFoundError:
    persona_data = []

# -------------------------
# Persona Colors
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

# -------------------------
# Helper Functions
# -------------------------
def apply_color(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    return f'<span style="color:{color}; font-weight:bold;">{text}</span>'

def format_response_line(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    lower = text.lower()
    bg = ""
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', lower):
        bg = "background-color:#d4edda;"  # insight
    elif re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', lower):
        bg = "background-color:#f8d7da;"  # concern
    return f'<div style="color:{color};{bg} padding:4px; margin:2px 0; border-left:4px solid {color}; white-space:pre-wrap;">{text}</div>'

def get_persona_by_name(name):
    for p in persona_data:
        if p["name"] == name:
            return p
    return None

# -------------------------
# Sidebar: Create Persona
# -------------------------
st.sidebar.header("Create New Persona")
new_name = st.sidebar.text_input("Name")
new_occupation = st.sidebar.text_input("Occupation")
new_location = st.sidebar.text_input("Location")
new_tech = st.sidebar.selectbox("Tech Proficiency", ["Low", "Medium", "High"])
new_traits = st.sidebar.text_area("Behavioral Traits (comma separated)")

if st.sidebar.button("Add Persona"):
    if new_name.strip():
        new_persona = {
            "id": f"p{len(persona_data)+1}",
            "name": new_name.strip(),
            "occupation": new_occupation.strip(),
            "location": new_location.strip(),
            "tech_proficiency": new_tech,
            "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
        }
        persona_data.append(new_persona)
        st.sidebar.success(f"Persona '{new_name}' added!")
    else:
        st.sidebar.error("Name is required.")

# -------------------------
# Main: Feature Input Tabs
# -------------------------
st.title("Simulated Persona Feedback App")

text_desc = st.text_area("Text Description", placeholder="Enter textual description")
functional_spec = st.text_area("Functional Specs")
interaction_flow = st.text_area("Interaction Flows")
contextual_info = st.text_area("Contextual Info")
wireframes = st.file_uploader("Upload Wireframes / Mockups", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)
visual_elements = st.file_uploader("Upload Visuals", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)

# -------------------------
# Main: Persona Selection
# -------------------------
persona_options = [f"{p['name']} ({p['occupation']})" for p in persona_data]
selected_personas = st.multiselect("Select Personas", options=persona_options)

# -------------------------
# Question Input
# -------------------------
user_question = st.text_input("Enter your question for the personas")

# -------------------------
# Conversation Storage
# -------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

# -------------------------
# Generate Response Function
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history):
    persona_desc = "\n".join([f"- {p['name']} ({p['occupation']}, {p['location']}, Tech:{p['tech_proficiency']}, Traits:{', '.join(p['behavioral_traits'])})" for p in personas])
    
    feature_text = ""
    for key, value in feature_inputs.items():
        if isinstance(value, list):
            value_text = ", ".join([f.name for f in value]) if value else "None"
        else:
            value_text = value if value else "None"
        feature_text += f"{key}:\n{value_text}\n\n"
    
    prompt = f"""
Personas:
{persona_desc}

Feature Inputs:
{feature_text}

Simulate a conversation between these personas about this feature.
- Each persona speaks in turn.
- Use the template:
[Persona Name]:
- Response: <what they say>
- Reasoning: <why they think that>
- Confidence: <High/Medium/Low>
- Suggested follow-up: <next question they might ask>
"""
    if conversation_history:
        prompt += f"\nPrevious conversation:\n{conversation_history}"
    return prompt.strip()

def generate_response(feature_inputs, selected_personas, conversation_history):
    personas_objs = [get_persona_by_name(p.split(" (")[0]) for p in selected_personas]
    prompt = build_prompt(personas_objs, feature_inputs, conversation_history)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":"You are an AI facilitator for a virtual focus group."},
            {"role":"user", "content":prompt}
        ],
        max_completion_tokens=700
    )
    return response.choices[0].message.content.strip()

# -------------------------
# Submit Button
# -------------------------
if st.button("Ask Personas"):
    if not user_question.strip():
        st.warning("Enter a question first!")
    elif not selected_personas:
        st.warning("Select at least one persona!")
    else:
        feature_inputs = {
            "Text Description": text_desc,
            "Wireframes": wireframes,
            "Visual Elements": visual_elements,
            "Functional Specs": functional_spec,
            "Interaction Flows": interaction_flow,
            "Contextual Info": contextual_info
        }
        st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
        reply = generate_response(feature_inputs, selected_personas, st.session_state.conversation_history)
        st.session_state.conversation_history += reply + "\n"

# -------------------------
# Display Conversation
# -------------------------
if st.session_state.conversation_history:
    st.markdown("### Conversation So Far:")
    for line in st.session_state.conversation_history.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            st.markdown("<br>", unsafe_allow_html=True)
            continue
        is_user = line_stripped.startswith("User:")
        formatted_line = None
        for p in selected_personas:
            name = p.split(" (")[0]
            if line_stripped.startswith(name) or line_stripped.startswith(f"[{name}]"):
                formatted_line = format_response_line(line_stripped, name)
                break
        if is_user:
            st.markdown(f"<div style='color:#444444;'><b>{line_stripped}</b></div>", unsafe_allow_html=True)
        elif formatted_line:
            st.markdown(formatted_line, unsafe_allow_html=True)
        else:
            st.markdown(line_stripped)
            
# -------------------------
# Report Generation Placeholder
# -------------------------
if st.button("Generate Feedback Report"):
    st.info("Report generation feature coming soon! This will summarize key insights, concerns, consensus, disagreements, and provide visualizations.")
