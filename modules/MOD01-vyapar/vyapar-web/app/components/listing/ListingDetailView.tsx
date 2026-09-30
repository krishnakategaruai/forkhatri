"use client";

// [IMP38 — Refactor C] Listing (business / work profile) detail,
// presentational half — props in, callbacks out, no fetching; blocks that
// load their own data (reviews, similar profiles, the report sheet, the
// verification panel, the performance report) arrive as slots. Form input
// state (the phone and code being typed) and the trust sheet toggle are
// presentation, so they stay here. See app/listings/[id]/page.tsx for the
// FR02/03/05/07 and IMP33 desktop-layout reasoning.
//
// [Design language 2026-09-29] The header carries the profile's kind tile
// beside the name, badges wrap under it; the owner's management panels are
// cards with a title and one line, full-row switches instead of 16px
// checkboxes, chips instead of native <select>s, the phone with +91 inside
// the field, and every word per GLOSSARY.md ("Ask for a price" on a
// business, "Contact" on a work profile; "skills", never capabilities;
// "Looking for work / Open to work / Just looking"). Data flow unchanged.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BadgeCheck, MapPin } from "lucide-react";
import type { Listing, ListingContact } from "@/lib/sdk";
import { VerificationBadge, TrustContextSheet } from "@/app/components/Verification";
import { ReputationLine } from "@/app/components/Reputation";
import SponsoredBadge from "@/app/components/SponsoredBadge";
import DisabledReason from "@/app/components/DisabledReason";
import { Morph } from "@/app/components/Screen";
import { BadgeList } from "@/app/components/trust/Badges";
import { useRoutes } from "@/app/host/HostProvider";
import { KindTile } from "@/app/components/account/AccountProfileCard";
import SwitchRow from "@/app/components/account/SwitchRow";
// [Trust pack] profession rules, council registrations, paid on time, restrictions
import { NoPromotionNote, ProfessionInfo, ProfessionOwnerNote, pricesBlocked, promotionBlocked, restrictedProfession, reviewsBlocked } from "@/app/components/trust/Profession";
import { CouncilBadges } from "@/app/components/trust/Council";
import { PaidOnTimeLine } from "@/app/components/trust/PaidOnTime";
import RestrictionCard from "@/app/components/trust/RestrictionCard";
import "@/app/styles/account-2026.css";

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
// plain language to the member, not the internal snake_case code.
const REASON_KEY: Record<string, string> = {
  prohibited_content: "reasonProhibitedContent",
  spam_pattern: "reasonSpamPattern",
};

const DISCLOSURES: ListingContact["disclosure"][] = ["public", "after_accept", "hidden"];
const INTENTS: { value: string; key: string }[] = [
  { value: "", key: "intentNotSet" },
  { value: "looking", key: "intentLooking" },
  { value: "open", key: "intentOpen" },
  { value: "curious", key: "intentCurious" },
  { value: "not_interested", key: "intentNotInterested" },
];

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
  /** [FE2] service packages: the compare view for visitors, the editor for the owner */
  packagesSlot?: React.ReactNode;
  /** [FE2] owner only: this listing's calling hours (override of the account settings) */
  contactPrefsSlot?: React.ReactNode;
  /** [Trust pack §5] owner only, work profile: council registrations */
  credentialsSlot?: React.ReactNode;
}

