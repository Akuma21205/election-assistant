# 🗳️ VoteGuide — AI-Powered Election Assistant

> **PromptWars Challenge — Google × Hack2Skill**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?logo=google)](https://ai.google.dev)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?logo=firebase)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

A **non-partisan, multilingual AI chatbot** that helps every citizen — first-time voter or seasoned participant — understand elections, registration, timelines, and civic participation. Fully accessible, voice-enabled, and available in 9 languages.

---

## 📌 Chosen Vertical

**Civic Technology / Government & Public Services**

VoteGuide targets the universal challenge of voter education. Millions of eligible citizens miss elections or make uninformed choices due to complex, inaccessible information. VoteGuide bridges that gap with a conversational AI that speaks the user's language — literally and figuratively — combining authoritative data with an approachable interface.

---

## 🎯 Approach and Logic

### Problem Statement
Election information is fragmented across dozens of government websites, written in bureaucratic language, and rarely available in regional languages. First-time voters, elderly citizens, and non-English speakers are disproportionately disadvantaged.

### Solution Design

The system is built around a **3-layer intelligence stack**:

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. INTENT LAYER                    │
│  Keyword-based classifier routes to │
│  timeline / eligibility / process   │
│  / registration / general           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  2. TOOL LAYER                      │
│  Structured data tools execute:     │
│  • Timeline Generator               │
│  • Eligibility Checker              │
│  • Registration Guide               │
│  • Voting Process Guide             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  3. RAG + LLM LAYER                 │
│  ChromaDB semantic search           │
│  + Gemini generates final response  │
│  in user's chosen language & mode   │
└─────────────────────────────────────┘
```

**Design Principles:**
- **Non-partisan**: System prompt explicitly prohibits political bias
- **Grounded**: RAG retrieval reduces hallucinations using verified election data
- **Accessible**: Multi-language, simplified mode, voice I/O, mobile-responsive
- **Resilient**: 3-model fallback chain prevents API failures from breaking UX

---

## ⚙️ How the Solution Works

### End-to-End Flow

```
User speaks / types
        │
        ▼ (optional) Google Cloud STT → transcript
        │
        ▼ POST /chat { message, language, mode, user_context, history }
        │
        ▼ Intent Classification (timeline/eligibility/registration/process/general)
        │
        ▼ Country Detection (India/USA/UK from context or keywords)
        │
        ▼ Tool Execution (structured election data)
        │
        ▼ RAG Search (ChromaDB vector DB, top-3 relevant chunks)
        │
        ▼ Prompt Assembly (system + tool output + RAG context + user message)
        │
        ▼ Gemini API (2.5 Flash → 2.0 Flash → 1.5 Flash fallback)
        │
        ▼ Response saved to Firebase Firestore (real-time sync)
        │
        ▼ Rendered in chat UI
        │
        ▼ (optional) Google Cloud TTS → Wavenet voice plays audio
```

### Key Components

#### Backend (`FastAPI` + Python 3.12)
| File | Responsibility |
|------|----------------|
| `main.py` | API server, agent orchestration, intent classification, LLM calls |
| `election_data.py` | Comprehensive structured election data for India, USA, UK |
| `rag.py` | ChromaDB vector store — ingests and searches election knowledge base |

#### Frontend (`Next.js 16` + TypeScript)
| File | Responsibility |
|------|----------------|
| `app/page.tsx` | Main chat UI with STT/TTS integration |
| `lib/translate.ts` | Google Cloud Translation API with in-memory caching |
| `lib/speech.ts` | Google Cloud STT (MediaRecorder → API) + TTS (Wavenet voices) |
| `lib/TranslationContext.tsx` | React context — translates all UI strings app-wide |
| `lib/uiStrings.ts` | Single source of truth for all 100+ English UI strings |
| `components/SettingsPanel.tsx` | Language, mode, and profile configuration |
| `components/EligibilityChecker.tsx` | Interactive eligibility form with translated results |
| `components/VotingFlow.tsx` | Visual step-by-step voting journey |

---

## 🌟 Features

| Feature | Implementation |
|---------|----------------|
| 💬 **Conversational AI** | Multi-turn chat with Firestore real-time sync |
| 🤖 **Agent Orchestration** | Intent → Tool → RAG → Gemini pipeline |
| 🔍 **RAG (ChromaDB)** | Semantic search over verified election knowledge base |
| 🌍 **Full UI Translation** | Google Cloud Translation API — entire interface in 9 languages |
| 🤖 **Native LLM Language** | Gemini responds natively in selected language (Wavenet-quality) |
| 🎤 **Google STT** | MediaRecorder → Google Cloud Speech-to-Text (language-aware) |
| 🔊 **Google TTS** | Per-message speaker button + auto-speak toggle (Wavenet voices) |
| ✅ **Eligibility Checker** | Country/age/citizenship check with translated results |
| 📅 **Timeline Generator** | Election dates, deadlines, and phases for India/USA/UK |
| 🗳️ **Voting Journey** | Visual 6-step flow: Register → ID → Verify → Booth → Vote → Results |
| 🧒 **Simplified Mode** | "Explain Like I'm 10" — friendly, emoji-rich explanations |
| 👤 **Personalization** | Tailored by country, age, first-time voter status |
| ⚡ **Model Fallback** | Gemini 2.5 Flash → 2.0 Flash → 1.5 Flash auto-failover |
| 🔒 **Rate Limiting** | 20 req/min per IP, CORS whitelisting |

---

## 🏗️ Architecture

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
│  │              │  │  • Eligibility│                 │
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

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| **Backend** | FastAPI, Python 3.12, uvicorn |
| **AI / LLM** | Google Gemini API (2.5 Flash, 2.0 Flash, 1.5 Flash fallback) |
| **RAG** | ChromaDB (in-process vector store) |
| **Translation** | Google Cloud Translation API v2 |
| **Voice STT** | Google Cloud Speech-to-Text API v1 |
| **Voice TTS** | Google Cloud Text-to-Speech API v1 (Wavenet voices) |
| **Database** | Firebase Firestore (real-time chat persistence) |
| **Deployment** | Docker (backend), Firebase Hosting (frontend) |

---

## 🌍 Supported Languages

| Language | Code | TTS Voice | STT Code |
|----------|------|-----------|----------|
| English | `en` | en-US-Wavenet-D | en-US |
| हिन्दी (Hindi) | `hi` | hi-IN-Wavenet-A | hi-IN |
| Español (Spanish) | `es` | es-ES-Wavenet-B | es-ES |
| Français (French) | `fr` | fr-FR-Wavenet-C | fr-FR |
| தமிழ் (Tamil) | `ta` | ta-IN-Wavenet-A | ta-IN |
| తెలుగు (Telugu) | `te` | te-IN-Wavenet-A | te-IN |
| বাংলা (Bengali) | `bn` | bn-IN-Wavenet-A | bn-IN |
| मराठी (Marathi) | `mr` | mr-IN-Wavenet-A | mr-IN |
| ಕನ್ನಡ (Kannada) | `kn` | kn-IN-Wavenet-A | kn-IN |

---

## 🌐 Supported Countries

| Country | Election Types |
|---------|---------------|
| 🇮🇳 **India** | Lok Sabha, Rajya Sabha, State Assembly, Local Body |
| 🇺🇸 **USA** | Presidential, Midterm, Congressional, State & Local, Primaries |
| 🇬🇧 **UK** | General, Local, Devolved, By-elections |

---

## 📂 Project Structure

```
prompt-to-war-2nd-challenge/
├── backend/
│   ├── main.py              # FastAPI server + agent orchestration
│   ├── election_data.py     # Structured election data (India/USA/UK)
│   ├── rag.py               # RAG engine with ChromaDB
│   ├── pyproject.toml       # Python dependencies (uv)
│   ├── Dockerfile           # Container definition
│   ├── .env.example         # Environment variable template
│   └── tests/
│       ├── test_api.py      # Integration tests for all API endpoints
│       ├── test_agent.py    # Unit tests for agent orchestration logic
│       └── test_proxy.py    # Unit tests for Google Cloud API proxies
├── frontend/
│   ├── __tests__/
│   │   └── speech.test.ts   # Frontend utility tests (jest)
│   ├── app/
│   │   ├── page.tsx          # Main chat UI (hooks + components composed)
│   │   ├── layout.tsx        # Root layout + SEO meta tags
│   │   ├── globals.css       # Design system + keyframe animations
│   │   └── components/
│   │       ├── Icons.tsx             # SVG icon components
│   │       ├── MessageBubble.tsx     # Single chat message with TTS button
│   │       ├── TypingIndicator.tsx   # Animated three-dot loading indicator
│   │       ├── SettingsPanel.tsx     # Language/mode/profile settings (ARIA dialog)
│   │       ├── EligibilityChecker.tsx # Eligibility form (ARIA dialog + focus trap)
│   │       └── VotingFlow.tsx        # Visual 6-step voting journey (ARIA dialog)
│   ├── lib/
│   │   ├── firebase.ts           # Firebase client init
│   │   ├── uiStrings.ts          # All UI strings (English source of truth)
│   │   ├── translate.ts          # Google Translate API + in-memory cache
│   │   ├── TranslationContext.tsx # React context for translated UI
│   │   ├── speech.ts             # Google STT + TTS utilities
│   │   └── hooks/
│   │       ├── useChat.ts        # Firestore sync + sendMessage hook
│   │       └── useSpeech.ts      # STT recording + TTS playback hook
│   └── .env.local.example        # Frontend env var template
├── docs/
│   └── architecture.md       # System architecture + component reference
├── firebase.json             # Firebase Hosting + Firestore config
├── firestore.rules           # Hardened Firestore security rules
└── README.md                 # This file
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+ with `uv` package manager
- Node.js 20+
- Google AI Studio API key (Gemini)
- Google Cloud project with these APIs enabled:
  - Cloud Translation API
  - Cloud Speech-to-Text API
  - Cloud Text-to-Speech API
- Firebase project (Firestore enabled)

### 1. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

uv sync
uv run uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Firebase + Google API credentials

npm install
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)**

