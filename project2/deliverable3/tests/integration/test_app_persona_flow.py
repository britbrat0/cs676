import json
from app import generate_persona_responses

def test_generate_responses_basic(mock_openai_success):
    personas = [{"name": "TestPersona"}]
    out = generate_persona_responses("Hello world", personas)
    assert isinstance(out, list)
    assert "great" in out[0]["text"].lower()
