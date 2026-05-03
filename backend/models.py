"""
Pydantic request/response models and TypedDicts for VoteGuide API.

Defines all request/response schemas used by FastAPI for:
- Automatic request validation
- OpenAPI documentation generation
- Type-safe data exchange between frontend and backend
"""

from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict


# ── Request Models ────────────────────────────────────────────────────────────

class Message(BaseModel):
    """A single chat message (user or assistant)."""
    role: str = Field(..., description="Message author: 'user' or 'assistant'")
    content: str = Field(..., description="The text content of the message")


class ChatRequest(BaseModel):
    """Request body for POST /chat and POST /chat/stream."""
    message: str = Field(
        ..., min_length=1, max_length=4000,
        description="The user's question about elections, voting, or civic processes",
    )
    history: List[Message] = Field(
        default=[], description="Previous conversation messages for multi-turn context",
    )
    language: str = Field(
        default="english",
        description="Response language: english, hindi, spanish, french, tamil, telugu, bengali, marathi, kannada",
    )
    mode: str = Field(
        default="standard",
        description="Response complexity: 'standard' for detailed answers, 'simplified' for plain language",
    )
    user_context: Optional[dict] = Field(
        default=None,
        description="Optional user profile: {country, age, is_first_time_voter}",
    )


class EligibilityRequest(BaseModel):
    """Request body for POST /eligibility."""
    country: str = Field(..., description="Country to check eligibility for (india, usa, uk)")
    age: int = Field(..., ge=0, le=150, description="Voter's age in years")
    is_citizen: bool = Field(default=True, description="Whether the person is a citizen")
    is_resident: bool = Field(default=True, description="Whether the person is a resident")


class TimelineRequest(BaseModel):
    """Request body for timeline queries."""
    country: str
    year: str = "2024"


class TranslateProxyRequest(BaseModel):
    """Request body for POST /api/translate (proxied Google Cloud Translation)."""
    q: list[str] = Field(..., description="List of strings to translate")
    target: str = Field(..., description="BCP-47 target language code (e.g. 'hi', 'es')")
    source: str = Field(default="en", description="BCP-47 source language code")


class STTProxyRequest(BaseModel):
    """Request body for POST /api/stt (proxied Google Cloud Speech-to-Text)."""
    audio_base64: str = Field(..., description="Base64-encoded audio bytes")
    language_code: str = Field(..., description="BCP-47 language code (e.g. 'en-US', 'hi-IN')")
    sample_rate: int = Field(default=48000, description="Audio sample rate in Hz")
    encoding: str = Field(default="WEBM_OPUS", description="Audio encoding format")


class TTSProxyRequest(BaseModel):
    """Request body for POST /api/tts (proxied Google Cloud Text-to-Speech)."""
    text: str = Field(..., max_length=5000, description="Text to synthesize into speech")
    language_code: str = Field(..., description="BCP-47 language code (e.g. 'en-US')")
    voice_name: str = Field(default="", description="Wavenet voice name; auto-selected if empty")


# ── Response Models ───────────────────────────────────────────────────────────

class AgentResult(TypedDict):
    """Structured return type for the agent orchestration pipeline."""
    response: str
    model_used: str
    intent: str
    country_detected: Optional[str]
    tools_used: list[str]
    rag_results_count: int


class ChatResponse(BaseModel):
    """Response schema for POST /chat — used in OpenAPI docs."""
    response: str = Field(..., description="AI-generated answer to the user's question")
    model_used: str = Field(..., description="Gemini model that produced the response")
    intent: str = Field(..., description="Detected intent category")
    country_detected: Optional[str] = Field(default=None, description="Detected country from query")
    tools_used: list[str] = Field(default=[], description="Tools invoked during processing")
    rag_results_count: int = Field(default=0, description="Number of RAG documents retrieved")


class EligibilityResponse(BaseModel):
    """Response schema for POST /eligibility."""
    eligible: bool = Field(..., description="Whether the person is eligible to vote")
    reason: str = Field(..., description="Human-readable explanation of the eligibility decision")
    next_steps: list[str] = Field(..., description="Actionable next steps for the user")


class HealthResponse(BaseModel):
    """Response schema for GET /health."""
    status: str = Field(..., description="Service status: 'healthy' or 'degraded'")
    version: str = Field(..., description="API version string")
    rag_documents: int = Field(default=0, description="Number of documents in RAG knowledge base")
    uptime_seconds: float = Field(default=0, description="Server uptime in seconds")


class CountryInfo(BaseModel):
    """Single country entry in /countries response."""
    key: str
    name: str
    voting_age: int
    election_commission: str
    website: str


class CountriesResponse(BaseModel):
    """Response schema for GET /countries."""
    countries: list[CountryInfo]
