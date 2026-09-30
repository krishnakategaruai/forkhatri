"use client";

// [Design language 2026-09-29, §10] The opportunity card.
//
// FE2's reading order is kept (owner review, 2026-09-29: never an accent
// title, never a run-on meta line, never raw pay, sentence case), and the
// card gains what makes it read in a glance at any literacy level:
//   ▣ trade icon tile (tinted by family — the same icon as the trade rail)
//   title (ink, 2 lines)                              action chip ›
//   PAY — the hero line, always ₹ with its period; an annual "LPA" figure
//         is shown as "₹X a month" with the yearly figure secondary
//         (critique W3: most people compare monthly pay)
//   ⌖ place · distance
//   ── ✓ ONE trust badge (the strongest earned) ·········· posted time
// "Why this?" (FE2) is an info button in the footer that shows the reason
// in place. The whole card is the link; the action chip names what
// happens next. Hover lifts 2px; press springs (language-2026 / discover
// CSS); reduced motion keeps only colour changes.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { BadgeCheck, ChevronRight, MapPin, Clock } from "lucide-react";
import type { OpportunityCard } from "@/lib/sdk";
import { formatRupees } from "@/lib/format";
import { useRoutes } from "@/app/host/HostProvider";
import { freshnessLabel, signalLabel } from "@/app/components/opportunity/labels";
import { cardVisual } from "./trades";
import CardMenu from "@/app/components/reco/CardMenu";
import { useHiddenPosts } from "@/app/components/reco/feedbackStore";

