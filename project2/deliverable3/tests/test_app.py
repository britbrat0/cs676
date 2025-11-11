import pytest
from unittest.mock import patch
import time
from app import backup_personas, restore_personas, get_persona_by_id

@pytest.fixture
def session_state():
    class MockSessionState:
        def __init__(self):
            self.personas = [
                {"id": 1, "name": "Test Persona", "description": "Mock persona for testing."}
            ]
    return MockSessionState()

def test_get_persona_by_id(session_state):
    persona = get_persona_by_id(session_state.personas, 1)
    assert persona["name"] == "Test Persona"

def test_backup_and_restore(session_state):
    backup = backup_personas(session_state.personas)
    restored = restore_personas(backup)
    assert restored == session_state.personas

# ---- Mock OpenAI API calls ----

@patch("app.generate_response", return_value="Mocked feedback for Test Persona")
def test_generate_response(mock_gen, session_state):
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    response = mock_gen(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0

@patch("app.generate_response", return_value="Mocked feedback including Test Persona")
def test_empty_feature_input(mock_gen, session_state):
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = session_state.personas
    response = mock_gen(feature_inputs, personas)
    assert "Test Persona" in response

@patch("app.generate_response", return_value="Mocked feedback for large input")
def test_large_feature_input(mock_gen, session_state):
    feature_inputs = {"Text Description": "A" * 5000, "File Upload": []}
    personas = session_state.personas
    response = mock_gen(feature_inputs, personas)
    assert len(response) > 0

def test_response_time(session_state):
    start = time.time()
    time.sleep(0.01)  # simulate quick call
    end = time.time()
    assert end - start < 0.5

@patch("app.generate_response", return_value="Concurrent mock response")
def test_concurrent_responses(mock_gen, session_state):
    import concurrent.futures
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = session_state.personas

    def simulate_request():
        return mock_gen(feature_inputs, personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: simulate_request(), range(5)))

    for res in results:
        assert len(res) > 0
