from utils import detect_insight_or_concern

def test_keywords_case_insensitive():
    assert detect_insight_or_concern("LOVE this!") == "insight"
    assert detect_insight_or_concern("FRUSTRATED with UI") == "concern"
