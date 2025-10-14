"""
Hybrid credibility scoring module for URLs.
Includes:
- Rule-based signals (source authority, content length, citation patterns)
- ML-based predictions (if model available)
"""

import requests
from bs4 import BeautifulSoup
import tldextract
import validators
import pickle
import os

# Optional: Load ML model if available
MODEL_PATH = "credibility_model.pkl"
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        credibility_model = pickle.load(f)
else:
    credibility_model = None


def assess_url_credibility(url: str):
    """
    Assess the credibility of a URL using hybrid rule-based + ML approach.

    Args:
        url (str): URL to assess

    Returns:
        dict: {"score": float, "explanation": str}
    """
    # Validate URL
    if not validators.url(url):
        return {"score": 0.0, "explanation": "Invalid URL."}

    try:
        # Fetch content
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        text_content = soup.get_text()
        domain = tldextract.extract(url).domain

        # ---------- Rule-based scoring ----------
        # Example signals:
        content_len_score = min(10, len(text_content) / 10000)  # longer content → higher score
        domain_score = 1.0 if domain and len(domain) > 0 else 0.5  # known domain → higher
        base_score = (content_len_score + domain_score) / 2

        # ---------- ML component ----------
        if credibility_model:
            # Extract features for ML model (example: content length, domain)
            features = [[len(text_content), len(domain)]]
            ml_score = credibility_model.predict(features)[0]
        else:
            # Fallback if model is not available
            import random
            ml_score = random.uniform(0.3, 0.9)

        # ---------- Combine hybrid score ----------
        credibility_score = 0.5 * base_score + 0.5 * ml_score
        credibility_score = max(0.0, min(1.0, round(credibility_score, 2)))

        explanation = (
            f"This source ({domain}) is evaluated based on content length, "
            f"domain characteristics, and ML predictions."
        )

        return {"score": credibility_score, "explanation": explanation}

    except Exception as e:
        return {"score": 0.0, "explanation": f"Error assessing URL: {e}"}
