"use client";

// [FE2 — imp-backend-d createContract, research §8] Start a contract from an
// accepted enquiry.
//
// Minimal typing: the title, the kind, the total and the milestones come
// pre-filled from the conversation (the enquiry's subject and, for a
// proposal, the applicant's own bid and milestones), so the client usually
// only checks and sends. Fixed price: milestone rows (name · ₹ · optional
// due date) with a live "₹2,000 left to assign" counter — the server refuses
// milestones that don't add up to the total, so the form says so before
// anyone taps Send, and offers one-tap fixes ("Split evenly", "Put the rest
// in the last one"). Hourly: rate, weekly cap and a total budget; each
// approved week becomes a paid milestone.
//
// Desktop: form on the left, "How it works" in a sticky column beside it.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ContractCreateInput, ContractKind } from "@/lib/sdk";
import { formatRupees, paiseToInput, rupeesToPaise } from "@/lib/format";

export interface MilestoneDraft {
  title: string;
  amount: string;
  due: string;
}

export interface ContractDraft {
  title: string;
  description: string;
  kind: ContractKind;
  total: string;
  rate: string;
  cap: string;
  milestones: MilestoneDraft[];
}

export function emptyMilestone(): MilestoneDraft {
  return { title: "", amount: "", due: "" };
}

