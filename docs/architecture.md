# VoteGuide Architecture

This document describes the technical architecture of VoteGuide — the AI-powered election assistant built for the PromptWars (Google × Hack2Skill) challenge.

---

## System Overview

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  Next.js 16 + React 19 + TypeScript                  │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Translation │  │ Speech (STT) │  │ TTS Player │  │
│  │  Context    │  │  MediaRec +  │  │  Wavenet   │  │
│  │  (9 langs)  │  │  Google STT  │  │  MP3 audio │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                │                │          │
│  Google Cloud Translation API   Google Cloud TTS/STT │
│                                                      │
│  Firebase Firestore ←→ Real-time chat history        │
└──────────────────────┬───────────────────────────────┘
                       │ POST /chat (fetch)
┌──────────────────────▼───────────────────────────────┐
│                    BACKEND                           │
│  FastAPI + Python 3.12                               │
│                                                      │
│  ┌──────────────┐  ┌───────────────┐                 │
│  │   Intent     │  │  Tool Layer   │                 │
│  │  Classifier  │  │  • Timeline   │                 │
│  │  (keyword)   │  │  • Eligibility│                 │
│  │              │  │  • Reg. Guide │                 │
│  └──────┬───────┘  └───────┬───────┘                 │
│         │                  │                         │
│  ┌──────▼──────────────────▼───────┐                 │
│  │         RAG Engine (ChromaDB)   │                 │
│  │   semantic search → top-3 docs  │                 │
│  └──────────────────┬──────────────┘                 │
│                     │                                │
│  ┌──────────────────▼──────────────┐                 │
│  │   Gemini API (fallback chain)   │                 │
│  │  2.5 Flash → 2.0 → 1.5 Flash   │                 │
│  └─────────────────────────────────┘                 │
└──────────────────────────────────────────────────────┘
```

---

## 3-Layer Intelligence Stack

### Layer 1 — Intent Classification

Keyword-based classifier routes user queries to one of five intents:

| Intent | Keywords |
|--------|----------|
| `timeline` | when, date, schedule, deadline, calendar |
| `eligibility` | eligible, qualify, requirements, age limit |
| `registration` | register, sign up, enroll, voter id |
| `process` | how to vote, steps, procedure, ballot |
| `general` | (fallback — no strong match) |

### Layer 2 — Tool Execution

Based on the detected intent + country, one of these structured tools runs:

| Tool | Output |
|------|--------|
| `get_timeline_info()` | Election phases, dates, deadlines |
| `get_registration_guide()` | Steps, documents, portal links |
| `get_voting_process()` | Step-by-step voting instructions |
| `format_eligibility_result()` | Eligibility decision + next steps |

### Layer 3 — RAG + LLM

1. **ChromaDB** performs semantic vector search over `election_data.py` (top-3 results)
2. Tool output + RAG context are injected into the system prompt
3. **Gemini** generates the final response with language enforcement

---

## Request Flow (End to End)

```
User speaks / types
        │
        ▼ (optional) MediaRecorder → POST /api/stt → Google Cloud STT → transcript
        │
        ▼ User types or paste transcript into chat input
        │
        ▼ POST /chat { message, language, mode, user_context, history }
        │
        ▼ Rate limit check (20 req/min per IP, in-memory sliding window)
        │
        ▼ Intent Classification (keyword scoring)
        │
        ▼ Country Detection (keywords + user_context)
        │
        ▼ Tool Execution (structured election data → formatted markdown)
        │
        ▼ RAG Search (ChromaDB, top-3 semantic matches, filtered by country)
        │
        ▼ Prompt Assembly (system + language enforcement + tool output + RAG + message)
        │
        ▼ Gemini API (2.5 Flash → 2.0 Flash → 1.5 Flash fallback on 429/404)
        │
        ▼ Response saved to Firebase Firestore (real-time sync to client)
        │
        ▼ Rendered as MessageBubble in chat UI
        │
        ▼ (optional) POST /api/tts → Google Cloud TTS → Wavenet MP3 plays
```

---

## Frontend Architecture

### Hooks (Custom React Hooks)

| Hook | Responsibility |
|------|---------------|
| `useChat` | Firestore sync, sendMessage, Firestore `addDoc`, auto-scroll |
| `useSpeech` | STT recording state, TTS playback, auto-speak, mic visual state |

### Components

| Component | Responsibility |
|-----------|---------------|
| `page.tsx` | Root composition — assembles all hooks + components (~300 lines) |
| `MessageBubble` | Single chat message with TTS play button |
| `TypingIndicator` | Animated three-dot loader with `role="status"` |
| `SettingsPanel` | Language, mode, profile settings modal (ARIA dialog) |
| `EligibilityChecker` | Eligibility form modal (ARIA dialog, focus trap) |
| `VotingFlow` | 6-step voting journey modal (ARIA dialog, focus trap) |

### Accessibility (WCAG 2.1 AA)

- All modals have `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Focus trapped inside modals; Escape key closes
- Toggle buttons have `aria-pressed`
- Form controls have `aria-label` (no placeholder-only labeling)
- Message list has `role="log"` with `aria-live="polite"`
- Status banners use `role="alert"` and `role="status"`
- Decorative icons have `aria-hidden="true"`

---

## Backend Architecture

### Module Layout

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app, agent orchestration (`run_agent`), all endpoints |
| `election_data.py` | Structured election data for India, USA, UK |
| `rag.py` | ChromaDB initialization and semantic search |
| `tests/test_api.py` | Integration tests for all API endpoints |
| `tests/test_agent.py` | Unit tests for agent logic (intent, tools, orchestration) |
| `tests/test_proxy.py` | Unit tests for Google Cloud API proxy endpoints |

### Key Constants (Module-Level)

```python
MODELS = ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash", "gemini-1.5-flash"]
RATE_LIMIT_MAX = 20       # requests per window
RATE_LIMIT_WINDOW = 60    # seconds
LANGUAGE_NAMES = {...}    # language code → display name
WAVENET_VOICES = {...}    # BCP-47 → Wavenet voice name
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
| Rate limiting | 20 req/min per IP (in-memory sliding window) |
| Input validation | Pydantic models with `Field(max_length=4000)` |
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
