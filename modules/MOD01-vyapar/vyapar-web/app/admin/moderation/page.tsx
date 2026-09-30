"use client";

// [TR040/TR041] Moderation queue and appeals — operator view (FR40, FR41).
// Most urgent first (severity, then due time); missed targets flagged. Each
// case holds everything needed to decide in place: the object, evidence
// (read-only), prior cases on the same object, and the six graduated
// actions, each requiring a reason code before Apply is enabled. Appeals sit
// below with Uphold / Overturn.
// [Design language 2026-09-29, operator console] Case cards with an icon
// tile, severity and due as quiet chips, the actions as selectable choice
// chips, and the reason panel nested one lightness step down. Two columns
// (cases · appeals) on a wide desk.
// Traces to: FR40, FR41, TR040, TR041
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, ChevronDown, ChevronUp, ExternalLink, Gavel, ShieldAlert, ShieldCheck } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import DisabledReason from "@/app/components/DisabledReason";
import { formatDate, formatDateTime } from "@/lib/format";
import "@/app/styles/deals-2026.css";

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
const REASON_CODES = ["scam_confirmed", "fake_listing", "impersonation", "harassment", "discrimination", "spam", "stale_info", "privacy_violation", "policy_other", "no_violation", "appeal_evidence_accepted"];
const OBJECT_PATH: Record<string, string> = { listing: "listings", opportunity: "opportunities" };

function severityTone(severity: string): "warn" | "wait" | undefined {
  return severity === "high" || severity === "critical" ? "warn" : severity === "medium" ? "wait" : undefined;
}

