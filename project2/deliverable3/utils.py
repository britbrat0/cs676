import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("persona_app")

# ---------------------------
# Retry Decorator for API Calls
# ---------------------------
def retry_on_failure():
    """Common retry configuration for unstable network/API calls."""
    return retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )

# ---------------------------
# Monitoring Helper
# ---------------------------
def log_event(event: str, user: str = "anonymous", level: str = "info"):
    """Log app events for monitoring and debugging."""
    message = f"[{user}] {event}"
    getattr(logger, level.lower())(message)

# ---------------------------
# Error Handling Utility
# ---------------------------
def handle_error(error: Exception, context: str = "general"):
    """Unified error handler for Streamlit app."""
    timestamp = datetime.utcnow().isoformat()
    logger.error(f"[{timestamp}] Context: {context} | Error: {error}")
    return f"⚠️ An error occurred in {context}: {error}"

# ---------------------------
# Example Usage (Optional)
# ---------------------------
if __name__ == "__main__":
    try:
        log_event("Starting utils test", "system")
        raise ValueError("Test error for demonstration")
    except Exception as e:
        handle_error(e, "utils_test")
