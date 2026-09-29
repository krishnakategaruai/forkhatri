"use client";

// [FE2 — owner review of Discover filters, 2026-09-29; research §6]
// The filters, as ONE panel used in two places: the slim sticky desktop
// sidebar (every tap applies at once) and the phone bottom sheet (applies
// on "Show N results"). Sort is NOT in here — it sits in the results header.
//
// Compared with the chip wall it replaces: sections are collapsible (the
// most used open), every option shows how many posts it would give (facet
// counts from the results endpoint, each counted with the OTHER filters
// applied), long option lists are checkboxes/radios rather than pills, and
// "Clear all" is at the top. Pay has a monthly-salary / project-budget
// switch, ₹ min–max fields with the amount echoed in Indian format, and
// quick presets. Shift appears only when jobs are in scope.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { FacetCount, FeedFacets, FeedFilterValues } from "@/lib/sdk";
import { formatRupees, rupeesToPaise, paiseToInput } from "@/lib/format";
import { EMPTY_FILTERS, activeCount } from "./feedFilters";
import { displayTitle } from "./DiscoverCard";

const MAIN_TYPES = ["employment", "freelance", "local_service"];
const MORE_TYPES = ["partnership", "training", "community"];
const MONTHLY_PRESETS = [10_000, 15_000, 20_000, 30_000];
const PROJECT_PRESETS = [5_000, 25_000, 50_000, 1_00_000];

function countOf(list: FacetCount[] | undefined, value: string): number | null {
  const hit = list?.find((f) => f.value === value);
  return hit ? hit.count : null;
}

function Section({ id, title, open, onToggle, children }: { id: string; title: string; open: boolean; onToggle: () => void; children: React.ReactNode }) {
  return (
    <section className="vy-fsec">
      <button type="button" className="vy-fsec-head" aria-expanded={open} aria-controls={`fsec-${id}`} onClick={onToggle}>
        <span>{title}</span>
        <span aria-hidden="true" className="vy-fsec-caret">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div id={`fsec-${id}`} className="vy-fsec-body">
          {children}
        </div>
      )}
    </section>
  );
}

function Option({
  type,
  name,
  checked,
  label,
  count,
  onChange,
}: {
  type: "checkbox" | "radio";
  name: string;
  checked: boolean;
  label: string;
  count: number | null;
  onChange: () => void;
}) {
  return (
    <label className="vy-fopt" data-empty={count === 0 && !checked ? "" : undefined}>
      <input type={type} name={name} checked={checked} onChange={onChange} />
      <span className="vy-fopt-label">{label}</span>
      {count !== null && <span className="vy-fopt-count">{count}</span>}
    </label>
  );
}

