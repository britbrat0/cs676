import json
import os
import streamlit as st

# -------------------------
# Default persona file path
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PERSONA_PATH = os.path.join(BASE_DIR, "personas.json")


def load_personas_from_file(file_path=DEFAULT_PERSONA_PATH):
    """
    Load personas from a JSON file.
    Returns a list of personas, empty list if file not found or invalid.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                st.warning("⚠️ personas.json is not a list. Returning empty list.")
                return []
    except FileNotFoundError:
        st.warning(f"⚠️ {file_path} not found. Returning empty list.")
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ personas.json is malformed: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading personas: {e}")
        return []


def load_personas_from_upload(uploaded_file):
    """
    Load personas from an uploaded file (Streamlit file uploader).
    Returns a list of personas, empty list if invalid.
    """
    if uploaded_file is None:
        return []

    try:
        data = json.load(uploaded_file)
        if isinstance(data, list):
            return data
        else:
            st.error("Uploaded JSON must be a list of personas.")
            return []
    except json.JSONDecodeError:
        st.error("Uploaded file contains invalid JSON.")
        return []
    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
        return []


def get_personas(uploaded_file=None):
    """
    Unified function to get personas.
    Priority:
    1. Uploaded JSON file
    2. personas.json in repo
    Returns a list of persona dicts.
    """
    if uploaded_file:
        personas = load_personas_from_upload(uploaded_file)
        if personas:
            return personas

    # fallback to default file
    return load_personas_from_file()
