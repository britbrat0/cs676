# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_CHOICES = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

# where the default personas.json lives
DEFAULT_PERSONA_PATH = os.path.join(BASE_DIR, "personas", "personas.json")

OPENAI_DEFAULTS = {
    "temperature": 0.8,
    "max_tokens": 1500
}

REPORT_DEFAULTS = {
    "temperature": 0.7,
    "max_tokens": 2000
}

# optional initial color palette (utils will extend on demand)
PERSONA_COLORS = {
    "Sophia Martinez": "#E6194B",
    "Jamal Robinson": "#3CB44B",
    "Eleanor Chen": "#FFE119",
    "Diego Alvarez": "#4363D8",
    "Anita Patel": "#F58231",
}
