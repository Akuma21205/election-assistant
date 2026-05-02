/**
 * Google Cloud Translation — routed through the backend proxy.
 * The API key is never exposed to the browser.
 */
import { UI_STRINGS, UIStrings } from "./uiStrings";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// BCP-47 codes for each language option
export const LANG_CODES: Record<string, string> = {
  english: "en",
  hindi: "hi",
  spanish: "es",
  french: "fr",
  tamil: "ta",
  telugu: "te",
  bengali: "bn",
  marathi: "mr",
  kannada: "kn",
};

// In-memory cache: languageCode → full translated UIStrings object
const cache = new Map<string, UIStrings>();

/** Decode HTML entities that Google Translate sometimes returns */
function decode(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");
}

/** Translate an array of plain-text strings in one proxy call */
export async function translateBatch(
  texts: string[],
  targetLang: string
): Promise<string[]> {
  const langCode = LANG_CODES[targetLang] ?? "en";
  if (langCode === "en") return texts;

  const res = await fetch(`${BACKEND}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: texts, target: langCode, source: "en" }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Translate proxy ${res.status}: ${err}`);
  }

  const data = await res.json();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return data.data.translations.map((t: any) => decode(t.translatedText));
}

/** Translate all UI strings, with caching. Returns cached copy if available. */
export async function translateUIStrings(
  targetLang: string
): Promise<UIStrings> {
  if (targetLang === "english") return UI_STRINGS as unknown as UIStrings;

  if (cache.has(targetLang)) return cache.get(targetLang)!;

  const keys = Object.keys(UI_STRINGS) as (keyof typeof UI_STRINGS)[];
  const values = keys.map((k) => UI_STRINGS[k]);

  try {
    const translated = await translateBatch(values, targetLang);
    const result = {} as UIStrings;
    keys.forEach((key, i) => {
      result[key] = translated[i] ?? UI_STRINGS[key];
    });
    cache.set(targetLang, result);
    return result;
  } catch (err) {
    console.error("[VoteGuide] Translation failed, falling back to English:", err);
    return UI_STRINGS as unknown as UIStrings;
  }
}

/** Translate a single arbitrary string (for dynamic content like eligibility results) */
export async function translateText(
  text: string,
  targetLang: string
): Promise<string> {
  if (targetLang === "english") return text;
  try {
    const [result] = await translateBatch([text], targetLang);
    return result ?? text;
  } catch {
    return text;
  }
}
