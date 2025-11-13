import streamlit as st
import openai
import json
import re
import pandas as pd
import altair as alt


# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="Persona Feedback Simulator", page_icon="💬", layout="wide")

# -------------------------
# Session State Initialization
# -------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""
if "personas" not in st.session_state:
    st.session_state.personas = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# -------------------------
# Sidebar - API Key Input
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
    st.sidebar.warning("⚠️ Please enter your OpenAI API key to use the app")

# Model selection
model_choice = st.sidebar.selectbox(
    "Select Model",
    ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    index=0,
    help="gpt-4o-mini is faster and cheaper, gpt-4o is more capable"
)

# -------------------------
# Load Personas (robust)
# -------------------------
persona_data = []
try:
    with open("personas.json", "r", encoding="utf-8") as f:
        try:
            persona_data = json.load(f)
            if not isinstance(persona_data, list):
                st.warning("personas.json content is not a list — starting with empty persona list.")
                persona_data = []
        except json.JSONDecodeError:
            st.error("personas.json is malformed. Starting with empty persona list.")
            persona_data = []
except FileNotFoundError:
    # safe fallback: file missing
    st.warning("personas.json not found. Starting with empty persona list.")
    persona_data = []

# Ensure session state has a list assigned (always)
if "personas" not in st.session_state or not isinstance(st.session_state.personas, list):
    st.session_state.personas = persona_data if persona_data else []


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

def get_color_for_persona(persona_name):
    """Get color for persona, generate if not exists"""
    if persona_name in PERSONA_COLORS:
        return PERSONA_COLORS[persona_name]
    # Generate a hash-based color for new personas
    hash_val = hash(persona_name)
    color = f"#{(hash_val & 0xFFFFFF):06x}"
    PERSONA_COLORS[persona_name] = color
    return color

def format_response_line(text, persona_name, highlight=None):
    color = get_color_for_persona(persona_name)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return f'<div style="color: {color}; {background} padding: 8px; margin: 4px 0; border-left: 4px solid {color}; border-radius: 4px; white-space: pre-wrap;">{text}</div>'

def detect_insight_or_concern(text):
    lower_text = text.lower()
    if re.search(r'\b(think|like|improve|great|benefit|love|helpful|excellent|wonderful)\b', lower_text):
        return "insight"
    if re.search(r'\b(worry|concern|unsure|problem|difficult|issue|hard|confused|frustrated)\b', lower_text):
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
- Each persona should speak in turn, but keep responses concise (2-3 sentences each).
- Use the following template for each persona's response:

[Persona Name]:
- Response: <what they say>
- Reasoning: <why they think that>
- Confidence: <High / Medium / Low>
- Suggested follow-up: <next question they might ask>

Keep the conversation natural and engaging. Each persona should provide unique perspectives based on their background.
"""
    if conversation_history:
        prompt += "\n\nPrevious conversation:\n" + conversation_history
        prompt += "\n\nContinue the conversation naturally based on the above context."
    return prompt.strip()

# -------------------------
# Generate GPT Response
# -------------------------
def generate_response(feature_inputs, personas, conversation_history=None, model="gpt-4o-mini"):
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        return ""
    
    try:
        prompt = build_prompt(personas, feature_inputs, conversation_history)
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an AI facilitator for a virtual focus group. Simulate realistic, diverse perspectives from each persona based on their unique backgrounds and traits."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        conversation_update = response.choices[0].message.content
        return conversation_update.strip() + "\n"
    except openai.AuthenticationError:
        st.error("❌ Invalid API key. Please check your OpenAI API key.")
        return ""
    except openai.RateLimitError:
        st.error("❌ Rate limit exceeded. Please wait and try again.")
        return ""
    except Exception as e:
        st.error(f"❌ Error generating response: {str(e)}")
        return ""

# -------------------------
# Feedback Report
# -------------------------
def generate_feedback_report(conversation, model="gpt-4o-mini"):
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        return ""
    
    try:
        prompt = f"""
Analyze the following conversation and create a structured feedback report:

Conversation:
{conversation}

Create a comprehensive report with the following sections:

## Executive Summary
Brief overview of key findings

## Patterns and Themes
Identify recurring topics and sentiments

## Consensus Points
Areas where personas agree

## Disagreements and Concerns
Areas of divergence and specific concerns raised

## Persona-Specific Insights
Key takeaways from each persona

## Actionable Recommendations
Concrete next steps for feature improvements (prioritized)

## Quantitative Metrics
Estimate:
- Overall acceptance rate (%)
- Likelihood of usage by persona segment
- Priority level (High/Medium/Low)

## Risk Assessment
Potential blockers or deal-breakers identified

