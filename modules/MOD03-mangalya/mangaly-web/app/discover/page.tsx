"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import MotionTitle from "@/components/MotionTitle";
import ScrollRail from "@/components/ScrollRail";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import ContextChip from "@/components/ContextChip";
import DiscoverFiltersSheet from "@/components/DiscoverFilters";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import MatchmakerEntry from "@/components/MatchmakerEntry";
import Vignette from "@/components/Vignette";
import {
  readBrowseLookingFor,
  useActiveContext,
  writeBrowseLookingFor,
} from "@/lib/activeContext";
import type { LookingFor } from "@/lib/auth";
import { resolveMediaUrl } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { listSent } from "@/lib/connections";
import {
  countActiveFilters,
  getShelves,
  search,
  type Shelf,
  type DiscoverFilters,
  type SearchResult,
} from "@/lib/discovery";
import { listShortlist, save, unsave } from "@/lib/shortlist";

import "./discover-hero.css";
import "./discover-wall.css";

/* Discover — the owner's brief (2026-09-21/22): "I want to just scroll and see
 * all the pictures… then select one picture", for a parent and a candidate
 * alike; "mature, well crafted, well established UI/UX, smooth"; and "few
 * people like to share few things openly — let them have that."
 *
 * So:
 *   * A photo wall, not a list of forms. Two columns on a phone, up to five on
 *     a wide screen. Each tile is the main photo and three short lines; the
 *     profile opens on a tap. Nothing else competes with the faces.
 *   * The tabs established matrimony apps use, filtered through Mangalya's own
 *     rules. Shaadi.com's Matches has Today's / My / New Matches, Near Me,
 *     Recently Viewed and Recent Visitors; Jeevansathi has Daily
 *     Recommendations and Just Joined. Mangalya keeps For you, New, Near you
 *     and Saved — and drops visitor lists, because the baseline rules out
 *     view counts and being watched.
 *   * What someone chose to show openly shows: their first name, a published
 *     prompt as a one-line quote, and a photo count when they opened all
 *     their photos. Everyone else's tile stays the privacy-first card.
 *   * Smooth: skeleton tiles instead of a spinner, more people load before
 *     the end of the page, and coming back from a profile returns to the
 *     same tab, the same results and the same scroll position. */

/* For you: themed rows (DEC-V1-022). All matches: the full searchable wall,
   where "See all" on any row lands with that row's filter applied. Saved. */
type Tab = "forYou" | "all" | "saved";

type Feed = {
  results: SearchResult[];
  total: number | null;
  page: number;
  hasMore: boolean;
  lookingForMissing: boolean;
  horoscopeChartMissing?: boolean;
};

/* Kept across client navigations so "back" from a profile lands exactly where
   the reader left: same results, same scroll. */
let lastView: { key: string; feed: Feed; scrollY: number } | null = null;

function tabFilters(_tab: Tab, filters: DiscoverFilters): DiscoverFilters {
  return filters;
}

