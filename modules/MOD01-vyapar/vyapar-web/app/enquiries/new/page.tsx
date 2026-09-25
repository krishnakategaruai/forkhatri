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
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import FileUpload from "@/app/components/FileUpload";
import Screen from "@/app/components/Screen";
import ProfileSetup from "@/app/components/ProfileSetup";
import type { Me } from "@/lib/sdk";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";

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
      router.push(`/enquiries/${enquiry.id}`);
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
      <Screen>
        <p className="vy-muted">{t("enquiries:compose.loading")}</p>
      </Screen>
    );
  }

  if (me?.profiles && !me.profiles.complete) {
    return (
      <Screen width="wide">
        <h1>{t("enquiries:compose.toTitle", { name: target.name })}</h1>
        <ProfileSetup profiles={me.profiles} required />
      </Screen>
    );
  }

  // [IMP39] Desktop: the compose form on the left, and on the right a live
  // preview of the exact message the provider will receive (finalMessage()
  // — the same composed text `send()` posts, including the rate/timeline
  // header for proposals and the default note for one-tap applications).
  const outgoing = finalMessage();

  return (
    <Screen width="wide">
      <h1>
        {actionLabel === "apply" && t("enquiries:compose.applyTitle")}
        {actionLabel === "propose" && t("enquiries:compose.proposeTitle")}
        {actionLabel === "register" && t("enquiries:compose.registerTitle")}
        {/* [Bug fix] sub-choice buttons (Ask a question / Request a quote,
            FR22 DEC-002) apply to every "Enquire Now" target, not only
            listings — a local_service Opportunity uses the identical
            action word and identical pattern, per 03-ux.md. */}
        {actionLabel === "enquire" && t("enquiries:compose.title")}
      </h1>
      <div className="vy-compose">
      <div className="vy-compose-main">
      {/* [Critique agent finding, fixed here] UX12's own wireframe names a
          "Context card: target name/title, one-line summary, trust label"
          inside Compose enquiry — this was missing entirely; only a plain
          "To {{name}}" line existed. */}
      <div className="vy-card vy-stack" style={{ gap: 4 }}>
        <strong>{target.name}</strong>
        <span className="vy-muted" style={{ fontSize: 13 }}>
          {target.targetKind === "listing"
            ? t("enquiries:compose.contextSummary", { kind: target.kind === "business" ? t("listings:mine.kindBusiness") : t("listings:mine.kindProfessional"), locality: target.locality })
            : target.location ?? t("enquiries:compose.contextSummary", { kind: target.type, locality: "" })}
        </span>
        {target.targetKind === "listing" && (
          <span className="vy-badge" style={{ alignSelf: "flex-start" }}>
            {target.verificationState === "verified" ? t("enquiries:compose.trustVerified") : t("enquiries:compose.trustUnverified")}
          </span>
        )}
      </div>

      {/* --- Enquire: WorkIndia-style fast structured ask, not a blank box --- */}
      {actionLabel === "enquire" && (
        <div className="vy-stack">
          <p>{t("enquiries:compose.enquireHelp")}</p>
          {(
            <div className="vy-row" style={{ gap: 8 }}>
              <button
                className={`vy-btn ${subChoice === "ask_question" ? "vy-btn-primary" : "vy-btn-secondary"}`}
                onClick={() => {
                  setSubChoice("ask_question");
                  if (!message) setMessage(t("enquiries:compose.enquireQuestionTemplate", { name: target.name }));
                }}
              >
                {t("enquiries:compose.askQuestion")}
              </button>
              <button
                className={`vy-btn ${subChoice === "request_quote" ? "vy-btn-primary" : "vy-btn-secondary"}`}
                onClick={() => {
                  setSubChoice("request_quote");
                  if (!message) setMessage(t("enquiries:compose.enquireQuoteTemplate", { name: target.name }));
                }}
              >
                {t("enquiries:compose.requestQuote")}
              </button>
            </div>
          )}
          <textarea
            className="vy-textarea"
            rows={6}
            maxLength={1000}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t("enquiries:compose.placeholder")}
          />
          {/* [Critique agent finding, fixed here] UX12 names a live counter
              "0 / 1000 · at least 20" — there was none. */}
          <span className={message.trim().length >= 20 ? "vy-muted" : "vy-error"} style={{ fontSize: 12 }}>
            {t("enquiries:compose.counter", { count: message.length, max: 1000, min: 20 })}
          </span>
        </div>
      )}

      {/* --- Apply: WorkIndia-style — your profile does the talking --- */}
      {actionLabel === "apply" && (
        <div className="vy-stack">
          <p className="vy-muted">{t("enquiries:compose.applyHelp")}</p>
          <div className="vy-card vy-stack" style={{ gap: 6 }}>
            <strong style={{ fontSize: 13, color: "var(--text-secondary)" }}>{t("enquiries:compose.yourProfile")}</strong>
            {myListing && myListing.capability_labels.length > 0 ? (
              <p>{myListing.capability_labels.join(", ")}</p>
            ) : (
              <p className="vy-muted">{t("enquiries:compose.noExperienceListed")}</p>
            )}
            {myListing?.experience_years != null && (
              <p className="vy-muted">{t("enquiries:compose.yourExperience", { years: myListing.experience_years })}</p>
            )}
          </div>
          <label className="vy-label">{t("enquiries:compose.noteLabel")}</label>
          <textarea
            className="vy-textarea"
            rows={4}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("enquiries:compose.notePlaceholder")}
          />
        </div>
      )}

      {/* --- Propose: Upwork-style — cover letter + rate + timeline --- */}
      {actionLabel === "propose" && (
        <div className="vy-stack">
          <p className="vy-muted">{t("enquiries:compose.proposeHelp")}</p>
          {/* [Critique agent finding, fixed here] Upwork's real proposal
              screen foregrounds a Fixed/Hourly rate-TYPE choice, not just a
              bare rate string — added as a real two-way toggle. */}
          <div className="vy-row" role="radiogroup" aria-label={t("enquiries:compose.rateLabel")}>
            <button
              type="button"
              role="radio"
              aria-checked={rateType === "fixed"}
              className={`vy-btn ${rateType === "fixed" ? "vy-btn-primary" : "vy-btn-secondary"}`}
              onClick={() => setRateType("fixed")}
            >
              {t("enquiries:compose.rateLabelFixed")}
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={rateType === "hourly"}
              className={`vy-btn ${rateType === "hourly" ? "vy-btn-primary" : "vy-btn-secondary"}`}
              onClick={() => setRateType("hourly")}
            >
              {t("enquiries:compose.rateLabelHourly")}
            </button>
          </div>
          <input className="vy-input" value={rate} onChange={(e) => setRate(e.target.value)} placeholder={t("enquiries:compose.ratePlaceholder")} />
          <label className="vy-label">{t("enquiries:compose.timelineLabel")}</label>
          <input className="vy-input" value={timeline} onChange={(e) => setTimeline(e.target.value)} placeholder={t("enquiries:compose.timelinePlaceholder")} />
          <label className="vy-label">{t("enquiries:compose.coverLetterLabel")}</label>
          <textarea
            className="vy-textarea"
            rows={6}
            maxLength={1000}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t("enquiries:compose.coverLetterPlaceholder")}
          />
          <span className={message.trim().length >= 20 ? "vy-muted" : "vy-error"} style={{ fontSize: 12 }}>
            {t("enquiries:compose.counter", { count: message.length, max: 1000, min: 20 })}
          </span>
          {/* [Critique agent finding, fixed here] FR22 allows one attachment
              and Upwork's real screen foregrounds work samples — there was
              no attachment control anywhere on this step. */}
          <label className="vy-label">{t("enquiries:compose.attachmentLabel")}</label>
          <FileUpload value={attachmentUrl} onChange={setAttachmentUrl} />
        </div>
      )}

      {/* --- Register: one tap, note optional --- */}
      {actionLabel === "register" && (
        <div className="vy-stack">
          <p className="vy-muted">{t("enquiries:compose.registerHelp")}</p>
          <label className="vy-label">{t("enquiries:compose.noteLabel")}</label>
          <textarea
            className="vy-textarea"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("enquiries:compose.notePlaceholder")}
          />
        </div>
      )}

      {/* [Real bug found live via third critique pass, fixed here] the
          409/429/400 error-parsing logic in `send()` already correctly
          populated `error` and `duplicateEnquiryId` — but no JSX anywhere
          in this file ever read `duplicateEnquiryId` or rendered a link to
          the existing thread, so a member hitting the single most common
          error on this screen (already having an open enquiry) saw only a
          plain error sentence with nowhere to go, per UX12's own wireframe
          which explicitly names "Open it" as a button, not just text. */}
      {error && (
        <div className="vy-card vy-stack" style={{ gap: 8 }}>
          <p className="vy-error">{error}</p>
          {duplicateEnquiryId && (
            <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} href={`/enquiries/${duplicateEnquiryId}`}>
              {t("enquiries:compose.openIt")}
            </a>
          )}
        </div>
      )}
      {/* [Same critique finding] UX12's own compose wireframe names this
          exact safety line inside Compose enquiry itself (not only in the
          post-accept contact card) — `compose.privacyLine` existed in the
          locale files since the earlier composer rewrite but was never
          actually rendered anywhere on this screen. */}
      <p className="vy-muted" style={{ fontSize: 12 }}>🔒 {t("enquiries:compose.privacyLine")}</p>
      <button className="vy-btn vy-btn-primary vy-submit" disabled={!readyToSend || sending} onClick={send}>
        {sending ? t("common:state.saving") : t("enquiries:compose.send")}
      </button>
      </div>
      <ComposerPreview
        caption={t("enquiries:compose.previewCaption", { name: target.name })}
        guide={[t("enquiries:compose.guide1"), t("enquiries:compose.guide2"), t("enquiries:compose.guide3")]}
      >
        <PreviewCard
          title={target.name}
          body={outgoing}
          bodyEmpty={t("enquiries:compose.previewEmpty")}
          chips={attachmentUrl ? [attachmentUrl.split("/").pop() ?? ""] : undefined}
        />
      </ComposerPreview>
      </div>
    </Screen>
  );
}

export default function NewEnquiryPage() {
  return (
    <Suspense fallback={null}>
      <ComposeInner />
    </Suspense>
  );
}
