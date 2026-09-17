"use client";

// [TR041] Appeals and outcome communication (FR41) — member side. Every
// decision on the member's own content, with its reason, date and appeal
// deadline; Appeal opens in place on the card (no separate form screen).
// The grievance channel and appeal process are shown on this outcome screen
// itself, as FR53 requires. Reporter identity is never part of this data.
// Traces to: FR41, FR53, TR041
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

interface Outcome {
  case_id: string;
  object_kind: string;
  object_id: string;
  action: string;
  reason_code: string | null;
  action_duration_days: number | null;
  decided_at: string;
  appeal_deadline: string;
  appeal_state: string | null;
  can_appeal: boolean;
}

function OutcomeCard({ item, onDone }: { item: Outcome; onDone: () => void }) {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  async function appeal() {
    setBusy(true);
    setError(null);
    try {
      await api.post("/v1/appeals", { case_id: item.case_id, text });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-card vy-stack">
      <strong>
        {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")} · {t(`trustSafety:action.${item.action}` as "action.limit")}
      </strong>
      {item.reason_code && <p className="vy-muted">{t(`trustSafety:reasonCode.${item.reason_code}` as "reasonCode.spam", { defaultValue: item.reason_code })}</p>}
      <p className="vy-muted">{t("trustSafety:outcomes.decidedOn", { date: fmt(item.decided_at) })}</p>
      {item.appeal_state && <span className="vy-badge vy-badge-member-provided">{t(`trustSafety:outcomes.appealState.${item.appeal_state}` as "outcomes.appealState.open")}</span>}
      {!item.appeal_state && !item.can_appeal && item.action !== "restore" && <p className="vy-muted">{t("trustSafety:outcomes.windowClosed")}</p>}
      {item.can_appeal && !open && (
        <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => setOpen(true)}>
          {t("trustSafety:outcomes.appeal")} · {t("trustSafety:outcomes.appealBy", { date: fmt(item.appeal_deadline) })}
        </button>
      )}
      {item.can_appeal && open && (
        <div className="vy-stack">
          <textarea className="vy-textarea" rows={4} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} placeholder={t("trustSafety:outcomes.appealPlaceholder")} />
          {error && <p className="vy-error">{error}</p>}
          <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={!text || busy} onClick={appeal}>
            {t("trustSafety:outcomes.appeal")}
          </button>
        </div>
      )}
    </div>
  );
}

export default function OutcomesPage() {
  const { t } = useTranslation(["trustSafety", "common"]);
  const [items, setItems] = useState<Outcome[] | null>(null);

  async function load() {
    setItems(await api.get<Outcome[]>("/v1/moderation/outcomes"));
  }

  useEffect(() => {
    load().catch(() => setItems([]));
  }, []);

  return (
    <main className="vy-shell">
      <h1>{t("trustSafety:outcomes.title")}</h1>
      <p className="vy-muted">{t("trustSafety:outcomes.process")}</p>
      <p id="grievance" className="vy-muted">{t("trustSafety:report.grievance")}</p>
      {items === null && <p className="vy-muted">{t("common:state.loading")}</p>}
      {items?.length === 0 && <p className="vy-muted">{t("trustSafety:outcomes.empty")}</p>}
      <div className="vy-stack">
        {items?.map((o) => <OutcomeCard key={o.case_id} item={o} onDone={load} />)}
      </div>
    </main>
  );
}
