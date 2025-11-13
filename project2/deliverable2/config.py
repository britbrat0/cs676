import os

# -------------------------
# Model Config
# -------------------------
MODEL_CHOICES = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

OPENAI_DEFAULTS = {
    "temperature": 0.8,
    "max_tokens": 2000
}

REPORT_DEFAULTS = {
    "temperature": 0.7,
    "max_tokens": 2500
}

# -------------------------
# Persona & Colors
# -------------------------
DEFAULT_PERSONA_PATH = "personas.json"
PERSONA_COLORS = {}  # dynamically filled at runtime
