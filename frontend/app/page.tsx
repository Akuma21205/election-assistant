"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { db } from "@/lib/firebase";
import { collection, addDoc, orderBy, query, onSnapshot, serverTimestamp, Timestamp } from "firebase/firestore";
import {
  BotIcon, SendIcon, HistoryIcon, MicIcon, SettingsIcon,
  CalendarIcon, CheckIcon, SpeakerIcon, SpeakerOffIcon, StopCircleIcon,
} from "./components/Icons";
import SettingsPanel, { LANGUAGES } from "./components/SettingsPanel";
import EligibilityChecker from "./components/EligibilityChecker";
import VotingFlow from "./components/VotingFlow";
import { TranslationProvider, useTranslation } from "@/lib/TranslationContext";
import {
  startRecording, stopRecording, recognizeSpeech,
  speakText, stopSpeaking,
} from "@/lib/speech";

type Role = "user" | "assistant";
interface Message { id: string; role: Role; content: string; timestamp: Date; }

function getSessionId(): string {
  const key = "voteguide_session";
  let id = sessionStorage.getItem(key);
  if (!id) { id = crypto.randomUUID(); sessionStorage.setItem(key, id); }
  return id;
}

const headerBtnStyle: React.CSSProperties = {
  width: 34, height: 34, borderRadius: 10, border: "1px solid var(--border)",
  background: "var(--bg-glass)", color: "var(--text-secondary)",
  display: "flex", alignItems: "center", justifyContent: "center",
  cursor: "pointer", transition: "all 0.2s", padding: 0,
};

const TypingIndicator = () => (
  <div style={{ display: "flex", gap: 6, alignItems: "center", padding: "4px 0" }}>
    {[0, 1, 2].map((i) => (
      <span key={i} style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent-primary)", display: "inline-block", animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite` }} />
    ))}
  </div>
);

