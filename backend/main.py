"""
VoteGuide API — Non-partisan AI Election Assistant.

This is the FastAPI application entry point. Business logic is delegated to:
  - agent.py     → Agent orchestration (intent → tools → RAG → LLM)
  - intent.py    → Intent classification and country detection
  - tools.py     → Structured election data tools
  - models.py    → Pydantic request/response schemas
  - rag.py       → ChromaDB vector search
  - middleware.py → Security, rate limiting, request tracing
"""

import os
import json
import time
import logging
import asyncio
import httpx
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from google import genai
from google.genai import types

# Local modules
from models import (
    ChatRequest, ChatResponse,
    EligibilityRequest, EligibilityResponse,
    HealthResponse, CountriesResponse, CountryInfo,
    TranslateProxyRequest, STTProxyRequest, TTSProxyRequest,
)
from agent import run_agent, MODELS, SYSTEM_PROMPT, SIMPLIFIED_SYSTEM_PROMPT, LANGUAGE_NAMES, MAX_HISTORY_TURNS
from middleware import (
    RequestTraceMiddleware, check_rate_limit, sanitize_chat_input,
)
from intent import classify_intent, detect_country
from tools import execute_tools
from rag import search as rag_search
from election_data import (
    check_eligibility, get_country_data, get_all_countries, ELECTION_DATA
)
from rag import initialize_rag

# ── Configuration ─────────────────────────────────────────────────────────────

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY", GEMINI_API_KEY)

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("voteguide.api")

# ── Startup / Shutdown ────────────────────────────────────────────────────────

startup_time: float = 0
rag_doc_count: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG and Gemini client on startup."""
    global startup_time, rag_doc_count
    startup_time = time.time()

    logger.info("🔧 Initializing RAG knowledge base...")
    rag_doc_count = initialize_rag()
    logger.info(f"✅ RAG ready — {rag_doc_count} documents indexed")

    logger.info("🤖 Gemini client ready")
    yield
    logger.info("👋 VoteGuide shutting down")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="VoteGuide API",
    description="Non-partisan AI Election Assistant for India, USA & UK",
    version="2.1.0",
    lifespan=lifespan,
)

# Middleware (order matters — outermost first)
app.add_middleware(RequestTraceMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini client — shared across requests
client = genai.Client(api_key=GEMINI_API_KEY)


# ── Route Helpers ─────────────────────────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Root Endpoint ────────────────────────────────────────────────────────────

@app.get("/", summary="API root — status and feature list")
async def root():
    """Return API status and list of available features."""
    return {
        "status": "ok",
        "message": "VoteGuide — Non-partisan AI Election Assistant",
        "version": "2.1.0",
        "features": [
            "Multi-turn AI chat with 3-model fallback",
            "RAG-grounded answers from verified election data",
            "Voting eligibility checker (India, USA, UK)",
            "Election timeline & registration guides",
            "Server-side streaming (SSE) for real-time responses",
            "9-language support with Google Cloud Translation",
            "Voice input (STT) & output (TTS) via Google Cloud",
            "Rate limiting & prompt injection defense",
        ],
    }


# ── Core Chat Endpoint ───────────────────────────────────────────────────────

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with VoteGuide AI",
    responses={
        429: {"description": "Rate limit exceeded"},
        400: {"description": "Input validation or safety filter error"},
    },
)
async def chat(payload: ChatRequest, request: Request):
    """Process a user chat message through the 3-layer agent pipeline.

    1. **Intent Layer** — Keyword-based classification
    2. **Tool Layer** — Structured data retrieval
    3. **RAG + LLM** — Grounded AI generation with model fallback
    """
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")

    # Input sanitization
    try:
        sanitized_message = sanitize_chat_input(payload.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = run_agent(
        message=sanitized_message,
        history=payload.history,
        language=payload.language,
        mode=payload.mode,
        user_context=payload.user_context,
        client=client,
    )

    return result


# ── SSE Streaming Chat Endpoint ──────────────────────────────────────────────

@app.post(
    "/chat/stream",
    summary="Chat with VoteGuide AI (Server-Sent Events streaming)",
    responses={
        429: {"description": "Rate limit exceeded"},
        400: {"description": "Input validation or safety filter error"},
    },
)
async def chat_stream(payload: ChatRequest, request: Request):
    """Stream AI response tokens via Server-Sent Events (SSE).

    Provides real-time token-by-token delivery for a better UX.
    Falls back to non-streaming if the model doesn't support it.
    """
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")

    try:
        sanitized_message = sanitize_chat_input(payload.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Pre-compute pipeline (intent, tools, RAG)
    intent = classify_intent(sanitized_message)
    country = detect_country(sanitized_message, payload.user_context)
    tool_outputs = execute_tools(intent, country, payload.user_context)
    rag_results = rag_search(sanitized_message, n_results=3, country=country)
    rag_context = "\n\n".join([r["content"] for r in rag_results]) if rag_results else ""

    system = SIMPLIFIED_SYSTEM_PROMPT if payload.mode == "simplified" else SYSTEM_PROMPT

    if payload.language and payload.language.lower() != "english":
        lang_name = LANGUAGE_NAMES.get(payload.language.lower(), payload.language.capitalize())
        system += (
            f"\n\nCRITICAL LANGUAGE REQUIREMENT: You MUST respond EXCLUSIVELY in {lang_name}. "
            f"Every single word of your response must be in {lang_name}."
        )

    # Build augmented message
    augmented_message = sanitized_message
    if tool_outputs or rag_context:
        augmented_message = f"""User Question: {sanitized_message}

