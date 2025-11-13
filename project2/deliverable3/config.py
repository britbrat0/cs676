import os

# -------------------------
# Model and API Config
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
# Persona Colors
# -------------------------
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

# -------------------------
# File Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PERSONA_PATH = os.path.join(BASE_DIR, "personas.json")
