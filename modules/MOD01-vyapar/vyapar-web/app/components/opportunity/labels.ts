// [IMP38 — Refactor C] Label helpers shared by every opportunity surface
// (feed cards, similar cards, the detail screen's "Why this?"). Moved out of
// the pages unchanged so the page and the embeddable components render the
// exact same text.

export const RANKING_SIGNAL_KEYS = [
  "capability_fit",
  "intent_fit",
  "location_fit",
  "timing_fit",
  "value_fit",
  "experience_fit",
  "freshness_fit",
  "trust_fit",
  // [Recommendations that learn] taste_fit is refined by the API into which
  // phrase fits; "explore" marks something new near the member's skills.
  "taste_fit",
  "taste_fit_applied",
  "taste_fit_saved",
  "taste_fit_more_like_this",
  "explore",
];

/** The `t` from useTranslation(), narrowed to what these helpers call. */
export type T = (key: string, options?: Record<string, unknown>) => string;

/** Ranking signal or fallback reason → translated line ("Why this?", card relevance). */
export function signalLabel(t: T, key: string, fallbackDefault?: string): string {
  if (RANKING_SIGNAL_KEYS.includes(key)) return t(`ranking:signal.${key}`);
  return fallbackDefault === undefined
    ? t(`ranking:fallback.${key}`)
    : t(`ranking:fallback.${key}`, { defaultValue: fallbackDefault });
}

/** Discover card freshness stamp. */
export function freshnessLabel(t: T, days: number | null): string {
  if (days === null) return "";
  if (days === 0) return t("discover:card.postedToday");
  if (days === 1) return t("discover:card.postedYesterday");
  return t("discover:card.postedDaysAgo", { days });
}

/** Detail-screen style "Posted today / Posted n days ago". */
export function postedLabel(t: T, days: number | null): string | null {
  if (days === null) return null;
  return days === 0 ? t("opportunities:detail.postedToday") : t("opportunities:detail.postedDaysAgo", { count: days });
}

export const NOT_INTERESTED_REASON_KEYS: Record<string, string> = {
  too_far: "notInterestedTooFar",
  wrong_type: "notInterestedWrongType",
  not_my_capability: "notInterestedNotMyCapability",
  value_too_low: "notInterestedValueTooLow",
  wrong_timing: "notInterestedWrongTiming",
  already_found: "notInterestedAlreadyFound",
  not_interested: "notInterestedGeneric",
};

export function hostOf(url: string | null): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}
