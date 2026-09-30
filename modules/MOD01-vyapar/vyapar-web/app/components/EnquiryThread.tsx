"use client";

// ======================================================================
// [IMP33] EnquiryThread — one request's conversation, used by the route
// /enquiries/[id] (phone, notifications, shared links) and by the ≥1024px
// split pane on /enquiries/mine. One implementation, two mounts, so FR23's
// lifecycle actions and FR24's consent-gated contact disclosure never
// drift apart (this module was once bitten by a second rendering path
// showing raw enum values).
//
// [Design language 2026-09-29] Reads like a messaging thread people know
// (WhatsApp, Upwork messages), in this order:
//   1. who and what: avatar · the other person · the post or profile it is
//      about (linked) · a quiet state chip
//   2. what needs doing now: the receiver's Accept as a "your turn" banner;
//      the proposal's terms (critique N6, ProposalSummary) and the Call /
//      WhatsApp card (FE2) once both sides accepted
//   3. the messages as bubbles, mine on the right, with times in IST
//   4. the composer, sticky at the bottom on a phone (it hides the hub)
// Secondary and destructive actions (resolve, close, withdraw, restrict,
// block, refer) sit in a quiet "More" menu — never a wall of buttons.
// Desktop (own width ≥860px): a sticky context aside with the facts and the
// actions; inside the split pane the thread stays one column.
//
// Traces to: FR23, FR24, FR27, FR39, TR023, TR024; 04-ui.md F4.
// ======================================================================

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { Ban, Check, CheckCircle2, ChevronRight, LifeBuoy, Lock, MoreHorizontal, Paperclip, Send, ShieldAlert, Undo2, XCircle } from "lucide-react";
import { api, ApiError, resolveAttachmentUrl } from "@/lib/api";
import ReportSheet from "@/app/components/ReportSheet";
import ReviewComposer from "@/app/components/ReviewComposer";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import ContactActionsBlock from "@/app/components/contact/ContactActionsBlock";
import ContractEntry from "@/app/components/contracts/ContractEntry";
import TranslateLink from "@/app/components/respond/TranslateLink";
import ProposalSummary, { hasProposalTerms } from "@/app/components/applicants/ProposalSummary";
import { enquiryTone, ENQUIRY_STATE_KEY } from "@/app/components/enquiries/EnquiriesView";
import { formatDate, formatDateTime } from "@/lib/format";
// [Trust pack] the poster's replies pass the scam shield; the paid person is asked "paid on time?"
import { ScamShieldNote, scamFromError, useScamShield, type ScamFinding } from "@/app/components/trust/ScamShield";
import { PaidOnTimeForLink } from "@/app/components/trust/PaidOnTime";

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
  state_reason?: string | null;
  delivered: boolean;
  safety_notice_seen: boolean;
  messages: Message[];
  disclosed_contacts: Contact[];
  bid_amount_paise?: number | null;
  bid_type?: string | null;
  timeline_days?: number | null;
  milestones?: { title: string; amount_paise: number; due_days?: number | null }[] | null;
  // [FE1 — N5/N6] the proposal's screening answers and backend A's note language
  screening_answers?: { question_id: string; answer: string }[] | null;
  message_language?: string | null;
}

export const STATE_KEY = ENQUIRY_STATE_KEY;

function initial(name: string | null | undefined): string {
  const s = (name ?? "").trim();
  return s ? s.charAt(0).toUpperCase() : "?";
}

