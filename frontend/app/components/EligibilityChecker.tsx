"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "@/lib/TranslationContext";
import { translateText } from "@/lib/translate";

interface EligibilityCheckerProps {
  isOpen: boolean;
  onClose: () => void;
  language: string;
}

interface EligibilityResult {
  eligible: boolean;
  reason: string;
  next_steps: string[];
}

export default function EligibilityChecker({
  isOpen,
  onClose,
  language,
}: EligibilityCheckerProps) {
  const { t } = useTranslation();
  const [country, setCountry] = useState("india");
  const [age, setAge] = useState("");
  const [isCitizen, setIsCitizen] = useState(true);
  const [isResident, setIsResident] = useState(true);
  const [result, setResult] = useState<null | EligibilityResult>(null);
  const [loading, setLoading] = useState(false);

  // Re-translate result when language changes
  useEffect(() => {
    if (!result || language === "english") return;
    let cancelled = false;

    const retranslate = async () => {
      const translatedReason = await translateText(result.reason, language);
      const translatedSteps = await Promise.all(
        result.next_steps.map((s) => translateText(s, language))
      );
      if (!cancelled) {
        setResult({
          ...result,
          reason: translatedReason,
          next_steps: translatedSteps,
        });
      }
    };
    retranslate();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  const checkEligibility = async () => {
    if (!age) return;
    setLoading(true);
    setResult(null);
    try {
      const apiBase =
        process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/eligibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          country,
          age: parseInt(age),
          is_citizen: isCitizen,
          is_resident: isResident,
        }),
      });
      const data: EligibilityResult = await res.json();

      // Translate result if not English
      if (language !== "english") {
        const [translatedReason, ...translatedSteps] = await Promise.all([
          translateText(data.reason, language),
          ...data.next_steps.map((s) => translateText(s, language)),
        ]);
        setResult({ ...data, reason: translatedReason, next_steps: translatedSteps });
      } else {
        setResult(data);
      }
    } catch {
      setResult({
        eligible: false,
        reason: t.serverConnectionError,
        next_steps: [],
      });
    } finally {
      setLoading(false);
    }
  };

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
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: 20,
          padding: 28,
          width: "90%",
          maxWidth: 420,
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
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>
            🗳️ {t.eligibilityTitle}
          </h2>
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

        <p
          style={{
            fontSize: 13,
            color: "var(--text-secondary)",
            marginBottom: 16,
            lineHeight: 1.5,
          }}
        >
          {t.eligibilityDesc}
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "var(--bg-card)",
              color: "var(--text-primary)",
              fontSize: 14,
              outline: "none",
            }}
          >
            <option value="india">🇮🇳 {t.countryIndia}</option>
            <option value="usa">🇺🇸 {t.countryUSA}</option>
            <option value="uk">🇬🇧 {t.countryUK}</option>
          </select>

          <input
            type="number"
            placeholder={t.agePlaceholder}
            value={age}
            onChange={(e) => setAge(e.target.value)}
            min={1}
            max={120}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "var(--bg-card)",
              color: "var(--text-primary)",
              fontSize: 14,
              outline: "none",
            }}
          />

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontSize: 14,
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={isCitizen}
              onChange={(e) => setIsCitizen(e.target.checked)}
              style={{ accentColor: "var(--accent-primary)", width: 16, height: 16 }}
            />
            {t.citizenLabel}
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontSize: 14,
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={isResident}
              onChange={(e) => setIsResident(e.target.checked)}
              style={{ accentColor: "var(--accent-primary)", width: 16, height: 16 }}
            />
            {t.residentLabel}
          </label>

          <button
            onClick={checkEligibility}
            disabled={!age || loading}
            style={{
              padding: "12px",
              borderRadius: 12,
              fontWeight: 600,
              fontSize: 14,
              cursor: age && !loading ? "pointer" : "not-allowed",
              background:
                age && !loading
                  ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
                  : "var(--bg-glass)",
              color: age && !loading ? "white" : "var(--text-muted)",
              border: "none",
              transition: "all 0.2s",
            }}
          >
            {loading ? t.checkingBtn : t.checkBtn}
          </button>
        </div>

        {result && (
          <div
            style={{
              marginTop: 16,
              padding: 16,
              borderRadius: 12,
              background: result.eligible
                ? "rgba(34,197,94,0.08)"
                : "rgba(239,68,68,0.08)",
              border: `1px solid ${
                result.eligible
                  ? "rgba(34,197,94,0.25)"
                  : "rgba(239,68,68,0.25)"
              }`,
              animation: "fadeSlideUp 0.3s ease forwards",
            }}
          >
            <div
              style={{
                fontSize: 16,
                fontWeight: 700,
                marginBottom: 6,
                color: result.eligible ? "#22c55e" : "#f87171",
              }}
            >
              {result.eligible
                ? `✅ ${t.eligibleTitle}`
                : `❌ ${t.notEligibleTitle}`}
            </div>
            <p
              style={{
                fontSize: 13,
                color: "var(--text-secondary)",
                lineHeight: 1.5,
                marginBottom: 8,
              }}
            >
              {result.reason}
            </p>
            {result.next_steps?.length > 0 && (
              <div>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 4,
                  }}
                >
                  {t.nextStepsLabel}
                </div>
                {result.next_steps.map((step, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: 13,
                      color: "var(--text-secondary)",
                      paddingLeft: 12,
                      position: "relative",
                      marginBottom: 4,
                      lineHeight: 1.4,
                    }}
                  >
                    <span style={{ position: "absolute", left: 0 }}>•</span>{" "}
                    {step}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
