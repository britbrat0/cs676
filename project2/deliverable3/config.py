# config.py
from typing import List, Dict

MODEL_CHOICES = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

# Where personas are stored by default (repo root)
DEFAULT_PERSONA_PATH = "personas.json"

# small defaults for OpenAI calls
OPENAI_DEFAULTS = {
    "temperature": 0.8,
    "max_tokens": 1200,
    "n_retries": 2,
    "retry_backoff": 1.0
}

REPORT_DEFAULTS = {
    "temperature": 0.6,
    "max_tokens": 1500
}

# default persona colors (can be extended)
PERSONA_COLORS = {
    "Sophia Martinez": "#E6194B",
    "Jamal Robinson": "#3CB44B",
    "Eleanor Chen": "#FFE119",
    "Diego Alvarez": "#4363D8",
    "Anita Patel": "#F58231",
    "Robert Klein": "#911EB4",
    "Nia Thompson": "#46F0F0",
    "Marcus Green": "#F032E6",
    "Aisha Mbatha": "#BCF60C",
    "Owen Gallagher": "#FABEBE",
}
