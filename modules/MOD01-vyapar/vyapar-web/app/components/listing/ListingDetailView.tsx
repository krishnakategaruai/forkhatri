"use client";

// [IMP38 — Refactor C] Listing (business / professional profile) detail,
// presentational half — the markup moved verbatim out of
// app/listings/[id]/page.tsx (see that file for the FR02/03/05/07 and
// IMP33 desktop-layout reasoning). Props in, callbacks out, no fetching;
// blocks that load their own data (reviews, similar profiles, the report
// sheet, the verification panel, the performance report) arrive as slots.
// Form input state (the phone and code being typed) and the trust sheet
// toggle are presentation, so they stay here.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { Listing, ListingContact } from "@/lib/sdk";
import { VerificationBadge, TrustContextSheet } from "@/app/components/Verification";
import { ReputationLine } from "@/app/components/Reputation";
import SponsoredBadge from "@/app/components/SponsoredBadge";
import { Morph } from "@/app/components/Screen";
import { useRoutes } from "@/app/host/HostProvider";

export const LISTING_STATE_KEY: Record<string, string> = {
  draft: "stateDraft",
  submitted: "stateSubmitted",
  active_unverified: "stateActiveUnverified",
  active_verified: "stateActiveVerified",
  suspended: "stateSuspended",
  archived: "stateArchived",
};

// [FR03 acceptance criterion: "Safety-check failure shows the reason
// category (not the wordlist)"] — a reason CATEGORY must still read as
// plain language to the member, not the internal snake_case code
// (`prohibited_content`/`spam_pattern`) the automated check writes to
// `state_reason`. Operator-entered suspend reasons are already free text
// typed by a person (in whatever language they typed it), so they pass
// through unchanged; only the fixed automated-check codes are i18n keys.
const REASON_KEY: Record<string, string> = {
  prohibited_content: "reasonProhibitedContent",
  spam_pattern: "reasonSpamPattern",
};

export interface ListingDetailActions {
  onToggleSave: () => void;
  onShare: () => void;
  onAttachCredential: () => void;
  onSubmit: () => void;
  onArchive: () => void;
  onRequestOtp: (phone: string) => void;
  onVerifyOtp: (code: string) => void;
  onUpdateContact: (index: number, disclosure: ListingContact["disclosure"]) => void;
  onToggleDiscoverable: (discoverable: boolean) => void;
  onUpdateIntent: (patch: { capability_visible?: boolean; intent_visible?: boolean; intent_state?: string | null }) => void;
}

export interface ListingDetailViewProps extends ListingDetailActions {
  listing: Listing;
  busy: boolean;
  notice: string | null;
  /** Owner OTP flow: a code has been sent. */
  otpRequested: boolean;
  /** Development only: the code the stand-in SMS provider "sent". */
  devCode: string | null;
  reviewsSlot?: React.ReactNode;
  similarSlot?: React.ReactNode;
  reportSlot?: React.ReactNode;
  verificationSlot?: React.ReactNode;
  performanceSlot?: React.ReactNode;
}

