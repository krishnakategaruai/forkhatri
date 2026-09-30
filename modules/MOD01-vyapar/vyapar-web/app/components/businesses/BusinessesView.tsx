"use client";

// [2026-09-30 rebuild — owner, on the old screen: "boring and weak"; a
// title, a floating "My profiles" link, a plain input, a giant full-width
// Search button, a lone Filters pill and a "near: Ameerpet" chip] The
// directory now reads like Discover:
//   Opportunities | Businesses tabs (the same switch, Businesses selected)
//   one search pill — icon, field, mic, clear; results update as you type
//   a sticky dropdown bar: Trade · Distance · Available · Verified · More
//   a count line and "My profiles" as a quiet link beside it
//   profile cards (trade icon, name, what they do, distance, reputation,
//   one trust signal, Ask for a price / Call where the owner allows it)
// Zero results keep FR17's labelled broadening options (never silent).
// Data in, events out; the only local state is each filter's draft.
import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Briefcase, BadgeCheck, Search, Store, X, SearchX, UserRound } from "lucide-react";
import type { BroadeningOption, SearchResponse } from "@/lib/sdk";
import type { Filters } from "@/app/components/FilterSheet";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import FilterDropdown, { ChoiceList } from "@/app/components/filters/FilterDropdown";
import TradePicker, { tradeValue, useTaxonomy } from "@/app/components/filters/TradePicker";
import ProfileCard from "./ProfileCard";
import { useRoutes } from "@/app/host/HostProvider";

export type BizFilters = Filters & { category?: string | null; locality?: string | null };

export interface BusinessesViewProps {
  query: string;
  onQuery: (q: string) => void;
  response: SearchResponse | null;
  loading: boolean;
  filters: BizFilters;
  onFiltersChange: (next: BizFilters) => void;
  onBroaden: (optionId: string) => void;
}

const AVAIL = ["now", "this_week", "later"] as const;
const AVAIL_KEY: Record<(typeof AVAIL)[number], string> = { now: "availNow", this_week: "availWeek", later: "availLater" };
const MODES = ["on_site", "remote", "both"] as const;
const MODE_KEY: Record<(typeof MODES)[number], string> = { on_site: "modeOnSite", remote: "modeRemote", both: "modeBoth" };
const SORTS = ["relevance", "distance", "freshness", "verified_first"] as const;
const SORT_KEY: Record<(typeof SORTS)[number], string> = {
  relevance: "sortRelevance",
  distance: "sortDistance",
  freshness: "sortFreshness",
  verified_first: "sortVerified",
};

function useNarrow() {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 599px)");
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return narrow;
}

function SkeletonCards() {
  return (
    <div className="vy-dgrid2" aria-busy="true">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="vy-card vy-ocard vy-ocard-skel" aria-hidden="true">
          <div className="vy-skeleton" style={{ width: 44, height: 44, borderRadius: 14 }} />
          <div className="vy-skeleton" style={{ height: 18, width: "80%" }} />
          <div className="vy-skeleton" style={{ height: 14, width: "60%" }} />
          <div className="vy-skeleton" style={{ height: 14, width: "45%" }} />
        </div>
      ))}
    </div>
  );
}

