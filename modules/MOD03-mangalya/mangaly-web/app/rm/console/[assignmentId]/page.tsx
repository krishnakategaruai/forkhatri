"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import { Avatar } from "@/components/Avatar";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { resolveMediaUrl } from "@/lib/api";
import { relationKey } from "@/lib/homeCircle";
import { openDirect, threadHref } from "@/lib/messages";
import {
  addInteraction,
  endAssignment,
  formatWhen,
  getAssignment,
  searchForMember,
  suggestToMember,
  type AssignmentDetail,
  type RmInteraction,
  type RmSearchResult,
} from "@/lib/rm";

import "../../rm.css";

/* [DEC-V1-032] One family, on the RM's desk: what the member is looking for
 * (never their contact details), a search that runs AS the member — ranked
 * the member's own way, with the member's own rule about whom they see —
 * each result with "Suggest" and a note in the member's language, the
 * suggestions already made and how the family answered, and the log of
 * calls and meetings the family reads. Desktop: summary left, work right. */

function readable(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "object") {
    const v = value as Record<string, unknown>;
    if ("min" in v || "max" in v) return [v.min, v.max].filter((x) => x != null).join(" – ");
    return Object.values(v).map(readable).filter(Boolean).join(", ");
  }
  return String(value).replace(/_/g, " ");
}

type T = (key: string, options?: Record<string, unknown>) => string;

/* [Owner walkthrough, 2026-09-30] What the family is looking for, the way an
 * agent or relationship manager reads it: "Age 27–32 · Hyderabad · Telugu ·
 * Vegetarian", then the family's own words once. The raw stored brief used to
 * be printed as-is — map coordinates, importance scores, a version stamp and
 * the same quote three times. Internal keys (scales, priorities, the brief's
 * scoring) never reach the screen. */
function preferenceSummary(pp: Record<string, unknown>, t: T): { facts: string[]; words: string[] } {
  const facts: string[] = [];
  const list = (v: unknown): string[] =>
    Array.isArray(v) ? v.map(String) : typeof v === "string" && v ? [v] : [];
  const age = pp.age_range as { min?: number; max?: number } | undefined;
  if (age && (age.min != null || age.max != null)) {
    facts.push(t("rm:console.pref.age", { min: age.min ?? "", max: age.max ?? "" }));
  }
  for (const place of list(pp.locality)) facts.push(place);
  // The matchmaker brief is stored as {text, items, …}; older rows as a bare list.
  const rawBrief = pp.brief as unknown;
  const briefObj = rawBrief && !Array.isArray(rawBrief) && typeof rawBrief === "object" ? (rawBrief as Record<string, unknown>) : null;
  const brief = (Array.isArray(rawBrief) ? rawBrief : Array.isArray(briefObj?.items) ? briefObj?.items : []) as Array<Record<string, unknown>>;
  for (const item of brief) {
    const field = String(item.field ?? "");
    for (const v of list(item.values)) {
      if (field === "mother_tongue") facts.push(t(`profile:option.mother_tongue.${v}`, { defaultValue: v }));
      if (field === "diet") facts.push(t(`profile:option.diet.${v}`, { defaultValue: v }));
    }
  }
  for (const v of list(pp.diet)) facts.push(t(`profile:option.diet.${v}`, { defaultValue: v }));
  for (const v of list(pp.education)) {
    facts.push(t(`profile:option.highest_education_level.${v}`, { defaultValue: v }));
  }
  // The family's own words: the whole sentence they wrote when there is one.
  const fullText = typeof briefObj?.text === "string" ? briefObj.text.trim() : "";
  const words = fullText
    ? [fullText]
    : brief.map((item) => String(item.quote ?? "").trim()).filter((q, i, all) => q && all.indexOf(q) === i);
  return { facts: facts.filter((f, i, all) => f && all.indexOf(f) === i), words };
}

