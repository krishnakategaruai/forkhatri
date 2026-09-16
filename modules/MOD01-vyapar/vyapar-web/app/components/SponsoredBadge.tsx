"use client";

// [TR030/TR054] SponsoredBadge-CC — the ONE render path for the "Sponsored"
// label (SP030 Class G: no second implementation). Every surface that can
// show a boosted card or detail — search cards, feed cards, listing detail,
// opportunity detail — renders this component, so the label can't be
// restyled, reworded or forgotten on one surface. Dashed neutral outline,
// visually distinct from the verification badge and the reputation line.
// Traces to: FR30, FR54, TR030, TR054, SP030, SP054
import { useTranslation } from "react-i18next";

export default function SponsoredBadge() {
  const { t } = useTranslation("common");
  return <span className="vy-badge vy-badge-sponsored">{t("badge.sponsored")}</span>;
}
