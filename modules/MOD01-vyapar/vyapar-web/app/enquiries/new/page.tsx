"use client";

// [TR022] Submit an Enquiry or Opportunity Response (FR22). One endpoint
// (`POST /v1/enquiries`) and one server-resolved action_type still stand —
// that part of the design was right. What was wrong: every one of the five
// typed actions ("Enquire Now"/"Apply"/"Submit a Proposal"/"Contact"/
// "Register") rendered through the SAME blank "type a message" textarea,
// which is a generic-chat pattern neither of this module's actual product
// references uses. Fixed per the product owner's 2026-09-17 correction and
// real research on how each reference app structures this step:
//   - Upwork's proposal step is a cover letter PLUS a separate rate/bid and
//     a timeline (support.upwork.com/hc/en-us/articles/211062998) — never
//     one bare box. "Propose" below has three real fields, composed into
//     one well-formatted message server expects (no schema change needed;
//     `message` stays 20-1000 chars, we just stop asking the member to
//     hand-format it themselves).
//   - WorkIndia's whole pitch is near-instant, low-typing application
//     (30-second registration, apply straight from your saved profile) —
//     "Apply" below shows the member's own capabilities as what the
//     employer will see and pre-fills a sensible note instead of demanding
//     a hand-typed paragraph; "Register" is similarly one-tap-first.
//   - "Enquire" keeps FR22 DEC-002's two sub-choices (Ask a question /
//     Request a quote) as real tap targets that seed the message, not a
//     blank field the member has to know to fill correctly.
// Traces to: FR22, TR022, FR22 DEC-002
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { AlertTriangle, BadgeCheck, Briefcase, ChevronLeft, HelpCircle, IndianRupee, Lock, Store, UserRound } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import FileUpload from "@/app/components/FileUpload";
import Screen from "@/app/components/Screen";
import ProfileSetup from "@/app/components/ProfileSetup";
import DisabledReason from "@/app/components/DisabledReason";
import { SkeletonGrid } from "@/app/components/States";
import { useRoutes } from "@/app/host/HostProvider";
import "@/app/styles/deals-2026.css";
import type { Me } from "@/lib/sdk";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";
import StructuredResponse, { isStructuredKind } from "@/app/components/respond/StructuredResponse";
import { useOpportunity } from "@/app/hooks/opportunities";

type Target =
  | { targetKind: "listing"; id: string; name: string; kind: string; locality: string; verificationState: string }
  | { targetKind: "opportunity"; id: string; name: string; type: string; typeActionLabel: string; location: string | null };

interface MyProfessionalListing {
  id: string;
  kind: string;
  capability_labels: string[];
  experience_years: number | null;
}

