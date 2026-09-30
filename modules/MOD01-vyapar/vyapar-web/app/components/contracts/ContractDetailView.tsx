"use client";

// [FE2 — imp-backend-d, research §8] Contract detail, presentational.
//
// Reading order: what the contract is and where it stands (title, the other
// person, state), then the one thing the viewer can do next as a "your turn"
// banner, then the stages as a vertical timeline — Not paid in yet → Paid in
// advance → Work sent → Paid, with Changes requested and In dispute — each
// row carrying at most ONE action for the person whose turn it is (Pay in
// advance · Send work · Approve and pay / Request changes). Money sits in a
// sticky right column on desktop; on a phone the current action is pinned in
// a footer that replaces the hub. Vocabulary follows GLOSSARY.md: "stage"
// not milestone, "paid in advance" not held/funded/escrow, "Paid" not
// released.
//
// Props in, callbacks out; the only state here is which inline note box is
// open and its text. Payments are a ledger (BLOCKER-01): the page says so,
// and says "test payments" whenever the Payment Bridge reported sandbox.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { AlertTriangle, Check, CheckCircle2, Clock, Flag, History, IndianRupee, ListChecks, Lock, MessageSquare, Send, Wallet } from "lucide-react";
import type { Contract, ContractEvent, Milestone, Timesheet, TimesheetInput } from "@/lib/sdk";
import { daysUntil, formatDate, formatDateTime, formatRupees } from "@/lib/format";
import { contractNeedsMe, counterpartOf, milestoneAction, milestoneTone, notFundedPaise, recentMondays, stateTone, timesheetNeedsMe, type Tone } from "./model";

export interface ContractDetailActions {
  onPropose: () => void;
  onAccept: () => void;
  onCancel: (reason?: string) => void;
  onComplete: () => void;
  onFund: (milestoneId: string) => void;
  onSubmit: (milestoneId: string, note?: string) => void;
  onApprove: (milestoneId: string) => void;
  onReject: (milestoneId: string, note: string) => void;
  onOpenDispute: (reason: string, milestoneId?: string | null) => void;
  onSubmitTimesheet: (input: TimesheetInput) => void;
  onApproveTimesheet: (timesheetId: string) => void;
  onRejectTimesheet: (timesheetId: string, note: string) => void;
}

export interface ContractDetailViewProps extends ContractDetailActions {
  contract: Contract;
  busy: boolean;
  error: string | null;
  /** true once the Payment Bridge said it is the development sandbox; null = not known yet. */
  sandbox: boolean | null;
  /** Rendered inside a split pane: no page-level title and no sticky phone footer. */
  embedded?: boolean;
}

type Open = { kind: "submit" | "reject" | "tsReject" | "dispute" | "end"; id?: string } | null;

function chipTone(tone: Tone): "action" | "done" | "warn" | "wait" | undefined {
  switch (tone) {
    case "action":
      return "action";
    case "done":
      return "done";
    case "warn":
      return "warn";
    case "held":
      return "wait";
    default:
      return undefined;
  }
}

function DotIcon({ tone }: { tone: Tone }) {
  if (tone === "done") return <Check size={13} strokeWidth={2.5} aria-hidden="true" />;
  if (tone === "warn") return <AlertTriangle size={12} strokeWidth={2.25} aria-hidden="true" />;
  if (tone === "held") return <Lock size={11} strokeWidth={2.25} aria-hidden="true" />;
  if (tone === "action") return <IndianRupee size={12} strokeWidth={2.5} aria-hidden="true" />;
  return null;
}

