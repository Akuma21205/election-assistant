# VoteGuide Architecture

This document describes the technical architecture of VoteGuide — the AI-powered election assistant built for the PromptWars (Google × Hack2Skill) challenge.

---

## System Overview

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  Next.js 16 + React 19 + TypeScript                  │
│  ErrorBoundary + TranslationProvider wrappers        │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Translation │  │ Speech (STT) │  │ TTS Player │  │
│  │  Context    │  │  via backend │  │  via backend│  │
│  │  (9 langs)  │  │  /api/stt    │  │  /api/tts  │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                │                │          │
│  Firebase Firestore ←→ Real-time chat history        │
└──────────────────────┬───────────────────────────────┘
                       │ POST /chat  (or /chat/stream SSE)
┌──────────────────────▼───────────────────────────────┐
│                    BACKEND (modular service layer)   │
│  FastAPI + Python 3.12                               │
│                                                      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │  intent.py   │  │   tools.py    │  │models.py │  │
│  │  Classifier  │  │  • Timeline   │  │ Pydantic │  │
│  │  + Country   │  │  • Eligibility│  │ schemas  │  │
│  │  Detection   │  │  • Reg. Guide │  │          │  │
│  └──────┬───────┘  └───────┬───────┘  └──────────┘  │
│         │                  │                         │
│  ┌──────▼──────────────────▼───────┐                 │
│  │  agent.py (orchestration)       │                 │
│  │  LRU cache + model fallback     │                 │
│  └──────────────────┬──────────────┘                 │
│                     │                                │
│  ┌──────────────────▼──────────────┐                 │
│  │   RAG Engine (rag.py + ChromaDB)│                 │
│  │   semantic search → top-3 docs  │                 │
│  └──────────────────┬──────────────┘                 │
│                     │                                │
│  ┌──────────────────▼──────────────┐                 │
│  │   Gemini API (fallback chain)   │                 │
│  │  2.5 Flash → 2.0 → 1.5 Flash   │                 │
│  └─────────────────────────────────┘                 │
│                                                      │
│  middleware.py — Rate limiting, tracing, sanitization │
└──────────────────────────────────────────────────────┘
```

---

## 3-Layer Intelligence Stack

### Layer 1 — Intent Classification (`intent.py`)

Keyword-based classifier routes user queries to one of six intents:

| Intent | Keywords |
|--------|----------|
| `timeline` | when, date, schedule, deadline, calendar, upcoming |
| `eligibility` | eligible, qualify, requirements, age limit, who can vote |
| `registration` | register, sign up, enroll, voter id, form 6 |
| `process` | how to vote, steps, procedure, ballot, polling |
| `explanation` | what is, explain, define, meaning of, describe |
| `general` | (fallback — no strong match) |

Country detection (`detect_country`) identifies India/USA/UK from keywords or `user_context`.

### Layer 2 — Tool Execution (`tools.py`)

Based on the detected intent + country, one of these structured tools runs:

| Tool | Output |
|------|--------|
| `get_timeline_info()` | Election phases, dates, deadlines |
| `get_registration_guide()` | Steps, documents, portal links |
| `get_voting_process()` | Step-by-step voting instructions |
| `format_eligibility_result()` | Eligibility decision + next steps |
| `execute_tools()` | Centralized dispatcher routing intent → tool |

### Layer 3 — RAG + LLM (`agent.py`)

1. **ChromaDB** performs semantic vector search over `election_data.py` (top-3 results)
2. Tool output + RAG context are injected into the system prompt
3. **Gemini** generates the final response with language enforcement
4. LRU cache (128 entries, 5-min TTL) deduplicates identical stateless queries

---

## Request Flow (End to End)

```
User speaks / types
        │
        ▼ (optional) MediaRecorder → POST /api/stt → Backend proxy → Google Cloud STT → transcript
        │
        ▼ User types or paste transcript into chat input
        │
        ▼ POST /chat (or POST /chat/stream for SSE)
        │  { message, language, mode, user_context, history }
        │
        ▼ middleware.py: X-Request-ID + timing + rate limit (20 req/min per IP)
        │
        ▼ middleware.py: sanitize_chat_input (prompt injection defense)
        │
        ▼ intent.py: classify_intent (keyword scoring)
        │
        ▼ intent.py: detect_country (keywords + user_context)
        │
        ▼ tools.py: execute_tools (structured election data → formatted markdown)
        │
        ▼ rag.py: search (ChromaDB, top-3 semantic matches, filtered by country)
        │
        ▼ agent.py: Prompt assembly + Gemini API (fallback chain)
        │
        ▼ Response saved to Firebase Firestore (real-time sync to client)
        │
        ▼ Rendered as MessageBubble with markdown formatting in chat UI
        │
        ▼ (optional) POST /api/tts → Backend proxy → Google Cloud TTS → MP3 plays
