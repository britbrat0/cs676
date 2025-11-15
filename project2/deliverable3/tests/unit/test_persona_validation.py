from utils import validate_persona

def test_valid_persona():
    p = {
        "name": "Test",
        "occupation": "Engineer",
        "tech_proficiency": "High",
        "behavioral_traits": ["curious", "thoughtful"]
    }
    assert validate_persona(p)

def test_missing_field():
    p = {"name": "X"}
    assert validate_persona(p) is False

def test_invalid_traits_type():
    p = {
        "name": "Test",
        "occupation": "Engineer",
        "tech_proficiency": "High",
        "behavioral_traits": "not a list"
    }
    assert validate_persona(p) is False
