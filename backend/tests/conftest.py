"""
Shared pytest fixtures for VoteGuide backend tests.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Patch Gemini client and RAG before importing app
@pytest.fixture(scope="session", autouse=True)
def mock_env():
    """Set required environment variables for tests."""
    os.environ.setdefault("GEMINI_API_KEY", "test-api-key-for-testing")
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")


@pytest.fixture(scope="session")
def mock_gemini():
    """Mock the Gemini client so tests don't hit real API."""
    mock_response = MagicMock()
    mock_response.text = "This is a test response from VoteGuide AI."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("main.client", mock_client), \
         patch("main.initialize_rag"), \
         patch("main.rag_search", return_value=[
             {"content": "Test RAG context about elections.", "metadata": {}, "relevance_score": 0.9}
         ]):
        from main import app
        yield app, mock_client


@pytest.fixture()
def client(mock_gemini):
    """Return a FastAPI TestClient with mocked dependencies."""
    app, _ = mock_gemini
    return TestClient(app)


@pytest.fixture()
def mock_client_obj(mock_gemini):
    """Return the mocked Gemini client for assertion purposes."""
    _, mock_client = mock_gemini
    return mock_client
