"use client";

// [TR047] Verification queue — operator view (FR47). Oldest first, rows
// waiting longer than 3 days flagged. One-tap decisions straight from the
// record (Verify / Reject / Needs clearer copy); Reject and Needs-clearer-
// copy need a reason code (FR08/FR09), and the public GST / Udyam lookup is
// one click away. Evidence stays masked (last 4 only). Non-operators get a
// plain explanation, not a crash.
// [Design language 2026-09-29, operator console] ≥1024px: a dense list on
// the left and the record on the right; below that, the records stacked.
// Traces to: FR47, FR08, FR09, TR047, SP047
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { BadgeCheck, Building2, ExternalLink, FileCheck2, ShieldAlert, UserRound } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { DOC_KEY } from "@/app/components/Verification";
import Screen from "@/app/components/Screen";
import { Reveal } from "@/app/components/Motion";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import DisabledReason from "@/app/components/DisabledReason";
import "@/app/styles/deals-2026.css";

interface QueueItem {
  id: string;
  listing_id: string;
  kind?: string;
  document_type: string;
  identifier_masked: string | null;
  credential_name: string | null;
  issuer: string | null;
  days_pending: number;
}

const REASON_CODES = ["document_illegible", "document_expired", "name_mismatch", "document_type_mismatch", "suspected_fraud", "other"];

// FR08 DEC-001: manual operator lookup against the real public registries.
const PUBLIC_LOOKUP_URL: Record<string, string> = {
  gst: "https://services.gst.gov.in/services/searchtp",
  udyam: "https://udyamregistration.gov.in/Udyam_Verify.aspx",
};