```

---

## Frontend Architecture

### Providers (Root Layout)

| Provider | Responsibility |
|----------|---------------|
| `ErrorBoundary` | Catches render crashes, shows recovery UI |
| `TranslationProvider` | Provides `t()` translation function to entire component tree |

### Hooks (Custom React Hooks)

| Hook | Responsibility |
|------|---------------|
| `useChat` | Firestore sync, sendMessage, Firestore `addDoc`, auto-scroll |
| `useSpeech` | STT recording state, TTS playback, auto-speak, mic visual state |

### Components

| Component | Responsibility |
|-----------|---------------|
| `page.tsx` | Root composition — assembles all hooks + components (~300 lines) |
| `MessageBubble` | Chat message with custom markdown renderer + TTS play button |
| `TypingIndicator` | Animated three-dot loader with `role="status"` |
| `SettingsPanel` | Language, mode, profile settings modal (ARIA dialog) |
| `EligibilityChecker` | Eligibility form modal (ARIA dialog, focus trap) |
| `VotingFlow` | 6-step voting journey modal (ARIA dialog, focus trap) |
| `ErrorBoundary` | Class-based React error boundary with retry |
| `Icons` | Reusable SVG icon components |

### Accessibility (WCAG 2.1 AA)

- All modals have `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Focus trapped inside modals; Escape key closes
- Toggle buttons have `aria-pressed`
- Form controls have `aria-label` (no placeholder-only labeling)
- Message list has `role="log"` with `aria-live="polite"`
- Status banners use `role="alert"` and `role="status"`
- Decorative icons have `aria-hidden="true"`

---

## Backend Architecture (Modular Service Layer)

### Module Layout

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app, thin routing layer, Google Cloud API proxies |
| `agent.py` | Agent orchestration: intent → tools → RAG → LLM, LRU cache, model fallback |
| `intent.py` | Intent classification and country detection (keyword scoring) |
| `tools.py` | Structured election data tools + centralized `execute_tools()` dispatcher |
| `models.py` | All Pydantic request/response schemas and TypedDicts |
| `middleware.py` | Request tracing, timing headers, rate limiting, input sanitization |
| `election_data.py` | Structured election data for India, USA, UK |
| `rag.py` | ChromaDB initialization and semantic search |
| `Dockerfile` | Multi-stage build with non-root user + HEALTHCHECK |
| `tests/conftest.py` | Shared fixtures, mocked Gemini client, rate-limit reset |
| `tests/test_api.py` | Integration tests for all API endpoints |
| `tests/test_agent.py` | Unit tests for agent logic (intent, tools, orchestration) |
| `tests/test_proxy.py` | Unit tests for Google Cloud API proxy endpoints |
| `tests/test_election_data.py` | Unit tests for election data, eligibility, RAG |

### Key Constants (Module-Level)

```python
# agent.py
MODELS = ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash", "gemini-1.5-flash"]
CACHE_MAX_SIZE = 128          # LRU cache entries
CACHE_TTL_SECONDS = 300       # 5-minute cache expiry
MAX_HISTORY_TURNS = 20        # conversation context limit

# middleware.py
RATE_LIMIT_MAX = 20           # requests per window per IP
RATE_LIMIT_WINDOW = 60        # sliding window in seconds
INJECTION_PATTERNS = [...]    # compiled regex patterns for prompt injection defense
```

### TypedDicts for Typed Returns

```python
class AgentResult(TypedDict):
    response: str
    model_used: str
    intent: str
    country_detected: Optional[str]
    tools_used: list[str]
    rag_results_count: int
```

---

## Security

| Layer | Mechanism |
|-------|-----------|
| Rate limiting | 20 req/min per IP (in-memory sliding window, `middleware.py`) |
| Input sanitization | Regex-based prompt injection detection (`middleware.py`) |
| Request tracing | `X-Request-ID` + `X-Response-Time` headers (`middleware.py`) |
| Input validation | Pydantic models with `Field(max_length=4000)` (`models.py`) |
| CORS | Explicit allowlist + Firebase Hosting regex |
| API keys | All Google API calls proxied server-side; keys never in browser |
| Firestore rules | `create`-only with field validation; no update/delete |
| Prompt isolation | RAG context clearly delimited with `---` separators |
| Non-partisan guardrail | System prompt prohibits political bias |

> ⚠️ **Known limitation:** Rate limiting is in-memory (per-process). For multi-instance deployments, integrate Redis or Cloud Memorystore.

---

## Google Services Integration

| Service | Usage |
|---------|-------|
| Gemini API (2.5/2.0/1.5 Flash) | Primary LLM with 3-model fallback |
| Google Cloud Translation API v2 | Batch UI translation (100+ strings), in-memory cached |
| Google Cloud Speech-to-Text v1 | Voice input (WEBM_OPUS, language-aware) |
| Google Cloud Text-to-Speech v1 | Wavenet voices for 9 languages |
| Firebase Firestore | Real-time chat persistence (no authentication required) |
| Firebase Hosting | Static Next.js frontend deployment |

---

## RAG Knowledge Base

- Seeded from `election_data.py` at startup (no external pipelines)
- ChromaDB in-process vector store (no separate server needed)
- Documents are chunked per election aspect (eligibility, registration, timeline, process)
- Search filtered by country when country is detected in the query
- Top-3 results are injected into the LLM prompt

---

## Assumptions

1. **Election data scope** — Deep structured data covers India, USA, UK. Other countries handled by Gemini general knowledge.
2. **API key scope** — Single Google Cloud API key covers Translation, STT, and TTS.
3. **Audio format** — MediaRecorder produces WebM/Opus (Chrome/Edge); STT configured for `WEBM_OPUS`.
4. **No user authentication** — Session identity is a UUID stored in `sessionStorage`.
5. **RAG data** — Knowledge base seeded from `election_data.py` at startup.
6. **TTS text limit** — Responses truncated to 4,800 chars (Google API ~5,000 byte limit).
