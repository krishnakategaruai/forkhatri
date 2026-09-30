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
//
// [FE2 — imp-backend-b §2] "Asked me for money" (`asked_for_money`) is a
// reason of its own for opportunities and enquiries: two reports from
// different people pause the post. Another block on the page (the seeker
// protection notice) can open this sheet with a reason already chosen via
// requestReport() — an event, so neither component owns the other.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import DisabledReason from "@/app/components/DisabledReason";

const REASONS = ["scam", "fake", "impersonation", "harassment", "discrimination", "spam", "stale", "privacy", "other"] as const;
const MONEY_REASON_KINDS = ["opportunity", "enquiry"];
const OPEN_REPORT_EVENT = "vyapar:open-report";

/** Open the report sheet for `objectId` on this page, with `reason` pre-chosen, and scroll to it. */
export function requestReport(objectId: string, reason: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(OPEN_REPORT_EVENT, { detail: { objectId, reason } }));
}

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
  const anchor = useRef<HTMLDivElement>(null);
  const reasons: readonly string[] = MONEY_REASON_KINDS.includes(objectKind) ? ["asked_for_money", ...REASONS] : REASONS;

  useEffect(() => {
    function onRequest(e: Event) {
      const detail = (e as CustomEvent<{ objectId: string; reason: string }>).detail;
      if (!detail || detail.objectId !== objectId) return;
      setOpen(true);
      setReason(detail.reason);
      requestAnimationFrame(() => anchor.current?.scrollIntoView({ behavior: "smooth", block: "center" }));
    }
    window.addEventListener(OPEN_REPORT_EVENT, onRequest);
    return () => window.removeEventListener(OPEN_REPORT_EVENT, onRequest);
  }, [objectId]);

  if (!open) {
    return (
      <div ref={anchor}>
        <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => setOpen(true)}>
          ⚑ {t("trustSafety:report.button")}
        </button>
      </div>
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
    <div className="vy-card vy-stack" ref={anchor}>
      <h2 className="vy-card-title">{t("trustSafety:report.title")}</h2>
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {reasons.map((r) => (
          <button
            key={r}
            className="vy-chip"
            style={{
              border: `1px solid ${reason === r ? "var(--selected-border)" : "var(--border-hairline)"}`,
              cursor: "pointer",
              background: reason === r ? "var(--selected-bg)" : "var(--surface-overlay)",
              color: reason === r ? "var(--selected-fg)" : "var(--text-primary)",
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
        <button className="vy-btn vy-btn-primary" aria-describedby={!reason ? "why-report" : undefined} disabled={!reason || sending} onClick={send}>
          {sending ? t("common:state.saving") : t("trustSafety:report.submit")}
        </button>
        <DisabledReason id={"why-report"} show={!reason}>{t("common:disabled.chooseReason")}</DisabledReason>
        <button className="vy-btn vy-btn-ghost" onClick={() => setOpen(false)}>
          {t("common:action.cancel")}
        </button>
      </div>
    </div>
  );
}
