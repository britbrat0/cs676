import json
import logging
import openai
import time
from typing import Dict, List, Any, Optional

# ---------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------
class PersonaLoadError(Exception):
    pass


class EmptyPersonaError(Exception):
    pass


class APIRequestError(Exception):
    pass


# ---------------------------------------------------------
# Safe JSON Loader
# ---------------------------------------------------------
def load_json_file(path: str) -> Any:
    """
    Safely load a JSON file with clear error reporting.
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise PersonaLoadError(f"JSON file missing: {path}")
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON in {path}: {e}")
        raise PersonaLoadError(f"Malformed JSON in {path}: {e}")


# ---------------------------------------------------------
# Persona Utilities
# ---------------------------------------------------------
def load_personas(path: str) -> List[Dict[str, Any]]:
    """
    Load personas from JSON with validation.
    """
    personas = load_json_file(path)

    if not isinstance(personas, list):
        raise PersonaLoadError("Personas JSON must be a list of persona objects.")

    if len(personas) == 0:
        raise EmptyPersonaError("The persona list is empty.")

    # Validate each persona
    for p in personas:
        if "id" not in p or "name" not in p:
            raise PersonaLoadError(f"Persona missing required fields: {p}")

    return personas


def save_personas(path: str, personas: List[Dict[str, Any]]) -> None:
    """
    Save personas back to JSON safely.
    """
    try:
        with open(path, "w") as f:
            json.dump(personas, f, indent=4)
        logger.info("Personas saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save personas: {e}")
        raise PersonaLoadError(f"Failed to save personas: {e}")


def add_persona(path: str, persona: Dict[str, Any]) -> None:
    """
    Create a new persona and save it.
    """
    personas = load_personas(path)

    if not isinstance(persona, dict):
        raise PersonaLoadError("Persona must be a JSON object.")

    required = ["id", "name", "background", "goals", "frustrations"]
    missing = [f for f in required if f not in persona]

    if missing:
        raise PersonaLoadError(f"Persona is missing required fields: {missing}")

    personas.append(persona)
    save_personas(path, personas)


# ---------------------------------------------------------
# OpenAI API Helper with Retry + Timeout
# ---------------------------------------------------------
def call_openai_model(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4.1-mini",
    max_retries: int = 3,
    timeout_seconds: int = 20,
) -> str:
    """
    Wrapper for OpenAI calls with retry logic, timeout handling,
    and clear error propagation.
    """

    for attempt in range(max_retries):
        try:
            start = time.time()

            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=timeout_seconds,
            )

            elapsed = time.time() - start
            logger.info(f"OpenAI call succeeded in {elapsed:.2f}s")

            return response.choices[0].message["content"]

        except Exception as e:
            logger.warning(
                f"OpenAI call failed (attempt {attempt + 1}/{max_retries}): {e}"
            )

            if attempt == max_retries - 1:
                logger.error("Max retries reached. Raising APIRequestError.")
                raise APIRequestError(f"OpenAI API failed after {max_retries} attempts.")

            time.sleep(1.5)  # backoff


# ---------------------------------------------------------
# Input Validation Helpers
# ---------------------------------------------------------
def validate_user_input(text: Optional[str]) -> str:
    """
    Reject empty or invalid input fields.
    """
    if not text or text.strip() == "":
        raise ValueError("Input text cannot be empty.")
    return text.strip()