### 3. Docker (Backend)

```bash
cd backend
docker build -t voteguide-backend .
docker run -p 8000:8000 --env-file .env voteguide-backend
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (default: localhost:3000) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase project API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase project ID |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase app ID |
| `NEXT_PUBLIC_API_URL` | Backend API URL (default: http://127.0.0.1:8000) |
| `NEXT_PUBLIC_GOOGLE_TRANSLATE_API_KEY` | Google Cloud API key (Translation + STT + TTS) |

---

## 🧪 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status and feature list |
| `/health` | GET | Health check |
| `/chat` | POST | Main chat (agent + RAG + multi-language + mode) |
| `/eligibility` | POST | Check voting eligibility by country/age/citizenship |
| `/timeline/{country}` | GET | Election timelines for a country |
| `/countries` | GET | List supported countries with metadata |
| `/registration/{country}` | GET | Voter registration guide |

### Chat Request Schema

```json
{
  "message": "How do I register to vote in India?",
  "history": [{ "role": "user", "content": "..." }],
  "language": "hindi",
  "mode": "standard",
  "user_context": {
    "country": "india",
    "age": 22,
    "is_first_time_voter": true
  }
}
```

---

## 🔐 Security

- **Rate Limiting** — 20 requests/minute per IP (in-memory sliding window)
- **Input Validation** — Pydantic models validate all request bodies with `Field(max_length=4000)`
- **CORS** — Whitelisted origins only; Firebase Hosting domains allowed via regex
- **Non-partisan Guardrails** — System prompt explicitly prohibits political bias or candidate promotion
- **Prompt Injection Defense** — RAG context is clearly delimited and labelled
- **Firestore Rules** — Create-only writes with field validation (role must be `user`/`assistant`, content < 10,000 chars); no updates or deletes
- **No PII Storage** — Only session ID (UUID) and chat content stored; no user authentication required
- **Server-side API keys** — All Google Cloud API calls are proxied through the backend; keys never exposed to the browser

---

## ♿ Accessibility

| Feature | Implementation |
|---------|----------------|
| **9 Languages** | Full UI + LLM responses translated via Google Cloud APIs |
| **Voice Input** | Google Cloud STT with language-aware BCP-47 codes |
| **Voice Output** | Google Cloud TTS with Wavenet voices per language |
| **Simplified Mode** | "Explain Like I'm 10" — plain language for any literacy level |
| **Semantic HTML** | `<header>`, `<main>`, `role="alert"`, `aria-label` on all buttons |
| **Keyboard Navigation** | Enter to send, full keyboard-accessible UI |
| **Responsive Layout** | `100dvh` flex layout, works on mobile |
| **Visual Indicators** | Recording banner, translating banner, typing indicator |
| **Color Contrast** | Dark mode with sufficient contrast ratios |

---

## ☁️ Google Services Integration

| Google Service | How It's Used |
|----------------|---------------|
| **Gemini API** | Primary LLM — 3-model fallback chain for resilience |
| **Google Cloud Translation API v2** | Translates entire UI (100+ strings) in one batched call; cached in-memory |
| **Google Cloud Speech-to-Text API v1** | Converts microphone audio (WebM/Opus) to text, language-aware |
| **Google Cloud Text-to-Speech API v1** | Wavenet voices for 9 languages; per-message play + auto-speak mode |
| **Firebase Firestore** | Real-time chat history persistence, cross-session continuity |
| **Firebase Hosting** | Static frontend deployment with CDN |

---

## 📋 Assumptions

1. **Election data scope** — Detailed structured data covers India, USA, and UK. Other countries are handled by Gemini's general knowledge.
2. **API key scope** — A single Google Cloud API key covers Translation, STT, and TTS (all enabled on the same GCP project).
3. **Audio format** — MediaRecorder produces WebM/Opus (Chrome/Edge); the STT API is configured for WEBM_OPUS encoding.
4. **Non-authentication** — No user login is required; session identity is a UUID stored in `sessionStorage`.
5. **RAG data** — The knowledge base is seeded from `election_data.py` at startup; no external data pipelines are needed.
6. **Language scope** — "Multi-language" covers UI translation and LLM language enforcement; election law accuracy in regional languages depends on Gemini's training data.
7. **TTS text limit** — Responses are truncated to 4,800 characters for TTS (Google API limit is ~5,000 bytes); longer responses are summarized in speech.

---

## 🏁 License

MIT — free to use, modify, and distribute with attribution.
