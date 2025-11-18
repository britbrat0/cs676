import openai
import logging
import time
from typing import List, Dict, Optional
from config import OPENAI_DEFAULTS, REPORT_DEFAULTS
from utils import build_sentiment_summary, extract_persona_response  # utils in same package

log = logging.getLogger(__name__)

def build_prompt(personas: List[Dict], feature_inputs: Dict, conversation_history: str = "") -> str:
    """Construct a compact prompt for the chat model."""
    persona_block = "\n".join(
        f"- {p['name']} ({p['occupation']}, {p.get('location','')}, Tech: {p.get('tech_proficiency','')})"
        for p in personas
    )
    feature_block = ""
    for k, v in feature_inputs.items():
        vtxt = ", ".join(v) if isinstance(v, list) else (v or "")
        feature_block += f"{k}:\n{vtxt}\n\n"

    prompt = f"""
Personas:
{persona_block}

Features:
{feature_block}

Simulate a realistic persona conversation. Each persona should reply in 2-3 sentences.
Use this template for each persona:

[Persona Name]:
- Response: <what they say>
- Reasoning: <why>
- Confidence: <High|Medium|Low>
- Suggested follow-up: <question>

"""
    if conversation_history:
        prompt += f"\nPrevious conversation:\n{conversation_history}\nContinue naturally."
    return prompt.strip()

def generate_response(feature_inputs: Dict, personas: List[Dict], history: str, model: str) -> str:
    """Single-shot OpenAI call (may raise exceptions)."""
    prompt = build_prompt(personas, feature_inputs, history)
    resp = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI facilitator for a virtual focus group."},
            {"role": "user", "content": prompt}
        ],
        temperature=OPENAI_DEFAULTS.get("temperature", 0.8),
        max_tokens=OPENAI_DEFAULTS.get("max_tokens", 1500)
    )
    return resp.choices[0].message.content.strip()

def generate_response_with_retry(feature_inputs: Dict, personas: List[Dict], history: str, model: str, retries: int = 3, backoff: float = 1.0) -> str:
    """Call OpenAI with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            return generate_response(feature_inputs, personas, history, model)
        except Exception as e:
            log.exception("OpenAI call failed (attempt %s): %s", attempt + 1, e)
            if attempt + 1 < retries:
                time.sleep(backoff * (2 ** attempt))
            else:
                # final failure
                raise

def generate_feedback_report(conversation: str, model: str) -> str:
    """Generate a structured feedback report using OpenAI."""
    prompt = f"""
Analyze the following conversation and create a structured feedback report.

Conversation:
{conversation}

Sections:
- Executive Summary
- Patterns & Themes
- Consensus Points
- Disagreements & Concerns
- Persona Insights
- Actionable Recommendations
- Quantitative Metrics (acceptance %, likelihood per persona, priority)
- Risk Assessment
"""
    resp = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert product analyst and UX researcher."},
            {"role": "user", "content": prompt}
        ],
        temperature=REPORT_DEFAULTS.get("temperature", 0.7),
        max_tokens=REPORT_DEFAULTS.get("max_tokens", 1500)
    )
    return resp.choices[0].message.content
