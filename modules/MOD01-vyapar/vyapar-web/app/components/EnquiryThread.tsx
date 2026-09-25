"use client";

// ======================================================================
// [IMP33] EnquiryThread — the enquiry conversation, extracted from
// app/enquiries/[id]/page.tsx so it can render in two places.
//
// REQUIREMENT (owner, 2026-09-17): "Enquiries/Activity: list + detail
// split pane, so clicking a thread opens it beside the list instead of
// navigating away." 04-ui.md F4's own `--fk-bp-console` breakpoint says
// the same thing for the Admin console ("list + right detail pane").
//
// WHY EXTRACT RATHER THAN DUPLICATE: the alternative — a second,
// pane-only rendering of a thread — would be two implementations of
// FR23's lifecycle actions and FR24's consent-gated contact disclosure,
// drifting apart on the next change. This module has already been bitten
// by exactly that (the enquiries list once rendered raw enum values
// because it was a second, divergent rendering path; see the comment at
// the top of enquiries/mine/page.tsx). One component, two mounts.
//
// The route /enquiries/[id] still exists and still works — it is what a
// phone uses, what a notification links to, and what a shared URL opens.
// The split pane is purely an additional desktop presentation.
//
// Traces to: FR23, FR24, FR27, FR39, TR023, TR024; 04-ui.md F4;
// product-owner direction 2026-09-17.
//
// [IMP39 — desktop layout] When the thread has room (its OWN width ≥860px,
// a container query — not the viewport), it becomes a conversation column
// plus a sticky context aside: who the other party is, what the enquiry is
// about (linked), its state and dates, and the lifecycle actions. Inside
// the ≥1024px split pane on /enquiries/mine the thread is narrower than
// that, so it stays exactly the single column it was. Below the container
// breakpoint every wrapper is display:contents and the context card is
// display:none, so the phone rendering is unchanged. The context names come
// from the same list endpoint the inbox uses (target_name/counterpart_name
// are populated only there); the detail endpoint returns ids only.
// ======================================================================

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { api, ApiError, resolveAttachmentUrl } from "@/lib/api";
import ReportSheet from "@/app/components/ReportSheet";
import ReviewComposer from "@/app/components/ReviewComposer";
import { SkeletonGrid, EmptyState } from "@/app/components/States";

interface Message {
  id: string;
  sender_id: string;
  body: string;
  system_note: boolean;
  created_at: string;
  attachment_url: string | null;
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
  listing_id: string | null;
  opportunity_id: string | null;
  created_at: string;
  last_activity_at: string;
  action_type: string;
  state: string;
  delivered: boolean;
  safety_notice_seen: boolean;
  messages: Message[];
  disclosed_contacts: Contact[];
}

export const STATE_KEY: Record<string, string> = {
  open: "stateOpen",
  awaiting_response: "stateAwaitingResponse",
  in_progress: "stateInProgress",
  resolved: "stateResolved",
  closed: "stateClosed",
  withdrawn: "stateWithdrawn",
  restricted: "stateRestricted",
};

