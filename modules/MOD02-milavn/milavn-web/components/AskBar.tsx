'use client';

/* "Ask Milavn" — ask-first discovery (thesis §31–§32, §40; Brand §13–§14).
 * Type or speak in English, Hindi or Telugu; the API returns what it understood
 * as filters, echoed back as chips before anything runs, so the interpretation
 * is always visible and correctable (Understand → Recommend → Authorize).
 * Voice uses the browser's own speech recognition when present; when absent
 * the mic simply is not shown. Deterministic on the server (discovery/nl.py). */

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { api } from '@/lib/api';

export type Understood = { category: string | null; when: string | null; distance: string | null; q: string | null; chips: string[] };

type SpeechRecognitionLike = { lang: string; interimResults: boolean; maxAlternatives: number; onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null; onend: (() => void) | null; onerror: (() => void) | null; start: () => void; stop: () => void };
const SPEECH_LANG: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN' };

function speechCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === 'undefined') return null;
  const w = window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export default function AskBar({ initial = '', onUnderstood, autoNavigate = true, prompts = [] }: { initial?: string; onUnderstood?: (u: Understood, text: string) => void; autoNavigate?: boolean; prompts?: string[] }) {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const [text, setText] = useState(initial);
  const [understood, setUnderstood] = useState<Understood | null>(null);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [canSpeak, setCanSpeak] = useState(false);
  const recRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => { setCanSpeak(speechCtor() !== null); }, []);

  useEffect(() => {
    if (!text.trim()) { setUnderstood(null); return; }
    const id = setTimeout(() => {
      api<Understood>(`/discovery/understand?q=${encodeURIComponent(text)}`).then(setUnderstood).catch(() => undefined);
    }, 220);
    return () => clearTimeout(id);
  }, [text]);

  const go = (value = text) => {
    if (!value.trim()) return;
    setBusy(true);
    const u = understood ?? { category: null, when: null, distance: null, q: value, chips: [] };
    if (onUnderstood) onUnderstood(u, value);
    if (autoNavigate) router.push(`/discover?${new URLSearchParams({ mode: 'search', ask: value })}`);
    setBusy(false);
  };

  const speak = () => {
    const Ctor = speechCtor();
    if (!Ctor) return;
    if (listening) { recRef.current?.stop(); return; }
    const rec = new Ctor();
    rec.lang = SPEECH_LANG[i18n.language] ?? 'en-IN';
    rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = (e) => { const said = e.results[0]?.[0]?.transcript ?? ''; if (said) { setText(said); setTimeout(() => go(said), 350); } };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec; setListening(true);
    try { rec.start(); } catch { setListening(false); }
  };

  return (
    <div className="stack" style={{ gap: 8 }}>
      <form className={`ask${listening ? ' ask--listening' : ''}`} onSubmit={(e) => { e.preventDefault(); go(); }} role="search" aria-label={t('ask.label')}>
        <span className="ask__spark" aria-hidden="true">✦</span>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder={listening ? t('ask.listening') : t('ask.placeholder')} aria-label={t('ask.label')} enterKeyHint="search" />
        {canSpeak && (
          <button type="button" className={`ask__mic${listening ? ' ask__mic--on' : ''}`} aria-label={t('ask.speak')} aria-pressed={listening} onClick={speak}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg>
          </button>
        )}
        <button type="submit" className="ask__go" aria-label={t('ask.go')} disabled={busy || !text.trim()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </button>
      </form>
      {understood && understood.chips.length > 0 && (
        <div className="ask__understood" aria-live="polite">
          <span>{t('ask.understood')}</span>
          {understood.chips.map((c) => <span key={c} className="pill">{c}</span>)}
        </div>
      )}
      {prompts.length > 0 && !text && (
        <div className="chips chips--scroll" aria-label={t('ask.tryLabel')}>
          {prompts.map((p) => <button key={p} type="button" className="chip chip--sm" onClick={() => { setText(p); setTimeout(() => go(p), 260); }}>{p}</button>)}
        </div>
      )}
    </div>
  );
}
