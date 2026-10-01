"use client";

import { useTranslation } from "react-i18next";
import { Award, Clock3, HeartHandshake, Medal, ShieldCheck, Star, Timer, Users, CalendarCheck } from "lucide-react";

export type EarnedBadge = { id: string; level: number; threshold: number | null; since: string };
export type NextMilestone = { id: string; level: number; target: number; have: number; needs_reviews: number; progress: number; reviews: number; min_reviews: number };

const ICON: Record<string, typeof Award> = {
  consultations: Medal, clients: Users, repeat_trust: HeartHandshake, highly_rated: Star, on_time: Timer,
  reliable: CalendarCheck, hours: Clock3, verified_professional: ShieldCheck, tenure: Award,
};

/** The badge's name for its level, e.g. "50 consultations", "Repeat trust · 10". */
export function badgeLabel(t: (k: string, o?: Record<string, unknown>) => string, id: string, n: number | null) {
  if (id === "consultations" && n === 1) return t("badge.first_consultation");
  return t(`badge.${id}`, { n: n ?? "" });
}

export function BadgeChip({ b, small = false }: { b: EarnedBadge; small?: boolean }) {
  const { t } = useTranslation();
  const Icon = ICON[b.id] ?? Award;
  return (
    <span className={`badge-chip ${small ? "sm" : ""}`} title={t(`badge_why.${b.id}`, { n: b.threshold ?? "" })}>
      <Icon size={small ? 12 : 14} strokeWidth={1.8} />
      {badgeLabel(t, b.id, b.threshold)}
    </span>
  );
}

export function BadgeRow({ badges, small }: { badges: EarnedBadge[]; small?: boolean }) {
  if (!badges?.length) return null;
  return <span className="row" style={{ gap: 6 }}>{badges.map((b) => <BadgeChip key={b.id} b={b} small={small} />)}</span>;
}

export function NextMilestones({ items }: { items: NextMilestone[] }) {
  const { t } = useTranslation();
  if (!items.length) return null;
  return (
    <div className="stack" style={{ gap: 10 }}>
      {items.map((m) => {
        const Icon = ICON[m.id] ?? Award;
        return (
          <div key={`${m.id}-${m.level}`} className="stack" style={{ gap: 4 }}>
            <div className="between small">
              <span className="row" style={{ gap: 6 }}><Icon size={14} className="muted" />{badgeLabel(t, m.id, m.target)}</span>
              <span className="num muted tiny">{m.needs_reviews > 0 ? t("badge_reviews_of", { have: m.reviews, need: m.min_reviews }) : m.id.endsWith("rated") || m.id === "on_time" ? `${(m.have / 10).toFixed(1)} / ${(m.target / 10).toFixed(1)}` : `${m.have} / ${m.target}`}</span>
            </div>
            <span className="meter light"><span style={{ width: `${Math.round(m.progress * 100)}%` }} /></span>
            {m.needs_reviews > 0 && <span className="tiny muted">{t("badge_needs_score", { score: (m.target / 10).toFixed(1) })}</span>}
          </div>
        );
      })}
    </div>
  );
}
