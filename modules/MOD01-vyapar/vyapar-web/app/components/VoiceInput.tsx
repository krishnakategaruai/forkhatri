"use client";

// ======================================================================
// [FE1 — 2026-09-28] VoiceInput — speak into any prose field.
//
// REQUIREMENT (owner): minimise typing for both sides; voice in the
// member's own language, with confirm-before-save on every field it fills.
// Research (references/2026-screen-research.md §9): Web Speech API with
// lang en-IN / hi-IN / te-IN and interim results for a live caption; four
// visible states (idle / listening / processing / confirm); nothing is
// committed until the person taps Keep (FormBharo: accuracy on real Indian
// speech drops sharply, so confirm per field, never trust free speech);
// errors inline, never a modal; typing always stays available.
//
// APPROACH: a wrapper around the field it serves. The mic (and a small
// language switch) sits inside the field's trailing edge; the live
// transcript and the Keep / Try again / Discard row appear directly under
// the field. The field itself is untouched until Keep, when `onConfirm`
// hands the text to the parent, which decides whether it appends or
// replaces. When the browser has no SpeechRecognition the mic is simply
// not rendered and the field works exactly as before.
// ======================================================================

import { useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { recognitionCtor, SPEECH_LOCALE, type Recognition, type SpeechLang } from "./voice/speech";

// [Voice interview 2026-09-30] Recognition typings and the constructor now
// live in ./voice/speech, shared with the guided VoiceInterview.
type VoiceLang = SpeechLang;
const LOCALE = SPEECH_LOCALE;
const ORDER: VoiceLang[] = ["en", "hi", "te", "mr", "kn"];

const noopSubscribe = () => () => {};

/** True only in a browser that can do speech recognition (false during SSR). */
export function useVoiceSupported(): boolean {
  return useSyncExternalStore(noopSubscribe, () => recognitionCtor() !== null, () => false);
}

/** Join kept speech onto what was already typed, with one space. */
export function appendSpoken(previous: string, spoken: string): string {
  const a = previous.trimEnd();
  const b = spoken.trim();
  if (!a) return b;
  if (!b) return a;
  return `${a} ${b}`;
}

type Phase = "idle" | "listening" | "confirm";
type VoiceError = "notAllowed" | "noSpeech" | "network" | "noMic" | "generic";

export interface VoiceInputProps {
  /** Called only when the person taps Keep. */
  onConfirm: (text: string) => void;
  /** The field this voice input fills (an <input> or <textarea>). */
  children: ReactNode;
  /** Accessible name of the field, used in the mic's label. */
  fieldLabel?: string;
  /** Hide the language switch (for very narrow fields). */
  compact?: boolean;
}

export default function VoiceInput({ onConfirm, children, fieldLabel, compact = false }: VoiceInputProps) {
  const { t, i18n } = useTranslation("hiring");
  const supported = useVoiceSupported();
  const appLang = (ORDER as string[]).includes(i18n.language) ? (i18n.language as VoiceLang) : "en";
  const [chosenLang, setChosenLang] = useState<VoiceLang | null>(null);
  const lang = chosenLang ?? appLang;
  const [phase, setPhase] = useState<Phase>("idle");
  const [finalText, setFinalText] = useState("");
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<VoiceError | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const finalRef = useRef("");

  useEffect(() => () => recRef.current?.abort(), []);

  function start() {
    const Ctor = recognitionCtor();
    if (!Ctor) return;
    recRef.current?.abort();
    const rec = new Ctor();
    rec.lang = LOCALE[lang];
    rec.continuous = true;
    rec.interimResults = true;
    finalRef.current = "";
    setFinalText("");
    setInterim("");
    setError(null);
    rec.onresult = (e) => {
      let live = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalRef.current = appendSpoken(finalRef.current, r[0].transcript);
        else live += r[0].transcript;
      }
      setFinalText(finalRef.current);
      setInterim(live);
    };
    rec.onerror = (e) => {
      const map: Record<string, VoiceError> = {
        "not-allowed": "notAllowed",
        "service-not-allowed": "notAllowed",
        "no-speech": "noSpeech",
        network: "network",
        "audio-capture": "noMic",
      };
      if (e.error === "aborted") return;
      setError(map[e.error] ?? "generic");
    };
    rec.onend = () => {
      recRef.current = null;
      setInterim("");
      setPhase(finalRef.current.trim() ? "confirm" : "idle");
    };
    recRef.current = rec;
    try {
      rec.start();
      setPhase("listening");
    } catch {
      setError("generic");
    }
  }

  function stop() {
    recRef.current?.stop();
  }

  function keep() {
    const text = finalText.trim();
    if (text) onConfirm(text);
    reset();
  }

  function reset() {
    recRef.current?.abort();
    recRef.current = null;
    finalRef.current = "";
    setFinalText("");
    setInterim("");
    setPhase("idle");
  }

  function cycleLang() {
    const next = ORDER[(ORDER.indexOf(lang) + 1) % ORDER.length];
    setChosenLang(next);
    if (phase === "listening") {
      recRef.current?.abort();
      setPhase("idle");
    }
  }

  const listening = phase === "listening";

  return (
    <div className="vy-voice">
      <div className="vy-voice-field">
        {children}
        {supported && (
          <div className="vy-voice-tools">
            {!compact && (
              <button
                type="button"
                className="vy-voice-lang"
                onClick={cycleLang}
                aria-label={t("voice.switchLanguage", { language: t(`voice.langName.${lang}`) })}
                title={t("voice.switchLanguage", { language: t(`voice.langName.${lang}`) })}
              >
                {t(`voice.langShort.${lang}`)}
              </button>
            )}
            <button
              type="button"
              className="vy-voice-mic"
              aria-pressed={listening}
              aria-label={listening ? t("voice.stop") : t("voice.speak", { field: fieldLabel ?? t("voice.thisField") })}
              title={listening ? t("voice.stop") : t("voice.speak", { field: fieldLabel ?? t("voice.thisField") })}
              onClick={listening ? stop : start}
            >
              {listening ? <span className="vy-voice-dot" aria-hidden="true" /> : <MicIcon />}
            </button>
          </div>
        )}
      </div>

      {supported && phase !== "idle" && (
        <div className="vy-voice-live" aria-live="polite">
          <span className="vy-voice-status">
            {listening && <span className="vy-voice-dot" aria-hidden="true" />}
            {listening ? t("voice.listening", { language: t(`voice.langName.${lang}`) }) : t("voice.checkIt")}
          </span>
          <p className="vy-voice-transcript">
            {finalText}
            {interim && <span className="vy-voice-interim"> {interim}</span>}
            {!finalText && !interim && <span className="vy-voice-interim">{t("voice.speakNow")}</span>}
          </p>
          <div className="vy-voice-actions">
            {listening ? (
              <button type="button" className="vy-btn vy-btn-secondary" onClick={stop}>
                {t("voice.done")}
              </button>
            ) : (
              <>
                <button type="button" className="vy-btn vy-btn-primary" onClick={keep}>
                  {t("voice.keep")}
                </button>
                <button type="button" className="vy-btn vy-btn-secondary" onClick={start}>
                  {t("voice.retry")}
                </button>
                <button type="button" className="vy-btn vy-btn-ghost" onClick={reset}>
                  {t("voice.discard")}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {supported && error && phase === "idle" && <p className="vy-field-hint" role="status">{t(`voice.error.${error}`)}</p>}
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
    </svg>
  );
}
