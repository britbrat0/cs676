# ai_helpers.py
import time
from typing import List, Dict, Any
import types

# Try import openai if available. We'll expose a client object that tests can patch.
try:
    import openai
    client = openai
except Exception:
    # Provide a minimal stub client so code/tests can patch app.client.responses.create
    client = types.SimpleNamespace()
    client.responses = types.SimpleNamespace()
    def _stub_create(*args, **kwargs):
        raise RuntimeError("OpenAI client not installed")
    client.responses.create = _stub_create


def _build_prompt(personas: List[Dict], feature_inputs: Dict[str, Any], conversation_history: str) -> str:
    persona_block = "\n".join(
        f"- {p.get('name')} ({p.get('occupation','')}, Tech: {p.get('tech_proficiency','')})"
        for p in personas
    )
    feature_block = ""
    for k, v in feature_inputs.items():
        if isinstance(v, list):
            feature_block += f"{k}:\n{', '.join(v)}\n\n"
        else:
            feature_block += f"{k}:\n{v}\n\n"
    prompt = f"""
Personas:
{persona_block}

Feature Inputs:
{feature_block}

Conversation history:
{conversation_history}

Simulate one concise response per persona. For each persona output a single line in the format:
<Persona Name>: - Response: <their 1-2 sentence response>
Do not add extra commentary.
"""
    return prompt.strip()


def generate_response_with_retry(feature_inputs: Dict, personas: List[Dict], conversation_history: str, model_choice: str, retries: int = 2, backoff: float = 1.0) -> List[Dict]:
    """
    Calls client.responses.create and returns list of dicts: {"persona": name, "response": text, "error": bool}
    On failure, returns list with error True for each persona.
    The tests patch `app.client.responses.create` so we call client.responses.create here.
    """
    prompt = _build_prompt(personas, feature_inputs, conversation_history)

    attempt = 0
    while True:
        try:
            # use the same call shape tests expect to patch
            resp = client.responses.create(model=model_choice, input=prompt)
            # many OpenAI SDKs return text in different places; be defensive:
            text = ""
            if hasattr(resp, "output_text"):
                text = resp.output_text
            elif isinstance(resp, dict) and "output" in resp:
                # hypothetical structure
                text = resp["output"]
            elif hasattr(resp, "choices") and resp.choices:
                # classic ChatCompletion-like object used in some SDKs
                text = resp.choices[0].message.content
            else:
                # fallback: string repr
                text = str(resp)

            # now split by persona lines
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            outputs = []
            for p in personas:
                # find first line that starts with the persona name
                found = None
                for ln in lines:
                    if ln.startswith(p.get("name")):
                        found = ln
                        break
                if found:
                    # extract response body after colon or "Response:"
                    # reuse simple parsing
                    body = found.split(":", 1)[1] if ":" in found else found
                    outputs.append({"persona": p.get("name"), "response": body.strip(), "error": False})
                else:
                    # fallback: no explicit match; create an empty response
                    outputs.append({"persona": p.get("name"), "response": "", "error": False})
            return outputs

        except Exception as e:
            attempt += 1
            if attempt > retries:
                # return error objects for all personas so tests can assert error paths
                return [{"persona": p.get("name"), "response": "", "error": True, "error_message": str(e)} for p in personas]
            time.sleep(backoff * attempt)