export default function ContractCreateForm({
  initial,
  counterpart,
  target,
  fromProposal,
  busy,
  error,
  onSubmit,
}: {
  initial: ContractDraft;
  counterpart: string;
  target: string | null;
  fromProposal: boolean;
  busy: boolean;
  error: string | null;
  onSubmit: (body: Omit<ContractCreateInput, "enquiry_id">) => void;
}) {
  const { t, i18n } = useTranslation(["contracts", "common"]);
  const [d, setD] = useState<ContractDraft>(initial);
  const [problem, setProblem] = useState<string | null>(null);
  const money = (p: number) => formatRupees(p, i18n.language);
  const set = (patch: Partial<ContractDraft>) => {
    setD((cur) => ({ ...cur, ...patch }));
    setProblem(null);
  };
  const setMs = (i: number, patch: Partial<MilestoneDraft>) =>
    set({ milestones: d.milestones.map((m, j) => (j === i ? { ...m, ...patch } : m)) });

  const totalPaise = rupeesToPaise(d.total) ?? 0;
  const assigned = useMemo(() => d.milestones.reduce((sum, m) => sum + (rupeesToPaise(m.amount) ?? 0), 0), [d.milestones]);
  const left = totalPaise - assigned;

  function splitEven() {
    const n = d.milestones.length;
    if (!n || totalPaise <= 0) return;
    // whole rupees each; any leftover rupees go to the last row
    const each = Math.floor(totalPaise / 100 / n) * 100;
    set({ milestones: d.milestones.map((m, i) => ({ ...m, amount: paiseToInput(i === n - 1 ? totalPaise - each * (n - 1) : each) })) });
  }

  function fillLast() {
    const n = d.milestones.length;
    if (!n) return;
    const others = d.milestones.slice(0, -1).reduce((s, m) => s + (rupeesToPaise(m.amount) ?? 0), 0);
    setMs(n - 1, { amount: paiseToInput(Math.max(0, totalPaise - others)) });
  }

  function fail(message: string): null {
    setProblem(message);
    return null;
  }

  function build(propose: boolean): Omit<ContractCreateInput, "enquiry_id"> | null {
    if (!d.title.trim()) return fail(t("contracts:new.errTitle"));
    if (d.kind === "fixed") {
      if (totalPaise <= 0) return fail(t("contracts:new.errTotal"));
      if (d.milestones.some((m) => !m.title.trim() || !((rupeesToPaise(m.amount) ?? 0) > 0))) return fail(t("contracts:new.errMilestone"));
      if (left !== 0) return fail(t("contracts:new.errSum"));
      return {
        title: d.title.trim(),
        description: d.description.trim() || null,
        kind: "fixed",
        total_paise: totalPaise,
        milestones: d.milestones.map((m) => ({ title: m.title.trim(), amount_paise: rupeesToPaise(m.amount) ?? 0, due_date: m.due || null })),
        propose,
      };
    }
    const rate = rupeesToPaise(d.rate) ?? 0;
    const cap = Number(d.cap);
    if (!(rate > 0) || !(cap > 0)) return fail(t("contracts:new.errRate"));
    if (totalPaise <= 0) return fail(t("contracts:new.errTotal"));
    return {
      title: d.title.trim(),
      description: d.description.trim() || null,
      kind: "hourly",
      total_paise: totalPaise,
      hourly_rate_paise: rate,
      weekly_hours_cap: cap,
      propose,
    };
  }

  function submit(propose: boolean) {
    const body = build(propose);
    if (body) onSubmit(body);
  }

  const today = new Date();
  const minDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <div className="vy-detail">
      <div className="vy-detail-main">
        <div className="vy-card vy-stack" style={{ gap: 20 }}>
          {fromProposal && <p className="vy-muted">{t("contracts:new.fromProposal", { name: counterpart })}</p>}
          <label className="vy-field">
            <span className="vy-label">{t("contracts:new.titleLabel")}</span>
            <input className="vy-input" maxLength={200} value={d.title} onChange={(e) => set({ title: e.target.value })} placeholder={t("contracts:new.titlePlaceholder")} />
          </label>
          <label className="vy-field">
            <span className="vy-label">{t("contracts:new.descLabel")}</span>
            <textarea className="vy-textarea" rows={3} maxLength={4000} value={d.description} onChange={(e) => set({ description: e.target.value })} placeholder={t("contracts:new.descPlaceholder")} />
          </label>

          <div className="vy-stack" style={{ gap: 8 }}>
            <span className="vy-label">{t("contracts:new.kindLabel")}</span>
            <div className="vy-segmented" role="group" aria-label={t("contracts:new.kindLabel")}>
              {(["fixed", "hourly"] as const).map((k) => (
                <button key={k} type="button" aria-pressed={d.kind === k} onClick={() => set({ kind: k })}>
                  {t(`contracts:kind.${k}`)}
                </button>
              ))}
            </div>
          </div>

          {d.kind === "fixed" ? (
            <>
              <label className="vy-field">
                <span className="vy-label">{t("contracts:new.totalLabel")}</span>
                <input className="vy-input" inputMode="decimal" value={d.total} onChange={(e) => set({ total: e.target.value })} />
              </label>

              <div className="vy-stack" style={{ gap: 10 }}>
                <div className="vy-stack" style={{ gap: 2 }}>
                  <span className="vy-label">{t("contracts:new.milestonesLabel")}</span>
                  <span className="vy-muted">{t("contracts:new.milestonesHint")}</span>
                </div>
                {d.milestones.map((m, i) => (
                  <div key={i} className="vy-ms-row">
                    <label className="vy-field">
                      <span className="vy-label">{t("contracts:new.msTitle", { n: i + 1 })}</span>
                      <input className="vy-input" maxLength={200} value={m.title} onChange={(e) => setMs(i, { title: e.target.value })} placeholder={i === 0 ? t("contracts:new.msTitlePlaceholder") : undefined} />
                    </label>
                    <label className="vy-field">
                      <span className="vy-label">{t("contracts:new.msAmount")}</span>
                      <input className="vy-input" inputMode="decimal" value={m.amount} onChange={(e) => setMs(i, { amount: e.target.value })} />
                    </label>
                    <label className="vy-field">
                      <span className="vy-label">{t("contracts:new.msDue")}</span>
                      <input className="vy-input" type="date" min={minDate} value={m.due} onChange={(e) => setMs(i, { due: e.target.value })} />
                    </label>
                    {d.milestones.length > 1 && (
                      <button type="button" className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => set({ milestones: d.milestones.filter((_, j) => j !== i) })}>
                        {t("contracts:new.removeMilestone")}
                      </button>
                    )}
                  </div>
                ))}
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                  {d.milestones.length < 10 && (
                    <button type="button" className="vy-btn vy-btn-secondary" onClick={() => set({ milestones: [...d.milestones, emptyMilestone()] })}>
                      + {t("contracts:new.addMilestone")}
                    </button>
                  )}
                  {totalPaise > 0 && d.milestones.length > 1 && (
                    <button type="button" className="vy-btn vy-btn-ghost" onClick={splitEven}>{t("contracts:new.splitEven")}</button>
                  )}
                  {totalPaise > 0 && left !== 0 && (
                    <button type="button" className="vy-btn vy-btn-ghost" onClick={fillLast}>{t("contracts:new.fillLast")}</button>
                  )}
                </div>
                {totalPaise > 0 && (
                  <div className="vy-remaining" role="status" aria-live="polite" data-ok={left === 0 || undefined} data-over={left < 0 || undefined}>
                    <span>
                      {left === 0
                        ? `✓ ${t("contracts:new.balanced")}`
                        : left > 0
                          ? t("contracts:new.remaining", { amount: money(left) })
                          : t("contracts:new.over", { amount: money(-left) })}
                    </span>
                    <span>{money(assigned)} / {money(totalPaise)}</span>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="vy-field-pair">
                <label className="vy-field">
                  <span className="vy-label">{t("contracts:new.rateLabel")}</span>
                  <input className="vy-input" inputMode="decimal" value={d.rate} onChange={(e) => set({ rate: e.target.value })} />
                </label>
                <label className="vy-field">
                  <span className="vy-label">{t("contracts:new.capLabel")}</span>
                  <input className="vy-input" type="number" min={1} max={168} value={d.cap} onChange={(e) => set({ cap: e.target.value })} />
                </label>
              </div>
              <label className="vy-field">
                <span className="vy-label">{t("contracts:new.budgetLabel")}</span>
                <input className="vy-input" inputMode="decimal" value={d.total} onChange={(e) => set({ total: e.target.value })} />
              </label>
            </>
          )}

          {(problem || error) && <p className="vy-error" role="alert">{problem ?? error}</p>}
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => submit(true)}>
              {busy ? t("contracts:new.sending") : t("contracts:new.send", { name: counterpart })}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => submit(false)}>
              {t("contracts:new.saveDraft")}
            </button>
          </div>
        </div>
      </div>
      <aside className="vy-detail-aside">
        <div className="vy-card vy-card-nested vy-stack" style={{ gap: 10 }}>
          <strong>{t("contracts:new.howTitle")}</strong>
          <ol className="vy-stack" style={{ gap: 8, margin: 0, paddingLeft: 18, color: "var(--text-secondary)", fontSize: 14 }}>
            <li>{t("contracts:new.how1", { name: counterpart })}</li>
            <li>{t("contracts:new.how2")}</li>
            <li>{t("contracts:new.how3", { name: counterpart })}</li>
            <li>{t("contracts:new.how4")}</li>
          </ol>
        </div>
        {target && <p className="vy-muted">{t("contracts:new.about", { target })}</p>}
        <p className="vy-sandbox-note">{t("contracts:sandbox.recorded")}</p>
      </aside>
    </div>
  );
}
