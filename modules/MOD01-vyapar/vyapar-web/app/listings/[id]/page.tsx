"use client";

// [TR002/TR003/TR005/TR007] Listing manage screen — combines four FRs on
// one screen because that is how an owner actually experiences their own
// listing (04-ui.md's "everything needed on one screen" pattern, applied
// here to owner management rather than a viewer's read):
//  - FR02: per-channel contact disclosure + discoverable toggle
//  - FR03: lifecycle actions (submit / archive), state + reason display
//  - FR05: (professional only) capability vs. seeking-visibility, kept as
//    two visibly separate controls, never combined into one switch
//  - FR07: listing-contact OTP verification gate before submit
// Approach: one GET on mount, optimistic-ish refetch after each mutating
// action (no separate confirmation dialog per the "no unnecessary
// intermediate screens" standing preference) — every action re-fetches the
// canonical listing state from the server rather than guessing the new state
// client-side, so the UI can never drift from what RLS/the state machine
// actually allowed.
// [Product-owner i18n rule] Converted to useTranslation(); backend error
// `detail` strings are already localized server-side (X-Vyapar-Language),
// rendered as-is — only this file's own JSX text/labels needed keys.
// Traces to: FR02, FR03, FR05, FR07, TR002, TR003, TR005, TR007
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { VerificationBadge, VerificationPanel } from "@/app/components/Verification";
import ReportSheet from "@/app/components/ReportSheet";
import { ReputationLine, ReviewList, type Reputation } from "@/app/components/Reputation";
import SponsoredBadge from "@/app/components/SponsoredBadge";
import PerformanceReport from "@/app/components/PerformanceReport";

interface Contact {
  channel: string;
  value: string;
  disclosure: "public" | "after_accept" | "hidden";
}

interface Listing {
  id: string;
  kind: string;
  name: string;
  headline: string | null;
  description: string | null;
  locality: string;
  categories: string[];
  capabilities: string[];
  unmapped_labels: string[];
  category_labels: string[];
  capability_labels: string[];
  primary_phone: string | null;
  contact_verified: boolean;
  discoverable: boolean;
  enquiry_pref: string;
  state: string;
  state_reason: string | null;
  verification_state: string;
  intent_state: string | null;
  intent_visible: boolean;
  capability_visible: boolean;
  is_owner: boolean;
  owner_id: string;
  saved: boolean;
  contacts: Contact[];
  credential_ref: { id: string; claim: string; issuer: string; last_checked: string } | null;
  verification_document: string | null;
  verification_claim: string | null;
  verified_at: string | null;
  verification_expires_at: string | null;
  partnership_open: boolean;
  reputation: Reputation | null;
  sponsored: boolean;
}

