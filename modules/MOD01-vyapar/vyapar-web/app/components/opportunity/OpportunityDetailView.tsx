"use client";

// [IMP38 — Refactor C] Opportunity detail, presentational half.
//
// Everything the screen SHOWS, moved verbatim out of
// app/opportunities/[id]/page.tsx (see that file for the product reasoning
// behind the layout: WHAT it is, AM I A FIT, WHO is behind it, HOW MANY
// others — rebuilt 2026-09-21 after the owner's review). This component
// fetches nothing: data comes in as props, every action goes out as a
// callback, and blocks that load their own data (matching profiles,
// performance report, report sheet) arrive as slots. That is what lets the
// same view render on the route, in the embeddable OpportunityDetailPanel,
// or in another host app.
//
// UI-only state stays here (the "Why this?" and "Not interested" toggles,
// and the phone action bar that slides in once the action card scrolls
// away) because it is about presentation, not data.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { NotInterestedReason, Opportunity, WhyResponse } from "@/lib/sdk";
import SponsoredBadge from "@/app/components/SponsoredBadge";
// [FE2] count-based poster badges + "Nobody charges job seekers" notice
import { BadgeList } from "@/app/components/trust/Badges";
import SeekerProtectionNotice from "@/app/components/trust/SeekerProtectionNotice";
import { Morph } from "@/app/components/Screen";
import { useRoutes } from "@/app/host/HostProvider";
import OpportunityCard from "./OpportunityCard";
import { hostOf, NOT_INTERESTED_REASON_KEYS, signalLabel } from "./labels";
import { structuredFacts, type T as LabelT } from "@/app/components/composer/labels";
import { formatDayMonth, formatMonthYear } from "@/lib/format";
import { payLines } from "@/app/components/discover/DiscoverCard";
import { Star } from "lucide-react";
// [Trust pack] paid on time, close the loop, restrictions
import { PaidOnTimeLine } from "@/app/components/trust/PaidOnTime";
import { ApplicantsWaitingNudge, CloseConfirmSheet } from "@/app/components/trust/CloseLoop";
import RestrictionCard from "@/app/components/trust/RestrictionCard";

/** [Design language 2026-09-29, glossary] A yearly "₹9–14 LPA" reads as
 *  "₹75,000–₹1,17,000 a month" with "₹9–14 lakh a year" under it — the same
 *  rule as the Discover card (payLines). Other pay lines show as written. */
function PayFact({ label }: { label: string }) {
  const { t, i18n } = useTranslation(["explore"]);
  const pay = payLines(label, i18n.language);
  return (
    <span className="vy-fact-value">
      {pay.monthly ? t("explore:card.perMonth", { amount: pay.main }) : pay.main}
      {pay.lakhRange && <small className="vy-fact-sub">{t("explore:card.perYearLakh", { range: pay.lakhRange })}</small>}
    </span>
  );
}

export interface OpportunityDetailActions {
  onToggleSave: () => void;
  onShare: () => void;
  /** The member followed the link to the public source. */
  onExternalOpen: () => void;
  onPause: () => void;
  onResume: () => void;
  onRenew: () => void;
  onClose: () => void;
  onConfirmField: (field: string) => void;
  onPublish: () => void;
  onNotInterested: (reason: NotInterestedReason) => void;
  /** Asked the first time "Why this?" opens; the container loads `why`. */
  onRequestWhy: () => void;
}

export interface OpportunityDetailViewProps extends OpportunityDetailActions {
  opportunity: Opportunity;
  similar: Opportunity[];
  why: WhyResponse | null;
  busy: boolean;
  notice: string | null;
  /** Poster only: profiles that already have the asked-for skills. */
  matchingProfilesSlot?: React.ReactNode;
  /** Poster only: the performance report. */
  performanceSlot?: React.ReactNode;
  /** Viewer only: the report / block sheet. */
  reportSlot?: React.ReactNode;
  /**
   * [FE1] Viewer only: replaces the default primary link (for a job, the
   * one-tap Apply that opens its confirmation sheet in place). Rendered in
   * the action card and in the phone action bar.
   */
  primaryActionSlot?: React.ReactNode;
  /**
   * [FE1 → FE2] Viewer only, when the poster allows calls before accepting
   * (`allow_precall`): FE2's PrecallActions (Call + WhatsApp) mounts here,
   * beside the primary action.
   */
  precallSlot?: React.ReactNode;
  /** [FE1] Poster only: applicant counts per stage + the link to the applicants board. */
  applicantsSlot?: React.ReactNode;
}

