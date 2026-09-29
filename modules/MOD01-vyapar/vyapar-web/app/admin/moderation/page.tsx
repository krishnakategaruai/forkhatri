"use client";

// [TR040/TR041] Moderation queue and appeals — operator view (FR40, FR41).
// Most urgent first (severity, then due time); missed targets flagged.
// Each case card holds everything needed to decide in place: the object,
// evidence (read-only — there is no edit path), prior cases on the same
// object, and the six graduated actions, each requiring a reason code
// before Apply is enabled. Appeals sit below with Uphold / Overturn.
// Traces to: FR40, FR41, TR040, TR041
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { formatDate } from "@/lib/format"; // [FE2] Indian date order

interface Evidence {
  reason: string;
  evidence_text: string | null;
  created_at: string;
}

interface CaseItem {
  id: string;
  object_kind: string;
  object_id: string;
  object_title: string | null;
  source: string;
  severity: string;
  state: string;
  reporter_count: number;
  primary_reason: string | null;
  distribution_limited: boolean;
  target_due_at: string;
  overdue: boolean;
  prior_cases: number;
  // [Critique agent finding, fixed here] FR40 requires the operator to
  // actually weigh history, not just see a count — real per-case detail.
  prior_case_history: { action: string | null; reason_code: string | null; primary_reason: string | null; state: string; date: string }[];
  evidence: Evidence[];
}

interface AppealItem {
  id: string;
  text: string;
  state: string;
  due_at: string;
  overdue: boolean;
  object_kind: string;
  object_title: string | null;
  action: string | null;
  reason_code: string | null;
}

const ACTIONS = ["limit", "remove", "restore", "request_verification", "suspend", "dismiss"] as const;
const REASON_CODES = [
  "scam_confirmed", "fake_listing", "impersonation", "harassment", "discrimination", "spam",
  "stale_info", "privacy_violation", "policy_other", "no_violation", "appeal_evidence_accepted",
];
const OBJECT_PATH: Record<string, string> = { listing: "listings", opportunity: "opportunities" };