export default function BusinessesView({ query, onQuery, response, loading, filters: f, onFiltersChange, onBroaden }: BusinessesViewProps) {
  const { t } = useTranslation(["discover", "explore", "common"]);
  const routes = useRoutes();
  const narrow = useNarrow();
  const { categories, labelOf } = useTaxonomy();

  // Filter drafts, reset whenever a panel opens.
  const [skills, setSkills] = useState<string[]>([]);
  const [km, setKm] = useState<number | null>(null);
  const [avail, setAvail] = useState<Filters["availability"] | null>(null);
  const [mode, setMode] = useState<Filters["service_mode"] | null>(null);
  const [sort, setSort] = useState<Filters["sort_by"]>("relevance");

  const tradeShown =
    tradeValue(f.skills ?? [], categories, labelOf, (first, count) => t("explore:fbar.tradeMore", { first, count })) ??
    (f.category ? labelOf(f.category) : null);
  const moreCount = (f.service_mode ? 1 : 0) + (f.sort_by !== "relevance" ? 1 : 0);

  function broadeningLabel(o: BroadeningOption): string {
    if (o.label === "radius") return t("discover:broaden.radius", { km: o.id.replace("radius_", "") });
    return t(`discover:broaden.${o.label}` as "broaden.remove_filter");
  }

  // Your own profile is not something you are looking for: it goes last.
  const results = [...(response?.results ?? [])].sort((a, b) => Number(!!a.listing.is_owner) - Number(!!b.listing.is_owner));
  const sponsored = response?.sponsored ?? [];

  return (
    <div className="vy-biz">
      <section className="vy-hero vy-biz-hero" aria-labelledby="vy-biz-title">
        <div className="vy-biz-head">
          <h1 id="vy-biz-title" className="vy-biz-title">
            {t("discover:businesses.title")}
          </h1>
          <p className="vy-hero-sub vy-biz-sub">{t("explore:biz.subtitle")}</p>
        </div>

        <div className="vy-hero-tabs" role="tablist" aria-label={t("explore:top.switchLabel")}>
          <Link role="tab" aria-selected="false" href="/" className="vy-hero-tab">
            <Briefcase size={18} strokeWidth={2} aria-hidden="true" />
            {t("explore:top.opportunities")}
          </Link>
          <span role="tab" aria-selected="true" className="vy-hero-tab">
            <Store size={18} strokeWidth={2} aria-hidden="true" />
            <span className="vy-hero-tab-long">{t("explore:top.businesses")}</span>
            <span className="vy-hero-tab-short">{t("common:nav.businesses")}</span>
          </span>
        </div>

        <form className="vy-hero-search" role="search" onSubmit={(e) => e.preventDefault()}>
          <div className="vy-hero-what">
            <Search size={20} strokeWidth={2} className="vy-hero-search-icon" aria-hidden="true" />
            <VoiceInput fieldLabel={t("explore:biz.searchShort")} compact onConfirm={(spoken) => onQuery(appendSpoken(query, spoken))}>
              <input
                className="vy-hero-input"
                type="search"
                enterKeyHint="search"
                value={query}
                onChange={(e) => onQuery(e.target.value)}
                placeholder={narrow ? t("explore:biz.searchShort") : t("explore:biz.searchPlaceholder")}
                aria-label={t("explore:biz.searchShort")}
              />
            </VoiceInput>
            {query && (
              <button type="button" className="vy-hero-clear" aria-label={t("explore:top.clearSearch")} onClick={() => onQuery("")}>
                <X size={16} strokeWidth={2.25} aria-hidden="true" />
              </button>
            )}
          </div>
        </form>
      </section>

      <div className="vy-fbar" role="group" aria-label={t("explore:fbar.label")}>
        <div className="vy-fbar-row">
          <FilterDropdown
            label={t("explore:fbar.trade")}
            value={tradeShown}
            active={!!tradeShown}
            width={360}
            onOpen={() => setSkills([...(f.skills ?? [])])}
            onApply={() => onFiltersChange({ ...f, skills, category: skills.length ? null : f.category })}
            onClear={() => onFiltersChange({ ...f, skills: [], category: null })}
          >
            <TradePicker value={skills} onChange={setSkills} />
          </FilterDropdown>

          <FilterDropdown
            label={t("explore:fbar.distance")}
            value={f.radius_km ? t("explore:fbar.km", { km: f.radius_km }) : null}
            active={!!f.radius_km}
            onOpen={() => setKm(f.radius_km ?? 10)}
            onApply={() => onFiltersChange({ ...f, radius_km: km ?? undefined })}
            onClear={() => onFiltersChange({ ...f, radius_km: undefined })}
          >
            <div className="vy-fdd-range">
              <div className="vy-fdd-range-head">
                <strong className="vy-num">{km ? t("explore:fbar.km", { km }) : t("explore:fbar.anyDistance")}</strong>
              </div>
              <input type="range" min={1} max={50} value={km ?? 50} onChange={(e) => setKm(Number(e.target.value))} aria-label={t("explore:fbar.distance")} />
            </div>
          </FilterDropdown>

          <FilterDropdown
            label={t("explore:fbar.available")}
            value={f.availability ? t(`explore:fbar.${AVAIL_KEY[f.availability]}`) : null}
            active={!!f.availability}
            width={260}
            onOpen={() => setAvail(f.availability ?? null)}
            onApply={() => onFiltersChange({ ...f, availability: avail ?? undefined })}
            onClear={() => onFiltersChange({ ...f, availability: undefined })}
          >
            <ChoiceList
              name={t("explore:fbar.available")}
              value={avail ?? null}
              onChange={setAvail}
              options={[{ value: null, label: t("explore:fbar.availAny") }, ...AVAIL.map((a) => ({ value: a, label: t(`explore:fbar.${AVAIL_KEY[a]}`) }))]}
            />
          </FilterDropdown>

          <FilterDropdown
            label={t("explore:fbar.verified")}
            icon={<BadgeCheck size={16} strokeWidth={2} aria-hidden="true" />}
            active={!!f.verified_only}
            toggle={() => onFiltersChange({ ...f, verified_only: !f.verified_only })}
          />

          <FilterDropdown
            label={t("explore:fbar.more")}
            value={moreCount ? t("explore:fbar.moreCount", { count: moreCount }) : null}
            active={moreCount > 0}
            width={320}
            onOpen={() => {
              setMode(f.service_mode ?? null);
              setSort(f.sort_by);
            }}
            onApply={() => onFiltersChange({ ...f, service_mode: mode ?? undefined, sort_by: sort })}
            onClear={() => onFiltersChange({ ...f, service_mode: undefined, sort_by: "relevance" })}
          >
            <div className="vy-fdd-sections">
              <fieldset className="vy-fdd-seg">
                <legend>{t("explore:fbar.serviceMode")}</legend>
                <ChoiceList
                  name={t("explore:fbar.serviceMode")}
                  value={mode ?? null}
                  onChange={setMode}
                  options={[{ value: null, label: t("explore:fbar.modeAny") }, ...MODES.map((m) => ({ value: m, label: t(`explore:fbar.${MODE_KEY[m]}`) }))]}
                />
              </fieldset>
              <fieldset className="vy-fdd-seg">
                <legend>{t("explore:fbar.sort")}</legend>
                <ChoiceList
                  name={t("explore:fbar.sort")}
                  value={sort}
                  onChange={setSort}
                  options={SORTS.map((s) => ({ value: s, label: t(`explore:fbar.${SORT_KEY[s]}`) }))}
                />
              </fieldset>
            </div>
          </FilterDropdown>
        </div>
      </div>

      <div className="vy-biz-meta">
        <p className="vy-biz-count" role="status" aria-live="polite">
          {response ? t("explore:biz.count", { count: results.length }) : " "}
        </p>
        <Link className="vy-link-btn vy-biz-mine" href={routes.myListings}>
          <UserRound size={16} strokeWidth={2} aria-hidden="true" />
          {t("common:action.myListings")}
        </Link>
      </div>

      {response?.degraded && response.notice && <p className="vy-muted">{t(`discover:notice.${response.notice}` as "notice.degraded")}</p>}

      {loading && !response ? (
        <SkeletonCards />
      ) : results.length > 0 || sponsored.length > 0 ? (
        <div className="vy-dgrid2" data-loading={loading ? "" : undefined}>
          {sponsored.map((r) => (
            <ProfileCard key={`s-${r.listing.id}`} result={r} sponsored />
          ))}
          {results.map((r) => (
            <ProfileCard key={r.listing.id} result={r} />
          ))}
        </div>
      ) : response ? (
        <div className="vy-empty">
          <span className="vy-empty-mark" aria-hidden="true">
            <SearchX size={26} strokeWidth={1.8} />
          </span>
          <h2 className="vy-card-title">{t(`discover:notice.${response.notice ?? "noMatch"}` as "notice.noMatch")}</h2>
          <div className="vy-row" style={{ flexWrap: "wrap", justifyContent: "center", gap: 8 }}>
            {response.broadening_options.map((o) => (
              <button key={o.id} type="button" className="vy-btn vy-btn-secondary" onClick={() => onBroaden(o.id)}>
                {broadeningLabel(o)}
              </button>
            ))}
            {response.fallback && (
              <a className="vy-btn vy-btn-ghost" href={response.fallback.post_link}>
                {t("discover:businesses.postWhatYouNeed")}
              </a>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