function CaseCard({ item, onDone }: { item: CaseItem; onDone: () => void }) {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const [action, setAction] = useState<string | null>(null);
  const [reasonCode, setReasonCode] = useState("");
  const [days, setDays] = useState(30);
  const [busy, setBusy] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  async function apply() {
    setBusy(true);
    try {
      await api.post(`/v1/admin/moderation-cases/${item.id}/decide`, { action, reason_code: reasonCode, duration_days: action === "suspend" ? days : undefined });
      onDone();
    } finally {
      setBusy(false);
    }
  }

  const path = OBJECT_PATH[item.object_kind];
  return (
    <div className="vy-dl-sec">
      <div className="vy-dl-sec-head">
        <span className={`vy-dl-tile ${severityTone(item.severity) === "warn" ? "vy-dl-tile-red" : "vy-dl-tile-amber"}`} aria-hidden="true">
          <ShieldAlert size={20} strokeWidth={1.75} />
        </span>
        <h2 className="vy-card-title">
          {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")}
          {item.object_title ? ` · ${item.object_title}` : ""}
        </h2>
        <span className="vy-dl-sec-hint">
          {t(`trustSafety:source.${item.source}` as "source.report")}
          {item.reporter_count > 0 ? ` · ${t("trustSafety:queue.reporters", { n: item.reporter_count })}` : ""}
          {item.primary_reason ? ` · ${t(`trustSafety:primaryReason.${item.primary_reason}` as "primaryReason.scam", { defaultValue: item.primary_reason })}` : ""}
        </span>
      </div>
      <div className="vy-dl-tags">
        <span className="vy-dl-state" data-tone={severityTone(item.severity)}>{t(`trustSafety:severity.${item.severity}` as "severity.low")}</span>
        <span className="vy-dl-state" data-tone={item.overdue ? "warn" : undefined}>
          {item.overdue ? t("trustSafety:queue.overdue") : t("trustSafety:queue.due", { date: formatDateTime(item.target_due_at, i18n.language) })}
        </span>
        {item.distribution_limited && <span className="vy-dl-state" data-tone="muted">{t("trustSafety:queue.distributionLimited")}</span>}
      </div>
      <div className="vy-dl-actions">
        {path && (
          <a className="vy-btn vy-btn-ghost vy-dl-btn-sm" href={`/${path}/${item.object_id}`}>
            {t("trustSafety:queue.openObject")} <ExternalLink size={14} strokeWidth={2} aria-hidden="true" />
          </a>
        )}
        {item.prior_cases > 0 && (
          <button type="button" className="vy-btn vy-btn-ghost vy-dl-btn-sm" aria-expanded={showHistory} onClick={() => setShowHistory((v) => !v)}>
            {t("trustSafety:queue.priorCases", { n: item.prior_cases })}
            {showHistory ? <ChevronUp size={14} strokeWidth={2} aria-hidden="true" /> : <ChevronDown size={14} strokeWidth={2} aria-hidden="true" />}
          </button>
        )}
      </div>
      {showHistory && item.prior_case_history.length > 0 && (
        <ol className="vy-dl-history">
          {item.prior_case_history.map((p, i) => (
            <li key={i}>
              <span>
                {p.action ? t(`trustSafety:action.${p.action}` as "action.limit") : t(`trustSafety:queue.caseState.${p.state}` as "queue.caseState.dismissed")}
                {p.reason_code
                  ? ` — ${t(`trustSafety:reasonCode.${p.reason_code}` as "reasonCode.spam", { defaultValue: p.reason_code })}`
                  : p.primary_reason
                    ? ` — ${t(`trustSafety:primaryReason.${p.primary_reason}` as "primaryReason.scam", { defaultValue: p.primary_reason })}`
                    : ""}
              </span>
              <time dateTime={p.date}>{formatDate(p.date, i18n.language)}</time>
            </li>
          ))}
        </ol>
      )}
      {item.evidence.length > 0 && (
        <div className="vy-dl-panel">
          <span className="vy-label">{t("trustSafety:queue.evidence")}</span>
          {item.evidence.map((e, i) => (
            <p key={i} className="vy-dl-hint">
              <strong style={{ color: "var(--text-primary)" }}>{t(`trustSafety:reason.${e.reason}` as "reason.scam")}</strong>
              {e.evidence_text ? ` — ${e.evidence_text}` : ""}
            </p>
          ))}
        </div>
      )}
      <div className="vy-field">
        <span className="vy-label">{t("trustSafety:queue.decisionLabel")}</span>
        <div className="vy-dl-tags" role="radiogroup" aria-label={t("trustSafety:queue.decisionLabel")}>
          {ACTIONS.map((a) => (
            <button key={a} type="button" role="radio" aria-checked={action === a} className={`vy-chip${action === a ? " vy-chip-selected" : ""}`} onClick={() => setAction(a)}>
              {action === a && <Check size={14} strokeWidth={2.5} aria-hidden="true" />}
              {t(`trustSafety:action.${a}` as "action.limit")}
            </button>
          ))}
        </div>
      </div>
      {action && (
        <div className="vy-dl-panel">
          <label className="vy-field">
            <span className="vy-label">{t("trustSafety:queue.reasonLabel")}</span>
            <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
              <option value="">{t("trustSafety:queue.chooseReason")}</option>
              {REASON_CODES.map((code) => (
                <option key={code} value={code}>
                  {t(`trustSafety:reasonCode.${code}` as "reasonCode.spam")}
                </option>
              ))}
            </select>
          </label>
          {action === "suspend" && (
            <label className="vy-field">
              <span className="vy-label">{t("trustSafety:queue.durationLabel")}</span>
              <input className="vy-input" type="number" min={1} max={365} value={days} onChange={(e) => setDays(Number(e.target.value))} />
            </label>
          )}
          <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} aria-describedby={!reasonCode ? `mq-why-${item.id}` : undefined} disabled={!reasonCode || busy} onClick={apply}>
            {t("trustSafety:queue.apply")}
          </button>
          <DisabledReason id={`mq-why-${item.id}`} show={!reasonCode}>{t("trustSafety:queue.chooseReason")}</DisabledReason>
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
    <div className="vy-dl-sec">
      <div className="vy-dl-sec-head">
        <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Gavel size={20} strokeWidth={1.75} /></span>
        <h2 className="vy-card-title">
          {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")}
          {item.object_title ? ` · ${item.object_title}` : ""}
        </h2>
        {item.action && <span className="vy-dl-sec-hint">{t("trustSafety:queue.appealAgainst", { action: t(`trustSafety:action.${item.action}` as "action.limit") })}</span>}
      </div>
      <div className="vy-dl-tags">
        <span className="vy-dl-state" data-tone={item.overdue ? "warn" : undefined}>
          {item.overdue ? t("trustSafety:queue.overdue") : t("trustSafety:queue.due", { date: formatDate(item.due_at, i18n.language) })}
        </span>
      </div>
      <p className="vy-dl-stage-note">{item.text}</p>
      <label className="vy-field">
        <span className="vy-label">{t("trustSafety:queue.reasonLabel")}</span>
        <select className="vy-select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
          <option value="">{t("trustSafety:queue.chooseReason")}</option>
          {REASON_CODES.map((code) => (
            <option key={code} value={code}>
              {t(`trustSafety:reasonCode.${code}` as "reasonCode.spam")}
            </option>
          ))}
        </select>
      </label>
      <div className="vy-dl-actions">
        <button className="vy-btn vy-btn-secondary" disabled={!reasonCode || busy} onClick={() => decide("upheld")}>
          {t("trustSafety:queue.uphold")}
        </button>
        <button className="vy-btn vy-btn-primary" aria-describedby={!reasonCode ? `why-overturn-${item.id}` : undefined} disabled={!reasonCode || busy} onClick={() => decide("overturned")}>
          {t("trustSafety:queue.overturn")}
        </button>
      </div>
      <DisabledReason id={`why-overturn-${item.id}`} show={!reasonCode}>{t("trustSafety:queue.chooseReason")}</DisabledReason>
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
      const [c, a] = await Promise.all([api.get<CaseItem[]>("/v1/admin/moderation-queue"), api.get<AppealItem[]>("/v1/admin/appeals")]);
      setCases(c);
      setAppeals(a);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      setCases([]);
    }
  }

  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  if (forbidden) {
    return (
      <Screen width="console">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("trustSafety:queue.title")}</h1>
          </div>
          <DealsEmpty tone="neutral" icon={<ShieldAlert size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("trustSafety:queue.notOperator")} />
        </div>
      </Screen>
    );
  }

  return (
    <Screen width="console">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("trustSafety:queue.title")}</h1>
          <p>{t("trustSafety:queue.subtitle")}</p>
        </div>
        <div className="vy-dl-console-2">
          <section className="vy-dl-page" aria-labelledby="mq-cases">
            <div className="vy-dl-head-row">
              <h2 id="mq-cases" className="vy-section-title">
                {t("trustSafety:queue.casesTitle")} {cases && <span className="vy-dl-count">{cases.length}</span>}
              </h2>
            </div>
            {cases === null && <SkeletonGrid count={2} grid={false} />}
            {cases?.length === 0 && <DealsEmpty tone="green" icon={<ShieldCheck size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("trustSafety:queue.empty")} />}
            {cases?.map((c) => <CaseCard key={c.id} item={c} onDone={load} />)}
          </section>
          <section className="vy-dl-page" aria-labelledby="mq-appeals">
            <div className="vy-dl-head-row">
              <h2 id="mq-appeals" className="vy-section-title">
                {t("trustSafety:queue.appealsTitle")} <span className="vy-dl-count">{appeals.length}</span>
              </h2>
            </div>
            {appeals.length === 0 && <DealsEmpty tone="neutral" icon={<Gavel size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("trustSafety:queue.appealsEmpty")} />}
            {appeals.map((a) => <AppealCard key={a.id} item={a} onDone={load} />)}
          </section>
        </div>
      </div>
    </Screen>
  );
}
