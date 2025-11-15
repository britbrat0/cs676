from utils import extract_persona_response

def test_extract_basic():
    line = "John: - Response: I think this is good"
    assert extract_persona_response(line) == "I think this is good"

def test_no_prefix():
    line = "Some random text"
    assert extract_persona_response(line) == "Some random text"
