"use client";

// [FE2 → design language 2026-09-29] The location chip ("Near Madhapur ·
// 25 km") and its distance popover (the member's area, a 1–50 km slider,
// "Anywhere"), lifted out of FE2's DiscoverTop unchanged in behaviour so it
// can sit in the quick-chip row (phones) and in the hero search pill's
// "Where" segment (desktop).
import { useState } from "react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { MapPin, ChevronDown } from "lucide-react";

export default function LocationChip({
  place,
  radiusKm,
  defaultRadiusKm,
  onRadius,
  bare = false,
}: {
  place: string | null;
  radiusKm: number | null;
  defaultRadiusKm: number | null;
  onRadius: (km: number | null) => void;
  /** Inside the hero pill: no chip frame. */
  bare?: boolean;
}) {
  const { t } = useTranslation(["explore"]);
  const [open, setOpen] = useState(false);
  const [draftKm, setDraftKm] = useState(radiusKm ?? defaultRadiusKm ?? 10);
  const pop = usePopoverDismiss(open, () => setOpen(false));

  // the radius in effect: the filter, else the member's own (the feed applies it either way)
  const effectiveKm = radiusKm ?? defaultRadiusKm;
  // The framed chip lives in the phone chip row, where "Near Banjara Hills
  // · 12 km" truncated at 360px; there the pin icon already says "near",
  // so the label is the place and the distance ("Banjara Hills · 12 km").
  // The bare form (desktop "Where" segment) keeps the full sentence.
  const label = effectiveKm
    ? place
      ? t(bare ? "explore:top.nearPlaceKm" : "explore:top.placeKm", { place, km: effectiveKm })
      : t("explore:filters.withinKm", { km: effectiveKm })
    : place
      ? bare
        ? t("explore:top.nearPlace", { place })
        : place
      : t("explore:filters.anyDistance");

  // The phone chip drops "Near" so the place and distance both fit.
  const short = effectiveKm && place ? t("explore:top.placeKm", { place, km: effectiveKm }) : label;

  return (
    <div ref={pop} className="vy-loc">
      <button
        type="button"
        className={bare ? "vy-loc-bare" : "vy-chip vy-loc-chip2"}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => {
          setDraftKm(radiusKm ?? defaultRadiusKm ?? 10);
          setOpen((v) => !v);
        }}
      >
        <MapPin size={16} strokeWidth={2} aria-hidden="true" />
        <span className="vy-loc-text">{bare ? label : short}</span>
        <ChevronDown size={14} strokeWidth={2.25} aria-hidden="true" />
      </button>
      {open && (
        <div className="vy-popover vy-loc-pop2" role="dialog" aria-label={t("explore:top.locationTitle")}>
          <div className="vy-stack" style={{ gap: 2, padding: "4px 6px" }}>
            <span className="vy-popover-label" style={{ padding: 0 }}>{t("explore:top.area")}</span>
            <strong>{place ?? t("explore:top.noArea")}</strong>
            <Link href="/profile" className="vy-link-btn">{t("explore:top.changeArea")}</Link>
          </div>
          <label className="vy-field" style={{ padding: "4px 6px" }}>
            <span className="vy-label">{t("explore:top.distance", { km: draftKm })}</span>
            <input type="range" min={1} max={50} step={1} value={draftKm} onChange={(e) => setDraftKm(Number(e.target.value))} />
          </label>
          <div className="vy-row" style={{ gap: 8, padding: "0 4px 4px" }}>
            <button
              type="button"
              className="vy-btn vy-btn-secondary"
              style={{ flex: 1 }}
              onClick={() => {
                onRadius(draftKm);
                setOpen(false);
              }}
            >
              {t("explore:top.apply")}
            </button>
            <button
              type="button"
              className="vy-btn vy-btn-ghost"
              onClick={() => {
                onRadius(null);
                setOpen(false);
              }}
            >
              {t("explore:top.anywhere")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