/** "CHAT CHEF NEEDED" → "Chat chef needed"; any mixed-case title is left as written. */
export function displayTitle(title: string): string {
  const letters = title.replace(/[^\p{L}]/gu, "");
  if (letters.length < 4 || letters !== letters.toUpperCase() || letters === letters.toLowerCase()) return title;
  const lower = title.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function km(d: number): string {
  return d < 10 ? d.toFixed(1) : String(Math.round(d));
}

/**
 * "₹8–10 LPA" → { monthly: "₹66,700–₹83,300", yearlyLakh: "₹8–10" }.
 * Anything that is not a lakh-per-annum figure is returned as written.
 * The caller words the yearly line ("₹8–10 lakh a year") through a
 * translation key: the recruiter shorthand "LPA" never reaches the screen
 * (owner, 2026-09-30), and the wording follows the reader's language.
 */
export function payLines(
  label: string,
  language: string,
): { main: string; monthly: boolean; yearlyLakh: string | null; /** same as yearlyLakh (restored callers) */ lakhRange: string | null } {
  // [2026-09-30, glossary] one wording for a monthly figure everywhere:
  // "₹12,000 a month". A poster's "₹12,000 / month", "per month", "/mo",
  // "pm" all become the bare amount, worded by the caller's key.
  const perMonth = label.match(/^(.*?₹.*?)\s*(?:\/\s*(?:month|mo)|per\s+month|a\s+month|p\.?m\.?)\s*$/i);
  if (perMonth) return { main: perMonth[1].trim(), monthly: true, yearlyLakh: null, lakhRange: null };
  const m = label.match(/₹\s?([\d.]+)\s?(?:[–-]\s?₹?\s?([\d.]+))?\s?(?:LPA|lpa|lakh(?:s)? (?:per|a) (?:annum|year))/);
  if (!m) return { main: label, monthly: false, yearlyLakh: null, lakhRange: null };
  // A converted figure is an estimate: round it to ₹1,000 ("₹1,17,000", not "₹1,16,700").
  const month = (lakh: string) => Math.round((parseFloat(lakh) * 100000) / 12 / 1000) * 1000 * 100; // paise
  const lo = formatRupees(month(m[1]), language);
  const main = m[2] ? `${lo}–${formatRupees(month(m[2]), language)}` : lo;
  const range = m[2] ? `₹${m[1]}–${m[2]}` : `₹${m[1]}`;
  return { main, monthly: true, yearlyLakh: range, lakhRange: range };
}

const TRUST_ORDER = ["verified_business", "verified_professional", "verified", "id_verified", "top_rated", "rising"];

export default function DiscoverCard({ item }: { item: OpportunityCard }) {
  const { t, i18n } = useTranslation(["discover", "opportunities", "ranking", "explore"]);
  const routes = useRoutes();
  const [why, setWhy] = useState(false);
  const hidden = useHiddenPosts();
  const visual = cardVisual(item.required_capabilities, item.type);
  const TradeIcon = visual.icon;
  const rawPay = item.compensation_label || item.compensation;
  const pay = rawPay ? payLines(rawPay, i18n.language) : null;
  // Server labels first ("Madhapur · In your area"), else the older fields.
  const place = [
    item.location_label ?? item.location,
    item.distance_label ?? (item.distance_km != null ? t("discover:businesses.distanceAway", { km: km(item.distance_km) }) : null),
  ]
    .filter(Boolean)
    .join(" · ");
  const postedFull = freshnessLabel(t, item.posted_days_ago);
  // The clock icon already says "posted": the footer reads "23 days ago".
  const days = item.posted_days_ago;
  const posted =
    days === null || days === undefined
      ? ""
      : days === 0
        ? t("explore:card.agoToday")
        : days === 1
          ? t("explore:card.agoYesterday")
          : t("explore:card.agoDays", { days });
  const badge = [...(item.poster_badges ?? [])].sort(
    (a, b) => (TRUST_ORDER.indexOf(a.key) + 99) % 99 - ((TRUST_ORDER.indexOf(b.key) + 99) % 99),
  )[0];
  const reasons = [
    item.relevance_reason ? signalLabel(t, item.relevance_reason, "") : "",
    item.source_segment === "community" ? t("explore:card.fromCommunity") : t("explore:card.publicSource"),
  ].filter(Boolean);

  // [Recommendations] a post the member said "Not interested" to leaves every list at once.
  if (hidden.has(item.id)) return null;

  return (
    <Link href={routes.opportunity(item.id)} transitionTypes={["vy-forward"]} className="vy-card vy-ocard">
      <div className="vy-ocard-top">
        <span className={`vy-trade-tile vy-trade-${visual.family}`} aria-hidden="true">
          <TradeIcon size={22} strokeWidth={1.9} />
        </span>
        <span className="vy-ocard-tags">
          {item.sponsored && <span className="vy-badge vy-badge-sponsored">{t("explore:card.sponsored")}</span>}
          <span className="vy-ocard-action">
            {t(`opportunities:actionLabel.${item.type_action_label}`)}
            <ChevronRight size={15} strokeWidth={2.25} aria-hidden="true" />
          </span>
        </span>
      </div>

      <h3 className="vy-ocard-title">{displayTitle(item.title)}</h3>

      {pay && (
        <p className="vy-ocard-pay">
          <span>{pay.monthly ? t("explore:card.perMonth", { amount: pay.main }) : pay.main}</span>
          {pay.yearlyLakh && <small>{t("explore:card.lakhAYear", { range: pay.yearlyLakh })}</small>}
        </p>
      )}

      {place && (
        <p className="vy-ocard-line">
          <MapPin size={15} strokeWidth={2} aria-hidden="true" />
          <span>{place}</span>
        </p>
      )}

      <div className="vy-ocard-foot">
        {badge ? (
          <span className="vy-ocard-trust" title={badge.description ?? undefined}>
            <BadgeCheck size={16} strokeWidth={2} aria-hidden="true" />
            {badge.label}
          </span>
        ) : (
          <span />
        )}
        <span className="vy-ocard-when" title={postedFull || undefined}>
          {posted && (
            <>
              <Clock size={14} strokeWidth={2} aria-hidden="true" />
              {posted}
            </>
          )}
          <CardMenu postId={item.id} title={displayTitle(item.title)} whyOpen={why} onWhy={reasons.length > 0 ? () => setWhy((v) => !v) : undefined} />
        </span>
      </div>
      {why && <p className="vy-ocard-reason">{reasons.join(" · ")}</p>}
    </Link>
  );
}
