"use client";

// [FE1 — 2026-09-28] The poster's view of responses on their own
// opportunity page: counts per stage (New / Shortlisted / Hired /
// Declined) and one prominent link into the applicants board. With no
// responses yet it says so plainly instead of showing four zeros.
import { useTranslation } from "react-i18next";
import { APPLICANT_STAGES } from "@/lib/sdk";
import { useApplicantCounts } from "@/app/hooks/hiring";

export default function ApplicantsSummary({ opportunityId, type }: { opportunityId: string; type: string }) {
  const { t } = useTranslation("hiring");
  const counts = useApplicantCounts(opportunityId);
  const c = counts.data?.stage_counts;
  const total = c ? APPLICANT_STAGES.reduce((n, s) => n + (c[s] ?? 0), 0) : 0;
  const noun = type === "freelance" ? "proposals" : type === "employment" ? "applicants" : "responses";

  return (
    <div className="vy-card vy-stack vy-card-actions" style={{ gap: 12 }}>
      <div className="vy-stack" style={{ gap: 2 }}>
        <h2 className="vy-card-title">{t(`board.title.${noun}`)}</h2>
        {c && total === 0 && <p style={{ fontSize: 13 }}>{t("board.noneYetShort")}</p>}
      </div>
      {!c ? (
        <div className="vy-skeleton" style={{ height: 58 }} />
      ) : total > 0 ? (
        <div className="vy-stage-summary">
          {APPLICANT_STAGES.map((s) => (
            <div key={s}>
              <strong>{c[s] ?? 0}</strong>
              <span>{t(`board.stage.${s}`)}</span>
            </div>
          ))}
        </div>
      ) : null}
      <a className={`vy-btn ${c && c.new > 0 ? "vy-btn-primary" : "vy-btn-secondary"}`} href={`/opportunities/${opportunityId}/applicants`} style={{ textDecoration: "none", textAlign: "center" }}>
        {c && c.new > 0 ? t("board.reviewNew", { count: c.new }) : t(`board.open.${noun}`)}
      </a>
    </div>
  );
}
