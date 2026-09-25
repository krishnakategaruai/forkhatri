"use client";

// [TR039] Report and block (FR39) — opens in place under the item, never a
// separate screen (fewer actions). Reason chips, optional note, one Send.
// The receipt says plainly the other person won't know who reported, shows
// the grievance channel (FR53), and offers Block in the same flow (FR24).
// An Idempotency-Key per opened sheet means a double tap or a retry after a
// dropped connection files one report, not two.
// Reference: Upwork's in-place "Flag as inappropriate" with a reason list and
// confidential review; WorkIndia's email-only reporting is what this avoids.
// Traces to: FR39, FR24, FR53, TR039
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

const REASONS = ["scam", "fake", "impersonation", "harassment", "discrimination", "spam", "stale", "privacy", "other"] as const;

export default function ReportSheet({
  objectKind,
  objectId,
  blockMemberId,
}: {
  objectKind: "listing" | "opportunity" | "enquiry" | "partnership" | "review";
  objectId: string;
  blockMemberId?: string;
}) {
  const { t } = useTranslation(["trustSafety", "common"]);
  const sdk = useSdk();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [blockTarget, setBlockTarget] = useState<string | null>(null);
  const [blocked, setBlocked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now())));

  if (!open) {
    return (
      <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => setOpen(true)}>
        ⚑ {t("trustSafety:report.button")}
      </button>
    );
  }

  if (sent) {
    return (
      <div className="vy-card vy-stack">
        <p>{t("trustSafety:report.received")}</p>
        <p className="vy-muted">{t("trustSafety:report.grievance")}</p>
        {blockTarget && !blocked && (
          <button
            className="vy-btn vy-btn-secondary"
            style={{ alignSelf: "flex-start" }}
            onClick={async () => {
              await sdk.enquiries.block(blockTarget);
              setBlocked(true);
            }}
          >
            {t("trustSafety:report.block")}
          </button>
        )}
        {blocked && <p className="vy-muted">{t("trustSafety:report.blocked")}</p>}
      </div>
    );
  }

  async function send() {
    if (!reason) return;
    setSending(true);
    setError(null);
    try {
      const result = await sdk.trustSafety.report(
        { object_kind: objectKind, object_id: objectId, reason, evidence_text: note || undefined },
        idempotencyKey,
      );
      setBlockTarget(blockMemberId ?? result.block_member_id);
      setSent(true);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="vy-card vy-stack">
      <h2 className="vy-card-title">{t("trustSafety:report.title")}</h2>
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {REASONS.map((r) => (
          <button
            key={r}
            className="vy-chip"
            style={{
              border: `1px solid ${reason === r ? "var(--accent)" : "var(--border-hairline)"}`,
              cursor: "pointer",
              background: reason === r ? "var(--accent-soft)" : "var(--surface-overlay)",
              color: reason === r ? "var(--accent-strong)" : "var(--text-primary)",
            }}
            onClick={() => setReason(r)}
          >
            {t(`trustSafety:reason.${r}` as "reason.scam")}
          </button>
        ))}
      </div>
      <textarea
        className="vy-textarea"
        rows={3}
        maxLength={1000}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder={t("trustSafety:report.evidencePlaceholder")}
      />
      {error && <p className="vy-error">{error}</p>}
      <div className="vy-row">
        <button className="vy-btn vy-btn-primary" disabled={!reason || sending} onClick={send}>
          {sending ? t("common:state.saving") : t("trustSafety:report.submit")}
        </button>
        <button className="vy-btn vy-btn-ghost" onClick={() => setOpen(false)}>
          {t("common:action.cancel")}
        </button>
      </div>
    </div>
  );
}
