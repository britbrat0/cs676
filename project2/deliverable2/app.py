import streamlit as st
import openai
import json
import re
import matplotlib.pyplot as plt

# -------------------------
# OpenAI API
# -------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------
# Load / Initialize Personas
# -------------------------
if "personas" not in st.session_state:
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            st.session_state.personas = json.load(f)
    except FileNotFoundError:
        st.session_state.personas = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

# -------------------------
# Sidebar: Add New Persona
# -------------------------
with st.sidebar.expander("Create New Persona"):
    name = st.text_input("Name")
    occupation = st.text_input("Occupation")
    location = st.text_input("Location")
    tech = st.selectbox("Tech Proficiency", ["Low", "Medium", "High"])
    traits = st.text_area("Behavioral Traits (comma separated)")
    if st.button("Add Persona"):
        if name.strip():
            new_id = f"p{len(st.session_state.personas)+1}"
            new_persona = {
                "id": new_id,
                "name": name.strip(),
                "occupation": occupation.strip(),
                "location": location.strip(),
                "tech_proficiency": tech,
                "behavioral_traits": [t.strip() for t in traits.split(",") if t.strip()]
            }
            st.session_state.personas.append(new_persona)
            st.success(f"Persona '{name}' added!")

# -------------------------
# Feature Inputs Tabs
# -------------------------
st.header("Feature Inputs")
tabs = st.tabs(["Text Description", "Wireframes", "Visual Elements",
                "Functional Specs", "Interaction Flows", "Contextual Info"])

with tabs[0]:
    text_desc = st.text_area("Text Description")

with tabs[1]:
    wireframes = st.file_uploader("Upload wireframes/mockups", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)

with tabs[2]:
    visuals = st.file_uploader("Upload visuals/design elements", type=["png","jpg","jpeg","pdf"], accept_multiple_files=True)

with tabs[3]:
    functional_spec = st.text_area("Functional Specs")

with tabs[4]:
    interaction_flow = st.text_area("Interaction Flows")

with tabs[5]:
    contextual_info = st.text_area("Contextual Info")

feature_inputs = {
    "Text Description": text_desc,
    "Wireframes": [f.name for f in wireframes] if wireframes else [],
    "Visual Elements": [f.name for f in visuals] if visuals else [],
    "Functional Specs": functional_spec,
    "Interaction Flows": interaction_flow,
    "Contextual Info": contextual_info
}

# -------------------------
# Persona Selection
# -------------------------
st.header("Select Personas")
persona_options = [f"{p['name']} ({p['occupation']})" for p in st.session_state.personas]
selected_personas_str = st.multiselect("Select Personas", options=persona_options)

# Map selected strings back to persona objects
personas = [p for p in st.session_state.personas if f"{p['name']} ({p['occupation']})" in selected_personas_str]

# -------------------------
# Conversation Inputs
# -------------------------
st.header("Ask Personas")
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
            
            # Build prompt for GPT
            persona_descriptions = "\n".join([
                f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
                for p in personas
            ])
            feature_text = "\n".join([f"{k}: {v}" for k,v in feature_inputs.items()])
            prompt = f"""
Personas:
{persona_descriptions}

Feature Inputs:
{feature_text}

Simulate a realistic conversation. Each persona should respond with:
- Response
- Reasoning
- Confidence (High/Medium/Low)
- Suggested follow-up
"""
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=700
            )
            st.session_state.conversation_history += response.choices[0].message.content.strip() + "\n"

with col2:
    if st.button("Generate Feedback Report"):
        if not st.session_state.conversation_history.strip():
            st.warning("No conversation yet to generate report.")
        else:
            # Simple report extraction
            conversation = st.session_state.conversation_history
            insights = re.findall(r'(?i)(?:great|improve|helpful|benefit|like)', conversation)
            concerns = re.findall(r'(?i)(?:concern|problem|issue|difficult|worry)', conversation)
            acceptance_rate = round((len(insights) / (len(insights)+len(concerns)+1))*100,1)
            usage_likelihood = min(100, acceptance_rate+10)

            st.subheader("🧭 Feedback Report")
            st.markdown(f"**Acceptance Rate:** {acceptance_rate}%")
            st.markdown(f"**Usage Likelihood:** {usage_likelihood}%")
            st.markdown(f"**Insights:** {len(insights)} positive mentions ({', '.join(insights[:5])})")
            st.markdown(f"**Concerns:** {len(concerns)} mentions ({', '.join(concerns[:5])})")

            # Visualization
            fig, ax = plt.subplots()
            ax.bar(["Positive","Concerns"], [len(insights), len(concerns)], color=["#d4edda","#f8d7da"])
            st.pyplot(fig)

# -------------------------
# Display Conversation History
# -------------------------
st.markdown("---")
st.subheader("💬 Conversation History")
for line in st.session_state.conversation_history.split("\n"):
    # Simple highlight of insights/concerns
    highlight = None
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', line.lower()):
        highlight = "insight"
    elif re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', line.lower()):
        highlight = "concern"
    color = "#000"
    background = ""
    if highlight=="insight":
        background="#d4edda"
    elif highlight=="concern":
        background="#f8d7da"
    st.markdown(f"<div style='color:{color}; background:{background}; padding:4px; margin:2px;'>{line}</div>", unsafe_allow_html=True)

# -------------------------
# Clear Conversation
# -------------------------
if st.button("Clear Conversation"):
    st.session_state.conversation_history = ""
    st.experimental_rerun()
