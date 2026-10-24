"use client";

/**
 * Members dashboard (/insights), open to every signed-in member (owner,
 * 2026-09-27: "let everyone know"). Reached from the hub.
 *
 * Reading order follows what the owner asked for: how many members, where they
 * live (India map, world map, ranked places), who they are (women and men, age,
 * candidate details), then accounts. Every figure is a total from
 * GET /v1/insights; no person is ever listed.
 */
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, identity, INTL_LOCALE, type Insights as Data, type Lang } from "@/lib/api";
import { langFromNavigator } from "@/lib/i18n";
import { insightsTranslator, valueLabel, type InsightsKey, type InsightsT } from "@/lib/insights-i18n";
import { AgePyramid, GrowthChart, MeterList, ShareBar, type MeterItem, type Segment } from "./charts";
import MemberMap, { step } from "./MemberMap";

type Phase =
  | { kind: "loading" }
  | { kind: "signedOut" }
  | { kind: "error" }
  | { kind: "ready"; data: Data };

type Range = "30" | "90" | "all";

const LOCALES: Record<Lang, string> = INTL_LOCALE;

function entries(record: Record<string, number>, t: InsightsT): MeterItem[] {
  return Object.entries(record)
    .sort((a, b) => (a[0] === "unknown" ? 1 : b[0] === "unknown" ? -1 : b[1] - a[1]))
    .map(([key, value]) => ({ key, label: valueLabel(t, key), value }));
}

export default function Insights() {
  const [lang, setLang] = useState<Lang>("en");
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const t = useMemo(() => insightsTranslator(lang), [lang]);
  const locale = LOCALES[lang];

  const load = useCallback(async () => {
    try {
      setPhase({ kind: "ready", data: await identity.insights() });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) setPhase({ kind: "signedOut" });
      else setPhase({ kind: "error" });
    }
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const session = await identity.session();
        const next = session?.member.preferred_language ?? langFromNavigator();
        setLang(next);
        document.documentElement.lang = next;
        if (!session) return setPhase({ kind: "signedOut" });
      } catch {
        return setPhase({ kind: "error" });
      }
      await load();
    })();
  }, [load]);

  async function refresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  return (
    <div className="insights">
      <header className="ins-header">
        <nav className="ins-crumbs" aria-label={t("pageTitle")}>
          <Link href="/" className="ins-brand" aria-label={t("backToHub")}>
            For<strong>Khatri</strong>
          </Link>
          <span className="ins-crumb-sep" aria-hidden>
            /
          </span>
          <span className="ins-crumb is-current" aria-current="page">
            {t("pageTitle")}
          </span>
        </nav>
        {phase.kind === "ready" && (
          <div className="ins-updated">
            <span className="ins-updated-text">
              {t("updated", {
                time: new Intl.DateTimeFormat(locale, { hour: "numeric", minute: "2-digit", day: "numeric", month: "short" }).format(
                  new Date(phase.data.generated_at),
                ),
              })}
            </span>
            <button
              type="button"
              className="ins-icon-button"
              onClick={() => void refresh()}
              disabled={refreshing}
              aria-label={refreshing ? t("refreshing") : t("refresh")}
              title={t("refresh")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={refreshing ? "is-spinning" : undefined} aria-hidden>
                <path d="M21 12a9 9 0 1 1-2.64-6.36" />
                <path d="M21 3v6h-6" />
              </svg>
            </button>
          </div>
        )}
      </header>

      <main className="ins-main" id="main">
        <div className="ins-intro">
          <h1 className="ins-title">{t("pageTitle")}</h1>
          <p className="ins-lede">{t("pageSub")}</p>
        </div>

        {phase.kind === "loading" && <Skeleton label={t("loading")} />}
        {phase.kind === "signedOut" && (
          <section className="ins-empty">
            <h2>{t("signedOutTitle")}</h2>
            <Link className="ins-button ins-button-primary" href="/">
              {t("signIn")}
            </Link>
          </section>
        )}
        {phase.kind === "error" && (
          <section className="ins-empty">
            <p>{t("loadFailed")}</p>
            <button type="button" className="ins-button ins-button-primary" onClick={() => void refresh()}>
              {t("retry")}
            </button>
          </section>
        )}
        {phase.kind === "ready" && <Dashboard data={phase.data} t={t} lang={lang} locale={locale} />}
      </main>
    </div>
  );
}