export default function RmAssignmentPage() {
  const { t, i18n } = useTranslation(["rm", "common", "circle", "profile"]);
  const router = useRouter();
  const params = useParams<{ assignmentId: string }>();
  const assignmentId = params.assignmentId;

  const [detail, setDetail] = useState<AssignmentDetail | null | undefined>(undefined);
  const [q, setQ] = useState("");
  const [ageMin, setAgeMin] = useState("");
  const [ageMax, setAgeMax] = useState("");
  const [results, setResults] = useState<RmSearchResult[] | null>(null);
  const [total, setTotal] = useState(0);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [noteFor, setNoteFor] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [kind, setKind] = useState<RmInteraction["kind"]>("call");
  const [when, setWhen] = useState("");
  const [summary, setSummary] = useState("");
  const [logging, setLogging] = useState(false);
  const [ending, setEnding] = useState(false);
  const [confirmEnd, setConfirmEnd] = useState(false);

  const reload = useCallback(async () => {
    const d = await getAssignment(assignmentId);
    setDetail(d);
  }, [assignmentId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const search = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setSearching(true);
    setSearchError(null);
    const page = await searchForMember(assignmentId, {
      q: q.trim() || undefined,
      age_min: ageMin ? Number(ageMin) : undefined,
      age_max: ageMax ? Number(ageMax) : undefined,
    });
    setSearching(false);
    if (!page) {
      setSearchError(t("rm:console.search.failed"));
      setResults([]);
      return;
    }
    setResults(page.results);
    setTotal(page.total);
  };

  const suggest = async (r: RmSearchResult) => {
    setSending(true);
    const out = await suggestToMember(assignmentId, r.candidate_account_id, note.trim());
    setSending(false);
    if (out.ok) {
      setNoteFor(null);
      setNote("");
      setResults((prev) =>
        (prev ?? []).map((x) => (x.candidate_account_id === r.candidate_account_id ? { ...x, already_suggested: true } : x)),
      );
      await reload();
    }
  };

  const log = async (e: React.FormEvent) => {
    e.preventDefault();
    setLogging(true);
    const out = await addInteraction(assignmentId, {
      kind,
      scheduled_at: when ? new Date(when).toISOString() : null,
      summary: summary.trim() || null,
    });
    setLogging(false);
    if (out.ok) {
      setWhen("");
      setSummary("");
      await reload();
    }
  };

  const end = async () => {
    setEnding(true);
    const out = await endAssignment(assignmentId);
    setEnding(false);
    setConfirmEnd(false);
    if (out.ok) router.push("/rm/console");
  };

  const message = async (accountId: string) => {
    const r = await openDirect(accountId);
    if (r.ok) router.push(threadHref(r.data.conversation_id, "direct"));
  };

  const member = detail?.member ?? null;
  const active = detail?.assignment.status === "active";
  const memberLanguage = member?.language_preference
    ? t(`rm:language.${member.language_preference}`, { defaultValue: member.language_preference })
    : null;

  return (
    <>
      <header className="topbar">
        <Link className="link" href="/rm/console">
          ‹ {t("rm:console.title")}
        </Link>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen rm-console">
        {detail === undefined ? (
          <p className="caption">{t("common:state.loading")}</p>
        ) : detail === null ? (
          <div className="empty rm-empty">
            <h2 className="h3">{t("rm:console.notFound")}</h2>
          </div>
        ) : (
          <div className="rm-detail">
            {/* ---- the member, as the RM may know them ---- */}
            <aside className="card rm-summary">
              <div className="rm-summary__head">
                <Avatar
                  name={detail.assignment.member_name ?? ""}
                  photoUrl={resolveMediaUrl(detail.assignment.member_photo_url)}
                  size={56}
                />
                <div>
                  <div className="rm-summary__name">{detail.assignment.member_name}</div>
                  <div className="caption">
                    {active
                      ? t("rm:console.families.since", { date: formatWhen(detail.assignment.assigned_at, i18n.language) })
                      : t("rm:console.families.endedOn", { date: formatWhen(detail.assignment.ended_at, i18n.language) })}
                  </div>
                </div>
              </div>
              {detail.assignment.note && <p className="caption" style={{ margin: 0 }}>{detail.assignment.note}</p>}
              {member && (
                <dl className="rm-facts">
                  {member.age != null && (
                    <>
                      <dt>{t("rm:console.member.age")}</dt>
                      <dd>{member.age}</dd>
                    </>
                  )}
                  {member.city && (
                    <>
                      <dt>{t("rm:console.member.city")}</dt>
                      <dd>{member.city}</dd>
                    </>
                  )}
                  {member.looking_for && (
                    <>
                      <dt>{t("rm:console.member.lookingFor")}</dt>
                      <dd>{t(`profile:option.looking_for.${member.looking_for}`, { defaultValue: member.looking_for })}</dd>
                    </>
                  )}
                  {member.mother_tongue && (
                    <>
                      <dt>{t("rm:console.member.motherTongue")}</dt>
                      <dd>{member.mother_tongue}</dd>
                    </>
                  )}
                  {memberLanguage && (
                    <>
                      <dt>{t("rm:console.member.appLanguage")}</dt>
                      <dd>{memberLanguage}</dd>
                    </>
                  )}
                  {(member.profession || member.education_level) && (
                    <>
                      <dt>{t("rm:console.member.work")}</dt>
                      <dd>{[member.profession, member.education_level ? t(`profile:option.highest_education_level.${member.education_level}`, { defaultValue: member.education_level }) : null].filter(Boolean).join(" · ")}</dd>
                    </>
                  )}
                  {(() => {
                    const { facts, words } = preferenceSummary(member.partner_preference, t as T);
                    if (facts.length === 0 && words.length === 0) return null;
                    return (
                      <>
                        <dt>{t("rm:console.member.partner")}</dt>
                        <dd>
                          {facts.length > 0 && <span>{facts.join(" · ")}</span>}
                          {words.length > 0 && (
                            <span className="rm-facts__words">“{words.join(" · ")}”</span>
                          )}
                        </dd>
                      </>
                    );
                  })()}
                  {Object.keys(member.family_involvement).length > 0 && (
                    <>
                      <dt>{t("rm:console.member.family")}</dt>
                      <dd>{Object.values(member.family_involvement).map(readable).join(" · ")}</dd>
                    </>
                  )}
                </dl>
              )}
              {member && member.family.length > 0 && (
                <div>
                  <div className="label">{t("rm:console.member.circle")}</div>
                  <ul className="rm-family">
                    {member.family.map((f) => {
                      const canChat = f.relationship_type === "parent" || f.relationship_type === "guardian";
                      return (
                        <li key={f.account_id}>
                          <button
                            type="button"
                            className="chip"
                            disabled={!canChat}
                            title={canChat ? t("rm:card.message") : undefined}
                            onClick={() => canChat && message(f.account_id)}
                          >
                            {f.display_name} · {t(relationKey(f.relation, f.relationship_type))}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
              {active && (
                <div className="rm-card__actions">
                  <button type="button" className="btn btn--primary btn--sm" onClick={() => message(detail.assignment.member_account_id)}>
                    {t("rm:console.member.message")}
                  </button>
                  {!confirmEnd ? (
                    <button type="button" className="btn btn--ghost btn--sm rm-summary__end" onClick={() => setConfirmEnd(true)}>
                      {t("rm:console.end.button")}
                    </button>
                  ) : (
                    <span className="rm-card__actions">
                      <button type="button" className="btn btn--danger btn--sm" disabled={ending} onClick={end}>
                        {t("rm:console.end.confirm")}
                      </button>
                      <button type="button" className="btn btn--ghost btn--sm" onClick={() => setConfirmEnd(false)}>
                        {t("common:action.cancel", { defaultValue: "Cancel" })}
                      </button>
                    </span>
                  )}
                </div>
              )}
            </aside>

            <div className="rm-work">
              {/* ---- search as the member ---- */}
              {active && (
                <section className="section rm-search">
                  <div className="section__head">
                    <h3 className="h3" style={{ margin: 0 }}>
                      {t("rm:console.search.title", { name: (detail.assignment.member_name ?? "").split(" ")[0] })}
                    </h3>
                    {results && <span className="caption">{t("rm:console.search.count", { count: total })}</span>}
                  </div>
                  <p className="caption" style={{ margin: 0 }}>
                    {t("rm:console.search.hint")}
                  </p>
                  <form className="rm-search__row" onSubmit={search}>
                    <label className="field">
                      <span className="label">{t("rm:console.search.q")}</span>
                      <input className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("rm:console.search.qPlaceholder")} />
                    </label>
                    <label className="field">
                      <span className="label">{t("rm:console.search.ageMin")}</span>
                      <input className="input" inputMode="numeric" value={ageMin} onChange={(e) => setAgeMin(e.target.value.replace(/\D/g, ""))} />
                    </label>
                    <label className="field">
                      <span className="label">{t("rm:console.search.ageMax")}</span>
                      <input className="input" inputMode="numeric" value={ageMax} onChange={(e) => setAgeMax(e.target.value.replace(/\D/g, ""))} />
                    </label>
                    <button type="submit" className="btn btn--primary" disabled={searching}>
                      {searching ? t("common:state.loading") : t("rm:console.search.submit")}
                    </button>
                  </form>
                  {searchError && <p className="rm-inline-error">{searchError}</p>}
                  {results && results.length === 0 && !searchError && (
                    <p className="caption">{t("rm:console.search.empty")}</p>
                  )}
                  {results && results.length > 0 && (
                    <ul className="rm-results">
                      {results.map((r) => {
                        const title = r.open_name
                          ? [r.open_name, r.age].filter(Boolean).join(", ")
                          : r.age
                            ? t("profile:hub.ageYears", { age: r.age })
                            : "";
                        const city = r.locality?.split(",")[0]?.trim();
                        const open = noteFor === r.candidate_account_id;
                        return (
                          <li key={r.candidate_account_id} className="rm-tile">
                            <Link href={`/profile/${r.candidate_account_id}`} className="rm-tile__link" prefetch={false}>
                              <div className="rm-tile__photo">
                                {r.photo_url ? (
                                  // eslint-disable-next-line @next/next/no-img-element
                                  <img src={resolveMediaUrl(r.photo_url) ?? ""} alt="" loading="lazy" decoding="async" />
                                ) : (
                                  <span className="rm-tile__nophoto">
                                    <Avatar anonymized size={64} />
                                  </span>
                                )}
                              </div>
                              <div className="rm-tile__text">
                                <span className="rm-tile__title">{[title, city].filter(Boolean).join(" · ")}</span>
                                {(r.profession || r.education_level) && (
                                  <span className="rm-tile__line">{[r.profession, r.education_level ? t(`profile:option.highest_education_level.${r.education_level}`, { defaultValue: r.education_level }) : null].filter(Boolean).join(" · ")}</span>
                                )}
                              </div>
                            </Link>
                            {r.already_suggested ? (
                              <span className="rm-suggest__done">{t("rm:console.suggest.done")}</span>
                            ) : open ? (
                              <div className="rm-suggest">
                                <textarea
                                  className="textarea"
                                  value={note}
                                  onChange={(e) => setNote(e.target.value)}
                                  placeholder={t("rm:console.suggest.notePlaceholder", { name: (detail.assignment.member_name ?? "").split(" ")[0] })}
                                  maxLength={1000}
                                  autoFocus
                                />
                                <div className="rm-tile__actions">
                                  <button type="button" className="btn btn--primary btn--sm" disabled={sending} onClick={() => suggest(r)}>
                                    {t("rm:console.suggest.send")}
                                  </button>
                                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => setNoteFor(null)}>
                                    {t("common:action.cancel", { defaultValue: "Cancel" })}
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="rm-tile__actions">
                                <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setNoteFor(r.candidate_account_id); setNote(""); }}>
                                  {t("rm:console.suggest.button")}
                                </button>
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </section>
              )}

              {/* ---- what has been put forward ---- */}
              <section className="section">
                <div className="section__head">
                  <h3 className="h3" style={{ margin: 0 }}>
                    {t("rm:console.suggested.title")}
                  </h3>
                  {detail.suggestions.length > 0 && (
                    <span className="caption">{t("rm:page.suggestions.count", { count: detail.suggestions.length })}</span>
                  )}
                </div>
                {detail.suggestions.length === 0 ? (
                  <p className="caption">{t("rm:console.suggested.empty")}</p>
                ) : (
                  <ul className="rm-wall">
                    {detail.suggestions.map((s) => {
                      const p = s.person;
                      const title = p?.open_name
                        ? [p.open_name, p.age].filter(Boolean).join(", ")
                        : p?.age
                          ? t("profile:hub.ageYears", { age: p.age })
                          : "";
                      return (
                        <li key={s.id} className={`rm-tile${s.member_decision ? ` rm-tile--${s.member_decision}` : ""}`}>
                          <Link href={`/profile/${s.suggested_account_id}`} className="rm-tile__link" prefetch={false}>
                            <div className="rm-tile__photo">
                              {p?.photo_url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img src={resolveMediaUrl(p.photo_url) ?? ""} alt="" loading="lazy" decoding="async" />
                              ) : (
                                <span className="rm-tile__nophoto">
                                  <Avatar anonymized size={64} />
                                </span>
                              )}
                              <span className="rm-tile__state">
                                {s.member_decision ? t(`rm:decision.${s.member_decision}`) : t("rm:decision.waiting")}
                              </span>
                            </div>
                            <div className="rm-tile__text">
                              <span className="rm-tile__title">{[title, p?.locality?.split(",")[0]?.trim()].filter(Boolean).join(" · ")}</span>
                              <span className="rm-tile__line">{formatWhen(s.created_at, i18n.language)}</span>
                            </div>
                          </Link>
                          {s.note && <blockquote className="rm-tile__note">{s.note}</blockquote>}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </section>

              {/* ---- calls, meetings, notes ---- */}
              <section className="section">
                <div className="section__head">
                  <h3 className="h3" style={{ margin: 0 }}>
                    {t("rm:page.log.title")}
                  </h3>
                </div>
                <p className="caption" style={{ margin: 0 }}>
                  {t("rm:console.log.hint")}
                </p>
                {active && (
                  <form className="card rm-interaction-form" onSubmit={log}>
                    <label className="field">
                      <span className="label">{t("rm:console.log.kind")}</span>
                      <select className="input" value={kind} onChange={(e) => setKind(e.target.value as RmInteraction["kind"])}>
                        <option value="call">{t("rm:interaction.kind.call")}</option>
                        <option value="meeting">{t("rm:interaction.kind.meeting")}</option>
                        <option value="note">{t("rm:interaction.kind.note")}</option>
                      </select>
                    </label>
                    <label className="field">
                      <span className="label">{t("rm:console.log.when")}</span>
                      <input className="input" type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
                    </label>
                    <label className="field">
                      <span className="label">{t("rm:console.log.summary")}</span>
                      <textarea className="textarea" value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={1000} />
                    </label>
                    <button type="submit" className="btn btn--primary" disabled={logging || (!when && !summary.trim())}>
                      {t("rm:console.log.submit")}
                    </button>
                  </form>
                )}
                {detail.interactions.length === 0 ? (
                  <p className="caption">{t("rm:page.log.empty")}</p>
                ) : (
                  <ol className="rm-log">
                    {detail.interactions.map((i) => {
                      const upcoming = !!i.scheduled_at && new Date(i.scheduled_at).getTime() > Date.now();
                      return (
                        <li key={i.id} className={`rm-log__item${upcoming ? " is-upcoming" : ""}`}>
                          <span className="rm-log__kind">{t(`rm:interaction.kind.${i.kind}`)}</span>
                          <span className="rm-log__when">
                            {formatWhen(i.scheduled_at ?? i.created_at, i18n.language)}
                            {upcoming ? ` · ${t("rm:page.log.upcoming")}` : ""}
                          </span>
                          {i.summary && <span className="rm-log__summary">{i.summary}</span>}
                        </li>
                      );
                    })}
                  </ol>
                )}
              </section>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
