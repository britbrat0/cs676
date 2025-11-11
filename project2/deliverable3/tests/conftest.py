import pytest

@pytest.fixture(autouse=True)
def disable_openai(monkeypatch):
    """Force all OpenAI calls to return a mock string."""
    def fake_generate_response(feature_inputs, personas):
        return f"Mocked feedback for {personas[0]['name'] if personas else 'Unknown Persona'}"

    # Patch both common locations
    monkeypatch.setattr("app.generate_response", fake_generate_response, raising=False)
    monkeypatch.setattr("utils.generate_response", fake_generate_response, raising=False)
    monkeypatch.setattr("openai_utils.generate_response", fake_generate_response, raising=False)
    yield
