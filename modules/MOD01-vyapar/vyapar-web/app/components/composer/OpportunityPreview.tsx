"use client";

// [FE1 — 2026-09-28] Live preview of what applicants will see, built from
// the draft being typed: type, title, the pay line (same wording the server
// derives), where, the structured facts and the skills. Static markup —
// never a link, never animated per keystroke. Shown as the composer's side
// panel on desktop and as a collapsible block on a phone.
import { useTranslation } from "react-i18next";
import type { ComposerDraft } from "./draft";
import { structuredOf } from "./draft";
import { payLine, structuredFacts } from "./labels";

export default function OpportunityPreview({
  draft,
  skillLabel,
  posterName,
}: {
  draft: ComposerDraft;
  skillLabel: (slug: string) => string;
  posterName?: string;
}) {
  const { t, i18n } = useTranslation(["hiring", "opportunities"]);
  const lang = i18n.language;
  const s = structuredOf(draft);
  const pay = payLine(t, draft.type, s, lang) ?? (draft.compensation.trim() || null);
  const allFacts = structuredFacts(t, draft.type, s, lang);
  const facts = allFacts.filter((f) => !f.wide);
  const timings = allFacts.find((f) => f.key === "timings");
  const where = [draft.location.trim(), draft.workMode ? t(`opportunities:workMode.${draft.workMode}`) : ""].filter(Boolean).join(" · ");
  const questions = draft.type === "freelance" ? draft.questions.filter((q) => q.trim()) : [];

  return (
    <div className="vy-card vy-preview-card" style={{ gap: 10 }}>
      <span className="vy-chip" style={{ alignSelf: "flex-start" }}>{t(`hiring:kinds.${draft.type}`, { defaultValue: t(`opportunities:type.${draft.type}`) })}</span>
      <h3 className={draft.title.trim() ? undefined : "vy-preview-empty"}>{draft.title.trim() || t("hiring:preview.titlePlaceholder")}</h3>
      {pay ? (
        <p style={{ color: "var(--text-primary)", fontWeight: 650 }}>{pay}</p>
      ) : (
        <p className="vy-preview-empty" style={{ fontSize: 14 }}>{t("hiring:preview.noPay")}</p>
      )}
      {where && <p style={{ fontSize: 14 }}>{where}</p>}
      {timings && <p style={{ fontSize: 14 }}>{timings.value}</p>}
      {draft.allowPrecall && (draft.type === "employment" || draft.type === "local_service") && (
        <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>{t(draft.precallChannel === "call_and_whatsapp" ? "hiring:precall.previewLineCall" : "hiring:precall.previewLine")}</p>
      )}
      {facts.length > 0 && (
        <div className="vy-facts" style={{ gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
          {facts.map((f) => (
            <div key={f.key} className="vy-fact">
              <span className="vy-fact-label">{f.label}</span>
              <span className="vy-fact-value" style={{ fontSize: 14 }}>{f.value}</span>
            </div>
          ))}
        </div>
      )}
      {draft.skills.length > 0 && (
        <div className="vy-options">
          {draft.skills.map((slug) => (
            <span key={slug} className="vy-chip">{skillLabel(slug)}</span>
          ))}
        </div>
      )}
      {draft.description.trim() && <p className="vy-preview-body">{draft.description.trim().slice(0, 280)}</p>}
      {questions.length > 0 && (
        <div className="vy-stack" style={{ gap: 4 }}>
          <span className="vy-fact-label">{t("hiring:preview.questionsForYou")}</span>
          <ol style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--text-secondary)" }}>
            {questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ol>
        </div>
      )}
      {posterName && <p style={{ fontSize: 13, fontWeight: 500, color: "var(--text-quaternary)" }}>{t("opportunities:detail.postedBy", { name: posterName })}</p>}
      <p className="vy-muted">{t("hiring:preview.postedToday")}</p>
    </div>
  );
}
