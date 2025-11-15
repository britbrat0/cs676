import pytest
from unittest.mock import patch

@pytest.fixture
def mock_openai_success():
    with patch("app.client.responses.create") as mock:
        mock.return_value = {
            "responses": [{
                "output_text": "TestPersona: - Response: This is great"
            }]
        }
        yield mock

@pytest.fixture
def mock_openai_fail():
    with patch("app.client.responses.create", side_effect=Exception("API error")):
        yield
