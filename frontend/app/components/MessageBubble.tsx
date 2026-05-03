"use client";

import { Message } from "@/lib/hooks/useChat";

interface MessageBubbleProps {
  msg: Message;
  isSimplified: boolean;
  speakingMsgId: string | null;
  onSpeak: (id: string, content: string) => void;
  speakMsgLabel: string;
  stopSpeakLabel: string;
}

/**
 * Renders a single chat message bubble.
 * Handles both user and assistant roles, with a TTS speak/stop button.
 */
export default function MessageBubble({
  msg,
  isSimplified,
  speakingMsgId,
  onSpeak,
  speakMsgLabel,
  stopSpeakLabel,
}: MessageBubbleProps) {
  const isUser = msg.role === "user";
  const isSpeaking = speakingMsgId === msg.id;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        gap: 8,
        alignItems: "flex-end",
      }}
    >
      {/* Avatar — AI only */}
      {!isUser && (
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            flexShrink: 0,
          }}
          aria-hidden="true"
        >
          🗳️
        </div>
      )}

      <div
        style={{
          maxWidth: "80%",
          padding: isSimplified ? "14px 18px" : "12px 16px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser
            ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
            : "var(--bg-glass)",
          border: isUser ? "none" : "1px solid var(--border)",
          color: isUser ? "white" : "var(--text-primary)",
          fontSize: isSimplified ? 16 : 14,
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          position: "relative",
        }}
      >
        {msg.content}

        {/* TTS speak button — AI only */}
        {!isUser && (
          <button
            onClick={() => onSpeak(msg.id, msg.content)}
            title={isSpeaking ? stopSpeakLabel : speakMsgLabel}
            aria-label={isSpeaking ? stopSpeakLabel : speakMsgLabel}
            aria-pressed={isSpeaking}
            style={{
              position: "absolute",
              bottom: 6,
              right: 8,
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 14,
              opacity: 0.6,
              padding: 2,
              transition: "opacity 0.2s",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.opacity = "1")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.opacity = "0.6")
            }
          >
            {isSpeaking ? "⏹" : "🔊"}
          </button>
        )}
      </div>
    </div>
  );
}
