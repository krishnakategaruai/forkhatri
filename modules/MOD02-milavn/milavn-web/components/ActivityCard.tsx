'use client';

/* The six-question card (FR006): what / when / where / who / how many / why —
 * as a poster. The photograph *is* the card: a full-bleed image, the host as
 * a glass pill, the trust badge always paired with text, a big title and a
 * glass info tray with the category's accent line. Real time, on the device:
 * a LIVE pulse while the activity is on, and "in 40 min" when it is close.
 * The why-reason is grounded in a real ranking factor (FR008). */

import { Radio } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { resolveMediaUrl, type Card } from '@/lib/api';
import { formatInr, formatWhen } from '@/lib/format';

const CATEGORY_ICON: Record<string, string> = { play: '🏸', meet: '☕', eat: '🍛', learn: '📚', work: '💼', explore: '🥾', celebrate: '🎉', help: '🤝' };
const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000;

export function TrustPill({ level, label, positive, onMedia }: { level: string; label: string; positive: boolean; onMedia?: boolean }) {
  const cls = onMedia ? (positive ? 'pill pill--onmedia' : 'pill pill--onmedia-neutral') : positive ? 'pill pill--trust' : 'pill pill--neutral';
  return (
    <span className={cls} data-level={level}>
      {positive && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M5 12l5 5L19 7" /></svg>}
      {label}
    </span>
  );
}

/** Live status computed on the device and refreshed every minute: 'live' | 'soon' (≤ 90 min) | null. */
export function useLiveStatus(start: string, end: string | null): { state: 'live' | 'soon' | null; minutes: number } {
  const compute = () => {
    const now = Date.now(); const s = new Date(start).getTime(); const e = end ? new Date(end).getTime() : s + DEFAULT_DURATION_MS;
    if (now >= s && now <= e) return { state: 'live' as const, minutes: 0 };
    const mins = Math.round((s - now) / 60000);
    if (mins > 0 && mins <= 90) return { state: 'soon' as const, minutes: mins };
    return { state: null, minutes: 0 };
  };
  const [st, setSt] = useState(compute);
  useEffect(() => { setSt(compute()); const id = setInterval(() => setSt(compute()), 60000); return () => clearInterval(id); }, [start, end]); // eslint-disable-line react-hooks/exhaustive-deps
  return st;
}

export default function ActivityCard({ card, compact = false, hero = false }: { card: Card; compact?: boolean; hero?: boolean }) {
  const { t, i18n } = useTranslation();
  const when = formatWhen(card.time_start, i18n.language);
  const live = useLiveStatus(card.time_start, card.time_end);
  const label = `${card.title}, ${when}, ${card.location_label}${card.distance_label ? `, ${card.distance_label}` : ''}, ${t('card.hostedBy')} ${card.host_name}, ${t('card.going', { count: card.going_count })}, ${card.why_reason}`;
  const cancelled = card.status === 'cancelled';
  const status = card.viewer_status && card.viewer_status !== 'cancelled' ? card.viewer_status : null;
  return (
    <Link href={`/a/${card.slug}`} className={`poster${compact ? ' poster--compact' : ''}${hero ? ' poster--hero' : ''}`} data-cat={card.intent_category} aria-label={label}>
      <div className="poster__media">
        {card.cover_image_url && <img src={resolveMediaUrl(card.cover_image_url) ?? ''} alt="" loading="lazy" />}
      </div>
      <div className="poster__top">
        <span className="glasspill">
          {card.host_avatar ? <img className="avatar" src={resolveMediaUrl(card.host_avatar) ?? ''} alt="" /> : <span className="avatar" />}
          <span className="truncate">{card.host_name}</span>
        </span>
        <span className="row" style={{ gap: 6 }}>
          {live.state === 'live' && !cancelled && <span className="pill pill--live"><Radio size={12} aria-hidden="true" /> {t('card.live')}</span>}
          {live.state === 'soon' && !cancelled && <span className="pill pill--onmedia-neutral">{t('card.startsIn', { minutes: live.minutes })}</span>}
          {status && <span className="pill pill--onmedia">{t(`card.youAre.${status}`)}</span>}
          {cancelled && <span className="pill pill--danger">{t('card.cancelled')}</span>}
          <TrustPill level={card.trust_level} label={card.trust_label} positive={card.trust_positive} onMedia />
        </span>
      </div>
      <div className="poster__body">
        <span className="poster__eyebrow">{CATEGORY_ICON[card.intent_category]} {card.category_label}{card.is_recurring ? ` · ${t('card.recurring')}` : ''}</span>
        <h3 className="poster__title">{card.title}</h3>
        <div className="poster__meta">
          <span className="datepill">{live.state === 'live' ? t('card.now') : when}</span>
          {card.price_paise != null && <span className="datepill datepill--price">{formatInr(card.price_paise, i18n.language)}</span>}
          <span className="poster__place">{card.location_label}{card.distance_label ? ` · ${card.distance_label}` : ''}</span>
        </div>
        <div className="poster__foot">
          <span className="poster__why"><span aria-hidden="true">✦</span> {card.why_reason}</span>
          <span className="poster__count">
            {card.going_count === 0 && !cancelled ? t('card.beFirst') : t('card.going', { count: card.going_count })}
            {card.capacity !== null && card.spots_left !== null && (card.spots_left > 0 ? ` · ${t('card.spotsLeft', { count: card.spots_left })}` : ` · ${t('card.full')}`)}
          </span>
        </div>
      </div>
    </Link>
  );
}