Keep the report concise but actionable.
"""
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert product analyst and UX researcher. Provide actionable, data-driven insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")
        return ""

# -------------------------
# Main App UI
# -------------------------
st.title("💬 Persona Feedback Simulator")
st.markdown("*Simulate realistic user feedback from diverse personas for your product features*")

# Check API key before proceeding
if not st.session_state.api_key:
    st.info("👈 Please enter your OpenAI API key in the sidebar to get started.")
    st.stop()

st.markdown("---")

# Feature Input Section
st.header("📝 Feature Description")
tabs = st.tabs(["Text Description", "File Upload"])

with tabs[0]:
    text_desc = st.text_area(
        "Enter a textual description of your feature",
        height=150,
        placeholder="Example: A new dark mode toggle that automatically adjusts based on time of day..."
    )

with tabs[1]:
    uploaded_files = st.file_uploader(
        "Upload wireframes/mockups (optional)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True,
        help="File content is not yet processed, only filenames are shared with personas"
    )

feature_inputs = {
    "Text Description": text_desc,
    "Files": [f.name for f in uploaded_files] if uploaded_files else []
}

st.markdown("---")

# -------------------------
# Persona Selection
# -------------------------
st.header("👥 Select Personas")

# Always initialize selected_personas to a safe empty list
selected_personas = []

if not st.session_state.personas:
    st.warning("No personas available. Create personas in the sidebar.")
else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        persona_options = [f"{p.get('name','Unknown')} ({p.get('occupation','Unknown')})" for p in st.session_state.personas]
        # default selection logic — choose up to first 3
        default_selection = persona_options[:3] if len(persona_options) >= 3 else persona_options
        selected_personas_str = st.multiselect(
            "Choose personas to participate in the discussion",
            persona_options,
            default=default_selection
        )
        # build selected_personas list from selection
        selected_personas = [
            p for p in st.session_state.personas 
            if f"{p.get('name','Unknown')} ({p.get('occupation','Unknown')})" in selected_personas_str
        ]
    
    with col2:
        st.metric("Selected", len(selected_personas))
        if st.button("Select All"):
            # set all options as selected and rerun
            # note: we cannot directly set multiselect value programmatically here, but we can trigger a rerun
            # using session_state to remember a 'select_all' flag is optional; simple rerun for UX
            st.session_state._select_all = True
            st.experimental_rerun()

# Display selected personas
if selected_personas:
    with st.expander("📋 View Selected Persona Details", expanded=False):
        for p in selected_personas:
            color = get_color_for_persona(p['name'])
            st.markdown(
                f"<div style='border-left: 4px solid {color}; padding: 10px; margin: 5px 0;'>"
                f"<strong>{p['name']}</strong> - {p['occupation']}<br>"
                f"<small>📍 {p['location']} | 💻 Tech: {p['tech_proficiency']} | "
                f"Traits: {', '.join(p['behavioral_traits'])}</small>"
                f"</div>",
                unsafe_allow_html=True
            )

st.markdown("---")

# Interaction Section
st.header("💭 Ask Your Question")
user_question = st.text_input(
    "What would you like to ask the personas?",
    placeholder="Example: What do you think about this feature? Would you use it daily?"
)

# Action Buttons
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    ask_button = st.button("🎯 Ask Personas", type="primary", use_container_width=True)

with col2:
    report_button = st.button("📊 Generate Feedback Report", use_container_width=True)

with col3:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

# Handle Ask Personas
if ask_button:
    if not selected_personas:
        st.warning("⚠️ Please select at least one persona!")
    elif not user_question.strip() and not text_desc.strip():
        st.warning("⚠️ Please enter a question or feature description!")
    else:
        with st.spinner("🤔 Personas are thinking..."):
            # Add user question to history
            if user_question.strip():
                st.session_state.conversation_history += f"\n**User Question:** {user_question}\n\n"
            
            # Generate response
            response = generate_response(
                feature_inputs,
                selected_personas,
                st.session_state.conversation_history,
                model=model_choice
            )
            
            if response:
                st.session_state.conversation_history += response + "\n"
                st.success("✅ Personas have responded!")
                st.rerun()

# Handle Generate Report
if report_button:
    if not st.session_state.conversation_history.strip():
        st.warning("⚠️ No conversation history yet. Ask personas some questions first!")
    else:
        with st.spinner("📊 Analyzing conversation and generating report..."):
            report = generate_feedback_report(st.session_state.conversation_history, model=model_choice)
            if report:
                st.markdown("---")
                st.markdown("## 📊 Feedback Analysis Report")

                # --- Extract Quantitative Data ---
                acceptance_rate = None
                usage_by_persona = {}
                priority_level = None

                # Try to extract numeric estimates from the report
                acceptance_match = re.search(r"acceptance rate[^0-9]*(\d{1,3})%", report, re.IGNORECASE)
                if acceptance_match:
                    acceptance_rate = int(acceptance_match.group(1))

                # Try to find priority level
                priority_match = re.search(r"priority level[^:]*:\s*(High|Medium|Low)", report, re.IGNORECASE)
                if priority_match:
                    priority_level = priority_match.group(1).capitalize()

                # Try to extract persona usage likelihoods if listed (e.g., "Sophia Martinez – 80%")
                for line in report.splitlines():
                    m = re.match(r"[-*]?\s*([A-Za-z ]+)\s*[-–]\s*(\d{1,3})%", line.strip())
                    if m:
                        usage_by_persona[m.group(1).strip()] = int(m.group(2))

                # --- Display Metrics ---
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    if acceptance_rate is not None:
                        st.metric("Overall Acceptance Rate", f"{acceptance_rate}%")
                        st.progress(acceptance_rate / 100)
                with metrics_col2:
                    if priority_level:
                        priority_color = {
                            "High": "🔴 High",
                            "Medium": "🟠 Medium",
                            "Low": "🟢 Low"
                        }.get(priority_level, priority_level)
                        st.metric("Priority Level", priority_color)

                # --- Persona Usage Visualization ---
                if usage_by_persona:
                    df_usage = pd.DataFrame({
                        "Persona": list(usage_by_persona.keys()),
                        "Likelihood of Use (%)": list(usage_by_persona.values())
                    })

                    chart = (
                        alt.Chart(df_usage)
                        .mark_bar(color="#3CB44B")
                        .encode(
                            x=alt.X("Likelihood of Use (%)", scale=alt.Scale(domain=[0, 100])),
                            y=alt.Y("Persona", sort="-x"),
                            tooltip=["Persona", "Likelihood of Use (%)"]
                        )
                        .properties(title="Persona Likelihood of Feature Usage", height=300)
                    )
                    st.altair_chart(chart, use_container_width=True)

                st.markdown("---")
                st.markdown(report)

                # --- Download button ---
                st.download_button(
                    label="⬇️ Download Report",
                    data=report,
                    file_name="persona_feedback_report.md",
                    mime="text/markdown"
                )

# Handle Clear
if clear_button:
    st.session_state.conversation_history = ""
    st.success("🗑️ Conversation cleared!")
    st.rerun()

st.markdown("---")

# Conversation History Display
st.header("💬 Conversation History")

if st.session_state.conversation_history.strip():
    conversation_container = st.container()
    
    with conversation_container:
        lines = st.session_state.conversation_history.split("\n")
        
        for line in lines:
            if not line.strip():
                continue
                
            # Check if line is from a persona
            matched = False
            for p in selected_personas:
                if line.startswith(p["name"] + ":") or line.startswith(f"[{p['name']}]"):
                    highlight = detect_insight_or_concern(line)
                    st.markdown(format_response_line(line, p["name"], highlight), unsafe_allow_html=True)
                    matched = True
                    break
            
            # If not matched to persona, check if it's a user question or other text
            if not matched:
                if line.startswith("**User Question:**") or line.startswith("User:"):
                    st.markdown(f"**{line}**")
                elif line.startswith("-") or line.startswith("*"):
                    st.markdown(f"  {line}")
                else:
                    st.markdown(line)

    st.info("💡 Continue the discussion using the **question field above** to ask a follow-up question.")
else:
    st.info("💡 No conversation yet. Ask your personas a question to get started!")

# -------------------------
# Sidebar - Persona Management
# -------------------------
st.sidebar.markdown("---")
st.sidebar.header("➕ Create New Persona")

with st.sidebar.form("new_persona_form"):
    new_name = st.text_input("Name*", placeholder="e.g., Alex Johnson")
    new_occupation = st.text_input("Occupation*", placeholder="e.g., Software Engineer")
    new_location = st.text_input("Location", placeholder="e.g., Seattle, WA")
    new_tech = st.selectbox("Tech Proficiency*", ["Low", "Medium", "High"], index=1)
    new_traits = st.text_area(
        "Behavioral Traits (comma-separated)",
        placeholder="e.g., detail-oriented, skeptical, early adopter"
    )
    
    submit_persona = st.form_submit_button("Add Persona", use_container_width=True)
    
    if submit_persona:
        if not new_name.strip():
            st.error("❌ Name is required!")
        elif not new_occupation.strip():
            st.error("❌ Occupation is required!")
        else:
            new_persona = {
                "id": f"p{len(st.session_state.personas) + 1}",
                "name": new_name.strip(),
                "occupation": new_occupation.strip(),
                "location": new_location.strip() or "Unknown",
                "tech_proficiency": new_tech,
                "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
            }
            st.session_state.personas.append(new_persona)
            
            # Save to JSON
            try:
                with open("personas.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state.personas, f, indent=2)
                st.success(f"✅ Persona '{new_name}' added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving persona: {str(e)}")

# Display existing personas count
st.sidebar.markdown("---")
st.sidebar.metric("Total Personas", len(st.session_state.personas))

# Export/Import Personas
with st.sidebar.expander("🔄 Export/Import Personas"):
    if st.button("📥 Export Personas"):
        personas_json = json.dumps(st.session_state.personas, indent=2)
        st.download_button(
            label="Download personas.json",
            data=personas_json,
            file_name="personas.json",
            mime="application/json"
        )
    
    uploaded_personas = st.file_uploader("📤 Import Personas", type=["json"])
    if uploaded_personas:
        try:
            imported_personas = json.load(uploaded_personas)
            st.session_state.personas = imported_personas
            with open("personas.json", "w", encoding="utf-8") as f:
                json.dump(imported_personas, f, indent=2)
            st.success("✅ Personas imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error importing personas: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 About")
st.sidebar.info(
    "This tool simulates user feedback from diverse personas to help you validate "
    "product ideas and features before development."
)
