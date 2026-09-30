"use client";

// [FE2 — imp-backend-d createContract, research §8] Start a contract from an
// accepted request.
//
// Minimal typing: the title, the kind, the total and the stages come
// pre-filled from the conversation (the request's subject and, for a
// proposal, the professional's own price and stages), so the client usually
// only checks and sends. Fixed price: stage rows (name · ₹ · optional due
// date) with a live "₹2,000 left to assign" line — the server refuses stages
// that don't add up to the total, so the form says so before anyone taps
// Send, and offers one-tap fixes ("Split evenly", "Put the rest in the last
// one"). Hourly: rate, weekly cap and a total budget; each approved week
// becomes a paid stage.
//
// [Design language 2026-09-29] Three section cards, each with its icon
// tile and one-line hint: the work · how you pay · the stages. Desktop: the
// form on the left, "How it works" sticky beside it. One filled button.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertTriangle, CheckCircle2, ClipboardList, IndianRupee, ListChecks, Plus, X } from "lucide-react";
import type { ContractCreateInput, ContractKind } from "@/lib/sdk";
import { formatRupees, paiseToInput, rupeesToPaise } from "@/lib/format";
import DisabledReason from "@/app/components/DisabledReason";

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
  const setMs = (i: number, patch: Partial<MilestoneDraft>) => set({ milestones: d.milestones.map((m, j) => (j === i ? { ...m, ...patch } : m)) });

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

  // What still blocks Send, in words (critique P2): shown under the button.
  const blocker = !d.title.trim()
    ? t("contracts:new.errTitle")
    : d.kind === "fixed"
      ? totalPaise <= 0
        ? t("contracts:new.errTotal")
        : d.milestones.some((m) => !m.title.trim() || !((rupeesToPaise(m.amount) ?? 0) > 0))
          ? t("contracts:new.errMilestone")
          : left !== 0
            ? t("contracts:new.errSum")
            : null
      : !((rupeesToPaise(d.rate) ?? 0) > 0) || !(Number(d.cap) > 0)
        ? t("contracts:new.errRate")
        : totalPaise <= 0
          ? t("contracts:new.errTotal")
          : null;

  const today = new Date();
  const minDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <div className="vy-detail">
      <div className="vy-detail-main">
        {fromProposal && (
          <p className="vy-dl-notice">
            <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" />
            <span>{t("contracts:new.fromProposal", { name: counterpart })}</span>
          </p>
        )}

        <section className="vy-dl-sec" aria-labelledby="cn-work">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true">
              <ClipboardList size={20} strokeWidth={1.75} />
            </span>
            <h2 id="cn-work" className="vy-card-title">{t("contracts:new.secWork")}</h2>
            <span className="vy-dl-sec-hint">{target ? t("contracts:new.about", { target }) : t("contracts:new.secWorkHint")}</span>
          </div>
          <label className="vy-field">
            <span className="vy-label">{t("contracts:new.titleLabel")}</span>
            <input className="vy-input" maxLength={200} value={d.title} onChange={(e) => set({ title: e.target.value })} placeholder={t("contracts:new.titlePlaceholder")} />
          </label>
          <label className="vy-field">
            <span className="vy-label">{t("contracts:new.descLabel")}</span>
            <textarea className="vy-textarea" rows={3} maxLength={4000} value={d.description} onChange={(e) => set({ description: e.target.value })} placeholder={t("contracts:new.descPlaceholder")} />
          </label>
        </section>

        <section className="vy-dl-sec" aria-labelledby="cn-pay">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true">
              <IndianRupee size={20} strokeWidth={1.75} />
            </span>
            <h2 id="cn-pay" className="vy-card-title">{t("contracts:new.kindLabel")}</h2>
            <span className="vy-dl-sec-hint">{t("contracts:new.kindHint")}</span>
          </div>
          <div className="vy-segmented vy-dl-tabs" role="group" aria-label={t("contracts:new.kindLabel")}>
            {(["fixed", "hourly"] as const).map((k) => (
              <button key={k} type="button" aria-pressed={d.kind === k} onClick={() => set({ kind: k })}>
                {t(`contracts:kind.${k}`)}
              </button>
            ))}
          </div>
          {d.kind === "fixed" ? (
            <label className="vy-field">
              <span className="vy-label">{t("contracts:new.totalLabel")}</span>
              <input className="vy-input" inputMode="decimal" value={d.total} onChange={(e) => set({ total: e.target.value })} placeholder="45,000" />
            </label>
          ) : (
            <>
              <div className="vy-field-pair">
                <label className="vy-field">
                  <span className="vy-label">{t("contracts:new.rateLabel")}</span>
                  <input className="vy-input" inputMode="decimal" value={d.rate} onChange={(e) => set({ rate: e.target.value })} placeholder="800" />
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
        </section>

        {d.kind === "fixed" && (
          <section className="vy-dl-sec" aria-labelledby="cn-stages">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true">
                <ListChecks size={20} strokeWidth={1.75} />
              </span>
              <h2 id="cn-stages" className="vy-card-title">{t("contracts:new.milestonesLabel")}</h2>
              <span className="vy-dl-sec-hint">{t("contracts:new.milestonesHint")}</span>
            </div>
            {d.milestones.map((m, i) => (
              <div key={i} className="vy-dl-panel">
                <div className="vy-dl-actions" style={{ justifyContent: "space-between" }}>
                  <span className="vy-label">{t("contracts:new.msTitle", { n: i + 1 })}</span>
                  {d.milestones.length > 1 && (
                    <button type="button" className="vy-iconbtn" aria-label={t("contracts:new.removeMilestoneN", { n: i + 1 })} title={t("contracts:new.removeMilestone")} onClick={() => set({ milestones: d.milestones.filter((_, j) => j !== i) })}>
                      <X size={18} strokeWidth={2} aria-hidden="true" />
                    </button>
                  )}
                </div>
                <input className="vy-input" maxLength={200} value={m.title} aria-label={t("contracts:new.msName")} onChange={(e) => setMs(i, { title: e.target.value })} placeholder={i === 0 ? t("contracts:new.msTitlePlaceholder") : t("contracts:new.msName")} />
                <div className="vy-field-pair">
                  <label className="vy-field">
                    <span className="vy-label">{t("contracts:new.msAmount")}</span>
                    <input className="vy-input" inputMode="decimal" value={m.amount} onChange={(e) => setMs(i, { amount: e.target.value })} />
                  </label>
                  <label className="vy-field">
                    <span className="vy-label">{t("contracts:new.msDue")}</span>
                    <input className="vy-input" type="date" min={minDate} value={m.due} onChange={(e) => setMs(i, { due: e.target.value })} />
                  </label>
                </div>
              </div>
            ))}
            <div className="vy-dl-actions">
              {d.milestones.length < 10 && (
                <button type="button" className="vy-btn vy-btn-secondary" onClick={() => set({ milestones: [...d.milestones, emptyMilestone()] })}>
                  <Plus size={16} strokeWidth={2} aria-hidden="true" /> {t("contracts:new.addMilestone")}
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
              <div className="vy-dl-notice" data-tone={left === 0 ? "good" : left < 0 ? "bad" : "warn"} role="status" aria-live="polite">
                {left === 0 ? <CheckCircle2 size={18} strokeWidth={1.75} aria-hidden="true" /> : <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />}
                <span style={{ flex: 1 }}>
                  {left === 0 ? t("contracts:new.balanced") : left > 0 ? t("contracts:new.remaining", { amount: money(left) }) : t("contracts:new.over", { amount: money(-left) })}
                </span>
                <span className="vy-dl-row-amount" style={{ fontSize: "var(--type-sm)" }}>
                  {money(assigned)} / {money(totalPaise)}
                </span>
              </div>
            )}
          </section>
        )}

        {(problem || error) && (
          <p className="vy-dl-notice" data-tone="bad" role="alert">
            <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
            <span>{problem ?? error}</span>
          </p>
        )}
        <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
          <div className="vy-dl-actions">
            <button className="vy-btn vy-btn-primary" aria-describedby={blocker ? "cn-why" : undefined} disabled={busy || !!blocker} onClick={() => submit(true)}>
              {busy ? t("contracts:new.sending") : t("contracts:new.send", { name: counterpart })}
            </button>
            <button className="vy-btn vy-btn-ghost" disabled={busy || !d.title.trim()} onClick={() => submit(false)}>
              {t("contracts:new.saveDraft")}
            </button>
          </div>
          <DisabledReason id="cn-why" show={!!blocker && !busy}>{blocker}</DisabledReason>
        </div>
      </div>

      <aside className="vy-detail-aside">
        <div className="vy-dl-sec">
          <div className="vy-dl-sec-head">
            <span className="vy-dl-tile" aria-hidden="true">
              <ListChecks size={20} strokeWidth={1.75} />
            </span>
            <h2 className="vy-card-title">{t("contracts:new.howTitle")}</h2>
            <span className="vy-dl-sec-hint">{t("contracts:new.howHint")}</span>
          </div>
          <ol className="vy-dl-stages">
            {[t("contracts:new.how1", { name: counterpart }), t("contracts:new.how2"), t("contracts:new.how3", { name: counterpart }), t("contracts:new.how4")].map((line, i) => (
              <li key={i} className="vy-dl-stage">
                <span className="vy-dl-stage-dot" aria-hidden="true">
                  <span style={{ fontSize: "var(--type-xs)" }}>{i + 1}</span>
                </span>
                <div className="vy-dl-stage-body">
                  <span className="vy-dl-stage-line">{line}</span>
                </div>
              </li>
            ))}
          </ol>
          <p className="vy-dl-fine">{t("contracts:sandbox.recorded")}</p>
        </div>
      </aside>
    </div>
  );
}
