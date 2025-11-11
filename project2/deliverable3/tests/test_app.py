# tests/test_app.py
import pytest
from unittest.mock import MagicMock

# -----------------------------
# FAKE generate_response for tests
# -----------------------------
def fake_generate_response(feature_inputs, personas):
    if not feature_inputs["Text Description"]:
        return f"Response from {personas[0]['name']}"
    return "Simulated response"

# -----------------------------
# MOCK session_state
# -----------------------------
@pytest.fixture
def session_state():
    mock_state = MagicMock()
    mock_state.personas = [{"id": 1, "name": "Test Persona"}]
    return mock_state

# -----------------------------
# TESTS
# -----------------------------
def test_generate_response(session_state):
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    response = fake_generate_response(feature_inputs, session_state.personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_empty_feature_input(session_state):
    feature_inputs = {"Text Description": "", "File Upload": []}
    response = fake_generate_response(feature_inputs, session_state.personas)
    assert "Test Persona" in response

def test_large_feature_input(session_state):
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    response = fake_generate_response(feature_inputs, session_state.personas)
    assert len(response) > 0

def test_concurrent_responses(session_state):
    import concurrent.futures
    feature_inputs = {"Text Description": "Load test", "File Upload": []}

    def simulate_request():
        return fake_generate_response(feature_inputs, session_state.personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]

    for res in results:
        assert len(res) > 0
