"use client";

// [Design system 2026-09-30 — replaces QuickChips + the filter sheet] Owner:
// "i really hate filters section… throwing all the tags which is hard job
// for user to scroll" and "all the screen is filled with unnecessary
// things". One sticky row of dropdown buttons under the search:
//   Trade ▾ · Distance ▾ · Pay ▾ · Posted ▾ · More ▾
// Each button shows its chosen value and opens only its own control. The
// URL stays the source of truth (feedFilters.ts), so saved searches, "See
// all" and shared links keep working. Sort lives on the results heading.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { numberLocale } from "@/lib/i18n/languages";
import type { FeedFilterValues } from "@/lib/sdk";
import FilterDropdown, { ChoiceList } from "@/app/components/filters/FilterDropdown";
import TradePicker, { tradeValue, useTaxonomy } from "@/app/components/filters/TradePicker";

const PAY_PRESETS = [10_000, 20_000, 40_000, 75_000];
const POSTED = ["today", "week", "month"] as const;
const MODES = ["on_site", "remote", "both"] as const;
const SHIFTS = ["day", "night", "flexible"] as const;
const EXPERIENCE = ["fresher", "1", "3"] as const;

export default function DiscoverFilterBar({
  filters: f,
  onChange,
  place,
  defaultRadiusKm,
}: {
  filters: FeedFilterValues;
  onChange: (next: FeedFilterValues) => void;
  place: string | null;
  defaultRadiusKm: number | null;
}) {
  const { t, i18n } = useTranslation(["explore"]);
  const { categories, labelOf } = useTaxonomy();
  const rupees = (n: number) => n.toLocaleString(numberLocale(i18n.language));

  // Drafts, reset each time a panel opens.
  const [skills, setSkills] = useState<string[]>([]);
  const [km, setKm] = useState<number | null>(null);
  const [payMin, setPayMin] = useState<number | null>(null);
  const [posted, setPosted] = useState<FeedFilterValues["posted_within"]>(null);
  const [more, setMore] = useState<Pick<FeedFilterValues, "work_mode" | "shift" | "experience" | "verified_only">>({});

  const payRupees = f.pay_kind === "monthly" && f.pay_min_paise != null ? f.pay_min_paise / 100 : null;
  const moreCount = [f.work_mode, f.shift, f.experience].filter(Boolean).length + (f.verified_only ? 1 : 0);
  const radius = f.radius_km ?? null;

  return (
    <div className="vy-fbar" role="group" aria-label={t("fbar.label")}>
      <div className="vy-fbar-row">
        <FilterDropdown
          label={t("fbar.trade")}
          value={tradeValue(f.skills ?? [], categories, labelOf, (first, count) => t("fbar.tradeMore", { first, count }))}
          active={(f.skills?.length ?? 0) > 0}
          width={360}
          onOpen={() => setSkills([...(f.skills ?? [])])}
          onApply={() => onChange({ ...f, skills })}
          onClear={() => onChange({ ...f, skills: [] })}
        >
          <TradePicker value={skills} onChange={setSkills} />
        </FilterDropdown>

        <FilterDropdown
          label={t("fbar.distance")}
          value={radius ? t("fbar.km", { km: radius }) : null}
          active={!!radius}
          onOpen={() => setKm(radius ?? defaultRadiusKm ?? 10)}
          onApply={() => onChange({ ...f, radius_km: km })}
          onClear={() => onChange({ ...f, radius_km: null, sort: f.sort === "distance" ? "relevance" : f.sort })}
        >
          <div className="vy-fdd-range">
            <div className="vy-fdd-range-head">
              <strong className="vy-num">{km ? t("fbar.km", { km }) : t("fbar.anyDistance")}</strong>
              {place && <span className="vy-muted">{t("fbar.fromPlace", { place })}</span>}
            </div>
            <input
              type="range"
              min={1}
              max={50}
              value={km ?? 50}
              onChange={(e) => setKm(Number(e.target.value))}
              aria-label={t("fbar.distance")}
            />
          </div>
        </FilterDropdown>

        <FilterDropdown
          label={t("fbar.pay")}
          value={payRupees ? t("fbar.payAtLeast", { amount: rupees(payRupees) }) : null}
          active={payRupees != null}
          onOpen={() => setPayMin(payRupees)}
          onApply={() =>
            onChange(
              payMin
                ? { ...f, pay_kind: "monthly", pay_min_paise: payMin * 100, pay_max_paise: null }
                : { ...f, pay_kind: null, pay_min_paise: null, pay_max_paise: null },
            )
          }
          onClear={() => onChange({ ...f, pay_kind: null, pay_min_paise: null, pay_max_paise: null })}
        >
          <ChoiceList
            name={t("fbar.pay")}
            value={payMin}
            onChange={setPayMin}
            options={[{ value: null, label: t("fbar.payAny") }, ...PAY_PRESETS.map((p) => ({ value: p, label: t("fbar.payAtLeast", { amount: rupees(p) }) }))]}
          />
        </FilterDropdown>

        <FilterDropdown
          label={t("fbar.posted")}
          value={f.posted_within ? t(`posted.${f.posted_within}`) : null}
          active={!!f.posted_within}
          width={260}
          onOpen={() => setPosted(f.posted_within ?? null)}
          onApply={() => onChange({ ...f, posted_within: posted })}
          onClear={() => onChange({ ...f, posted_within: null })}
        >
          <ChoiceList
            name={t("fbar.posted")}
            value={posted ?? null}
            onChange={setPosted}
            options={[{ value: null, label: t("posted.any") }, ...POSTED.map((p) => ({ value: p, label: t(`posted.${p}`) }))]}
          />
        </FilterDropdown>

        <FilterDropdown
          label={t("fbar.more")}
          value={moreCount ? t("fbar.moreCount", { count: moreCount }) : null}
          active={moreCount > 0}
          width={340}
          onOpen={() => setMore({ work_mode: f.work_mode ?? null, shift: f.shift ?? null, experience: f.experience ?? null, verified_only: !!f.verified_only })}
          onApply={() => onChange({ ...f, ...more })}
          onClear={() => onChange({ ...f, work_mode: null, shift: null, experience: null, verified_only: false })}
        >
          <div className="vy-fdd-sections">
            <label className="vy-fdd-switch">
              <span>{t("fbar.verifiedOnly")}</span>
              <input
                type="checkbox"
                role="switch"
                checked={!!more.verified_only}
                onChange={(e) => setMore((m) => ({ ...m, verified_only: e.target.checked }))}
              />
            </label>
            <fieldset className="vy-fdd-seg">
              <legend>{t("fbar.workMode")}</legend>
              <div className="vy-segmented">
                {[null, ...MODES].map((m) => (
                  <button key={String(m)} type="button" aria-pressed={(more.work_mode ?? null) === m} onClick={() => setMore((x) => ({ ...x, work_mode: m }))}>
                    {m ? t(`workMode.${m}`) : t("filters.anyMode")}
                  </button>
                ))}
              </div>
            </fieldset>
            <fieldset className="vy-fdd-seg">
              <legend>{t("fbar.shift")}</legend>
              <div className="vy-segmented">
                {[null, ...SHIFTS].map((s) => (
                  <button key={String(s)} type="button" aria-pressed={(more.shift ?? null) === s} onClick={() => setMore((x) => ({ ...x, shift: s }))}>
                    {s ? t(`shift.${s}`) : t("shift.any")}
                  </button>
                ))}
              </div>
            </fieldset>
            <fieldset className="vy-fdd-seg">
              <legend>{t("fbar.experience")}</legend>
              <div className="vy-segmented">
                {[null, ...EXPERIENCE].map((x) => (
                  <button key={String(x)} type="button" aria-pressed={(more.experience ?? null) === x} onClick={() => setMore((m) => ({ ...m, experience: x }))}>
                    {x ? t(`experience.${x}`) : t("experience.any")}
                  </button>
                ))}
              </div>
            </fieldset>
          </div>
        </FilterDropdown>
      </div>
    </div>
  );
}
