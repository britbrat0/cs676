import json
import streamlit as st
import re
import os

from config import DEFAULT_PERSONA_PATH, PERSONA_COLORS

# -------------------------
# Persona Helpers
# -------------------------
def get_personas(uploaded_file=None):
    try:
        if uploaded_file:
            personas = json.load(uploaded_file)
        elif os.path.exists(DEFAULT_PERSONA_PATH):
            with open(DEFAULT_PERSONA_PATH, "r", encoding="utf-8") as f:
                personas = json.load(f)
        else:
            personas = []
        personas = [p for p in personas if validate_persona(p)]
        return personas
    except Exception as e:
        st.error(f"Failed to load personas: {e}")
        return []

def validate_persona(persona):
    required_keys = ["id", "name", "occupation", "tech_proficiency"]
    return all(k in persona for k in required_keys)

def save_personas(personas, path=DEFAULT_PERSONA_PATH):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save personas: {e}")
        return False

# -------------------------
# Conversation Helpers
# -------------------------
def get_color_for_persona(name):
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]

def format_response_line(text, name, highlight=None):
    color = get_color_for_persona(name)
    bg = ""
    if highlight == "insight":
        bg = "background-color: #d4edda;"
    elif highlight == "concern":
        bg = "background-color: #f8d7da;"
    return f"<div style='color:{color}; {bg} padding:6px; margin:4px 0; border-left:4px solid {color}; border-radius:4px;'>{text}</div>"

def detect_insight_or_concern(text):
    t = text.lower()
    if re.search(r'\b(think|improve|great|helpful|excellent|love)\b', t):
        return "insight"
    if re.search(r'\b(worry|concern|problem|issue|hard|frustrated)\b', t):
        return "concern"
    return None
