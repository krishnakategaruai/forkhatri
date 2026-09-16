"use client";

// [TR026] Respond to and manage a Partnership Request (FR26) — UX17's
// request detail for both sides. State chip first in reading order; the
// other side's listing with its reputation line as trust context (FR25);
// the seven fields; contact details only once Accepted (FR26, same
// disclosure function as enquiries); actions for exactly this role and
// state — no confirmation dialogs, Close explains its consequence in place.
// After Close, the review composer appears right here (FR27), and Report is
// always available (FR39).
// Traces to: FR25, FR26, FR27, FR39, TR026, UX17
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { ReputationLine, type Reputation } from "@/app/components/Reputation";
import ReviewComposer from "@/app/components/ReviewComposer";
import ReportSheet from "@/app/components/ReportSheet";

interface ListingSummary {
  id: string;
  name: string;
  kind: string;
  verification_state: string;
  reputation: Reputation | null;
}

interface Partnership {
  id: string;
  state: string;
  is_sender: boolean;
  need: string;
  offer: string;
  expectations: string;
  category: string;
  locality: string;
  timing: string;
  next_step: string;
  created_at: string;
  sender_listing: ListingSummary | null;
  recipient_listing: ListingSummary | null;
  disclosed_contacts: { channel: string; value: string }[];
}

const FIELD_LABELS: [keyof Partnership, string][] = [
  ["need", "compose.need"],
  ["offer", "compose.offer"],
  ["expectations", "compose.expectations"],
  ["category", "compose.category"],
  ["locality", "compose.locality"],
  ["timing", "compose.timing"],
  ["next_step", "compose.nextStep"],
];

export default function PartnershipDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["partnerships", "common"]);
  const [request, setRequest] = useState<Partnership | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setRequest(await api.get<Partnership>(`/v1/partnership-requests/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("partnerships:detail.notFound"));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(action: string) {
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/partnership-requests/${id}/${action}`);
      await refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (error) return <main className="vy-shell"><h1>{t("partnerships:detail.notFound")}</h1><p>{error}</p></main>;
  if (!request) return <main className="vy-shell"><p>{t("common:state.loading")}</p></main>;

  const other = request.is_sender ? request.recipient_listing : request.sender_listing;
  const pending = request.state === "pending";

  return (
    <main className="vy-shell">
      <div>
        <span className="vy-badge vy-badge-member-provided">{t(`partnerships:state.${request.state}` as "state.pending")}</span>
        <h1 style={{ marginTop: 8 }}>{t("partnerships:detail.title")}</h1>
        <p className="vy-muted">{t("partnerships:detail.sent", { date: new Date(request.created_at).toLocaleDateString(i18n.language) })}</p>
      </div>

      {other && (
        <a className="vy-card" href={`/listings/${other.id}`} style={{ textDecoration: "none" }}>
          <span className="vy-muted" style={{ fontSize: 12 }}>{request.is_sender ? t("partnerships:detail.to") : t("partnerships:detail.from")}</span>
          <h2 style={{ fontSize: 17 }}>{other.name}</h2>
          <ReputationLine rep={other.reputation} />
        </a>
      )}

      <div className="vy-card vy-stack">
        {FIELD_LABELS.map(([field, key]) => (
          <div key={field}>
            <span className="vy-label">{t(`partnerships:${key}` as "compose.need")}</span>
            <p>{String(request[field] ?? "")}</p>
          </div>
        ))}
      </div>

      {request.disclosed_contacts.length > 0 && (
        <div className="vy-card vy-stack">
          <strong style={{ fontSize: 14 }}>{t("partnerships:detail.contactTitle")}</strong>
          {request.disclosed_contacts.map((c) => (
            <p key={c.channel}>{c.channel}: {c.value}</p>
          ))}
          <p className="vy-muted" style={{ fontSize: 13 }}>{t("partnerships:detail.safety")}</p>
        </div>
      )}

      {notice && <p className="vy-error">{notice}</p>}
      {request.is_sender && request.state === "declined" && <p className="vy-muted">{t("partnerships:detail.declinedCooldown")}</p>}
      {request.state === "restricted" && <p className="vy-muted">{t("partnerships:detail.restrictedNote")}</p>}

      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {!request.is_sender && pending && (
          <>
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act("accept")}>{t("partnerships:detail.accept")}</button>
            <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act("decline")}>{t("partnerships:detail.decline")}</button>
          </>
        )}
        {!request.is_sender && (pending || request.state === "accepted") && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act("restrict")}>{t("partnerships:detail.restrict")}</button>
        )}
        {request.is_sender && pending && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act("withdraw")}>{t("partnerships:detail.withdraw")}</button>
        )}
      </div>
      {request.state === "accepted" && (
        <div className="vy-stack" style={{ gap: 4 }}>
          <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => act("close")}>
            {t("partnerships:detail.close")}
          </button>
          <p className="vy-muted" style={{ fontSize: 13 }}>{t("partnerships:detail.closeHelp")}</p>
        </div>
      )}

      {request.state === "closed" && <ReviewComposer interactionKind="partnership" interactionId={id} />}
      <ReportSheet objectKind="partnership" objectId={id} />
    </main>
  );
}
