"""
VoteGuide — AI-Powered Election Assistant Backend

Features:
- LangGraph agent with intent classification & tool routing
- RAG-powered answers using ChromaDB
- Eligibility checker, timeline generator, registration guide
- Multi-language support via Gemini
- Standard & Simplified explanation modes
- Rate limiting & robust error handling
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict
import os
import time
import json
import logging
import httpx
from collections import defaultdict
from google import genai
from google.genai import types
from dotenv import load_dotenv

from election_data import (
    ELECTION_DATA,
    SIMPLE_EXPLANATIONS,
    get_country_data,
    get_all_countries,
    check_eligibility,
)
from rag import initialize_rag, search as rag_search

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voteguide")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

client = genai.Client(api_key=api_key)

# Initialize RAG on startup
initialize_rag()

# Models to try in order (fallback chain)
MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

# ── Rate Limiting ──────────────────────────────────────────────
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 20  # max requests per window per IP
_rate_store: dict[str, list[float]] = defaultdict(list)

# ── Module-level constants ──────────────────────────────────────
LANGUAGE_NAMES: dict[str, str] = {
    "hindi": "Hindi (हिन्दी)",
    "spanish": "Spanish (Español)",
    "french": "French (Français)",
    "tamil": "Tamil (தமிழ்)",
    "telugu": "Telugu (తెలుగు)",
    "bengali": "Bengali (বাংলা)",
    "marathi": "Marathi (मराठी)",
    "kannada": "Kannada (ಕನ್ನಡ)",
}

WAVENET_VOICES: dict[str, str] = {
    "en-US": "en-US-Wavenet-D",
    "en-GB": "en-GB-Wavenet-B",
    "hi-IN": "hi-IN-Wavenet-B",
    "es-ES": "es-ES-Wavenet-B",
    "fr-FR": "fr-FR-Wavenet-B",
    "ta-IN": "ta-IN-Wavenet-B",
    "te-IN": "te-IN-Wavenet-B",
    "bn-IN": "bn-IN-Wavenet-B",
    "mr-IN": "mr-IN-Wavenet-C",
    "kn-IN": "kn-IN-Wavenet-B",
}

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
STT_URL = "https://speech.googleapis.com/v1/speech:recognize"
TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


def check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # Clean old entries
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if t > window_start]
    if len(_rate_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_store[client_ip].append(now)
    return True


# ── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title="VoteGuide — AI Election Assistant API",
    version="2.0.0",
    description="AI-powered, non-partisan election assistant with RAG, agent tools, and multi-language support.",
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.(web\.app|firebaseapp\.com)$",
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── System Prompt ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are VoteGuide — an expert, non-partisan AI Election Assistant.

Your responsibilities:
- Explain election processes clearly and accurately (voting, registration, candidates, electoral systems)
- Break down complex political or civic topics into simple, step-by-step language
- Provide country- or region-specific guidance when asked (you have deep knowledge of India, USA, and UK elections)
- Cite official sources when possible (e.g., election commission websites)
- Stay strictly neutral — never advocate for any political party, candidate, or ideology
- If a question is outside your scope (e.g., personal legal advice), politely redirect
- When RAG context is provided, use it to give accurate, grounded answers
- For eligibility checks, clearly state requirements and next steps
- For timeline queries, present dates in a clear, organized format

Tone: Informative, friendly, and accessible to first-time voters.
Format: Use bullet points and numbered lists when explaining processes. Use bold for key terms.
When presenting timelines, use a structured format with dates clearly labeled.
"""

SIMPLIFIED_SYSTEM_PROMPT = """You are VoteGuide — an AI Election Assistant explaining things in the simplest way possible.

IMPORTANT: Explain everything as if you're talking to a 10-year-old child.
- Use simple words and short sentences
- Use fun analogies and comparisons to everyday things (ice cream, school, games)
- Avoid technical jargon completely
- Use emojis to make it engaging
- Keep explanations brief and cheerful

You are still non-partisan and factual, just very simple in your language.
"""

