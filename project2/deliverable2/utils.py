import json
import streamlit as st
import re
from config import DEFAULT_PERSONA_PATH

# -------------------------
# Load Personas
# -------------------------
def load_personas_from_file(path=DEFAULT_PERSONA_PATH):
    """
    Load personas from a JSON file.
    Returns a list of persona dicts or empty list if file not found or invalid.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                st.warning(f"⚠️ {path} is not a list. Returning empty personas.")
                return []
            return data
    except FileNotFoundError:
        st.warning(f"⚠️ {path} not found. Returning empty personas.")
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ Malformed JSON in {path}: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading {path}: {e}")
        return []

# -------------------------
# Upload & Merge Personas
# -------------------------
def get_personas(uploaded_file=None):
    """
    Returns a list of personas, optionally loading from an uploaded JSON file.
    If a file is uploaded, it replaces the default personas.
    """
    personas = load_personas_from_file()
    
    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            if not isinstance(imported, list):
                st.error("Uploaded file must be a JSON list.")
            else:
                personas = imported
                # Save back to default file
                try:
                    with open(DEFAULT_PERSONA_PATH, "w", encoding="utf-8") as f:
                        json.dump(personas, f, indent=2)
                    st.success("✅ Personas imported and saved successfully!")
                except Exception as e:
                    st.error(f"❌ Could not save uploaded personas: {e}")
        except json.JSONDecodeError:
            st.error("❌ Uploaded file contains invalid JSON.")
        except Exception as e:
            st.error(f"❌ Error reading uploaded file: {e}")

    return personas

# -------------------------
# Persona Validation
# -------------------------
def validate_persona(persona):
    """
    Checks that required fields exist in a persona dict.
    Returns True if valid, False otherwise.
    """
    required_fields = ["name", "occupation", "tech_proficiency", "behavioral_traits"]
    for field in required_fields:
        if field not in persona or not persona[field]:
            return False
    # Ensure behavioral_traits is a list
    if not isinstance(persona.get("behavioral_traits", []), list):
        return False
    return True

# -------------------------
# Save Personas
# -------------------------
def save_personas(personas, path=DEFAULT_PERSONA_PATH):
    """
    Save a list of personas to a JSON file.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Could not save personas: {e}")
        return False

# -------------------------
# Persona Display Helpers
# -------------------------
PERSONA_COLORS = {}

def get_color_for_persona(name):
    """
    Returns a consistent color for a persona name. Generates one if not exists.
    """
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]

def format_response_line(text, persona_name, highlight=None):
    """
    Formats a persona response line with color and optional highlight (insight/concern).
    """
    color = get_color_for_persona(persona_name)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return f"<div style='color:{color}; {background} padding:6px; margin:4px 0; border-left:4px solid {color}; border-radius:4px;'>{text}</div>"

# -------------------------
# Insight / Concern Detection
# -------------------------
def detect_insight_or_concern(text):
    """
    Returns 'insight' or 'concern' based on keywords in the text, or None if neutral.
    """
    t = text.lower()
    if re.search(r'\b(think|improve|great|helpful|excellent|love)\b', t):
        return "insight"
    if re.search(r'\b(worry|concern|problem|issue|hard|frustrated)\b', t):
        return "concern"
    return None


# -------------------------
# Persona Sentiment Heatmap
# -------------------------
def score_sentiment(text):
    """
    Simple scoring: insight=1, concern=-1, neutral=0
    """
    t = detect_insight_or_concern(text)
    if t == "insight":
        return 1
    elif t == "concern":
        return -1
    else:
        return 0
