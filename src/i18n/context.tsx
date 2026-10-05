import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { pt, zh, type TranslationKey } from "./catalog";

export type Locale = "pt" | "zh";
type Interpolation = Record<string, string | number>;
type I18nValue = { locale: Locale; setLocale: (locale: Locale) => void; t: (key: TranslationKey, values?: Interpolation) => string };
const localeStorageKey = "pesquisaclima:locale";
const I18nContext = createContext<I18nValue | null>(null);

function readSavedLocale(): Locale {
  try {
    return window.localStorage.getItem(localeStorageKey) === "zh" ? "zh" : "pt";
  } catch {
    return "pt";
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("pt");

  useEffect(() => {
    const savedLocale = readSavedLocale();
    setLocaleState(savedLocale);
    document.documentElement.lang = savedLocale === "zh" ? "zh-CN" : "pt-BR";
    document.title = "Pesquisa de Clima";
    const syncLocale = (event: StorageEvent) => {
      if (event.key === localeStorageKey) {
        const nextLocale = event.newValue === "zh" ? "zh" : "pt";
        setLocaleState(nextLocale);
        document.documentElement.lang = nextLocale === "zh" ? "zh-CN" : "pt-BR";
        document.title = "Pesquisa de Clima";
      }
    };
    window.addEventListener("storage", syncLocale);
    return () => window.removeEventListener("storage", syncLocale);
  }, []);

  const setLocale = useCallback((nextLocale: Locale) => {
    setLocaleState(nextLocale);
    document.documentElement.lang = nextLocale === "zh" ? "zh-CN" : "pt-BR";
    document.title = "Pesquisa de Clima";
    try {
      window.localStorage.setItem(localeStorageKey, nextLocale);
    } catch {
      // Language remains usable for this page even when storage is unavailable.
    }
  }, []);

  const t = useCallback((key: TranslationKey, values: Interpolation = {}) => {
    const template = (locale === "zh" ? zh[key] : undefined) ?? pt[key];
    return template.replace(/\{(\w+)\}/g, (_match, name: string) => String(values[name] ?? ""));
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n deve ser usado dentro de LanguageProvider.");
  return context;
}
