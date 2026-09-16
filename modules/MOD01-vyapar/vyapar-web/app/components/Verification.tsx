"use client";

// [TR008/TR009/TR010] Verification UI shared by every listing surface.
// VerificationBadge: the ONE render path for FR10's eight verification
// states — each a plain-language label with claim scope + date, never a
// bare "Verified". Only verified/expiring use the green trust tint; every
// other state uses the neutral tag, so verification, Sponsored and
// member-provided stay visually distinct (04-ui.md's separation rule).
// FR09 credentials read "Credential reviewed: <name>" — never "verified
// professional". VerificationPanel: owner-side submission — exactly one
// document per request, four FR08 business options (no Aadhaar anywhere,
// FR08 DEC-002) plus the FR09 credential option for professional listings.
// Fewer actions: while a request is pending the form is hidden and a
// single status line is shown instead of a second, duplicate form.
// Traces to: FR08, FR09, FR10, TR008, TR009, TR010
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

export const DOC_KEY: Record<string, string> = {
  gst: "typeGst",
  udyam: "typeUdyam",
  pan: "typePan",
  shops_est: "typeShopsEst",
  credential: "typeCredential",
};

export interface VerificationFields {
  verification_state: string;
  verification_document: string | null;
  verification_claim: string | null;
  verified_at: string | null;
  verification_expires_at: string | null;
}

export function VerificationBadge({ listing }: { listing: VerificationFields }) {
  const { t, i18n } = useTranslation("verification");
  const fmt = (d: string | null) => (d ? new Date(d).toLocaleDateString(i18n.language) : "");
  const isCredential = listing.verification_document === "credential";
  const scope = isCredential
    ? listing.verification_claim ?? ""
    : listing.verification_document
      ? t(DOC_KEY[listing.verification_document] as "typeGst")
      : "";
  const state = listing.verification_state;
  if (state === "verified") {
    const key = isCredential ? "label.credentialReviewed" : "label.verified";
    return <span className="vy-badge vy-badge-verified">✓ {t(key as "label.verified", { scope, date: fmt(listing.verified_at) })}</span>;
  }
  if (state === "expiring") {
    return <span className="vy-badge vy-badge-verified">✓ {t("label.expiring", { scope, date: fmt(listing.verification_expires_at) })}</span>;
  }
  return <span className="vy-badge vy-badge-member-provided">{t(`label.${state}` as "label.not_started")}</span>;
}

interface RecordOut {
  id: string;
  document_type: string;
  state: string;
  reason_code: string | null;
}

export function VerificationPanel({
  listingId,
  kind,
  verificationState,
  onChanged,
}: {
  listingId: string;
  kind: string;
  verificationState: string;
  onChanged: () => void;
}) {
  const { t } = useTranslation(["verification", "common"]);
  const [records, setRecords] = useState<RecordOut[] | null>(null);
  const options = kind === "professional" ? ["credential", "gst", "udyam", "pan", "shops_est"] : ["gst", "udyam", "pan", "shops_est"];
  const [docType, setDocType] = useState(options[0]);
  const [identifier, setIdentifier] = useState("");
  const [credentialName, setCredentialName] = useState("");
  const [issuer, setIssuer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setRecords(await api.get<RecordOut[]>(`/v1/listings/${listingId}/verification`));
  }

  useEffect(() => {
    load().catch(() => setRecords([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  if (records === null) return null;
  const latest = records[0];
  if (latest?.state === "pending") {
    return <p className="vy-muted">{t("verification:pendingNotice")}</p>;
  }
  if (verificationState === "verified") return null;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/v1/listings/${listingId}/verification`, {
        document_type: docType,
        identifier: docType === "credential" ? undefined : identifier,
        credential_name: docType === "credential" ? credentialName : undefined,
        issuer: docType === "credential" ? issuer : undefined,
      });
      await load();
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  const ready = docType === "credential" ? credentialName && issuer : identifier;

  return (
    <div className="vy-card vy-stack">
      <h2 style={{ fontSize: 16 }}>{t("verification:title")}</h2>
      {verificationState === "expiring" || verificationState === "expired" ? (
        <p className="vy-muted">{t("verification:reconfirmNotice")}</p>
      ) : (
        <p className="vy-muted">{t("verification:help")}</p>
      )}
      {latest?.state === "needs_clearer_copy" && <p className="vy-error">{t("verification:stateNeedsClearerCopy")}</p>}
      {latest?.state === "rejected" && (
        <p className="vy-error">
          {t("verification:stateRejected")}
          {latest.reason_code ? ` — ${t("verification:reasonLabel", { reason: latest.reason_code })}` : ""}
        </p>
      )}
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {options.map((o) => (
          <button
            key={o}
            className="vy-chip"
            style={{
              border: "none",
              cursor: "pointer",
              background: docType === o ? "var(--accent)" : "var(--surface-overlay)",
              color: docType === o ? "var(--accent-ink)" : "var(--text-primary)",
            }}
            onClick={() => setDocType(o)}
          >
            {t(`verification:${DOC_KEY[o]}` as "typeGst")}
          </button>
        ))}
      </div>
      {docType === "credential" ? (
        <>
          <input className="vy-input" value={credentialName} onChange={(e) => setCredentialName(e.target.value)} placeholder={t("verification:credentialNameLabel")} />
          <input className="vy-input" value={issuer} onChange={(e) => setIssuer(e.target.value)} placeholder={t("verification:issuerLabel")} />
        </>
      ) : (
        <input className="vy-input" value={identifier} onChange={(e) => setIdentifier(e.target.value.toUpperCase())} placeholder={t("verification:identifierLabel")} />
      )}
      {error && <p className="vy-error">{error}</p>}
      <button className="vy-btn vy-btn-primary" disabled={!ready || busy} onClick={submit}>
        {busy ? t("common:state.saving") : t("verification:submit")}
      </button>
    </div>
  );
}