export default function ContractDetailView(props: ContractDetailViewProps) {
  const { contract: c, busy, error, sandbox, embedded } = props;
  const { t, i18n } = useTranslation(["contracts", "common"]);
  const lang = i18n.language;
  const money = (p: number) => formatRupees(p, lang);
  const [open, setOpen] = useState<Open>(null);
  const [text, setText] = useState("");
  const [disputeMs, setDisputeMs] = useState<string>("");
  const [week, setWeek] = useState<string>("");
  const [hours, setHours] = useState<string>("");
  const [tsNote, setTsNote] = useState("");

  const isClient = c.my_role === "client";
  const other = counterpartOf(c);
  const clientName = c.client_name ?? "";
  const providerName = c.provider_name ?? "";
  const toggle = (next: Open) => {
    setText("");
    setOpen((cur) => (cur && next && cur.kind === next.kind && cur.id === next.id ? null : next));
  };

  // ---- the one current action (for the phone footer) -----------------------
  const firstMs = c.milestones.find((m) => milestoneAction(c, m) !== null);
  const firstTs = c.timesheets.find((ts) => timesheetNeedsMe(c, ts));

  function actorName(e: ContractEvent): string {
    if (!e.actor_member_id) return t("contracts:actor.system");
    if (e.actor_member_id === c.client_member_id) return isClient ? t("contracts:actor.you") : clientName;
    if (e.actor_member_id === c.provider_member_id) return isClient ? providerName : t("contracts:actor.you");
    return t("contracts:actor.system");
  }

  function eventText(e: ContractEvent): string {
    const ms = c.milestones.find((m) => m.id === e.milestone_id);
    const amount = typeof e.data?.amount_paise === "number" ? money(e.data.amount_paise as number) : ms ? money(ms.amount_paise) : "";
    const key = `contracts:event.${e.type.replace(".", "_")}`;
    return t(key, { actor: actorName(e), title: ms?.title ?? "", amount, defaultValue: t("contracts:event.other") });
  }

  function milestoneStatusLine(m: Milestone): string | null {
    // before acceptance nobody is waiting on anybody for a stage yet
    if (c.state !== "active" && !["released", "approved"].includes(m.state)) return null;
    switch (m.state) {
      case "pending":
        return isClient ? null : t("contracts:action.waitFund", { name: clientName });
      case "funded":
        return isClient ? t("contracts:action.waitWork", { name: providerName }) : null;
      case "submitted": {
        if (!m.auto_release_at) return null;
        const count = daysUntil(m.auto_release_at);
        const date = formatDate(m.auto_release_at, lang);
        return isClient ? t("contracts:action.autoInClient", { count, date }) : t("contracts:action.autoIn", { count, date, name: clientName });
      }
      case "released":
      case "approved":
        return m.released_at ? t("contracts:action.paidOn", { date: formatDate(m.released_at, lang) }) : null;
      default:
        return null;
    }
  }

  const noteBox = (label: string, onSend: () => void, sendLabel: string, requireText = true, primary = true) => (
    <div className="vy-dl-panel">
      <textarea className="vy-textarea" rows={2} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} aria-label={label} placeholder={label} />
      <div className="vy-dl-actions">
        <button className={`vy-btn ${primary ? "vy-btn-primary" : "vy-btn-secondary"}`} disabled={busy || (requireText && !text.trim())} onClick={onSend}>
          {sendLabel}
        </button>
        <button className="vy-btn vy-btn-ghost" onClick={() => toggle(null)}>{t("contracts:detail.cancel")}</button>
      </div>
    </div>
  );

  function milestoneActions(m: Milestone) {
    const action = milestoneAction(c, m);
    // One primary per screen: the current step gets the brand fill; later
    // stages that could also be paid early get a quiet button.
    const primary = m.id === firstMs?.id ? "vy-btn vy-btn-primary" : "vy-btn vy-btn-secondary";
    if (action === "fund") {
      const resume = !!(m.funded_order_id && m.checkout_url);
      return (
        <button className={primary} style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => props.onFund(m.id)}>
          {resume ? t("contracts:action.continuePay") : t("contracts:action.fund", { amount: money(m.amount_paise) })}
        </button>
      );
    }
    if (action === "submit") {
      const isOpen = open?.kind === "submit" && open.id === m.id;
      return isOpen ? (
        noteBox(t("contracts:action.submitNote"), () => props.onSubmit(m.id, text.trim() || undefined), t("contracts:action.submitSend"), false)
      ) : (
        <button className={primary} style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => toggle({ kind: "submit", id: m.id })}>
          <Send size={16} strokeWidth={2} aria-hidden="true" /> {m.state === "rejected" ? t("contracts:action.submitAgain") : t("contracts:action.submit")}
        </button>
      );
    }
    if (action === "review") {
      const isOpen = open?.kind === "reject" && open.id === m.id;
      return (
        <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
          <div className="vy-dl-actions">
            <button className={primary} disabled={busy} onClick={() => props.onApprove(m.id)}>
              <Check size={16} strokeWidth={2.25} aria-hidden="true" /> {t("contracts:action.approve")}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={busy} aria-expanded={isOpen} onClick={() => toggle({ kind: "reject", id: m.id })}>
              {t("contracts:action.requestChanges")}
            </button>
          </div>
          {isOpen && noteBox(t("contracts:action.changesNote"), () => props.onReject(m.id, text.trim()), t("contracts:action.changesSend"), true, false)}
        </div>
      );
    }
    return null;
  }

  function timesheetRow(ts: Timesheet) {
    const needs = timesheetNeedsMe(c, ts);
    const isOpen = open?.kind === "tsReject" && open.id === ts.id;
    const tone: Tone = ts.state === "paid" ? "done" : needs ? "action" : ts.state === "rejected" ? "warn" : "held";
    return (
      <li key={ts.id} id={`ts-${ts.id}`} className="vy-dl-stage">
        <span className="vy-dl-stage-dot" data-tone={tone} aria-hidden="true">
          <DotIcon tone={tone} />
        </span>
        <div className="vy-dl-stage-body">
          <div className="vy-dl-stage-head">
            <strong className="vy-dl-stage-title">{t("contracts:hours.rowTitle", { date: formatDate(ts.week_start, lang), hours: ts.hours })}</strong>
            <strong className="vy-dl-stage-amt vy-num">{money(ts.amount_paise)}</strong>
          </div>
          <div className="vy-dl-tags">
            <span className="vy-dl-state" data-tone={chipTone(tone)}>{t(`contracts:ts.${ts.state}`)}</span>
          </div>
          {ts.note && <p className="vy-dl-stage-line">{ts.note}</p>}
          {ts.reject_note && <p className="vy-dl-stage-note">{t("contracts:action.changesAsked", { note: ts.reject_note })}</p>}
          {needs && (
            <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
              <div className="vy-dl-actions">
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => props.onApproveTimesheet(ts.id)}>
                  <Check size={16} strokeWidth={2.25} aria-hidden="true" /> {t("contracts:hours.approve")}
                </button>
                <button className="vy-btn vy-btn-ghost" disabled={busy} aria-expanded={isOpen} onClick={() => toggle({ kind: "tsReject", id: ts.id })}>
                  {t("contracts:hours.reject")}
                </button>
              </div>
              {isOpen && noteBox(t("contracts:hours.rejectNote"), () => props.onRejectTimesheet(ts.id, text.trim()), t("contracts:hours.reject"), true, false)}
            </div>
          )}
        </div>
      </li>
    );
  }

  // ---- contract-level banner: whose turn, or what happened ----------------
  let banner: React.ReactNode = null;
  if (c.state === "draft" && isClient) {
    banner = (
      <div className="vy-dl-turn" role="status">
        <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Send size={20} strokeWidth={1.75} /></span>
        <div className="vy-dl-row-body">
          <strong>{t("contracts:detail.draftTitle")}</strong>
          <span className="vy-dl-hint">{t("contracts:detail.draftClient", { name: other })}</span>
        </div>
        <div className="vy-dl-turn-actions">
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onPropose}>{t("contracts:detail.send", { name: other })}</button>
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => props.onCancel()}>{t("contracts:detail.discard")}</button>
        </div>
      </div>
    );
  } else if (c.state === "proposed") {
    // Calm offer card: one line, the facts, ONE full-width action (owner, 2026-09-30).
    banner = (
      <div className="vy-cl-offer" role="status">
        <strong>{isClient ? t("contracts:detail.proposedTitleClient") : t("contracts:detail.proposedTitleProvider", { name: other })}</strong>
        <dl className="vy-cl-offer-facts">
          <div>
            <dt>{t("contracts:detail.total")}</dt>
            <dd className="vy-num">{money(c.total_paise)}</dd>
          </div>
          {c.kind === "fixed" && (
            <div>
              <dt>{t("contracts:detail.milestones")}</dt>
              <dd className="vy-num">{c.milestones.length}</dd>
            </div>
          )}
        </dl>
        <span className="vy-dl-hint">{isClient ? t("contracts:detail.proposedClient", { name: other }) : t("contracts:detail.proposedProvider", { name: other })}</span>
        {!isClient && (
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onAccept}>{t("contracts:detail.accept")}</button>
        )}
        <button type="button" className="vy-cl-textbtn" disabled={busy} onClick={() => props.onCancel()}>
          {isClient ? t("contracts:detail.withdraw") : t("contracts:detail.decline")}
        </button>
      </div>
    );
  } else if (c.state === "disputed") {
    banner = (
      <p className="vy-dl-notice" data-tone="warn" role="status">
        <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
        <span>{t("contracts:detail.disputedBanner")}</span>
      </p>
    );
  } else if (c.state === "completed" && c.completed_at) {
    banner = (
      <p className="vy-dl-notice" data-tone="good">
        <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" />
        <span>
          {t("contracts:detail.completedOn", { date: formatDate(c.completed_at, lang) })}{" "}
          <Link className="vy-dl-link" href={`/enquiries/${c.enquiry_id}`}>{t("contracts:detail.reviewLink")}</Link>
        </span>
      </p>
    );
  } else if (c.state === "cancelled" && c.cancelled_at) {
    banner = (
      <p className="vy-dl-notice">
        <Clock size={18} strokeWidth={1.75} aria-hidden="true" />
        <span>
          {t("contracts:detail.cancelledOn", { date: formatDate(c.cancelled_at, lang) })}
          {c.cancel_reason ? ` ${c.cancel_reason}` : ""}
        </span>
      </p>
    );
  }

  // One line per action: a payment that went through (or failed) replaces
  // its own "payment started" line; only a still-pending one shows it.
  const settled = new Set(c.events.filter((e) => e.type === "milestone.funded" || e.type === "milestone.payment_failed").map((e) => e.milestone_id));
  const visibleEvents = c.events.filter((e) => !(e.type === "milestone.funding_started" && settled.has(e.milestone_id)));

  const usedWeeks = new Set(c.timesheets.filter((x) => x.state !== "rejected").map((x) => x.week_start));
  const weeks = recentMondays(6).filter((w) => !usedWeeks.has(w));
  const weekValue = week || weeks[0] || "";
  const canComplete = isClient && c.state === "active" && c.ledger.held_paise === 0 && c.ledger.released_paise > 0 && c.kind === "hourly";
  const canEnd = c.state === "active" && (isClient || c.ledger.held_paise === 0) && !c.milestones.some((m) => m.state === "submitted");
  const openDispute = c.disputes.find((d) => d.state === "open");
  const headTone = contractNeedsMe(c) ? "wait" : chipTone(stateTone(c.state));
  const paidStages = c.milestones.filter((m) => ["released", "approved"].includes(m.state)).length;

  return (
    <div className="vy-dl-page">
      <div className="vy-dl-head">
        <div className="vy-dl-tags">
          <span className="vy-dl-state" data-tone={headTone}>{contractNeedsMe(c) ? t("contracts:list.needsYou") : t(`contracts:state.${c.state}`)}</span>
        </div>
        {embedded ? <h2 className="vy-dl-thread-name">{c.title}</h2> : <h1>{c.title}</h1>}
        <p className="vy-dl-hint">{t(`contracts:kind.${c.kind}`)} · {t(`contracts:role.${c.my_role}`)}</p>
        <p className="vy-dl-thread-about">
          <span>{t("contracts:detail.with", { name: other })}</span>
          <span aria-hidden="true">·</span>
          <Link href={`/enquiries/${c.enquiry_id}`} className="vy-dl-inline-icon">
            <MessageSquare size={14} strokeWidth={2} aria-hidden="true" /> {t("contracts:detail.openThread")}
          </Link>
        </p>
        {c.description && <p className="vy-dl-hint">{c.description}</p>}
      </div>

      {banner}
      {error && (
        <p className="vy-dl-notice" data-tone="bad" role="alert">
          <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}

      <div className="vy-detail">
        <div className="vy-detail-main">
          {c.kind === "fixed" ? (
            <section className="vy-dl-sec" aria-labelledby="ms-title">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><ListChecks size={20} strokeWidth={1.75} /></span>
                <h2 id="ms-title" className="vy-card-title">{t("contracts:detail.milestones")}</h2>
                <span className="vy-dl-sec-hint">{t("contracts:detail.stagesHint", { paid: paidStages, total: c.milestones.length })}</span>
              </div>
              <ol className="vy-dl-stages">
                {c.milestones.map((m) => {
                  const raw = milestoneTone(c, m);
                  const tone: Tone = raw === "action" && m.id !== firstMs?.id ? "open" : raw;
                  const status = milestoneStatusLine(m);
                  return (
                    <li key={m.id} id={`ms-${m.id}`} className="vy-dl-stage">
                      <span className="vy-dl-stage-dot" data-tone={tone} aria-hidden="true">
                        <DotIcon tone={tone} />
                      </span>
                      <div className="vy-dl-stage-body">
                        <div className="vy-dl-stage-head">
                          <strong className="vy-dl-stage-title">{m.title}</strong>
                          <strong className="vy-dl-stage-amt vy-num">{money(m.amount_paise)}</strong>
                        </div>
                        <div className="vy-dl-tags">
                          <span className="vy-dl-state" data-tone={chipTone(tone)}>{t(`contracts:ms.${m.state}`)}</span>
                          {m.due_date && !["released", "approved", "refunded"].includes(m.state) && (
                            <span className="vy-dl-fine">{t("contracts:action.due", { date: formatDate(m.due_date, lang) })}</span>
                          )}
                        </div>
                        {m.submission_note && m.state === "submitted" && <p className="vy-dl-stage-note">{t("contracts:action.delivered", { note: m.submission_note })}</p>}
                        {m.reject_note && m.state === "rejected" && <p className="vy-dl-stage-note">{t("contracts:action.changesAsked", { note: m.reject_note })}</p>}
                        {status && <p className="vy-dl-stage-line">{status}</p>}
                        {milestoneActions(m)}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </section>
          ) : (
            <section className="vy-dl-sec" aria-labelledby="ts-title">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Clock size={20} strokeWidth={1.75} /></span>
                <h2 id="ts-title" className="vy-card-title">{t("contracts:detail.timesheets")}</h2>
                {c.hourly_rate_paise != null && (
                  <span className="vy-dl-sec-hint">{t("contracts:detail.rate", { amount: money(c.hourly_rate_paise), hours: c.weekly_hours_cap ?? "—" })}</span>
                )}
              </div>
              {c.timesheets.length === 0 ? (
                <p className="vy-dl-hint">{t("contracts:hours.none")}</p>
              ) : (
                <ol className="vy-dl-stages">{[...c.timesheets].sort((a, b) => b.week_start.localeCompare(a.week_start)).map((ts) => timesheetRow(ts))}</ol>
              )}
              {!isClient && c.state === "active" && weeks.length > 0 && (
                <div className="vy-dl-panel">
                  <span className="vy-label">{t("contracts:hours.log")}</span>
                  <div className="vy-field-pair">
                    <label className="vy-field">
                      <span className="vy-label">{t("contracts:hours.week")}</span>
                      <select className="vy-select" value={weekValue} onChange={(e) => setWeek(e.target.value)}>
                        {weeks.map((w) => (
                          <option key={w} value={w}>{formatDate(w, lang)}</option>
                        ))}
                      </select>
                    </label>
                    <label className="vy-field">
                      <span className="vy-label">{t("contracts:hours.hours")}</span>
                      <input className="vy-input" type="number" inputMode="decimal" min={0.5} step={0.5} max={c.weekly_hours_cap ?? 168} value={hours} onChange={(e) => setHours(e.target.value)} />
                    </label>
                  </div>
                  {c.weekly_hours_cap != null && <span className="vy-dl-fine">{t("contracts:hours.capHint", { hours: c.weekly_hours_cap })}</span>}
                  <textarea className="vy-textarea" rows={2} value={tsNote} onChange={(e) => setTsNote(e.target.value)} aria-label={t("contracts:hours.note")} placeholder={t("contracts:hours.note")} />
                  <button
                    className="vy-btn vy-btn-primary"
                    style={{ alignSelf: "flex-start" }}
                    disabled={busy || !weekValue || !(Number(hours) > 0)}
                    onClick={() => {
                      props.onSubmitTimesheet({ week_start: weekValue, hours: Number(hours), note: tsNote.trim() || null });
                      setHours("");
                      setTsNote("");
                      setWeek("");
                    }}
                  >
                    {t("contracts:hours.submit")}
                  </button>
                </div>
              )}
            </section>
          )}
        </div>

        <aside className="vy-detail-aside">
          <section className="vy-dl-sec" aria-labelledby="money-title">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Wallet size={20} strokeWidth={1.75} /></span>
              <h2 id="money-title" className="vy-card-title">{t("contracts:detail.money")}</h2>
              <span className="vy-dl-sec-hint">{t("contracts:detail.moneyHint")}</span>
            </div>
            <dl className="vy-dl-receipt vy-num">
              <dt>{t("contracts:detail.held")}</dt>
              <dd>{money(c.ledger.held_paise)}</dd>
              <dt>{t("contracts:detail.paid")}</dt>
              <dd>{money(c.ledger.released_paise)}</dd>
              {c.ledger.refunded_paise > 0 && (
                <>
                  <dt>{t("contracts:detail.refunded")}</dt>
                  <dd>{money(c.ledger.refunded_paise)}</dd>
                </>
              )}
              {c.ledger.fee_paise > 0 && (
                <>
                  <dt>{t("contracts:detail.fee")}</dt>
                  <dd>{money(c.ledger.fee_paise)}</dd>
                </>
              )}
              <dt>{c.kind === "hourly" ? t("contracts:detail.budgetLeft") : t("contracts:detail.notFunded")}</dt>
              <dd>{money(notFundedPaise(c))}</dd>
              <dt className="vy-dl-receipt-total">{t("contracts:detail.total")}</dt>
              <dd className="vy-dl-receipt-total"><strong>{money(c.total_paise)}</strong></dd>
            </dl>
            <p className="vy-dl-safety">
              <Lock size={13} strokeWidth={2} aria-hidden="true" />
              <span>
                {sandbox ? (
                  <>
                    <strong>{t("contracts:sandbox.title")}.</strong> {t("contracts:sandbox.body")}
                  </>
                ) : (
                  t("contracts:sandbox.recorded")
                )}
              </span>
            </p>
          </section>
          {canComplete && (
            <div className="vy-dl-page" style={{ gap: 6 }}>
              <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={props.onComplete}>{t("contracts:detail.complete")}</button>
              <span className="vy-dl-fine">{t("contracts:detail.completeHint")}</span>
            </div>
          )}
          {canEnd &&
            (open?.kind === "end" ? (
              noteBox(t("contracts:detail.endReason"), () => props.onCancel(text.trim() || undefined), t("contracts:detail.endConfirm"), false, false)
            ) : (
              <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => toggle({ kind: "end" })}>{t("contracts:detail.end")}</button>
            ))}
        </aside>

        {/* after the money on a phone; under the stages on desktop */}
        <div className="vy-detail-main">
          {c.disputes.length > 0 && (
            <section className="vy-dl-page" style={{ gap: 6 }}>
              {c.disputes.map((d) => (
                <p key={d.id} className="vy-dl-notice" data-tone={d.state === "open" ? "warn" : undefined}>
                  <Flag size={18} strokeWidth={1.75} aria-hidden="true" />
                  <span>
                    {t("contracts:dispute.opened", { date: formatDate(d.created_at, lang), reason: d.reason })} · {t(`contracts:dispute.state.${d.state}`, { defaultValue: d.state })}
                  </span>
                </p>
              ))}
            </section>
          )}
          {c.state === "active" &&
            !openDispute &&
            (open?.kind === "dispute" ? (
              <section className="vy-dl-sec" aria-labelledby="dispute-title">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile vy-dl-tile-amber" aria-hidden="true"><Flag size={20} strokeWidth={1.75} /></span>
                  <h2 id="dispute-title" className="vy-card-title">{t("contracts:dispute.title")}</h2>
                  <span className="vy-dl-sec-hint">{t("contracts:dispute.help")}</span>
                </div>
                <label className="vy-field">
                  <span className="vy-label">{t("contracts:dispute.reason")}</span>
                  <textarea className="vy-textarea" rows={3} maxLength={2000} value={text} onChange={(e) => setText(e.target.value)} placeholder={t("contracts:dispute.reasonPlaceholder")} />
                </label>
                {c.milestones.length > 0 && (
                  <label className="vy-field">
                    <span className="vy-label">{t("contracts:dispute.milestone")}</span>
                    <select className="vy-select" value={disputeMs} onChange={(e) => setDisputeMs(e.target.value)}>
                      <option value="">{t("contracts:dispute.any")}</option>
                      {c.milestones.map((m) => (
                        <option key={m.id} value={m.id}>{m.title}</option>
                      ))}
                    </select>
                  </label>
                )}
                <div className="vy-dl-actions">
                  <button className="vy-btn vy-btn-primary" disabled={busy || text.trim().length < 10} onClick={() => props.onOpenDispute(text.trim(), disputeMs || null)}>
                    {t("contracts:dispute.send")}
                  </button>
                  <button className="vy-btn vy-btn-ghost" onClick={() => toggle(null)}>{t("contracts:detail.cancel")}</button>
                </div>
              </section>
            ) : (
              <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => toggle({ kind: "dispute" })}>
                <Flag size={16} strokeWidth={2} aria-hidden="true" /> {t("contracts:dispute.open")}
              </button>
            ))}

          {c.events.length > 0 && (
            <section className="vy-dl-sec" aria-labelledby="history-title">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile" aria-hidden="true"><History size={20} strokeWidth={1.75} /></span>
                <h2 id="history-title" className="vy-card-title">{t("contracts:detail.activity")}</h2>
                <span className="vy-dl-sec-hint">{t("contracts:detail.activityHint")}</span>
              </div>
              <ol className="vy-dl-history">
                {visibleEvents.map((e) => (
                  <li key={e.id}>
                    <span>{eventText(e)}</span>
                    <time dateTime={e.created_at}>{formatDateTime(e.created_at, lang)}</time>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      </div>

      {/* Phone: the current step's action stays in reach while scrolling; it
          replaces the hub (vy-actionbar-in) and hides while a note box is open. */}
      {!embedded && !open && (firstMs || firstTs) && (
        <div className="vy-dl-footer vy-actionbar-in">
          {firstMs && milestoneAction(c, firstMs) === "fund" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => props.onFund(firstMs.id)}>
              {firstMs.funded_order_id && firstMs.checkout_url ? t("contracts:action.continuePay") : t("contracts:action.fund", { amount: money(firstMs.amount_paise) })}
            </button>
          )}
          {/* Approving releases money, so the footer never approves in one
              tap: it takes the person to the sent work to read first. */}
          {firstMs && milestoneAction(c, firstMs) !== "fund" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => document.getElementById(`ms-${firstMs.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}>
              {milestoneAction(c, firstMs) === "review" ? t("contracts:action.reviewWork") : firstMs.state === "rejected" ? t("contracts:action.submitAgain") : t("contracts:action.submit")}
            </button>
          )}
          {!firstMs && firstTs && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => document.getElementById(`ts-${firstTs.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}>
              {t("contracts:hours.review")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
