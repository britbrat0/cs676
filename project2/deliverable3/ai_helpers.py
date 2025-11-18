# ai_helpers.py
import time
import json
from typing import List, Dict, Optional

import openai
from config import OPENAI_DEFAULTS, REPORT_DEFAULTS

# Make a module-level reference to the openai client so tests can patch app.client
client = openai


def _call_chat_completion(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """
    Thin wrapper around the OpenAI Chat API.
    Returns the assistant text (str). Raises exceptions on failure.
    """
    # Use the Chat Completions (or Responses) API depending on available attributes.
    # Keep call minimal so tests can patch client.responses.create or client.chat.completions.create
    # Try preferred attributes in order.
    try:
        # Try the 'responses' style if available (newer OpenAI SDKs)
        if hasattr(client, "responses") and hasattr(client.responses, "create"):
            resp = client.responses.create(
                model=model,
                input=prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            # Many 'responses' objects include .output_text or nested choices; try several fallbacks
            if hasattr(resp, "output_text"):
                return resp.output_text
            # fallback to parsing JSON-like structure
            try:
                # some mock objects in tests supply dict-like responses
                out = getattr(resp, "output", None) or resp
                # if it's a mapping with 'content' or 'choices'
                if isinstance(out, dict):
                    # try to extract a text field
                    if "output_text" in out:
                        return out["output_text"]
                    if "choices" in out and len(out["choices"]) > 0:
                        c = out["choices"][0]
                        return c.get("text") or c.get("message", {}).get("content", "")
                # fallback to string conversion
                return str(resp)
            except Exception:
                return str(resp)

        # else try legacy chat completion
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # standard response path
            return resp.choices[0].message.content
        elif hasattr(client, "ChatCompletion") or hasattr(client, "chat_completions"):
            # Some SDK variants
            resp = client.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        else:
            # fallback to attribute that tests likely patch: client.responses.create or client.chat.completions.create
            raise RuntimeError("No supported OpenAI client method found on 'client'.")
    except Exception:
        # re-raise so caller can handle retries
        raise


def generate_response_with_retry(feature_inputs: Dict, personas: List[Dict], conversation_history: str, model_choice: str) -> str:
    """
    Call the language model to generate a simulated multi-persona conversation.
    Returns the returned chat text (string). On failure, raises the underlying exception.
    """
    # build prompt (simple)
    persona_block = "\n".join(
        f"- {p.get('name')} ({p.get('occupation','')}, Tech: {p.get('tech_proficiency','')})" for p in personas
    )

    feature_block = ""
    for k, v in feature_inputs.items():
        if isinstance(v, list):
            feature_block += f"{k}:\n{', '.join(v)}\n\n"
        else:
            feature_block += f"{k}:\n{v}\n\n"

    prompt = (
        f"Personas:\n{persona_block}\n\n"
        f"Feature:\n{feature_block}\n\n"
        "Simulate a conversation between these personas. For each persona include the persona name and a short response. "
        "Keep each persona's contribution on its own line starting with the persona name. Keep responses concise.\n\n"
    )
    if conversation_history:
        prompt += f"Previous conversation:\n{conversation_history}\nContinue naturally.\n"

    n_retries = OPENAI_DEFAULTS.get("n_retries", 2)
    backoff = OPENAI_DEFAULTS.get("retry_backoff", 1.0)
    temp = OPENAI_DEFAULTS.get("temperature", 0.8)
    max_tokens = OPENAI_DEFAULTS.get("max_tokens", 800)

    last_exc = None
    for attempt in range(n_retries + 1):
        try:
            txt = _call_chat_completion(prompt, model_choice, temp, max_tokens)
            # normalize to string
            return str(txt)
        except Exception as e:
            last_exc = e
            if attempt < n_retries:
                time.sleep(backoff * (attempt + 1))
            else:
                # final raise so callers can decide how to convert to error responses
                raise last_exc


def generate_feedback_report(conversation: str, model_choice: str) -> str:
    """
    Generates a report analyzing conversation using the LM.
    Returns report text or raises on failure.
    """
    prompt = (
        f"Analyze the following conversation and produce a concise UX research report.\n\nConversation:\n{conversation}\n\n"
        "Include: Executive Summary, Patterns & Themes, Consensus Points, Disagreements & Concerns, Persona Insights, "
        "Actionable Recommendations, Quantitative Metrics (acceptance %, likelihood by persona), Risk Assessment."
    )
    try:
        out = _call_chat_completion(prompt, model_choice, REPORT_DEFAULTS["temperature"], REPORT_DEFAULTS["max_tokens"])
        return str(out)
    except Exception:
        raise
