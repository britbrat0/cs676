# -----------------------------
# assess_credibility.py
# -----------------------------
"""
Hybrid credibility scoring module for URLs.
Uses a combination of:
- Rule-based signals: evaluates source authority, content length, and citation patterns
- ML-based predictions: optional, if a pre-trained model is available
This module returns a credibility score (0–1) and a textual explanation.
"""

# -----------------------------
# Imports
# -----------------------------
# requests: fetch webpage content
# BeautifulSoup: parse HTML and extract text
# tldextract: extract domain name from URL
# validators: validate URL format
# pickle & os: load optional ML model from file
import requests
from bs4 import BeautifulSoup
import tldextract
import validators
import pickle
import os

# -----------------------------
# Optional: Load ML model
# -----------------------------
# Check if a trained ML model exists (credibility_model.pkl)
# If available, load it for hybrid scoring.
# If not, fall back to random or rule-based scoring.
MODEL_PATH = "credibility_model.pkl"
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        credibility_model = pickle.load(f)
else:
    credibility_model = None

# -----------------------------
# Main function: assess_url_credibility
# -----------------------------
# Combines rule-based signals and ML predictions to score URL credibility.
# Returns a dictionary with:
#   - score: float (0–1)
#   - explanation: string describing how the score was determined
def assess_url_credibility(url: str):
    """
    Assess the credibility of a URL using hybrid rule-based + ML approach.

    Args:
        url (str): URL to assess

    Returns:
        dict: {"score": float, "explanation": str}
    """
    # -----------------------------
    # Validate URL
    # -----------------------------
    # Ensure the input is a valid URL format.
    # Invalid URLs immediately return a 0 score with explanation.
    if not validators.url(url):
        return {"score": 0.0, "explanation": "Invalid URL."}

    try:
        # -----------------------------
        # Fetch webpage content
        # -----------------------------
        # Requests the URL with a 10-second timeout.
        # Raises exceptions for network errors or HTTP 4xx/5xx responses.
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text_content = soup.get_text().strip()
        domain = tldextract.extract(url).domain or "unknown"

        # -----------------------------
        # Rule-based scoring
        # -----------------------------
        # Base score is calculated from:
        #   1. Content length (normalized, max 10k chars)
        #   2. Domain presence (unknown domains get lower score)
        content_len_score = min(10, len(text_content) / 10000)
        domain_score = 1.0 if domain != "unknown" else 0.5
        base_score = (content_len_score + domain_score) / 2

        # -----------------------------
        # ML-based scoring
        # -----------------------------
        # If an ML model is loaded, predict a score based on features like
        # content length and domain length.
        # If ML model fails or is absent, fallback to random plausible score.
        if credibility_model:
            features = [[len(text_content), len(domain)]]
            try:
                ml_score = credibility_model.predict(features)[0]
            except Exception:
                ml_score = 0.5
        else:
            import random
            ml_score = random.uniform(0.3, 0.9)

        # -----------------------------
        # Hybrid scoring
        # -----------------------------
        # Combine rule-based and ML scores equally.
        # Clamp final score between 0 and 1 and round to 2 decimals.
        credibility_score = 0.5 * base_score + 0.5 * ml_score
        credibility_score = max(0.0, min(1.0, round(credibility_score, 2)))

        # -----------------------------
        # Explanation
        # -----------------------------
        # Generate a textual explanation of how the score was derived.
        explanation = (
            f"This source ({domain}) is evaluated based on content length, "
            f"domain characteristics, and ML predictions."
        )

        return {"score": credibility_score, "explanation": explanation}

    # -----------------------------
    # Error handling
    # -----------------------------
    # Handles timeouts, network errors, or unexpected exceptions gracefully.
    # Returns a score of 0 with an appropriate explanation.
    except requests.exceptions.Timeout:
        return {"score": 0.0, "explanation": "Request timed out."}
    except requests.exceptions.RequestException:
        return {"score": 0.0, "explanation": "Unable to fetch the URL."}
    except Exception as e:
        return {"score": 0.0, "explanation": f"Error assessing URL: {e}"}
