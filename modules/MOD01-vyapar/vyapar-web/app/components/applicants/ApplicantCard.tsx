"use client";

// [FE1 — 2026-09-28] One applicant, as the poster scans a list (research
// §3): who (name, verified, earned badges), how far and how experienced,
// their terms for a proposal (price, days, milestones), the match — the
// AI's 1–10 with its top reasons and one risk, or else the count-based
// "matches n of m skills" line, never a percentage — and the actions for
// the current stage. Presentational: data in, events out.
import { useTranslation } from "react-i18next";
import type { AiShortlistItem, Applicant, Badge, ContactAction } from "@/lib/sdk";
import ApplicantContact from "./ApplicantContact";

// AI reasons/risks about skills would repeat (or contradict) the one verdict line.
const SKILL_CODES = ["capability_fit", "no_capability_overlap", "partial_capability_overlap"];
import { formatDateIN, formatRupees } from "@/lib/money";

export interface ApplicantCardProps {
  a: Applicant;
  name: string;
  ai?: AiShortlistItem;
  badges: Badge[];
  selected: boolean;
  comparing: boolean;
  compareFull: boolean;
  confirmingHire: boolean;
  busy: boolean;
  opportunityType: string;
  /** FE2's useContractEligible rule: freelance and local services only, never jobs. */
  contractEligible: boolean;
  onSelect: () => void;
  onToggleCompare: () => void;
  onShortlist: () => void;
  onAskHire: () => void;
  onCancelHire: () => void;
  onHire: () => void;
  onDecline: () => void;
  onMoveBack: () => void;
  /** §6: Call / WhatsApp on a shortlisted row. */
  onContact: (action: ContactAction) => void;
  contactBusy: string | null;
  /** Mobile only: the full detail, expanded under the card. */
  expandedDetail?: React.ReactNode;
}

export function bidLine(t: (k: string, o?: Record<string, unknown>) => string, a: Applicant, lang: string): string | null {
  if (a.bid_amount_paise == null) return null;
  const amount = formatRupees(a.bid_amount_paise, lang);
  return a.bid_type === "hourly" ? t("hiring:board.bidHourly", { amount }) : t("hiring:board.bidFixed", { amount });
}

