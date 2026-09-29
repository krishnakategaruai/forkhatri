"use client";

// [FE1 — 2026-09-29, critique N6] The terms of a proposal in one card —
// price, days, stages and the screening answers — so the person who pays
// never accepts terms they cannot see. One component, used on the
// applicants board's detail and at the top of the enquiry thread.
// Presentational: the numbers come in, nothing is fetched here.
import { useTranslation } from "react-i18next";
import { formatRupees } from "@/lib/money";

export interface ProposalTerms {
  bid_amount_paise?: number | null;
  bid_type?: string | null;
  timeline_days?: number | null;
  milestones?: { title: string; amount_paise: number; due_days?: number | null }[] | null;
  /** Each answer with the question as the poster wrote it (null when unknown). */
  screening_answers?: { question_id: string; question?: string | null; answer: string }[] | null;
}

/** True when there is anything to show (a price, days or stages). */
export function hasProposalTerms(p: ProposalTerms): boolean {
  return p.bid_amount_paise != null || p.timeline_days != null || (p.milestones?.length ?? 0) > 0;
}

export default function ProposalSummary({ terms, title }: { terms: ProposalTerms; title?: string }) {
  const { t, i18n } = useTranslation("hiring");
  const lang = i18n.language;
  const price =
    terms.bid_amount_paise != null
      ? terms.bid_type === "hourly"
        ? t("board.bidHourly", { amount: formatRupees(terms.bid_amount_paise, lang) })
        : t("board.bidFixed", { amount: formatRupees(terms.bid_amount_paise, lang) })
      : null;
  const stages = terms.milestones ?? [];
  const answers = (terms.screening_answers ?? []).filter((a) => a.answer);

  return (
    <section className="vy-card vy-card-nested vy-stack" style={{ gap: 12, padding: 16 }} aria-label={title ?? t("proposalCard.title")}>
      <span className="vy-fact-label">{title ?? t("proposalCard.title")}</span>
      {(price || terms.timeline_days != null) && (
        <div className="vy-facts" style={{ gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
          {price && (
            <div className="vy-fact">
              <span className="vy-fact-label">{t("board.price")}</span>
              <span className="vy-fact-value">{price}</span>
            </div>
          )}
          {terms.timeline_days != null && (
            <div className="vy-fact">
              <span className="vy-fact-label">{t("board.timeline")}</span>
              <span className="vy-fact-value">{t("proposal.days", { count: terms.timeline_days })}</span>
            </div>
          )}
        </div>
      )}
      {stages.length > 0 && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <span className="vy-fact-label">{t("proposal.milestones")}</span>
          <ol className="vy-milestone-list">
            {stages.map((m, i) => (
              <li key={i}>
                <span>
                  {i + 1}. {m.title}
                  {m.due_days ? ` · ${t("board.byDay", { count: m.due_days })}` : ""}
                </span>
                <strong style={{ color: "var(--text-primary)" }}>{formatRupees(m.amount_paise, lang)}</strong>
              </li>
            ))}
          </ol>
        </div>
      )}
      {answers.length > 0 && (
        <dl className="vy-qa" style={{ margin: 0 }}>
          {answers.map((s) => (
            <div key={s.question_id}>
              <dt>{s.question ?? t("proposalCard.question")}</dt>
              <dd>{s.answer}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
