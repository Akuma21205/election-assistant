"use client";
import { useState, useCallback } from "react";
import {
  startRecording,
  stopRecording,
  recognizeSpeech,
  speakText,
  stopSpeaking,
} from "@/lib/speech";

interface UseSpeechOptions {
  language: string;
  onTranscript: (text: string) => void;
  onError: (msg: string) => void;
  focusInput: () => void;
  t: {
    recordingLabel: string;
    processingAudioLabel: string;
    voiceInputTooltip: string;
    micPermissionError: string;
    sttError: string;
    ttsError: string;
    autoSpeakOn: string;
    autoSpeakOff: string;
    speakMsgLabel: string;
    stopSpeakLabel: string;
  };
}

export function useSpeech(opts: UseSpeechOptions) {
  const { language, onTranscript, onError, focusInput, t } = opts;

  // STT state
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);

  // TTS state
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  // ── STT: toggle recording ────────────────────────────────
  const handleMicClick = useCallback(async () => {
    if (isProcessingAudio) return;

    if (isRecording) {
      setIsRecording(false);
      setIsProcessingAudio(true);
      try {
        const blob = await stopRecording();
        const transcript = await recognizeSpeech(blob, language);
        if (transcript) onTranscript(transcript);
        else onError(t.sttError);
      } catch (err) {
        onError(err instanceof Error ? err.message : t.sttError);
      } finally {
        setIsProcessingAudio(false);
        focusInput();
      }
    } else {
      try {
        await startRecording();
        setIsRecording(true);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "";
        onError(
          msg.includes("Permission") || msg.includes("denied")
            ? t.micPermissionError
            : t.sttError
        );
      }
    }
  }, [isRecording, isProcessingAudio, language, onTranscript, onError, focusInput, t]);

  // ── TTS: play/stop for a specific message bubble ─────────
  const handleSpeak = useCallback(
    async (msgId: string, content: string) => {
      if (speakingMsgId === msgId) {
        stopSpeaking();
        setSpeakingMsgId(null);
        return;
      }
      setSpeakingMsgId(msgId);
      try {
        await speakText(content, language, () => setSpeakingMsgId(null));
      } catch {
        onError(t.ttsError);
        setSpeakingMsgId(null);
      }
    },
    [speakingMsgId, language, onError, t.ttsError]
  );

  // ── Toggle auto-speak ────────────────────────────────────
  const toggleAutoSpeak = useCallback(() => {
    if (autoSpeak) {
      stopSpeaking();
      setSpeakingMsgId(null);
    }
    setAutoSpeak((v) => !v);
  }, [autoSpeak]);

  // ── Mic button visual state ──────────────────────────────
  const micBg = isRecording
    ? "rgba(239,68,68,0.18)"
    : isProcessingAudio
    ? "rgba(99,102,241,0.15)"
    : "var(--bg-glass)";

  const micColor = isRecording
    ? "#ef4444"
    : isProcessingAudio
    ? "var(--accent-primary)"
    : "var(--text-muted)";

  const micTitle = isRecording
    ? t.recordingLabel
    : isProcessingAudio
    ? t.processingAudioLabel
    : t.voiceInputTooltip;

  return {
    // STT
    isRecording,
    isProcessingAudio,
    handleMicClick,
    micBg,
    micColor,
    micTitle,
    // TTS
    autoSpeak,
    speakingMsgId,
    setSpeakingMsgId,
    handleSpeak,
    toggleAutoSpeak,
  };
}
