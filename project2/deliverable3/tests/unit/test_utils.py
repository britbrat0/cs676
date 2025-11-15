import pytest
from utils import detect_insight_or_concern, score_sentiment, get_color_for_persona

def test_detect_insight():
    assert detect_insight_or_concern("This is great") == "insight"

def test_detect_concern():
    assert detect_insight_or_concern("I'm worried about this") == "concern"

def test_detect_neutral():
    assert detect_insight_or_concern("Hello world") is None

def test_score_sentiment():
    assert score_sentiment("great work") == 1
    assert score_sentiment("I'm concerned") == -1
    assert score_sentiment("nothing here") == 0

def test_color_generation_stable():
    c1 = get_color_for_persona("Alice")
    c2 = get_color_for_persona("Alice")
    assert c1 == c2