function ComposeInner() {
  const { t, i18n } = useTranslation(["enquiries", "common", "listings"]);
  const router = useRouter();
  const routes = useRoutes();
  const params = useSearchParams();
  const listingId = params.get("listing_id");
  const opportunityId = params.get("opportunity_id");

  const [target, setTarget] = useState<Target | null>(null);
  const [myListing, setMyListing] = useState<MyProfessionalListing | null>(null);
  const [subChoice, setSubChoice] = useState<"ask_question" | "request_quote" | null>(null);
  const [message, setMessage] = useState("");
  const [rate, setRate] = useState("");
  const [timeline, setTimeline] = useState("");
  const [note, setNote] = useState("");
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [rateType, setRateType] = useState<"fixed" | "hourly">("fixed");
  const [error, setError] = useState<string | null>(null);
  const [duplicateEnquiryId, setDuplicateEnquiryId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  // [Owner, 2026-09-22] no profile of either kind → the setup block replaces
  // the form (the API refuses the send too; this is the way forward).
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    api.get<Me>("/v1/members/me").then(setMe).catch(() => setMe(null));
  }, [i18n.language]);

  useEffect(() => {
    (async () => {
      if (listingId) {
        const l = await api.get<{ id: string; name: string; kind: string; locality: string; verification_state: string }>(`/v1/listings/${listingId}`);
        setTarget({ targetKind: "listing", id: l.id, name: l.name, kind: l.kind, locality: l.locality, verificationState: l.verification_state });
      } else if (opportunityId) {
        const o = await api.get<{ id: string; title: string; type: string; type_action_label: string; location: string | null }>(
          `/v1/opportunities/${opportunityId}`
        );
        setTarget({ targetKind: "opportunity", id: o.id, name: o.title, type: o.type, typeActionLabel: o.type_action_label, location: o.location });
        if (o.type_action_label === "apply") {
          const mine = await api.get<MyProfessionalListing[]>("/v1/listings/mine").catch(() => []);
          setMyListing(mine.find((x) => x.kind === "professional") ?? null);
        }
      }
    })().catch(() => setTarget(null));
  }, [listingId, opportunityId]);

  // The one action word this compose step resolves down to, purely for
  // choosing which structured UI to render — the server independently
  // re-resolves the real action_type from the target, this is never trusted.
  // [Bug fix] `type_action_label` values are the real i18n keys from
  // TYPE_ACTION_LABEL in opportunities.py ("apply"/"submitProposal"/
  // "enquireNow"/"contact"/"register"), not the shorthand this file
  // originally guessed at — matching against the wrong strings meant every
  // structured UI silently failed to render for freelance/local-service/
  // partnership opportunities, leaving only the bare title + Send button.
  const actionLabel: "enquire" | "apply" | "propose" | "register" | "contact" =
    target?.targetKind === "opportunity"
      ? target.typeActionLabel === "apply"
        ? "apply"
        : target.typeActionLabel === "submitProposal"
        ? "propose"
        : target.typeActionLabel === "register"
        ? "register"
        : "enquire"
      : "enquire";

  function finalMessage(): string {
    if (actionLabel === "propose") {
      const parts = [];
      // [Critique agent finding, fixed here] Upwork's real proposal screen
      // distinguishes Fixed-price from Hourly bids, not just a free-text
      // "rate" string — the rate label now carries that distinction.
      if (rate.trim()) {
        const rateLabel = rateType === "hourly" ? t("enquiries:compose.rateLabelHourly") : t("enquiries:compose.rateLabelFixed");
        parts.push(`${rateLabel}: ${rate.trim()}`);
      }
      if (timeline.trim()) parts.push(`${t("enquiries:compose.timelineLabel")}: ${timeline.trim()}`);
      const header = parts.length ? `${parts.join(" · ")}\n\n` : "";
      return `${header}${message}`.trim();
    }
    if (actionLabel === "apply") return note.trim() || t("enquiries:compose.applyDefaultNote");
    if (actionLabel === "register") return note.trim() || t("enquiries:compose.registerDefaultNote");
    return message.trim();
  }

  const readyToSend =
    actionLabel === "apply" || actionLabel === "register"
      ? finalMessage().length >= 20
      : actionLabel === "propose"
      ? message.trim().length >= 20
      : message.trim().length >= 20 && (target?.targetKind !== "listing" || subChoice !== null || true);

  async function send() {
    setSending(true);
    setError(null);
    setDuplicateEnquiryId(null);
    try {
      const enquiry = await api.post<{ id: string }>("/v1/enquiries", {
        listing_id: listingId || undefined,
        opportunity_id: opportunityId || undefined,
        message: finalMessage(),
        sub_choice: subChoice ?? undefined,
        attachment_url: attachmentUrl.trim() || undefined,
      });
      router.push(routes.enquiry(enquiry.id));
    } catch (e) {
      // [Critique agent finding, fixed here] the daily-cap (429) and
      // duplicate-open (409) responses were never parsed into UX12's own
      // specified copy — a 409's `detail` is a {message, existing_enquiry_id}
      // OBJECT, and `String(e.detail)` on an object literally renders
      // "[object Object]" to the member. Now each status is handled per
      // UX12's exact wireframe text, and the duplicate case gets a real
      // "Open it" button to the existing thread, not just an error string.
      if (e instanceof ApiError && e.status === 409 && e.detail && typeof e.detail === "object") {
        const d = e.detail as { existing_enquiry_id?: string | null };
        setDuplicateEnquiryId(d.existing_enquiry_id ?? null);
        setError(t("enquiries:compose.alreadyOpenWithName", { name: target?.name ?? "" }));
      } else if (e instanceof ApiError && e.status === 429) {
        setError(t("enquiries:compose.dailyCapReached", { cap: 20 }));
      } else if (e instanceof ApiError && e.status === 400) {
        setError(t("enquiries:compose.targetNotActive"));
      } else {
        setError(e instanceof ApiError && typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"));
      }
    } finally {
      setSending(false);
    }
  }

  if (!target) {
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <div className="vy-skeleton" style={{ height: 40, width: 280, maxWidth: "70%" }} aria-hidden="true" />
          <SkeletonGrid count={2} grid={false} />
        </div>
      </Screen>
    );
  }

  if (me?.profiles && !me.profiles.complete) {
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("enquiries:compose.toTitle", { name: target.name })}</h1>
          </div>
          <ProfileSetup profiles={me.profiles} required />
        </div>
      </Screen>
    );
  }

  // [IMP39] Desktop: the form on the left and a live preview of the exact
  // message the other person receives (finalMessage(), the same text send()
  // posts) on the right.
  const outgoing = finalMessage();
  const title =
    actionLabel === "apply"
      ? t("enquiries:compose.applyTitle")
      : actionLabel === "propose"
        ? t("enquiries:compose.proposeTitle")
        : actionLabel === "register"
          ? t("enquiries:compose.registerTitle")
          : t("enquiries:compose.title");
  const subtitle =
    actionLabel === "apply"
      ? t("enquiries:compose.applyHelp")
      : actionLabel === "propose"
        ? t("enquiries:compose.proposeHelp")
        : actionLabel === "register"
          ? t("enquiries:compose.registerHelp")
          : t("enquiries:compose.enquireHelp");
  const tooShort = !readyToSend && !sending;
  const verified = target.targetKind === "listing" && target.verificationState === "verified";
  const TargetIcon = target.targetKind === "listing" ? (target.kind === "business" ? Store : UserRound) : Briefcase;
  const counter = (value: string) => (
    <span className="vy-dl-counter" aria-live="polite">
      <span className={value.trim().length >= 20 ? undefined : "vy-error"}>{t("enquiries:compose.counter", { count: value.length, max: 1000, min: 20 })}</span>
    </span>
  );

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href={target.targetKind === "listing" ? routes.listing(target.id) : routes.opportunity(target.id)} transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {target.name}
        </Link>
        <div className="vy-dl-head">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <div className="vy-compose">
          <div className="vy-compose-main">
            <div className="vy-dl-page" style={{ gap: "var(--space-4)" }}>
              {/* UX12's context card: who you are writing to, one line, one trust label */}
              <div className="vy-dl-sec vy-dl-target">
                <span className={`vy-dl-tile ${target.targetKind === "listing" ? "vy-dl-tile-teal" : "vy-dl-tile-brand"}`} aria-hidden="true">
                  <TargetIcon size={20} strokeWidth={1.75} />
                </span>
                <div className="vy-dl-target-body">
                  <strong>{target.name}</strong>
                  <span>
                    {target.targetKind === "listing"
                      ? t("enquiries:compose.contextSummary", {
                          kind: target.kind === "business" ? t("listings:mine.kindBusiness") : t("listings:mine.kindProfessional"),
                          locality: target.locality,
                        })
                      : target.location ?? t(`enquiries:kind.${target.type}` as "kind.employment", { defaultValue: target.type })}
                  </span>
                  {target.targetKind === "listing" && (
                    <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                      <span className="vy-dl-state" data-tone={verified ? "done" : undefined}>
                        {verified && <BadgeCheck size={13} strokeWidth={2} aria-hidden="true" />}
                        {verified ? t("enquiries:compose.trustVerified") : t("enquiries:compose.trustUnverified")}
                      </span>
                    </span>
                  )}
                </div>
              </div>

              {/* --- Ask: a question or a price, then the details --- */}
              {actionLabel === "enquire" && (
                <div className="vy-dl-sec">
                  <div className="vy-dl-choice-row" role="radiogroup" aria-label={t("enquiries:compose.whatYouNeed")}>
                    <button
                      type="button"
                      role="radio"
                      aria-checked={subChoice === "ask_question"}
                      className="vy-dl-choice"
                      onClick={() => {
                        setSubChoice("ask_question");
                        if (!message) setMessage(t("enquiries:compose.enquireQuestionTemplate", { name: target.name }));
                      }}
                    >
                      <HelpCircle size={20} strokeWidth={1.75} aria-hidden="true" />
                      {t("enquiries:compose.askQuestion")}
                    </button>
                    <button
                      type="button"
                      role="radio"
                      aria-checked={subChoice === "request_quote"}
                      className="vy-dl-choice"
                      onClick={() => {
                        setSubChoice("request_quote");
                        if (!message) setMessage(t("enquiries:compose.enquireQuoteTemplate", { name: target.name }));
                      }}
                    >
                      <IndianRupee size={20} strokeWidth={1.75} aria-hidden="true" />
                      {t("enquiries:compose.requestQuote")}
                    </button>
                  </div>
                  <label className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.messageLabel")}</span>
                    <textarea className="vy-textarea" rows={6} maxLength={1000} value={message} onChange={(e) => setMessage(e.target.value)} placeholder={t("enquiries:compose.placeholder")} />
                  </label>
                  {counter(message)}
                </div>
              )}

              {/* --- Apply (public-source job): your work profile does the talking --- */}
              {actionLabel === "apply" && (
                <div className="vy-dl-sec">
                  <div className="vy-dl-panel">
                    <span className="vy-label">{t("enquiries:compose.yourProfile")}</span>
                    {myListing && myListing.capability_labels.length > 0 ? (
                      <div className="vy-dl-tags">
                        {myListing.capability_labels.map((c) => (
                          <span key={c} className="vy-chip">{c}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="vy-dl-hint">{t("enquiries:compose.noExperienceListed")}</p>
                    )}
                    {myListing?.experience_years != null && <p className="vy-dl-hint">{t("enquiries:compose.yourExperience", { years: myListing.experience_years })}</p>}
                  </div>
                  <label className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.noteLabel")}</span>
                    <textarea className="vy-textarea" rows={4} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("enquiries:compose.notePlaceholder")} />
                  </label>
                </div>
              )}

              {/* --- Propose (non-structured project): price, timeline, note --- */}
              {actionLabel === "propose" && (
                <div className="vy-dl-sec">
                  <div className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.rateLabel")}</span>
                    <div className="vy-dl-choice-row" role="radiogroup" aria-label={t("enquiries:compose.rateLabel")}>
                      <button type="button" role="radio" aria-checked={rateType === "fixed"} className="vy-dl-choice" onClick={() => setRateType("fixed")}>
                        {t("enquiries:compose.rateLabelFixed")}
                      </button>
                      <button type="button" role="radio" aria-checked={rateType === "hourly"} className="vy-dl-choice" onClick={() => setRateType("hourly")}>
                        {t("enquiries:compose.rateLabelHourly")}
                      </button>
                    </div>
                    <input className="vy-input" value={rate} onChange={(e) => setRate(e.target.value)} placeholder={t("enquiries:compose.ratePlaceholder")} aria-label={t("enquiries:compose.rateLabel")} />
                  </div>
                  <label className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.timelineLabel")}</span>
                    <input className="vy-input" value={timeline} onChange={(e) => setTimeline(e.target.value)} placeholder={t("enquiries:compose.timelinePlaceholder")} />
                  </label>
                  <label className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.coverLetterLabel")}</span>
                    <textarea className="vy-textarea" rows={6} maxLength={1000} value={message} onChange={(e) => setMessage(e.target.value)} placeholder={t("enquiries:compose.coverLetterPlaceholder")} />
                  </label>
                  {counter(message)}
                  <div className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.attachmentLabel")}</span>
                    <FileUpload value={attachmentUrl} onChange={setAttachmentUrl} />
                  </div>
                </div>
              )}

              {/* --- Interested: one tap, note optional --- */}
              {actionLabel === "register" && (
                <div className="vy-dl-sec">
                  <label className="vy-field">
                    <span className="vy-label">{t("enquiries:compose.noteLabel")}</span>
                    <textarea className="vy-textarea" rows={3} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("enquiries:compose.notePlaceholder")} />
                  </label>
                </div>
              )}

              {error && (
                <div className="vy-dl-notice" data-tone="bad" role="alert">
                  <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
                  <div className="vy-dl-row-body">
                    <span>{error}</span>
                    {duplicateEnquiryId && (
                      <a className="vy-btn vy-btn-secondary vy-dl-btn-sm" style={{ alignSelf: "flex-start", marginTop: 6 }} href={routes.enquiry(duplicateEnquiryId)}>
                        {t("enquiries:compose.openIt")}
                      </a>
                    )}
                  </div>
                </div>
              )}

              <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
                <button className="vy-btn vy-btn-primary" aria-describedby={tooShort ? "compose-why" : undefined} disabled={!readyToSend || sending} onClick={send}>
                  {sending ? t("common:state.saving") : t("enquiries:compose.send")}
                </button>
                <DisabledReason id="compose-why" show={tooShort}>
                  {actionLabel === "enquire" && subChoice === null && !message.trim() ? t("enquiries:compose.chooseFirst") : t("enquiries:compose.messageTooShort")}
                </DisabledReason>
                <p className="vy-dl-safety">
                  <Lock size={13} strokeWidth={2} aria-hidden="true" />
                  <span>{t("enquiries:compose.privacyLine")}</span>
                </p>
              </div>
            </div>
          </div>
          <ComposerPreview caption={t("enquiries:compose.previewCaption", { name: target.name })} guide={[t("enquiries:compose.guide1"), t("enquiries:compose.guide2"), t("enquiries:compose.guide3")]}>
            <PreviewCard title={target.name} body={outgoing} bodyEmpty={t("enquiries:compose.previewEmpty")} chips={attachmentUrl ? [attachmentUrl.split("/").pop() ?? ""] : undefined} />
          </ComposerPreview>
        </div>
      </div>
    </Screen>
  );
}

// [FE1 — 2026-09-28] Jobs, freelance projects and local services now each
// have their own structured composer (one-tap apply, proposal, quote —
// app/components/respond/StructuredResponse.tsx). Listings and the other
// opportunity types keep the composer above, unchanged.
function Router() {
  const params = useSearchParams();
  const opportunityId = params.get("opportunity_id");
  const opportunity = useOpportunity(opportunityId ?? "", { enabled: !!opportunityId });
  if (opportunityId && !opportunity.data && !opportunity.error) {
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <div className="vy-skeleton" style={{ height: 40, width: 280, maxWidth: "70%" }} aria-hidden="true" />
          <SkeletonGrid count={2} grid={false} />
        </div>
      </Screen>
    );
  }
  if (opportunity.data && isStructuredKind(opportunity.data.type) && opportunity.data.source_segment !== "public") {
    return <StructuredResponse opportunity={opportunity.data} />;
  }
  return <ComposeInner />;
}

export default function NewEnquiryPage() {
  return (
    <Suspense fallback={null}>
      <Router />
    </Suspense>
  );
}
