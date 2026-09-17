'use client';

import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { useTranslation } from 'react-i18next';

import { resolveMediaUrl } from '@/lib/api';
import { deleteVoiceIntro, recordVoiceIntro } from '@/lib/profile';

/* Product owner, 2026-09-17: "voice input, introduction".
 *
 * A spoken introduction says things a biodata row cannot — warmth, humour, how
 * someone actually speaks — and it is the one part of a profile a person can
 * make without typing, which matters for a parent or a candidate more at ease
 * talking than writing. One clip per profile, capped at a minute: re-recording
 * replaces it, so there is never a list of takes to manage.
 *
 * Heard only by an accepted connection (migration 029): a voice reveals
 * identity in a way the pre-connection card deliberately does not. */

const MAX_SECONDS = 60;

type Props = { initialUrl: string | null };

export default function VoiceIntro({ initialUrl }: Props) {
  const { t } = useTranslation(['common', 'profile']);
  const [url, setUrl] = useState<string | null>(initialUrl);
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Whether this browser can record at all, read at render time rather than
  // set from an effect (which would cost a second render and trip the lint
  // rule against cascading renders). The server snapshot is false, so the
  // button appears only once we are running in a browser that has the API.
  const supported = useSyncExternalStore(
    () => () => {},
    () => typeof window.MediaRecorder !== 'undefined',
    () => false
  );
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const ticker = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (ticker.current) clearInterval(ticker.current);
      recorder.current?.stream.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function start() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const media = new MediaRecorder(stream);
      chunks.current = [];
      media.ondataavailable = (e) => chunks.current.push(e.data);
      media.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const clip = new Blob(chunks.current, { type: media.mimeType || 'audio/webm' });
        setBusy(true);
        const outcome = await recordVoiceIntro(clip);
        setBusy(false);
        if (!outcome.ok) {
          setError(outcome.message ?? t('profile:voice.error'));
          return;
        }
        setUrl(outcome.data.voice_intro_url);
      };
      media.start();
      recorder.current = media;
      setRecording(true);
      setSeconds(0);
      ticker.current = setInterval(() => {
        setSeconds((s) => {
          if (s + 1 >= MAX_SECONDS) stop();
          return s + 1;
        });
      }, 1000);
    } catch {
      setError(t('profile:voice.noMicrophone'));
    }
  }

  function stop() {
    if (ticker.current) clearInterval(ticker.current);
    ticker.current = null;
    recorder.current?.stop();
    setRecording(false);
  }

  async function remove() {
    setBusy(true);
    setError(null);
    const outcome = await deleteVoiceIntro();
    setBusy(false);
    if (!outcome.ok) {
      setError(t('profile:voice.error'));
      return;
    }
    setUrl(null);
  }

  if (!supported) return null;

  return (
    <section className="card voice-intro" aria-label={t('profile:voice.title')}>
      <div className="label">{t('profile:voice.title')}</div>
      <p className="caption" style={{ margin: 0 }}>
        {t('profile:voice.intro')}
      </p>

      {url && (
        <audio controls src={resolveMediaUrl(url) ?? ''} className="voice-intro__player" />
      )}

      <div className="voice-intro__actions">
        {recording ? (
          <button type="button" className="cta" onClick={stop}>
            {t('profile:voice.stop', { seconds: MAX_SECONDS - seconds })}
          </button>
        ) : (
          <button type="button" className="quick-pick__chip quick-pick__chip--active" disabled={busy} onClick={() => void start()}>
            {url ? t('profile:voice.rerecord') : t('profile:voice.record')}
          </button>
        )}
        {url && !recording && (
          <button type="button" className="quick-pick__chip" disabled={busy} onClick={() => void remove()}>
            {t('profile:voice.delete')}
          </button>
        )}
      </div>

      {error && (
        <p className="form__error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