export default function EnquiryThread({
  id,
  onChanged,
  embedded = false,
}: {
  id: string;
  /** The split pane refreshes its list when a lifecycle action changes the state. */
  onChanged?: () => void;
  /** Rendered inside the split pane: no page-level title. */
  embedded?: boolean;
}) {
  const { t, i18n } = useTranslation(["enquiries", "common"]);
  const [enquiry, setEnquiry] = useState<Enquiry | null>(null);
  const [names, setNames] = useState<{ target: string | null; counterpart: string | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [more, setMore] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);
  // [FE1 — N6] the post's screening questions, so the proposal card shows
  // each answer under the question the poster wrote.
  const [questions, setQuestions] = useState<Record<string, string>>({});
  const oppId = enquiry?.opportunity_id ?? null;
  const hasAnswers = (enquiry?.screening_answers?.length ?? 0) > 0;
  // [Trust pack §1] The person who posted is replying to an applicant on
  // their own post: the reply is checked as they type, by the post's type.
  const posterReply = !!enquiry && !enquiry.is_sender && !!oppId;
  const [oppType, setOppType] = useState<string | null>(null);
  const [sendShield, setSendShield] = useState<ScamFinding | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  useEffect(() => {
    if (!oppId || (!hasAnswers && !posterReply)) return;
    api
      .get<{ type?: string; structured?: { screening_questions?: { id?: string; text: string }[] } | null }>(`/v1/opportunities/${oppId}`)
      .then((o) => {
        setOppType(o.type ?? null);
        setQuestions(Object.fromEntries((o.structured?.screening_questions ?? []).filter((q) => q.id).map((q) => [q.id as string, q.text])));
      })
      .catch(() => undefined);
  }, [oppId, hasAnswers, posterReply]);
  const liveShield = useScamShield(reply, "enquiry_reply", oppType, posterReply);
  const replyShield = liveShield ?? sendShield;

  async function refresh() {
    try {
      setEnquiry(await api.get<Enquiry>(`/v1/enquiries/${id}`));
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("enquiries:detail.notFound"));
    }
  }

  // Callers that swap `id` in place (the split pane) pass a `key`, so this
  // component remounts with fresh state.
  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    // The detail endpoint returns ids only; the names come from the list rows.
    Promise.all([
      api.get<{ id: string; target_name: string | null; counterpart_name: string | null }[]>("/v1/enquiries/mine?role=sent").catch(() => []),
      api.get<{ id: string; target_name: string | null; counterpart_name: string | null }[]>("/v1/enquiries/mine?role=received").catch(() => []),
    ]).then(([a, b]) => {
      const row = [...a, ...b].find((r) => r.id === id);
      if (row) setNames({ target: row.target_name, counterpart: row.counterpart_name });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // The "More" menu closes on an outside tap or Escape.
  useEffect(() => {
    if (!more) return;
    const onDown = (e: PointerEvent) => {
      if (!moreRef.current?.contains(e.target as Node)) setMore(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMore(false);
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [more]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setMore(false);
    try {
      await fn();
      await refresh();
      onChanged?.();
    } finally {
      setBusy(false);
    }
  }

  if (error) return <DealsEmpty tone="neutral" icon={<XCircle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("enquiries:detail.notFound")} body={error} />;
  if (!enquiry) return <SkeletonGrid count={3} grid={false} />;

  const otherParty = enquiry.is_sender ? enquiry.provider_id : enquiry.sender_id;
  const viewerId = enquiry.is_sender ? enquiry.sender_id : enquiry.provider_id;
  const lang = i18n.language;
  const stateLabel =
    enquiry.is_sender && enquiry.state === "closed" && enquiry.state_reason === "post_closed"
      ? t("enquiries:detail.statePostClosed")
      : t(`enquiries:detail.${STATE_KEY[enquiry.state] ?? "stateOpen"}` as "detail.stateOpen");
  const tone = enquiryTone(enquiry.state, enquiry.is_sender);
  const kindLabel = t(`enquiries:actionType.${enquiry.action_type}` as "actionType.enquire", { defaultValue: enquiry.action_type });
  const counterpart = names?.counterpart ?? t("enquiries:detail.them");
  const targetHref = enquiry.listing_id ? `/listings/${enquiry.listing_id}` : enquiry.opportunity_id ? `/opportunities/${enquiry.opportunity_id}` : null;
  const live = !["closed", "withdrawn"].includes(enquiry.state);
  const postClosed = enquiry.is_sender && enquiry.state === "closed" && enquiry.state_reason === "post_closed";
  const canAccept = !enquiry.is_sender && ["open", "awaiting_response"].includes(enquiry.state);
  const canResolve = !enquiry.is_sender && enquiry.state === "in_progress";
  const canClose = ["resolved", "in_progress"].includes(enquiry.state);
  const canWithdraw = enquiry.is_sender && live;
  const canRestrict = enquiry.state !== "restricted";
  const showContract = ["in_progress", "resolved", "closed"].includes(enquiry.state);
  const terms = hasProposalTerms(enquiry)
    ? { ...enquiry, screening_answers: (enquiry.screening_answers ?? []).map((s) => ({ ...s, question: questions[s.question_id] ?? null })) }
    : null;

  // The secondary actions, as one quiet menu. Rendered in the header row on
  // a phone and in the aside on desktop (one JSX value, two placements).
  const moreMenu = (
    <div className="vy-dl-more" ref={moreRef}>
      <button
        type="button"
        className="vy-iconbtn"
        aria-label={t("enquiries:detail.moreActions")}
        title={t("enquiries:detail.moreActions")}
        aria-haspopup="menu"
        aria-expanded={more}
        disabled={busy}
        onClick={() => setMore((v) => !v)}
      >
        <MoreHorizontal size={20} strokeWidth={2} aria-hidden="true" />
      </button>
      {more && (
        <div className="vy-dl-more-menu" role="menu">
          {canResolve && (
            <button type="button" role="menuitem" onClick={() => act(() => api.post(`/v1/enquiries/${id}/resolve`))}>
              <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.resolve")}
            </button>
          )}
          {canClose && (
            <button type="button" role="menuitem" onClick={() => act(() => api.post(`/v1/enquiries/${id}/close`))}>
              <Check size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.close")}
            </button>
          )}
          {canWithdraw && (
            <button type="button" role="menuitem" onClick={() => act(() => api.post(`/v1/enquiries/${id}/withdraw`))}>
              <Undo2 size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.withdraw")}
            </button>
          )}
          {canRestrict && (
            <button type="button" role="menuitem" onClick={() => act(() => api.post(`/v1/enquiries/${id}/restrict`))}>
              <ShieldAlert size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.restrict")}
            </button>
          )}
          <button type="button" role="menuitem" data-danger onClick={() => act(() => api.post("/v1/enquiries/block", { blocked_id: otherParty, enquiry_id: id }))}>
            <Ban size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.block")}
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => act(() => api.post(`/v1/enquiries/${id}/refer-to-counsel`, { problem_summary: enquiry.messages[0]?.body.slice(0, 400) ?? kindLabel, consent: true }))}
          >
            <LifeBuoy size={18} strokeWidth={1.75} aria-hidden="true" /> {t("enquiries:detail.referToCounsel")}
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="vy-ctx vy-ctx-tight vy-dl-thread">
      <div className="vy-ctx-grid">
        <div className="vy-ctx-main">
          {/* 1. who and what */}
          <div className="vy-dl-sec-head vy-dl-sec-head-3" style={{ alignItems: "center" }}>
            <span className="vy-dl-avatar vy-dl-avatar-lg" aria-hidden="true">{initial(names?.counterpart)}</span>
            <div className="vy-dl-row-body">
              {embedded ? <h2 className="vy-dl-thread-name">{counterpart}</h2> : <h1 className="vy-dl-thread-name">{counterpart}</h1>}
              <div className="vy-dl-thread-about">
                <span className="vy-dl-state" data-tone={tone}>{stateLabel}</span>
                <span>{kindLabel}</span>
                {names?.target && (
                  <>
                    <span aria-hidden="true">·</span>
                    {targetHref ? (
                      <Link href={targetHref} transitionTypes={["vy-forward"]}>{names.target}</Link>
                    ) : (
                      <span>{names.target}</span>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="vy-dl-sec-head-end vy-ctx-narrow-only">{moreMenu}</div>
          </div>

          {/* 2. what needs doing now */}
          {canAccept && (
            <div className="vy-dl-turn" role="status">
              <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true">
                <Check size={20} strokeWidth={2} />
              </span>
              <div className="vy-dl-row-body">
                <strong>{t("enquiries:detail.turnTitle", { name: counterpart })}</strong>
                <span className="vy-dl-hint">{t("enquiries:detail.turnBody")}</span>
              </div>
              <div className="vy-dl-turn-actions">
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/accept`))}>
                  {t("enquiries:detail.accept")}
                </button>
              </div>
            </div>
          )}

          {/* [Trust pack §2] the hired person is asked, once, whether they were paid on time */}
          <PaidOnTimeForLink link={`/enquiries/${id}`} />

          {/* phone: the way into the contract sits with the head, before the messages */}
          {showContract && (
            <div className="vy-ctx-narrow-only vy-dl-actions">
              <ContractEntry enquiryId={id} enquiryState={enquiry.state} opportunityId={enquiry.opportunity_id} />
            </div>
          )}

          {/* [Critique N6] the proposal's terms, so the payer never accepts terms they cannot see */}
          {terms && <ProposalSummary terms={terms} />}

          {/* [FE2] Call / WhatsApp once both sides accepted */}
          <ContactActionsBlock
            enquiryId={id}
            enquiryState={enquiry.state}
            disclosedContacts={enquiry.disclosed_contacts}
            safetyLine={t("enquiries:detail.safetyNotice")}
            fallback={
              enquiry.disclosed_contacts.length > 0 && (
                <div className="vy-dl-panel">
                  <span className="vy-label">{t("enquiries:detail.contactRevealed")}</span>
                  {enquiry.disclosed_contacts.map((c) => (
                    <p key={c.channel}>
                      <span className="vy-dl-hint">{t(`enquiries:channel.${c.channel}` as "channel.phone", { defaultValue: c.channel })}</span> · {c.value}
                    </p>
                  ))}
                  <p className="vy-dl-safety">
                    <Lock size={13} strokeWidth={2} aria-hidden="true" />
                    <span>{t("enquiries:detail.safetyNotice")}</span>
                  </p>
                </div>
              )
            }
          />

          {/* 3. the conversation */}
          <div className="vy-dl-msgs" aria-label={t("enquiries:detail.messagesLabel")}>
            {enquiry.messages.map((m) => {
              if (m.system_note) {
                return (
                  <p key={m.id} className="vy-dl-msg-sys">
                    {m.body}
                  </p>
                );
              }
              const mine = m.sender_id === viewerId;
              return (
                <div key={m.id} className={`vy-dl-msg${mine ? " vy-dl-msg-mine" : ""}`}>
                  <p>{m.body}</p>
                  {/* [FE1 — N5] only what the other person typed, only when the server knows its language */}
                  {!mine && <TranslateLink text={m.body} language={enquiry.message_language} />}
                  {m.attachment_url && (
                    <a href={resolveAttachmentUrl(m.attachment_url)} target="_blank" rel="noopener noreferrer" className="vy-dl-attach">
                      <Paperclip size={14} strokeWidth={2} aria-hidden="true" />
                      <span>{m.attachment_url.split("/").pop()}</span>
                    </a>
                  )}
                  <time className="vy-dl-msg-time" dateTime={m.created_at}>
                    {mine ? `${t("enquiries:detail.you")} · ` : ""}
                    {formatDateTime(m.created_at, lang)}
                  </time>
                </div>
              );
            })}
          </div>

          {/* 4. reply, or why you cannot */}
          {live ? (
            <form
              className="vy-dl-composer vy-actionbar-in"
              onSubmit={(e) => {
                e.preventDefault();
                if (!reply.trim() || busy || enquiry.state === "restricted" || replyShield) return;
                setSendError(null);
                void act(async () => {
                  try {
                    await api.post(`/v1/enquiries/${id}/messages`, { body: reply.trim() });
                    setReply("");
                  } catch (err) {
                    // [Trust pack §1] 422 seeker_charge_not_allowed lands under the reply, calmly
                    const scam = scamFromError(err);
                    if (scam) setSendShield(scam);
                    else setSendError(err instanceof ApiError ? String(err.detail) : t("common:state.actionFailed"));
                  }
                });
              }}
            >
              {(replyShield || sendError) && (
                <div className="vy-dl-composer-note">
                  <ScamShieldNote finding={replyShield} id={`shield-${id}`} />
                  {sendError && !replyShield && (
                    <p className="vy-error" role="alert">
                      {sendError}
                    </p>
                  )}
                </div>
              )}
              {/* [FR43/TR043] a placeholder alone is never a valid accessible name */}
              <input
                className="vy-input"
                value={reply}
                onChange={(e) => {
                  setReply(e.target.value);
                  setSendShield(null);
                  setSendError(null);
                }}
                aria-describedby={replyShield ? `shield-${id}` : undefined}
                placeholder={enquiry.state === "restricted" ? t("enquiries:detail.restrictedLine") : t("enquiries:detail.replyPlaceholder")}
                aria-label={t("enquiries:detail.replyPlaceholder")}
                disabled={enquiry.state === "restricted"}
                maxLength={1000}
              />
              <button type="submit" className="vy-btn vy-btn-primary vy-dl-composer-send" disabled={!reply.trim() || busy || enquiry.state === "restricted" || !!replyShield} aria-label={t("enquiries:detail.reply")} title={t("enquiries:detail.reply")}>
                <Send size={18} strokeWidth={2} aria-hidden="true" />
              </button>
            </form>
          ) : postClosed ? (
            // [Trust pack §3] the post closed before an answer: said kindly, never "rejected"
            <div className="vy-dl-thread-closed vy-postclosed">
              <p>{t("enquiries:detail.postClosedLine")}</p>
              <Link href="/" transitionTypes={["vy-forward"]}>{t("enquiries:detail.postClosedSimilar")}</Link>
            </div>
          ) : (
            <p className="vy-dl-thread-closed">{t("enquiries:detail.closedLine")}</p>
          )}
        </div>

        <aside className="vy-ctx-aside">
          <div className="vy-card vy-ctx-card vy-ctx-wide-only">
            <div className="vy-dl-actions" style={{ justifyContent: "space-between" }}>
              <span className="vy-ctx-heading">{t("enquiries:detail.contextTitle")}</span>
              {moreMenu}
            </div>
            <dl>
              <div>
                <dt>{t("enquiries:detail.withLabel")}</dt>
                <dd>{counterpart}</dd>
              </div>
              {names?.target && (
                <div>
                  <dt>{t("enquiries:detail.aboutLabel")}</dt>
                  <dd>
                    {targetHref ? (
                      <Link href={targetHref} transitionTypes={["vy-forward"]} className="vy-dl-inline-icon">
                        {names.target} <ChevronRight size={14} strokeWidth={2} aria-hidden="true" />
                      </Link>
                    ) : (
                      names.target
                    )}
                  </dd>
                </div>
              )}
              <div>
                <dt>{t("enquiries:detail.startedLabel")}</dt>
                <dd>{formatDate(enquiry.created_at, lang)}</dd>
              </div>
              <div>
                <dt>{t("enquiries:detail.lastActivityLabel")}</dt>
                <dd>{formatDate(enquiry.last_activity_at, lang)}</dd>
              </div>
            </dl>
            <p className="vy-dl-fine">{enquiry.is_sender ? t("enquiries:detail.youSent") : t("enquiries:detail.youReceived")}</p>
          </div>

          {/* desktop: the primary things to do (the quiet menu sits in the card above) */}
          {(showContract || canResolve) && (
            <div className="vy-ctx-wide-only vy-dl-actions">
              {showContract && <ContractEntry enquiryId={id} enquiryState={enquiry.state} opportunityId={enquiry.opportunity_id} />}
              {canResolve && (
                <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act(() => api.post(`/v1/enquiries/${id}/resolve`))}>
                  {t("enquiries:detail.resolve")}
                </button>
              )}
            </div>
          )}
        </aside>

        <div className="vy-ctx-after">
          {/* [FR27] invite-gated review composer, in place once Resolved/Closed */}
          {["resolved", "closed"].includes(enquiry.state) && <ReviewComposer interactionKind="enquiry" interactionId={id} />}
          {/* [FR39] Block has its own place in the menu, so the sheet doesn't offer it twice. */}
          <ReportSheet objectKind="enquiry" objectId={id} />
        </div>
      </div>
    </div>
  );
}
