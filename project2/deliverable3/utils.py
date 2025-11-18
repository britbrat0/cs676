import json
import re
import streamlit as st
import pandas as pd
import altair as alt
import logging
from typing import List, Dict, Optional
from config import DEFAULT_PERSONA_PATH, PERSONA_COLORS as CONFIG_PERSONA_COLORS

log = logging.getLogger(__name__)

# Local color cache that starts from config's colors (if provided)
PERSONA_COLORS = dict(CONFIG_PERSONA_COLORS) if isinstance(CONFIG_PERSONA_COLORS, dict) else {}

# -------------------------
# Personas I/O & validation
# -------------------------
def load_personas_from_file(path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """Load personas from JSON file. Returns [] on errors."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                st.warning(f"⚠️ {path} does not contain a list. Returning empty personas.")
                return []
            return data
    except FileNotFoundError:
        log.info("personas file not found: %s", path)
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ Malformed JSON in {path}: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading {path}: {e}")
        return []

def get_personas(uploaded_file=None, path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """
    Return personas. If uploaded_file is provided (streamlit UploadedFile),
    attempt to load and replace saved personas.
    """
    personas = load_personas_from_file(path)

    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            if not isinstance(imported, list):
                st.error("Uploaded persona file must be a JSON list.")
            else:
                personas = imported
                # try to persist
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(personas, f, indent=2)
                    st.success("✅ Personas imported and saved successfully!")
                except Exception as e:
                    st.error(f"❌ Could not save uploaded personas to disk: {e}")
        except json.JSONDecodeError:
            st.error("❌ Uploaded file contains invalid JSON.")
        except Exception as e:
            st.error(f"❌ Error reading uploaded file: {e}")

    return personas

def validate_persona(persona: Dict) -> bool:
    """Basic validation for persona structure."""
    required = ["name", "occupation", "tech_proficiency", "behavioral_traits"]
    for r in required:
        if r not in persona or persona[r] in (None, "", []):
            return False
    if not isinstance(persona.get("behavioral_traits", []), list):
        return False
    return True

def save_personas(personas: List[Dict], path: str = DEFAULT_PERSONA_PATH) -> bool:
    """Persist personas to disk. Returns True on success."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Could not save personas: {e}")
        log.exception("save_personas failed")
        return False

# -------------------------
# Display & formatting
# -------------------------
def get_color_for_persona(name: str) -> str:
    """Return or generate a stable hex color for a persona name."""
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]

def format_response_line(text: str, persona_name: str, highlight: Optional[str] = None) -> str:
    """Return HTML string for styled persona line."""
    color = get_color_for_persona(persona_name)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return (
        f"<div style='color:{color}; {background} padding:8px; margin:6px 0; "
        f"border-left:4px solid {color}; border-radius:4px; white-space:pre-wrap;'>{text}</div>"
    )

# -------------------------
# Text parsing & sentiment
# -------------------------
_INSIGHT_PATTERN = re.compile(r'\b(think|improve|great|helpful|excellent|love|benefit|useful|like)\b', re.I)
_CONCERN_PATTERN = re.compile(r'\b(worry|concern|problem|issue|difficult|hard|confused|frustrat|dislike)\b', re.I)

def detect_insight_or_concern(text: str) -> Optional[str]:
    """Return 'insight' / 'concern' / None based on simple keyword matching."""
    if not text:
        return None
    if _INSIGHT_PATTERN.search(text):
        return "insight"
    if _CONCERN_PATTERN.search(text):
        return "concern"
    return None

def extract_persona_response(line):
    """
    Remove persona name and metadata, return only the response text.
    Example:
    "John: - Response: I think this is great" -> "I think this is great"
    """
    parts = re.split(r":\s*-?\s*Response:?", line, maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip()
    else:
        return line

def score_sentiment(text: str) -> int:
    """Simple numeric score: insight=1, concern=-1, neutral=0"""
    cat = detect_insight_or_concern(text)
    return 1 if cat == "insight" else -1 if cat == "concern" else 0

# -------------------------
# Heatmap / Chart builder
# -------------------------
def build_sentiment_summary(lines: List[str], selected_personas: List[Dict]) -> pd.DataFrame:
    """
    Return a DataFrame with average sentiment score per persona.
    Ensures each selected persona appears in the result.
    """
    rows = []
    for line in lines:
        for p in selected_personas:
            if line.startswith(p["name"]):
                text = extract_persona_response(line)
                rows.append({"Persona": p["name"], "Sentiment": score_sentiment(text)})
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Persona", "Sentiment"])
    # ensure order & include personas with no rows
    names = [p["name"] for p in selected_personas]
    if df.empty:
        return pd.DataFrame({"Persona": names, "Sentiment": [0]*len(names)})
    summary = df.groupby("Persona")["Sentiment"].mean().reindex(names, fill_value=0).reset_index()
    return summary

def build_heatmap_chart(df_summary: pd.DataFrame, height: int = 220) -> alt.Chart:
    """Return an Altair bar chart representing sentiment summary."""
    chart = (
        alt.Chart(df_summary)
        .mark_bar()
        .encode(
            x=alt.X("Persona", sort="-y"),
            y=alt.Y("Sentiment", title="Average Sentiment Score", scale=alt.Scale(domain=[-1, 1])),
            color=alt.Color(
                "Sentiment",
                scale=alt.Scale(domain=[-1, 0, 1], range=["#F94144", "#FFC300", "#3CB44B"]),
                legend=None
            ),
            tooltip=["Persona", "Sentiment"]
        )
        .properties(height=height)
    )
    return chart
