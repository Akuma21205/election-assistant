"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { db } from "@/lib/firebase";
import {
  collection, addDoc, orderBy, query, onSnapshot,
  serverTimestamp, Timestamp,
} from "firebase/firestore";
import { speakText } from "@/lib/speech";

type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
}

function getSessionId(): string {
  const key = "voteguide_session";
  let id = sessionStorage.getItem(key);
  if (!id) { id = crypto.randomUUID(); sessionStorage.setItem(key, id); }
  return id;
}

interface UseChatOptions {
  language: string;
  mode: string;
  userContext: { country: string; age: string; is_first_time_voter: boolean };
  autoSpeak: boolean;
  setSpeakingMsgId: (id: string | null) => void;
  t: { rateLimitError: string; timeoutError: string; serverError: string };
}

export function useChat(opts: UseChatOptions) {
  const { language, mode, userContext, autoSpeak, setSpeakingMsgId, t } = opts;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState<string>(() =>
    typeof window !== "undefined" ? getSessionId() : crypto.randomUUID()
  );
  const [isSynced, setIsSynced] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Firestore real-time sync
  useEffect(() => {
    const q = query(
      collection(db, "chats", sessionId, "messages"),
      orderBy("timestamp", "asc")
    );
    const unsub = onSnapshot(q, (snap) => {
      setMessages(
        snap.docs.map((doc) => {
          const d = doc.data();
          return {
            id: doc.id,
            role: d.role as Role,
            content: d.content,
            timestamp:
              d.timestamp instanceof Timestamp
                ? d.timestamp.toDate()
                : new Date(),
          };
        })
      );
      setIsSynced(true);
    });
    return () => unsub();
  }, [sessionId]);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const saveMessage = useCallback(
    async (role: Role, content: string) => {
      await addDoc(collection(db, "chats", sessionId, "messages"), {
        role,
        content,
        timestamp: serverTimestamp(),
      });
    },
    [sessionId]
  );

  const sendMessage = async (text?: string) => {
    const messageText = (text ?? input).trim();
    if (!messageText || isLoading) return;
    setError(null);
    setInput("");
    setIsLoading(true);

    await saveMessage("user", messageText);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 45000);
      const ctx =
        userContext.country || userContext.age
          ? {
              country: userContext.country || undefined,
              age: userContext.age ? parseInt(userContext.age) : undefined,
              is_first_time_voter: userContext.is_first_time_voter,
            }
          : undefined;
      const apiBase =
        process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          message: messageText,
          history: messages.map(({ role, content }) => ({ role, content })),
          language,
          mode,
          user_context: ctx,
        }),
      });
      clearTimeout(timeout);

      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        if (res.status === 429)
          throw new Error(`⏳ ${t.rateLimitError}`);
        throw new Error(e?.detail ?? `Server error: ${res.status}`);
      }
      const data = await res.json();
      const reply = data.response ?? "No response received.";
      await saveMessage("assistant", reply);

      // Auto-speak the response
      if (autoSpeak) {
        try {
          await speakText(reply, language, () => setSpeakingMsgId(null));
        } catch {
          /* TTS failure is non-critical */
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError")
        setError(`⏱️ ${t.timeoutError}`);
      else setError(err instanceof Error ? err.message : t.serverError);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return {
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
  };
}
