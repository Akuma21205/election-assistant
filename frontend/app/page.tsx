"use client";

import { useState, useEffect, useRef, useCallback, KeyboardEvent } from "react";
import { useTranslation } from "@/lib/TranslationContext";
import { useChat } from "@/lib/hooks/useChat";
import { useSpeech } from "@/lib/hooks/useSpeech";
import SettingsPanel from "./components/SettingsPanel";
import EligibilityChecker from "./components/EligibilityChecker";
import VotingFlow from "./components/VotingFlow";
import TypingIndicator from "./components/TypingIndicator";
import MessageBubble from "./components/MessageBubble";
import {
  SettingsIcon,
  MicIcon,
  SendIcon,
  VolumeIcon,
  CheckIcon,
} from "./components/Icons";

// ── Keyframe for typing animation (injected via globals.css) ──
const QUICK_CHIPS = [
  "How do I register to vote? 🗳️",
  "Am I eligible to vote? ✅",
  "When is the next election? 📅",
  "Explain the voting process 📋",
  "What ID do I need to vote? 🪪",
];

export default function Home() {
  const { t } = useTranslation();

  // ── App state ────────────────────────────────────────────────────────────
  const [language, setLanguage] = useState("english");
  const [mode, setMode] = useState("standard");
  const [userContext, setUserContext] = useState({
    country: "",
    age: "",
    is_first_time_voter: false,
  });

  // ── Panel visibility ─────────────────────────────────────────────────────
  const [showSettings, setShowSettings] = useState(false);
  const [showEligibility, setShowEligibility] = useState(false);
  const [showVotingFlow, setShowVotingFlow] = useState(false);

  // ── Speech (STT/TTS) via the dedicated hook ──────────────────────────────
  const {
    isRecording,
    isProcessingAudio,
    handleMicClick,
    micBg,
    micColor,
    micTitle,
    autoSpeak,
    speakingMsgId,
    setSpeakingMsgId,
    handleSpeak,
    toggleAutoSpeak,
  } = useSpeech({
    language,
    onTranscript: (text) => {
      setInput(text);
    },
    onError: (msg) => setError(msg),
    focusInput: () => inputRef.current?.focus(),
    t: {
      recordingLabel: t.recordingLabel,
      processingAudioLabel: t.processingAudioLabel,
      voiceInputTooltip: t.voiceInputTooltip,
      micPermissionError: t.micPermissionError,
      sttError: t.sttError,
      ttsError: t.ttsError,
      autoSpeakOn: t.autoSpeakOn,
      autoSpeakOff: t.autoSpeakOff,
      speakMsgLabel: t.speakMsgLabel,
      stopSpeakLabel: t.stopSpeakLabel,
    },
  });

  // ── Chat logic via the dedicated hook ────────────────────────────────────
  const {
    messages,
    input,
    setInput,
    isLoading,
    error,
    setError,
    isSynced,
    bottomRef,
    inputRef,
    sendMessage,
  } = useChat({
    language,
    mode,
    userContext,
    autoSpeak,
    setSpeakingMsgId,
    t: {
      rateLimitError: t.rateLimitError,
      timeoutError: t.timeoutError,
      serverError: t.serverError,
    },
  });

  // ── Handle Enter key in textarea ─────────────────────────────────────────
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ── Ask-about helper for VotingFlow chips ────────────────────────────────
  const handleAskAbout = useCallback(
    (topic: string) => {
      sendMessage(topic);
    },
    [sendMessage]
  );

  const isSimplified = mode === "simplified";

  return (
    <main
      id="main-content"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100dvh",
        position: "relative",
        overflow: "hidden",
        background: "var(--bg-primary)",
      }}
    >
      {/* ── Modal overlays ───────────────────────────────────────────────── */}
      <SettingsPanel
        language={language}
        setLanguage={setLanguage}
        mode={mode}
        setMode={setMode}
        userContext={userContext}
        setUserContext={setUserContext}
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
      <EligibilityChecker
        isOpen={showEligibility}
        onClose={() => setShowEligibility(false)}
        language={language}
      />
      <VotingFlow
        isOpen={showVotingFlow}
        onClose={() => setShowVotingFlow(false)}
        onAskAbout={handleAskAbout}
      />

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-secondary)",
          backdropFilter: "blur(12px)",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24 }} aria-hidden="true">🗳️</span>
          <div>
            <h1
              style={{
                fontSize: 18,
                fontWeight: 700,
                background: "linear-gradient(135deg, #6366f1, #a78bfa)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              VoteGuide
            </h1>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              {isSynced ? (
                <>
                  <CheckIcon />
                  {t.syncedLabel}
                </>
              ) : (
                t.connectingLabel
              )}
            </div>
          </div>
        </div>

        {/* Header actions */}
        <div style={{ display: "flex", gap: 6 }}>
          {/* Auto-speak toggle */}
          <button
            id="auto-speak-toggle"
            onClick={toggleAutoSpeak}
            title={autoSpeak ? t.autoSpeakOn : t.autoSpeakOff}
            aria-label={autoSpeak ? t.autoSpeakOn : t.autoSpeakOff}
            aria-pressed={autoSpeak}
            style={{
              background: autoSpeak
                ? "rgba(99,102,241,0.15)"
                : "var(--bg-glass)",
              border: `1px solid ${autoSpeak ? "var(--accent-primary)" : "var(--border)"}`,
              borderRadius: 10,
              padding: "6px 10px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
              fontSize: 12,
              color: autoSpeak ? "var(--accent-primary)" : "var(--text-muted)",
            }}
          >
            <VolumeIcon />
            {autoSpeak ? t.autoSpeakOn : t.autoSpeakOff}
          </button>

          {/* Eligibility checker button */}
          <button
            id="eligibility-btn"
            onClick={() => setShowEligibility(true)}
            title={t.eligibilityBtn}
            aria-label={t.eligibilityBtn}
            style={{
              background: "var(--bg-glass)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              padding: "6px 10px",
              cursor: "pointer",
              fontSize: 12,
              color: "var(--text-muted)",
            }}
          >
            ✅ {t.eligibilityBtn}
          </button>

          {/* Voting journey button */}
          <button
            id="voting-flow-btn"
            onClick={() => setShowVotingFlow(true)}
            title={t.votingFlowBtn}
            aria-label={t.votingFlowBtn}
            style={{
              background: "var(--bg-glass)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              padding: "6px 10px",
              cursor: "pointer",
              fontSize: 12,
              color: "var(--text-muted)",
            }}
          >
            📊 {t.votingFlowBtn}
          </button>

          {/* Settings button */}
          <button
            id="settings-btn"
            onClick={() => setShowSettings(true)}
            title={t.settingsTitle}
            aria-label={t.settingsTitle}
            style={{
              background: "var(--bg-glass)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              padding: 8,
              cursor: "pointer",
              color: "var(--text-muted)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <SettingsIcon />
          </button>
        </div>
      </header>

      {/* ── Status banners ────────────────────────────────────────────────── */}
      {isRecording && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            background: "rgba(239,68,68,0.1)",
            borderBottom: "1px solid rgba(239,68,68,0.25)",
            padding: "6px 16px",
            fontSize: 12,
            color: "#f87171",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span
            style={{
              display: "inline-block",
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "#ef4444",
              animation: "pulse-dot 1s ease-in-out infinite",
            }}
          />
          {t.recordingLabel}
        </div>
      )}
      {isProcessingAudio && (
        <div
          role="status"
          style={{
            background: "rgba(99,102,241,0.08)",
            borderBottom: "1px solid rgba(99,102,241,0.15)",
            padding: "6px 16px",
            fontSize: 12,
            color: "var(--accent-primary)",
          }}
        >
          {t.processingAudioLabel}
        </div>
      )}

      {/* ── Message list ──────────────────────────────────────────────────── */}
      <div
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {/* Welcome state */}
        {messages.length === 0 && !isLoading && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              flex: 1,
              gap: 12,
              textAlign: "center",
              padding: "24px 16px",
            }}
          >
            <div style={{ fontSize: 48 }}>🗳️</div>
            <h2
              style={{
                fontSize: 22,
                fontWeight: 700,
                background: "linear-gradient(135deg, #6366f1, #a78bfa)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {t.welcomeTitle}
            </h2>
            <p
              style={{
                fontSize: 14,
                color: "var(--text-secondary)",
                maxWidth: 320,
                lineHeight: 1.6,
              }}
            >
              {t.welcomeDesc}
            </p>
            {/* Quick-start chips */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 8,
                justifyContent: "center",
                marginTop: 8,
              }}
            >
              {QUICK_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => sendMessage(chip)}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 20,
                    background: "var(--bg-glass)",
                    border: "1px solid var(--border)",
                    fontSize: 13,
                    color: "var(--text-secondary)",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor =
                      "var(--accent-primary)";
                    (e.currentTarget as HTMLButtonElement).style.color =
                      "var(--accent-primary)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor =
                      "var(--border)";
                    (e.currentTarget as HTMLButtonElement).style.color =
                      "var(--text-secondary)";
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            isSimplified={isSimplified}
            speakingMsgId={speakingMsgId}
            onSpeak={handleSpeak}
            speakMsgLabel={t.speakMsgLabel}
            stopSpeakLabel={t.stopSpeakLabel}
          />
        ))}

        {/* Typing indicator */}
        {isLoading && <TypingIndicator />}

        {/* Error banner */}
        {error && (
          <div
            role="alert"
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.2)",
              color: "#f87171",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span>⚠️</span>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              aria-label="Dismiss error"
              style={{
                marginLeft: "auto",
                background: "none",
                border: "none",
                color: "#f87171",
                cursor: "pointer",
                fontSize: 16,
              }}
            >
              ✕
            </button>
          </div>
        )}

        <div ref={bottomRef} aria-hidden="true" />
      </div>

      {/* ── Input area ────────────────────────────────────────────────────── */}
      <div
        style={{
          padding: "12px 16px",
          borderTop: "1px solid var(--border)",
          background: "var(--bg-secondary)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "flex-end",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 16,
            padding: "8px 8px 8px 14px",
          }}
        >
          {/* Mic button */}
          <button
            id="mic-btn"
            onClick={handleMicClick}
            disabled={isProcessingAudio}
            title={micTitle}
            aria-label={micTitle}
            aria-pressed={isRecording}
            style={{
              background: micBg,
              border: "1px solid var(--border)",
              borderRadius: 10,
              padding: 8,
              cursor: isProcessingAudio ? "wait" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: micColor,
              transition: "all 0.2s",
              flexShrink: 0,
            }}
          >
            <MicIcon />
          </button>

          {/* Text input */}
          <textarea
            ref={inputRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.inputPlaceholder}
            aria-label={t.inputPlaceholder}
            rows={1}
            style={{
              flex: 1,
              resize: "none",
              background: "none",
              border: "none",
              outline: "none",
              fontSize: 14,
              color: "var(--text-primary)",
              lineHeight: 1.5,
              padding: "4px 0",
              maxHeight: 120,
              overflowY: "auto",
            }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
            }}
          />

          {/* Send button */}
          <button
            id="send-btn"
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            aria-label={t.sendBtn}
            style={{
              background:
                input.trim() && !isLoading
                  ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
                  : "var(--bg-glass)",
              border: "none",
              borderRadius: 10,
              padding: 8,
              cursor: input.trim() && !isLoading ? "pointer" : "not-allowed",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color:
                input.trim() && !isLoading ? "white" : "var(--text-muted)",
              transition: "all 0.2s",
              flexShrink: 0,
            }}
          >
            <SendIcon />
          </button>
        </div>

        <div
          style={{
            textAlign: "center",
            fontSize: 11,
            color: "var(--text-muted)",
            marginTop: 6,
          }}
        >
          {t.footer}
        </div>
      </div>
    </main>
  );
}