# ── Pydantic Models ────────────────────────────────────────────

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[Message] = []
    language: str = "english"
    mode: str = "standard"  # "standard" or "simplified"
    user_context: Optional[dict] = None  # {country, age, is_first_time_voter}


class EligibilityRequest(BaseModel):
    country: str
    age: int
    is_citizen: bool = True
    is_resident: bool = True


class TimelineRequest(BaseModel):
    country: str
    year: str = "2024"


# ── TypedDicts for structured return types ────────────────────

class AgentResult(TypedDict):
    response: str
    model_used: str
    intent: str
    country_detected: Optional[str]
    tools_used: list[str]
    rag_results_count: int


# ── Intent Classification ─────────────────────────────────────

INTENT_KEYWORDS: dict[str, list[str]] = {
    "timeline": ["timeline", "when", "date", "schedule", "deadline", "calendar", "upcoming", "phases"],
    "eligibility": ["eligible", "eligibility", "can i vote", "am i eligible", "qualify", "requirements", "age limit", "who can vote"],
    "registration": ["register", "registration", "sign up", "enroll", "how to register", "voter id", "form 6"],
    "process": ["how to vote", "voting process", "steps to vote", "procedure", "how does voting work", "polling", "ballot"],
    "explanation": ["what is", "explain", "define", "meaning of", "tell me about", "describe"],
}


def classify_intent(message: str) -> str:
    """Classify user intent based on keywords."""
    msg_lower = message.lower()
    scores: dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in msg_lower)
        if score > 0:
            scores[intent] = score

    if scores:
        return max(scores, key=scores.get)
    return "general"


def detect_country(message: str, user_context: dict | None = None) -> str | None:
    """Detect country from message or user context."""
    if user_context and user_context.get("country"):
        return user_context["country"]

    msg_lower = message.lower()
    country_keywords: dict[str, list[str]] = {
        "india": ["india", "indian", "bharat", "lok sabha", "eci", "evm", "vvpat", "nota", "nri"],
        "usa": ["usa", "us", "america", "american", "electoral college", "congress", "senate", "midterm", "democrat", "republican"],
        "uk": ["uk", "britain", "british", "parliament", "mp", "commons", "house of lords",
               "england", "scotland", "wales", "northern ireland", "devolved", "holyrood", "senedd"],
    }
    for country, keywords in country_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            return country
    return None


# ── Tool Functions ─────────────────────────────────────────────

def get_timeline_info(country: str, year: str = "2024") -> str:
    """Get election timeline for a country."""
    data = get_country_data(country)
    if not data:
        return f"Timeline data not available for '{country}'. Supported countries: India, USA, UK."

    timelines = data.get("timelines", {})
    result_parts = [f"## 📅 Election Timeline for {data['country']}"]

    # Specific year
    if year in timelines:
        for election_name, dates in timelines[year].items():
            if isinstance(dates, dict):
                result_parts.append(f"\n### {election_name} ({year})")
                for phase, date in dates.items():
                    result_parts.append(f"- **{phase.replace('_', ' ').title()}**: {date}")

    # General timeline
    general = timelines.get("general_timeline", {})
    if general:
        result_parts.append(f"\n### General Election Timeline")
        for phase, info in general.items():
            result_parts.append(f"- **{phase}**: {info}")

    return "\n".join(result_parts)


def get_registration_guide(country: str) -> str:
    """Get voter registration guide for a country."""
    data = get_country_data(country)
    if not data:
        return f"Registration data not available for '{country}'. Supported countries: India, USA, UK."

    reg = data.get("registration", {})
    result_parts = [f"## 📝 Voter Registration Guide for {data['country']}"]

    if reg.get("steps"):
        result_parts.append("\n### Steps to Register:")
        for i, step in enumerate(reg["steps"], 1):
            result_parts.append(f"{i}. {step}")

    if reg.get("documents_required"):
        result_parts.append("\n### Documents Required:")
        for doc in reg["documents_required"]:
            result_parts.append(f"- {doc}")

    if reg.get("online_portal"):
        result_parts.append(f"\n🌐 **Online Portal**: {reg['online_portal']}")
    if reg.get("deadline"):
        result_parts.append(f"⏰ **Deadline**: {reg['deadline']}")
    if reg.get("processing_time"):
        result_parts.append(f"⏳ **Processing Time**: {reg['processing_time']}")

    return "\n".join(result_parts)


