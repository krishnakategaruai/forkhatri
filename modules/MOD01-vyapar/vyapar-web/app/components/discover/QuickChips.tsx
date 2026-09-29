"use client";

// [Design language 2026-09-29, §11] One sticky row under the top bar, on
// every width (replaces FE2's phone-only MobileFilterBar and the desktop
// sidebar): "Filters (n)" opens the sheet / drawer; the location chip
// opens the distance popover (phones — desktop has it in the hero pill);
// then the six filters people use most as one-tap toggles, each with its
// icon (words + icon: low-literacy guidance). A pressed chip shows a
// check. When the list is filtered, Sort sits at the end (desktop has it
// in the results header too).
import { useTranslation } from "react-i18next";
import { Check, SlidersHorizontal, Navigation, Clock, IndianRupee, BadgeCheck, House, Moon, type LucideIcon } from "lucide-react";
import type { FeedFilterValues } from "@/lib/sdk";
import { activeCount } from "./feedFilters";
import LocationChip from "./LocationChip";

const PAY_20K_PAISE = 20_000 * 100;

export default function QuickChips({
  filters,
  onChange,
  onOpenFilters,
  place,
  defaultRadiusKm,
}: {
  filters: FeedFilterValues;
  onChange: (next: FeedFilterValues) => void;
  onOpenFilters: () => void;
  place: string | null;
  defaultRadiusKm: number | null;
}) {
  const { t } = useTranslation(["explore"]);
  const f = filters;
  const n = activeCount(f) - (f.q ? 1 : 0);

  const near = f.radius_km === 5 && f.sort === "distance";
  const today = f.posted_within === "today";
  const pay = f.pay_kind === "monthly" && f.pay_min_paise === PAY_20K_PAISE;
  const verified = !!f.verified_only;
  const remote = f.work_mode === "remote";
  const night = f.shift === "night";

  const chips: { key: string; on: boolean; icon: LucideIcon; label: string; toggle: () => FeedFilterValues }[] = [
    { key: "near", on: near, icon: Navigation, label: t("explore:quick.nearMe"), toggle: () => ({ ...f, radius_km: near ? null : 5, sort: near ? "relevance" : "distance" }) },
    { key: "today", on: today, icon: Clock, label: t("explore:quick.today"), toggle: () => ({ ...f, posted_within: today ? null : "today" }) },
    {
      key: "pay",
      on: pay,
      icon: IndianRupee,
      label: t("explore:quick.pay20k"),
      toggle: () => (pay ? { ...f, pay_kind: null, pay_min_paise: null, pay_max_paise: null } : { ...f, pay_kind: "monthly", pay_min_paise: PAY_20K_PAISE, pay_max_paise: null }),
    },
    { key: "verified", on: verified, icon: BadgeCheck, label: t("explore:quick.verified"), toggle: () => ({ ...f, verified_only: !verified }) },
    { key: "remote", on: remote, icon: House, label: t("explore:quick.remote"), toggle: () => ({ ...f, work_mode: remote ? null : "remote" }) },
    { key: "night", on: night, icon: Moon, label: t("explore:quick.night"), toggle: () => ({ ...f, shift: night ? null : "night" }) },
  ];

  return (
    <div className="vy-qbar">
      <div className="vy-qbar-row" role="group" aria-label={t("explore:quick.label")}>
        <button type="button" className="vy-chip vy-qbar-filters" aria-haspopup="dialog" onClick={onOpenFilters} data-count={n > 0 ? "" : undefined}>
          <SlidersHorizontal size={16} strokeWidth={2} aria-hidden="true" />
          {t("explore:quick.filters")}
          {n > 0 && <span className="vy-qbar-count">{n}</span>}
        </button>
        <span className="vy-mobile-only vy-qbar-loc">
          <LocationChip place={place} radiusKm={f.radius_km ?? null} defaultRadiusKm={defaultRadiusKm} onRadius={(km) => onChange({ ...f, radius_km: km })} />
        </span>
        <span className="vy-qbar-sep" aria-hidden="true" />
        {chips.map((c) => {
          const I = c.on ? Check : c.icon;
          return (
            <button key={c.key} type="button" className="vy-chip" aria-pressed={c.on} onClick={() => onChange(c.toggle())}>
              <I size={16} strokeWidth={c.on ? 2.5 : 2} aria-hidden="true" />
              {c.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
