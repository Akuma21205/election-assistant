"""
Integration tests for VoteGuide API endpoints.

Tests all public endpoints:
  - GET /
  - GET /health
  - POST /chat
  - POST /eligibility
  - GET /timeline/{country}
  - GET /countries
  - GET /registration/{country}
  - POST /translate (security proxy)
"""
import pytest
from fastapi.testclient import TestClient


# ── Root & Health ─────────────────────────────────────────────────────────────

class TestHealthEndpoints:
    def test_root_returns_ok(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "VoteGuide" in data["message"]
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0

    def test_health_returns_healthy(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


# ── Countries Endpoint ────────────────────────────────────────────────────────

class TestCountriesEndpoint:
    def test_countries_returns_list(self, client: TestClient):
        resp = client.get("/countries")
        assert resp.status_code == 200
        data = resp.json()
        assert "countries" in data
        assert isinstance(data["countries"], list)

    def test_countries_includes_big_three(self, client: TestClient):
        resp = client.get("/countries")
        keys = [c["key"] for c in resp.json()["countries"]]
        assert "india" in keys
        assert "usa" in keys
        assert "uk" in keys

    def test_countries_have_required_fields(self, client: TestClient):
        resp = client.get("/countries")
        for country in resp.json()["countries"]:
            assert "key" in country
            assert "name" in country
            assert "voting_age" in country
            assert "election_commission" in country
            assert "website" in country

    def test_countries_voting_age_is_18(self, client: TestClient):
        resp = client.get("/countries")
        for country in resp.json()["countries"]:
            assert country["voting_age"] == 18


# ── Timeline Endpoint ─────────────────────────────────────────────────────────

class TestTimelineEndpoint:
    @pytest.mark.parametrize("country", ["india", "usa", "uk"])
    def test_timeline_for_supported_countries(self, client: TestClient, country: str):
        resp = client.get(f"/timeline/{country}")
        assert resp.status_code == 200
        data = resp.json()
        assert "country" in data
        assert "timeline" in data
        assert isinstance(data["timeline"], dict)

    def test_timeline_india_has_2024_data(self, client: TestClient):
        resp = client.get("/timeline/india")
        assert resp.status_code == 200
        data = resp.json()
        assert "2024" in data["timeline"]

    def test_timeline_usa_has_election_types(self, client: TestClient):
        resp = client.get("/timeline/usa")
        data = resp.json()
        assert "election_types" in data
        assert len(data["election_types"]) > 0

    def test_timeline_unknown_country_returns_404(self, client: TestClient):
        resp = client.get("/timeline/atlantis")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @pytest.mark.parametrize("alias", ["United States", "Britain", "Bharat"])
    def test_timeline_country_aliases(self, client: TestClient, alias: str):
        resp = client.get(f"/timeline/{alias}")
        assert resp.status_code == 200

    def test_timeline_case_insensitive(self, client: TestClient):
        resp = client.get("/timeline/INDIA")
        assert resp.status_code == 200


# ── Registration Endpoint ─────────────────────────────────────────────────────

class TestRegistrationEndpoint:
    @pytest.mark.parametrize("country", ["india", "usa", "uk"])
    def test_registration_for_supported_countries(self, client: TestClient, country: str):
        resp = client.get(f"/registration/{country}")
        assert resp.status_code == 200
        data = resp.json()
        assert "country" in data
        assert "registration" in data

    def test_registration_india_has_steps(self, client: TestClient):
        resp = client.get("/registration/india")
        reg = resp.json()["registration"]
        assert "steps" in reg
        assert len(reg["steps"]) > 0

    def test_registration_india_has_portal(self, client: TestClient):
        resp = client.get("/registration/india")
        reg = resp.json()["registration"]
        assert "online_portal" in reg
        assert reg["online_portal"].startswith("http")

    def test_registration_unknown_country_returns_404(self, client: TestClient):
        resp = client.get("/registration/narnia")
        assert resp.status_code == 404


# ── Eligibility Endpoint ──────────────────────────────────────────────────────

class TestEligibilityEndpoint:
    def test_eligible_adult_citizen(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 25,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert "next_steps" in data
        assert len(data["next_steps"]) > 0

    def test_underage_is_ineligible(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 16,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False
        assert "18" in data["reason"]

    def test_non_citizen_is_ineligible(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "usa",
            "age": 30,
            "is_citizen": False,
            "is_resident": True,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is False

    def test_non_resident_is_ineligible(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "uk",
            "age": 20,
            "is_citizen": True,
            "is_resident": False,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is False

    def test_multiple_ineligibility_reasons(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 15,
            "is_citizen": False,
            "is_resident": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False
        # Multiple issues should appear
        assert "|" in data["reason"] or len(data["next_steps"]) > 1

    def test_unknown_country_eligibility(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "wakanda",
            "age": 22,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False

    @pytest.mark.parametrize("country", ["india", "usa", "uk"])
    def test_eligibility_all_countries(self, client: TestClient, country: str):
        resp = client.post("/eligibility", json={
            "country": country,
            "age": 22,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is True

    def test_eligibility_missing_country_returns_422(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "age": 22,
            "is_citizen": True,
        })
        assert resp.status_code == 422

    def test_eligibility_missing_age_returns_422(self, client: TestClient):
        resp = client.post("/eligibility", json={
            "country": "india",
            "is_citizen": True,
        })
        assert resp.status_code == 422

    def test_eligibility_defaults_applied(self, client: TestClient):
        """is_citizen and is_resident default to True."""
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 22,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is True

    def test_exact_voting_age_is_eligible(self, client: TestClient):
        """Boundary: exactly 18 → eligible."""
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 18,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is True

    def test_one_year_below_voting_age_is_ineligible(self, client: TestClient):
        """Boundary: exactly 17 → not eligible."""
        resp = client.post("/eligibility", json={
            "country": "india",
            "age": 17,
            "is_citizen": True,
            "is_resident": True,
        })
        assert resp.status_code == 200
        assert resp.json()["eligible"] is False


# ── Chat Endpoint ─────────────────────────────────────────────────────────────

class TestChatEndpoint:
    def test_basic_chat_returns_response(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "How do I register to vote in India?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    def test_chat_returns_metadata(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "When is the next election?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "intent" in data
        assert "model_used" in data
        assert "rag_results_count" in data

    def test_chat_with_history(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "Tell me more about that.",
            "history": [
                {"role": "user", "content": "What is the Electoral College?"},
                {"role": "assistant", "content": "The Electoral College is a US election system..."},
            ],
        })
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_with_language(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "How do I vote?",
            "language": "hindi",
        })
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_simplified_mode(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "What is voting?",
            "mode": "simplified",
        })
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_with_user_context(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "Am I eligible to vote?",
            "user_context": {
                "country": "india",
                "age": 22,
                "is_first_time_voter": True,
            },
        })
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_default_language_is_english(self, client: TestClient):
        resp = client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 200

    def test_chat_empty_message_returns_422(self, client: TestClient):
        resp = client.post("/chat", json={})
        assert resp.status_code == 422

    def test_chat_with_all_supported_languages(self, client: TestClient):
        languages = ["hindi", "spanish", "french", "tamil", "telugu", "english"]
        for lang in languages:
            resp = client.post("/chat", json={
                "message": "What is voting?",
                "language": lang,
            })
            assert resp.status_code == 200, f"Failed for language: {lang}"

    def test_chat_intent_detected_for_registration(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "How do I register to vote?",
        })
        assert resp.status_code == 200
        assert resp.json()["intent"] == "registration"

    def test_chat_intent_detected_for_eligibility(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "Am I eligible to vote?",
        })
        assert resp.status_code == 200
        assert resp.json()["intent"] == "eligibility"

    def test_chat_intent_detected_for_timeline(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "When is the election date?",
        })
        assert resp.status_code == 200
        assert resp.json()["intent"] == "timeline"

    def test_chat_country_detected_for_india(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "How does India's Lok Sabha election work?",
        })
        assert resp.status_code == 200
        assert resp.json()["country_detected"] == "india"

    def test_chat_country_detected_for_usa(self, client: TestClient):
        resp = client.post("/chat", json={
            "message": "How does the US Electoral College work?",
        })
        assert resp.status_code == 200
        assert resp.json()["country_detected"] == "usa"

    def test_chat_model_used_is_in_fallback_chain(self, client: TestClient):
        resp = client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        model = resp.json()["model_used"]
        valid_models = [
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        assert model in valid_models


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class TestRateLimiting:
    def test_rate_limit_allows_normal_requests(self, client: TestClient):
        """First few requests should always succeed after clearing store."""
        import main
        main._rate_store.clear()  # reset shared state between test classes
        for _ in range(3):
            resp = client.post("/chat", json={"message": "Hello"})
            assert resp.status_code == 200

