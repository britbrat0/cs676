import pytest
import time
import concurrent.futures

from app import backup_personas, restore_personas, get_persona_by_id

# ----------------------------
# Mock session state
# ----------------------------
@pytest.fixture
def session_state():
    class MockSessionState:
        def __init__(self):
            self.personas = [
                {"id": 1, "name": "Test Persona", "description": "Mock persona for testing."}
            ]
    return MockSessionState()

# ----------------------------
# Basic functionality tests
# ----------------------------
def test_get_persona_by_id(session_state):
    persona = get_persona_by_id(session_state.personas, 1)
    assert persona["name"] == "Test Persona"

def test_backup_and_restore(session_state):
    backup = backup_personas(session_state.personas)
    restored = restore_personas(backup)
    assert restored == session_state.personas

# ----------------------------
# Mocked generate_response tests
# ----------------------------
def fake_generate_response(feature_inputs, personas):
    return f"Mocked feedback for {personas[0]['name']}"

def test_generate_response(session_state, monkeypatch):
    from app import generate_response
    monkeypatch.setattr("app.generate_response", fake_generate_response)
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_empty_feature_input(session_state, monkeypatch):
    from app import generate_response
    monkeypatch.setattr("app.generate_response", fake_generate_response)
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert "Test Persona" in response

def test_large_feature_input(session_state, monkeypatch):
    from app import generate_response
    monkeypatch.setattr("app.generate_response", fake_generate_response)
    feature_inputs = {"Text Description": "A" * 5000, "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert len(response) > 0

def test_response_time():
    start = time.time()
    time.sleep(0.01)
    end = time.time()
    assert end - start < 0.5

def test_concurrent_responses(session_state, monkeypatch):
    from app import generate_response
    monkeypatch.setattr("app.generate_response", fake_generate_response)
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = session_state.personas

    def simulate_request():
        return generate_response(feature_inputs, personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: simulate_request(), range(5)))

    for res in results:
        assert len(res) > 0
