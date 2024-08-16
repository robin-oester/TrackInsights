import i18next from "i18next";
import { initReactI18next } from "react-i18next";

import translationEnglish from "./translation/en.json";
import translationGerman from "./translation/de.json";

const resources = {
  en: {
    translation: translationEnglish
  },
  de: {
    translation: translationGerman,
  }
}

void i18next
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    lng: "en",
  });
