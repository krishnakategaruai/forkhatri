"use client";

/**
 * Inline intent field on the signed-in hub. (The file name is left over from the
 * removed orb/composer dialog; there is no dialog any more.)
 *
 * "What would you like to do?" is a real text input on the hub. While the member types,
 * the rule-based parser (lib/intent.ts) runs in place:
 * - understanding chips and one quiet note appear directly under the input;
 * - Hub highlights the matching module rows, moves them to the top and dims the rest;
 * - Enter opens the top available match; Escape or ✕ clears.
 * Voice input is a small mic inside the field, only where the Web Speech API exists.
 */
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState, type FormEvent, type RefObject } from "react";
import type { Lang, ModuleEntry } from "@/lib/api";
import { speechRecognitionCtor, useSpeechSupported, type SpeechRecognitionLike } from "@/lib/hooks";
import type { MessageKey, Translate } from "@/lib/i18n";
import type { Intent } from "@/lib/intent";
import { CloseIcon, MicIcon, SearchIcon, Sigil } from "./ui";

export const SUGGESTIONS: MessageKey[] = ["suggestActivity", "suggestMatch", "suggestService"];

type IntentFieldProps = {
  t: Translate;
  lang: Lang;
  modules: ModuleEntry[];
  query: string;
  onQueryChange: (query: string) => void;
  intent: Intent;
  inputRef: RefObject<HTMLInputElement | null>;
  onSubmit: () => void;
};

const SPEECH_LANG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

export default function IntentField({ t, lang, modules, query, onQueryChange: setQuery, intent, inputRef, onSubmit }: IntentFieldProps) {
  const [listening, setListening] = useState(false);
  const [voiceError, setVoiceError] = useState(false);
  const speechSupported = useSpeechSupported();
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => () => recognitionRef.current?.abort(), []);

  const byKey = useMemo(() => new Map(modules.map((module) => [module.key, module])), [modules]);
  const trimmed = query.trim();
  const matched = intent.module ? (byKey.get(intent.module) ?? null) : null;
  const candidates = intent.module ? [] : intent.candidates.map((key) => byKey.get(key)).filter((m): m is ModuleEntry => !!m);

  const chips: { key: string; label: string }[] = [];
  if (matched) chips.push({ key: "module", label: matched.name });
  if (intent.kind) chips.push({ key: "kind", label: t(`kind_${intent.kind}` as MessageKey) });
  if (intent.time) chips.push({ key: "time", label: t(`time_${intent.time}` as MessageKey) });
  if (intent.place) chips.push({ key: "place", label: intent.place.type === "near" ? t("place_near") : t("place_in", { place: intent.place.value }) });

  // One quiet note at most: a not-yet-open match (named with its glyph), an ambiguous phrase, or no match.
  let note: { text: string; moduleKey?: string } | null = null;
  if (matched && matched.availability !== "available") {
    note = {
      text: t(matched.availability === "planned" ? "intentNotOpenPlanned" : "intentNotOpenDev", { module: matched.name }),
      moduleKey: matched.key,
    };
  } else if (!matched && candidates.length > 1) {
    note = { text: t("intentAmbiguous") };
  } else if (!matched && candidates.length === 0 && trimmed.length > 2) {
    note = { text: t("intentNoMatch") };
  }

  const summary = [chips.map((chip) => chip.label).join(" · "), note?.text].filter(Boolean).join(". ");

  function toggleVoice() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const Ctor = speechRecognitionCtor();
    if (!Ctor) return;
    const recognition = new Ctor();
    recognition.lang = SPEECH_LANG[lang];
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      setQuery(
        Array.from(event.results)
          .map((result) => result[0]?.transcript ?? "")
          .join(" "),
      );
    };
    recognition.onerror = (event) => {
      if (event.error !== "aborted" && event.error !== "no-speech") setVoiceError(true);
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    setVoiceError(false);
    setListening(true);
    try {
      recognition.start();
    } catch {
      setListening(false);
      setVoiceError(true);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="ask-form" role="search" onSubmit={submit}>
      <label htmlFor="ask-input" className="sr-only">
        {t("askPrompt")}
      </label>
      <div className={`ask-field ${listening ? "is-listening" : ""}`}>
        <SearchIcon size={20} className="ask-icon" />
        <input
          id="ask-input"
          ref={inputRef}
          className="ask-input"
          type="text"
          value={query}
          onChange={(event) => {
            setVoiceError(false);
            setQuery(event.target.value);
          }}
          onKeyDown={(event) => {
            if (event.key !== "Escape") return;
            event.preventDefault();
            if (query) setQuery("");
            else event.currentTarget.blur();
          }}
          placeholder={listening ? t("listening") : t("askPrompt")}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          enterKeyHint="go"
        />
        {query && (
          <button
            type="button"
            className="ask-btn"
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            aria-label={t("clearInput")}
          >
            <CloseIcon size={18} />
          </button>
        )}
        {speechSupported && (
          <button type="button" className="ask-btn" onClick={toggleVoice} aria-pressed={listening} aria-label={listening ? t("voiceStop") : t("voiceStart")}>
            <MicIcon size={20} />
          </button>
        )}
        {!query && !speechSupported && <kbd aria-hidden="true">/</kbd>}
      </div>

      {(chips.length > 0 || note || voiceError) && (
        // Visual duplicate of the live summary below, so it is hidden from assistive technology.
        <div className="understanding" aria-hidden="true">
          <AnimatePresence mode="popLayout" initial={false}>
            {chips.map((chip, index) => (
              <motion.span
                key={`${chip.key}-${chip.label}`}
                layout
                className="u-chip"
                data-kind={chip.key}
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1, transition: { duration: 0.16, delay: index * 0.03 } }}
                exit={{ opacity: 0 }}
              >
                {chip.label}
              </motion.span>
            ))}
          </AnimatePresence>
          {note && (
            <span className="ask-note">
              {note.moduleKey && <Sigil moduleKey={note.moduleKey} size={16} />}
              {note.text}
            </span>
          )}
          {voiceError && <span className="ask-note error-text">{t("voiceError")}</span>}
        </div>
      )}
      <p className="sr-only" aria-live="polite">
        {summary}
      </p>
    </form>
  );
}
