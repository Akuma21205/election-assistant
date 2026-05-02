/**
 * Google Cloud Speech-to-Text & Text-to-Speech utilities.
 * All API calls are routed through the backend proxy — the API key
 * is never exposed to the browser.
 */

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Language → BCP-47 region code for Speech APIs ────────────────
export const SPEECH_LANG_CODES: Record<string, string> = {
  english: "en-US",
  hindi: "hi-IN",
  spanish: "es-ES",
  french: "fr-FR",
  tamil: "ta-IN",
  telugu: "te-IN",
  bengali: "bn-IN",
  marathi: "mr-IN",
  kannada: "kn-IN",
};

// ── Recording state ───────────────────────────────────────────────
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: BlobPart[] = [];

/** Start capturing audio from the microphone */
export async function startRecording(): Promise<void> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  audioChunks = [];

  const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : "audio/webm";

  mediaRecorder = new MediaRecorder(stream, { mimeType });
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data);
  };
  mediaRecorder.start(100);
}

/** Stop recording and return the audio Blob */
export async function stopRecording(): Promise<Blob> {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) { reject(new Error("No active recorder")); return; }
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      mediaRecorder?.stream.getTracks().forEach((t) => t.stop());
      resolve(blob);
    };
    mediaRecorder.stop();
  });
}

/** Convert Blob → base64 string */
async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      resolve(dataUrl.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/** Send recorded audio to backend STT proxy → returns transcript string */
export async function recognizeSpeech(
  audioBlob: Blob,
  language: string
): Promise<string> {
  const base64Audio = await blobToBase64(audioBlob);
  const langCode = SPEECH_LANG_CODES[language] ?? "en-US";

  const res = await fetch(`${BACKEND}/api/stt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audio_base64: base64Audio,
      language_code: langCode,
      sample_rate: 48000,
      encoding: "WEBM_OPUS",
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`STT proxy ${res.status}: ${err}`);
  }

  const data = await res.json();
  return data.results?.[0]?.alternatives?.[0]?.transcript ?? "";
}

/** Strip markdown so TTS reads clean prose */
function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s/g, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/`[^`]+`/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^\s*[-*+]\s/gm, "")
    .replace(/^\s*\d+\.\s/gm, "")
    .replace(/\n{2,}/g, " ")
    .trim();
}

let currentAudio: HTMLAudioElement | null = null;

/** Stop any currently playing TTS audio */
export function stopSpeaking(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
}

/** Send text to backend TTS proxy → play MP3 audio. Returns the Audio element. */
export async function speakText(
  text: string,
  language: string,
  onEnd?: () => void
): Promise<HTMLAudioElement | null> {
  stopSpeaking();

  const clean = stripMarkdown(text).slice(0, 4800);
  if (!clean) return null;

  const langCode = SPEECH_LANG_CODES[language] ?? "en-US";

  const res = await fetch(`${BACKEND}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: clean, language_code: langCode }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`TTS proxy ${res.status}: ${err}`);
  }

  const data = await res.json();
  if (!data.audioContent) throw new Error("No audio content returned");

  const audio = new Audio(`data:audio/mp3;base64,${data.audioContent}`);
  currentAudio = audio;
  audio.onended = () => {
    currentAudio = null;
    onEnd?.();
  };
  await audio.play();
  return audio;
}

/** True if TTS is currently playing */
export function isSpeaking(): boolean {
  return currentAudio !== null && !currentAudio.paused;
}
