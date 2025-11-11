# tests/test_app.py
import os
import json
import time
import pytest
from unittest.mock import patch, MagicMock

# ----------------------------
# Fix imports for local folder structure
# ----------------------------
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))

from app import get_persona_by_id, backup_personas, restore_backup, generate_response

# ----------------------------
# Sample test personas
# ----------------------------
TEST_PERSONAS = [
    {
        "id": 1,
        "name": "Test Persona 1",
        "occupation": "Engineer",
        "location": "NY",
        "tech_proficiency": "High",
        "behavioral_traits": ["curious", "analytical"]
    },
    {
        "id": 2,
        "name": "Test Persona 2",
        "occupation": "Designer",
        "location": "SF",
        "tech_proficiency": "Medium",
        "behavioral_traits": ["creative", "critical"]
    }
]

# ----------------------------
# Fixture to reset session state for testing
# ----------------------------
@pytest.fixture
def session_state(monkeypatch):
    import streamlit as st
    st.session_state.personas = TEST_PERSONAS.copy()
    yield st.session_state
    st.session_state.personas = []

# ----------------------------
# Functional Tests
# ----------------------------
def test_get_persona_by_id(session_state):
    persona = get_persona_by_id(1)
    assert persona["name"] == "Test Persona 1"
    assert get_persona_by_id(999) is None

def test_backup_and_restore(session_state, tmp_path):
    # Backup current session personas
    backup_file = tmp_path / "backup.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("app.BACKUP_FILE", str(backup_file))
    backup_personas()
    
    # Clear session and restore
    session_state.personas = []
    restore_backup()
    assert len(session_state.personas) == 2
    assert session_state.personas[0]["name"] == "Test Persona 1"

# ----------------------------
# Mocked AI Simulation Tests
# ----------------------------
@patch("app.openai.chat.completions.create")
def test_generate_response(mock_openai, session_state):
    # Mock a fake API response
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Test Persona 1: response\nTest Persona 2: response"))]
    mock_openai.return_value = fake_response

    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)

    assert isinstance(response, str)
    assert len(response) > 0
    assert "Test Persona 1" in response or "Test Persona 2" in response

@patch("app.openai.chat.completions.create")
def test_empty_feature_input(mock_openai, session_state):
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Test Persona 1 response"))]

    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert "Test Persona" in response

@patch("app.openai.chat.completions.create")
def test_large_feature_input(mock_openai, session_state):
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Test Persona 1 response"))]

    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert len(response) > 0

@patch("app.openai.chat.completions.create")
def test_response_time(mock_openai, session_state):
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Test Persona 1 response"))]

    feature_inputs = {"Text Description": "Quick test", "File Upload": []}
    personas = session_state.personas
    start = time.time()
    generate_response(feature_inputs, personas)
    elapsed = time.time() - start
    assert elapsed < 5.0  # basic performance benchmark

@patch("app.openai.chat.completions.create")
def test_concurrent_responses(mock_openai, session_state):
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Test Persona 1 response"))]

    import concurrent.futures
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = session_state.personas
    
    def simulate_request():
        return generate_response(feature_inputs, personas)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]
    
    for res in results:
        assert len(res) > 0
