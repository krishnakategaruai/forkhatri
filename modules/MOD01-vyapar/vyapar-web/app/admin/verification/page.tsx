"use client";

// [TR047] Verification queue — operator view (FR47). Oldest first, rows
// waiting longer than 3 days flagged. One-tap decisions straight from the
// card (Verify / Reject / Needs clearer copy) — no separate detail screen,
// per the "no unnecessary intermediate screens" standing preference.
// Evidence stays masked (last 4 only); the API never returns the encrypted
// identifier at all. Non-operators get a plain explanation, not a crash.
// Traces to: FR47, FR08, FR09, TR047, SP047
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { DOC_KEY } from "@/app/components/Verification";
import Screen from "@/app/components/Screen";
import { Reveal } from "@/app/components/Motion";
import { SkeletonGrid, EmptyState } from "@/app/components/States";

interface QueueItem {
  id: string;
  listing_id: string;
  document_type: string;
  identifier_masked: string | null;
  credential_name: string | null;
  issuer: string | null;
  days_pending: number;
}

// [Critique agent finding, fixed here] `decide()` posted `{}` for every
// action, including Reject and Needs-clearer-copy — FR08/FR09's own
// acceptance criteria name "Operator Verify/Reject WITH REASON", and the
// listing's own rejected-state template reads that reason back. Reusing
// the exact gating pattern already correct in admin/moderation/page.tsx
// (a REASON_CODES select that must hold a value before Apply is enabled)
// rather than inventing a second pattern. Verify needs no reason — only
// Reject and Needs-clearer-copy do, per FR08/FR09's own wording.
const REASON_CODES = ["document_illegible", "document_expired", "name_mismatch", "document_type_mismatch", "suspected_fraud", "other"];

