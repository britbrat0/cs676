import pytest
from unittest.mock import patch

# -----------------------------
# Fake generate_response
# -----------------------------
def fake_generate_response(feature_inputs, personas):
    return "Simulated response from Test Persona"

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def session_state(monkeypatch):
    import streamlit as st
    st.session_state.personas = [{"id": 1, "name": "Test Persona"}]
    yield st.session_state
    st.session_state.personas = []

# -----------------------------
# Tests
# -----------------------------
@pytest.fixture(autouse=True)
def patch_generate(monkeypatch):
    # Patch generate_response in the app module
    import app
    monkeypatch.setattr(app, "generate_response", fake_generate_response)

def test_get_persona_by_id(session_state):
    from app import get_persona_by_id
    persona = get_persona_by_id(1)
    assert persona["name"] == "Test Persona"

def test_backup_and_restore(session_state):
    from app import backup_personas, restore_personas
    backup = backup_personas()
    session_state.personas = []
    restore_personas(backup)
    assert session_state.personas[0]["name"] == "Test Persona"

def test_generate_response(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    response = generate_response(feature_inputs, session_state.personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_empty_feature_input(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "", "File Upload": []}
    response = generate_response(feature_inputs, session_state.personas)
    assert "Test Persona" in response

def test_large_feature_input(session_state):
    from app import generate_response
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    response = generate_response(feature_inputs, session_state.personas)
    assert len(response) > 0

def test_response_time(session_state):
    import time
    from app import generate_response
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    start = time.time()
    response = generate_response(feature_inputs, session_state.personas)
    end = time.time()
    assert (end - start) < 1

def test_concurrent_responses(session_state):
    import concurrent.futures
    from app import generate_response
    feature_inputs = {"Text Description": "Load test", "File Upload": []}

    def simulate_request():
        return generate_response(feature_inputs, session_state.personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]

    for res in results:
        assert len(res) > 0