export default function ListingDetailView(props: ListingDetailViewProps) {
  const { listing, busy, notice, otpRequested, devCode } = props;
  const id = listing.id;
  const { t } = useTranslation(["listings", "common", "partnerships", "commercial", "workspace", "discover"]);
  const routes = useRoutes();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  // [Critique agent finding, fixed here — UX07 Trust context sheet]
  const [showTrustSheet, setShowTrustSheet] = useState(false);

  function humanizeReason(reason: string): string {
    return REASON_KEY[reason] ? t(`listings:detail.${REASON_KEY[reason]}` as "detail.reasonProhibitedContent") : reason;
  }

  return (
    <>
      <div>
        <div className="vy-row" style={{ justifyContent: "space-between" }}>
          {/* [IMP33] Shared-element target: the card the person tapped on
              Businesses morphs into this heading. Same name as the
              `morphName` LivingCard passes there. */}
          <Morph name={`listing-${id}`}>
            <h1>{listing.name}</h1>
          </Morph>
        </div>
        <div className="vy-row" style={{ flexWrap: "wrap", marginTop: 8 }}>
          <span className="vy-badge vy-badge-member-provided">{t(`listings:mine.${LISTING_STATE_KEY[listing.state] ?? "stateDraft"}` as "mine.stateDraft")}</span>
          {/* [FR10] One shared badge for all eight states — the previous
              else-branch rendered "Verified" on UNverified listings. */}
          <VerificationBadge listing={listing} onOpenTrustSheet={() => setShowTrustSheet(true)} />
          {listing.sponsored && <SponsoredBadge />}
          {listing.contact_verified && <span className="vy-badge vy-badge-verified">✓ {t("listings:mine.contactVerified")}</span>}
        </div>
        {/* [FR28] reputation line — counts only, kept apart from the verification badge */}
        <ReputationLine rep={listing.reputation} />
        {listing.state_reason && <p className="vy-muted" style={{ marginTop: 6 }}>{t("listings:detail.reason", { reason: humanizeReason(listing.state_reason) })}</p>}
      </div>

      <div className="vy-detail">
      <div className="vy-detail-main">
      <div className="vy-card">
        <p><strong>{listing.locality}</strong> · {listing.category_labels.concat(listing.capability_labels).join(", ") || t("listings:detail.noCategoriesYet")}</p>
        {listing.description && <p style={{ marginTop: 8 }}>{listing.description}</p>}
        {listing.verification_state !== "verified" && (
          <p className="vy-muted" style={{ marginTop: 8 }}>
            {t("listings:detail.unverifiedNotice")}
          </p>
        )}
      </div>

      {/* [FR06/TR006] Read-only VerifiedCredential reference — never
          MOD04 Counsel data, never evidence, just {claim, issuer, date}.
          "Attach" is only offered to the owner of a professional listing;
          the dev-only stand-in provider decides whether one exists. */}
      {listing.credential_ref && (
        <div className="vy-badge vy-badge-verified" style={{ display: "block", padding: "10px 14px" }}>
          ✓ {t("listings:detail.credentialVerifiedBy", { claim: listing.credential_ref.claim })}
        </div>
      )}
      {listing.is_owner && listing.kind === "professional" && !listing.credential_ref && (
        <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={props.onAttachCredential}>
          {t("listings:detail.attachCredential")}
        </button>
      )}

      {notice && <p className="vy-error">{notice}</p>}
      </div>

      {/* [IMP33] The sticky action column (desktop ≥900px). On phones this
          is simply the next block in the single-column flow, in exactly
          the position it already occupied. */}
      <div className="vy-detail-aside vy-detail-aside-full">

      {/* [FR16/FR22] Viewer-facing trust context + action, for anyone who
          isn't the owner. Enquire Now routes to the real compose flow;
          Save is real (member_listing.saved_at); Share needs no backend
          call — native share sheet where supported, clipboard otherwise. */}
      {!listing.is_owner && (
        // [IMP33] This action set is what moves to the sticky right
        // column on desktop (see `.vy-detail-aside`). `vy-card-actions`
        // stacks the buttons full-width at ≥900px.
        <div className="vy-card vy-stack vy-card-actions">
          <a className="vy-btn vy-btn-primary" href={routes.enquireListing(id)} style={{ textDecoration: "none", display: "inline-block", textAlign: "center" }}>
            {t("listings:detail.enquireNow")}
          </a>
          <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={props.onToggleSave}>
            {listing.saved ? `★ ${t("common:action.saved")}` : `☆ ${t("common:action.save")}`}
          </button>
          <button className="vy-btn vy-btn-ghost" onClick={props.onShare}>
            {t("common:action.share")}
          </button>
          {/* [FR25] hidden entirely when the owner has opted out of partnership requests */}
          {listing.partnership_open && (
            <a className="vy-btn vy-btn-ghost" href={routes.proposePartnership(id)} style={{ textDecoration: "none", display: "inline-block" }}>
              {t("partnerships:propose")}
            </a>
          )}
        </div>
      )}
      {/* [IMP33] The owner's equivalent of the viewer action card: FR03
          lifecycle + FR30 boost + FR33/FR34 workspace, in the same sticky
          column so they are never buried below reviews on desktop. */}
      {listing.is_owner && (
        <div className="vy-card vy-stack vy-card-actions">
          {listing.state === "draft" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onSubmit}>
              {t("listings:detail.submit")}
            </button>
          )}
          {listing.state.startsWith("active") && (
            <a className="vy-btn vy-btn-secondary" href={routes.boost("listing", id)} style={{ textDecoration: "none" }}>
              {t("commercial:action.boost")}
            </a>
          )}
          <a className="vy-btn vy-btn-ghost" href={routes.workspace(id)} style={{ textDecoration: "none" }}>
            {t("workspace:open")}
          </a>
          {listing.state !== "archived" && (
            <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={props.onArchive}>
              {t("listings:detail.archive")}
            </button>
          )}
        </div>
      )}
      </div>

      <div className="vy-detail-main">
      {/* [FR28/FR29] reviews from real interactions; the subject can dispute in place */}
      {props.reviewsSlot}
      {/* A person comparing providers keeps going instead of dead-ending. */}
      {!listing.is_owner && props.similarSlot}
      {/* [FR39] Report in place. */}
      {!listing.is_owner && props.reportSlot && <div id="report-listing">{props.reportSlot}</div>}

      {listing.is_owner && (
        <>
          {/* FR08/FR09/FR10 — request or reconfirm verification */}
          {props.verificationSlot}

          {/* FR07 — listing-contact OTP verification, required before submit */}
          {!listing.contact_verified && (
            // [Design-enhancement pass, DESIGN-ENHANCEMENT.md] this panel
            // sits inside the listing's own page flow, not as the screen's
            // primary subject — steps to --surface-nested per the spec's
            // named example.
            <div className="vy-card vy-card-nested vy-stack">
              <h2 className="vy-card-title">{t("listings:detail.verifyPhoneTitle")}</h2>
              <p>{t("listings:detail.verifyPhoneHelp")}</p>
              {!otpRequested ? (
                <div className="vy-row">
                  <input className="vy-input" placeholder={t("listings:new.phonePlaceholder")} value={phone} onChange={(e) => setPhone(e.target.value)} />
                  <button className="vy-btn vy-btn-primary" disabled={!phone || busy} onClick={() => props.onRequestOtp(phone)}>
                    {t("listings:detail.sendCode")}
                  </button>
                </div>
              ) : (
                <div className="vy-row">
                  <input className="vy-input" placeholder={t("listings:detail.codePlaceholder")} value={code} onChange={(e) => setCode(e.target.value)} />
                  <button className="vy-btn vy-btn-primary" disabled={code.length !== 6 || busy} onClick={() => props.onVerifyOtp(code)}>
                    {t("listings:detail.verify")}
                  </button>
                </div>
              )}
              {devCode && <p className="vy-muted">{t("listings:detail.devCodeNotice", { code: devCode })}</p>}
            </div>
          )}

          {/* FR02 — per-channel contact disclosure + discoverability */}
          <div className="vy-card vy-card-nested vy-stack">
            <h2 className="vy-card-title">{t("listings:detail.contactVisibilityTitle")}</h2>
            <label className="vy-row" style={{ justifyContent: "space-between" }}>
              <span>{t("listings:detail.discoverableInSearch")}</span>
              <input type="checkbox" checked={listing.discoverable} onChange={(e) => props.onToggleDiscoverable(e.target.checked)} />
            </label>
            {listing.contacts.map((c, i) => (
              <div key={c.channel} className="vy-row" style={{ justifyContent: "space-between" }}>
                <span className="vy-muted">{c.channel}: {c.value}</span>
                <select className="vy-select" style={{ width: "auto" }} value={c.disclosure} onChange={(e) => props.onUpdateContact(i, e.target.value as ListingContact["disclosure"])}>
                  <option value="public">{t("listings:detail.disclosurePublic")}</option>
                  <option value="after_accept">{t("listings:detail.disclosureAfterAccept")}</option>
                  <option value="hidden">{t("listings:detail.disclosureHidden")}</option>
                </select>
              </div>
            ))}
            {listing.contacts.length === 0 && <p className="vy-muted">{t("listings:detail.noContactsYet")}</p>}
          </div>

          {/* FR05 — capability visibility independent of seeking visibility (professional only) */}
          {listing.kind === "professional" && (
            <div className="vy-card vy-card-nested vy-stack">
              <h2 className="vy-card-title">{t("listings:detail.capabilityVisibilityTitle")}</h2>
              <p className="vy-muted">{t("listings:detail.capabilityVisibilityHelp")}</p>
              <label className="vy-row" style={{ justifyContent: "space-between" }}>
                <span>{t("listings:detail.showCapabilitiesPublicly")}</span>
                <input type="checkbox" checked={listing.capability_visible} onChange={(e) => props.onUpdateIntent({ capability_visible: e.target.checked })} />
              </label>
              <div className="vy-field">
                <label className="vy-label">{t("listings:detail.currentIntentLabel")}</label>
                <select className="vy-select" value={listing.intent_state ?? ""} onChange={(e) => props.onUpdateIntent({ intent_state: e.target.value || null })}>
                  <option value="">{t("listings:detail.intentNotSet")}</option>
                  <option value="looking">{t("listings:detail.intentLooking")}</option>
                  <option value="open">{t("listings:detail.intentOpen")}</option>
                  <option value="curious">{t("listings:detail.intentCurious")}</option>
                  <option value="not_interested">{t("listings:detail.intentNotInterested")}</option>
                </select>
              </div>
              <label className="vy-row" style={{ justifyContent: "space-between" }}>
                <span>{t("listings:detail.makeSeekingVisible")}</span>
                <input type="checkbox" checked={listing.intent_visible} onChange={(e) => props.onUpdateIntent({ intent_visible: e.target.checked })} />
              </label>
            </div>
          )}

          {/* [FR32] counts for the last 30 days, inline for the owner */}
          {listing.state.startsWith("active") && props.performanceSlot}
        </>
      )}
      </div>
      </div>
      {showTrustSheet && (
        <TrustContextSheet
          listing={listing}
          contactVerified={listing.contact_verified}
          onClose={() => setShowTrustSheet(false)}
          onReport={
            !listing.is_owner
              ? () => {
                  setShowTrustSheet(false);
                  document.getElementById("report-listing")?.scrollIntoView({ behavior: "smooth" });
                }
              : undefined
          }
        />
      )}
    </>
  );
}
