"use client";

// [FE2 — imp-backend-d, research §8] Contract detail, presentational.
//
// Reading order: what the contract is and where it stands (title, the other
// person, state), then the one thing the viewer can do next, then the
// milestones as a vertical timeline — Not funded → Held → Submitted → Paid,
// with Changes requested and In dispute — each row carrying at most ONE
// action for the person whose turn it is (Fund · Submit work · Approve and
// pay / Request changes). Money sits in a sticky right column on desktop
// (Held · Paid · Not yet funded); on a phone the current action is pinned
// in a footer. Vocabulary follows the research: "Held", not escrow;
// "Submitted", not in review; "Paid", not released.
//
// Props in, callbacks out; the only state here is which inline note box is
// open and its text. Payments are a ledger (BLOCKER-01): the page says so,
// and says "test payments" whenever the Payment Bridge reported sandbox.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { Contract, ContractEvent, Milestone, Timesheet, TimesheetInput } from "@/lib/sdk";
import { daysUntil, formatDate, formatDateTime, formatRupees } from "@/lib/format";
import Icon from "@/app/components/Icon";
import {
  contractNeedsMe,
  counterpartOf,
  milestoneAction,
  milestoneTone,
  notFundedPaise,
  recentMondays,
  stateTone,
  timesheetNeedsMe,
} from "./model";

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
  /** Rendered inside a split pane: no page-level back link and no sticky phone footer. */
  embedded?: boolean;
}

