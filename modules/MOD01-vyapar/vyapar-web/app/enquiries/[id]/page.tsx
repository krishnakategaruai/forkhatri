"use client";

// [TR023/TR024] Provider manages the Enquiry lifecycle (FR23); consent-
// based contact disclosure and blocking (FR24). One screen: thread
// messages, state, disclosed contacts (only once In Progress), lifecycle
// actions, block, and Refer to Counsel.
// Traces to: FR23, FR24, TR023, TR024
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import ReportSheet from "@/app/components/ReportSheet";
import ReviewComposer from "@/app/components/ReviewComposer";

interface Message {
  id: string;
  sender_id: string;
  body: string;
  system_note: boolean;
  created_at: string;
}

interface Contact {
  channel: string;
  value: string;
}

interface Enquiry {
  id: string;
  sender_id: string;
  provider_id: string;
  is_sender: boolean;
  action_type: string;
  state: string;
  delivered: boolean;
  safety_notice_seen: boolean;
  messages: Message[];
  disclosed_contacts: Contact[];
}

const STATE_KEY: Record<string, string> = {
  open: "stateOpen",
  awaiting_response: "stateAwaitingResponse",
  in_progress: "stateInProgress",
  resolved: "stateResolved",
  closed: "stateClosed",
  withdrawn: "stateWithdrawn",
  restricted: "stateRestricted",
};

export default function EnquiryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["enquiries", "common"]);
  const [enquiry, setEnquiry] = useState<Enquiry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setEnquiry(await api.get<Enquiry>(`/v1/enquiries/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("enquiries:detail.notFound"));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  if (error) return <main className="vy-shell"><h1>{t("enquiries:detail.notFound")}</h1><p>{error}</p></main>;
  if (!enquiry) return <main className="vy-shell"><p>{t("common:state.loading")}</p></main>;

  const otherParty = enquiry.is_sender ? enquiry.provider_id : enquiry.sender_id;

  return (
    <main className="vy-shell">
      <h1>{t(`enquiries:detail.${STATE_KEY[enquiry.state] ?? "stateOpen"}` as "detail.stateOpen")}</h1>

      <div className="vy-stack">
        {enquiry.messages.map((m) => (
          <div key={m.id} className="vy-card" style={{ background: m.sender_id === enquiry.sender_id ? "var(--surface-raised)" : "var(--accent-soft)" }}>
            <p>{m.body}</p>
          </div>
        ))}
      </div>

      {enquiry.disclosed_contacts.length > 0 && (
        <div className="vy-card vy-stack">
          <p className="vy-muted">{t("enquiries:detail.safetyNotice")}</p>
          <strong style={{ fontSize: 13 }}>{t("enquiries:detail.contactRevealed")}</strong>
          {enquiry.disclosed_contacts.map((c) => (
            <p key={c.channel}>{c.channel}: {c.value}</p>
          ))}
        </div>
      )}

      {!["closed", "withdrawn"].includes(enquiry.state) && (
        <div className="vy-row">
          {/* [FR43/TR043] a placeholder alone is never a valid accessible name */}
          <input className="vy-input" value={reply} onChange={(e) => setReply(e.target.value)} placeholder={t("enquiries:detail.replyPlaceholder")} aria-label={t("enquiries:detail.replyPlaceholder")} />
          <button
            className="vy-btn vy-btn-primary"
            disabled={!reply || busy || enquiry.state === "restricted"}
            onClick={() => act(async () => { await api.post(`/v1/enquiries/${id}/messages`, { body: reply }); setReply(""); })}
          >
            {t("enquiries:detail.reply")}
          </button>
        </div>
      )}

      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {!enquiry.is_sender && ["open", "awaiting_response"].includes(enquiry.state) && (
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/accept`))}>
            {t("enquiries:detail.accept")}
          </button>
        )}
        {!enquiry.is_sender && enquiry.state === "in_progress" && (
          <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/resolve`))}>
            {t("enquiries:detail.resolve")}
          </button>
        )}
        {["resolved", "in_progress"].includes(enquiry.state) && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/close`))}>
            {t("enquiries:detail.close")}
          </button>
        )}
        {enquiry.is_sender && !["closed", "withdrawn"].includes(enquiry.state) && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/withdraw`))}>
            {t("enquiries:detail.withdraw")}
          </button>
        )}
        {enquiry.state !== "restricted" && (
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/restrict`))}>
            {t("enquiries:detail.restrict")}
          </button>
        )}
        <button
          className="vy-btn vy-btn-ghost"
          disabled={busy}
          onClick={() => act(() => api.post("/v1/enquiries/block", { blocked_id: otherParty, enquiry_id: id }))}
        >
          {t("enquiries:detail.block")}
        </button>
        <button
          className="vy-btn vy-btn-ghost"
          disabled={busy}
          onClick={() => act(() => api.post(`/v1/enquiries/${id}/refer-to-counsel`, { problem_summary: enquiry.messages[0]?.body.slice(0, 400) ?? "Referral", consent: true }))}
        >
          {t("enquiries:detail.referToCounsel")}
        </button>
      </div>
      {/* [FR27] invite-gated review composer, in place on the thread once Resolved/Closed */}
      {["resolved", "closed"].includes(enquiry.state) && <ReviewComposer interactionKind="enquiry" interactionId={id} />}
      {/* [FR39] Block already has its own button on this screen, so the sheet doesn't offer it twice. */}
      <ReportSheet objectKind="enquiry" objectId={id} />
    </main>
  );
}