function CaseCard({ item, onDone }: { item: CaseItem; onDone: () => void }) {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const [action, setAction] = useState<string | null>(null);
  const [reasonCode, setReasonCode] = useState("");
  const [days, setDays] = useState(30);
  const [busy, setBusy] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const urgent = item.severity === "high" || item.severity === "critical";

  async function apply() {
    setBusy(true);
    try {
      await api.post(`/v1/admin/moderation-cases/${item.id}/decide`, {
        action,
        reason_code: reasonCode,
        duration_days: action === "suspend" ? days : undefined,
      });
      onDone();
    } finally {
      setBusy(false);
    }
  }

  const path = OBJECT_PATH[item.object_kind];
  return (
    <div className="vy-card vy-stack">
      <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <span className={urgent ? "vy-chip" : "vy-badge vy-badge-member-provided"}>{t(`trustSafety:severity.${item.severity}` as "severity.low")}</span>
        <span className={item.overdue ? "vy-error" : "vy-muted"}>
          {item.overdue ? t("trustSafety:queue.overdue") : t("trustSafety:queue.due", { date: new Date(item.target_due_at).toLocaleString(i18n.language) })}
        </span>
      </div>
      <strong>
        {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")}
        {item.object_title ? ` · ${item.object_title}` : ""}
      </strong>
      {path && (
        <a className="vy-muted" href={`/${path}/${item.object_id}`}>
          {t("trustSafety:queue.openObject")} →
        </a>
      )}
      <p className="vy-muted">
        {t(`trustSafety:source.${item.source}` as "source.report")}
        {item.reporter_count > 0 ? ` · ${t("trustSafety:queue.reporters", { n: item.reporter_count })}` : ""}
        {item.primary_reason ? ` · ${t(`trustSafety:primaryReason.${item.primary_reason}` as "primaryReason.scam", { defaultValue: item.primary_reason })}` : ""}
      </p>
      {item.prior_cases > 0 && (
        <div>
          <button type="button" className="vy-btn vy-btn-ghost" style={{ fontSize: 13, padding: "4px 0" }} onClick={() => setShowHistory((v) => !v)}>
            {t("trustSafety:queue.priorCases", { n: item.prior_cases })} {showHistory ? "▲" : "▼"}
          </button>
          {showHistory && (
            <div className="vy-stack" style={{ gap: 4, marginTop: 4 }}>
              {item.prior_case_history.map((p, i) => (
                <p key={i} className="vy-muted" style={{ fontSize: 13 }}>
                  {p.action ? t(`trustSafety:action.${p.action}` as "action.limit") : t(`trustSafety:queue.caseState.${p.state}` as "queue.caseState.dismissed")}
                  {p.reason_code ? ` — ${t(`trustSafety:reasonCode.${p.reason_code}` as "reasonCode.spam", { defaultValue: p.reason_code })}` : p.primary_reason ? ` — ${t(`trustSafety:primaryReason.${p.primary_reason}` as "primaryReason.scam", { defaultValue: p.primary_reason })}` : ""}
                  {" · "}{formatDate(p.date, i18n.language)}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
      {item.distribution_limited && <span className="vy-badge vy-badge-sponsored">{t("trustSafety:queue.distributionLimited")}</span>}
      {item.evidence.length > 0 && (
        <div className="vy-stack" style={{ gap: 4 }}>
          <strong style={{ fontSize: 13 }}>{t("trustSafety:queue.evidence")}</strong>
          {item.evidence.map((e, i) => (
            <p key={i} className="vy-muted" style={{ fontSize: 13 }}>
              {t(`trustSafety:reason.${e.reason}` as "reason.scam")}
              {e.evidence_text ? ` — ${e.evidence_text}` : ""}
            </p>
          ))}
        </div>
      )}
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {ACTIONS.map((a) => (
          <button
            key={a}
            className="vy-chip"
            style={{
              border: `1px solid ${action === a ? "var(--selected-border)" : "var(--border-hairline)"}`,
              cursor: "pointer",
              background: action === a ? "var(--selected-bg)" : "var(--surface-overlay)",
              color: action === a ? "var(--selected-fg)" : "var(--text-primary)",
            }}
            onClick={() => setAction(a)}
          >
            {t(`trustSafety:action.${a}` as "action.limit")}
          </button>
        ))}
      </div>
      {action && (
        <div className="vy-stack">
          <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
            <option value="">{t("trustSafety:queue.chooseReason")}</option>
            {REASON_CODES.map((code) => (
              <option key={code} value={code}>
                {t(`trustSafety:reasonCode.${code}` as "reasonCode.spam")}
              </option>
            ))}
          </select>
          {action === "suspend" && (
            <label className="vy-field">
              <span className="vy-label">{t("trustSafety:queue.durationLabel")}</span>
              <input className="vy-input" type="number" min={1} max={365} value={days} onChange={(e) => setDays(Number(e.target.value))} />
            </label>
          )}
          <button className="vy-btn vy-btn-primary" disabled={!reasonCode || busy} onClick={apply}>
            {t("trustSafety:queue.apply")}
          </button>
        </div>
      )}
    </div>
  );
}

function AppealCard({ item, onDone }: { item: AppealItem; onDone: () => void }) {
  const { t, i18n } = useTranslation(["trustSafety"]);
  const [reasonCode, setReasonCode] = useState("");
  const [busy, setBusy] = useState(false);

  async function decide(decision: "upheld" | "overturned") {
    setBusy(true);
    try {
      await api.post(`/v1/admin/appeals/${item.id}/decide`, { decision, reason_code: reasonCode });
      onDone();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-card vy-stack">
      <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <strong>
          {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")}
          {item.object_title ? ` · ${item.object_title}` : ""}
        </strong>
        <span className={item.overdue ? "vy-error" : "vy-muted"}>
          {item.overdue ? t("trustSafety:queue.overdue") : t("trustSafety:queue.due", { date: formatDate(item.due_at, i18n.language) })}
        </span>
      </div>
      {item.action && <p className="vy-muted">{t(`trustSafety:action.${item.action}` as "action.limit")}</p>}
      <p>{item.text}</p>
      <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
        <option value="">{t("trustSafety:queue.chooseReason")}</option>
        {REASON_CODES.map((code) => (
          <option key={code} value={code}>
            {t(`trustSafety:reasonCode.${code}` as "reasonCode.spam")}
          </option>
        ))}
      </select>
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        <button className="vy-btn vy-btn-secondary" disabled={!reasonCode || busy} onClick={() => decide("upheld")}>
          {t("trustSafety:queue.uphold")}
        </button>
        <button className="vy-btn vy-btn-primary" disabled={!reasonCode || busy} onClick={() => decide("overturned")}>
          {t("trustSafety:queue.overturn")}
        </button>
      </div>
    </div>
  );
}

export default function ModerationQueuePage() {
  const { t } = useTranslation(["trustSafety", "common"]);
  const [cases, setCases] = useState<CaseItem[] | null>(null);
  const [appeals, setAppeals] = useState<AppealItem[]>([]);
  const [forbidden, setForbidden] = useState(false);

  async function load() {
    try {
      const [c, a] = await Promise.all([
        api.get<CaseItem[]>("/v1/admin/moderation-queue"),
        api.get<AppealItem[]>("/v1/admin/appeals"),
      ]);
      setCases(c);
      setAppeals(a);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      setCases([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (forbidden) {
    return (
      <Screen width="console">
        <h1>{t("trustSafety:queue.title")}</h1>
        <p className="vy-muted">{t("trustSafety:queue.notOperator")}</p>
      </Screen>
    );
  }

  return (
    <Screen width="console">
      <h1>{t("trustSafety:queue.title")}</h1>
      {cases === null && <p className="vy-muted">{t("common:state.loading")}</p>}
      {cases?.length === 0 && <p className="vy-muted">{t("trustSafety:queue.empty")}</p>}
      <div className="vy-stack">
        {cases?.map((c) => <CaseCard key={c.id} item={c} onDone={load} />)}
      </div>
      <h2 style={{ fontSize: 18 }}>{t("trustSafety:queue.appealsTitle")}</h2>
      {appeals.length === 0 && <p className="vy-muted">{t("trustSafety:queue.appealsEmpty")}</p>}
      <div className="vy-stack">
        {appeals.map((a) => <AppealCard key={a.id} item={a} onDone={load} />)}
      </div>
    </Screen>
  );
}
