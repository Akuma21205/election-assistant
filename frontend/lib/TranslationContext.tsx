"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { UI_STRINGS, UIStrings } from "./uiStrings";
import { translateUIStrings } from "./translate";

interface TranslationContextType {
  t: UIStrings;
  isTranslating: boolean;
}

const TranslationContext = createContext<TranslationContextType>({
  t: UI_STRINGS as unknown as UIStrings,
  isTranslating: false,
});

/**
 * Wrap your app (or page) with this provider and pass the currently
 * selected language string (e.g. "hindi", "french").
 * All children can call useTranslation() to get translated strings.
 */
export function TranslationProvider({
  language,
  children,
}: {
  language: string;
  children: ReactNode;
}) {
  const [t, setT] = useState<UIStrings>(UI_STRINGS as unknown as UIStrings);
  const [isTranslating, setIsTranslating] = useState(false);

  useEffect(() => {
    if (language === "english") {
      setT(UI_STRINGS as unknown as UIStrings);
      return;
    }

    setIsTranslating(true);
    translateUIStrings(language)
      .then(setT)
      .catch(() => setT(UI_STRINGS as unknown as UIStrings))
      .finally(() => setIsTranslating(false));
  }, [language]);

  return (
    <TranslationContext.Provider value={{ t, isTranslating }}>
      {children}
    </TranslationContext.Provider>
  );
}

/** Hook to consume translated strings in any component */
export function useTranslation() {
  return useContext(TranslationContext);
}