function MessageBubble({
  msg, onSpeak, speakingId,
}: {
  msg: Message;
  onSpeak: (id: string, content: string) => void;
  speakingId: string | null;
}) {
  const { t } = useTranslation();
  const isUser = msg.role === "user";
  const isSpeakingThis = speakingId === msg.id;

  return (
    <div style={{ display: "flex", flexDirection: isUser ? "row-reverse" : "row", gap: 12, alignItems: "flex-start", animation: "fadeSlideUp 0.3s ease forwards" }}>
      {!isUser && <div style={{ flexShrink: 0, marginTop: 2 }}><BotIcon /></div>}
      {isUser && <div style={{ flexShrink: 0, width: 30, height: 30, borderRadius: "50%", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "white", marginTop: 2 }}>U</div>}
      <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: 4, alignItems: isUser ? "flex-end" : "flex-start" }}>
        <div className={isUser ? "" : "markdown-content"} style={{ padding: "12px 16px", borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px", background: isUser ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "var(--bg-card)", border: isUser ? "none" : "1px solid var(--border)", color: isUser ? "white" : "var(--text-primary)", fontSize: 14.5, lineHeight: 1.65, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {msg.content}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, paddingInline: 4 }}>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
          {/* TTS play button — assistant messages only */}
          {!isUser && (
            <button
              onClick={() => onSpeak(msg.id, msg.content)}
              title={isSpeakingThis ? t.stopSpeakLabel : t.speakMsgLabel}
              style={{
                background: isSpeakingThis ? "rgba(139,92,246,0.15)" : "transparent",
                border: "none", borderRadius: 6, padding: "2px 4px",
                cursor: "pointer", color: isSpeakingThis ? "#8b5cf6" : "var(--text-muted)",
                display: "flex", alignItems: "center", transition: "all 0.2s",
              }}
            >
              {isSpeakingThis ? <StopCircleIcon /> : <SpeakerIcon />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Inner component — consumes TranslationContext ──────────────────
function HomeContent({ language, setLanguage }: { language: string; setLanguage: (l: string) => void }) {
  const { t, isTranslating } = useTranslation();

  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState<string>(() => typeof window !== "undefined" ? getSessionId() : crypto.randomUUID());
  const [isSynced, setIsSynced] = useState(false);

  // Settings
  const [mode, setMode] = useState("standard");
  const [userContext, setUserContext] = useState({ country: "", age: "", is_first_time_voter: false });
  const [showSettings, setShowSettings] = useState(false);
  const [showEligibility, setShowEligibility] = useState(false);
  const [showVotingFlow, setShowVotingFlow] = useState(false);

  // STT state
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);

  // TTS state
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const SUGGESTED_QUESTIONS = [
    { text: t.sq1, icon: "📝" }, { text: t.sq2, icon: "🏛️" },
    { text: t.sq3, icon: "✅" }, { text: t.sq4, icon: "📅" },
    { text: t.sq5, icon: "🗳️" }, { text: t.sq6, icon: "🪪" },
  ];

  // Firestore sync
  useEffect(() => {
    const q = query(collection(db, "chats", sessionId, "messages"), orderBy("timestamp", "asc"));
    const unsub = onSnapshot(q, (snap) => {
      setMessages(snap.docs.map((doc) => {
        const d = doc.data();
        return { id: doc.id, role: d.role as Role, content: d.content, timestamp: d.timestamp instanceof Timestamp ? d.timestamp.toDate() : new Date() };
      }));
      setIsSynced(true);
    });
    return () => unsub();
  }, [sessionId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  const saveMessage = useCallback(async (role: Role, content: string) => {
    await addDoc(collection(db, "chats", sessionId, "messages"), { role, content, timestamp: serverTimestamp() });
  }, [sessionId]);

  const sendMessage = async (text?: string) => {
    const messageText = (text ?? input).trim();
    if (!messageText || isLoading) return;
    setError(null); setInput(""); setIsLoading(true);
    await saveMessage("user", messageText);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 45000);
      const ctx = userContext.country || userContext.age ? {
        country: userContext.country || undefined,
        age: userContext.age ? parseInt(userContext.age) : undefined,
        is_first_time_voter: userContext.is_first_time_voter,
      } : undefined;
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ message: messageText, history: messages.map(({ role, content }) => ({ role, content })), language, mode, user_context: ctx }),
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        if (res.status === 429) throw new Error(`⏳ ${t.rateLimitError}`);
        throw new Error(e?.detail ?? `Server error: ${res.status}`);
      }
      const data = await res.json();
      const reply = data.response ?? "No response received.";
      await saveMessage("assistant", reply);

      // Auto-speak the response
      if (autoSpeak) {
        // ID will be assigned by Firestore; use a temp trigger via the last message
        try {
          await speakText(reply, language, () => setSpeakingMsgId(null));
        } catch { /* TTS failure is non-critical */ }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") setError(`⏱️ ${t.timeoutError}`);
      else setError(err instanceof Error ? err.message : t.serverError);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // ── STT: toggle recording ────────────────────────────────────────
  const handleMicClick = async () => {
    if (isProcessingAudio) return;

    if (isRecording) {
      // Stop → process
      setIsRecording(false);
      setIsProcessingAudio(true);
      setError(null);
      try {
        const blob = await stopRecording();
        const transcript = await recognizeSpeech(blob, language);
        if (transcript) setInput(transcript);
        else setError(t.sttError);
      } catch (err) {
        setError(err instanceof Error ? err.message : t.sttError);
      } finally {
        setIsProcessingAudio(false);
        inputRef.current?.focus();
      }
    } else {
      // Start recording
      try {
        await startRecording();
        setIsRecording(true);
        setError(null);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "";
        setError(msg.includes("Permission") || msg.includes("denied") ? t.micPermissionError : t.sttError);
      }
    }
  };

  // ── TTS: play/stop for a specific message bubble ─────────────────
  const handleSpeak = async (msgId: string, content: string) => {
    if (speakingMsgId === msgId) {
      stopSpeaking();
      setSpeakingMsgId(null);
      return;
    }
    setSpeakingMsgId(msgId);
    try {
      await speakText(content, language, () => setSpeakingMsgId(null));
    } catch {
      setError(t.ttsError);
      setSpeakingMsgId(null);
    }
  };

  // ── Toggle auto-speak ─────────────────────────────────────────────
  const toggleAutoSpeak = () => {
    if (autoSpeak) { stopSpeaking(); setSpeakingMsgId(null); }
    setAutoSpeak(!autoSpeak);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const isEmpty = isSynced && messages.length === 0;
  const currentLangLabel = LANGUAGES.find((l) => l.code === language)?.label ?? "EN";

  // Mic button visual state
  const micBg = isRecording ? "rgba(239,68,68,0.18)" : isProcessingAudio ? "rgba(99,102,241,0.15)" : "var(--bg-glass)";
  const micColor = isRecording ? "#ef4444" : isProcessingAudio ? "var(--accent-primary)" : "var(--text-muted)";
  const micTitle = isRecording ? t.recordingLabel : isProcessingAudio ? t.processingAudioLabel : t.voiceInputTooltip;

  return (
    <main style={{ display: "flex", flexDirection: "column", height: "100dvh", background: "var(--bg-primary)", position: "relative", overflow: "hidden" }}>
      <div aria-hidden style={{ position: "absolute", top: "-120px", left: "50%", transform: "translateX(-50%)", width: 600, height: 300, background: "radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

      {/* Translating banner */}
      {isTranslating && (
        <div style={{ position: "absolute", top: 60, left: "50%", transform: "translateX(-50%)", zIndex: 100, padding: "6px 16px", borderRadius: 20, background: "rgba(99,102,241,0.9)", color: "white", fontSize: 12, fontWeight: 500, display: "flex", alignItems: "center", gap: 6, backdropFilter: "blur(8px)" }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "white", display: "inline-block", animation: "pulse-dot 1s ease-in-out infinite" }} />
          {t.translatingLabel}
        </div>
      )}

      {/* Recording banner */}
      {isRecording && (
        <div style={{ position: "absolute", top: 60, left: "50%", transform: "translateX(-50%)", zIndex: 100, padding: "6px 16px", borderRadius: 20, background: "rgba(239,68,68,0.88)", color: "white", fontSize: 12, fontWeight: 500, display: "flex", alignItems: "center", gap: 6, backdropFilter: "blur(8px)" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "white", display: "inline-block", animation: "pulse-dot 0.8s ease-in-out infinite" }} />
          {t.recordingLabel}
        </div>
      )}

      {/* Header */}
      <header style={{ padding: "12px 20px", borderBottom: "1px solid var(--border)", background: "rgba(9,9,15,0.8)", backdropFilter: "blur(16px)", display: "flex", alignItems: "center", gap: 12, position: "relative", zIndex: 10 }}>
        <div style={{ width: 38, height: 38, borderRadius: 12, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px var(--accent-glow)", animation: "glow-pulse 3s ease-in-out infinite" }}>
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="white" strokeWidth="2" /></svg>
        </div>
        <div>
          <h1 style={{ fontSize: 17, fontWeight: 700, letterSpacing: "-0.02em" }}>{t.appName}</h1>
          <p style={{ fontSize: 11, color: "var(--text-secondary)" }}>{t.appSubtitle} • {mode === "simplified" ? `🧒 ${t.modeSimplifiedShort}` : `📚 ${t.modeStandardShort}`} • {currentLangLabel}</p>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
          {/* Auto-speak toggle */}
          <button
            onClick={toggleAutoSpeak}
            title={autoSpeak ? t.autoSpeakOn : t.autoSpeakOff}
            style={{
              ...headerBtnStyle,
              background: autoSpeak ? "rgba(139,92,246,0.15)" : "var(--bg-glass)",
              borderColor: autoSpeak ? "rgba(139,92,246,0.4)" : "var(--border)",
              color: autoSpeak ? "#8b5cf6" : "var(--text-secondary)",
            }}
          >
            {autoSpeak ? <SpeakerIcon active /> : <SpeakerOffIcon />}
          </button>
          <button onClick={() => setShowVotingFlow(true)} title={t.votingJourneyTooltip} style={headerBtnStyle}><CalendarIcon /></button>
          <button onClick={() => setShowEligibility(true)} title={t.eligibilityTooltip} style={headerBtnStyle}><CheckIcon /></button>
          <button onClick={() => setShowSettings(true)} title={t.settingsTooltip} style={headerBtnStyle}><SettingsIcon /></button>
          <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 16, marginLeft: 4, background: isSynced ? "rgba(34,197,94,0.08)" : "rgba(250,204,21,0.08)", border: `1px solid ${isSynced ? "rgba(34,197,94,0.2)" : "rgba(250,204,21,0.2)"}` }}>
            {isSynced ? (<><HistoryIcon /><span style={{ fontSize: 11, color: "#22c55e", fontWeight: 500 }}>{t.syncedLabel}</span></>) : (<span style={{ fontSize: 11, color: "#facc15", fontWeight: 500 }}>{t.syncingLabel}</span>)}
          </div>
        </div>
      </header>

      {/* Chat area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 16px", display: "flex", flexDirection: "column", gap: 20, position: "relative", zIndex: 1, maxWidth: 800, width: "100%", margin: "0 auto" }}>
        {isEmpty && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 28, textAlign: "center", padding: "32px 16px", animation: "fadeSlideUp 0.5s ease forwards" }}>
            <div>
              <div style={{ width: 68, height: 68, borderRadius: 20, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px", boxShadow: "0 8px 32px var(--accent-glow)" }}>
                <svg viewBox="0 0 24 24" fill="none" width="34" height="34"><path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="white" strokeWidth="2" /></svg>
              </div>
              <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 8 }}>{t.emptyTitle}</h2>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6, maxWidth: 420 }}>{t.emptyDesc}</p>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 460 }}>
              {[
                { label: `🗳️ ${t.votingJourneyChip}`, action: () => setShowVotingFlow(true) },
                { label: `✅ ${t.eligibilityChip}`, action: () => setShowEligibility(true) },
                { label: `⚙️ ${t.settingsChip}`, action: () => setShowSettings(true) },
              ].map((chip) => (
                <button key={chip.label} onClick={chip.action} style={{ padding: "8px 14px", borderRadius: 20, border: "1px solid var(--border)", background: "var(--bg-glass)", color: "var(--text-secondary)", fontSize: 13, cursor: "pointer", transition: "all 0.2s" }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-accent)"; e.currentTarget.style.color = "var(--text-primary)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
                >{chip.label}</button>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, width: "100%", maxWidth: 520 }}>
              {SUGGESTED_QUESTIONS.map((q) => (
                <button key={q.text} id={`suggestion-${q.text.replace(/\s+/g, "-").toLowerCase()}`} onClick={() => sendMessage(q.text)}
                  style={{ padding: "12px 14px", borderRadius: 12, border: "1px solid var(--border)", background: "var(--bg-glass)", color: "var(--text-secondary)", fontSize: 13, textAlign: "left", cursor: "pointer", transition: "all 0.2s", lineHeight: 1.4, display: "flex", gap: 8, alignItems: "flex-start" }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "var(--bg-glass-hover)"; e.currentTarget.style.borderColor = "var(--border-accent)"; e.currentTarget.style.color = "var(--text-primary)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "var(--bg-glass)"; e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
                >
                  <span style={{ fontSize: 16 }}>{q.icon}</span><span>{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} onSpeak={handleSpeak} speakingId={speakingMsgId} />
        ))}

        {isLoading && (
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start", animation: "fadeSlideUp 0.3s ease forwards" }}>
            <BotIcon />
            <div style={{ padding: "12px 16px", borderRadius: "18px 18px 18px 4px", background: "var(--bg-card)", border: "1px solid var(--border)" }}><TypingIndicator /></div>
          </div>
        )}

        {error && (
          <div role="alert" style={{ padding: "12px 16px", borderRadius: 12, background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)", color: "#f87171", fontSize: 14, display: "flex", alignItems: "center", gap: 8, animation: "fadeSlideUp 0.3s ease forwards" }}>
            ⚠️ {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div style={{ padding: "14px 16px", borderTop: "1px solid var(--border)", background: "rgba(9,9,15,0.9)", backdropFilter: "blur(16px)", position: "relative", zIndex: 10 }}>
        <div style={{ maxWidth: 800, margin: "0 auto", display: "flex", gap: 8, alignItems: "flex-end", background: "var(--bg-card)", border: `1px solid ${isRecording ? "rgba(239,68,68,0.5)" : "var(--border)"}`, borderRadius: 16, padding: "8px 8px 8px 16px", transition: "border-color 0.2s" }}>
          <textarea id="chat-input" ref={inputRef} value={input}
            onChange={(e) => { setInput(e.target.value); e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px"; }}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? t.recordingLabel : isProcessingAudio ? t.processingAudioLabel : t.inputPlaceholder}
            rows={1} disabled={isLoading || isRecording || isProcessingAudio}
            style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "var(--text-primary)", fontSize: 15, lineHeight: 1.5, resize: "none", fontFamily: "inherit", maxHeight: 140, overflowY: "auto", padding: 0 }}
          />

          {/* Mic button — Google STT */}
          <button
            onClick={handleMicClick}
            aria-label={micTitle}
            title={micTitle}
            disabled={isProcessingAudio}
            style={{ flexShrink: 0, width: 38, height: 38, borderRadius: 10, border: "none", background: micBg, color: micColor, display: "flex", alignItems: "center", justifyContent: "center", cursor: isProcessingAudio ? "wait" : "pointer", transition: "all 0.2s" }}
          >
            {isProcessingAudio
              ? <span style={{ width: 16, height: 16, border: "2px solid var(--accent-primary)", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.7s linear infinite" }} />
              : <MicIcon active={isRecording} />
            }
          </button>

          {/* Send button */}
          <button id="send-button" onClick={() => sendMessage()} disabled={isLoading || !input.trim()} aria-label={t.sendMsgLabel}
            style={{ flexShrink: 0, width: 38, height: 38, borderRadius: 10, border: "none", background: isLoading || !input.trim() ? "var(--bg-glass)" : "linear-gradient(135deg, #6366f1, #8b5cf6)", color: isLoading || !input.trim() ? "var(--text-muted)" : "white", display: "flex", alignItems: "center", justifyContent: "center", cursor: isLoading || !input.trim() ? "not-allowed" : "pointer", transition: "all 0.2s", boxShadow: isLoading || !input.trim() ? "none" : "0 4px 14px var(--accent-glow)" }}>
            <SendIcon />
          </button>
        </div>
        <p style={{ textAlign: "center", fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
          {t.disclaimer} <kbd style={{ padding: "1px 5px", borderRadius: 4, border: "1px solid var(--border)", fontSize: 10 }}>{t.pressEnter}</kbd> {t.pressEnterLabel}
        </p>
      </div>

      {/* Modals */}
      <SettingsPanel language={language} setLanguage={setLanguage} mode={mode} setMode={setMode} userContext={userContext} setUserContext={setUserContext} isOpen={showSettings} onClose={() => setShowSettings(false)} />
      <EligibilityChecker isOpen={showEligibility} onClose={() => setShowEligibility(false)} language={language} />
      <VotingFlow isOpen={showVotingFlow} onClose={() => setShowVotingFlow(false)} onAskAbout={sendMessage} />
    </main>
  );
}

// ── Outer shell — owns language state, wraps with TranslationProvider ──
export default function Home() {
  const [language, setLanguage] = useState("english");
  return (
    <TranslationProvider language={language}>
      <HomeContent language={language} setLanguage={setLanguage} />
    </TranslationProvider>
  );
}