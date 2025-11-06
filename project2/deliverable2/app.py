import openai
import json
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import re

# -------------------------
# Load Personas
# -------------------------
with open("personas.json", "r", encoding="utf-8") as f:
    persona_data = json.load(f)

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
# Tabbed Feature Inputs
# -------------------------
text_desc = widgets.Textarea(placeholder="Enter a textual description of the feature", layout=widgets.Layout(width='100%', height='80px'))
functional_spec = widgets.Textarea(placeholder="Enter functional specifications", layout=widgets.Layout(width='100%', height='80px'))
interaction_flow = widgets.Textarea(placeholder="Describe interaction flows", layout=widgets.Layout(width='100%', height='80px'))
contextual_info = widgets.Textarea(placeholder="Provide any contextual information", layout=widgets.Layout(width='100%', height='80px'))
visual_elements = widgets.FileUpload(accept='image/*,.pdf', multiple=True, description="Upload visuals or mockups")
wireframes = widgets.FileUpload(accept='image/*,.pdf', multiple=True, description="Upload wireframes/mockups")

tab_contents = ['Text Description', 'Wireframes', 'Visual Elements', 'Functional Specs', 'Interaction Flows', 'Contextual Info']
children = [text_desc, wireframes, visual_elements, functional_spec, interaction_flow, contextual_info]
feature_tabs = widgets.Tab(children=children)
for i, title in enumerate(tab_contents):
    feature_tabs.set_title(i, title)

# -------------------------
# Persona Selection
# -------------------------
persona_options = [(p['name'] + f" ({p['occupation']})", p['id']) for p in persona_data]
persona_select = widgets.SelectMultiple(options=persona_options, description='Personas:',
                                        layout=widgets.Layout(width='50%', height='200px'))

# -------------------------
# User Question
# -------------------------
question_input = widgets.Text(placeholder='Enter your question here', description='Question:', layout=widgets.Layout(width='80%'))

# -------------------------
# Buttons
# -------------------------
submit_button = widgets.Button(description='Ask Personas', button_style='success')
clear_button = widgets.Button(description='Clear Conversation', button_style='warning')
report_button = widgets.Button(description='Generate Feedback Report', button_style='primary')

# -------------------------
# Output Area
# -------------------------
output_area = widgets.Output(layout={'border': '1px solid black', 'height': '400px', 'overflow_y': 'auto'})
conversation_history = ""

# -------------------------
# Button Handlers
# -------------------------
def on_submit_button_clicked(b):
    global conversation_history
    clear_output(wait=True)

    selected_ids = persona_select.value
    if not selected_ids:
        selected_personas = persona_data
    else:
        selected_personas = [get_persona_by_id(pid) for pid in selected_ids]

    user_question = question_input.value.strip()
    if not user_question:
        return

    feature_inputs = {
        "Text Description": text_desc.value,
        "Wireframes": [f['metadata']['name'] for f in wireframes.value.values()] if wireframes.value else [],
        "Visual Elements": [f['metadata']['name'] for f in visual_elements.value.values()] if visual_elements.value else [],
        "Functional Specs": functional_spec.value,
        "Interaction Flows": interaction_flow.value,
        "Contextual Info": contextual_info.value
    }

    conversation_history += f"\nUser: {user_question}\n\n"
    persona_reply = generate_response(feature_inputs, selected_personas, conversation_history)
    conversation_history += persona_reply + "\n"

    with output_area:
        clear_output(wait=True)
        # Persona legend
        legend_html = "👥 Personas in this round:<br>" + "".join([
            f'{apply_color_to_text(p["name"], p["name"])} ({p["occupation"]})<br>'
            for p in selected_personas
        ])
        display(HTML(legend_html))
        display(HTML("<br>💬 Conversation so far:<br>"))

        # Format conversation
        colored_history_html = ""
        for line in conversation_history.split('\n'):
            line_stripped = line.strip()
            if not line_stripped:
                colored_history_html += "<br>"
                continue

            is_user = line_stripped.startswith("User:")
            formatted_line = None

            for p in selected_personas:
                name = p["name"]
                if line_stripped.startswith(name) or line_stripped.startswith(f"[{name}]"):
                    highlight = detect_insight_or_concern(line_stripped)
                    formatted_line = format_response_line(line_stripped, name, highlight)
                    break

            if is_user:
                formatted_line = f'<div style="color: #444444; white-space: pre-wrap;"><b>{line_stripped}</b></div>'

            if formatted_line:
                colored_history_html += formatted_line
            else:
                colored_history_html += f'<div style="white-space: pre-wrap;">{line_stripped}</div>'

        display(HTML(colored_history_html))
        display(HTML("<br>➡ Next Question: Please enter a follow-up question for the personas above."))

def on_clear_button_clicked(b):
    global conversation_history
    conversation_history = ""
    with output_area:
        clear_output(wait=True)
        display(HTML("Conversation cleared."))
        display(HTML("<br>➡ Enter a feature and ask the personas your first question."))

def on_report_button_clicked(b):
    if not conversation_history.strip():
        with output_area:
            display(HTML("<span style='color:red'>No conversation yet to generate report.</span>"))
        return
    report = generate_feedback_report(conversation_history)
    with output_area:
        display(HTML("<h3>Feedback Report</h3>"))
        display(HTML(f"<pre style='white-space: pre-wrap;'>{report}</pre>"))

submit_button.on_click(on_submit_button_clicked)
clear_button.on_click(on_clear_button_clicked)
report_button.on_click(on_report_button_clicked)

# -------------------------
# Create New Persona Form
# -------------------------
new_name = widgets.Text(placeholder="Full Name", description="Name:")
new_occupation = widgets.Text(placeholder="Occupation", description="Occupation:")
new_location = widgets.Text(placeholder="Location", description="Location:")
new_tech = widgets.Dropdown(options=['Low','Medium','High'], description="Tech Proficiency:")
new_traits = widgets.Text(placeholder="Comma-separated traits", description="Traits:")
create_persona_button = widgets.Button(description="Add Persona", button_style='info')

def add_persona_to_json(b):
    global persona_data
    new_id = max([p['id'] for p in persona_data]) + 1 if persona_data else 1
    traits_list = [t.strip() for t in new_traits.value.split(",") if t.strip()]
    new_persona = {
        "id": new_id,
        "name": new_name.value.strip(),
        "occupation": new_occupation.value.strip(),
        "location": new_location.value.strip(),
        "tech_proficiency": new_tech.value,
        "behavioral_traits": traits_list
    }
    persona_data.append(new_persona)
    with open("personas.json", "w", encoding="utf-8") as f:
        json.dump(persona_data, f, indent=2)
    persona_select.options = [(p['name'] + f" ({p['occupation']})", p['id']) for p in persona_data]
    new_name.value = ""
    new_occupation.value = ""
    new_location.value = ""
    new_traits.value = ""
    display(HTML(f"<span style='color:green'>Persona '{new_persona['name']}' added successfully!</span>"))

create_persona_button.on_click(add_persona_to_json)

# -------------------------
# Display All Widgets
# -------------------------
display(HTML("<h2>Feature Input</h2>"))
display(feature_tabs)
display(HTML("<h2>Select Personas</h2>"))
display(persona_select)
display(HTML("<h2>Ask Personas</h2>"))
display(question_input)
display(submit_button)
display(clear_button)
display(report_button)
display(output_area)

display(HTML("<h2>Create a New Persona</h2>"))
display(new_name)
display(new_occupation)
display(new_location)
display(new_tech)
display(new_traits)
display(create_persona_button)
