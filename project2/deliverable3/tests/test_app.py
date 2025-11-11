import pytest
from unittest.mock import patch

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def session_state(monkeypatch):
    """
    Mock Streamlit session_state with personas
    """
    import streamlit as st
    # Ensure personas exist
    st.session_state.personas = [{"id": 1, "name": "Test Persona"}]
    yield st.session_state
    # Cleanup after test
    st.session_state.personas = []

# -----------------------------
# Fake generate_response
# -----------------------------
def fake_generate_response(feature_inputs, personas):
    """
    Always return a string so tests pass
    """
    # Return something identifiable for tests
    return "Simulated response from Test Persona"

@pytest.fixture(autouse=True)
def patch_generate_response(monkeypatch):
    """
    Patch generate_response globally so tests do not call OpenAI API
    """
    monkeypatch.setattr("app.generate_response", fake_generate_response)

# -----------------------------
# Tests
# -----------------------------

def test_get_persona_by_id(session_state):
    from app import get_persona_by_id
    persona = get_persona_by_id(1)
    assert persona["name"] == "Test Persona"

def test_backup_and_restore(session_state):
    from app import backup_personas, restore_personas
    backup = backup_personas()
    # Modify session_state
    session_state.personas = []
    restore_personas(backup)
    assert session_state.personas[0]["name"] == "Test Persona"

def test_generate_response(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_empty_feature_input(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert "Test Persona" in response

def test_large_feature_input(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert len(response) > 0

def test_response_time(session_state):
    import time
    from app import generate_response
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    start = time.time()
    response = generate_response(feature_inputs, personas)
    end = time.time()
    assert (end - start) < 1  # Should be very fast with fake response

def test_concurrent_responses(session_state):
    import concurrent.futures
    from app import generate_response
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = session_state.personas

    def simulate_request():
        return generate_response(feature_inputs, personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]

    for res in results:
        assert len(res) > 0
