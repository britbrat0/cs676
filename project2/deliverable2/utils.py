import json
import streamlit as st
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
