"use client";

// [TR026] Respond to and manage a Partnership Request (FR26) — UX17's
// request detail for both sides. State chip first in reading order; the
// other side's listing with its reputation line as trust context (FR25);
// the seven fields; contact details only once Accepted (FR26, same
// disclosure function as enquiries); actions for exactly this role and
// state — no confirmation dialogs, Close explains its consequence in place.
// After Close, the review composer appears right here (FR27), and Report is
// always available (FR39).
// [IMP39 — desktop layout] ≥860px of room: the request (fields, contact,
// review) in the main column; a sticky aside with the other side's listing
// and exactly the actions this role and state allow. The action block is
// rendered in the aside on desktop and in its original phone position
// otherwise (one JSX value, two placements, one of them display:none), so
// the phone order is unchanged.
// Traces to: FR25, FR26, FR27, FR39, TR026, UX17
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { ReputationLine, type Reputation } from "@/app/components/Reputation";
import ReviewComposer from "@/app/components/ReviewComposer";
import ReportSheet from "@/app/components/ReportSheet";
import Screen from "@/app/components/Screen";

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
  // [IMP39] Older requests stored the category as a taxonomy slug
  // ("food_catering"); show its label from the shared taxonomy instead.
  const [categoryLabels, setCategoryLabels] = useState<Record<string, string>>({});

  async function refresh() {
    try {
      setRequest(await api.get<Partnership>(`/v1/partnership-requests/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("partnerships:detail.notFound"));
    }
  }

  useEffect(() => {
    api
      .get<{ categories: { slug: string; label: string }[] }>("/v1/listings/search-suggestions")
      .then((d) => setCategoryLabels(Object.fromEntries(d.categories.map((c) => [c.slug, c.label]))))
      .catch(() => undefined);
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

  if (error) return <Screen><h1>{t("partnerships:detail.notFound")}</h1><p>{error}</p></Screen>;
  if (!request) return <Screen><p>{t("common:state.loading")}</p></Screen>;

  const other = request.is_sender ? request.recipient_listing : request.sender_listing;
  const pending = request.state === "pending";

  const actionBlock = (
    <>
      {notice && <p className="vy-error">{notice}</p>}
      {request.is_sender && request.state === "declined" && <p className="vy-muted">{t("partnerships:detail.declinedCooldown")}</p>}
      {request.state === "restricted" && <p className="vy-muted">{t("partnerships:detail.restrictedNote")}</p>}

      <div className="vy-row vy-ctx-actions" style={{ flexWrap: "wrap" }}>
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
    </>
  );

  return (
    <Screen width="wide">
      <div className="vy-ctx">
      <div className="vy-ctx-grid">
      <div className="vy-ctx-main">
      <div>
        <span className="vy-badge vy-badge-member-provided">{t(`partnerships:state.${request.state}` as "state.pending")}</span>
        <h1 style={{ marginTop: 8 }}>{t("partnerships:detail.title")}</h1>
        <p className="vy-muted">{t("partnerships:detail.sent", { date: new Date(request.created_at).toLocaleDateString(i18n.language) })}</p>
      </div>
      </div>

      <aside className="vy-ctx-aside">
      {other && (
        <a className="vy-card" href={`/listings/${other.id}`} style={{ textDecoration: "none" }}>
          <span className="vy-muted" style={{ fontSize: 12 }}>{request.is_sender ? t("partnerships:detail.to") : t("partnerships:detail.from")}</span>
          <h2 style={{ fontSize: 17 }}>{other.name}</h2>
          <ReputationLine rep={other.reputation} />
        </a>
      )}
      <div className="vy-stack vy-ctx-wide-only">{actionBlock}</div>
      </aside>

      <div className="vy-ctx-after">
      <div className="vy-card vy-stack">
        {FIELD_LABELS.map(([field, key]) => (
          <div key={field}>
            <span className="vy-label">{t(`partnerships:${key}` as "compose.need")}</span>
            <p>{field === "category" ? categoryLabels[request.category] ?? request.category : String(request[field] ?? "")}</p>
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

      <div className="vy-ctx-contents vy-ctx-narrow-only">{actionBlock}</div>

      {request.state === "closed" && <ReviewComposer interactionKind="partnership" interactionId={id} />}
      <ReportSheet objectKind="partnership" objectId={id} />
      </div>
      </div>
      </div>
    </Screen>
  );
}
