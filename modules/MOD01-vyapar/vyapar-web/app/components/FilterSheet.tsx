"use client";

// [Real regression fix — coordinator's product-owner direction, verbatim:
// "We also need location and location-based opportunities, and we need
// sort-by conditions."] FR15 names radius/service-mode/availability/
// verification/freshness as real, structured filters, and organic
// relevance as text-match/category/distance/verification/freshness,
// configuration-weighted. The IntentBar's free-text field had quietly
// become the ONLY way to narrow results — this panel restores the actual
// structured filters as a real, always-reachable control (a "Filters"
// button that expands in place, not a hidden setting), on top of whichever
// free-text/parsed shortcut IntentBar already applied. Shared between the
// Businesses & Professionals surface and (once wired) the Discover feed,
// so there is exactly one filter-panel implementation, not a second
// divergent one per surface.
// Traces to: FR15, FR17, FR19
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";

export interface Filters {
  radius_km?: number;
  service_mode?: "on_site" | "remote" | "both";
  availability?: "now" | "this_week" | "later";
  verified_only?: boolean;
  sort_by: "relevance" | "distance" | "freshness" | "verified_first";
  // [Original-Vyapar upgrade, product-owner direction: "based on skills we
  // need list to be flown"] explicit, member-controlled skill/capability
  // filter — reuses the same taxonomy capability list first-run's own
  // picker already fetches, same pattern as categories.
  skills?: string[];
}

export const DEFAULT_FILTERS: Filters = { sort_by: "relevance" };

const RADIUS_STEPS = [5, 10, 25];

export function activeFilterCount(f: Filters): number {
  let n = 0;
  if (f.radius_km) n++;
  if (f.service_mode) n++;
  if (f.availability) n++;
  if (f.verified_only) n++;
  if (f.sort_by !== "relevance") n++;
  if (f.skills && f.skills.length > 0) n++;
  return n;
}

interface SkillOption {
  slug: string;
  label: string;
}

export default function FilterSheet({
  filters,
  onChange,
  namespace = "discover",
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  namespace?: string;
}) {
  const { t, i18n } = useTranslation([namespace]);
  const sdk = useSdk();
  const ns = (key: string) => `${namespace}:businesses.${key}` as "discover.businesses.filters";
  const [skillOptions, setSkillOptions] = useState<SkillOption[]>([]);
  const [skillSearch, setSkillSearch] = useState("");

  // [Real bug found live by the product owner, fixed here] this fetch's
  // `X-Vyapar-Language` header is set once, at fetch time, by lib/api.ts —
  // an empty dependency array meant it never ran again on a language
  // switch while the sheet stayed open, so the surrounding labels (all
  // static translation-file strings, re-rendered live by react-i18next)
  // updated instantly but this fetched chip data stayed in whatever
  // language was active when the effect first ran. `i18n.language` in the
  // dependency array makes the general rule hold: "make language also
  // live" — a switch must never leave any visible content, fetched or
  // static, in the old language.
  useEffect(() => {
    sdk.firstRun.capabilityOptions<SkillOption[]>().then(setSkillOptions);
  }, [i18n.language, sdk]);

  function toggleSkill(slug: string) {
    const current = filters.skills ?? [];
    onChange({ ...filters, skills: current.includes(slug) ? current.filter((s) => s !== slug) : [...current, slug] });
  }

  return (
    // [Design-enhancement pass, DESIGN-ENHANCEMENT.md — named example]
    // FilterSheet, when expanded, is genuinely-overlaid content — steps to
    // --surface-floating.
    <div className="vy-card vy-card-floating vy-stack" style={{ gap: 14 }}>
      <div className="vy-stack" style={{ gap: 6 }}>
        <span className="vy-label">{t(ns("radius"))}</span>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <button
            className="vy-chip"
            aria-pressed={!filters.radius_km}
                style={{ cursor: "pointer" }}
            onClick={() => onChange({ ...filters, radius_km: undefined })}
          >
            {t(ns("radiusAny"))}
          </button>
          {RADIUS_STEPS.map((km) => (
            <button
              key={km}
              className="vy-chip"
              aria-pressed={filters.radius_km === km}
                style={{ cursor: "pointer" }}
              onClick={() => onChange({ ...filters, radius_km: km })}
            >
              {t(ns("radiusKm"), { km })}
            </button>
          ))}
        </div>
      </div>

      <label className="vy-field">
        <span className="vy-label">{t(ns("serviceMode"))}</span>
        <select
          className="vy-select"
          value={filters.service_mode ?? ""}
          onChange={(e) => onChange({ ...filters, service_mode: (e.target.value || undefined) as Filters["service_mode"] })}
        >
          <option value="">{t(ns("serviceModeAny"))}</option>
          <option value="on_site">{t(ns("serviceModeOnSite"))}</option>
          <option value="remote">{t(ns("serviceModeRemote"))}</option>
          <option value="both">{t(ns("serviceModeBoth"))}</option>
        </select>
      </label>

      <label className="vy-field">
        <span className="vy-label">{t(ns("availability"))}</span>
        <select
          className="vy-select"
          value={filters.availability ?? ""}
          onChange={(e) => onChange({ ...filters, availability: (e.target.value || undefined) as Filters["availability"] })}
        >
          <option value="">{t(ns("availabilityAny"))}</option>
          <option value="now">{t(ns("availabilityNow"))}</option>
          <option value="this_week">{t(ns("availabilityThisWeek"))}</option>
          <option value="later">{t(ns("availabilityLater"))}</option>
        </select>
      </label>

      <label className="vy-row" style={{ gap: 8, cursor: "pointer" }}>
        <input type="checkbox" checked={!!filters.verified_only} onChange={(e) => onChange({ ...filters, verified_only: e.target.checked })} />
        <span>{t(ns("verifiedOnly"))}</span>
      </label>

      <label className="vy-field">
        <span className="vy-label">{t(ns("sortBy"))}</span>
        <select className="vy-select" value={filters.sort_by} onChange={(e) => onChange({ ...filters, sort_by: e.target.value as Filters["sort_by"] })}>
          <option value="relevance">{t(ns("sortRelevance"))}</option>
          <option value="distance">{t(ns("sortDistance"))}</option>
          <option value="freshness">{t(ns("sortFreshness"))}</option>
          <option value="verified_first">{t(ns("sortVerifiedFirst"))}</option>
        </select>
      </label>

      <div className="vy-stack" style={{ gap: 6 }}>
        <span className="vy-label">{t(ns("skills"))}</span>
        <input
          className="vy-input"
          value={skillSearch}
          onChange={(e) => setSkillSearch(e.target.value)}
          placeholder={t(ns("skillsSearchPlaceholder"))}
        />
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {skillOptions
            .filter((s) => s.label.toLowerCase().includes(skillSearch.toLowerCase()))
            .map((s) => (
              <button
                key={s.slug}
                className="vy-chip"
                aria-pressed={(filters.skills ?? []).includes(s.slug)}
                style={{ cursor: "pointer" }}
                onClick={() => toggleSkill(s.slug)}
              >
                {(filters.skills ?? []).includes(s.slug) ? "✓ " : ""}{s.label}
              </button>
            ))}
        </div>
      </div>

      {activeFilterCount(filters) > 0 && (
        <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => onChange(DEFAULT_FILTERS)}>
          {t(ns("clearFilters"))}
        </button>
      )}
    </div>
  );
}
