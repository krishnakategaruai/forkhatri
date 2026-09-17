'use client';

import { useTranslation } from 'react-i18next';

import { resolveMediaUrl } from '@/lib/api';

/* The other person's spoken introduction, on a profile the viewer is connected
 * to. Nothing renders when there is no recording, so a profile without one
 * never shows an empty player (migration 029). */

export default function VoiceIntroPlayer({ url, name }: { url: string | null; name: string }) {
  const { t } = useTranslation(['profile']);
  if (!url) return null;
  return (
    <section className="card voice-intro" aria-label={t('profile:voice.theirs', { name })}>
      <div className="label">{t('profile:voice.theirs', { name })}</div>
      <audio controls src={resolveMediaUrl(url) ?? ''} className="voice-intro__player" />
    </section>
  );
}
