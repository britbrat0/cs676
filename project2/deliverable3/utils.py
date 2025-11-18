# utils.py
import json
import re
from typing import List, Dict, Optional
import streamlit as st
import pandas as pd
import altair as alt

from config import DEFAULT_PERSONA_PATH, PERSONA_COLORS as DEFAULT_COLORS

# internal color map (mutable)
PERSONA_COLORS = dict(DEFAULT_COLORS)


# -------------------------
# File I/O
# -------------------------
def load_personas_from_file(path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                st.warning(f"⚠️ {path} content is not a list. Returning empty list.")
                return []
            return data
    except FileNotFoundError:
        # don't spam errors for missing file; caller may upload
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ Malformed JSON in {path}: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading {path}: {e}")
        return []


def save_personas(personas: List[Dict], path: str = DEFAULT_PERSONA_PATH) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Could not save personas: {e}")
        return False


def get_personas(uploaded_file=None, path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """
    Loads personas from repo file, optionally replaces them with an uploaded file.
    """
    personas = load_personas_from_file(path)
    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            if not isinstance(imported, list):
                st.error("Uploaded file must be a JSON list of personas.")
            else:
                personas = imported
                # try saving to default path
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(personas, f, indent=2)
                except Exception:
                    # saving is optional; warn but still return imported
                    st.warning("Uploaded personas loaded but could not be saved to repo path.")
        except json.JSONDecodeError:
            st.error("Uploaded file contains invalid JSON.")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    return personas


# -------------------------
# Validation
# -------------------------
def validate_persona(persona: Dict) -> bool:
    required = ["name", "occupation", "tech_proficiency", "behavioral_traits"]
    for r in required:
        if r not in persona or persona[r] in (None, "", []):
            return False
    if not isinstance(persona.get("behavioral_traits", []), list):
        return False
    return True


# -------------------------
# Colors & display
# -------------------------
def get_color_for_persona(name: str) -> str:
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]


def format_response_line(text: str, persona_name: str, highlight: Optional[str] = None) -> str:
    color = get_color_for_persona(persona_name)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return (
        f"<div style='color:{color}; {background} "
        "padding:6px; margin:4px 0; border-left:4px solid {color}; "
        "border-radius:4px; white-space:pre-wrap;'>{text}</div>"
    ).format(color=color)


# -------------------------
# Sentiment detection & scoring
# -------------------------
def detect_insight_or_concern(text: str) -> Optional[str]:
    """
    Return 'insight' if positive keywords present, 'concern' if negative keywords present, else None.
    Case-insensitive and handles common word forms.
    """
    if not text:
        return None
    t = text.lower()

    # positive stems/words
    positive_pattern = r"\b(thank|think|like|love|enjoy|great|improv|helpful|excellent|useful|benefit)\w*\b"
    negative_pattern = r"\b(worri|worry|worried|concern|concerned|proble|issue|difficult|hard|frustrat|frustrated|hate|unsure)\w*\b"

    if re.search(positive_pattern, t):
        return "insight"
    if re.search(negative_pattern, t):
        return "concern"
    return None


def score_sentiment(text: str) -> int:
    s = detect_insight_or_concern(text)
    if s == "insight":
        return 1
    if s == "concern":
        return -1
    return 0


def extract_persona_response(line: str) -> str:
    """
    Remove persona name and the 'Response:' label if present and return the human text.
    Examples:
    'John: - Response: I like this' -> 'I like this'
    'John: I like this' -> 'I like this'
    """
    # Remove leading "Name:" prefix
    # First try pattern where assistant provided "- Response: <text>"
    m = re.split(r":\s*-?\s*Response:?\s*", line, maxsplit=1)
    if len(m) == 2 and m[1].strip():
        return m[1].strip()
    # fallback: remove "Name:" prefix
    m2 = re.split(r"^[^:]+:\s*", line, maxsplit=1)
    if len(m2) == 2:
        return m2[1].strip()
    return line.strip()


# -------------------------
# Heatmap helpers
# -------------------------
def build_sentiment_summary(lines: List[str], selected_personas: List[Dict]) -> pd.DataFrame:
    """
    Given conversation lines and selected_personas, return a DataFrame with average sentiment per persona.
    Ensures order follows selected_personas list.
    """
    records = []
    persona_names = [p["name"] for p in selected_personas]
    for ln in lines:
        for name in persona_names:
            if ln.startswith(name):
                txt = extract_persona_response(ln)
                records.append({"Persona": name, "Sentiment": score_sentiment(txt)})
                break
    if not records:
        # return a DataFrame with zeroed sentiments for each persona
        df0 = pd.DataFrame({"Persona": persona_names, "Sentiment": [0] * len(persona_names)})
        return df0

    df = pd.DataFrame(records)
    df_summary = df.groupby("Persona")["Sentiment"].mean().reindex(persona_names, fill_value=0).reset_index()
    return df_summary


def build_heatmap_chart(df_summary: pd.DataFrame) -> alt.Chart:
    """
    Return an Altair bar chart representing average sentiment per persona.
    """
    chart = (
        alt.Chart(df_summary)
        .mark_bar()
        .encode(
            x=alt.X("Persona", sort="-y"),
            y=alt.Y("Sentiment", scale=alt.Scale(domain=[-1, 1]), title="Average Sentiment"),
            color=alt.Color(
                "Sentiment",
                scale=alt.Scale(domain=[-1, 0, 1], range=["#F94144", "#FFC300", "#3CB44B"]),
                legend=None,
            ),
            tooltip=["Persona", alt.Tooltip("Sentiment", format=".2f")],
        )
        .properties(height=200)
    )
    return chart
