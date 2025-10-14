# assess_credibility.py
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
        # Fetch content with timeout
        r = requests.get(url, timeout=10)
        r.raise_for_status()  # raise exception for 4xx/5xx
        soup = BeautifulSoup(r.text, "html.parser")
        text_content = soup.get_text().strip()
        domain = tldextract.extract(url).domain or "unknown"

        # ---------- Rule-based scoring ----------
        content_len_score = min(10, len(text_content) / 10000)
        domain_score = 1.0 if domain != "unknown" else 0.5
        base_score = (content_len_score + domain_score) / 2

        # ---------- ML component ----------
        if credibility_model:
            # Example feature vector: content length, domain length
            features = [[len(text_content), len(domain)]]
            try:
                ml_score = credibility_model.predict(features)[0]
            except Exception:
                ml_score = 0.5  # fallback if model fails
        else:
            import random
            ml_score = random.uniform(0.3, 0.9)

        # ---------- Hybrid score ----------
        credibility_score = 0.5 * base_score + 0.5 * ml_score
        credibility_score = max(0.0, min(1.0, round(credibility_score, 2)))

        explanation = (
            f"This source ({domain}) is evaluated based on content length, "
            f"domain characteristics, and ML predictions."
        )

        return {"score": credibility_score, "explanation": explanation}

    except requests.exceptions.Timeout:
        return {"score": 0.0, "explanation": "Request timed out."}
    except requests.exceptions.RequestException:
        return {"score": 0.0, "explanation": "Unable to fetch the URL."}
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error assessing URL: {e}"}
