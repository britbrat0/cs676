import streamlit as st
import json
import re
import openai

# -------------------------
# Load Personas
# -------------------------
def load_personas():
    with open("personas.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_personas(data):
    with open("personas.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

persona_data = load_personas()

def get_persona_by_id(pid):
    for p in persona_data:
        if p["id"] == pid:
            return p
    return None


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

def color_text(text, persona_name):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    return f'<span style="color:{color};font-weight:bold;">{text}</span>'

def format_line(text, persona_name, highlight=None):
    color = PERSONA_COLORS.get(persona_name, "#000000")
    background = ""
    if highlight == "insight":
        background = "background-color:#d4edda;"
    elif highlight == "concern":
        background = "background-color:#f8d7da;"
    return f'<div style="color:{color};{background}padding:4px;margin:2px 0;border-left:4px solid {color};white-space:pre-wrap;">{text}</div>'

def detect_highlight(text):
    t = text.lower()
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful)\b', t):
        return "insight"
    if re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard)\b', t):
        return "concern"
    return None


# -------------------------
# Prompt Building
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
Each persona should respond in turn.

Format:
[Persona Name]:
- Response: <what they say>
- Reasoning: <why they think that>
- Confidence: <High / Medium / Low>
- Suggested follow-up: <next question>
"""
    if conversation_history:
        prompt += "\nPrevious conversation:\n" + conversation_history
    return prompt.strip()


# -------------------------
# GPT Responses
# -------------------------
def generate_response(feature_inputs, personas, conversation_history=None):
    prompt = build_prompt(personas, feature_inputs, conversation_history)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=700,
    )
    return response.choices[0].message.content.strip()


def generate_feedback_report(conversation):
    prompt = f"""
Analyze the following conversation and create a structured feedback report:

Conversation:
{conversation}

Report should include:
- Patterns and themes
- Consensus and disagreements between personas
- Actionable recommendations for feature improvements
- Quantitative metrics (e.g., acceptance, likelihood of use)
- Qualitative insights
"""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI product analyst."},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=1200,
    )
    return response.choices[0].message.content.strip()


# -------------------------
# Streamlit App Layout
# -------------------------
st.set_page_config(page_title="Persona Feedback Simulator", layout="wide")
st.title("🎭 Persona Feedback Simulator")

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

# --- Tabs for Feature Input ---
tab1, tab2 = st.tabs(["📝 Text Description", "📎 File Upload"])

with tab1:
    text_desc = st.text_area("Describe your feature:", height=120)

with tab2:
    uploaded_files = st.file_uploader("Upload wireframes or mockups", type=["jpg","png","pdf"], accept_multiple_files=True)
    file_names = [f.name for f in uploaded_files] if uploaded_files else []

# --- Persona Selection ---
st.subheader("👥 Select Personas")
persona_choices = {f"{p['name']} ({p['occupation']})": p["id"] for p in persona_data}
selected = st.multiselect("Choose which personas to include:", options=list(persona_choices.keys()))
selected_personas = [get_persona_by_id(persona_choices[s]) for s in selected] if selected else persona_data

# --- Question Input ---
st.subheader("💬 Ask a Question")
user_question = st.text_input("Enter your question for the personas:")

col1, col2, col3 = st.columns(3)
ask = col1.button("Ask Personas", use_container_width=True)
clear = col2.button("Clear Conversation", use_container_width=True)
report_btn = col3.button("Generate Feedback Report", use_container_width=True)


# -------------------------
# Conversation Logic
# -------------------------
if ask:
    if user_question.strip():
        feature_inputs = {"Text Description": text_desc, "File Upload": file_names}
        st.session_state.conversation_history += f"\nUser: {user_question}\n\n"
        reply = generate_response(feature_inputs, selected_personas, st.session_state.conversation_history)
        st.session_state.conversation_history += reply + "\n"

if clear:
    st.session_state.conversation_history = ""

# -------------------------
# Display Conversation
# -------------------------
if st.session_state.conversation_history.strip():
    st.markdown("### 🗨️ Conversation History")
    legend = "👥 **Personas in this round:**<br>" + "".join(
        [f"{color_text(p['name'], p['name'])} ({p['occupation']})<br>" for p in selected_personas]
    )
    st.markdown(legend, unsafe_allow_html=True)

    html_output = ""
    for line in st.session_state.conversation_history.split("\n"):
        line = line.strip()
        if not line:
            html_output += "<br>"
            continue

        if line.startswith("User:"):
            html_output += f"<div style='color:#444;font-weight:bold;'>{line}</div>"
        else:
            formatted = None
            for p in selected_personas:
                if line.startswith(p["name"]) or line.startswith(f"[{p['name']}]"):
                    hl = detect_highlight(line)
                    formatted = format_line(line, p["name"], hl)
                    break
            html_output += formatted or f"<div>{line}</div>"
    st.markdown(html_output, unsafe_allow_html=True)


# -------------------------
# Feedback Report
# -------------------------
if report_btn:
    if not st.session_state.conversation_history.strip():
        st.warning("No conversat
