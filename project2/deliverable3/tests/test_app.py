import pytest
from unittest.mock import MagicMock
import time

# Adjust sys.path so Python can find app.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))

from app import (
    get_persona_by_id,
    backup_personas,
    restore_backup,
    generate_response,
    RESPONSE_TIME,
    REQUEST_COUNTER
)

# --------------------------
# Sample test personas
# --------------------------
TEST_PERSONAS = [
    {"id": 1, "name": "Alice", "occupation": "Engineer", "location": "NY",
     "tech_proficiency": "High", "behavioral_traits": ["curious", "analytical"]},
    {"id": 2, "name": "Bob", "occupation": "Designer", "location": "SF",
     "tech_proficiency": "Medium", "behavioral_traits": ["creative", "critical"]}
]

# --------------------------
# Fixtures
# --------------------------
@pytest.fixture
def mock_personas(monkeypatch):
    """Set up a fake Streamlit session state with personas."""
    import streamlit as st
    st.session_state.personas = TEST_PERSONAS.copy()
    yield st.session_state
    st.session_state.personas = []

@pytest.fixture(autouse=True)
def mock_openai_create(monkeypatch):
    """Mock OpenAI API responses for generate_response."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Alice: response\nBob: response"))]

    class FakeOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    return fake_response

    monkeypatch.setattr("app.openai", FakeOpenAI)
    yield

# --------------------------
# Tests
# --------------------------
def test_get_persona_by_id(mock_personas):
    assert get_persona_by_id(1)["name"] == "Alice"
    assert get_persona_by_id(2)["name"] == "Bob"
    assert get_persona_by_id(999) is None

def test_backup_and_restore(mock_personas, tmp_path):
    backup_file = tmp_path / "backup.json"
    # Backup current personas
    backup_personas(str(backup_file))
    # Clear session_state
    import streamlit as st
    st.session_state.personas = []
    assert st.session_state.personas == []
    # Restore
    restore_backup(str(backup_file))
    assert len(st.session_state.personas) == 2
    assert st.session_state.personas[0]["name"] == "Alice"

def test_generate_response_returns_text(mock_personas):
    feature_inputs = {"Text Description": "Test feature", "File Upload": []}
    personas = mock_personas.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Alice" in response
    assert "Bob" in response

def test_empty_feature_input(mock_personas):
    feature_inputs = {"Text Description": "", "File Upload": []}
    personas = mock_personas.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_large_feature_input(mock_personas):
    feature_inputs = {"Text Description": "A"*5000, "File Upload": []}
    personas = mock_personas.personas
    response = generate_response(feature_inputs, personas)
    assert isinstance(response, str)
    assert len(response) > 0

def test_response_time(mock_personas):
    start_count = len(RESPONSE_TIME._metrics)
    feature_inputs = {"Text Description": "Test timing", "File Upload": []}
    personas = mock_personas.personas
    generate_response(feature_inputs, personas)
    assert len(RESPONSE_TIME._metrics) >= start_count

def test_concurrent_responses(mock_personas):
    import concurrent.futures
    feature_inputs = {"Text Description": "Load test", "File Upload": []}
    personas = mock_personas.personas

    def simulate_request():
        return generate_response(feature_inputs, personas)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_request) for _ in range(5)]
        results = [f.result() for f in futures]

    for res in results:
        assert isinstance(res, str)
        assert len(res) > 0
