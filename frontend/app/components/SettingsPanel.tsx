"use client";

import { useState } from "react";
import { GlobeIcon, SparkleIcon, UserIcon } from "./Icons";
import { useTranslation } from "@/lib/TranslationContext";

export const LANGUAGES = [
  { code: "english", label: "English", flag: "🇬🇧" },
  { code: "hindi", label: "हिन्दी", flag: "🇮🇳" },
  { code: "spanish", label: "Español", flag: "🇪🇸" },
  { code: "french", label: "Français", flag: "🇫🇷" },
  { code: "tamil", label: "தமிழ்", flag: "🇮🇳" },
  { code: "telugu", label: "తెలుగు", flag: "🇮🇳" },
  { code: "bengali", label: "বাংলা", flag: "🇮🇳" },
  { code: "marathi", label: "मराठी", flag: "🇮🇳" },
  { code: "kannada", label: "ಕನ್ನಡ", flag: "🇮🇳" },
];

interface SettingsPanelProps {
  language: string;
  setLanguage: (lang: string) => void;
  mode: string;
  setMode: (mode: string) => void;
  userContext: { country: string; age: string; is_first_time_voter: boolean };
  setUserContext: (ctx: {
    country: string;
    age: string;
    is_first_time_voter: boolean;
  }) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsPanel({
  language,
  setLanguage,
  mode,
  setMode,
  userContext,
  setUserContext,
  isOpen,
  onClose,
}: SettingsPanelProps) {
  const { t, isTranslating } = useTranslation();
  const [localLang, setLocalLang] = useState(language);

  if (!isOpen) return null;

  const handleLangSelect = (code: string) => {
    setLocalLang(code);
    setLanguage(code);
  };

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
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: 20,
          padding: 28,
          width: "90%",
          maxWidth: 440,
          animation: "scaleIn 0.25s ease forwards",
          maxHeight: "80vh",
          overflowY: "auto",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 24,
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>{t.settingsTitle}</h2>
          <button
            onClick={onClose}
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

        {/* Translating indicator */}
        {isTranslating && (
          <div
            style={{
              marginBottom: 16,
              padding: "8px 12px",
              borderRadius: 8,
              background: "rgba(99,102,241,0.1)",
              border: "1px solid rgba(99,102,241,0.25)",
              fontSize: 12,
              color: "var(--accent-primary)",
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
                background: "var(--accent-primary)",
                animation: "pulse-dot 1s ease-in-out infinite",
              }}
            />
            {t.translatingLabel}
          </div>
        )}

        {/* Language Selection */}
        <div style={{ marginBottom: 20 }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: "var(--text-secondary)",
              marginBottom: 8,
              fontWeight: 600,
            }}
          >
            <GlobeIcon /> {t.languageLabel}
          </label>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}
          >
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLangSelect(lang.code)}
                style={{
                  padding: "8px 10px",
                  borderRadius: 10,
                  fontSize: 12,
                  border: `1px solid ${
                    localLang === lang.code
                      ? "var(--accent-primary)"
                      : "var(--border)"
                  }`,
                  background:
                    localLang === lang.code
                      ? "rgba(99,102,241,0.15)"
                      : "var(--bg-glass)",
                  color:
                    localLang === lang.code
                      ? "var(--accent-primary)"
                      : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "center",
                  transition: "all 0.15s",
                }}
              >
                {lang.flag} {lang.label}
              </button>
            ))}
          </div>
        </div>

        {/* Explanation Mode */}
        <div style={{ marginBottom: 20 }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: "var(--text-secondary)",
              marginBottom: 8,
              fontWeight: 600,
            }}
          >
            <SparkleIcon /> {t.modeLabel}
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            {[
              {
                value: "standard",
                label: `📚 ${t.standardModeLabel}`,
                desc: t.standardModeDesc,
              },
              {
                value: "simplified",
                label: `🧒 ${t.simplifiedModeLabel}`,
                desc: t.simplifiedModeDesc,
              },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setMode(opt.value)}
                style={{
                  flex: 1,
                  padding: "12px 14px",
                  borderRadius: 12,
                  textAlign: "left",
                  border: `1px solid ${
                    mode === opt.value ? "var(--accent-primary)" : "var(--border)"
                  }`,
                  background:
                    mode === opt.value
                      ? "rgba(99,102,241,0.15)"
                      : "var(--bg-glass)",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color:
                      mode === opt.value
                        ? "var(--accent-primary)"
                        : "var(--text-primary)",
                  }}
                >
                  {opt.label}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    marginTop: 2,
                  }}
                >
                  {opt.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* User Profile */}
        <div>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: "var(--text-secondary)",
              marginBottom: 8,
              fontWeight: 600,
            }}
          >
            <UserIcon /> {t.profileLabel}
          </label>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <select
              value={userContext.country}
              onChange={(e) =>
                setUserContext({ ...userContext, country: e.target.value })
              }
              style={{
                padding: "10px 14px",
                borderRadius: 10,
                fontSize: 14,
                border: "1px solid var(--border)",
                background: "var(--bg-card)",
                color: "var(--text-primary)",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="">{t.selectCountry}</option>
              <option value="india">🇮🇳 {t.countryIndia}</option>
              <option value="usa">🇺🇸 {t.countryUSA}</option>
              <option value="uk">🇬🇧 {t.countryUK}</option>
            </select>

            <input
              type="number"
              placeholder={t.agePlaceholder}
              value={userContext.age}
              onChange={(e) =>
                setUserContext({ ...userContext, age: e.target.value })
              }
              min={1}
              max={120}
              style={{
                padding: "10px 14px",
                borderRadius: 10,
                fontSize: 14,
                border: "1px solid var(--border)",
                background: "var(--bg-card)",
                color: "var(--text-primary)",
                outline: "none",
              }}
            />

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                borderRadius: 10,
                border: "1px solid var(--border)",
                background: "var(--bg-glass)",
                cursor: "pointer",
                fontSize: 14,
                color: "var(--text-secondary)",
              }}
            >
              <input
                type="checkbox"
                checked={userContext.is_first_time_voter}
                onChange={(e) =>
                  setUserContext({
                    ...userContext,
                    is_first_time_voter: e.target.checked,
                  })
                }
                style={{
                  accentColor: "var(--accent-primary)",
                  width: 16,
                  height: 16,
                }}
              />
              {t.firstTimeVoter}
            </label>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            marginTop: 20,
            width: "100%",
            padding: "12px",
            borderRadius: 12,
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "white",
            border: "none",
            fontWeight: 600,
            fontSize: 14,
            cursor: "pointer",
            transition: "all 0.2s",
          }}
        >
          {t.saveClose}
        </button>
      </div>
    </div>
  );
}
