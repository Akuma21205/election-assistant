"""
Tests for the Google Cloud API proxy endpoints:
  POST /api/translate
  POST /api/stt
  POST /api/tts

These run against the FastAPI test client and mock the httpx calls
so no real Google API key is needed.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import main
from main import app

client = TestClient(app)


# ── /api/translate ─────────────────────────────────────────────────────────

class TestTranslateProxy:
    def test_translate_without_key_returns_503(self):
        """When GOOGLE_CLOUD_API_KEY env var is missing, endpoint returns 503."""
        original = main.GOOGLE_API_KEY
        try:
            main.GOOGLE_API_KEY = ""
            resp = client.post(
                "/api/translate",
                json={"q": ["Hello"], "target": "hi", "source": "en"},
            )
            assert resp.status_code == 503
            assert "not configured" in resp.json()["detail"].lower()
        finally:
            main.GOOGLE_API_KEY = original

    def test_translate_invalid_body_returns_422(self):
        """Missing required fields triggers 422 validation error."""
        resp = client.post("/api/translate", json={})
        assert resp.status_code == 422

    def test_translate_missing_target_returns_422(self):
        """Missing 'target' field triggers 422 validation error."""
        resp = client.post("/api/translate", json={"q": ["Hello"], "source": "en"})
        assert resp.status_code == 422

    def test_translate_success(self):
        """Successful translation returns data from Google API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"translations": [{"translatedText": "नमस्ते"}]}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", return_value=mock_response) as mock_post:
            resp = client.post(
                "/api/translate",
                json={"q": ["Hello"], "target": "hi", "source": "en"},
            )
        assert resp.status_code == 200
        assert mock_post.called

    def test_translate_upstream_error_returns_502(self):
        """When Google API returns an error, proxy returns 502."""
        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", side_effect=httpx.HTTPStatusError(
                 "error", request=MagicMock(), response=MagicMock(text="Bad Request")
             )):
            resp = client.post(
                "/api/translate",
                json={"q": ["Hello"], "target": "hi", "source": "en"},
            )
        assert resp.status_code == 502


# ── /api/stt ───────────────────────────────────────────────────────────────

class TestSTTProxy:
    def test_stt_without_key_returns_503(self):
        """When GOOGLE_CLOUD_API_KEY is missing, endpoint returns 503."""
        original = main.GOOGLE_API_KEY
        try:
            main.GOOGLE_API_KEY = ""
            resp = client.post(
                "/api/stt",
                json={
                    "audio_base64": "dGVzdA==",
                    "language_code": "en-US",
                    "sample_rate": 48000,
                    "encoding": "WEBM_OPUS",
                },
            )
            assert resp.status_code == 503
        finally:
            main.GOOGLE_API_KEY = original

    def test_stt_invalid_body_returns_422(self):
        """Missing required fields triggers 422."""
        resp = client.post("/api/stt", json={})
        assert resp.status_code == 422

    def test_stt_missing_audio_base64_returns_422(self):
        """Missing audio_base64 triggers 422."""
        resp = client.post(
            "/api/stt",
            json={"language_code": "en-US"},
        )
        assert resp.status_code == 422

    def test_stt_success(self):
        """Successful STT returns transcript from Google API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"alternatives": [{"transcript": "hello world"}]}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", return_value=mock_response):
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

    def test_stt_upstream_error_returns_502(self):
        """When Google STT API fails, proxy returns 502."""
        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", side_effect=httpx.HTTPStatusError(
                 "error", request=MagicMock(), response=MagicMock(text="error")
             )):
            resp = client.post(
                "/api/stt",
                json={
                    "audio_base64": "dGVzdA==",
                    "language_code": "en-US",
                },
            )
        assert resp.status_code == 502


# ── /api/tts ───────────────────────────────────────────────────────────────

class TestTTSProxy:
    def test_tts_without_key_returns_503(self):
        """When GOOGLE_CLOUD_API_KEY is missing, endpoint returns 503."""
        original = main.GOOGLE_API_KEY
        try:
            main.GOOGLE_API_KEY = ""
            resp = client.post(
                "/api/tts",
                json={"text": "Hello", "language_code": "en-US"},
            )
            assert resp.status_code == 503
        finally:
            main.GOOGLE_API_KEY = original

    def test_tts_invalid_body_returns_422(self):
        """Missing required fields triggers 422."""
        resp = client.post("/api/tts", json={})
        assert resp.status_code == 422

    def test_tts_missing_text_returns_422(self):
        """Missing text field triggers 422."""
        resp = client.post("/api/tts", json={"language_code": "en-US"})
        assert resp.status_code == 422

    def test_tts_success(self):
        """Successful TTS returns base64 audio from Google API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"audioContent": "base64encodedaudio=="}
        mock_response.raise_for_status = MagicMock()

        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", return_value=mock_response):
            resp = client.post(
                "/api/tts",
                json={"text": "Hello, world!", "language_code": "en-US"},
            )
        assert resp.status_code == 200
        assert "audioContent" in resp.json()

    def test_tts_selects_wavenet_voice_for_language(self):
        """Proxy auto-selects the correct Wavenet voice per language code."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"audioContent": "base64=="}
        mock_response.raise_for_status = MagicMock()

        captured_body = {}

        def capture_post(url, params, json, timeout):
            captured_body.update(json)
            return mock_response

        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", side_effect=capture_post):
            client.post(
                "/api/tts",
                json={"text": "नमस्ते", "language_code": "hi-IN"},
            )

        assert captured_body.get("voice", {}).get("name") == "hi-IN-Wavenet-B"

    def test_tts_upstream_error_returns_502(self):
        """When Google TTS API fails, proxy returns 502."""
        with patch.object(main, "GOOGLE_API_KEY", "fake-key"), \
             patch("httpx.post", side_effect=httpx.HTTPStatusError(
                 "error", request=MagicMock(), response=MagicMock(text="error")
             )):
            resp = client.post(
                "/api/tts",
                json={"text": "Hello", "language_code": "en-US"},
            )
        assert resp.status_code == 502
