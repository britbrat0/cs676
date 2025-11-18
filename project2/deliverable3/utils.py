# utils.py
import json
import os
import re
from typing import List, Dict
import pandas as pd
import altair as alt

from config import DEFAULT_PERSONA_PATH

# -------------------------
# Personas load/save
# -------------------------
def load_personas_from_file(path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def get_personas(uploaded_file=None, path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """
    If uploaded_file provided (Streamlit UploadedFile), use it.
    Otherwise load from default path on disk.
    """
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []
    return load_personas_from_file(path)


def save_personas(personas: List[Dict], path: str = DEFAULT_PERSONA_PATH) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception:
        return False


# -------------------------
# Response formatting helpers
# -------------------------
_PERSONA_COLOR_CACHE = {}

def get_color_for_persona(name: str) -> str:
    if name not in _PERSONA_COLOR_CACHE:
        _PERSONA_COLOR_CACHE[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return _PERSONA_COLOR_CACHE[name]


def format_response_line(text: str, persona_name: str, highlight: str = None) -> str:
    color = get_color_for_persona(persona_name)
    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"
    elif highlight == "concern":
        background = "background-color: #f8d7da;"
    return (
        f"<div style='color:{color}; {background} padding:6px; "
        f"margin:4px 0; border-left:4px solid {color}; border-radius:4px;'>{text}</div>"
    )


# -------------------------
# Text extraction / sentiment
# -------------------------
def extract_persona_response(line: str) -> str:
    """
    Remove persona name and optional structured prefixes, return just the message body.
    Accept formats like:
      "John: - Response: I think..."
      "John: I think..."
      "[John]: - Response: ..."
    """
    if not isinstance(line, str):
        return ""
    # drop leading [ and ] around names
    # remove leading persona "Name:" or "[Name]:"
    line2 = re.sub(r"^\[?([^\]]+?)\]?:\s*", "", line)
    # if there is "- Response:" or "Response:" remove
    line2 = re.sub(r"^-?\s*Response:\s*", "", line2, flags=re.IGNORECASE)
    # remove leading "- " if present
    line2 = re.sub(r"^\s*-\s*", "", line2)
    return line2.strip()


_CONCERN_PATTERNS = re.compile(
    r"\b(worry|worried|concern|concerned|unsure|problem|issue|hard|difficult|frustrat|frustrated|confused|avoid)\b",
    flags=re.IGNORECASE
)
_INSIGHT_PATTERNS = re.compile(
    r"\b(think|like|improve|great|benefit|love|helpful|excellent|wonderful|suggest|prefer|interested)\b",
    flags=re.IGNORECASE
)


def detect_insight_or_concern(text: str):
    if not text:
        return None
    if _INSIGHT_PATTERNS.search(text):
        return "insight"
    if _CONCERN_PATTERNS.search(text):
        return "concern"
    return None


def score_sentiment(text: str) -> int:
    t = detect_insight_or_concern(text)
    if t == "insight":
        return 1
    if t == "concern":
        return -1
    return 0


# -------------------------
# Heatmap helper: build summary dataframe and chart
# -------------------------
def build_sentiment_summary(lines: List[str], selected_personas: List[Dict]):
    """
    Returns DataFrame with Persona and average sentiment score.
    `lines` are raw conversation lines. selected_personas is list of persona dicts.
    """
    rows = []
    for line in lines:
        for p in selected_personas:
            name = p.get("name")
            if line.startswith(name):
                text = extract_persona_response(line)
                rows.append({"Persona": name, "Sentiment": score_sentiment(text)})
    if not rows:
        # return zero rows for selected personas
        return pd.DataFrame({"Persona": [p.get("name") for p in selected_personas], "Sentiment": [0]*len(selected_personas)})
    df = pd.DataFrame(rows)
    df_summary = df.groupby("Persona")["Sentiment"].mean().reset_index()
    # ensure all selected personas present
    personas_order = [p.get("name") for p in selected_personas]
    df_summary = df_summary.set_index("Persona").reindex(personas_order, fill_value=0).reset_index()
    return df_summary


def build_heatmap_chart(df_summary):
    """
    Returns an altair bar chart (used like a heatmap) showing avg sentiment per persona.
    """
    chart = (
        alt.Chart(df_summary)
        .mark_bar()
        .encode(
            x=alt.X("Persona:N", sort="-y"),
            y=alt.Y("Sentiment:Q", scale=alt.Scale(domain=[-1, 1]), title="Average Sentiment"),
            color=alt.Color(
                "Sentiment:Q",
                scale=alt.Scale(domain=[-1, 0, 1], range=["#F94144", "#FFC300", "#3CB44B"]),
                legend=None
            ),
            tooltip=["Persona", "Sentiment"]
        )
        .properties(height=220)
    )
    return chart