function Skeleton({ label }: { label: string }) {
  return (
    <div className="ins-skeleton" aria-busy="true" aria-live="polite">
      <span className="sr-only">{label}</span>
      <div className="ins-sk ins-sk-kpis" />
      <div className="ins-sk ins-sk-chart" />
      <div className="ins-sk ins-sk-map" />
    </div>
  );
}

function Dashboard({ data, t, lang, locale }: { data: Data; t: InsightsT; lang: Lang; locale: string }) {
  const [mapKind, setMapKind] = useState<"india" | "world">("india");
  const [placeList, setPlaceList] = useState<"cities" | "states">("cities");
  const [range, setRange] = useState<Range>("all");
  const n = (v: number) => v.toLocaleString(locale);
  const pct = new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 });
  const countryName = useMemo(() => {
    const names = new Intl.DisplayNames([locale], { type: "region" });
    return (cc: string) => {
      try {
        return names.of(cc) ?? cc;
      } catch {
        return cc;
      }
    };
  }, [locale]);
  const members = (v: number) => (v === 1 ? t("tipMember") : t("tipMembers", { n: n(v) }));
  const { totals, location } = data;

  const stateValues = useMemo(() => new Map(location.india_states.map((s) => [s.state, s.members])), [location]);
  const countryValues = useMemo(() => new Map(location.countries.map((c) => [c.cc, c.members])), [location]);

  const growth = range === "all" ? data.growth : data.growth.slice(-Number(range));
  const periodNew = growth.reduce((sum, p) => sum + p.new, 0);

  const cityMarks = location.cities
    .filter((c) => mapKind === "world" || c.cc === "IN")
    .map((c) => ({
      key: `${c.name}-${c.region}-${c.cc}`,
      lat: c.lat,
      lon: c.lon,
      members: c.members,
      tip: (
        <>
          <strong>
            {c.name}
            {c.region ? `, ${c.region}` : ""}
            {c.cc !== "IN" ? `, ${countryName(c.cc)}` : ""}
          </strong>
          <span>{members(c.members)}</span>
          {(c.by_gender.female || c.by_gender.male) && (
            <span className="ins-tip-muted">{t("tipCity", { women: n(c.by_gender.female ?? 0), men: n(c.by_gender.male ?? 0) })}</span>
          )}
        </>
      ),
    }));

  const women = data.gender.counts.female ?? 0;
  const men = data.gender.counts.male ?? 0;
  const otherGender = Object.entries(data.gender.counts)
    .filter(([k]) => k !== "female" && k !== "male")
    .reduce((sum, [, v]) => sum + v, 0);
  const known = women + men + otherGender;

  const bands = data.age.bands
    .filter((b, i, all) => Object.keys(b.by_gender).length > 0 || all.slice(i).some((x) => Object.keys(x.by_gender).length > 0))
    .map((b) => ({ band: b.band, left: b.by_gender.female ?? 0, right: b.by_gender.male ?? 0 }))
    .reverse();
  const age = (v: number | null | undefined) => (v === null || v === undefined ? "—" : n(v));

  const languageName = new Intl.DisplayNames([LOCALES[lang]], { type: "language" });
  const languageSegments: Segment[] = Object.entries(data.languages)
    .sort((a, b) => b[1] - a[1])
    .map(([code, value], i) => ({ key: code, label: languageName.of(code) ?? code, value, className: `ins-s-${i + 1}` }));
  const signInSegments: Segment[] = (["phone", "email", "both"] as const)
    .filter((k) => data.sign_in[k])
    .map((k, i) => ({ key: k, label: t(k), value: data.sign_in[k], className: `ins-s-${i + 1}` }));

  const ranges: { key: Range; label: InsightsKey }[] = [
    { key: "30", label: "range30" },
    { key: "90", label: "range90" },
    { key: "all", label: "rangeAll" },
  ];

  return (
    <>
      {/* Headline numbers: one strip, hairline dividers */}
      <section className="ins-kpis" aria-label={t("pageTitle")}>
        <div className="ins-kpi">
          <span className="ins-kpi-label">{t("kpiTotal")}</span>
          <span className="ins-kpi-value is-hero">{n(totals.members)}</span>
          <span className="ins-kpi-note">{t("kpiWaiting", { joined: n(totals.joined), pending: n(totals.not_yet_joined) })}</span>
        </div>
        <div className="ins-kpi">
          <span className="ins-kpi-label">{t("kpiNew30")}</span>
          <span className="ins-kpi-value">{n(totals.new_30d)}</span>
          <span className={`ins-kpi-note${totals.new_7d ? " is-up" : ""}`}>{t("kpiNewDelta", { n: n(totals.new_7d) })}</span>
        </div>
        <div className="ins-kpi">
          <span className="ins-kpi-label">{t("kpiActive30")}</span>
          <span className="ins-kpi-value">{n(totals.active_30d)}</span>
          <span className="ins-kpi-note">
            {t("kpiActive7", { n: n(totals.active_7d) })}
            {totals.suspended > 0 && ` · ${t("kpiSuspended", { n: n(totals.suspended) })}`}
          </span>
        </div>
        <div className="ins-kpi">
          <span className="ins-kpi-label">{t("kpiLocated")}</span>
          <span className="ins-kpi-value">{n(location.located)}</span>
          <span className="ins-kpi-note">{t("kpiLocatedNote", { pct: totals.members ? pct.format(location.located / totals.members) : "—" })}</span>
          <span className="ins-kpi-meter" aria-hidden>
            <span style={{ width: `${totals.members ? (location.located / totals.members) * 100 : 0}%` }} />
          </span>
        </div>
      </section>

      {/* Growth */}
      <section className="ins-card">
        <div className="ins-card-head">
          <div>
            <h2 className="ins-h2">{t("growthTitle")}</h2>
            <p className="ins-sub">
              {t("growthBy")} · <span className={periodNew ? "ins-up" : undefined}>{t("growthPeriod", { n: n(periodNew) })}</span>
            </p>
          </div>
          <div className="ins-segmented" role="tablist" aria-label={t("growthTitle")}>
            {ranges.map((r) => (
              <button key={r.key} type="button" role="tab" aria-selected={range === r.key} onClick={() => setRange(r.key)}>
                {t(r.label)}
              </button>
            ))}
          </div>
        </div>
        <GrowthChart
          points={growth}
          locale={locale}
          labelTotal={(v) => t("growthTotal", { n: n(v) })}
          labelNew={(v) => t("growthNew", { n: n(v) })}
        />
      </section>

      {/* Where members live */}
      <section className="ins-card ins-where">
        <div className="ins-card-head">
          <div>
            <h2 className="ins-h2">{t("mapsTitle")}</h2>
            <p className="ins-sub">{t("mapsSub")}</p>
          </div>
          <div className="ins-segmented" role="tablist" aria-label={t("mapsTitle")}>
            {(["india", "world"] as const).map((kind) => (
              <button key={kind} type="button" role="tab" aria-selected={mapKind === kind} onClick={() => setMapKind(kind)}>
                {t(kind === "india" ? "indiaMap" : "worldMap")}
              </button>
            ))}
          </div>
        </div>
        <div className="ins-where-grid">
          <div className="ins-map-col">
            <MemberMap
              key={mapKind}
              kind={mapKind}
              locale={locale}
              values={mapKind === "india" ? stateValues : countryValues}
              cities={cityMarks}
              ariaLabel={t(mapKind === "india" ? "mapIndiaAria" : "mapWorldAria")}
              regionName={(key, fallback) => countryName(key) || fallback}
              regionTip={(key, name, value) => {
                const country = mapKind === "world" ? location.countries.find((c) => c.cc === key) : undefined;
                return (
                  <>
                    <strong>{mapKind === "world" ? countryName(key) || name : name}</strong>
                    <span>{value ? members(value) : t("legendNone")}</span>
                    {country && <span className="ins-tip-muted">{t("countryFromCity", { city: n(country.from_city), phone: n(country.from_phone) })}</span>}
                  </>
                );
              }}
            />
            <MapLegend t={t} values={mapKind === "india" ? stateValues : countryValues} kind={mapKind} />
          </div>

          <div className="ins-where-side">
            {mapKind === "india" ? (
              <>
                <div className="ins-side-head">
                  <div className="ins-segmented is-small" role="tablist" aria-label={t("placesTitle")}>
                    {(["cities", "states"] as const).map((k) => (
                      <button key={k} type="button" role="tab" aria-selected={placeList === k} onClick={() => setPlaceList(k)}>
                        {t(k === "cities" ? "rankCities" : "rankStates")}
                      </button>
                    ))}
                  </div>
                </div>
                {location.cities.length === 0 ? (
                  <p className="ins-note">{t("noPlaces")}</p>
                ) : placeList === "cities" ? (
                  <>
                    <MeterList
                      ranked
                      locale={locale}
                      total={location.located}
                      items={location.cities.slice(0, 10).map((c) => ({
                        key: `${c.name}-${c.region}-${c.cc}`,
                        label: c.name,
                        sub:
                          (c.cc === "IN" ? c.region : countryName(c.cc)) +
                          (c.by_gender.female || c.by_gender.male
                            ? ` · ${t("cityGenderShort", { women: n(c.by_gender.female ?? 0), men: n(c.by_gender.male ?? 0) })}`
                            : ""),
                        value: c.members,
                      }))}
                    />
                    <p className="ins-note">{t("citiesGenderNote")}</p>
                  </>
                ) : (
                  <MeterList
                    ranked
                    locale={locale}
                    total={location.india_states.reduce((sum, s) => sum + s.members, 0)}
                    items={location.india_states.map((s) => ({ key: s.state, label: s.state, value: s.members }))}
                  />
                )}
              </>
            ) : (
              <>
                <h3 className="ins-h3">{t("countriesTitle")}</h3>
                <MeterList
                  ranked
                  locale={locale}
                  total={totals.members}
                  items={location.countries.map((c) => ({
                    key: c.cc,
                    label: countryName(c.cc),
                    sub: t("countryFromCity", { city: n(c.from_city), phone: n(c.from_phone) }),
                    value: c.members,
                  }))}
                />
                {location.country_unknown > 0 && <p className="ins-note">{t("countryUnknown", { n: n(location.country_unknown) })}</p>}
              </>
            )}
            {location.unresolved.length > 0 && (
              <>
                <h3 className="ins-h3">{t("unresolvedTitle")}</h3>
                <p className="ins-note">{location.unresolved.map((u) => `${u.text} (${n(u.members)})`).join(" · ")}</p>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Who they are */}
      <section className="ins-card">
        <h2 className="ins-h2">{t("whoTitle")}</h2>
        <p className="ins-sub">{t("whoSub", { known: n(data.gender.candidates), total: n(totals.members) })}</p>
        <div className="ins-who">
          <div className="ins-who-gender">
            <h3 className="ins-h3">{t("genderTitle")}</h3>
            <div className="ins-gender-stats">
              <div>
                <span className="ins-gender-label">
                  <span className="ins-swatch ins-s-women" aria-hidden /> {t("female")}
                </span>
                <span className="ins-gender-value">{n(women)}</span>
                <span className="ins-kpi-note">{t("shareOfKnown", { pct: known ? pct.format(women / known) : "—" })}</span>
              </div>
              <div>
                <span className="ins-gender-label">
                  <span className="ins-swatch ins-s-men" aria-hidden /> {t("male")}
                </span>
                <span className="ins-gender-value">{n(men)}</span>
                <span className="ins-kpi-note">{t("shareOfKnown", { pct: known ? pct.format(men / known) : "—" })}</span>
              </div>
              {otherGender > 0 && (
                <div>
                  <span className="ins-gender-label">
                    <span className="ins-swatch ins-s-other" aria-hidden /> {t("other")}
                  </span>
                  <span className="ins-gender-value">{n(otherGender)}</span>
                </div>
              )}
            </div>
            <div className="ins-split" role="img" aria-label={`${t("female")} ${women}, ${t("male")} ${men}`}>
              {women > 0 && <span className="ins-s-women" style={{ flexGrow: women }} />}
              {men > 0 && <span className="ins-s-men" style={{ flexGrow: men }} />}
              {otherGender > 0 && <span className="ins-s-other" style={{ flexGrow: otherGender }} />}
            </div>
          </div>

          <div className="ins-who-age">
            <h3 className="ins-h3">{t("ageTitle")}</h3>
            <AgePyramid
              bands={bands}
              left={{ label: t("female"), className: "ins-s-women" }}
              right={{ label: t("male"), className: "ins-s-men" }}
              locale={locale}
              bandLabel={(band) => t("ageBand", { band })}
            />
            <dl className="ins-age-facts">
              <div>
                <dt>{t("ageMedianLabel")}</dt>
                <dd>{age(data.age.median)}</dd>
              </div>
              <div>
                <dt>{t("female")}</dt>
                <dd>{age(data.age.median_by_gender.female)}</dd>
              </div>
              <div>
                <dt>{t("male")}</dt>
                <dd>{age(data.age.median_by_gender.male)}</dd>
              </div>
              <div>
                <dt>{t("ageRangeLabel")}</dt>
                <dd>
                  {age(data.age.youngest)}–{age(data.age.oldest)}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="ins-three ins-divided">
          <div>
            <h3 className="ins-h3">{t("lookingFor")}</h3>
            <MeterList items={entries(data.candidates.looking_for, t)} locale={locale} />
          </div>
          <div>
            <h3 className="ins-h3">{t("maritalStatus")}</h3>
            <MeterList items={entries(data.candidates.marital_status, t)} locale={locale} />
          </div>
          <div>
            <h3 className="ins-h3">{t("motherTongue")}</h3>
            <MeterList items={entries(data.candidates.mother_tongue, t)} locale={locale} />
          </div>
        </div>
      </section>

      {/* Accounts */}
      <section className="ins-card">
        <h2 className="ins-h2">{t("accountsTitle")}</h2>
        <div className="ins-three">
          <div>
            <h3 className="ins-h3">{t("modulesTitle")}</h3>
            <MeterList
              locale={locale}
              total={totals.members}
              items={data.modules.map((m) => ({ key: m.key, label: m.name, value: m.members }))}
            />
            <p className="ins-note">{t("modulesSub")}</p>
          </div>
          <div>
            <h3 className="ins-h3">{t("signInTitle")}</h3>
            <ShareBar segments={signInSegments} locale={locale} />
          </div>
          <div>
            <h3 className="ins-h3">{t("languageTitle")}</h3>
            <ShareBar segments={languageSegments} locale={locale} />
          </div>
        </div>
      </section>

      <footer className="ins-footer">
        <ul className="ins-sources" aria-label={t("sourcesTitle")}>
          {data.sources.map((s) => {
            const source = t(`source_${s.module}` as InsightsKey);
            return (
              <li key={s.module} className={s.ok ? "is-ok" : "is-down"}>
                <span className="ins-source-dot" aria-hidden /> {t(s.ok ? "sourceOk" : "sourceDown", { source })}
              </li>
            );
          })}
        </ul>
        <p className="ins-attribution">{t("attribution")}</p>
      </footer>
    </>
  );
}

function MapLegend({ t, values, kind }: { t: InsightsT; values: Map<string, number>; kind: "india" | "world" }) {
  // The world view is a flat backdrop with one marker per country, so its
  // legend is just that marker; the shading ramp belongs to the India view.
  if (kind === "world") {
    return (
      <div className="ins-map-legend">
        <span className="ins-legend-item">
          <span className="ins-city-key" aria-hidden /> {t("legendCountry")}
        </span>
      </div>
    );
  }
  const max = Math.max(1, ...values.values());
  const used = new Set([...values.values()].map((v) => step(v, max)));
  return (
    <div className="ins-map-legend">
      <span className="ins-legend-item">
        <span className="ins-swatch ins-q0" aria-hidden /> {t("legendNone")}
      </span>
      <span className="ins-legend-item">
        {t("legendFewer")}
        <span className="ins-ramp" aria-hidden>
          {[1, 2, 3, 4, 5].map((q) => (
            <span key={q} className={`ins-q${q}${used.has(q) ? "" : " is-unused"}`} />
          ))}
        </span>
        {t("legendMore")}
      </span>
      <span className="ins-legend-item">
        <span className="ins-city-key" aria-hidden /> {t("legendCity")}
      </span>
    </div>
  );
}
