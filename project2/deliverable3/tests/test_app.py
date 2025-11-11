import requests
import time
import json

BASE_URL = "http://localhost"
APP_PORT = 8501
HEALTH_PORT = 8080 # Based on the app code

def test_health_endpoint():
    """FT004: Test the simple HTTP health endpoint."""
    print(f"Testing health endpoint: {BASE_URL}:{HEALTH_PORT}/healthz")
    try:
        response = requests.get(f"{BASE_URL}:{HEALTH_PORT}/healthz")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        assert response.text == "OK", f"Expected 'OK' response, got {response.text}"
        print("✅ Health check passed.")
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to health server on port {HEALTH_PORT}. Is it running?")

def test_metrics_endpoint():
    """FT005: Test that Prometheus metrics are exposed."""
    print(f"Testing metrics endpoint: {BASE_URL}:8000/metrics")
    try:
        response = requests.get(f"{BASE_URL}:8000/metrics")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        assert "app_requests_total" in response.text, "Metrics missing 'app_requests_total'"
        assert "app_response_time_seconds" in response.text, "Metrics missing 'app_response_time_seconds'"
        print("✅ Metrics check passed.")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to metrics server on port 8000. Is it running?")

def run_all_functional_tests():
    print("--- Starting Functional Tests ---")
    test_health_endpoint()
    test_metrics_endpoint()
    # Note: Testing the *Streamlit UI* itself (like the generate feedback button) requires UI automation tools like Playwright/Selenium.
    print("--- Functional Tests Complete ---")

if __name__ == "__main__":
    # Give servers a moment to spin up
    time.sleep(2)
    run_all_functional_tests()