export default function ListingDetailView(props: ListingDetailViewProps) {
  const { listing, busy, notice, otpRequested, devCode } = props;
  const id = listing.id;
  const { t } = useTranslation(["listings", "common", "partnerships", "commercial", "workspace", "discover", "contact"]);
  const routes = useRoutes();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  // [Critique agent finding, fixed here — UX07 Trust context sheet]
  const [showTrustSheet, setShowTrustSheet] = useState(false);
  const business = listing.kind === "business";
  // A category and a skill can share a label ("Legal advice"): show it once.
  const skills = [...new Set(listing.category_labels.concat(listing.capability_labels))];
  // [Trust pack §4] A council that forbids advertising (advocates, architects):
  // no reviews, badges, prices, packages, promotion or "Sponsored" — and a
  // neutral "Contact". The API already strips these for other readers; the
  // screen simply never draws them, for the owner too (promote → a note).
  const profession = restrictedProfession(listing.profession);
  const noReviews = reviewsBlocked(listing.profession);
  const noPrices = pricesBlocked(listing.profession);
  const noPromotion = promotionBlocked(listing.profession);
  const councilChecked = listing.verification_document === "credential" && (listing.council_badges ?? []).some((b) => b.status === "verified");
  const badges = noReviews ? (listing.badges ?? []).filter((b) => b.key === "verified_business") : listing.badges;

  function humanizeReason(reason: string): string {
    return REASON_KEY[reason] ? t(`listings:detail.${REASON_KEY[reason]}` as "detail.reasonProhibitedContent") : reason;
  }

  return (
    <>
      <header className="vy-acct-detail-head">
        <KindTile kind={listing.kind} size={48} />
        {/* [IMP33] Shared-element target: the card the person tapped on
            Businesses morphs into this heading. */}
        <Morph name={`listing-${id}`}>
          <h1>{listing.name}</h1>
        </Morph>
        <div className="vy-acct-detail-badges">
          <span className="vy-badge vy-badge-member-provided">{t(`listings:mine.${LISTING_STATE_KEY[listing.state] ?? "stateDraft"}` as "mine.stateDraft")}</span>
          {/* [FR10] One shared badge for all eight states. */}
          {/* [Trust pack §5] a checked council entry says it better: don't repeat it as a second badge */}
          {!councilChecked && <VerificationBadge listing={listing} onOpenTrustSheet={() => setShowTrustSheet(true)} />}
          {listing.sponsored && !profession && <SponsoredBadge />}
          {listing.contact_verified && (
            <span className="vy-badge vy-badge-verified">
              <BadgeCheck size={14} strokeWidth={2.25} aria-hidden="true" /> {t("listings:mine.contactVerified")}
            </span>
          )}
        </div>
      </header>
      {/* [Trust pack §3] the owner sees why the profile is restricted, and can appeal */}
      {listing.is_owner && listing.restriction && <RestrictionCard item={listing.restriction} compact />}
      <div className="vy-stack" style={{ gap: 6 }}>
        {listing.headline && <p style={{ color: "var(--text-secondary)" }}>{listing.headline}</p>}
        {/* [Trust pack §5] council register entries under the name */}
        <CouncilBadges badges={listing.council_badges} />
        {/* [FR28] reputation line — counts only, kept apart from the verification badge */}
        {!noReviews && <ReputationLine rep={listing.reputation} />}
        {/* [Trust pack §2] "Paid on time: 2 of 3", only once three people answered */}
        <PaidOnTimeLine value={listing.paid_on_time} />
        {/* [FE2] earned, count-based badges — never a score */}
        <BadgeList badges={badges} />
        {listing.state_reason && <p className="vy-acct-hint" style={{ marginTop: 6 }}>{t("listings:detail.reason", { reason: humanizeReason(listing.state_reason) })}</p>}
      </div>

      <div className="vy-detail">
        <div className="vy-detail-main">
          <section className="vy-card vy-acct-card" aria-label={t("listings:detail.aboutTitle")}>
            <p className="vy-acct-meta">
              <span>
                <MapPin size={15} strokeWidth={2} aria-hidden="true" />
                {listing.locality}
              </span>
            </p>
            {skills.length > 0 ? (
              <div className="vy-acct-chips">
                {skills.map((s) => (
                  <span key={s} className="vy-acct-chip">
                    <span>{s}</span>
                  </span>
                ))}
              </div>
            ) : (
              <p className="vy-acct-hint">{t("listings:detail.noCategoriesYet")}</p>
            )}
            {listing.description && <p>{listing.description}</p>}
            {listing.verification_state !== "verified" && <p className="vy-acct-hint">{t("listings:detail.unverifiedNotice")}</p>}
          </section>

          {/* [FR06/TR006] Read-only VerifiedCredential reference — never
              MOD04 Counsel data, never evidence, just {claim, issuer, date}. */}
          {listing.credential_ref && (
            <div className="vy-acct-note" role="note">
              <BadgeCheck size={18} strokeWidth={2} aria-hidden="true" style={{ color: "var(--verified-text)" }} />
              <span>{t("listings:detail.credentialVerifiedBy", { claim: listing.credential_ref.claim })}</span>
            </div>
          )}
          {listing.is_owner && listing.kind === "professional" && !listing.credential_ref && (
            <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={props.onAttachCredential}>
              {t("listings:detail.attachCredential")}
            </button>
          )}

          {profession && (listing.is_owner ? <ProfessionOwnerNote profession={profession} /> : <ProfessionInfo profession={profession} />)}
          {notice && <p className="vy-error" role="status">{notice}</p>}
          {!noPrices && props.packagesSlot}
        </div>

        {/* [IMP33] The sticky action column (desktop ≥900px). On phones this
            is the next block in the single-column flow. */}
        <div className="vy-detail-aside vy-detail-aside-full">
          {/* [FR16/FR22] Viewer-facing action, for anyone who isn't the owner. */}
          {!listing.is_owner && (
            <div className="vy-card vy-stack vy-card-actions">
              <a className="vy-btn vy-btn-primary" href={routes.enquireListing(id)} style={{ textDecoration: "none" }}>
                {profession?.contact_label ?? (business ? t("listings:detail.enquireNow") : t("listings:detail.contactProfessional"))}
              </a>
              <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={props.onToggleSave}>
                {listing.saved ? `★ ${t("common:action.saved")}` : `☆ ${t("common:action.save")}`}
              </button>
              <button className="vy-btn vy-btn-ghost" onClick={props.onShare}>
                {t("common:action.share")}
              </button>
              {/* [FR25] hidden entirely when the owner has opted out of partnership requests */}
              {listing.partnership_open && (
                <a className="vy-btn vy-btn-ghost" href={routes.proposePartnership(id)} style={{ textDecoration: "none" }}>
                  {t("partnerships:propose")}
                </a>
              )}
            </div>
          )}
          {/* [IMP33] The owner's equivalent: FR03 lifecycle + FR30 promote + FR33/FR34 workspace. */}
          {listing.is_owner && (
            <div className="vy-card vy-stack vy-card-actions">
              {listing.state === "draft" && (
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onSubmit}>
                  {t("listings:detail.submit")}
                </button>
              )}
              {listing.state.startsWith("active") && !noPromotion && (
                <a className="vy-btn vy-btn-secondary" href={routes.boost("listing", id)} style={{ textDecoration: "none" }}>
                  {t("commercial:action.boost")}
                </a>
              )}
              {noPromotion && listing.profession && <NoPromotionNote profession={listing.profession} />}
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
          {!noReviews && props.reviewsSlot}
          {/* A person comparing providers keeps going instead of dead-ending. */}
          {!listing.is_owner && props.similarSlot}
          {/* [FR39] Report in place. */}
          {!listing.is_owner && props.reportSlot && <div id="report-listing">{props.reportSlot}</div>}

          {listing.is_owner && (
            <>
              <h2 className="vy-section-title" style={{ marginTop: 8 }}>{t("listings:detail.manageTitle")}</h2>

              {/* FR08/FR09/FR10 — request or reconfirm verification */}
              {props.verificationSlot}

              {/* [Trust pack §5] council registrations (work profile) */}
              {listing.kind === "professional" && props.credentialsSlot}

              {/* FR07 — listing-contact OTP verification, required before submit */}
              {!listing.contact_verified && (
                <section className="vy-card vy-acct-card" aria-labelledby="otp-title">
                  <div className="vy-acct-card-head" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
                    <h2 id="otp-title">{t("listings:detail.verifyPhoneTitle")}</h2>
                    <p>{t("listings:detail.verifyPhoneHelp")}</p>
                  </div>
                  {!otpRequested ? (
                    <div className="vy-acct-form" style={{ gap: 10 }}>
                      <div className="vy-acct-prefixed">
                        <span aria-hidden="true">+91</span>
                        <input type="tel" inputMode="numeric" aria-label={t("listings:new.phoneLabel")} placeholder={t("listings:new.phonePlaceholder")} value={phone} onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, ""))} />
                      </div>
                      <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} aria-describedby={!phone ? "why-phone" : undefined} disabled={!phone || busy} onClick={() => props.onRequestOtp(`+91${phone.replace(/\D/g, "")}`)}>
                        {t("listings:detail.sendCode")}
                      </button>
                      <DisabledReason id="why-phone" show={!phone}>{t("common:disabled.phone")}</DisabledReason>
                    </div>
                  ) : (
                    <div className="vy-acct-form" style={{ gap: 10 }}>
                      <input className="vy-input" inputMode="numeric" autoComplete="one-time-code" maxLength={6} placeholder={t("listings:detail.codePlaceholder")} aria-label={t("listings:detail.codePlaceholder")} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
                      <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} aria-describedby={code.length !== 6 ? "why-code" : undefined} disabled={code.length !== 6 || busy} onClick={() => props.onVerifyOtp(code)}>
                        {t("listings:detail.verify")}
                      </button>
                      <DisabledReason id="why-code" show={code.length !== 6}>{t("common:disabled.code")}</DisabledReason>
                    </div>
                  )}
                  {devCode && <p className="vy-acct-hint">{t("listings:detail.devCodeNotice", { code: devCode })}</p>}
                </section>
              )}

              {/* FR02 — per-channel contact disclosure + discoverability */}
              <section className="vy-card vy-acct-card" aria-labelledby="vis-title">
                <div className="vy-acct-card-head" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
                  <h2 id="vis-title">{t("listings:detail.contactVisibilityTitle")}</h2>
                  <p>{t("listings:detail.contactVisibilityHelp")}</p>
                </div>
                <div className="vy-acct-card-body" style={{ gap: 0 }}>
                  <SwitchRow id={`disc-${id}`} label={t("listings:detail.discoverableInSearch")} checked={listing.discoverable} disabled={busy} onChange={(v) => props.onToggleDiscoverable(v)} />
                  {listing.contacts.map((c, i) => (
                    <div key={c.channel} className="vy-acct-contact-row">
                      <span>
                        {t(`contact:channel.${c.channel}` as "channel.phone", { defaultValue: c.channel })} <small>{c.value}</small>
                      </span>
                      <div className="vy-acct-inline-choices" role="group" aria-label={t(`contact:channel.${c.channel}` as "channel.phone", { defaultValue: c.channel })}>
                        {DISCLOSURES.map((d) => (
                          <button key={d} type="button" className="vy-chip" aria-pressed={c.disclosure === d} disabled={busy} onClick={() => props.onUpdateContact(i, d)}>
                            {t(`listings:detail.disclosure${d === "public" ? "Public" : d === "after_accept" ? "AfterAccept" : "Hidden"}` as "detail.disclosurePublic")}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  {listing.contacts.length === 0 && <p className="vy-acct-hint" style={{ paddingTop: 8 }}>{t("listings:detail.noContactsYet")}</p>}
                </div>
              </section>

              {props.contactPrefsSlot}

              {/* FR05 — skills visibility independent of looking-for-work visibility (work profile only) */}
              {listing.kind === "professional" && (
                <section className="vy-card vy-acct-card" aria-labelledby="intent-title">
                  <div className="vy-acct-card-head" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
                    <h2 id="intent-title">{t("listings:detail.capabilityVisibilityTitle")}</h2>
                    <p>{t("listings:detail.capabilityVisibilityHelp")}</p>
                  </div>
                  <div className="vy-acct-card-body" style={{ gap: 0 }}>
                    <SwitchRow id={`cap-${id}`} label={t("listings:detail.showCapabilitiesPublicly")} checked={listing.capability_visible} disabled={busy} onChange={(v) => props.onUpdateIntent({ capability_visible: v })} />
                    <div className="vy-acct-switch" style={{ gridTemplateColumns: "minmax(0, 1fr)", cursor: "default" }}>
                      <span className="vy-acct-switch-text">
                        <span className="vy-acct-switch-label">{t("listings:detail.currentIntentLabel")}</span>
                      </span>
                      <div className="vy-acct-inline-choices" role="group" aria-label={t("listings:detail.currentIntentLabel")} style={{ marginTop: 6 }}>
                        {INTENTS.map((o) => (
                          <button key={o.value} type="button" className="vy-chip" aria-pressed={(listing.intent_state ?? "") === o.value} disabled={busy} onClick={() => props.onUpdateIntent({ intent_state: o.value || null })}>
                            {t(`listings:detail.${o.key}` as "detail.intentNotSet")}
                          </button>
                        ))}
                      </div>
                    </div>
                    <SwitchRow id={`seek-${id}`} label={t("listings:detail.makeSeekingVisible")} checked={listing.intent_visible} disabled={busy} onChange={(v) => props.onUpdateIntent({ intent_visible: v })} />
                  </div>
                </section>
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
