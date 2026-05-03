"use client";

import { Message } from "@/lib/hooks/useChat";
import { useMemo } from "react";

interface MessageBubbleProps {
  msg: Message;
  isSimplified: boolean;
  speakingMsgId: string | null;
  onSpeak: (id: string, content: string) => void;
  speakMsgLabel: string;
  stopSpeakLabel: string;
}

/**
 * Parse basic markdown into React elements.
 * Handles: bold, italic, inline code, headers, links, and lists.
 */
function parseMarkdown(text: string): (string | JSX.Element)[] {
  const lines = text.split("\n");
  const elements: (string | JSX.Element)[] = [];

  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let listKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const Tag = listType === "ol" ? "ol" : "ul";
    elements.push(
      <Tag key={`list-${listKey++}`} style={{
        margin: "6px 0",
        paddingLeft: 20,
        lineHeight: 1.6,
      }}>
        {listItems.map((item, i) => (
          <li key={i}>{formatInline(item)}</li>
        ))}
      </Tag>
    );
    listItems = [];
    listType = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Headers
    const headerMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (headerMatch) {
      flushList();
      const level = headerMatch[1].length;
      const sizes = { 1: 18, 2: 16, 3: 14 };
      elements.push(
        <div key={`h-${i}`} style={{
          fontSize: sizes[level as 1 | 2 | 3] || 14,
          fontWeight: 700,
          margin: "10px 0 4px",
          color: "var(--accent-primary)",
        }}>
          {formatInline(headerMatch[2])}
        </div>
      );
      continue;
    }

    // Unordered list
    const ulMatch = line.match(/^\s*[-*+]\s+(.+)$/);
    if (ulMatch) {
      if (listType === "ol") flushList();
      listType = "ul";
      listItems.push(ulMatch[1]);
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^\s*\d+\.\s+(.+)$/);
    if (olMatch) {
      if (listType === "ul") flushList();
      listType = "ol";
      listItems.push(olMatch[1]);
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      flushList();
      elements.push(<div key={`br-${i}`} style={{ height: 8 }} />);
      continue;
    }

    // Horizontal rule / separator
    if (/^---+$/.test(line.trim())) {
      flushList();
      elements.push(
        <hr key={`hr-${i}`} style={{
          border: "none",
          borderTop: "1px solid var(--border)",
          margin: "8px 0",
        }} />
      );
      continue;
    }

    // Plain text
    flushList();
    elements.push(
      <span key={`p-${i}`} style={{ display: "block", margin: "2px 0" }}>
        {formatInline(line)}
      </span>
    );
  }

  flushList();
  return elements;
}

/**
 * Format inline markdown: **bold**, *italic*, `code`, [links](url)
 */
function formatInline(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  // Combined regex for bold, italic, code, and links
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\))/g;
  let lastIndex = 0;
  let match;
  let idx = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2]) {
      // Bold
      parts.push(
        <strong key={`b-${idx++}`} style={{ fontWeight: 600 }}>
          {match[2]}
        </strong>
      );
    } else if (match[3]) {
      // Italic
      parts.push(
        <em key={`i-${idx++}`} style={{ fontStyle: "italic" }}>
          {match[3]}
        </em>
      );
    } else if (match[4]) {
      // Code
      parts.push(
        <code key={`c-${idx++}`} style={{
          background: "rgba(99,102,241,0.12)",
          padding: "1px 5px",
          borderRadius: 4,
          fontSize: "0.9em",
          fontFamily: "'Fira Code', 'Consolas', monospace",
        }}>
          {match[4]}
        </code>
      );
    } else if (match[5] && match[6]) {
      // Link
      parts.push(
        <a
          key={`a-${idx++}`}
          href={match[6]}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: "var(--accent-primary)",
            textDecoration: "underline",
            textUnderlineOffset: 2,
          }}
        >
          {match[5]}
        </a>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

/**
 * Renders a single chat message bubble with markdown parsing.
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

  // Memoize markdown parsing for performance
  const renderedContent = useMemo(() => {
    if (isUser) return msg.content;
    return parseMarkdown(msg.content);
  }, [msg.content, isUser]);

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
          wordBreak: "break-word",
          position: "relative",
        }}
      >
        {isUser ? (
          <span style={{ whiteSpace: "pre-wrap" }}>{renderedContent}</span>
        ) : (
          <div>{renderedContent}</div>
        )}

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