--- Retrieved Information ---
{chr(10).join(tool_outputs)}

--- Knowledge Base Context ---
{rag_context}
---

Based on the above, provide a comprehensive answer."""

    # Build conversation contents
    truncated_history = payload.history[-MAX_HISTORY_TURNS:]
    contents = []
    for msg in truncated_history:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=augmented_message)]))

    async def event_generator():
        # Send metadata first
        metadata = {
            "type": "metadata",
            "intent": intent,
            "country_detected": country,
            "tools_used": [t[:50] for t in tool_outputs] if tool_outputs else [],
            "rag_results_count": len(rag_results),
        }
        yield f"data: {json.dumps(metadata)}\n\n"

        model_used = "fallback-tool-data"

        for model_id in MODELS:
            try:
                logger.info(f"[stream] Trying model: {model_id}")
                stream = client.models.generate_content_stream(
                    model=model_id,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=0.7,
                        max_output_tokens=2048,
                    ),
                )

                model_used = model_id
                for chunk in stream:
                    if chunk.text:
                        token_event = {"type": "token", "content": chunk.text}
                        yield f"data: {json.dumps(token_event)}\n\n"
                        await asyncio.sleep(0)  # yield control

                # Done event
                done_event = {"type": "done", "model_used": model_used}
                yield f"data: {json.dumps(done_event)}\n\n"
                return

            except Exception as e:
                err_str = str(e)
                logger.warning(f"[stream] Model {model_id} failed: {err_str[:120]}")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str:
                    await asyncio.sleep(0.5)
                    continue
                error_event = {"type": "error", "message": f"AI error: {err_str[:200]}"}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

        # Fallback if all models exhausted
        fallback_text = "\n\n".join(tool_outputs) if tool_outputs else (
            "I'm experiencing high demand. Please try again in ~60 seconds."
        )
        fallback_event = {"type": "token", "content": fallback_text}
        yield f"data: {json.dumps(fallback_event)}\n\n"
        done_event = {"type": "done", "model_used": "fallback-tool-data"}
        yield f"data: {json.dumps(done_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Eligibility Endpoint ─────────────────────────────────────────────────────

@app.post(
    "/eligibility",
    response_model=EligibilityResponse,
    summary="Check voting eligibility",
)
async def eligibility(payload: EligibilityRequest, request: Request):
    """Check voting eligibility based on country, age, citizenship, and residency."""
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    result = check_eligibility(
        payload.country, payload.age, payload.is_citizen, payload.is_resident
    )
    return result


# ── Information Endpoints ─────────────────────────────────────────────────────

@app.get(
    "/countries",
    response_model=CountriesResponse,
    summary="List supported countries",
)
async def list_countries():
    """Return metadata for all supported countries."""
    countries = []
    for key in get_all_countries():
        data = ELECTION_DATA[key]
        countries.append(CountryInfo(
            key=key,
            name=data["country"],
            voting_age=data["voting_age"],
            election_commission=data["election_commission"],
            website=data["website"],
        ))
    return CountriesResponse(countries=countries)


@app.get(
    "/timeline/{country}",
    summary="Get election timeline for a country",
    responses={404: {"description": "Country not found"}},
)
async def get_timeline(country: str):
    """Return election timeline data for a supported country.

    Accepts country names, aliases, and codes (case-insensitive).
    """
    data = get_country_data(country)
    if not data:
        raise HTTPException(status_code=404, detail=f"Timeline not found for '{country}'.")

    timelines = data.get("timelines", {})
    election_types = data.get("election_types", [])

    return {
        "country": data["country"],
        "timeline": timelines,
        "election_types": election_types,
        "voting_age": data.get("voting_age", 18),
        "election_commission": data.get("election_commission", ""),
        "website": data.get("website", ""),
    }


@app.get(
    "/registration/{country}",
    summary="Get voter registration guide for a country",
    responses={404: {"description": "Country not found"}},
)
async def get_registration(country: str):
    """Return voter registration steps, required documents, and portal links.

    Accepts country names, aliases, and codes (case-insensitive).
    """
    data = get_country_data(country)
    if not data:
        raise HTTPException(status_code=404, detail=f"Registration data not found for '{country}'.")

    registration = data.get("registration", {})

    return {
        "country": data["country"],
        "registration": registration,
        "voting_age": data.get("voting_age", 18),
        "website": data.get("website", ""),
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
)
async def health():
    """Deep health check including RAG status and uptime."""
    uptime = time.time() - startup_time if startup_time else 0
    return HealthResponse(
        status="healthy",
        version="2.1.0",
        rag_documents=rag_doc_count,
        uptime_seconds=round(uptime, 1),
    )


# ── Google Cloud API Proxies ─────────────────────────────────────────────────

@app.post(
    "/api/translate",
    summary="Translate text via Google Cloud Translation API (proxied)",
)
async def proxy_translate(body: TranslateProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Translation API.

    Keeps the API key secure on the backend. Accepts multiple strings
    for batch translation.
    """
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    api_key = GOOGLE_TRANSLATE_API_KEY or GOOGLE_CLOUD_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="Translation API key not configured.")

    url = f"https://translation.googleapis.com/language/translate/v2?key={api_key}"

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        resp = await http_client.post(url, json={
            "q": body.q,
            "target": body.target,
            "source": body.source,
            "format": "text",
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.post(
    "/api/stt",
    summary="Speech-to-Text via Google Cloud (proxied)",
)
async def proxy_stt(body: STTProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Speech-to-Text API."""
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    api_key = GOOGLE_CLOUD_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="Speech API key not configured.")

    url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resp = await http_client.post(url, json={
            "config": {
                "encoding": body.encoding,
                "sampleRateHertz": body.sample_rate,
                "languageCode": body.language_code,
                "model": "latest_short",
                "enableAutomaticPunctuation": True,
            },
            "audio": {"content": body.audio_base64},
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.post(
    "/api/tts",
    summary="Text-to-Speech via Google Cloud (proxied)",
)
async def proxy_tts(body: TTSProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Text-to-Speech API."""
    client_ip = _get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    api_key = GOOGLE_CLOUD_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="TTS API key not configured.")

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

    voice_cfg: dict = {"languageCode": body.language_code}
    if body.voice_name:
        voice_cfg["name"] = body.voice_name

    async with httpx.AsyncClient(timeout=15.0) as http_client:
        resp = await http_client.post(url, json={
            "input": {"text": body.text[:4800]},
            "voice": voice_cfg,
            "audioConfig": {"audioEncoding": "MP3"},
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)