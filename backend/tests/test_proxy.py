"""
Tests for the Google Cloud API proxy endpoints:
  POST /api/translate
  POST /api/stt
  POST /api/tts

These run against the FastAPI test client and mock httpx.AsyncClient
so no real Google API key is needed.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.text = str(json_data)
    mock.raise_for_status = MagicMock()
    return mock


def _make_mock_async_client(response):
    """Create a mock httpx.AsyncClient context manager."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm, mock_client


# ── /api/translate ─────────────────────────────────────────────────────────

class TestTranslateProxy:
    def test_translate_without_key_returns_500(self, client: TestClient):
        """When translation API key is missing, endpoint returns 500."""
        import main
        orig_translate = main.GOOGLE_TRANSLATE_API_KEY
        orig_cloud = main.GOOGLE_CLOUD_API_KEY
        try:
            main.GOOGLE_TRANSLATE_API_KEY = ""
            main.GOOGLE_CLOUD_API_KEY = ""
            resp = client.post(
                "/api/translate",
                json={"q": ["Hello"], "target": "hi", "source": "en"},
            )
            assert resp.status_code == 500
            assert "not configured" in resp.json()["detail"].lower()
        finally:
            main.GOOGLE_TRANSLATE_API_KEY = orig_translate
            main.GOOGLE_CLOUD_API_KEY = orig_cloud

    def test_translate_invalid_body_returns_422(self, client: TestClient):
        """Missing required fields triggers 422 validation error."""
        resp = client.post("/api/translate", json={})
        assert resp.status_code == 422

    def test_translate_missing_target_returns_422(self, client: TestClient):
        """Missing 'target' field triggers 422 validation error."""
        resp = client.post("/api/translate", json={"q": ["Hello"], "source": "en"})
        assert resp.status_code == 422

    def test_translate_success(self, client: TestClient):
        """Successful translation returns data from Google API."""
        mock_resp = _make_mock_response(
            {"data": {"translations": [{"translatedText": "नमस्ते"}]}}
        )
        mock_cm, mock_post_client = _make_mock_async_client(mock_resp)

        import main
        with patch.object(main, "GOOGLE_TRANSLATE_API_KEY", "fake-key"), \
             patch("httpx.AsyncClient", return_value=mock_cm):
            resp = client.post(
                "/api/translate",
                json={"q": ["Hello"], "target": "hi", "source": "en"},
            )
        assert resp.status_code == 200


# ── /api/stt ───────────────────────────────────────────────────────────────

class TestSTTProxy:
    def test_stt_without_key_returns_500(self, client: TestClient):
        """When GOOGLE_CLOUD_API_KEY is missing, endpoint returns 500."""
        import main
        original = main.GOOGLE_CLOUD_API_KEY
        try:
            main.GOOGLE_CLOUD_API_KEY = ""
            resp = client.post(
                "/api/stt",
                json={
                    "audio_base64": "dGVzdA==",
                    "language_code": "en-US",
                    "sample_rate": 48000,
                    "encoding": "WEBM_OPUS",
                },
            )
            assert resp.status_code == 500
        finally:
            main.GOOGLE_CLOUD_API_KEY = original

    def test_stt_invalid_body_returns_422(self, client: TestClient):
        """Missing required fields triggers 422."""
        resp = client.post("/api/stt", json={})
        assert resp.status_code == 422

    def test_stt_missing_audio_base64_returns_422(self, client: TestClient):
        """Missing audio_base64 triggers 422."""
        resp = client.post(
            "/api/stt",
            json={"language_code": "en-US"},
        )
        assert resp.status_code == 422

    def test_stt_success(self, client: TestClient):
        """Successful STT returns transcript from Google API."""
        mock_resp = _make_mock_response(
            {"results": [{"alternatives": [{"transcript": "hello world"}]}]}
        )
        mock_cm, _ = _make_mock_async_client(mock_resp)

        import main
        with patch.object(main, "GOOGLE_CLOUD_API_KEY", "fake-key"), \
             patch("httpx.AsyncClient", return_value=mock_cm):
            resp = client.post(
                "/api/stt",
                json={
                    "audio_base64": "dGVzdA==",
                    "language_code": "en-US",
                    "sample_rate": 48000,
                    "encoding": "WEBM_OPUS",
                },
            )
        assert resp.status_code == 200


# ── /api/tts ───────────────────────────────────────────────────────────────

class TestTTSProxy:
    def test_tts_without_key_returns_500(self, client: TestClient):
        """When GOOGLE_CLOUD_API_KEY is missing, endpoint returns 500."""
        import main
        original = main.GOOGLE_CLOUD_API_KEY
        try:
            main.GOOGLE_CLOUD_API_KEY = ""
            resp = client.post(
                "/api/tts",
                json={"text": "Hello", "language_code": "en-US"},
            )
            assert resp.status_code == 500
        finally:
            main.GOOGLE_CLOUD_API_KEY = original

    def test_tts_invalid_body_returns_422(self, client: TestClient):
        """Missing required fields triggers 422."""
        resp = client.post("/api/tts", json={})
        assert resp.status_code == 422

    def test_tts_missing_text_returns_422(self, client: TestClient):
        """Missing text field triggers 422."""
        resp = client.post("/api/tts", json={"language_code": "en-US"})
        assert resp.status_code == 422

    def test_tts_success(self, client: TestClient):
        """Successful TTS returns base64 audio from Google API."""
        mock_resp = _make_mock_response(
            {"audioContent": "base64encodedaudio=="}
        )
        mock_cm, _ = _make_mock_async_client(mock_resp)

        import main
        with patch.object(main, "GOOGLE_CLOUD_API_KEY", "fake-key"), \
             patch("httpx.AsyncClient", return_value=mock_cm):
            resp = client.post(
                "/api/tts",
                json={"text": "Hello, world!", "language_code": "en-US"},
            )
        assert resp.status_code == 200
