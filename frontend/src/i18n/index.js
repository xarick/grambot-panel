import en from "./en.js";
import ru from "./ru.js";
import uz from "./uz.js";

const translations = { en, ru, uz };

export function getTranslations(lang) {
  return translations[lang] || translations.en;
}

export const SUPPORTED_LANGS = ["en", "ru", "uz"];
