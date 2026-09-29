"use client";

// [FE1 — 2026-09-28] Compare 2–4 applicants: a column per person, a row per
// attribute (research §3; the same matrix shape as service packages). Data
// from compareApplicants, in the order picked. The best value in rows where
// "best" is unambiguous (AI score, skills matched, days) is set in the
// primary ink — no colour, no badge. Each column ends with its actions.
import { useTranslation } from "react-i18next";
import type { AiShortlistItem, Applicant, ApplicantCompare } from "@/lib/sdk";
import { formatDateIN } from "@/lib/money";
import { bidLine } from "./ApplicantCard";

export default function CompareTable({
  data,
  aiById,
  nameOf,
  onShortlist,
  onHire,
}: {
  data: ApplicantCompare | null;
  aiById: ReadonlyMap<string, AiShortlistItem>;
  nameOf: (a: Applicant) => string;
  onShortlist: (a: Applicant) => void;
  onHire: (a: Applicant) => void;
}) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const lang = i18n.language;
  if (!data) return <div className="vy-skeleton" style={{ height: 240 }} aria-busy="true" />;
  const items = data.items;
  const hasAi = items.some((a) => aiById.has(a.enquiry_id));

  const best = (vals: (number | null)[], mode: "max" | "min") => {
    const nums = vals.filter((v): v is number => v !== null);
    if (nums.length < 2 || new Set(nums).size === 1) return null;
    return mode === "max" ? Math.max(...nums) : Math.min(...nums);
  };
  const scores = items.map((a) => aiById.get(a.enquiry_id)?.match_score ?? null);
  const matched = items.map((a) => a.matched_capability_labels.length);
  const days = items.map((a) => a.timeline_days);
  const bestScore = best(scores, "max");
  const bestMatched = best(matched, "max");
  const bestDays = best(days, "min");

  const questionIds = [...new Set(items.flatMap((a) => a.screening_answers.map((s) => s.question_id)))];
  const questionText = (id: string) => items.flatMap((a) => a.screening_answers).find((s) => s.question_id === id)?.question ?? id;

  const row = (label: string, cell: (a: Applicant, i: number) => React.ReactNode, show = true) =>
    show ? (
      <tr key={label}>
        <th scope="row">{label}</th>
        {items.map((a, i) => (
          <td key={a.enquiry_id}>{cell(a, i) ?? "—"}</td>
        ))}
      </tr>
    ) : null;

  return (
    <div className="vy-compare-wrap">
      <table className="vy-compare">
        <thead>
          <tr>
            <th scope="col" aria-label={t("hiring:board.attribute")} />
            {items.map((a) => (
              <th key={a.enquiry_id} scope="col">{nameOf(a)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {row(t("hiring:board.stageLabel"), (a) => t(`hiring:board.stage.${a.stage}`))}
          {row(
            t("hiring:board.match"),
            (a, i) => (scores[i] !== null ? <span className={scores[i] === bestScore ? "vy-compare-best" : undefined}>{scores[i]}/10</span> : null),
            hasAi,
          )}
          {row(
            t("hiring:board.skillsForThis"),
            (a, i) =>
              data.required_capability_labels.length ? (
                <span className={matched[i] === bestMatched ? "vy-compare-best" : undefined}>
                  {t("hiring:board.nOfM", { have: matched[i], total: data.required_capability_labels.length })}
                  {a.matched_capability_labels.length > 0 && <><br />{a.matched_capability_labels.join(", ")}</>}
                </span>
              ) : null,
          )}
          {row(t("hiring:board.price"), (a) => bidLine(t, a, lang), items.some((a) => a.bid_amount_paise != null))}
          {row(
            t("hiring:board.timeline"),
            (a, i) => (a.timeline_days != null ? <span className={days[i] === bestDays ? "vy-compare-best" : undefined}>{t("hiring:proposal.days", { count: a.timeline_days })}</span> : null),
            items.some((a) => a.timeline_days != null),
          )}
          {row(t("hiring:proposal.milestones"), (a) => (a.milestones.length ? t("hiring:board.milestones", { count: a.milestones.length }) : null), items.some((a) => a.milestones.length > 0))}
          {row(t("hiring:fields.experience"), (a) => (a.profile.experience_years != null ? t("hiring:apply.years", { count: a.profile.experience_years }) : null))}
          {row(t("hiring:board.where"), (a) => {
            const km = aiById.get(a.enquiry_id)?.distance_km;
            return km != null ? t("hiring:board.kmAway", { km: km < 10 ? km.toFixed(1) : Math.round(km) }) : a.profile.locality;
          })}
          {row(
            t("hiring:board.why"),
            (a) => {
              const r = aiById.get(a.enquiry_id)?.reasons.map((x) => x.text) ?? a.match_reasons;
              return r.length ? r.slice(0, 3).join("; ") : null;
            },
          )}
          {row(
            t("hiring:board.watchOut"),
            (a) => (aiById.get(a.enquiry_id)?.risks.map((x) => x.text) ?? a.match_risks ?? []).join("; ") || null,
            hasAi || items.some((a) => (a.match_risks?.length ?? 0) > 0),
          )}
          {questionIds.map((qid) => row(questionText(qid), (a) => a.screening_answers.find((s) => s.question_id === qid)?.answer ?? null))}
          {row(t("hiring:board.applied"), (a) => `${t(`hiring:board.via.${a.applied_via}`, { defaultValue: a.applied_via })} · ${formatDateIN(a.created_at, lang, false)}`)}
          <tr>
            <th scope="row" />
            {items.map((a) => (
              <td key={a.enquiry_id}>
                <div className="vy-stack" style={{ gap: 6 }}>
                  {a.stage === "new" && (
                    <button type="button" className="vy-btn vy-btn-secondary" style={{ padding: "8px 14px", fontSize: 13 }} onClick={() => onShortlist(a)}>
                      {t("hiring:board.shortlist")}
                    </button>
                  )}
                  {(a.stage === "new" || a.stage === "shortlisted") && (
                    <button type="button" className="vy-btn vy-btn-secondary" style={{ padding: "8px 14px", fontSize: 13 }} onClick={() => onHire(a)}>
                      {t("hiring:board.hire")}
                    </button>
                  )}
                </div>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
