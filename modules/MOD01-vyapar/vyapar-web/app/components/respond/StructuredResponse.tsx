"use client";

// ======================================================================
// [FE1 — 2026-09-28] The response screen for the three main opportunity
// types, one structured composer each (owner rule: never one generic chat
// box):
//   - Job → one-tap Apply: a confirmation of the profile snapshot sent.
//   - Freelance project → a proposal: price, timeline, milestones,
//     screening answers, cover text with "Improve with AI".
//   - Local service → a quote or a question, as chips plus a note.
// Desktop: the composer on the left and the opportunity's brief pinned on
// the right, so the person never scrolls away from what they are answering
// (research §2). Phone: the brief is a compact card above the composer.
// Sent: the composer is replaced by a short "Sent" card — no modal.
// Listings and the other opportunity types keep the existing composer.
// ======================================================================

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { Opportunity } from "@/lib/sdk";
import Screen from "@/app/components/Screen";
import { useRoutes } from "@/app/host/HostProvider";
import { structuredFacts, type T as LabelT } from "@/app/components/composer/labels";
import ApplyConfirm from "./ApplyConfirm";
import ProposalComposer from "./ProposalComposer";
import QuoteComposer from "./QuoteComposer";

export function isStructuredKind(type: string): boolean {
  return type === "employment" || type === "freelance" || type === "local_service";
}

function Brief({ opp }: { opp: Opportunity }) {
  const { t, i18n } = useTranslation(["hiring", "opportunities"]);
  const facts = structuredFacts(t as LabelT, opp.type, opp.structured, i18n.language);
  const pay = opp.compensation_label ?? opp.compensation;
  return (
    <div className="vy-card vy-stack" style={{ gap: 10 }}>
      <span className="vy-chip" style={{ alignSelf: "flex-start" }}>{t(`hiring:kinds.${opp.type}`, { defaultValue: t(`opportunities:type.${opp.type}`) })}</span>
      <strong style={{ color: "var(--text-primary)", fontSize: 17, lineHeight: 1.3 }}>{opp.title}</strong>
      {pay && <p style={{ color: "var(--text-primary)", fontWeight: 650, fontSize: 15 }}>{pay}</p>}
      {(opp.location || opp.submitter_name) && (
        <p style={{ fontSize: 14 }}>{[opp.location, opp.submitter_name ? t("opportunities:detail.postedBy", { name: opp.submitter_name }) : null].filter(Boolean).join(" · ")}</p>
      )}
      {facts.length > 0 && (
        <dl className="vy-qa" style={{ margin: 0 }}>
          {facts.map((f) => (
            <div key={f.key}>
              <dt>{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
      )}
      {opp.capability_labels.length > 0 && (
        <div className="vy-options">
          {opp.capability_labels.map((c, i) => (
            <span key={c} className={opp.capability_match?.[i] ? "vy-chip vy-chip-match" : "vy-chip"}>{c}</span>
          ))}
        </div>
      )}
      {opp.description && <p className="vy-preview-body" style={{ maxHeight: 180 }}>{opp.description}</p>}
    </div>
  );
}

export default function StructuredResponse({ opportunity: opp }: { opportunity: Opportunity }) {
  const { t } = useTranslation(["hiring"]);
  const routes = useRoutes();
  const [sentId, setSentId] = useState<string | null>(null);
  const title =
    opp.type === "employment" ? t("hiring:respond.applyTitle") : opp.type === "freelance" ? t("hiring:respond.proposeTitle") : t("hiring:respond.quoteTitle");

  return (
    <Screen width="wide">
      <div className="vy-stack" style={{ gap: 6 }}>
        <a href={routes.opportunity(opp.id)} style={{ fontSize: 14 }}>← {t("hiring:respond.backToPost")}</a>
        <h1>{title}</h1>
      </div>
      <div className="vy-compose">
        <div className="vy-compose-main">
          <details className="vy-mobile-only vy-card vy-card-nested" style={{ padding: "12px 16px" }}>
            <summary style={{ cursor: "pointer", fontWeight: 600, color: "var(--text-primary)" }}>{opp.title}</summary>
            <div style={{ marginTop: 12 }}>
              <Brief opp={opp} />
            </div>
          </details>
          {sentId && opp.type !== "employment" ? (
            <div className="vy-sent" role="status">
              <span className="vy-sent-mark" aria-hidden="true">✓</span>
              <strong style={{ color: "var(--text-primary)", fontSize: 17 }}>{opp.type === "freelance" ? t("hiring:respond.proposalSent") : t("hiring:respond.messageSent")}</strong>
              <p style={{ fontSize: 14 }}>{t("hiring:apply.sentBody", { title: opp.title })}</p>
              <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={routes.enquiry(sentId)}>
                {t("hiring:apply.openConversation")}
              </a>
            </div>
          ) : opp.type === "employment" ? (
            <ApplyConfirm target={{ id: opp.id, title: opp.title, pay: opp.compensation_label ?? opp.compensation, location: opp.location }} onDone={setSentId} />
          ) : opp.type === "freelance" ? (
            <ProposalComposer opportunity={opp} onSent={setSentId} />
          ) : (
            <QuoteComposer opportunity={opp} onSent={setSentId} />
          )}
        </div>
        <aside className="vy-compose-aside" aria-label={t("hiring:respond.youreAnswering")}>
          <span className="vy-preview-label">{t("hiring:respond.youreAnswering")}</span>
          <Brief opp={opp} />
        </aside>
      </div>
    </Screen>
  );
}
