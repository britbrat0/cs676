import json
import re
import streamlit as st
import pandas as pd
import altair as alt
import logging
from typing import List, Dict, Optional

from config import DEFAULT_PERSONA_PATH, PERSONA_COLORS as CONFIG_PERSONA_COLORS

log = logging.getLogger(__name__)

# In-memory color map
PERSONA_COLORS = dict(CONFIG_PERSONA_COLORS) if isinstance(CONFIG_PERSONA_COLORS, dict) else {}

# -------------------------
# Personas I/O & validation
# -------------------------

def load_personas_from_file(path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """Load personas from disk, return [] if missing."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                st.warning(f"{path} does not contain a list.")
                return []
            return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in {path}: {e}")
        return []
    except Exception as e:
        st.error(f"Error loading personas: {e}")
        return []


def get_personas(uploaded_file=None, path: str = DEFAULT_PERSONA_PATH) -> List[Dict]:
    """Return personas, optionally replacing with uploaded."""
    personas = load_personas_from_file(path)

    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            if not isinstance(imported, list):
                st.error("Uploaded persona file must be a JSON LIST.")
                return personas
            personas = imported
            with open(path, "w", encoding="utf-8") as f:
                json.dump(personas, f, indent=2)
            st.success("Personas imported & saved!")
        except Exception as e:
            st.error(f"Could not load uploaded personas: {e}")

    return personas


def validate_persona(persona: Dict) -> bool:
    required = ["name", "occupation", "tech_proficiency", "behavioral_traits"]
    for r in required:
        if r not in persona or not persona[r]:
            return False
    return isinstance(persona.get("behavioral_traits"), list)


def save_personas(personas: List[Dict], path: str = DEFAULT_PERSONA_PATH) -> bool:
    """Persist personas."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Could not save personas: {e}")
        return False


# -------------------------
# Display & formatting
# -------------------------

def get_color_for_persona(name: str) -> str:
    if name not in PERSONA_COLORS:
        PERSONA_COLORS[name] = f"#{(hash(name) & 0xFFFFFF):06x}"
    return PERSONA_COLORS[name]


def format_response_line(text: str, persona_name: str, highlight: Optional[str] = None) -> str:
    color = get_color_for_persona(persona_name)

    background = ""
    if highlight == "insight":
        background = "background-color: #d4edda;"  # light green
    elif highlight == "concern":
        background = "background-color: #f8d7da;"  # light red

    return (
        f"<div style='color:{color}; {background} padding:8px; "
        f"margin:6px 0; border-left:4px solid {color}; border-radius:4px; "
        f"white-space:pre-wrap;'>{text}</div>"
    )


# -------------------------
# Text parsing & sentiment
# -------------------------

# Expanded patterns (now pass your tests)
_INSIGHT_PATTERN = re.compile(
    r'\b(think|improve|great|helpful|excellent|love|benefit|useful|like)\b',
    re.I
)

_CONCERN_PATTERN = re.compile(
    r'\b(worry|worried|concern|concerned|problem|issue|difficult|hard|confused|confusing|frustrat|frustrated|dislike)\b',
    re.I
)


def extract_persona_response(line: str) -> str:
    log.info(f"[extract IN] {line}")

    original = line

    # Remove leading '- Response:' (optional spaces/dashes)
    line = re.sub(r'^\s*-\s*Response\s*[:\-—]*\s*', '', line, flags=re.I)

    line = line.strip()

    log.info(f"[extract OUT] original='{original}' → extracted='{line}'")
    return line


def detect_insight_or_concern(text: str) -> Optional[str]:
    log.info(f"[detect] analyzing: '{text}'")

    if not text:
        return None
    if _INSIGHT_PATTERN.search(text):
        log.info("[detect] → insight")
        return "insight"
    if _CONCERN_PATTERN.search(text):
        log.info("[detect] → concern")
        return "concern"

    log.info("[detect] → none")
    return None


def score_sentiment(text: str) -> int:
    cat = detect_insight_or_concern(text)
    if cat == "insight":
        return 1
    if cat == "concern":
        return -1
    return 0


# -------------------------
# Heatmap / Chart builder
# -------------------------

def build_sentiment_summary(lines: List[str], selected_personas: List[Dict]) -> pd.DataFrame:
    rows = []

    for raw_line in lines:
        # Normalize markdown persona names like "**Ava:**"
        line = re.sub(r'^\*+\s*(.+?)\s*\*+:', r'\1:', raw_line)

        for p in selected_personas:
            name = p["name"]

            # Match "Ava:", "Ava -", "Ava —", etc.
            if re.match(rf'^{re.escape(name)}[\s:\-—]+', line):
                text = extract_persona_response(line)
                sentiment = score_sentiment(text)
                rows.append({"Persona": name, "Sentiment": sentiment})

    if not rows:
        # Every persona gets neutral score
        names = [p["name"] for p in selected_personas]
        return pd.DataFrame({"Persona": names, "Sentiment": [0]*len(names)})

    df = pd.DataFrame(rows)
    names = [p["name"] for p in selected_personas]
    summary = df.groupby("Persona")["Sentiment"].mean().reindex(names, fill_value=0).reset_index()
    return summary


def build_heatmap_chart(df_summary: pd.DataFrame, height: int = 220) -> alt.Chart:
    return (
        alt.Chart(df_summary)
        .mark_bar()
        .encode(
            x=alt.X("Persona", sort="-y"),
            y=alt.Y("Sentiment", title="Avg Sentiment", scale=alt.Scale(domain=[-1, 1])),
            color=alt.Color(
                "Sentiment",
                scale=alt.Scale(
                    domain=[-1, 0, 1],
                    range=["#F94144", "#FFC300", "#3CB44B"]
                ),
                legend=None
            ),
            tooltip=["Persona", "Sentiment"]
        )
        .properties(height=height)
    )
