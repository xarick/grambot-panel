import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { getTranslations, SUPPORTED_LANGS } from "@/i18n/index.js";

function interpolate(str, vars) {
  return str.replace(/\{\{(\w+)\}\}/g, (_, key) => (vars[key] !== undefined ? vars[key] : `{{${key}}}`));
}

const TranslationContext = createContext(null);

export function TranslationProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    const stored = localStorage.getItem("lang");
    return SUPPORTED_LANGS.includes(stored) ? stored : "en";
  });

  const translations = useMemo(() => getTranslations(lang), [lang]);

  const setLanguage = useCallback((newLang) => {
    if (!SUPPORTED_LANGS.includes(newLang)) return;
    localStorage.setItem("lang", newLang);
    setLangState(newLang);
  }, []);

  const t = useCallback(
    (key, vars) => {
      const raw = translations[key] || key;
      return vars ? interpolate(raw, vars) : raw;
    },
    [translations]
  );

  const value = useMemo(
    () => ({ t, lang, setLanguage, supportedLangs: SUPPORTED_LANGS }),
    [t, lang, setLanguage]
  );

  return <TranslationContext.Provider value={value}>{children}</TranslationContext.Provider>;
}

export function useTranslation() {
  const ctx = useContext(TranslationContext);
  if (!ctx) {
    throw new Error("useTranslation must be used within TranslationProvider");
  }
  return ctx;
}
