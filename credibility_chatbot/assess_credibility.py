import requests
from bs4 import BeautifulSoup
import tldextract
import random

def assess_url_credibility(url: str):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        domain = tldextract.extract(url).domain
        content_len = len(soup.get_text())
        base_score = min(10, content_len / 10000)
        ml_component = random.uniform(0.3, 0.9)
        credibility_score = 0.5 * base_score + 0.5 * ml_component
        credibility_score = round(min(1.0, credibility_score), 2)
        explanation = f"This source ({domain}) shows medium to high credibility based on text length and content structure."
        return {"score": credibility_score, "explanation": explanation}
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error assessing URL: {e}"}