// [Critique agent finding, fixed here] FR47's own requirement text: "...
// provide a link to the public GST/Udyam lookup where applicable...". No
// such link existed anywhere on this screen — FR08 DEC-001 committed to
// manual operator lookup against the real public registries (not a paid
// verification API), so the operator needs a real place to click through to.
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
  // [IMP33] Which queue item the ≥1024px console pane is showing.
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
      <Screen>
        <h1>{t("verification:queueTitle")}</h1>
        <EmptyState mark="⚠" title={t("verification:notOperator")} />
      </Screen>
    );
  }

  // [IMP33] The full record + decision controls for one queue item.
  // Extracted as a function so the SAME markup serves the phone's stacked
  // queue and the ≥1024px console's right-hand detail pane — one decision
  // surface, not two that can drift (this queue applies FR47's operator
  // actions with mandatory reason codes; two copies would be a real risk).
  function record(item: QueueItem) {
    return (
          <div key={item.id} className="vy-card vy-stack">
            <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
              <strong>{t(`verification:${DOC_KEY[item.document_type]}` as "typeGst")}</strong>
              <span className={item.days_pending > 3 ? "vy-badge vy-badge-sponsored" : "vy-muted"}>
                {item.days_pending > 3 ? t("verification:overdue") : t("verification:daysPending", { days: item.days_pending })}
              </span>
            </div>
            <p className="vy-muted">
              {item.document_type === "credential" ? `${item.credential_name ?? ""} · ${item.issuer ?? ""}` : item.identifier_masked}
            </p>
            <a className="vy-muted" href={`/listings/${item.listing_id}`}>
              {t("common:action.back")} →
            </a>
            {PUBLIC_LOOKUP_URL[item.document_type] && (
              <a className="vy-muted" href={PUBLIC_LOOKUP_URL[item.document_type]} target="_blank" rel="noopener noreferrer">
                {t("verification:publicLookup", { doc: t(`verification:${DOC_KEY[item.document_type]}` as "typeGst") })} ↗
              </a>
            )}
            <div className="vy-row" style={{ flexWrap: "wrap" }}>
              <button className="vy-btn vy-btn-primary" disabled={busy === item.id} onClick={() => decide(item.id, "verify")}>
                {t("verification:verify")}
              </button>
              <button
                className="vy-btn vy-btn-secondary"
                disabled={busy === item.id}
                onClick={() => setPendingAction(pendingAction?.id === item.id && pendingAction.action === "reject" ? null : { id: item.id, action: "reject" })}
              >
                {t("verification:reject")}
              </button>
              <button
                className="vy-btn vy-btn-ghost"
                disabled={busy === item.id}
                onClick={() => setPendingAction(pendingAction?.id === item.id && pendingAction.action === "needs-clearer-copy" ? null : { id: item.id, action: "needs-clearer-copy" })}
              >
                {t("verification:needsClearerCopy")}
              </button>
            </div>
            {pendingAction?.id === item.id && (
              <div className="vy-stack">
                <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
                  <option value="">{t("verification:chooseReason")}</option>
                  {REASON_CODES.map((code) => (
                    <option key={code} value={code}>
                      {t(`verification:reasonCode.${code}` as "reasonCode.document_illegible")}
                    </option>
                  ))}
                </select>
                <button
                  className="vy-btn vy-btn-primary"
                  disabled={!reasonCode || busy === item.id}
                  onClick={() => decide(item.id, pendingAction.action, reasonCode)}
                >
                  {t(pendingAction.action === "reject" ? "verification:reject" : "verification:needsClearerCopy")}
                </button>
              </div>
            )}
          </div>
    );
  }

  const selectedItem = items?.find((i) => i.id === selected) ?? items?.[0] ?? null;

  return (
    // ==================================================================
    // [IMP33 — Admin console layout, 04-ui.md F4 `--fk-bp-console`]
    // The sealed spec says ≥1024px Admin screens are "list + right detail
    // pane"; UI19's own mobile-first section spells out the proportions
    // ("Desktop ≥ 1024 px: list left (40 %) + record/case right"). None of
    // it was built — the console rendered as the same 480px phone column,
    // which for an operator working a queue all day is the worst place in
    // the app for it.
    // Below 1024px the queue stays exactly as it was: full records
    // stacked, each with its own decision controls.
    // Traces to: FR47, 04-ui.md F4 + UI19, product-owner direction.
    // ==================================================================
    <Screen width="console">
      <h1>{t("verification:queueTitle")}</h1>
      {items === null && <SkeletonGrid count={3} grid={false} />}
      {items?.length === 0 && <EmptyState mark="✓" title={t("verification:queueEmpty")} />}

      {items && items.length > 0 && (
        <div className="vy-pane">
          <div className="vy-pane-list vy-stack">
            {items.map((item, i) => (
              <Reveal key={item.id} index={i}>
                {/* Phone/tablet: the whole record, inline. */}
                <div className="vy-pane-row-mobile">{record(item)}</div>
                {/* Console: a compact, scannable row that selects. */}
                <button
                  type="button"
                  className={`vy-card vy-pane-row-console vy-card-interactive ${selectedItem?.id === item.id ? "vy-card-selected" : ""}`}
                  aria-current={selectedItem?.id === item.id ? "true" : undefined}
                  style={{ gap: 4, width: "100%", textAlign: "left", cursor: "pointer", font: "inherit", color: "inherit", padding: "var(--space-4)" }}
                  onClick={() => setSelected(item.id)}
                >
                  <strong>{t(`verification:${DOC_KEY[item.document_type]}` as "typeGst")}</strong>
                  <span className={item.days_pending > 3 ? "vy-badge vy-badge-sponsored" : "vy-muted"} style={{ alignSelf: "flex-start" }}>
                    {item.days_pending > 3 ? t("verification:overdue") : t("verification:daysPending", { days: item.days_pending })}
                  </span>
                  <span className="vy-muted">
                    {item.document_type === "credential" ? `${item.credential_name ?? ""} · ${item.issuer ?? ""}` : item.identifier_masked}
                  </span>
                </button>
              </Reveal>
            ))}
          </div>
          <div className="vy-pane-detail vy-console-only">{selectedItem && record(selectedItem)}</div>
        </div>
      )}
    </Screen>
  );
}
