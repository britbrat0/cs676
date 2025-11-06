import openai
import json
import streamlit as st
import re
import os

# Set up OpenAI API key securely via Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------
# Load Personas
# -------------------------
# Assume "personas.json" is in the same directory as the app.py file
try:
    with open("personas.json", "r", encoding="utf-8") as f:
        persona_data = json.load(f)
except FileNotFoundError:
    st.error("personas.json not found. Please ensure the file is in the same directory.")
    persona_data = []

def get_persona_by_id(pid):
    for p in persona_data:
        if p["id"] == pid:
            return p
    return None

# -------------------------
# Define Colors for Personas
# -------------------------
PERSONA_COLORS = {
    "Sophia Martinez": "#E6194B",  # Red
    "Jamal Robinson": "#3CB44B",   # Green
    "Eleanor Chen": "#FFE119",     # Yellow
    "Diego Alvarez": "#4363D8",    # Blue
    "Anita Patel": "#F58231",      # Orange
    "Robert Klein": "#911EB4",     # Purple
    "Nia Thompson": "#46F0F0",     # Cyan
    "Marcus Green": "#F032E6",     # Magenta
    "Aisha Mbatha": "#BCF60C",     # Lime
    "Owen Gallagher": "#FABEBE",   # Pink
}

def apply_color_to_text(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    return f'<span style="color: {color}; font-weight: bold;">{text}</span>'

def format_response_line(text, persona_name, highlight=None):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return f'<div style="color: {color}; {background} padding: 4px; margin: 2px 0; border-left: 4px solid {color}; white-space: pre-wrap;">{text}</div>'

def detect_insight_or_concern(text):
    lower_text = text.lower()
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', lower_text):
        return "insight"
    if re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', lower_text):
        return "concern"
    return None

# -------------------------
# Build GPT Prompt
# -------------------------
def build_prompt(personas, feature_inputs, conversation_history=None):
    persona_descriptions = "\n".join([
        f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
        for p in personas
    ])
    
    feature_description = ""
    for key, value in feature_inputs.items():
        if isinstance(value, list):
            value_text = ", ".join(value) if value else "None"
        else:
            value_text = value.strip() if value else "None"
        feature_description += f"{key}:\n{value_text}\n\n"

    prompt = f"""
Personas:
{persona_descriptions}

Feature Inputs:
{feature_description}

Simulate a realistic conversation between these personas about this feature.
- Each persona should speak in turn.
- Use the following template for each persona's response:

[Persona Name]:
- Response: <what they say>
- Reasoning: <why they think that>
- Confidence: <High / Medium / Low>
- Suggested follow-up: <next question they might ask>
"""
    if conversation_history:
        prompt += "\nPrevious conversation:\n" + conversation_history
    return prompt.strip()

# -------------------------
# Generate GPT Response
# -------------------------
def generate_response(feature_inputs, personas, conversation_history=None, model="gpt-4o-mini"):
    prompt = build_prompt(personas, feature_inputs, conversation_history)
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=700
    )
    conversation_update = response.choices[0].message.content
    return conversation_update.strip() + "\n"

# -------------------------
# Feedback Report
# -------------------------
def generate_feedback_report(conversation):
    prompt = f"""
Analyze the following conversation and create a structured feedback report:

Conversation:
{conversation}

Report should include:
- Patterns and themes
- Consensus and disagreements between personas
- Actionable recommendations for feature improvements
- Quantitative metrics (e.g., acceptance, usage likelihood)
- Qualitative insights (specific concerns, suggested improvements)
- Simple visualizations if possible
"""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI product analyst."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=1200
    )
    return response.choices[0].message.content

# -------------------------
# Streamlit App Layout
# -------------------------

st.set_page_config(page_title="AI Persona Focus Group Simulator", layout="wide")
st.title("AI Persona Focus Group Simulator")

# Initialize conversation history in session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = ""
if 'report_text' not in st.session_state:
    st.session_state.report_text = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Feature Inputs & Personas")
    
    # Feature Inputs (using tabs for organization)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(['Text Desc', 'Wireframes', 'Visuals', 'Specs', 'Flows', 'Context'])

    with tab1:
        text_desc = st.text_area("Textual description of the feature", height=100)
    with tab2:
        wireframes = st.file_uploader("Upload wireframes/mockups", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])
    with tab3:
        visual_elements = st.file_uploader("Upload visuals or mockups", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])
    with tab4:
        functional_spec = st.text_area("Functional specifications", height=100)
    with tab5:
        interaction_flow = st.text_area("Interaction flows", height=100)
    with tab6:
        contextual_info = st.text_area("Contextual information", height=100)

    # Persona Selection
    st.subheader("Select Personas")
    persona_options = [p['name'] + f" ({p['occupation']})" for p in persona_data]
    selected_personas_names = st.multiselect("Choose personas for the focus group:", options=persona_options, default=persona_options)
    
    # Map selected names back to persona data
    selected_personas = [p for p in persona_data if p['name'] + f" ({p['occupation']})" in selected_personas_names]

    # User Question Input
    st.subheader("User Question")
    user_question = st.text_input("Enter your question for the personas:")
    
    # Buttons
    col1_a, col1_b, col1_c = st.columns(3)
    with col1_a:
        submit_button = st.button("Ask Personas", type="primary")
    with col1_b:
        clear_button = st.button("Clear Conversation", type="secondary")
    with col1_c:
        report_button = st.button("Generate Report", type="secondary")

with col2:
    st.header("Conversation History")
    # Display area for conversation
    conversation_container = st.container(border=True, height=600)
    
    # Display report area
    st.header("Feedback Report")
    report_container = st.container(border=True, height=600)


# -------------------------
# Button Handlers & Logic (Streamlit style)
# -------------------------

if clear_button:
    st.session_state.conversation_history = ""
    st.session_state.report_text = ""
    st.experimental_rerun()

if submit_button and user_question:
    if not selected_personas:
        st.warning("Please select at least one persona.")
    else:
        feature_inputs = {
            "Text Description": text_desc,
            "Wireframes": [f.name for f in wireframes],
            "Visual Elements": [f.name for f in visual_elements],
            "Functional Specs": functional_spec,
            "Interaction Flows": interaction_flow,
            "Contextual Info": contextual_info
        }

        st.session_state.conversation_history += f"\n\n**User:** {user_question}\n"
        
        with st.spinner("Generating persona responses..."):
            persona_reply = generate_response(feature_inputs, selected_personas, st.session_state.conversation_history)
            st.session_state.conversation_history += persona_reply

        # After generating response, clear report area
        st.session_state.report_text = ""
        st.experimental_rerun() # Rerun to update the history display

if report_button and st.session_state.conversation_history:
    with st.spinner("Generating feedback report..."):
        st.session_state.report_text = generate_feedback_report(st.session_state.conversation_history)
    st.experimental_rerun() # Rerun to update the report display


# -------------------------
# Displaying Content
# -------------------------

# Display the conversation history with formatting
with conversation_container:
    # Use markdown with unsafe_allow_html for styling
    st.markdown(st.session_state.conversation_history, unsafe_allow_html=True)

    # Optional: Implement the detailed line-by-line formatting if needed
    # (The current simple markdown works well too)

# Display the feedback report
with report_container:
    if st.session_state.report_text:
        st.markdown(st.session_state.report_text)
