"""
Intent classification and country detection for VoteGuide.

The classifier uses keyword scoring to route user queries
to the appropriate tool/handler in the agent pipeline.
"""

import re
import logging

logger = logging.getLogger("voteguide.intent")


# ── Intent Keywords ───────────────────────────────────────────────────────────

INTENT_KEYWORDS: dict[str, list[str]] = {
    "timeline": [
        "timeline", "when", "date", "schedule", "deadline",
        "calendar", "upcoming", "phases", "next election",
    ],
    "eligibility": [
        "eligible", "eligibility", "can i vote", "am i eligible",
        "qualify", "requirements", "age limit", "who can vote",
        "minimum age", "voter qualification",
    ],
    "registration": [
        "register", "registration", "sign up", "enroll",
        "how to register", "voter id", "form 6", "voter card",
        "epic", "voter list",
    ],
    "process": [
        "how to vote", "voting process", "steps to vote",
        "procedure", "how does voting work", "polling",
        "ballot", "evm", "booth", "casting vote",
    ],
    "explanation": [
        "what is", "explain", "define", "meaning of",
        "tell me about", "describe", "difference between",
    ],
}

# ── Country Keywords ──────────────────────────────────────────────────────────

COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "india": [
        "india", "indian", "bharat", "lok sabha", "rajya sabha",
        "eci", "evm", "vvpat", "nota", "nri", "assembly election",
    ],
    "usa": [
        "usa", "us", "america", "american", "electoral college",
        "congress", "senate", "midterm", "democrat", "republican",
        "primary", "caucus", "swing state",
    ],
    "uk": [
        "uk", "britain", "british", "parliament", "mp",
        "commons", "house of lords", "england", "scotland",
        "wales", "northern ireland", "devolved", "holyrood",
        "senedd", "westminster",
    ],
}


def classify_intent(message: str) -> str:
    """Classify user intent based on keyword scoring.

    Returns one of: 'timeline', 'eligibility', 'registration',
    'process', 'explanation', or 'general' (fallback).
    """
    msg_lower = message.lower()
    scores: dict[str, int] = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in msg_lower)
        if score > 0:
            scores[intent] = score

    if scores:
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        logger.debug(f"Intent scores: {scores} → selected '{best}'")
        return best

    return "general"


def detect_country(message: str, user_context: dict | None = None) -> str | None:
    """Detect country from message text or user context.

    Priority: user_context.country > keyword detection in message.
    Returns lowercase country key ('india', 'usa', 'uk') or None.
    """
    if user_context and user_context.get("country"):
        return user_context["country"]

    msg_lower = message.lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return country

    return None
