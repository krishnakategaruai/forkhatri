"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { ArrowDownUp, MapPin, Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { api, type Card, type Expertise } from "@/lib/api";
import { locate, saveNear, savedNear, usePlaces } from "@/lib/places";
import { SUPPORTED_LANGUAGES } from "@/lib/i18n/config";
import { ProviderCard } from "@/components/ProviderCard";
import { Empty, Skeleton, useToast } from "@/components/ui";

type Understood = { filters: { areas: string[]; duration_max: number | null; max_price: number | null; keywords: string[] }; results: Card[] };
type V = { q: string; area: string; min: string; max: string; lang: string; verified: boolean; sort: string; now: boolean; near: string; nearby: boolean; soon: boolean; rating: string };

const SORTS = ["best", "rating", "consultations", "soonest", "price_asc", "price_desc", "newest", "experience"] as const;
const LOCATE = "__locate";
const SOON_HOURS = 24;

function Discover() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const toast = useToast();
  const sp = useSearchParams();
  const need = sp.get("need") ?? "";
  const fromUrl = (): V => ({
    q: sp.get("q") ?? need, area: sp.get("area") ?? "", min: sp.get("min") ?? "", max: sp.get("max") ?? "", lang: sp.get("lang") ?? "",
    verified: sp.get("verified") === "1", sort: sp.get("sort") ?? "best", now: sp.get("now") === "1", near: sp.get("near") ?? "",
    nearby: sp.get("nearby") === "1", soon: sp.get("soon") === "1", rating: sp.get("rating") ?? "",
  });
  const [v, setV] = useState<V>(fromUrl);
  const set = (over: Partial<V>) => setV((s) => ({ ...s, ...over }));
  const [showFilters, setShowFilters] = useState(false);
  const [areas, setAreas] = useState<Expertise[]>([]);
  const [results, setResults] = useState<Card[] | null>(null);
  const [understood, setUnderstood] = useState<Understood["filters"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [locating, setLocating] = useState(false);
  const places = usePlaces(i18n.language);
  const cities = places?.cities ?? [];
  const nearName = cities.find((c) => c.id === v.near)?.name;

  useEffect(() => { void api<Expertise[]>("/expertise").then(setAreas); }, []);

  // A city chosen earlier on this device is used again (it only adds distances; it never hides anyone).
  useEffect(() => {
    if (sp.get("near") || need) return;
    const saved = savedNear();
    if (saved) apply({ near: saved }, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const key = sp.toString();
  useEffect(() => {
    let alive = true;
    setLoading(true);
    setV(fromUrl());
    const run = async () => {
      if (need) {
        const u = await api<Understood>("/understand", { body: { text: need } });
        if (!alive) return;
        setUnderstood(u.filters);
        if (u.filters.areas[0]) set({ area: u.filters.areas[0] });
        setResults(u.results);
      } else {
        const s = fromUrl();
        const p = new URLSearchParams();
        if (s.q) p.set("q", s.q);
        if (s.area) p.set("area", s.area);
        if (s.min) p.set("min_price", s.min);
        if (s.max) p.set("max_price", s.max);
        if (s.lang) p.set("language", s.lang);
        if (s.verified) p.set("verified", "true");
        if (s.sort) p.set("sort", s.sort === "nearest" && !s.near ? "best" : s.sort);
        if (s.now) p.set("now", "true");
        if (s.near) p.set("near", s.near);
        if (s.near && s.nearby) p.set("nearby", "true");
        if (s.soon) p.set("within_hours", String(SOON_HOURS));
        if (s.rating) p.set("min_rating", s.rating);
        const r = await api<Card[]>(`/search?${p.toString()}`);
        if (!alive) return;
        setUnderstood(null);
        setResults(r);
      }
    };
    void run().finally(() => alive && setLoading(false));
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  function apply(over: Partial<V> = {}, replace = false) {
    const s = { ...v, ...over };
    const p = new URLSearchParams();
    if (s.q) p.set("q", s.q);
    if (s.area) p.set("area", s.area);
    if (s.min) p.set("min", s.min);
    if (s.max) p.set("max", s.max);
    if (s.lang) p.set("lang", s.lang);
    if (s.verified) p.set("verified", "1");
    if (s.sort && s.sort !== "best" && !(s.sort === "nearest" && !s.near)) p.set("sort", s.sort);
    if (s.now) p.set("now", "1");
    if (s.near) p.set("near", s.near);
    if (s.near && s.nearby) p.set("nearby", "1");
    if (s.soon) p.set("soon", "1");
    if (s.rating) p.set("rating", s.rating);
    const url = `/discover?${p.toString()}`;
    if (replace) router.replace(url); else router.push(url);
  }

  const chooseNear = async (id: string) => {
    if (id !== LOCATE) { saveNear(id); apply({ near: id, ...(id ? {} : { nearby: false, sort: v.sort === "nearest" ? "best" : v.sort }) }); return; }
    setLocating(true);
    const c = await locate(cities);
    setLocating(false);
    if (!c) { toast(t("near.locate_failed")); return; }
    saveNear(c.id);
    apply({ near: c.id });
  };

  const areaName = areas.find((a) => a.id === v.area)?.name;
  const activeFilters = [v.min, v.max, v.lang, v.verified, v.rating].filter(Boolean).length;

  return (
    <div className="wrap page stack">
      <form className="search" onSubmit={(e) => { e.preventDefault(); apply(); }}>
        <Search size={18} className="muted" />
        <input value={v.q} onChange={(e) => set({ q: e.target.value })} placeholder={t("discover.placeholder")} aria-label={t("discover.placeholder")} />
        <button type="button" className="icon-btn filter-btn" aria-label={t("discover.filters")} aria-expanded={showFilters} onClick={() => setShowFilters((s) => !s)}>
          <SlidersHorizontal size={18} />{activeFilters > 0 && <span className="dot-count">{activeFilters}</span>}
        </button>
        <button className="btn btn-primary btn-sm" type="submit">{t("discover.search")}</button>
      </form>

      {understood && (
        <div className="card card-pad row small fade-in">
          <Sparkles size={16} className="muted" />
          <span className="muted">{t("discover.understood")}</span>
          {understood.areas.map((a) => <span key={a} className="tag">{areas.find((x) => x.id === a)?.name ?? a}</span>)}
          {understood.duration_max && <span className="tag">{t("discover.upto_min", { n: understood.duration_max })}</span>}
          {understood.max_price && <span className="tag">{t("discover.under", { n: understood.max_price })}</span>}
          {understood.keywords.slice(0, 4).map((k) => <span key={k} className="tag">{k}</span>)}
          <button className="link" type="button" onClick={() => { set({ q: "" }); router.push("/discover"); }}>{t("discover.clear")}</button>
        </div>
      )}

      {!need && (
        <div className="toolbar">
          <label className="tool-select">
            <MapPin size={15} className="muted" aria-hidden />
            <span className="sr">{t("near.label")}</span>
            <select value={locating ? LOCATE : v.near} onChange={(e) => void chooseNear(e.target.value)} aria-label={t("near.label")}>
              <option value="">{t("near.anywhere")}</option>
              <option value={LOCATE}>{locating ? t("near.locating") : t("near.use_location")}</option>
              {cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label className="tool-select">
            <ArrowDownUp size={15} className="muted" aria-hidden />
            <span className="sr">{t("discover.sort")}</span>
            <select value={v.sort === "price" ? "price_asc" : v.sort} onChange={(e) => apply({ sort: e.target.value })} aria-label={t("discover.sort")}>
              {SORTS.map((s) => <option key={s} value={s}>{t(`sort.${s}`)}</option>)}
              {v.near && <option value="nearest">{t("sort.nearest")}</option>}
            </select>
          </label>
        </div>
      )}

      {!need && (
        <div className="row" style={{ gap: 8 }}>
          <button className="chip" aria-pressed={v.now} onClick={() => apply({ now: !v.now })}><span className="presence" data-on="true" />{t("offers.available_now")}</button>
          <button className="chip" aria-pressed={v.soon} onClick={() => apply({ soon: !v.soon })}>{t("quick.soon", { n: SOON_HOURS })}</button>
          <button className="chip" aria-pressed={v.rating === "4"} onClick={() => apply({ rating: v.rating === "4" ? "" : "4" })}>{t("quick.rating4")}</button>
          {v.near && nearName && (
            <button className="chip" aria-pressed={v.nearby} onClick={() => apply({ nearby: !v.nearby })}><MapPin size={13} />{t("quick.nearby", { city: nearName, n: places?.nearby_km ?? 150 })}</button>
          )}
        </div>
      )}

      <div className="row" style={{ gap: 8 }}>
        <button className="chip" aria-pressed={!v.area} onClick={() => apply({ area: "" })}>{t("discover.all")}</button>
        {areas.filter((a) => a.providers > 0 || a.id === v.area).map((a) => (
          <button key={a.id} className="chip" aria-pressed={v.area === a.id} onClick={() => apply({ area: a.id })}>{a.name}</button>
        ))}
      </div>

      {showFilters && (
        <div className="card card-pad grid grid-4 fade-in">
          <div className="field"><span className="label">{t("discover.price_range")}</span>
            <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
              <input className="input" inputMode="numeric" value={v.min} onChange={(e) => set({ min: e.target.value.replace(/\D/g, "") })} placeholder={t("discover.min")} aria-label={t("discover.min_price")} />
              <span className="muted">–</span>
              <input className="input" inputMode="numeric" value={v.max} onChange={(e) => set({ max: e.target.value.replace(/\D/g, "") })} placeholder={t("discover.max")} aria-label={t("discover.max_price")} />
            </div></div>
          <label className="field"><span className="label">{t("discover.language")}</span>
            <select className="select" value={v.lang} onChange={(e) => set({ lang: e.target.value })}>
              <option value="">{t("discover.any")}</option>
              {SUPPORTED_LANGUAGES.map((l) => <option key={l} value={l}>{t(`lang.${l}`)}</option>)}
            </select></label>
          <label className="field"><span className="label">{t("discover.rating")}</span>
            <select className="select" value={v.rating} onChange={(e) => set({ rating: e.target.value })}>
              <option value="">{t("discover.any")}</option>
              {["4.5", "4", "3.5"].map((r) => <option key={r} value={r}>{t("discover.rating_min", { n: r })}</option>)}
            </select></label>
          <label className="check" style={{ alignSelf: "end", paddingBottom: 12 }}>
            <input type="checkbox" checked={v.verified} onChange={(e) => set({ verified: e.target.checked })} /><span className="small">{t("discover.verified_only")}</span>
          </label>
          <div className="row" style={{ gridColumn: "1 / -1" }}>
            <button className="btn btn-secondary btn-sm" type="button" onClick={() => { apply(); setShowFilters(false); }}>{t("discover.apply")}</button>
            {activeFilters > 0 && <button className="link small" type="button" onClick={() => { apply({ min: "", max: "", lang: "", verified: false, rating: "" }); setShowFilters(false); }}>{t("discover.clear_filters")}</button>}
          </div>
        </div>
      )}

      {v.near && nearName && !need && <p className="tiny muted">{t("near.honest", { city: nearName })}</p>}

      <div className="between">
        <h2>{need ? t("discover.for_need") : areaName ?? t("discover.people")}</h2>
        {results && <span className="small muted">{t("discover.count", { n: results.length })}</span>}
      </div>
      {v.sort === "rating" && !need && <p className="tiny muted" style={{ marginTop: -8 }}>{t("sort.rating_note")}</p>}

      {loading ? <Skeleton h={170} n={4} /> : results && results.length ? (
        <div className="grid grid-2">{results.map((c) => <ProviderCard key={c.id} c={c} />)}</div>
      ) : (
        <Empty title={t("discover.empty_title")} body={t("discover.empty_body")} action={<button className="btn btn-secondary" onClick={() => { set({ q: "", area: "" }); router.push(v.near ? `/discover?near=${v.near}` : "/discover"); }}>{t("discover.clear")}</button>} />
      )}
    </div>
  );
}

export default function DiscoverPage() {
  return <Suspense fallback={<div className="wrap page"><Skeleton h={170} n={4} /></div>}><Discover /></Suspense>;
}