type Open = { kind: "submit" | "reject" | "tsReject" | "dispute" | "end"; id?: string } | null;

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
    // before acceptance nobody is waiting on anybody for a milestone yet
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
        return isClient
          ? t("contracts:action.autoInClient", { count, date })
          : t("contracts:action.autoIn", { count, date, name: clientName });
      }
      case "released":
      case "approved":
        return m.released_at ? t("contracts:action.paidOn", { date: formatDate(m.released_at, lang) }) : null;
      default:
        return null;
    }
  }

  function milestoneActions(m: Milestone) {
    const action = milestoneAction(c, m);
    // One primary per screen: the current step gets the accent; later
    // milestones that could also be funded early get a quiet button.
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
        <div className="vy-stack" style={{ gap: 8 }}>
          <textarea className="vy-textarea" rows={2} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} aria-label={t("contracts:action.submitNote")} placeholder={t("contracts:action.submitNote")} />
          <div className="vy-row">
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => props.onSubmit(m.id, text.trim() || undefined)}>
              {t("contracts:action.submitSend")}
            </button>
            <button className="vy-btn vy-btn-ghost" onClick={() => toggle(null)}>{t("contracts:detail.cancel")}</button>
          </div>
        </div>
      ) : (
        <button className={primary} style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => toggle({ kind: "submit", id: m.id })}>
          {m.state === "rejected" ? t("contracts:action.submitAgain") : t("contracts:action.submit")}
        </button>
      );
    }
    if (action === "review") {
      const isOpen = open?.kind === "reject" && open.id === m.id;
      return (
        <div className="vy-stack" style={{ gap: 8 }}>
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            <button className={primary} disabled={busy} onClick={() => props.onApprove(m.id)}>
              {t("contracts:action.approve")}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={busy} aria-expanded={isOpen} onClick={() => toggle({ kind: "reject", id: m.id })}>
              {t("contracts:action.requestChanges")}
            </button>
          </div>
          {isOpen && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <textarea className="vy-textarea" rows={2} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} aria-label={t("contracts:action.changesNote")} placeholder={t("contracts:action.changesNote")} />
              <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy || !text.trim()} onClick={() => props.onReject(m.id, text.trim())}>
                {t("contracts:action.changesSend")}
              </button>
            </div>
          )}
        </div>
      );
    }
    return null;
  }

  function timesheetRow(ts: Timesheet) {
    const needs = timesheetNeedsMe(c, ts);
    const isOpen = open?.kind === "tsReject" && open.id === ts.id;
    const tone = ts.state === "paid" ? "done" : needs ? "action" : ts.state === "rejected" ? "warn" : "held";
    return (
      <li key={ts.id} id={`ts-${ts.id}`} className="vy-timeline-item">
        <span className="vy-dot" data-tone={tone} aria-hidden="true" />
        <div className="vy-timeline-body">
          <div className="vy-timeline-head">
            <strong>{t("contracts:hours.row", { date: formatDate(ts.week_start, lang), hours: ts.hours, amount: money(ts.amount_paise) })}</strong>
            <span className="vy-state-chip" data-tone={tone === "action" ? "action" : tone === "done" ? "done" : undefined}>
              {t(`contracts:ts.${ts.state}`)}
            </span>
          </div>
          {ts.note && <p style={{ fontSize: 14 }}>{ts.note}</p>}
          {ts.reject_note && <p className="vy-muted">{t("contracts:action.changesAsked", { note: ts.reject_note })}</p>}
          {needs && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <div className="vy-row" style={{ flexWrap: "wrap" }}>
                <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => props.onApproveTimesheet(ts.id)}>
                  {t("contracts:hours.approve")}
                </button>
                <button className="vy-btn vy-btn-ghost" disabled={busy} aria-expanded={isOpen} onClick={() => toggle({ kind: "tsReject", id: ts.id })}>
                  {t("contracts:hours.reject")}
                </button>
              </div>
              {isOpen && (
                <div className="vy-stack" style={{ gap: 8 }}>
                  <textarea className="vy-textarea" rows={2} value={text} onChange={(e) => setText(e.target.value)} aria-label={t("contracts:hours.rejectNote")} placeholder={t("contracts:hours.rejectNote")} />
                  <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy || !text.trim()} onClick={() => props.onRejectTimesheet(ts.id, text.trim())}>
                    {t("contracts:hours.reject")}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </li>
    );
  }

  // ---- contract-level banner -------------------------------------------------
  let banner: React.ReactNode = null;
  if (c.state === "draft" && isClient) {
    banner = (
      <div className="vy-card vy-stack" style={{ gap: 12 }}>
        <p>{t("contracts:detail.draftClient", { name: other })}</p>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onPropose}>{t("contracts:detail.send", { name: other })}</button>
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => props.onCancel()}>{t("contracts:detail.discard")}</button>
        </div>
      </div>
    );
  } else if (c.state === "proposed") {
    banner = (
      <div className="vy-card vy-stack" style={{ gap: 12 }}>
        <p>{isClient ? t("contracts:detail.proposedClient", { name: other }) : t("contracts:detail.proposedProvider", { name: other })}</p>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {!isClient && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={props.onAccept}>{t("contracts:detail.accept")}</button>
          )}
          <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => props.onCancel()}>
            {isClient ? t("contracts:detail.withdraw") : t("contracts:detail.decline")}
          </button>
        </div>
      </div>
    );
  } else if (c.state === "disputed") {
    banner = <p className="vy-sandbox-note" role="status"><Icon name="alert" size={16} /> <span>{t("contracts:detail.disputedBanner")}</span></p>;
  } else if (c.state === "completed" && c.completed_at) {
    banner = (
      <div className="vy-card vy-card-nested vy-stack" style={{ gap: 6 }}>
        <p>{t("contracts:detail.completedOn", { date: formatDate(c.completed_at, lang) })}</p>
        <Link className="vy-link-btn" href={`/enquiries/${c.enquiry_id}`}>{t("contracts:detail.reviewLink")}</Link>
      </div>
    );
  } else if (c.state === "cancelled" && c.cancelled_at) {
    banner = (
      <p className="vy-muted">
        {t("contracts:detail.cancelledOn", { date: formatDate(c.cancelled_at, lang) })}
        {c.cancel_reason ? ` ${c.cancel_reason}` : ""}
      </p>
    );
  }

  // One line per action: a payment that went through (or failed) replaces
  // its own "payment started" line; only a still-pending one shows it.
  const settled = new Set(
    c.events.filter((e) => e.type === "milestone.funded" || e.type === "milestone.payment_failed").map((e) => e.milestone_id),
  );
  const visibleEvents = c.events.filter((e) => !(e.type === "milestone.funding_started" && settled.has(e.milestone_id)));

  const usedWeeks = new Set(c.timesheets.filter((x) => x.state !== "rejected").map((x) => x.week_start));
  const weeks = recentMondays(6).filter((w) => !usedWeeks.has(w));
  const weekValue = week || weeks[0] || "";
  const canComplete = isClient && c.state === "active" && c.ledger.held_paise === 0 && c.ledger.released_paise > 0 && c.kind === "hourly";
  const canEnd = c.state === "active" && (isClient || c.ledger.held_paise === 0) && !c.milestones.some((m) => m.state === "submitted");
  const openDispute = c.disputes.find((d) => d.state === "open");

  return (
    <div className="vy-stack" style={{ gap: "var(--space-5)" }}>
      <div className="vy-stack" style={{ gap: 8 }}>
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
          <span className="vy-state-chip" data-tone={contractNeedsMe(c) ? "action" : stateTone(c.state) === "done" ? "done" : stateTone(c.state) === "warn" ? "warn" : undefined}>
            {t(`contracts:state.${c.state}`)}
          </span>
          <span className="vy-muted">{t(`contracts:kind.${c.kind}`)} · {t(`contracts:role.${c.my_role}`)}</span>
        </div>
        {embedded ? <h2>{c.title}</h2> : <h1>{c.title}</h1>}
        <p>
          {t("contracts:detail.with", { name: other })} ·{" "}
          <Link href={`/enquiries/${c.enquiry_id}`} className="vy-link-btn">{t("contracts:detail.openThread")}</Link>
        </p>
        {c.description && <p style={{ fontSize: 14 }}>{c.description}</p>}
      </div>

      {banner}
      {error && <p className="vy-error" role="alert">{error}</p>}

      <div className="vy-detail">
        <div className="vy-detail-main">
          {c.kind === "fixed" ? (
            <section className="vy-card vy-stack" style={{ gap: 16 }} aria-labelledby="ms-title">
              <h2 id="ms-title" className="vy-card-title">{t("contracts:detail.milestones")}</h2>
              <ol className="vy-timeline">
                {c.milestones.map((m) => {
                  const raw = milestoneTone(c, m);
                  const tone = raw === "action" && m.id !== firstMs?.id ? "open" : raw;
                  const status = milestoneStatusLine(m);
                  return (
                    <li key={m.id} id={`ms-${m.id}`} className="vy-timeline-item">
                      <span className="vy-dot" data-tone={tone} aria-hidden="true" />
                      <div className="vy-timeline-body">
                        <div className="vy-timeline-head">
                          <strong>{m.title}</strong>
                          <span className="vy-timeline-amount">{money(m.amount_paise)}</span>
                        </div>
                        <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                          <span className="vy-state-chip" data-tone={tone === "action" ? "action" : tone === "done" ? "done" : tone === "warn" ? "warn" : undefined}>
                            {t(`contracts:ms.${m.state}`)}
                          </span>
                          {m.due_date && !["released", "approved", "refunded"].includes(m.state) && (
                            <span className="vy-muted">{t("contracts:action.due", { date: formatDate(m.due_date, lang) })}</span>
                          )}
                        </div>
                        {m.submission_note && m.state === "submitted" && <p style={{ fontSize: 14 }}>{t("contracts:action.delivered", { note: m.submission_note })}</p>}
                        {m.reject_note && m.state === "rejected" && <p style={{ fontSize: 14 }}>{t("contracts:action.changesAsked", { note: m.reject_note })}</p>}
                        {status && <p className="vy-muted">{status}</p>}
                        {milestoneActions(m)}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </section>
          ) : (
            <section className="vy-card vy-stack" style={{ gap: 16 }} aria-labelledby="ts-title">
              <div className="vy-stack" style={{ gap: 4 }}>
                <h2 id="ts-title" className="vy-card-title">{t("contracts:detail.timesheets")}</h2>
                {c.hourly_rate_paise != null && (
                  <p className="vy-muted">{t("contracts:detail.rate", { amount: money(c.hourly_rate_paise), hours: c.weekly_hours_cap ?? "—" })}</p>
                )}
              </div>
              {c.timesheets.length === 0 ? (
                <p className="vy-muted">{t("contracts:hours.none")}</p>
              ) : (
                <ol className="vy-timeline">
                  {[...c.timesheets].sort((a, b) => b.week_start.localeCompare(a.week_start)).map((ts) => timesheetRow(ts))}
                </ol>
              )}
              {!isClient && c.state === "active" && weeks.length > 0 && (
                <div className="vy-card vy-card-nested vy-stack" style={{ gap: 12 }}>
                  <strong>{t("contracts:hours.log")}</strong>
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
                  {c.weekly_hours_cap != null && <span className="vy-muted">{t("contracts:hours.capHint", { hours: c.weekly_hours_cap })}</span>}
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
          <section className="vy-card vy-stack" style={{ gap: 12 }} aria-labelledby="money-title">
            <h2 id="money-title" className="vy-card-title">{t("contracts:detail.money")}</h2>
            <dl className="vy-ledger">
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
              <dt className="vy-ledger-total">{t("contracts:detail.total")}</dt>
              <dd className="vy-ledger-total">{money(c.total_paise)}</dd>
            </dl>
          </section>
          <p className="vy-sandbox-note">
            <Icon name="lock" size={15} style={{ marginTop: 2 }} />
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
          {canComplete && (
            <div className="vy-stack" style={{ gap: 6 }}>
              <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={props.onComplete}>{t("contracts:detail.complete")}</button>
              <span className="vy-muted">{t("contracts:detail.completeHint")}</span>
            </div>
          )}
          {canEnd &&
            (open?.kind === "end" ? (
              <div className="vy-stack" style={{ gap: 8 }}>
                <textarea className="vy-textarea" rows={2} value={text} onChange={(e) => setText(e.target.value)} aria-label={t("contracts:detail.endReason")} placeholder={t("contracts:detail.endReason")} />
                <div className="vy-row">
                  <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => props.onCancel(text.trim() || undefined)}>{t("contracts:detail.endConfirm")}</button>
                  <button className="vy-btn vy-btn-ghost" onClick={() => toggle(null)}>{t("contracts:detail.cancel")}</button>
                </div>
              </div>
            ) : (
              <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => toggle({ kind: "end" })}>{t("contracts:detail.end")}</button>
            ))}
        </aside>

        {/* after the money on a phone; under the milestones on desktop */}
        <div className="vy-detail-main">
          {/* Disputes: the open one is stated plainly; either side can report while active. */}
          {c.disputes.length > 0 && (
            <section className="vy-stack" style={{ gap: 6 }}>
              {c.disputes.map((d) => (
                <p key={d.id} className="vy-muted">
                  {t("contracts:dispute.opened", { date: formatDate(d.created_at, lang), reason: d.reason })} · {t(`contracts:dispute.state.${d.state}`, { defaultValue: d.state })}
                </p>
              ))}
            </section>
          )}
          {c.state === "active" && !openDispute && (
            open?.kind === "dispute" ? (
              <section className="vy-card vy-stack" style={{ gap: 12 }} aria-labelledby="dispute-title">
                <h2 id="dispute-title" className="vy-card-title">{t("contracts:dispute.title")}</h2>
                <p className="vy-muted">{t("contracts:dispute.help")}</p>
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
                <div className="vy-row">
                  <button className="vy-btn vy-btn-primary" disabled={busy || text.trim().length < 10} onClick={() => props.onOpenDispute(text.trim(), disputeMs || null)}>
                    {t("contracts:dispute.send")}
                  </button>
                  <button className="vy-btn vy-btn-ghost" onClick={() => toggle(null)}>{t("contracts:detail.cancel")}</button>
                </div>
              </section>
            ) : (
              <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => toggle({ kind: "dispute" })}>
                ⚑ {t("contracts:dispute.open")}
              </button>
            )
          )}

          {c.events.length > 0 && (
            <section className="vy-stack" style={{ gap: 10 }} aria-labelledby="history-title">
              <h2 id="history-title" className="vy-section-title">{t("contracts:detail.activity")}</h2>
              <ol className="vy-events">
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

      {/* Phone: the current step's action stays in reach while scrolling. */}
      {/* hidden while a note box is open, so it never sits over the form's own buttons */}
      {!embedded && !open && (firstMs || firstTs) && (
        <div className="vy-contract-footer">
          {firstMs && milestoneAction(c, firstMs) === "fund" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => props.onFund(firstMs.id)}>
              {firstMs.funded_order_id && firstMs.checkout_url ? t("contracts:action.continuePay") : t("contracts:action.fund", { amount: money(firstMs.amount_paise) })}
            </button>
          )}
          {/* Approving releases money, so the footer never approves in one
              tap: it takes the person to the submitted work to read first. */}
          {firstMs && milestoneAction(c, firstMs) !== "fund" && (
            <button
              className="vy-btn vy-btn-primary"
              disabled={busy}
              onClick={() => document.getElementById(`ms-${firstMs.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}
            >
              {milestoneAction(c, firstMs) === "review"
                ? t("contracts:action.reviewWork")
                : firstMs.state === "rejected"
                  ? t("contracts:action.submitAgain")
                  : t("contracts:action.submit")}
            </button>
          )}
          {!firstMs && firstTs && (
            <button
              className="vy-btn vy-btn-primary"
              disabled={busy}
              onClick={() => document.getElementById(`ts-${firstTs.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}
            >
              {t("contracts:hours.review")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
