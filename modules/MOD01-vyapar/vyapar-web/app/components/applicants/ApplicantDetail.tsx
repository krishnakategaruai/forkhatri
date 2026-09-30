"use client";

// [FE1 — 2026-09-28] Everything about one applicant, for the desktop detail
// pane and the phone's expanded card: profile snapshot (as it stood when
// they applied), skills matched against the post, terms and milestones,
// every screening answer under its question, their message, the AI's
// summary with reasons and risks, and — once hired — the shared contact
// with the way into the conversation and "Start a contract".
import { useTranslation } from "react-i18next";
import type { AiShortlistItem, Applicant, Badge, ContactAction } from "@/lib/sdk";
import ApplicantContact from "./ApplicantContact";
import { formatDateIN } from "@/lib/money";
import { useDisclosedContacts } from "@/app/hooks/hiring";
import ProposalSummary, { hasProposalTerms } from "./ProposalSummary";
import TranslateLink from "@/app/components/respond/TranslateLink";
import ContactActionsBlock from "@/app/components/contact/ContactActionsBlock";

export default function ApplicantDetail({
  a,
  name,
  ai,
  badges,
  contractEligible,
  onContact,
  contactBusy,
}: {
  a: Applicant;
  name: string;
  ai?: AiShortlistItem;
  badges: Badge[];
  /** Kept for callers; the contract rule now comes in as contractEligible. */
  opportunityType?: string;
  contractEligible: boolean;
  onContact?: (action: ContactAction) => void;
  contactBusy?: string | null;
}) {
  const { t, i18n } = useTranslation(["hiring", "common"]);
  const lang = i18n.language;
  const contacts = useDisclosedContacts(a.enquiry_id, a.stage === "hired");

  return (
    <div className="vy-applicant-detail">
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 className="vy-card-title" style={{ fontSize: 20 }}>{name}</h2>
        {a.profile.headline && <p style={{ fontSize: 14 }}>{a.profile.headline}</p>}
        <p className="vy-field-hint" style={{ fontSize: 13 }}>
          {[
            a.profile.experience_years != null ? t("hiring:apply.years", { count: a.profile.experience_years }) : null,
            a.profile.locality,
            a.profile.availability ? t(`hiring:apply.availability.${a.profile.availability}`) : null,
            a.profile.languages.length ? a.profile.languages.map((l) => t(`hiring:voice.langName.${l}`, { defaultValue: l })).join(", ") : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </div>

      {a.stage === "shortlisted" && (a.contact_actions?.length ?? 0) > 0 && onContact && (
        <div className="vy-card vy-card-nested vy-stack" style={{ gap: 8, padding: 16 }}>
          <strong style={{ color: "var(--text-primary)" }}>{t("hiring:board.shortlistedContactTitle", { name })}</strong>
          <ApplicantContact actions={a.contact_actions ?? []} busy={contactBusy ?? null} onContact={onContact} />
          <span className="vy-field-hint">{t("hiring:board.shortlistedContactHint")}</span>
        </div>
      )}

      {a.stage === "shortlisted" && (a.contact_actions?.length ?? 0) === 0 && (
        <p className="vy-field-hint">
          {t("hiring:board.noNumberShared", { name })} <a href={`/enquiries/${a.enquiry_id}`}>{t("hiring:board.openConversation")}</a>
        </p>
      )}

      {!ai && (a.match_risks?.length ?? 0) > 0 && (
        <ul className="vy-reasons">
          {(a.match_risks ?? []).map((r) => (
            <li key={r} className="vy-risk">{r}</li>
          ))}
        </ul>
      )}

      {a.stage === "hired" && (
        <div className="vy-card vy-card-nested vy-stack" style={{ gap: 8, padding: 16 }}>
          <strong style={{ color: "var(--text-primary)" }}>{t("hiring:board.hiredTitle")}</strong>
          {/* FE2's contact block: Call / WhatsApp from the thread's contact
              actions (hours and daily limit applied), the other disclosed
              contacts listed under it. */}
          <ContactActionsBlock
            enquiryId={a.enquiry_id}
            enquiryState={a.thread_state}
            disclosedContacts={contacts.data ?? []}
            fallback={<p style={{ fontSize: 13 }}>{t("hiring:board.contactInThread")}</p>}
          />
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
            <a className="vy-btn vy-btn-primary" href={`/enquiries/${a.enquiry_id}`} style={{ textDecoration: "none" }}>
              {t("hiring:board.openConversation")}
            </a>
            {contractEligible && (
              <a className="vy-btn vy-btn-secondary" href={`/contracts/new?enquiry=${a.enquiry_id}`} style={{ textDecoration: "none" }}>
                {t("hiring:board.startContract")}
              </a>
            )}
          </div>
        </div>
      )}

      {badges.length > 0 && (
        <div className="vy-stack" style={{ gap: 6 }}>
          {badges.map((b) => (
            <p key={b.key} style={{ fontSize: 13 }}>
              <span className={b.key === "verified_business" ? "vy-badge vy-badge-verified" : "vy-badge vy-badge-member-provided"}>{b.label}</span> {b.description}
            </p>
          ))}
        </div>
      )}

      {(a.matched_capability_labels.length > 0 || a.missing_capability_labels.length > 0) && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <span className="vy-fact-label">{t("hiring:board.skillsForThis")}</span>
          <div className="vy-options">
            {a.matched_capability_labels.map((c) => (
              <span key={c} className="vy-chip vy-chip-match">✓ {c}</span>
            ))}
            {/* §7: one "Missing: …" chip, never "No <skill>". */}
            {a.skills_match?.missing_text ? (
              <span className="vy-chip" style={{ opacity: 0.8 }}>{a.skills_match.missing_text}</span>
            ) : !a.skills_match && a.missing_capability_labels.length > 0 ? (
              <span className="vy-chip" style={{ opacity: 0.8 }}>
                {t("hiring:board.missingList", { skills: a.missing_capability_labels.join(", ") })}
              </span>
            ) : null}
          </div>
        </div>
      )}

      {/* [N6] the same proposal card the thread shows */}
      {hasProposalTerms(a) && (
        <ProposalSummary terms={a} />
      )}
      {!hasProposalTerms(a) && a.screening_answers.length > 0 && <ProposalSummary terms={{ screening_answers: a.screening_answers }} />}

      {a.message_preview && (
        <div className="vy-stack" style={{ gap: 4 }}>
          <span className="vy-fact-label">{t("hiring:board.theirMessage")}</span>
          <p style={{ whiteSpace: "pre-wrap", color: "var(--text-primary)", fontSize: 14 }}>{a.message_preview}</p>
          <TranslateLink text={a.message_preview} language={a.message_language} />
        </div>
      )}

      {ai && (
        <div className="vy-ai-card">
          <span className="vy-fact-label">{t("hiring:board.aiRead", { score: ai.match_score })}</span>
          {ai.summary && <p style={{ fontSize: 14, color: "var(--text-primary)" }}>{ai.summary}</p>}
          <ul className="vy-reasons">
            {ai.reasons.map((r) => (
              <li key={r.code}>{r.text}</li>
            ))}
            {ai.risks.map((r) => (
              <li key={r.code} className="vy-risk">{r.text}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="vy-field-hint">
        {t("hiring:board.appliedVia", { how: t(`hiring:board.via.${a.applied_via}`, { defaultValue: a.applied_via }), date: formatDateIN(a.created_at, lang) })}
      </p>
    </div>
  );
}