export default function ApplicantCard(p: ApplicantCardProps) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const lang = i18n.language;
  const { a, ai } = p;
  const verified = ai?.verified || p.badges.some((b) => b.key === "verified_business");
  const otherBadges = p.badges.filter((b) => b.key !== "verified_business").slice(0, 2);
  const years = a.profile.experience_years ?? ai?.experience_years ?? null;
  // §7: one skills verdict, worded for the poster; older rows fall back to the labels.
  const sm = a.skills_match ?? null;
  const matched = sm ? sm.matched_count : a.matched_capability_labels.length;
  const wanted = sm ? sm.required_count : matched + a.missing_capability_labels.length;
  const skillsLine = sm?.text ?? null;
  const reasons = (a.match_reasons ?? []).filter((r) => r !== skillsLine);
  const risks = (a.match_risks ?? []).filter((r) => r !== skillsLine);
  const bid = bidLine(t, a, lang);
  const final = a.stage === "hired" || a.stage === "declined";

  return (
    <article className={`vy-applicant${p.selected ? " vy-applicant-selected" : ""}`} aria-label={p.name}>
      <div className="vy-applicant-top">
        <span className="vy-monogram" aria-hidden="true">{p.name.trim().charAt(0).toUpperCase()}</span>
        <div className="vy-stack" style={{ gap: 4, minWidth: 0 }}>
          <button type="button" className="vy-applicant-name" onClick={p.onSelect} aria-expanded={p.expandedDetail ? true : undefined}>
            {p.name}
          </button>
          <div className="vy-options" style={{ gap: 4 }}>
            {verified && <span className="vy-badge vy-badge-verified">✓ {t("hiring:board.verified")}</span>}
            {otherBadges.map((b) => (
              <span key={b.key} className="vy-badge vy-badge-member-provided" title={b.description}>{b.label}</span>
            ))}
            {a.applied_via === "call" && <span className="vy-badge vy-badge-check">{t("hiring:board.calledYou")}</span>}
            {a.applied_via === "one_tap" && <span className="vy-badge vy-badge-member-provided">{t("hiring:board.oneTap")}</span>}
          </div>
          <div className="vy-applicant-meta">
            {a.profile.headline && <span>{a.profile.headline}</span>}
            {years != null && <span>{t("hiring:apply.years", { count: years })}</span>}
            {ai?.distance_km != null ? (
              <span>{t("hiring:board.kmAway", { km: ai.distance_km < 10 ? ai.distance_km.toFixed(1) : Math.round(ai.distance_km) })}</span>
            ) : (
              a.profile.locality && <span>{a.profile.locality}</span>
            )}
            <span>{t("hiring:board.appliedOn", { date: formatDateIN(a.created_at, lang, false) })}</span>
          </div>
        </div>
        {ai ? (
          <span className="vy-score" title={t("hiring:board.scoreTitle")}>
            {ai.match_score}
            <small>/10</small>
          </span>
        ) : wanted > 0 ? (
          <span className="vy-score" title={t("hiring:board.skillsTitle")}>
            {matched}
            <small>/{wanted} {t("hiring:board.skillsWord")}</small>
          </span>
        ) : null}
      </div>

      {(bid || a.timeline_days) && (
        <div className="vy-applicant-terms">
          {bid && <span><strong>{bid}</strong></span>}
          {a.timeline_days != null && <span>{t("hiring:proposal.days", { count: a.timeline_days })}</span>}
          {a.milestones.length > 0 && <span>{t("hiring:board.milestones", { count: a.milestones.length })}</span>}
        </div>
      )}

      <ul className="vy-reasons">
        {skillsLine && <li className={sm?.kind === "risk" ? "vy-risk" : undefined}>{skillsLine}</li>}
        {ai
          ? ai.reasons.filter((r) => !SKILL_CODES.includes(r.code)).slice(0, 2).map((r) => <li key={r.code}>{r.text}</li>)
          : reasons.slice(0, 2).map((r) => <li key={r}>{r}</li>)}
        {ai
          ? ai.risks.filter((r) => !SKILL_CODES.includes(r.code)).slice(0, 1).map((r) => (
              <li key={r.code} className="vy-risk">{r.text}</li>
            ))
          : risks.slice(0, 1).map((r) => (
              <li key={r} className="vy-risk">{r}</li>
            ))}
      </ul>

      {a.message_preview && (
        <p style={{ fontSize: 14, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{a.message_preview}</p>
      )}

      {a.stage === "shortlisted" && (a.contact_actions?.length ?? 0) > 0 && (
        <ApplicantContact actions={a.contact_actions ?? []} busy={p.contactBusy} onContact={p.onContact} />
      )}

      {p.confirmingHire ? (
        <div className="vy-confirm-inline" role="group" aria-label={t("hiring:board.confirmHireTitle", { name: p.name })}>
          <strong style={{ color: "var(--text-primary)" }}>{t("hiring:board.confirmHireTitle", { name: p.name })}</strong>
          <p style={{ fontSize: 13 }}>{t("hiring:board.confirmHireBody")}</p>
          <div className="vy-applicant-actions">
            <button type="button" className="vy-btn vy-btn-primary" disabled={p.busy} onClick={p.onHire}>
              {t("hiring:board.confirmHire")}
            </button>
            <button type="button" className="vy-btn vy-btn-ghost" onClick={p.onCancelHire}>
              {t("common:action.cancel")}
            </button>
          </div>
        </div>
      ) : (
        <div className="vy-applicant-actions">
          {a.stage === "new" && (
            <button type="button" className="vy-btn vy-btn-secondary" disabled={p.busy} onClick={p.onShortlist}>
              {t("hiring:board.shortlist")}
            </button>
          )}
          {!final && (
            <button type="button" className="vy-btn vy-btn-secondary" disabled={p.busy} onClick={p.onAskHire}>
              {t("hiring:board.hire")}
            </button>
          )}
          {!final && (
            <button type="button" className="vy-btn vy-btn-ghost" disabled={p.busy} onClick={p.onDecline}>
              {t("hiring:board.decline")}
            </button>
          )}
          {a.stage === "shortlisted" && (
            <button type="button" className="vy-btn vy-btn-ghost" disabled={p.busy} onClick={p.onMoveBack}>
              {t("hiring:board.moveBack")}
            </button>
          )}
          {a.stage === "hired" && (
            <>
              <a className="vy-btn vy-btn-primary" href={`/enquiries/${a.enquiry_id}`} style={{ textDecoration: "none" }}>
                {t("hiring:board.openConversation")}
              </a>
              {p.contractEligible && (
                <a className="vy-btn vy-btn-secondary" href={`/contracts/new?enquiry=${a.enquiry_id}`} style={{ textDecoration: "none" }}>
                  {t("hiring:board.startContract")}
                </a>
              )}
            </>
          )}
          {a.stage !== "declined" && (
            <label className="vy-select-box" style={{ marginLeft: "auto" }}>
              <input type="checkbox" checked={p.comparing} disabled={!p.comparing && p.compareFull} onChange={p.onToggleCompare} />
              {t("hiring:board.compare")}
            </label>
          )}
        </div>
      )}
      {p.expandedDetail}
    </article>
  );
}
