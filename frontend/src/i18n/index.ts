import { en } from "./en";
import type { Language, Messages } from "./types";
import { zh } from "./zh";

export const messages: Record<Language, Messages> = { en, zh };

export function getInitialLanguage(): Language {
  const stored = window.localStorage.getItem("vbi-language");
  return stored === "en" || stored === "zh" ? stored : "zh";
}

export function persistLanguage(language: Language) {
  window.localStorage.setItem("vbi-language", language);
}

export type { Language, Messages };