const STATE_KEY: Record<string, string> = {
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

export default function ListingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["listings", "common", "partnerships", "commercial", "workspace"]);
  const [listing, setListing] = useState<Listing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  function humanizeReason(reason: string): string {
    return REASON_KEY[reason] ? t(`listings:detail.${REASON_KEY[reason]}` as "detail.reasonProhibitedContent") : reason;
  }

  async function refresh() {
    try {
      const l = await api.get<Listing>(`/v1/listings/${id}`);
      setListing(l);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.notFound"));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error) {
    return (
      <main className="vy-shell">
        <h1>{t("common:state.notFound")}</h1>
        <p>{error}</p>
      </main>
    );
  }
  if (!listing) return <main className="vy-shell"><p>{t("common:state.loading")}</p></main>;

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function updateContact(index: number, disclosure: Contact["disclosure"]) {
    const next = listing!.contacts.map((c, i) => (i === index ? { ...c, disclosure } : c));
    await act(() => api.patch(`/v1/listings/${id}/contacts`, { contacts: next }));
  }

  async function toggleDiscoverable(discoverable: boolean, confirm = false) {
    try {
      await act(() => api.patch(`/v1/listings/${id}/visibility`, { discoverable, confirm_no_reach: confirm }));
    } catch {
      /* handled in act() */
    }
  }

  return (
    <main className="vy-shell">
      <div>
        <div className="vy-row" style={{ justifyContent: "space-between" }}>
          <h1>{listing.name}</h1>
        </div>
        <div className="vy-row" style={{ flexWrap: "wrap", marginTop: 8 }}>
          <span className="vy-badge vy-badge-member-provided">{t(`listings:mine.${STATE_KEY[listing.state] ?? "stateDraft"}` as "mine.stateDraft")}</span>
          {/* [FR10] One shared badge for all eight states — the previous
              else-branch rendered "Verified" on UNverified listings. */}
          <VerificationBadge listing={listing} />
          {listing.sponsored && <SponsoredBadge />}
          {listing.contact_verified && <span className="vy-badge vy-badge-verified">✓ {t("listings:mine.contactVerified")}</span>}
        </div>
        {/* [FR28] reputation line — counts only, kept apart from the verification badge */}
        <ReputationLine rep={listing.reputation} />
        {listing.state_reason && <p className="vy-muted" style={{ marginTop: 6 }}>{t("listings:detail.reason", { reason: humanizeReason(listing.state_reason) })}</p>}
      </div>

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
        <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => act(() => api.post(`/v1/listings/${id}/credential-ref/attach`))}>
          {t("listings:detail.attachCredential")}
        </button>
      )}

      {notice && <p className="vy-error">{notice}</p>}

      {/* [FR16/FR22] Viewer-facing trust context + action, for anyone who
          isn't the owner. Enquire Now now routes to the real compose flow
          (FR22, built this session — previously disabled since Enquiries
          didn't exist yet). Save is real (member_listing.saved_at). Share
          is real and needs no backend call — native share sheet where
          supported, clipboard copy otherwise. Report (FR39) is deferred —
          see listings.py's own comment for why. */}
      {!listing.is_owner && (
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <a className="vy-btn vy-btn-primary" href={`/enquiries/new?listing_id=${id}`} style={{ textDecoration: "none", display: "inline-block" }}>
            {t("listings:detail.enquireNow")}
          </a>
          <button
            className="vy-btn vy-btn-secondary"
            disabled={busy}
            onClick={() => act(() => (listing.saved ? api.delete(`/v1/listings/${id}/save`) : api.post(`/v1/listings/${id}/save`)))}
          >
            {listing.saved ? `★ ${t("common:action.saved")}` : `☆ ${t("common:action.save")}`}
          </button>
          <button
            className="vy-btn vy-btn-ghost"
            onClick={async () => {
              const url = typeof window !== "undefined" ? window.location.href : "";
              const shareData = { title: listing.name, text: `${listing.name} on Vyapar`, url };
              if (typeof navigator !== "undefined" && navigator.share) {
                try {
                  await navigator.share(shareData);
                } catch {
                  /* member cancelled the native share sheet — not an error */
                }
              } else if (typeof navigator !== "undefined" && navigator.clipboard) {
                await navigator.clipboard.writeText(url);
                setNotice(t("common:action.linkCopied"));
              }
            }}
          >
            {t("common:action.share")}
          </button>
          {/* [FR25] hidden entirely when the owner has opted out of partnership requests */}
          {listing.partnership_open && (
            <a className="vy-btn vy-btn-ghost" href={`/partnerships/new?listing_id=${id}`} style={{ textDecoration: "none", display: "inline-block" }}>
              {t("partnerships:propose")}
            </a>
          )}
        </div>
      )}
      {/* [FR28/FR29] reviews from real interactions; the subject can dispute in place */}
      <ReviewList listingId={id} />
      {/* [FR39] Report in place — the FR16 action deferred in IMP10 until
          FR39's moderation cases existed. */}
      {!listing.is_owner && <ReportSheet objectKind="listing" objectId={id} blockMemberId={listing.owner_id} />}

      {listing.is_owner && (
        <>
          {/* FR08/FR09/FR10 — request or reconfirm verification */}
          <VerificationPanel listingId={id} kind={listing.kind} verificationState={listing.verification_state} onChanged={refresh} />

          {/* FR07 — listing-contact OTP verification, required before submit */}
          {!listing.contact_verified && (
            <div className="vy-card vy-stack">
              <h2 style={{ fontSize: 16 }}>{t("listings:detail.verifyPhoneTitle")}</h2>
              <p>{t("listings:detail.verifyPhoneHelp")}</p>
              {!otpRequested ? (
                <div className="vy-row">
                  <input className="vy-input" placeholder={t("listings:new.phonePlaceholder")} value={phone} onChange={(e) => setPhone(e.target.value)} />
                  <button
                    className="vy-btn vy-btn-primary"
                    disabled={!phone || busy}
                    onClick={() =>
                      act(async () => {
                        const r = await api.post<{ dev_code: string }>(`/v1/listings/${id}/otp/request`, { phone });
                        setOtpRequested(true);
                        setDevCode(r.dev_code ?? null);
                      })
                    }
                  >
                    {t("listings:detail.sendCode")}
                  </button>
                </div>
              ) : (
                <div className="vy-row">
                  <input className="vy-input" placeholder={t("listings:detail.codePlaceholder")} value={code} onChange={(e) => setCode(e.target.value)} />
                  <button
                    className="vy-btn vy-btn-primary"
                    disabled={code.length !== 6 || busy}
                    onClick={() => act(() => api.post(`/v1/listings/${id}/otp/verify`, { code }))}
                  >
                    {t("listings:detail.verify")}
                  </button>
                </div>
              )}
              {devCode && <p className="vy-muted">{t("listings:detail.devCodeNotice", { code: devCode })}</p>}
            </div>
          )}

          {/* FR02 — per-channel contact disclosure + discoverability */}
          <div className="vy-card vy-stack">
            <h2 style={{ fontSize: 16 }}>{t("listings:detail.contactVisibilityTitle")}</h2>
            <label className="vy-row" style={{ justifyContent: "space-between" }}>
              <span>{t("listings:detail.discoverableInSearch")}</span>
              <input type="checkbox" checked={listing.discoverable} onChange={(e) => toggleDiscoverable(e.target.checked)} />
            </label>
            {listing.contacts.map((c, i) => (
              <div key={c.channel} className="vy-row" style={{ justifyContent: "space-between" }}>
                <span className="vy-muted">{c.channel}: {c.value}</span>
                <select className="vy-select" style={{ width: "auto" }} value={c.disclosure} onChange={(e) => updateContact(i, e.target.value as Contact["disclosure"])}>
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
            <div className="vy-card vy-stack">
              <h2 style={{ fontSize: 16 }}>{t("listings:detail.capabilityVisibilityTitle")}</h2>
              <p className="vy-muted">{t("listings:detail.capabilityVisibilityHelp")}</p>
              <label className="vy-row" style={{ justifyContent: "space-between" }}>
                <span>{t("listings:detail.showCapabilitiesPublicly")}</span>
                <input
                  type="checkbox"
                  checked={listing.capability_visible}
                  onChange={(e) => act(() => api.patch(`/v1/listings/${id}/intent`, { capability_visible: e.target.checked }))}
                />
              </label>
              <div className="vy-field">
                <label className="vy-label">{t("listings:detail.currentIntentLabel")}</label>
                <select
                  className="vy-select"
                  value={listing.intent_state ?? ""}
                  onChange={(e) => act(() => api.patch(`/v1/listings/${id}/intent`, { intent_state: e.target.value || null }))}
                >
                  <option value="">{t("listings:detail.intentNotSet")}</option>
                  <option value="looking">{t("listings:detail.intentLooking")}</option>
                  <option value="open">{t("listings:detail.intentOpen")}</option>
                  <option value="curious">{t("listings:detail.intentCurious")}</option>
                  <option value="not_interested">{t("listings:detail.intentNotInterested")}</option>
                </select>
              </div>
              <label className="vy-row" style={{ justifyContent: "space-between" }}>
                <span>{t("listings:detail.makeSeekingVisible")}</span>
                <input
                  type="checkbox"
                  checked={listing.intent_visible}
                  onChange={(e) => act(() => api.patch(`/v1/listings/${id}/intent`, { intent_visible: e.target.checked }))}
                />
              </label>
            </div>
          )}

          {/* [FR32] counts for the last 30 days, inline for the owner */}
          {listing.state.startsWith("active") && <PerformanceReport targetKind="listing" targetId={id} />}

          {/* FR03 — lifecycle actions; [FR30] Boost (the boost screen explains "verify first" when needed) */}
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {listing.state.startsWith("active") && (
              <a className="vy-btn vy-btn-secondary" href={`/boost/listing/${id}`} style={{ textDecoration: "none" }}>
                {t("commercial:action.boost")}
              </a>
            )}
            {/* [FR33/FR34] plan, team and campaigns for this business */}
            <a className="vy-btn vy-btn-ghost" href={`/workspace/${id}`} style={{ textDecoration: "none" }}>
              {t("workspace:open")}
            </a>
            {listing.state === "draft" && (
              <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/listings/${id}/submit`))}>
                {t("listings:detail.submit")}
              </button>
            )}
            {listing.state !== "archived" && (
              <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act(() => api.post(`/v1/listings/${id}/archive`))}>
                {t("listings:detail.archive")}
              </button>
            )}
          </div>
        </>
      )}
    </main>
  );
}
