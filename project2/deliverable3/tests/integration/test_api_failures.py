from app import generate_persona_responses

def test_api_failure_returns_error(mock_openai_fail):
    personas = [{"name": "TestPersona"}]
    out = generate_persona_responses("Hello", personas)
    assert out[0]["error"] is True
