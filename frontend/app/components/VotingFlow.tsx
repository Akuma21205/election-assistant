"use client";

import { useEffect, useRef } from "react";
import { useTranslation } from "@/lib/TranslationContext";

interface VotingFlowProps {
  isOpen: boolean;
  onClose: () => void;
  onAskAbout: (topic: string) => void;
}

export default function VotingFlow({
  isOpen,
  onClose,
  onAskAbout,
}: VotingFlowProps) {
  const { t } = useTranslation();
  const panelRef = useRef<HTMLDivElement>(null);

  const STEPS = [
    { icon: "📋", title: t.step1Title, desc: t.step1Desc },
    { icon: "🪪", title: t.step2Title, desc: t.step2Desc },
    { icon: "✅", title: t.step3Title, desc: t.step3Desc },
    { icon: "📍", title: t.step4Title, desc: t.step4Desc },
    { icon: "🗳️", title: t.step5Title, desc: t.step5Desc },
    { icon: "📊", title: t.step6Title, desc: t.step6Desc },
  ];

  // Focus trap + Escape key
  useEffect(() => {
    if (!isOpen) return;

    const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
      'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusable?.[0]?.focus();

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key !== "Tab" || !focusable || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.6)",
        backdropFilter: "blur(4px)",
        animation: "fadeIn 0.2s ease",
      }}
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="voting-flow-dialog-title"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: 20,
          padding: 28,
          width: "90%",
          maxWidth: 500,
          animation: "scaleIn 0.25s ease forwards",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <h2 id="voting-flow-dialog-title" style={{ fontSize: 18, fontWeight: 700 }}>
            🗳️ {t.votingJourneyTitle}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close voting journey"
            style={{
              background: "var(--bg-glass)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              width: 32,
              height: 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-secondary)",
              cursor: "pointer",
              fontSize: 16,
            }}
          >
            ✕
          </button>
        </div>

        <p
          style={{
            fontSize: 13,
            color: "var(--text-secondary)",
            marginBottom: 20,
            lineHeight: 1.5,
          }}
        >
          {t.votingJourneyDesc}
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {STEPS.map((step, i) => (
            <div key={i}>
              <button
                onClick={() => {
                  onClose();
                  onAskAbout(
                    `Tell me about the "${step.title}" step in the voting process. ${step.desc}`
                  );
                }}
                aria-label={`Ask about step ${i + 1}: ${step.title}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  width: "100%",
                  padding: "14px 16px",
                  borderRadius: 12,
                  border: "1px solid var(--border)",
                  background: "var(--bg-glass)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background =
                    "var(--bg-glass-hover)";
                  (e.currentTarget as HTMLButtonElement).style.borderColor =
                    "var(--border-accent)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background =
                    "var(--bg-glass)";
                  (e.currentTarget as HTMLButtonElement).style.borderColor =
                    "var(--border)";
                }}
              >
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 12,
                    background: "rgba(99,102,241,0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 20,
                    flexShrink: 0,
                  }}
                  aria-hidden="true"
                >
                  {step.icon}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {t.stepLabel} {i + 1}: {step.title}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-muted)",
                      marginTop: 2,
                    }}
                  >
                    {step.desc}
                  </div>
                </div>
                <div
                  style={{
                    marginLeft: "auto",
                    color: "var(--text-muted)",
                    fontSize: 14,
                  }}
                  aria-hidden="true"
                >
                  →
                </div>
              </button>
              {i < STEPS.length - 1 && (
                <div
                  style={{
                    width: 2,
                    height: 12,
                    background: "var(--border)",
                    marginLeft: 35,
                  }}
                  aria-hidden="true"
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