export default function FilterPanel({
  value,
  onChange,
  facets,
}: {
  value: FeedFilterValues;
  onChange: (next: FeedFilterValues) => void;
  facets: FeedFacets | null;
}) {
  const { t, i18n } = useTranslation(["explore"]);
  const [open, setOpen] = useState<Record<string, boolean>>({ kind: true, pay: true, posted: true, skills: true, mode: false, shift: false, exp: false });
  const [moreKinds, setMoreKinds] = useState(() => (value.types ?? []).some((x) => MORE_TYPES.includes(x)));
  const [skillSearch, setSkillSearch] = useState("");
  const toggle = (k: string) => setOpen((o) => ({ ...o, [k]: !o[k] }));
  const set = (patch: Partial<FeedFilterValues>) => onChange({ ...value, ...patch });
  const types = value.types ?? [];
  const jobsInScope = types.length === 0 || types.includes("employment");
  const payKind = value.pay_kind ?? "monthly";
  const presets = payKind === "monthly" ? MONTHLY_PRESETS : PROJECT_PRESETS;
  const money = (p: number) => formatRupees(p, i18n.language);

  const toggleType = (x: string) => set({ types: types.includes(x) ? types.filter((y) => y !== x) : [...types, x] });
  const skills = value.skills ?? [];
  const skillFacets = (facets?.skills ?? []).filter((s) => !skillSearch || (s.label ?? s.value).toLowerCase().includes(skillSearch.toLowerCase()));

  return (
    <div className="vy-fpanel">
      <div className="vy-fpanel-head">
        <strong>{t("explore:filters.title")}</strong>
        {activeCount(value) > 0 && (
          <button type="button" className="vy-link-btn" onClick={() => onChange({ ...EMPTY_FILTERS, q: value.q, sort: value.sort })}>
            {t("explore:filters.clearAll")}
          </button>
        )}
      </div>

      <Section id="kind" title={t("explore:filters.type")} open={open.kind} onToggle={() => toggle("kind")}>
        {[...MAIN_TYPES, ...(moreKinds ? MORE_TYPES : [])].map((x) => (
          <Option key={x} type="checkbox" name="kind" checked={types.includes(x)} label={t(`explore:type.${x}`)} count={countOf(facets?.type, x)} onChange={() => toggleType(x)} />
        ))}
        {!moreKinds && (
          <button type="button" className="vy-link-btn" onClick={() => setMoreKinds(true)}>
            {t("explore:filters.moreKinds")}
          </button>
        )}
      </Section>

      <Section id="pay" title={t("explore:filters.pay")} open={open.pay} onToggle={() => toggle("pay")}>
        <div className="vy-segmented" role="group" aria-label={t("explore:filters.pay")}>
          {(["monthly", "project"] as const).map((k) => (
            <button key={k} type="button" aria-pressed={payKind === k} onClick={() => set({ pay_kind: k, pay_min_paise: null, pay_max_paise: null })}>
              {t(`explore:filters.payKind.${k}`)}
            </button>
          ))}
        </div>
        <div className="vy-pay-range">
          <label className="vy-field">
            <span className="vy-label">{t("explore:filters.payMin")}</span>
            <input
              className="vy-input"
              inputMode="numeric"
              value={paiseToInput(value.pay_min_paise ?? null)}
              onChange={(e) => set({ pay_kind: payKind, pay_min_paise: rupeesToPaise(e.target.value) })}
            />
          </label>
          <label className="vy-field">
            <span className="vy-label">{t("explore:filters.payMax")}</span>
            <input
              className="vy-input"
              inputMode="numeric"
              value={paiseToInput(value.pay_max_paise ?? null)}
              onChange={(e) => set({ pay_kind: payKind, pay_max_paise: rupeesToPaise(e.target.value) })}
            />
          </label>
        </div>
        {(value.pay_min_paise != null || value.pay_max_paise != null) && (
          <p className="vy-muted">
            {value.pay_min_paise != null && value.pay_max_paise != null
              ? t("explore:filters.payEchoRange", { min: money(value.pay_min_paise), max: money(value.pay_max_paise) })
              : value.pay_min_paise != null
                ? t("explore:filters.payEchoMin", { min: money(value.pay_min_paise) })
                : t("explore:filters.payEchoMax", { max: money(value.pay_max_paise ?? 0) })}
            {" "}
            {payKind === "monthly" ? t("explore:filters.perMonth") : ""}
          </p>
        )}
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
          {presets.map((r) => (
            <button
              key={r}
              type="button"
              className="vy-chip"
              aria-pressed={value.pay_min_paise === r * 100 && value.pay_kind === payKind}
              onClick={() => set({ pay_kind: payKind, pay_min_paise: r * 100, pay_max_paise: null })}
            >
              {money(r * 100)}+
            </button>
          ))}
        </div>
      </Section>

      <Section id="posted" title={t("explore:filters.posted")} open={open.posted} onToggle={() => toggle("posted")}>
        {(["today", "week", "month"] as const).map((x) => (
          <Option key={x} type="radio" name="posted" checked={value.posted_within === x} label={t(`explore:posted.${x}`)} count={countOf(facets?.posted_within, x)} onChange={() => set({ posted_within: x })} />
        ))}
        <Option type="radio" name="posted" checked={!value.posted_within} label={t("explore:posted.any")} count={null} onChange={() => set({ posted_within: null })} />
      </Section>

      <Section id="mode" title={t("explore:filters.workMode")} open={open.mode || !!value.work_mode} onToggle={() => toggle("mode")}>
        {(["on_site", "remote", "both"] as const).map((x) => (
          <Option key={x} type="radio" name="mode" checked={value.work_mode === x} label={t(`explore:workMode.${x}`)} count={countOf(facets?.work_mode, x)} onChange={() => set({ work_mode: x })} />
        ))}
        <Option type="radio" name="mode" checked={!value.work_mode} label={t("explore:filters.anyMode")} count={null} onChange={() => set({ work_mode: null })} />
      </Section>

      {jobsInScope && (
        <Section id="shift" title={t("explore:filters.shift")} open={open.shift || !!value.shift} onToggle={() => toggle("shift")}>
          {(["day", "night", "flexible"] as const).map((x) => (
            <Option key={x} type="radio" name="shift" checked={value.shift === x} label={t(`explore:shift.${x}`)} count={countOf(facets?.shift, x)} onChange={() => set({ shift: x })} />
          ))}
          <Option type="radio" name="shift" checked={!value.shift} label={t("explore:shift.any")} count={null} onChange={() => set({ shift: null })} />
        </Section>
      )}

      <Section id="exp" title={t("explore:filters.experience")} open={open.exp || !!value.experience} onToggle={() => toggle("exp")}>
        {(["fresher", "1", "3"] as const).map((x) => (
          <Option key={x} type="radio" name="exp" checked={value.experience === x} label={t(`explore:experience.${x}`)} count={countOf(facets?.experience, x)} onChange={() => set({ experience: x })} />
        ))}
        <Option type="radio" name="exp" checked={!value.experience} label={t("explore:experience.any")} count={null} onChange={() => set({ experience: null })} />
      </Section>

      <Section id="skills" title={t("explore:filters.skills")} open={open.skills} onToggle={() => toggle("skills")}>
        <input className="vy-input" value={skillSearch} onChange={(e) => setSkillSearch(e.target.value)} placeholder={t("explore:filters.skillsSearch")} aria-label={t("explore:filters.skillsSearch")} />
        {skillFacets.map((s) => (
          <Option
            key={s.value}
            type="checkbox"
            name="skills"
            checked={skills.includes(s.value)}
            label={displayTitle(s.label ?? s.value)}
            count={s.count}
            onChange={() => set({ skills: skills.includes(s.value) ? skills.filter((x) => x !== s.value) : [...skills, s.value] })}
          />
        ))}
        {facets && skillFacets.length === 0 && <p className="vy-muted">{t("explore:filters.noSkills")}</p>}
      </Section>

      <label className="vy-fopt vy-fverified">
        <span className="vy-fopt-label">{t("explore:filters.verifiedOnly")}</span>
        {facets && <span className="vy-fopt-count">{facets.verified}</span>}
        <input type="checkbox" role="switch" checked={!!value.verified_only} onChange={(e) => set({ verified_only: e.target.checked })} />
      </label>
    </div>
  );
}