export default function EnquiryThread({
  id,
  onChanged,
}: {
  id: string;
  // The split pane needs to refresh its own list when a lifecycle action
  // changes a thread's state, or the chip counts beside it go stale.
  onChanged?: () => void;
}) {
  const { t, i18n } = useTranslation(["enquiries", "common"]);
  const [enquiry, setEnquiry] = useState<Enquiry | null>(null);
  // [IMP39] names for the desktop context aside (see header)
  const [names, setNames] = useState<{ target: string | null; counterpart: string | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setEnquiry(await api.get<Enquiry>(`/v1/enquiries/${id}`));
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("enquiries:detail.notFound"));
    }
  }

  // Callers that swap `id` in place (the split pane) pass a `key` so this
  // component remounts with fresh state — that is why there is no
  // setEnquiry(null) reset here, which would be a synchronous setState
  // inside an effect (react-hooks/set-state-in-effect).
  useEffect(() => {
    refresh();
    api
      .get<{ id: string; target_name: string | null; counterpart_name: string | null }[]>("/v1/enquiries/mine")
      .then((rows) => {
        const row = rows.find((r) => r.id === id);
        if (row) setNames({ target: row.target_name, counterpart: row.counterpart_name });
      })
      .catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      await refresh();
      onChanged?.();
    } finally {
      setBusy(false);
    }
  }

  if (error) return <EmptyState mark="⚠" title={t("enquiries:detail.notFound")} body={error} />;
  if (!enquiry) return <SkeletonGrid count={3} grid={false} />;

  const otherParty = enquiry.is_sender ? enquiry.provider_id : enquiry.sender_id;
  const stateLabel = t(`enquiries:detail.${STATE_KEY[enquiry.state] ?? "stateOpen"}` as "detail.stateOpen");
  const viewerId = enquiry.is_sender ? enquiry.sender_id : enquiry.provider_id;
  const targetHref = enquiry.listing_id
    ? `/listings/${enquiry.listing_id}`
    : enquiry.opportunity_id
    ? `/opportunities/${enquiry.opportunity_id}`
    : null;
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  return (
    <div className="vy-ctx vy-ctx-tight">
    <div className="vy-ctx-grid">
    <div className="vy-ctx-main">
      <h2>{stateLabel}</h2>

      <div className="vy-stack">
        {enquiry.messages.map((m) => (
          <div
            key={m.id}
            className={`vy-card vy-thread-msg${m.sender_id === viewerId ? " vy-thread-msg-mine" : ""}`}
            style={{ background: m.sender_id === enquiry.sender_id ? "var(--surface-raised)" : "var(--accent-soft)" }}
          >
            <p>{m.body}</p>
            {/* [Critique agent finding] UX12 names "attachments as file chips". */}
            {m.attachment_url && (
              <a href={resolveAttachmentUrl(m.attachment_url)} target="_blank" rel="noopener noreferrer" className="vy-chip" style={{ display: "inline-block", marginTop: 6, textDecoration: "none" }}>
                📎 {m.attachment_url.split("/").pop()}
              </a>
            )}
          </div>
        ))}
      </div>

      {enquiry.disclosed_contacts.length > 0 && (
        <div className="vy-card vy-card-nested vy-stack">
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

    </div>

    <aside className="vy-ctx-aside">
      {/* desktop-only context card; display:none in the single-column layout */}
      <div className="vy-card vy-ctx-card vy-ctx-wide-only">
        <span className="vy-ctx-heading">{t("enquiries:detail.contextTitle")}</span>
        <dl>
          {names?.counterpart && (
            <div>
              <dt>{t("enquiries:detail.withLabel")}</dt>
              <dd>{names.counterpart}</dd>
            </div>
          )}
          {names?.target && (
            <div>
              <dt>{t("enquiries:detail.aboutLabel")}</dt>
              <dd>
                {targetHref ? (
                  <Link href={targetHref} transitionTypes={["vy-forward"]}>{names.target} →</Link>
                ) : (
                  names.target
                )}
              </dd>
            </div>
          )}
          <div>
            <dt>{t("enquiries:detail.startedLabel")}</dt>
            <dd>{fmt(enquiry.created_at)}</dd>
          </div>
          <div>
            <dt>{t("enquiries:detail.lastActivityLabel")}</dt>
            <dd>{fmt(enquiry.last_activity_at)}</dd>
          </div>
        </dl>
        <p className="vy-muted">{enquiry.is_sender ? t("enquiries:detail.youSent") : t("enquiries:detail.youReceived")}</p>
      </div>
      <span className="vy-ctx-heading vy-ctx-wide-only">{t("common:layout.actions")}</span>
      <div className="vy-row vy-ctx-actions" style={{ flexWrap: "wrap" }}>
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
    </aside>

    <div className="vy-ctx-after">
      {/* [FR27] invite-gated review composer, in place on the thread once Resolved/Closed */}
      {["resolved", "closed"].includes(enquiry.state) && <ReviewComposer interactionKind="enquiry" interactionId={id} />}
      {/* [FR39] Block already has its own button here, so the sheet doesn't offer it twice. */}
      <ReportSheet objectKind="enquiry" objectId={id} />
    </div>
    </div>
    </div>
  );
}