export default function OpportunityDetailView(props: OpportunityDetailViewProps) {
  const { opportunity: opp, similar, why, busy, notice } = props;
  const id = opp.id;
  const { t, i18n } = useTranslation(["opportunities", "common", "ranking", "commercial", "discover", "hiring"]);
  const routes = useRoutes();
  const [showWhy, setShowWhy] = useState(false);
  const [showReasons, setShowReasons] = useState(false);
  // [Trust pack §3] Close asks first: who is still waiting, and that they will be told politely.
  const [closing, setClosing] = useState(false);
  // Phone only: once the in-page action card scrolls away, a slim bar with
  // the primary action slides up so a person who has just finished reading
  // never has to scroll back to act. Both reference apps pin their action
  // permanently, which duplicates it on the first screen; this appears only
  // when the real one is out of view. Hidden by CSS on desktop, where the
  // action column is already sticky.
  const actionCardRef = useRef<HTMLDivElement | null>(null);
  const [actionOffscreen, setActionOffscreen] = useState(false);
  useEffect(() => {
    const el = actionCardRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([entry]) => setActionOffscreen(!entry.isIntersecting && entry.boundingClientRect.top < 0));
    io.observe(el);
    return () => io.disconnect();
  }, [opp?.id]);

  // [Design language 2026-09-29] Indian day-first dates ("Apply by 4 Oct"),
  // never the browser's US order ("Oct 4") — lib/format.ts.
  const fmtDay = (iso: string) => formatDayMonth(iso, i18n.language);
  const fmtMonthYear = (iso: string) => formatMonthYear(iso, i18n.language);

  const isPublic = opp.source_segment === "public";
  const sourceLabel = opp.source_name || hostOf(opp.source_url);
  const viewerCanAct = !opp.is_poster && opp.state === "active";
  const soon = opp.days_left !== null && opp.days_left <= 3;

  // [FE1] The typed fields read as facts (salary range, shift, openings,
  // qualification, English, budget, duration, level…), with the server's
  // localized money line first and the free-text pay as its fallback.
  const facts = [
    { key: "pay", label: t("opportunities:detail.factPay"), value: opp.compensation_label ?? opp.compensation, wide: false },
    { key: "timing", label: t("opportunities:detail.factDuration"), value: opp.timing, wide: false },
    { key: "mode", label: t("opportunities:detail.factMode"), value: opp.work_mode ? t(`opportunities:workMode.${opp.work_mode}` as "workMode.on_site") : null, wide: false },
    { key: "location", label: t("opportunities:detail.factLocation"), value: opp.location, wide: false },
    ...structuredFacts(t as LabelT, opp.type, opp.structured, i18n.language),
  ].filter((f) => f.value);

  const matchCount = opp.capability_match ? opp.capability_match.filter(Boolean).length : 0;
  const replyHabit = opp.poster?.reply_rate
    ? [
        t(`opportunities:detail.replyRate.${opp.poster.reply_rate}` as "detail.replyRate.most"),
        opp.poster.reply_speed ? t(`opportunities:detail.replySpeed.${opp.poster.reply_speed}` as "detail.replySpeed.day") : null,
      ]
        .filter(Boolean)
        .join(" · ")
    : null;

  const primaryAction =
    isPublic && opp.source_url ? (
      <a className="vy-btn vy-btn-primary" href={opp.source_url} target="_blank" rel="noopener noreferrer" onClick={props.onExternalOpen}>
        {t(opp.type === "employment" ? "opportunities:actionLabel.applyOnSource" : "opportunities:detail.openOfficialWebsite")}
      </a>
    ) : (
      <a className="vy-btn vy-btn-primary" href={routes.enquireOpportunity(id)} style={{ textDecoration: "none" }}>
        {t(`opportunities:actionLabel.${opp.type_action_label}` as "actionLabel.apply")}
      </a>
    );

  const hasFitSection = opp.capability_labels.length > 0 || opp.min_experience_years !== null || !!opp.requirements;

  return (
    <>
      {/* Header: what kind of thing, how long it stays open, then the title
          and a byline that carries trust — who posted it and from where. */}
      <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
        {/* [FE1] One word per type everywhere a person sees it: Job / Freelance project / Local service. */}
        <span className="vy-chip">{t(`hiring:kinds.${opp.type}`, { defaultValue: t(`opportunities:type.${opp.type}` as "type.employment") })}</span>
        {opp.state !== "active" && <span className="vy-chip">{t(`opportunities:detail.state.${opp.state}` as "detail.state.active")}</span>}
        {opp.sponsored && <SponsoredBadge />}
        {opp.deadline && opp.state === "active" && (
          <span className={soon ? "vy-deadline-soon" : "vy-muted"} style={{ fontSize: 14 }}>
            {opp.days_left === 0
              ? t("opportunities:detail.lastDay")
              : `${t("opportunities:detail.applyBy", { date: fmtDay(opp.deadline) })} · ${t("opportunities:detail.daysLeft", { count: opp.days_left ?? 0 })}`}
          </span>
        )}
      </div>

      <Morph name={`opportunity-${id}`}>
        <h1>{opp.title}</h1>
      </Morph>

      {/* [Trust pack §3] the poster sees why their post is restricted, and can appeal */}
      {opp.is_poster && opp.restriction && <RestrictionCard item={opp.restriction} compact />}

      {!opp.is_poster && (
        <div className="vy-byline">
          {opp.submitter_name && (
            <span>
              {isPublic && sourceLabel
                ? t("opportunities:detail.sharedBy", { name: opp.submitter_name, source: sourceLabel })
                : t("opportunities:detail.postedBy", { name: opp.submitter_name })}
            </span>
          )}
          {!isPublic && (
            <>
              <span className="vy-byline-sep" aria-hidden="true">·</span>
              <span>{t("opportunities:detail.fromCommunity")}</span>
            </>
          )}
          {/* [Trust pack §2] "Paid on time: 2 of 3" under the name, only once three people answered */}
          {opp.poster_paid_on_time?.shown && (
            <span style={{ flexBasis: "100%" }}>
              <PaidOnTimeLine value={opp.poster_paid_on_time} />
            </span>
          )}
          {opp.posted_days_ago !== null && (
            <>
              <span className="vy-muted" style={{ flexBasis: "100%" }}>
                {opp.posted_days_ago === 0
                  ? t("opportunities:detail.postedToday")
                  : t("opportunities:detail.postedDaysAgo", { count: opp.posted_days_ago })}
              </span>
            </>
          )}
        </div>
      )}

      <div className="vy-detail">
        {/* Reading column, part 1 — the at-a-glance facts come first so a
            person can decide before reading a word of description. */}
        <div className="vy-detail-main">
          {facts.length > 0 ? (
            <div className="vy-facts">
              {facts.map((f) => (
                <div key={f.key} className={f.wide ? "vy-fact vy-fact-wide" : "vy-fact"}>
                  <span className="vy-fact-label">{f.label}</span>
                  {f.key === "pay" && typeof f.value === "string" ? (
                    <PayFact label={f.value} />
                  ) : (
                    <span className="vy-fact-value">{f.value}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="vy-muted">{t("opportunities:detail.noDetailsYet")}</p>
          )}
          {notice && <p className="vy-error">{notice}</p>}
          {!opp.is_poster && <SeekerProtectionNotice protection={opp.seeker_protection} objectId={id} />}
        </div>

        {/* Action column: sticky beside the whole read on desktop; on a
            phone it sits right under the facts, so the primary action is on
            the first screen without scrolling. */}
        <div className="vy-detail-aside vy-detail-aside-full">
          {opp.is_poster && opp.state !== "draft" && <ApplicantsWaitingNudge waiting={opp.applicants_waiting} />}
          {opp.is_poster && opp.state !== "draft" && props.applicantsSlot}

          {opp.is_poster && opp.state !== "draft" && (
            <div className="vy-card vy-stack vy-card-actions">
              {(opp.state === "active" || opp.state === "stale") && (
                <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={props.onPause}>
                  {t("opportunities:detail.pause")}
                </button>
              )}
              {opp.state === "paused" && (
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onResume}>
                  {t("opportunities:detail.resume")}
                </button>
              )}
              {opp.state === "expired" && (
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onRenew}>
                  {t("opportunities:detail.renew")}
                </button>
              )}
              {["active", "paused", "stale"].includes(opp.state) && (
                <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => setClosing(true)}>
                  {t("opportunities:detail.close")}
                </button>
              )}
              {opp.state === "active" && (
                <a className="vy-btn vy-btn-secondary" href={routes.boost("opportunity", id)} style={{ textDecoration: "none" }}>
                  {t("commercial:action.boost")}
                </a>
              )}
            </div>
          )}

          {viewerCanAct && (
            <div className="vy-card vy-stack vy-card-actions" ref={actionCardRef}>
              {props.primaryActionSlot ?? primaryAction}
              {props.precallSlot}

              {/* Decision context at the moment of acting: how many others
                  have responded and whether this person replies, the
                  question neither reference app answers directly. */}
              {isPublic && opp.source_url ? (
                <p className="vy-muted" style={{ fontSize: 12 }}>🔒 {t("opportunities:detail.leavingVyaparNotice")}</p>
              ) : (
                (opp.response_bucket || replyHabit) && (
                  <ul className="vy-signal-list">
                    {opp.response_bucket && <li>{t(`opportunities:detail.responses.${opp.response_bucket}` as "detail.responses.none")}</li>}
                    {replyHabit && <li>{replyHabit}</li>}
                  </ul>
                )
              )}

              <div className="vy-row" style={{ gap: 8 }}>
                <button className="vy-btn vy-btn-secondary" style={{ flex: 1 }} disabled={busy} onClick={props.onToggleSave}>
                  {opp.saved ? `★ ${t("common:action.saved")}` : `☆ ${t("common:action.save")}`}
                </button>
                <button className="vy-btn vy-btn-secondary" style={{ flex: 1 }} onClick={props.onShare}>
                  {t("common:action.share")}
                </button>
              </div>

              {/* WorkIndia's "No payment involved" banner, placed where it
                  matters (beside the action) and one tap from doing
                  something about it. Not on Public items: an official
                  source can legitimately charge an application fee. */}
              {/* [FE2] the fuller seeker-protection notice replaces this line on job posts */}
              {!isPublic && !opp.seeker_protection?.applies && (
                <p className="vy-safety-line">
                  {t("opportunities:detail.freeToRespond")}{" "}
                  <a className="vy-tap-link" href="#report-opportunity">{t("opportunities:detail.reportIfAsked")}</a>
                </p>
              )}

              <div className="vy-row" style={{ gap: 8, justifyContent: "space-between" }}>
                <button
                  className="vy-btn vy-btn-ghost"
                  onClick={() => {
                    setShowWhy((v) => !v);
                    if (!why) props.onRequestWhy();
                  }}
                  aria-expanded={showWhy}
                >
                  {t("opportunities:detail.whyThis")}
                </button>
                <button className="vy-btn vy-btn-ghost" onClick={() => setShowReasons((v) => !v)} aria-expanded={showReasons}>
                  {t("common:action.notInterested")}
                </button>
              </div>

              {showWhy && why && (
                <div className="vy-card vy-card-nested">
                  {why.sponsored_note && <p className="vy-muted" style={{ marginBottom: 6 }}>{t("commercial:why.sponsored")}</p>}
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {why.signals.map((s) => <li key={s}>{signalLabel(t, s)}</li>)}
                  </ul>
                  {why.gap && (
                    <p className="vy-muted" style={{ marginTop: 6 }}>
                      {t(`ranking:gap.${why.gap}` as "gap.missingSkills", { skills: why.gap_skills })}
                    </p>
                  )}
                </div>
              )}

              {showReasons && (
                <div className="vy-stack" style={{ gap: 8 }}>
                  <p className="vy-muted" style={{ fontSize: 13 }}>{t("opportunities:detail.notInterestedPrompt")}</p>
                  <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
                    {Object.entries(NOT_INTERESTED_REASON_KEYS).map(([reason, key]) => (
                      <button
                        key={reason}
                        className="vy-chip"
                        style={{ cursor: "pointer" }}
                        disabled={busy}
                        onClick={() => props.onNotInterested(reason as NotInterestedReason)}
                      >
                        {t(`opportunities:detail.${key}` as "detail.notInterestedTooFar")}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Reading column, part 2 — fit, the role itself, the source, the
            person behind it, then a way to keep going. */}
        <div className="vy-detail-main">
          {opp.is_poster && opp.state === "draft" && (
            <div className="vy-card vy-stack">
              <h2 className="vy-card-title">{t("opportunities:detail.confirmTitle")}</h2>
              {opp.unconfirmed_fields.length === 0 ? (
                <p className="vy-muted">{t("opportunities:detail.allConfirmed")}</p>
              ) : (
                opp.unconfirmed_fields.map((f) => (
                  <div key={f} className="vy-row" style={{ justifyContent: "space-between" }}>
                    <span>
                      <span className="vy-badge vy-badge-member-provided">{t("opportunities:detail.unconfirmed")}</span> {f}
                    </span>
                    <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => props.onConfirmField(f)}>
                      {t("opportunities:detail.confirm")}
                    </button>
                  </div>
                ))
              )}
              <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onPublish}>
                {t("opportunities:detail.publish")}
              </button>
            </div>
          )}

          {hasFitSection && (
            <section className="vy-card vy-stack" style={{ gap: 12 }}>
              <h2 className="vy-card-title">{t(opp.is_poster ? "opportunities:detail.lookingForYours" : "opportunities:detail.lookingFor")}</h2>
              {/* Not just what they want: how the viewer measures up, skill
                  by skill. Upwork keeps this behind a paid tier; here it is
                  the plain answer to "am I a fit?". */}
              {opp.capability_match && (
                <p className={matchCount === opp.capability_match.length ? "vy-fit-line vy-fit-full" : "vy-fit-line"}>
                  {matchCount === opp.capability_match.length
                    ? t("opportunities:detail.fitAll")
                    : matchCount === 0
                      ? t("opportunities:detail.fitNone")
                      : t("opportunities:detail.fitSome", { have: matchCount, total: opp.capability_match.length })}
                </p>
              )}
              {opp.capability_labels.length > 0 && (
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
                  {/* The viewer's own skills lead the row. */}
                  {opp.capability_labels
                    .map((c, i) => ({ c, match: !!opp.capability_match?.[i] }))
                    .sort((a, b) => Number(b.match) - Number(a.match))
                    .map(({ c, match }) =>
                      match ? (
                        <span key={c} className="vy-chip vy-chip-match">
                          <span aria-hidden="true">✓</span> {c}
                          <span className="vy-visually-hidden"> ({t("opportunities:detail.youHaveSkill")})</span>
                        </span>
                      ) : (
                        <span key={c} className="vy-chip">{c}</span>
                      ),
                    )}
                </div>
              )}
              {opp.min_experience_years !== null && (
                <p style={{ fontWeight: 600 }}>{t("opportunities:detail.experience", { count: opp.min_experience_years })}</p>
              )}
              {opp.requirements && <p className="vy-muted" style={{ whiteSpace: "pre-line" }}>{opp.requirements}</p>}
            </section>
          )}

          {opp.description && (
            <section className="vy-card vy-stack" style={{ gap: 8 }}>
              <h2 className="vy-card-title">{t("opportunities:detail.aboutRole")}</h2>
              <p style={{ whiteSpace: "pre-line" }}>{opp.description}</p>
            </section>
          )}

          {isPublic && sourceLabel && (
            <section className="vy-card vy-stack" style={{ gap: 6 }}>
              <h2 className="vy-card-title">{t("opportunities:detail.sourceTitle")}</h2>
              <p>
                {t("opportunities:detail.sourceFound", {
                  source: sourceLabel,
                  name: opp.submitter_name ?? t("opportunities:detail.fromCommunity"),
                })}
              </p>
              <p className="vy-muted" style={{ fontSize: 13 }}>{t("opportunities:detail.sourceUnverified")}</p>
            </section>
          )}

          {!opp.is_poster && opp.poster && (
            <section className="vy-card vy-stack" style={{ gap: 8 }}>
              <h2 className="vy-card-title">{t("opportunities:detail.aboutPoster")}</h2>
              <p style={{ fontWeight: 600 }}>{opp.poster.name ?? opp.submitter_name}</p>
              <PaidOnTimeLine value={opp.poster_paid_on_time} />
              <BadgeList badges={opp.poster_badges} />
              {opp.poster.verified_listing_id && opp.poster.verified_listing_name && (
                <p>
                  <span className="vy-badge vy-badge-verified">✓</span>{" "}
                  {t("opportunities:detail.verifiedBusiness", { name: opp.poster.verified_listing_name })}
                  <br />
                  <a className="vy-tap-link" href={routes.listing(opp.poster.verified_listing_id)}>{t("opportunities:detail.viewBusiness")} →</a>
                </p>
              )}
              <p className="vy-muted" style={{ fontSize: 13 }}>
                {[
                  opp.poster.member_since ? t("opportunities:detail.memberSince", { date: fmtMonthYear(opp.poster.member_since) }) : null,
                  t("opportunities:detail.activeOpportunities", { count: opp.poster.active_opportunities }),
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {replyHabit && <p style={{ fontSize: 14 }}>{replyHabit}</p>}
            </section>
          )}

          {/* The poster doesn't only wait for responses: the profiles that
              already have the skills this asks for are right here. */}
          {opp.is_poster && ["active", "paused", "stale"].includes(opp.state) && props.matchingProfilesSlot}

          {opp.is_poster && opp.state !== "draft" && props.performanceSlot}

          {!opp.is_poster && similar.length > 0 && (
            <section className="vy-stack" style={{ gap: 12 }}>
              <h2 className="vy-section-title">{t("opportunities:detail.similarTitle")}</h2>
              <div className="vy-grid">
                {similar.map((s, i) => (
                  <OpportunityCard key={s.id} item={s} variant="similar" index={i} />
                ))}
              </div>
            </section>
          )}

          {viewerCanAct && props.reportSlot && <div id="report-opportunity">{props.reportSlot}</div>}
        </div>
      </div>

      {viewerCanAct && (
        <div className={actionOffscreen ? "vy-actionbar vy-actionbar-in" : "vy-actionbar"} inert={!actionOffscreen}>
          <button
            className="vy-btn vy-btn-secondary vy-actionbar-save"
            disabled={busy}
            onClick={props.onToggleSave}
            aria-label={opp.saved ? t("common:action.saved") : t("common:action.save")}
          >
            <Star size={20} strokeWidth={2} fill={opp.saved ? "currentColor" : "none"} aria-hidden="true" />
          </button>
          <div className="vy-actionbar-main">
            {props.primaryActionSlot ?? primaryAction}
            {props.precallSlot && <div className="vy-actionbar-precall">{props.precallSlot}</div>}
          </div>
        </div>
      )}
      {closing && (
        <CloseConfirmSheet
          opportunityId={id}
          busy={busy}
          onCancel={() => setClosing(false)}
          onConfirm={() => {
            setClosing(false);
            props.onClose();
          }}
        />
      )}
    </>
  );
}
