"use client";

/** Animated three-dot typing indicator shown while the AI is generating a response. */
export default function TypingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        padding: "12px 16px",
        borderRadius: 16,
        background: "var(--bg-glass)",
        border: "1px solid var(--border)",
        width: "fit-content",
        alignItems: "center",
      }}
      role="status"
      aria-label="AI is typing"
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "var(--accent-primary)",
            display: "inline-block",
            animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
            opacity: 0.7,
          }}
        />
      ))}
    </div>
  );
}
