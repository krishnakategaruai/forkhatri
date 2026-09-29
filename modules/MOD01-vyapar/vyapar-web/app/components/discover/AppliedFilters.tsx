"use client";

// [FE2 — research §6] Applied filters as removable chips above the results
// (Baymard: 28 % of sites fail to show them). Each chip removes its own
// filter; "Clear all" when there is more than one. Sort is not a filter and
// has its own control, so it is not a chip.
import { useTranslation } from "react-i18next";
import type { FeedFilterValues } from "@/lib/sdk";
import { formatRupees } from "@/lib/format";
import Icon from "@/app/components/Icon";
import { EMPTY_FILTERS } from "./feedFilters";

export default function AppliedFilters({
  value,
  skillLabel,
  onChange,
}: {
  value: FeedFilterValues;
  /** slug → localized skill label */
  skillLabel: (slug: string) => string;
  onChange: (next: FeedFilterValues) => void;
}) {
  const { t, i18n } = useTranslation(["explore"]);
  const money = (p: number) => formatRupees(p, i18n.language);
  const chips: { key: string; label: string; clear: FeedFilterValues }[] = [];
  if (value.q) chips.push({ key: "q", label: `“${value.q}”`, clear: { ...value, q: null } });
  for (const x of value.types ?? []) chips.push({ key: `type-${x}`, label: t(`explore:type.${x}`), clear: { ...value, types: (value.types ?? []).filter((y) => y !== x) } });
  if (value.radius_km) chips.push({ key: "radius", label: t("explore:filters.withinKm", { km: value.radius_km }), clear: { ...value, radius_km: null } });
  if (value.pay_min_paise != null || value.pay_max_paise != null) {
    const label =
      value.pay_min_paise != null && value.pay_max_paise != null
        ? t("explore:filters.payEchoRange", { min: money(value.pay_min_paise), max: money(value.pay_max_paise) })
        : value.pay_min_paise != null
          ? t("explore:filters.payEchoMin", { min: money(value.pay_min_paise) })
          : t("explore:filters.payEchoMax", { max: money(value.pay_max_paise ?? 0) });
    chips.push({ key: "pay", label, clear: { ...value, pay_min_paise: null, pay_max_paise: null, pay_kind: null } });
  }
  if (value.posted_within) chips.push({ key: "posted", label: t(`explore:posted.${value.posted_within}`), clear: { ...value, posted_within: null } });
  if (value.work_mode) chips.push({ key: "mode", label: t(`explore:workMode.${value.work_mode}`), clear: { ...value, work_mode: null } });
  if (value.shift) chips.push({ key: "shift", label: t(`explore:shift.${value.shift}`), clear: { ...value, shift: null } });
  if (value.experience) chips.push({ key: "exp", label: t(`explore:experience.${value.experience}`), clear: { ...value, experience: null } });
  if (value.availability) chips.push({ key: "avail", label: t(`explore:availability.${value.availability}`), clear: { ...value, availability: null } });
  for (const s of value.skills ?? []) chips.push({ key: `skill-${s}`, label: skillLabel(s), clear: { ...value, skills: (value.skills ?? []).filter((x) => x !== s) } });
  if (value.segment) chips.push({ key: "segment", label: t(`explore:segment.${value.segment}`), clear: { ...value, segment: null } });
  if (value.verified_only) chips.push({ key: "verified", label: t("explore:filters.verifiedChip"), clear: { ...value, verified_only: false } });
  if (chips.length === 0) return null;

  return (
    <div className="vy-applied" role="group" aria-label={t("explore:filters.applied")}>
      {chips.map((c) => (
        <button key={c.key} type="button" className="vy-chip" onClick={() => onChange(c.clear)} aria-label={t("explore:filters.remove", { label: c.label })}>
          {c.label} <Icon name="close" size={13} />
        </button>
      ))}
      {chips.length > 1 && (
        <button type="button" className="vy-btn vy-btn-ghost" style={{ fontSize: 13, flexShrink: 0 }} onClick={() => onChange({ ...EMPTY_FILTERS, sort: value.sort })}>
          {t("explore:filters.clearAll")}
        </button>
      )}
    </div>
  );
}