export default function VerificationQueuePage() {
  const { t } = useTranslation(["verification", "common"]);
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<{ id: string; action: "reject" | "needs-clearer-copy" } | null>(null);
  const [reasonCode, setReasonCode] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api.get<QueueItem[]>("/v1/admin/verification-queue"));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      setItems([]);
    }
  }

  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  async function decide(id: string, action: "verify" | "reject" | "needs-clearer-copy", reason?: string) {
    setBusy(id);
    try {
      await api.post(`/v1/admin/verification-queue/${id}/${action}`, reason ? { reason_code: reason } : {});
      setPendingAction(null);
      setReasonCode("");
      await load();
    } finally {
      setBusy(null);
    }
  }

  if (forbidden) {
    return (
      <Screen width="console">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("verification:queueTitle")}</h1>
          </div>
          <DealsEmpty tone="neutral" icon={<ShieldAlert size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("verification:notOperator")} />
        </div>
      </Screen>
    );
  }

  const docLabel = (item: QueueItem) => t(`verification:${DOC_KEY[item.document_type]}` as "typeGst");
  const evidence = (item: QueueItem) => (item.document_type === "credential" ? [item.credential_name, item.issuer].filter(Boolean).join(" · ") : (item.identifier_masked ?? ""));
  const waiting = (item: QueueItem) => (item.days_pending > 3 ? t("verification:overdue") : t("verification:daysPending", { days: item.days_pending }));

  // One decision surface, used by the phone's stacked queue and the console's pane.
  function record(item: QueueItem) {
    const pending = pendingAction?.id === item.id ? pendingAction : null;
    return (
      <div className="vy-dl-sec" key={item.id}>
        <div className="vy-dl-sec-head vy-dl-sec-head-3">
          <span className={`vy-dl-tile ${item.kind === "professional" ? "vy-dl-tile-teal" : "vy-dl-tile-brand"}`} aria-hidden="true">
            {item.kind === "professional" ? <UserRound size={20} strokeWidth={1.75} /> : <Building2 size={20} strokeWidth={1.75} />}
          </span>
          <h2 className="vy-card-title">{docLabel(item)}</h2>
          <span className="vy-dl-sec-hint">{evidence(item)}</span>
          <span className="vy-dl-sec-head-end">
            <span className="vy-dl-state" data-tone={item.days_pending > 3 ? "warn" : undefined}>{waiting(item)}</span>
          </span>
        </div>
        <div className="vy-dl-actions">
          <a className="vy-btn vy-btn-ghost vy-dl-btn-sm" href={`/listings/${item.listing_id}`}>
            {t("verification:openProfile")} <ExternalLink size={14} strokeWidth={2} aria-hidden="true" />
          </a>
          {PUBLIC_LOOKUP_URL[item.document_type] && (
            <a className="vy-btn vy-btn-ghost vy-dl-btn-sm" href={PUBLIC_LOOKUP_URL[item.document_type]} target="_blank" rel="noopener noreferrer">
              {t("verification:publicLookup", { doc: docLabel(item) })} <ExternalLink size={14} strokeWidth={2} aria-hidden="true" />
            </a>
          )}
        </div>
        <div className="vy-dl-actions">
          <button className="vy-btn vy-btn-primary" disabled={busy === item.id} onClick={() => decide(item.id, "verify")}>
            <BadgeCheck size={16} strokeWidth={2} aria-hidden="true" /> {t("verification:verify")}
          </button>
          <button className="vy-btn vy-btn-secondary" disabled={busy === item.id} aria-expanded={pending?.action === "reject"} onClick={() => setPendingAction(pending?.action === "reject" ? null : { id: item.id, action: "reject" })}>
            {t("verification:reject")}
          </button>
          <button className="vy-btn vy-btn-ghost" disabled={busy === item.id} aria-expanded={pending?.action === "needs-clearer-copy"} onClick={() => setPendingAction(pending?.action === "needs-clearer-copy" ? null : { id: item.id, action: "needs-clearer-copy" })}>
            {t("verification:needsClearerCopy")}
          </button>
        </div>
        {pending && (
          <div className="vy-dl-panel">
            <label className="vy-field">
              <span className="vy-label">{t("verification:reasonLabel")}</span>
              <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
                <option value="">{t("verification:chooseReason")}</option>
                {REASON_CODES.map((code) => (
                  <option key={code} value={code}>
                    {t(`verification:reasonCode.${code}` as "reasonCode.document_illegible")}
                  </option>
                ))}
              </select>
            </label>
            <div className="vy-dl-actions">
              <button className="vy-btn vy-btn-secondary" aria-describedby={!reasonCode ? `vq-why-${item.id}` : undefined} disabled={!reasonCode || busy === item.id} onClick={() => decide(item.id, pending.action, reasonCode)}>
                {t(pending.action === "reject" ? "verification:reject" : "verification:needsClearerCopy")}
              </button>
              <button className="vy-btn vy-btn-ghost" onClick={() => setPendingAction(null)}>{t("common:action.cancel")}</button>
            </div>
            <DisabledReason id={`vq-why-${item.id}`} show={!reasonCode}>{t("verification:chooseReason")}</DisabledReason>
          </div>
        )}
      </div>
    );
  }

  const selectedItem = items?.find((i) => i.id === selected) ?? items?.[0] ?? null;

  return (
    <Screen width="console">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("verification:queueTitle")}</h1>
          <p>{t("verification:queueSubtitle")}</p>
        </div>
        {items === null && <SkeletonGrid count={3} grid={false} />}
        {items?.length === 0 && <DealsEmpty tone="green" icon={<FileCheck2 size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("verification:queueEmpty")} />}

        {items && items.length > 0 && (
          <div className="vy-pane">
            <div className="vy-pane-list vy-dl-list">
              {items.map((item, i) => (
                <Reveal key={item.id} index={i}>
                  {/* Phone/tablet: the whole record, inline. */}
                  <div className="vy-pane-row-mobile">{record(item)}</div>
                  {/* Console: a compact, scannable row that selects. */}
                  <button type="button" className="vy-dl-row vy-pane-row-console" aria-current={selectedItem?.id === item.id ? "true" : undefined} onClick={() => setSelected(item.id)}>
                    <span className={`vy-dl-tile ${item.kind === "professional" ? "vy-dl-tile-teal" : "vy-dl-tile-brand"}`} aria-hidden="true">
                      {item.kind === "professional" ? <UserRound size={18} strokeWidth={1.75} /> : <Building2 size={18} strokeWidth={1.75} />}
                    </span>
                    <span className="vy-dl-row-body">
                      <span className="vy-dl-row-title">{docLabel(item)}</span>
                      <span className="vy-dl-row-meta"><span>{evidence(item)}</span></span>
                    </span>
                    <span className="vy-dl-row-aside">
                      <span className="vy-dl-state" data-tone={item.days_pending > 3 ? "warn" : undefined}>{waiting(item)}</span>
                    </span>
                  </button>
                </Reveal>
              ))}
            </div>
            <div className="vy-pane-detail vy-console-only">{selectedItem && record(selectedItem)}</div>
          </div>
        )}
      </div>
    </Screen>
  );
}
