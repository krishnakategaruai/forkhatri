'use client';

import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { useTranslation } from 'react-i18next';

/* Product owner, 2026-09-17: "voice input".
 *
 * Speaking instead of typing, for the places where someone writes in their own
 * words — a prompt answer, a private note about a match. Uses the browser's own
 * speech recognition in the reader's current language, and simply does not
 * render where the browser has none, so no screen ever shows a button that
 * cannot work. Nothing is uploaded by this component: the browser returns text,
 * and the text goes into the field the person was already filling in. */

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
};

type Props = {
  /** Called with the recognised words, to append to whatever is being written. */
  onText: (text: string) => void;
  label?: string;
};

export default function VoiceInput({ onText, label }: Props) {
  const { t, i18n } = useTranslation(['common', 'profile']);
  // Whether this browser can recognise speech, read at render time rather than
  // set from an effect. The server snapshot is false, so a browser without the
  // API simply never shows the button.
  const supported = useSyncExternalStore(
    () => () => {},
    () => {
      const w = window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown };
      return !!(w.SpeechRecognition ?? w.webkitSpeechRecognition);
    },
    () => false
  );
  const [listening, setListening] = useState(false);
  const recognition = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    return () => recognition.current?.stop();
  }, []);

  function toggle() {
    if (listening) {
      recognition.current?.stop();
      return;
    }
    const w = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    const Recognition = w.SpeechRecognition ?? w.webkitSpeechRecognition;
    if (!Recognition) return;
    const engine = new Recognition();
    // Hindi and Telugu speakers dictate in their own language, not in English.
    engine.lang = { hi: 'hi-IN', te: 'te-IN' }[i18n.language] ?? 'en-IN';
    engine.continuous = false;
    engine.interimResults = false;
    engine.onresult = (event) => {
      const said = Array.from({ length: event.results.length }, (_, i) => event.results[i][0].transcript)
        .join(' ')
        .trim();
      if (said) onText(said);
    };
    engine.onend = () => setListening(false);
    engine.onerror = () => setListening(false);
    recognition.current = engine;
    engine.start();
    setListening(true);
  }

  if (!supported) return null;

  return (
    <button
      type="button"
      className={`quick-pick__chip${listening ? ' quick-pick__chip--active' : ''}`}
      aria-pressed={listening}
      onClick={toggle}
    >
      {listening ? t('profile:voice.listening') : (label ?? t('profile:voice.speak'))}
    </button>
  );
}
