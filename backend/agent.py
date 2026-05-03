"""
Agent orchestration service for VoteGuide.

Coordinates the 3-layer intelligence stack:
1. Intent Classification
2. Tool Execution
3. RAG + LLM Generation

Includes LRU caching for repeated queries and model fallback chain.
"""

import time
import hashlib
import logging
from collections import OrderedDict
from typing import Optional

from google import genai
from google.genai import types

from models import AgentResult
from intent import classify_intent, detect_country
from tools import execute_tools
from rag import search as rag_search

logger = logging.getLogger("voteguide.agent")


# ── Constants ─────────────────────────────────────────────────────────────────

MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

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

MAX_HISTORY_TURNS = 20  # Limit conversation context to prevent token overflow

# ── LRU Response Cache ────────────────────────────────────────────────────────

_cache: OrderedDict[str, tuple[AgentResult, float]] = OrderedDict()
CACHE_MAX_SIZE = 128
CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(message: str, language: str, mode: str, country: Optional[str]) -> str:
    """Generate a deterministic cache key from query parameters."""
    raw = f"{message.lower().strip()}|{language}|{mode}|{country or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cache_get(key: str) -> Optional[AgentResult]:
    """Get a cached result if it exists and hasn't expired."""
    if key in _cache:
        result, ts = _cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            _cache.move_to_end(key)
            return result
        else:
            del _cache[key]
    return None


def _cache_set(key: str, result: AgentResult) -> None:
    """Store a result in cache, evicting oldest if at capacity."""
    _cache[key] = (result, time.time())
    if len(_cache) > CACHE_MAX_SIZE:
        _cache.popitem(last=False)


# ── System Prompts ────────────────────────────────────────────────────────────

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


# ── Agent Orchestration ───────────────────────────────────────────────────────

def run_agent(
    message: str,
    history: list,
    language: str,
    mode: str,
    user_context: dict | None,
    client: genai.Client,
) -> AgentResult:
    """
    Main agent orchestration pipeline:
    1. Classify intent
    2. Detect country
    3. Check cache for identical queries
    4. Run appropriate tool(s)
    5. Gather RAG context
    6. Build prompt with language enforcement
    7. Generate response with LLM (fallback chain)
    8. Cache and return result
    """
    intent = classify_intent(message)
    country = detect_country(message, user_context)

    logger.info(f"Intent: {intent}, Country: {country}, Mode: {mode}, Language: {language}")

    # Check cache for stateless queries (no history)
    cache_key = None
    if not history:
        cache_key = _cache_key(message, language, mode, country)
        cached = _cache_get(cache_key)
        if cached:
            logger.info("Cache HIT — returning cached response")
            return cached

    # Execute tools based on intent
    tool_outputs = execute_tools(intent, country, user_context)

    # RAG search for additional context
    rag_results = rag_search(message, n_results=3, country=country)
    rag_context = ""
    if rag_results:
        rag_context = "\n\n".join([r["content"] for r in rag_results])

    # Build the enhanced system prompt
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

    # Combine all context into augmented prompt
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

    # Build conversation contents (truncate long histories)
    truncated_history = history[-MAX_HISTORY_TURNS:]
    contents = []
    for msg in truncated_history:
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
            result = AgentResult(
                response=response.text.strip(),
                model_used=model_id,
                intent=intent,
                country_detected=country,
                tools_used=[t[:50] for t in tool_outputs] if tool_outputs else [],
                rag_results_count=len(rag_results),
            )

            # Cache successful responses
            if cache_key:
                _cache_set(cache_key, result)

            return result

        except Exception as e:
            err_str = str(e)
            logger.warning(f"❌ Model {model_id} failed: {err_str[:120]}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str or "NOT_FOUND" in err_str:
                last_error = e
                time.sleep(0.5)
                continue
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"AI error ({model_id}): {err_str}")

    # ── Graceful no-LLM fallback ──────────────────────────────────────────────
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
