"""
Unit tests for election_data module:
  - check_eligibility()
  - get_country_data()
  - get_all_countries()
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from election_data import (
    check_eligibility,
    get_country_data,
    get_all_countries,
    ELECTION_DATA,
    FAQ_DATA,
    SIMPLE_EXPLANATIONS,
)


# ── get_country_data ──────────────────────────────────────────────────────────

class TestGetCountryData:
    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_direct_keys_work(self, key):
        data = get_country_data(key)
        assert data is not None
        assert "country" in data

    @pytest.mark.parametrize("alias,expected_key", [
        ("us", "usa"),
        ("United States", "usa"),
        ("america", "usa"),
        ("united states of america", "usa"),
        ("britain", "uk"),
        ("united kingdom", "uk"),
        ("england", "uk"),
        ("great britain", "uk"),
        ("bharat", "india"),
    ])
    def test_aliases(self, alias, expected_key):
        data = get_country_data(alias)
        assert data is not None
        assert data == ELECTION_DATA[expected_key]

    def test_unknown_country_returns_none(self):
        assert get_country_data("atlantis") is None

    def test_case_insensitive(self):
        assert get_country_data("INDIA") == get_country_data("india")

    def test_strips_whitespace(self):
        assert get_country_data("  india  ") == get_country_data("india")


# ── get_all_countries ─────────────────────────────────────────────────────────

class TestGetAllCountries:
    def test_returns_list(self):
        result = get_all_countries()
        assert isinstance(result, list)

    def test_contains_all_three(self):
        result = get_all_countries()
        assert "india" in result
        assert "usa" in result
        assert "uk" in result

    def test_no_duplicates(self):
        result = get_all_countries()
        assert len(result) == len(set(result))


# ── check_eligibility ─────────────────────────────────────────────────────────

class TestCheckEligibility:
    # Happy path
    @pytest.mark.parametrize("country", ["india", "usa", "uk"])
    def test_eligible_adult_citizen(self, country):
        result = check_eligibility(country, 25, True, True)
        assert result["eligible"] is True
        assert "next_steps" in result
        assert len(result["next_steps"]) > 0

    # Boundary tests
    def test_exactly_voting_age_is_eligible(self):
        result = check_eligibility("india", 18, True, True)
        assert result["eligible"] is True

    def test_one_below_voting_age_is_ineligible(self):
        result = check_eligibility("india", 17, True, True)
        assert result["eligible"] is False
        assert "18" in result["reason"]

    def test_zero_age_is_ineligible(self):
        result = check_eligibility("india", 0, True, True)
        assert result["eligible"] is False

    def test_usa_exactly_18(self):
        result = check_eligibility("usa", 18, True, True)
        assert result["eligible"] is True

    def test_uk_exactly_18(self):
        result = check_eligibility("uk", 18, True, True)
        assert result["eligible"] is True

    # Non-citizen
    def test_non_citizen_ineligible(self):
        result = check_eligibility("india", 22, False, True)
        assert result["eligible"] is False
        assert "citizen" in result["reason"].lower()

    # Non-resident
    def test_non_resident_ineligible(self):
        result = check_eligibility("usa", 22, True, False)
        assert result["eligible"] is False
        assert "resident" in result["reason"].lower()

    # Multiple failures
    def test_multiple_issues_combined(self):
        result = check_eligibility("uk", 15, False, False)
        assert result["eligible"] is False
        # Should report multiple issues
        assert "|" in result["reason"] or len(result["next_steps"]) > 1

    # Unknown country
    def test_unknown_country(self):
        result = check_eligibility("narnia", 22, True, True)
        assert result["eligible"] is False
        assert "not found" in result["reason"].lower() or "narnia" in result["reason"].lower()

    def test_unknown_country_has_no_next_steps(self):
        result = check_eligibility("narnia", 22, True, True)
        assert result["next_steps"] == []

    # Result structure
    def test_result_always_has_three_keys(self):
        for country in ["india", "usa", "uk"]:
            result = check_eligibility(country, 22, True, True)
            assert "eligible" in result
            assert "reason" in result
            assert "next_steps" in result

    def test_eligible_reason_is_positive(self):
        result = check_eligibility("india", 25, True, True)
        assert "eligible" in result["reason"].lower() or "meet" in result["reason"].lower()

    def test_ineligible_next_steps_not_empty(self):
        result = check_eligibility("india", 15, True, True)
        assert len(result["next_steps"]) > 0

    def test_aliases_work_in_eligibility(self):
        india_direct = check_eligibility("india", 22, True, True)
        india_alias = check_eligibility("bharat", 22, True, True)
        assert india_direct["eligible"] == india_alias["eligible"]


# ── ELECTION_DATA structure ───────────────────────────────────────────────────

class TestElectionDataStructure:
    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_required_top_level_keys(self, key):
        data = ELECTION_DATA[key]
        for field in ("country", "voting_age", "election_commission", "website", "registration", "voting_process"):
            assert field in data, f"Missing '{field}' in {key}"

    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_voting_age_is_18(self, key):
        assert ELECTION_DATA[key]["voting_age"] == 18

    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_registration_has_steps(self, key):
        reg = ELECTION_DATA[key]["registration"]
        assert "steps" in reg
        assert len(reg["steps"]) > 0

    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_voting_process_is_nonempty(self, key):
        assert len(ELECTION_DATA[key]["voting_process"]) > 0

    @pytest.mark.parametrize("key", ["india", "usa", "uk"])
    def test_election_types_nonempty(self, key):
        assert len(ELECTION_DATA[key]["election_types"]) > 0

    def test_faq_data_nonempty(self):
        assert len(FAQ_DATA) > 0

    def test_faq_entries_have_required_fields(self):
        for faq in FAQ_DATA:
            assert "question" in faq
            assert "answer" in faq
            assert "country" in faq

    def test_simple_explanations_has_voting_key(self):
        assert "voting" in SIMPLE_EXPLANATIONS

    def test_india_has_important_contacts(self):
        assert "important_contacts" in ELECTION_DATA["india"]

    def test_usa_has_electoral_college(self):
        assert "electoral_college" in ELECTION_DATA["usa"]
        ec = ELECTION_DATA["usa"]["electoral_college"]
        assert ec["total_votes"] == 538
        assert ec["to_win"] == 270


# ── RAG module ────────────────────────────────────────────────────────────────

class TestRAGModule:
    def test_rag_initialize_and_search(self):
        from rag import initialize_rag, search
        initialize_rag()
        results = search("how to register to vote in India", n_results=3, country="india")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_rag_search_returns_content_key(self):
        from rag import initialize_rag, search
        initialize_rag()
        results = search("electoral college", n_results=2)
        for r in results:
            assert "content" in r
            assert "relevance_score" in r

    def test_rag_search_with_country_filter(self):
        from rag import initialize_rag, search
        initialize_rag()
        results = search("voting process", n_results=3, country="usa")
        assert isinstance(results, list)

    def test_rag_search_no_filter(self):
        from rag import initialize_rag, search
        initialize_rag()
        results = search("what is EVM", n_results=3)
        assert len(results) > 0

    def test_rag_relevance_score_between_0_and_1(self):
        from rag import initialize_rag, search
        initialize_rag()
        results = search("voter registration India", n_results=3, country="india")
        for r in results:
            assert 0.0 <= r["relevance_score"] <= 1.0
