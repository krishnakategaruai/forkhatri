// [Voice interview 2026-09-30] Browser speech, both directions, shared by
// VoiceInput (dictate into one field) and VoiceInterview (the guided
// conversation). Web Speech API: SpeechRecognition (Chrome/Safari still
// prefix it) with lang en-IN / hi-IN / te-IN, and speechSynthesis.
//
// Rule from the owner's brief: never read Telugu (or Hindi) with an English
// voice. pickVoice() returns a voice only when one exists for the member's
// language; otherwise the question is shown as text with a small note.

export type SpeechLang = "en" | "hi" | "te";
export const SPEECH_LOCALE: Record<SpeechLang, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

export function speechLang(language: string | undefined): SpeechLang {
  return language === "hi" || language === "te" ? language : "en";
}

// Minimal typings: SpeechRecognition is not in every TS DOM lib.
export interface RecognitionAlternative {
  transcript: string;
}
export interface RecognitionResult {
  isFinal: boolean;
  0: RecognitionAlternative;
}
export interface RecognitionEvent {
  resultIndex: number;
  results: ArrayLike<RecognitionResult>;
}
export interface Recognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: RecognitionEvent) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  onspeechstart?: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}
export type RecognitionCtor = new () => Recognition;

export function recognitionCtor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function synthesisSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";
}

/** Voices load asynchronously in Chrome; wait briefly for them. */
export function loadVoices(timeoutMs = 1200): Promise<SpeechSynthesisVoice[]> {
  if (!synthesisSupported()) return Promise.resolve([]);
  const now = window.speechSynthesis.getVoices();
  if (now.length) return Promise.resolve(now);
  return new Promise((resolve) => {
    const done = () => {
      window.speechSynthesis.removeEventListener("voiceschanged", done);
      clearTimeout(timer);
      resolve(window.speechSynthesis.getVoices());
    };
    const timer = setTimeout(done, timeoutMs);
    window.speechSynthesis.addEventListener("voiceschanged", done);
  });
}

/**
 * A voice for exactly this language: the Indian locale first (en-IN, hi-IN,
 * te-IN), then any voice of the same language, preferring on-device ones.
 * English may fall back to another English accent; Hindi and Telugu never
 * fall back to a different language.
 */
export function pickVoice(voices: SpeechSynthesisVoice[], lang: SpeechLang): SpeechSynthesisVoice | null {
  const norm = (v: SpeechSynthesisVoice) => v.lang.replace("_", "-").toLowerCase();
  const exact = voices.filter((v) => norm(v) === SPEECH_LOCALE[lang].toLowerCase());
  const same = voices.filter((v) => norm(v).split("-")[0] === lang);
  const pool = exact.length ? exact : same;
  if (!pool.length) return null;
  return pool.find((v) => v.localService) ?? pool[0];
}

export interface SpeakHandle {
  /** Resolves true when finished, false when cancelled. */
  done: Promise<boolean>;
  cancel: () => void;
}

/** Speak one line. A safety timer resolves even if the engine never fires onend (a known Chrome bug). */
export function speak(text: string, voice: SpeechSynthesisVoice, opts: { rate?: number; onStart?: () => void } = {}): SpeakHandle {
  let settle: (ok: boolean) => void = () => {};
  let finished = false;
  const done = new Promise<boolean>((resolve) => {
    settle = (ok) => {
      if (finished) return;
      finished = true;
      clearTimeout(safety);
      resolve(ok);
    };
  });
  const synth = window.speechSynthesis;
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.voice = voice;
  u.lang = voice.lang;
  u.rate = opts.rate ?? 0.95;
  u.onstart = () => opts.onStart?.();
  u.onend = () => settle(true);
  u.onerror = (e) => settle(e.error !== "interrupted" && e.error !== "canceled");
  const safety = setTimeout(() => settle(true), 4000 + text.length * 110);
  synth.speak(u);
  return {
    done,
    cancel: () => {
      settle(false);
      synth.cancel();
    },
  };
}

/** Is this interim text just our own question coming back through the speaker? */
export function isEcho(heard: string, spoken: string): boolean {
  const words = heard.toLowerCase().split(/\s+/).filter((w) => w.length > 1);
  if (!words.length) return true;
  const said = spoken.toLowerCase();
  const inside = words.filter((w) => said.includes(w)).length;
  return inside / words.length >= 0.6;
}