def get_voting_process(country: str) -> str:
    """Get step-by-step voting process for a country."""
    data = get_country_data(country)
    if not data:
        return f"Voting process data not available for '{country}'. Supported countries: India, USA, UK."

    result_parts = [f"## 🗳️ How to Vote in {data['country']}"]

    if data.get("voting_process"):
        result_parts.append("\n### Step-by-Step Process:")
        for i, step in enumerate(data["voting_process"], 1):
            result_parts.append(f"{i}. {step}")

    if data.get("voter_id"):
        result_parts.append(f"\n🪪 **Required ID**: {data['voter_id']}")

    return "\n".join(result_parts)


def format_eligibility_result(result: dict) -> str:
    """Format eligibility check result."""
    parts = []
    if result["eligible"]:
        parts.append("## ✅ You Are Eligible to Vote!")
    else:
        parts.append("## ❌ Eligibility Issues Found")

    parts.append(f"\n{result['reason']}")

    if result["next_steps"]:
        parts.append("\n### Next Steps:")
        for step in result["next_steps"]:
            parts.append(f"- {step}")

    return "\n".join(parts)


# ── Agent Orchestration ────────────────────────────────────────

def run_agent(
    message: str,
    history: list,
    language: str,
    mode: str,
    user_context: dict | None,
) -> AgentResult:
    """
    Main agent orchestration:
    1. Classify intent
    2. Detect country
    3. Run appropriate tool(s)
    4. Gather RAG context
    5. Generate response with LLM
    """
    intent = classify_intent(message)
    country = detect_country(message, user_context)
    tool_outputs: list[str] = []
    rag_context = ""

    logger.info(f"Intent: {intent}, Country: {country}, Mode: {mode}, Language: {language}")

    # Execute tools based on intent
    if intent == "timeline" and country:
        tool_outputs.append(get_timeline_info(country))
    elif intent == "eligibility":
        if user_context and user_context.get("age"):
            result = check_eligibility(
                country=country or user_context.get("country", "india"),
                age=user_context["age"],
                is_citizen=user_context.get("is_citizen", True),
                is_resident=user_context.get("is_resident", True),
            )
            tool_outputs.append(format_eligibility_result(result))
    elif intent == "registration" and country:
        tool_outputs.append(get_registration_guide(country))
    elif intent == "process" and country:
        tool_outputs.append(get_voting_process(country))

    # RAG search for additional context
    rag_results = rag_search(message, n_results=3, country=country)
    if rag_results:
        rag_context = "\n\n".join([r["content"] for r in rag_results])

    # Build the enhanced prompt
    system = SIMPLIFIED_SYSTEM_PROMPT if mode == "simplified" else SYSTEM_PROMPT

    # Language instruction — native language enforcement
    if language and language.lower() != "english":
        lang_name = LANGUAGE_NAMES.get(language.lower(), language.capitalize())
        system += (
            f"\n\nCRITICAL LANGUAGE REQUIREMENT: You MUST respond EXCLUSIVELY in {lang_name}. "
            f"Every single word of your response — including headers, bullet points, numbered lists, "
            f"labels, dates, explanations, and any other text — must be written in {lang_name}. "
            f"Do NOT use any English words or phrases anywhere in your response. "
            f"Think and respond naturally as a fluent native speaker of {lang_name} would. "
            f"If you include technical terms, provide them in {lang_name} script followed by the original in parentheses only if absolutely necessary."
        )

    # User context
    context_info = ""
    if user_context:
        ctx_parts = []
        if user_context.get("country"):
            ctx_parts.append(f"Country: {user_context['country']}")
        if user_context.get("age"):
            ctx_parts.append(f"Age: {user_context['age']}")
        if user_context.get("is_first_time_voter"):
            ctx_parts.append("First-time voter: Yes")
        if ctx_parts:
            context_info = f"\n\nUser Context: {', '.join(ctx_parts)}"

    # Combine all context
    augmented_message = message
    if tool_outputs or rag_context:
        augmented_message = f"""User Question: {message}
{context_info}

--- Retrieved Information (use this to answer accurately) ---
{chr(10).join(tool_outputs)}

--- Additional Knowledge Base Context ---
{rag_context}
---

Based on the above information, provide a comprehensive, accurate answer to the user's question.
If the retrieved information is relevant, use it. If not, answer from your own knowledge.
Always cite official sources where applicable."""

    # Build conversation contents
    contents = []
    for msg in history:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=augmented_message)]))

    # Call LLM with fallback chain
    last_error = None
    for model_id in MODELS:
        try:
            logger.info(f"Trying model: {model_id}")
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.7,
                    max_output_tokens=2048,
                ),
            )

            if not response or not response.text:
                raise ValueError("Empty response from model.")

            logger.info(f"✅ Success with model: {model_id}")
            return AgentResult(
                response=response.text.strip(),
                model_used=model_id,
                intent=intent,
                country_detected=country,
                tools_used=[t[:50] for t in tool_outputs] if tool_outputs else [],
                rag_results_count=len(rag_results),
            )

        except Exception as e:
            err_str = str(e)
            logger.warning(f"❌ Model {model_id} failed: {err_str[:120]}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str or "NOT_FOUND" in err_str:
                last_error = e
                time.sleep(0.5)
                continue
            raise HTTPException(status_code=500, detail=f"AI error ({model_id}): {err_str}")

    # ── Graceful no-LLM fallback ──────────────────────────────────────────────
    # All Gemini models are quota-exhausted. Return tool + RAG data directly
    # so the user always gets a useful, structured answer.
    logger.warning("All models quota-exhausted — returning tool/RAG fallback response.")

    fallback_parts = []

    if tool_outputs:
        fallback_parts.extend(tool_outputs)
    elif rag_results:
        fallback_parts.append("## 📚 Information from Knowledge Base\n")
        for r in rag_results[:3]:
            fallback_parts.append(r["content"])
    else:
        fallback_parts.append(
            "I'm currently experiencing high demand and my AI models are temporarily unavailable. "
            "Here are some quick resources:\n\n"
            "- **India**: Visit [voters.eci.gov.in](https://voters.eci.gov.in) for registration\n"
            "- **USA**: Visit [vote.gov](https://vote.gov) for voter registration\n"
            "- **UK**: Visit [gov.uk/register-to-vote](https://www.gov.uk/register-to-vote) for registration\n\n"
            "Please try again in a minute for a personalized AI response."
        )

    fallback_note = (
        "\n\n---\n*⚠️ AI model temporarily at capacity. Showing verified data directly. "
        "Please try again in ~60 seconds for a full AI response.*"
    )

    return AgentResult(
        response="\n\n".join(fallback_parts) + fallback_note,
        model_used="fallback-tool-data",
        intent=intent,
        country_detected=country,
        tools_used=[t[:50] for t in tool_outputs] if tool_outputs else [],
        rag_results_count=len(rag_results),
    )


# ── API Endpoints ──────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "VoteGuide — AI Election Assistant API v2.0",
        "features": [
            "Multi-turn conversation",
            "RAG-powered answers",
            "Intent classification",
            "Eligibility checker",
            "Timeline generator",
            "Multi-language support",
            "Simplified explanations",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a moment before sending more messages.",
        )

    result = run_agent(
        message=req.message,
        history=req.history,
        language=req.language,
        mode=req.mode,
        user_context=req.user_context,
    )
    return result


@app.post("/eligibility")
def eligibility_check(req: EligibilityRequest):
    result = check_eligibility(
        country=req.country,
        age=req.age,
        is_citizen=req.is_citizen,
        is_resident=req.is_resident,
    )
    return result


@app.get("/timeline/{country}")
def get_timeline(country: str, year: str = "2024"):
    data = get_country_data(country)
    if not data:
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found. Supported: India, USA, UK.")
    return {
        "country": data["country"],
        "timeline": data.get("timelines", {}),
        "election_types": data.get("election_types", []),
        "registration_deadline": data.get("registration", {}).get("deadline"),
    }


@app.get("/countries")
def list_countries():
    countries = []
    for key, data in ELECTION_DATA.items():
        countries.append({
            "key": key,
            "name": data["country"],
            "voting_age": data["voting_age"],
            "election_commission": data["election_commission"],
            "website": data["website"],
        })
    return {"countries": countries}


@app.get("/registration/{country}")
def get_registration(country: str):
    data = get_country_data(country)
    if not data:
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found.")
    return {
        "country": data["country"],
        "registration": data.get("registration", {}),
        "voter_id": data.get("voter_id", ""),
    }


# ── Google Cloud API Proxy (server-side key — never exposed to browser) ────────

GOOGLE_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY", "")


class TranslateProxyRequest(BaseModel):
    q: list[str]          # strings to translate
    target: str           # BCP-47 target language code
    source: str = "en"    # source language


class STTProxyRequest(BaseModel):
    audio_base64: str     # base64-encoded audio bytes
    language_code: str    # BCP-47 e.g. "en-US", "hi-IN"
    sample_rate: int = 48000
    encoding: str = "WEBM_OPUS"


class TTSProxyRequest(BaseModel):
    text: str
    language_code: str    # BCP-47 e.g. "en-US"
    voice_name: str = ""  # optional; auto-selected if empty


@app.post("/api/translate")
def proxy_translate(req: TranslateProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Translation API v2."""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="Translation service not configured.")

    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    try:
        resp = httpx.post(
            TRANSLATE_URL,
            params={"key": GOOGLE_API_KEY},
            json={"q": req.q, "target": req.target, "source": req.source, "format": "text"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Translate API error: {e.response.text}")
        raise HTTPException(status_code=502, detail="Translation service error.")
    except Exception as e:
        logger.error(f"Translate proxy error: {e}")
        raise HTTPException(status_code=502, detail="Translation service unavailable.")


@app.post("/api/stt")
def proxy_stt(req: STTProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Speech-to-Text API."""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="Speech-to-text service not configured.")

    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    body = {
        "config": {
            "encoding": req.encoding,
            "sampleRateHertz": req.sample_rate,
            "languageCode": req.language_code,
            "enableAutomaticPunctuation": True,
            "model": "latest_long",
        },
        "audio": {"content": req.audio_base64},
    }

    try:
        resp = httpx.post(
            STT_URL,
            params={"key": GOOGLE_API_KEY},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"STT API error: {e.response.text}")
        raise HTTPException(status_code=502, detail="Speech-to-text service error.")
    except Exception as e:
        logger.error(f"STT proxy error: {e}")
        raise HTTPException(status_code=502, detail="Speech-to-text service unavailable.")


@app.post("/api/tts")
def proxy_tts(req: TTSProxyRequest, request: Request):
    """Server-side proxy for Google Cloud Text-to-Speech API."""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="Text-to-speech service not configured.")

    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    voice_name = req.voice_name or WAVENET_VOICES.get(req.language_code, "")

    voice_payload: dict = {"languageCode": req.language_code}
    if voice_name:
        voice_payload["name"] = voice_name

    body = {
        "input": {"text": req.text},
        "voice": voice_payload,
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0},
    }

    try:
        resp = httpx.post(
            TTS_URL,
            params={"key": GOOGLE_API_KEY},
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()  # {"audioContent": "<base64 MP3>"}
    except httpx.HTTPStatusError as e:
        logger.error(f"TTS API error: {e.response.text}")
        raise HTTPException(status_code=502, detail="Text-to-speech service error.")
    except Exception as e:
        logger.error(f"TTS proxy error: {e}")
        raise HTTPException(status_code=502, detail="Text-to-speech service unavailable.")