export default function DiscoverPage() {
  const { t } = useTranslation(["common", "discover", "profile"]);
  const { contexts, active, choose, loaded } = useActiveContext();
  const family = active?.kind === "family" ? active.circle : null;
  const forCandidate = family?.candidate_account_id;
  const familyName = family ? family.candidate_name.split(" ")[0] : "";
  /* Browse mode: an account with no profile of its own and no circle (a
     parent who has not joined yet, a new member) still searches, for a bride
     or a groom they pick here. Until they pick, nothing is asked of the
     server, which would only answer "looking for missing" (409). */
  /* Browse mode: an account with no profile and no circle says what it is
     looking for; the choice is kept on this device. (The shell does not
     mount lib/session's provider, so this is local state.) */
  // Read lazily on the client; it only affects output once `loaded` is
  // true, which never happens during server rendering.
  const [browse, setBrowseState] = useState<LookingFor | null>(() =>
    typeof window === "undefined" ? null : readBrowseLookingFor(),
  );
  const setBrowse = (value: LookingFor) => {
    writeBrowseLookingFor(value);
    setBrowseState(value);
  };
  const browseMode = loaded && !family && !contexts?.own_profile;
  const browseFor = browseMode ? browse : null;
  const needsChoice = browseMode && !browse;

  const [tab, setTab] = useState<Tab>("forYou");
  const [filters, setFilters] = useState<DiscoverFilters>({});
  const [q, setQ] = useState("");
  const [feed, setFeed] = useState<Feed | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<Record<string, string>>({});
  const [broken, setBroken] = useState<Set<string>>(new Set());
  const sentinel = useRef<HTMLDivElement | null>(null);
  const [shelves, setShelves] = useState<Shelf[] | null>(null);
  const [shelvesMissing, setShelvesMissing] = useState(false);
  /* [DEC-V1-030] "For you" is one photo wall, not stacked rows: each row's
     theme became a lens chip over the same wall. "everyone" shows them all. */
  const [lens, setLens] = useState<string>("everyone");
  const wall = useMemo(() => {
    const seen = new Set<string>();
    const items: { r: SearchResult; reason: string | null; key: Shelf["key"] }[] = [];
    for (const sh of shelves ?? []) {
      for (const r of sh.results) {
        if (seen.has(r.candidate_account_id)) continue;
        seen.add(r.candidate_account_id);
        items.push({ r, reason: r.reason ?? null, key: sh.key });
      }
    }
    return items;
  }, [shelves]);
  const lenses = useMemo(
    () =>
      (shelves ?? [])
        .map((sh) => ({
          key: sh.key,
          count: wall.filter((w) => w.key === sh.key).length,
        }))
        .filter((l) => l.count > 0),
    [shelves, wall],
  );

  // The rows, fetched when "For you" is showing.
  useEffect(() => {
    if (!loaded || needsChoice) return;
    let alive = true;
    void getShelves({ forCandidate, lookingFor: browseFor }).then((r) => {
      if (!alive) return;
      setShelves(r.shelves);
      setShelvesMissing(r.lookingForMissing);
    });
    return () => {
      alive = false;
    };
  }, [loaded, forCandidate, needsChoice, browseFor]);

  /* "See all" on a row: the full wall with that row's filter applied. */
  function seeAll(sh: Shelf) {
    setFilters(sh.see_all ?? {});
    setTab("all");
    window.scrollTo({ top: 0 });
  }

  const viewKey = useMemo(
    () =>
      JSON.stringify([forCandidate ?? browseFor ?? "self", tab, filters, q.trim()]),
    [forCandidate, browseFor, tab, filters, q],
  );

  const load = useCallback(
    async (page: number): Promise<Feed> => {
      if (tab === "forYou") {
        return {
          results: [],
          total: null,
          page: 1,
          hasMore: false,
          lookingForMissing: false,
        };
      }
      if (tab === "saved") {
        const list = await listShortlist(forCandidate);
        return {
          results: list,
          total: list.length,
          page: 1,
          hasMore: false,
          lookingForMissing: false,
        };
      }
      if (needsChoice) {
        return {
          results: [],
          total: 0,
          page: 1,
          hasMore: false,
          lookingForMissing: true,
        };
      }
      const found = await search(
        { ...tabFilters(tab, filters), q: q.trim() || undefined },
        { forCandidate, lookingFor: browseFor, page },
      );
      return {
        results: found.results,
        total: found.total,
        page,
        hasMore: found.hasMore,
        lookingForMissing: found.lookingForMissing,
        horoscopeChartMissing: found.horoscopeChartMissing,
      };
    },
    [tab, filters, q, forCandidate, needsChoice, browseFor],
  );

  // First page for the current tab / filters / search. A matching cached view
  // shows instantly and restores the scroll; the fresh page replaces it.
  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    const cached = lastView?.key === viewKey ? lastView : null;
    (async () => {
      const session = await requireSession();
      if (!alive || !session) return;
      if (cached) {
        setFeed(cached.feed);
        requestAnimationFrame(() => window.scrollTo(0, cached.scrollY));
      } else {
        setFeed(null);
      }
      const [first, sent, shortlist] = await Promise.all([
        cached ? Promise.resolve(cached.feed) : load(1),
        listSent(forCandidate).catch(() => []),
        listShortlist(forCandidate).catch(() => []),
      ]);
      if (!alive) return;
      setFeed(first);
      setStatus(
        Object.fromEntries(sent.map((c) => [c.target_account_id, c.status])),
      );
      setSaved(new Set(shortlist.map((s) => s.candidate_account_id)));
    })();
    return () => {
      alive = false;
    };
  }, [loaded, viewKey, load, forCandidate]);

  // Remember where the reader is, for the way back from a profile.
  useEffect(() => {
    if (!feed) return;
    const remember = () => {
      lastView = { key: viewKey, feed, scrollY: window.scrollY };
    };
    remember();
    window.addEventListener("scroll", remember, { passive: true });
    return () => window.removeEventListener("scroll", remember);
  }, [feed, viewKey]);

  const loadMore = useCallback(async () => {
    if (!feed || loadingMore || !feed.hasMore) return;
    setLoadingMore(true);
    const next = await load(feed.page + 1);
    setFeed((prev) => {
      if (!prev) return next;
      const seen = new Set(prev.results.map((r) => r.candidate_account_id));
      return {
        ...next,
        results: [
          ...prev.results,
          ...next.results.filter((r) => !seen.has(r.candidate_account_id)),
        ],
      };
    });
    setLoadingMore(false);
  }, [feed, loadingMore, load]);

  // More people arrive well before the end of the wall.
  useEffect(() => {
    const target = sentinel.current;
    if (!target) return;
    const observer = new IntersectionObserver(
      (entries) => entries.some((e) => e.isIntersecting) && void loadMore(),
      { rootMargin: "900px" },
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [loadMore]);

  // Search as you type, gently debounced.
  const [typed, setTyped] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setQ(typed), 450);
    return () => window.clearTimeout(timer);
  }, [typed]);

  async function toggleSave(id: string) {
    const on = saved.has(id);
    setSaved((s) => {
      const next = new Set(s);
      if (on) next.delete(id);
      else next.add(id);
      return next;
    });
    const outcome = on
      ? await unsave(id, forCandidate)
      : await save(id, forCandidate);
    if (!outcome.ok) {
      // Put it back as it was: the save did not happen.
      setSaved((s) => {
        const next = new Set(s);
        if (on) next.add(id);
        else next.delete(id);
        return next;
      });
    } else if (tab === "saved" && on) {
      setFeed(
        (f) =>
          f && {
            ...f,
            results: f.results.filter((r) => r.candidate_account_id !== id),
          },
      );
    }
  }

  /* The filters currently narrowing the wall, each removable in one tap. */
  const activeChips: {
    key: string;
    label: string;
    clear: () => DiscoverFilters;
  }[] = [];
  const opt = (k: string, v: string) => t(`profile:option.${k}.${v}`);
  if (filters.ageMin || filters.ageMax)
    activeChips.push({
      key: "age",
      label: t("discover:chips.age", {
        min: filters.ageMin ?? "…",
        max: filters.ageMax ?? "…",
      }),
      clear: () => ({ ...filters, ageMin: undefined, ageMax: undefined }),
    });
  if (filters.heightMin || filters.heightMax)
    activeChips.push({
      key: "height",
      label: t("discover:chips.height", {
        min: filters.heightMin ?? "…",
        max: filters.heightMax ?? "…",
      }),
      clear: () => ({ ...filters, heightMin: undefined, heightMax: undefined }),
    });
  if (filters.nearby)
    activeChips.push({
      key: "nearby",
      label: t(
        filters.nearby === "city"
          ? "discover:filters.nearbyCity"
          : "discover:filters.nearbyState",
      ),
      clear: () => ({ ...filters, nearby: undefined }),
    });
  if (filters.city)
    activeChips.push({
      key: "city",
      label: filters.city,
      clear: () => ({ ...filters, city: undefined }),
    });
  if (filters.openToRelocate)
    activeChips.push({
      key: "reloc",
      label: t("discover:filters.openToRelocate"),
      clear: () => ({ ...filters, openToRelocate: undefined }),
    });
  if (filters.manglik)
    activeChips.push({
      key: "manglik",
      label: `${t("profile:field.horoscope.manglik")}: ${opt("manglik", filters.manglik)}`,
      clear: () => ({ ...filters, manglik: undefined }),
    });
  (
    [
      ["maritalStatus", "marital_status"],
      ["education", "highest_education_level"],
      ["diet", "diet"],
      ["motherTongue", "mother_tongue"],
      ["subCommunity", "sub_community"],
      ["incomeBand", "income_band"],
    ] as const
  ).forEach(([key, optKey]) =>
    (filters[key] ?? []).forEach((v) =>
      activeChips.push({
        key: `${key}.${v}`,
        label: opt(optKey, v),
        clear: () => {
          const rest = (filters[key] ?? []).filter((x) => x !== v);
          return { ...filters, [key]: rest.length ? rest : undefined };
        },
      }),
    ),
  );

  /* A render function, not a component declared in here: a nested component
     is a new type on every render, which would remount every tile (and
     re-flash every photo) each time anything on the page changed. */
  function renderTile(r: SearchResult, reason?: string | null, featured = false) {
    const id = r.candidate_account_id;
    const photo = !broken.has(id) ? resolveMediaUrl(r.photo_url ?? null) : null;
    const city = r.locality?.split(",")[0]?.trim() || null;
    /* [DEC-V1-030] The words sit on the photo, like the Home portraits:
       first name and age large, then city and work. Someone who has not
       shown their name openly is introduced by age. */
    const firstName = r.open_name?.trim().split(/\s+/)[0] ?? null;
    const place = city;
    const work = r.profession ?? null;
    const photos = r.open_photo_urls?.length ?? 0;
    const state = status[id];
    return (
      <article key={id} className={`dtile${featured ? " dtile--featured" : ""}`}>
        <Link href={`/profile/${id}`} className="dtile__link" prefetch={false}>
          <div className="dtile__photo">
            {photo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={photo}
                alt=""
                loading="lazy"
                decoding="async"
                onError={() => setBroken((b) => new Set(b).add(id))}
              />
            ) : (
              <span className="dtile__nophoto" aria-hidden="true">
                <Vignette id="photos" />
              </span>
            )}
            {photos > 1 && (
              <span className="dtile__count">
                {t("discover:tile.photos", { count: photos })}
              </span>
            )}
            {state && state !== "withdrawn" && (
              <span className={`dtile__state dtile__state--${state}`}>
                {t(`discover:tile.state.${state}`)}
              </span>
            )}
            <div className="dtile__text">
              {/* [DEC-V1-031] The engine's word for the pair, never its number. */}
              {(r.match_label || reason) && (
                <span className="dtile__why">
                  {r.match_label && (
                    <span className="dtile__match">{t(`discover:match.${r.match_label}`)}</span>
                  )}
                  {r.match_label && reason ? " · " : null}
                  {reason}
                </span>
              )}
              <span className="dtile__title">
                {firstName ?? (r.age ? t("profile:hub.ageYears", { age: r.age }) : "")}
                {firstName && r.age ? <span className="dtile__age"> {r.age}</span> : null}
                {(r.verification?.length ?? 0) > 0 && (
                  <Icon name="verified" size={16} className="seal" label={t("discover:verified.title")} />
                )}
              </span>
              {(place || work) && (
                <span className="dtile__line">
                  {place && <span className="dtile__place">{place}</span>}
                  {place && work ? " · " : null}
                  {work}
                </span>
              )}
              {featured && r.open_prompt?.a && (
                <span className="dtile__quote">“{r.open_prompt.a}”</span>
              )}
            </div>
          </div>
        </Link>
        <button
          type="button"
          className={`dtile__save${saved.has(id) ? " is-on" : ""}`}
          aria-pressed={saved.has(id)}
          aria-label={t(
            saved.has(id) ? "discover:tile.unsave" : "discover:tile.save",
          )}
          onClick={() => void toggleSave(id)}
        >
          <Icon name="bookmark" filled={saved.has(id)} />
        </button>
      </article>
    );
  }

  const filterCount = countActiveFilters(filters);
  const lookingFor = family
    ? family.looking_for
    : (contexts?.own_profile?.looking_for ?? browseFor);

  /* The Bride / Groom choice, in place, for browse mode. */
  const browseChoice = browseMode ? (
    <div className="dempty__choice" role="group" aria-label={t("discover:lookingFor.title")}>
      {(["bride", "groom"] as const).map((v) => (
        <button
          key={v}
          type="button"
          className={`btn ${browse === v ? "btn--primary" : "btn--ghost"}`}
          aria-pressed={browse === v}
          onClick={() => setBrowse(v)}
        >
          {t(`profile:option.looking_for.${v}`)}
        </button>
      ))}
    </div>
  ) : null;

  return (
    <>
      <header className="topbar dhead">
        {/* Whose search this is sits above the title as a quiet eyebrow —
            a parent sees the candidate's name — instead of taking its own
            line between the title and the photos. */}
        <div className="dhead__text">
          {/* A parent's header already carries the candidate chip, so the
              eyebrow is only for one's own search: what it looks for. */}
          {!family && lookingFor && (
            <p className="dhead__for">
              {t("discover:lookingForLine", {
                value: t(`profile:option.looking_for.${lookingFor}`),
              })}
              {/* [D1, 2026-10-06] Looking around first: the way back to
                  making a profile stays one tap away, never pushed. */}
              {browseMode && (
                <>
                  {" · "}
                  <Link className="link" href="/profile/create?start=1">
                    {t("discover:lookAround.makeProfile")}
                  </Link>
                </>
              )}
            </p>
          )}
          <MotionTitle as="h1" className="royal-title" text={t("discover:title")} />
        </div>
        <div className="topbar__actions">
          {contexts && active && (
            <ContextChip
              contexts={contexts}
              active={active}
              onChoose={choose}
            />
          )}
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>

      <main className="screen dscreen">
        <div className="discover__bar">
          <label className="dsearch">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle
                cx="11"
                cy="11"
                r="6.5"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              />
              <path
                d="m16 16 4 4"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
            <input
              type="search"
              value={typed}
              onChange={(e) => {
                setTyped(e.target.value);
                if (e.target.value.trim() && tab === "forYou") setTab("all");
              }}
              placeholder={t("discover:searchPlaceholder")}
              aria-label={t("discover:searchLabel")}
            />
          </label>
          <button
            type="button"
            className={`dfilter${filterCount ? " is-on" : ""}`}
            aria-haspopup="dialog"
            onClick={() => setFiltersOpen(true)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M4 7h16M7 12h10M10 17h4"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
            {t("discover:filters.open")}
            {filterCount > 0 && (
              <span className="dfilter__n">{filterCount}</span>
            )}
          </button>
        </div>

        {/* [DEC-V1-030] One row of choices, one active marker: the For you
            wall and its themes, every match, and saved. (Tabs and lens chips
            used to be two rows with two things "selected" at once.) */}
        <ScrollRail className="dlenses dnav">
          <button
            type="button"
            className={`dlens${tab === "forYou" && lens === "everyone" ? " is-on" : ""}`}
            aria-pressed={tab === "forYou" && lens === "everyone"}
            onClick={() => {
              setTab("forYou");
              setLens("everyone");
              window.scrollTo({ top: 0 });
            }}
          >
            {t("discover:tabs.forYou")}
            {wall.length > 0 && <span className="dlens__n">{wall.length}</span>}
          </button>
          {lenses
            .filter((l) => l.key !== "picked")
            .map((l) => (
              <button
                key={l.key}
                type="button"
                className={`dlens${tab === "forYou" && lens === l.key ? " is-on" : ""}`}
                aria-pressed={tab === "forYou" && lens === l.key}
                onClick={() => {
                  setTab("forYou");
                  setLens(l.key);
                  window.scrollTo({ top: 0 });
                }}
              >
                {t(`discover:lens.${l.key}`)}
                <span className="dlens__n">{l.count}</span>
              </button>
            ))}
          {(["all", "saved"] as Tab[]).map((k) => (
            <button
              key={k}
              type="button"
              className={`dlens${tab === k ? " is-on" : ""}`}
              aria-pressed={tab === k}
              onClick={() => {
                setTab(k);
                window.scrollTo({ top: 0 });
              }}
            >
              {t(`discover:tabs.${k}`)}
            </button>
          ))}
        </ScrollRail>

        {activeChips.length > 0 && (
          <div className="dchips">
            {activeChips.map((c) => (
              <button
                key={c.key}
                type="button"
                className="dchip"
                onClick={() => setFilters(c.clear())}
              >
                {c.label}
                <span aria-hidden="true">×</span>
                <span className="sr-only">{t("discover:chips.remove")}</span>
              </button>
            ))}
            <button
              type="button"
              className="link link--button"
              onClick={() => setFilters({})}
            >
              {t("discover:chips.clearAll")}
            </button>
          </div>
        )}

        {feed &&
          !feed.lookingForMissing &&
          feed.results.length > 0 &&
          feed.total !== null && (
            <p className="discover__count" aria-live="polite">
              {t(`discover:count.${tab}`, { count: feed.total })}
            </p>
          )}

        {tab === "forYou" ? (
          shelves === null && !needsChoice ? (
            <div className="shelves" aria-busy="true">
              {[0, 1].map((n) => (
                <section key={n} className="shelf">
                  <span className="sk sk--w50" style={{ height: 18 }} />
                  <div className="shelf__rail">
                    {Array.from({ length: 4 }, (_, i) => (
                      <div
                        key={i}
                        className="dtile dtile--skeleton"
                        aria-hidden="true"
                      >
                        <div className="dtile__photo" />
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : shelvesMissing || needsChoice || shelves === null ? (
            <div className="dempty">
              <Vignette id="partner" className="dempty__art" />
              <h2 className="h2">
                {family
                  ? t("discover:lookingFor.familyTitle", { name: familyName })
                  : t("discover:lookingFor.title")}
              </h2>
              <p className="caption">
                {family
                  ? t("discover:lookingFor.familyBody", { name: familyName })
                  : t("discover:lookingFor.body")}
              </p>
              {browseChoice ??
                (!family && (
                  <Link
                    className="btn btn--primary"
                    href="/me?edit=partner_preference"
                  >
                    {t("discover:lookingFor.cta")}
                  </Link>
                ))}
            </div>
          ) : shelves.length === 0 ? (
            <div className="dempty">
              <Vignette id="community" className="dempty__art" />
              <h2 className="h2">{t("discover:empty.forYou.title")}</h2>
              <p className="caption">{t("discover:empty.forYou.body")}</p>
              {!family && <MatchmakerEntry />}
            </div>
          ) : (
            <div className="dlens-wall">
              {!family && <MatchmakerEntry />}
              {/* The row themes as lenses over one wall of photos. Each
                  person appears once, under the first theme that claims
                  them; the chip's count says how many that is. */}

              {lens !== "everyone" && (
                <p className="dlens__sub">
                  {t(
                    `discover:shelf.${lens}.${family ? "subFor" : "sub"}`,
                    { name: familyName },
                  )}
                  {(() => {
                    const sh = shelves.find((s) => s.key === lens);
                    return sh && Object.keys(sh.see_all ?? {}).length > 0 ? (
                      <>
                        {" · "}
                        <button
                          type="button"
                          className="link link--button"
                          onClick={() => seeAll(sh)}
                        >
                          {t("discover:shelf.seeAll")}
                        </button>
                      </>
                    ) : null;
                  })()}
                </p>
              )}
              <div className="dwall dwall--lens">
                {wall
                  .filter((w) => lens === "everyone" || w.key === lens)
                  .map((w, i) =>
                    renderTile(
                      w.r,
                      // Every match "fits each other's preferences", and "in
                      // your city" repeats the city already on the tile, so
                      // those say nothing; the other reasons are the news.
                      w.key === "picked" || w.key === "mostCompatible" || w.key === "near"
                        ? null
                        : w.key === "moving"
                          ? t("discover:lens.moving")
                          : w.reason,
                      lens === "everyone" && i === 0 && w.key === "mostCompatible",
                    ),
                  )}
              </div>
            </div>
          )
        ) : !feed ? (
          <div className="dwall" aria-busy="true">
            {Array.from({ length: 10 }, (_, i) => (
              <div key={i} className="dtile dtile--skeleton" aria-hidden="true">
                <div className="dtile__photo" />
                <div className="dtile__text">
                  <span className="sk sk--w70" />
                  <span className="sk sk--w50" />
                </div>
              </div>
            ))}
          </div>
        ) : feed.horoscopeChartMissing ? (
          <div className="dempty">
            <h2 className="h2">{t("horoscope:filter.needChartTitle")}</h2>
            <p className="caption">
              {family
                ? t("horoscope:missing.NO_CHART_SELF_FAMILY", { name: familyName })
                : t("horoscope:missing.NO_CHART_SELF")}
            </p>
            {!family && (
              <Link className="btn btn--primary" href="/me">
                {t("horoscope:addDetails")}
              </Link>
            )}
          </div>
        ) : feed.lookingForMissing ? (
          <div className="dempty">
            <Vignette id="partner" className="dempty__art" />
            <h2 className="h2">
              {family
                ? t("discover:lookingFor.familyTitle", { name: familyName })
                : t("discover:lookingFor.title")}
            </h2>
            <p className="caption">
              {family
                ? t("discover:lookingFor.familyBody", { name: familyName })
                : t("discover:lookingFor.body")}
            </p>
            {browseChoice ??
              (!family && (
                <Link
                  className="btn btn--primary"
                  href="/me?edit=partner_preference"
                >
                  {t("discover:lookingFor.cta")}
                </Link>
              ))}
          </div>
        ) : feed.results.length === 0 ? (
          <div className="dempty">
            <Vignette
              id={tab === "saved" ? "photos" : "community"}
              className="dempty__art"
            />
            <h2 className="h2">{t(`discover:empty.${tab}.title`)}</h2>
            <p className="caption">
              {t(`discover:empty.${tab}.body`, { name: familyName })}
            </p>
            {(filterCount > 0 || q) && tab !== "saved" && (
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => {
                  setFilters({});
                  setTyped("");
                }}
              >
                {t("discover:chips.clearAll")}
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="dwall">
              {feed.results.map((r) => renderTile(r))}
            </div>
            <div ref={sentinel} className="dwall__end">
              {loadingMore
                ? t("discover:search.more")
                : !feed.hasMore
                  ? t("discover:search.end")
                  : null}
            </div>
          </>
        )}
      </main>

      {filtersOpen && (
        <DiscoverFiltersSheet
          initial={filters}
          forCandidate={forCandidate}
          onClose={() => setFiltersOpen(false)}
          onApply={(next) => {
            setFilters(next);
            setFiltersOpen(false);
            if (tab !== "all") setTab("all");
            window.scrollTo({ top: 0 });
          }}
        />
      )}
    </>
  );
}
