# tests/test_app.py

import pytest
from unittest.mock import MagicMock, patch
from app import get_persona_by_id, backup_personas, restore_backup, generate_response

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def mock_st_session(monkeypatch):
    """Mock Streamlit session_state with sample personas."""
    import streamlit as st
    st.session_state.personas = [
        {"id": 1, "name": "Test Persona"},
        {"id": 2, "name": "Another Persona"}
    ]
    yield st.session_state
    st.session_state.personas = []  # Clean up after test

@pytest.fixture(autouse=True)
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Simulated response from persona."))]

    class FakeOpenAI:
        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                return fake_response

    monkeypatch.setattr("app.openai.ChatCompletion", FakeOpenAI.ChatCompletion)

# -----------------------------
# Tests
# -----------------------------

def test_get_persona_by_id(mock_st_session):
    persona = get_persona_by_id(1)
    assert persona is not None
    assert persona["name"] == "Test Persona"

def test_backup_and_restore(mock_st_session, tmp_path):
    backup_file = tmp_path / "backup.json"
    backup_personas(backup_file)
    # Reset session
    mock_st_session.personas = []
    restore_backup(backup_file)
    assert len(mock_st_session.personas) == 2
    assert mock_st_session.personas[0]["name"] == "Test Persona"

def test_generate_response(mock_st_session):
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = mock_st_session.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Simulated response" in response

def test_empty_feature_input(mock_st_session):
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = mock_st_session.personas
    response = generate_response(feature_inputs, personas)
    assert "Simulated response" in response

def test_large_feature_input(mock_st_session):
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    personas = mock_st_session.personas
    response = generate_response(feature_inputs, personas)
    assert len(response) > 0

def test_response_time(mock_st_session):
    import time
    start = time.time()
    feature_inputs = {"Text Description": "Timing test", "File Upload": []}
    personas = mock_st_session.personas
    _ = generate_response(feature_inputs, personas)
    duration = time.time() - start
    assert duration >= 0  # basic check, should complete

def test_concurrent_responses(mock_st_session):
    import concurrent.futures
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = mock_st_session.personas

    def simulate_request():
        return generate_response(feature_inputs, personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]

    for res in results:
        assert len(res) > 0
        assert "Simulated response" in res
