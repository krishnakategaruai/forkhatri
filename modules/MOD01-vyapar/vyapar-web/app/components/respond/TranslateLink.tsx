"use client";

// [FE1 — 2026-09-29, critique N5] "Translate" on a free-text note written
// in another language than the reader's (a Telugu applicant, a Hindi
// poster). Shown only when all of these hold:
//  - the server says which language the note is in (`message_language`,
//    backend A) — until that field exists nothing renders;
//  - it differs from the app language;
//  - a translation service is configured: NEXT_PUBLIC_TRANSLATE_URL_TEMPLATE
//    with {sl}, {tl} and {text} placeholders (see .env.example). No service
//    URL is hard-coded in the app.
// System-written notes are rendered per viewer by the server, so this is
// only for what a person typed.
import { useTranslation } from "react-i18next";

const TEMPLATE = process.env.NEXT_PUBLIC_TRANSLATE_URL_TEMPLATE ?? "";

export default function TranslateLink({ text, language }: { text: string; language: string | null | undefined }) {
  const { t, i18n } = useTranslation("hiring");
  const to = i18n.language;
  if (!TEMPLATE || !language || !text.trim() || language.slice(0, 2) === to.slice(0, 2)) return null;
  const href = TEMPLATE.replace("{sl}", encodeURIComponent(language)).replace("{tl}", encodeURIComponent(to)).replace("{text}", encodeURIComponent(text));
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13 }}>
      {t("translate.link", { language: t(`voice.langName.${language.slice(0, 2)}`, { defaultValue: language }) })}
    </a>
  );
}
