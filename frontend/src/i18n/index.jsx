/**
 * I18nContext — contexte React pour la langue.
 */

import { createContext, useContext, useState, useCallback } from "react";
import { TRANSLATIONS } from "./translations.js";

const I18nContext = createContext(null);

function getNested(obj, path) {
  return path.split(".").reduce((o, k) => (o ? o[k] : undefined), obj);
}

export function I18nProvider({ children }) {
  const [lang, setLang] = useState("en");

  const t = useCallback(
    (key, fallback, data) => {
      const parts = getNested(TRANSLATIONS, key);
      if (parts == null) return fallback ?? key;
      let text = parts[lang] ?? parts.fr ?? fallback ?? key;
      if (typeof text === "function") text = text();
      if (data && typeof data === "object") {
        text = String(text).replace(/\{(\w+)\}/g, (_, k) => String(data[k] ?? `{${k}}`));
      }
      return text;
    },
    [lang]
  );

  const toggle = useCallback(() => {
    setLang((l) => (l === "fr" ? "en" : "fr"));
  }, []);

  return (
    <I18nContext.Provider value={{ lang, t, toggle }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
