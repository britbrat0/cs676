import streamlit as st
import json
import openai
import re
from pathlib import Path

# -------------------------
# Load Personas
# -------------------------
persona_path = Path("personas.json")
if not persona_path.exists():
    persona_path.write_text("[]", encoding="utf-8")

with open(persona_path, "r", encoding="utf-8") as f:
    persona_data = json.load(f)

# -------------------------
# Helper Functions
# -------------------------
def get_persona_by_id(pid):
    for p in persona_data:
        if p["id"] == pid:
            return p
    return None

def highlight_insights(text):
    text = re.sub(r"(?i)(concern[s]?)", r"🟥 **\1**", text)
    text = re.sub(r"(?i)(insight[s]?)", r"🟩 **\1**", text)
    return text

def build_prompt(personas, feature_description, conversation_history=None):
    persona_descriptions = "\n".join([
        f"- {p['name']} ({p['occupation']}, {p['location']}, Tech: {p['tech_proficiency']}, Traits: {', '.join(p['behavioral_traits'])})"
        for p in personas
    ])
    prompt = f"""
Personas:
{persona_descriptions}

Feature Description:
{feature_description}

Simulate a realistic conversation between these personas about this feature.
Each persona should:
- Respond with realistic tone and depth.
- Include reasoning, confidence, and suggested follow-up.
- Highlight insights and concerns if relevant.

"""
    if conversation_history:
        prompt += "\nPrevious conversation:\n" + conversation_history
    return prompt.strip()

def generate_response(feature_description, personas, conversation_history=None, model="gpt-4o-mini"):
    prompt = build_prompt(personas, feature_description, conversation_history)
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=700
    )
    return response.choices[0].message.content.strip()

# -------------------------
# Streamlit App Layout
# -------------------------
st.set_page_config(page_title="AI Focus Group Simulator", layout="wide")

st.title("🧠 AI Focus Group Simulator")

# --- API Key Input
openai.api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# --- Tabs for feature input
tabs = st.tabs(["Feature Description", "Wireframe / Mockup", "Functional Specs", "Interaction Flow", "Visual Elements", "Context Info"])

feature_inputs = {}
with tabs[0]:
    feature_inputs["description"] = st.text_area("Describe your feature:", height=150)
with tabs[1]:
    feature_inputs["wireframe"] = st.text_area("Paste or describe wireframe/mockup:")
with tabs[2]:
    feature_inputs["specs"] = st.text_area("Enter functional specs:")
with tabs[3]:
    feature_inputs["interaction"] = st.text_area("Describe user interaction flow:")
with tabs[4]:
    feature_inputs["visuals"] = st.text_area("Describe visual elements:")
with tabs[5]:
    feature_inputs["context"] = st.text_area("Add contextual information:")

feature_description = "\n".join([f"{k}: {v}" for k, v in feature_inputs.items() if v])

# --- Persona selection
st.header("Select Personas")
persona_options = {f"{p['name']} ({p['occupation']})": p["id"] for p in persona_data}
selected_labels = st.multiselect("Choose personas to include:", list(persona_options.keys()))
selected_personas = [get_persona_by_id(persona_options[label]) for label in selected_labels] if selected_labels else persona_data

# --- Conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

st.header("Ask the Personas")
user_question = st.text_input("Enter your question:")
if st.button("Ask Personas"):
    if not openai.api_key:
        st.warning("Please enter your OpenAI API key first.")
    elif not user_question:
        st.warning("Please enter a question.")
    else:
        st.session_state.conversation_history += f"\n**User:** {user_question}\n\n"
        reply = generate_response(feature_description, selected_personas, st.session_state.conversation_history)
        st.session_state.conversation_history += reply + "\n"
        st.success("Personas have responded!")

# --- Display conversation
if st.session_state.conversation_history:
    st.markdown("### 💬 Conversation")
    st.markdown(highlight_insights(st.session_state.conversation_history))

# --- Generate Report
if st.button("📊 Generate Feedback Report"):
    st.subheader("AI Feedback Report")
    analysis_prompt = f"""
Analyze this simulated conversation:
{st.session_state.conversation_history}

Generate a report identifying:
- Key patterns and themes in feedback
- Consensus and disagreements between personas
- Actionable recommendations for feature improvements
- Quantitative metrics (acceptance rate, usage likelihood)
- Qualitative insights (specific concerns, suggestions)
"""
    report = generate_response(analysis_prompt, selected_personas)
    st.markdown(report)

# --- Create a new persona
st.header("Add a New Persona")
new_name = st.text_input("Name:")
new_occ = st.text_input("Occupation:")
new_loc = st.text_input("Location:")
new_tech = st.selectbox("Tech Proficiency:", ["Low", "Medium", "High"])
new_traits = st.text_area("Behavioral Traits (comma-separated):")

if st.button("Add Persona"):
    if new_name and new_occ:
        new_persona = {
            "id": len(persona_data) + 1,
            "name": new_name,
            "occupation": new_occ,
            "location": new_loc,
            "tech_proficiency": new_tech,
            "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
        }
        persona_data.append(new_persona)
        with open("personas.json", "w", encoding="utf-8") as f:
            json.dump(persona_data, f, indent=4)
        st.success(f"✅ Added new persona: {new_name}")
    else:
        st.warning("Please fill in at least name and occupation.")
