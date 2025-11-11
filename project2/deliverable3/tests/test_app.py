import os
import json
import time
import pytest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import get_persona_by_id, backup_personas, restore_backup, generate_response

# ----------------------------
# Configuration for tests
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_PATH = os.path.join(BASE_DIR, "../personas_backup.json")

# Sample test personas
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
# Configuration for tests
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_PATH = os.path.join(BASE_DIR, "../personas_backup.json")

# Sample test personas
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
# AI Simulation Functional Test
# ----------------------------
def test_generate_response(session_state):
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = session_state.personas
    # This requires valid OPENAI_API_KEY
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Test Persona 1" in response or "Test Persona 2" in response

# ----------------------------
# Edge Case Tests
# ----------------------------
def test_empty_feature_input(session_state):
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert "Test Persona" in response

def test_large_feature_input(session_state):
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    personas = session_state.personas
    response = generate_response(feature_inputs, personas)
    assert len(response) > 0

# ----------------------------
# Performance & Stress Tests
# ----------------------------
def test_response_time(session_state):
    feature_inputs = {"Text Description": "Quick test", "File Upload": []}
    personas = session_state.personas
    start = time.time()
    generate_response(feature_inputs, personas)
    elapsed = time.time() - start
    # Basic performance benchmark: response < 5 seconds
    assert elapsed < 5.0

def test_concurrent_responses(session_state):
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
