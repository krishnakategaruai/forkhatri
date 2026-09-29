"use client";

// ======================================================================
// [FE1 — 2026-09-28] Applicants board for the poster:
// /opportunities/[id]/applicants.
//
// REQUIREMENT (owner): the poster reviews applicants and proposals in one
// place and acts on each in one tap. Research §3 (Upwork "Review
// proposals", Indeed Candidates, Apna, Naukri Response Manager):
//  - stage tabs New / Shortlisted / Hired / Declined with counts;
//  - sort by newest or best match (AI 1–10 with reasons and risks; else
//    the rule-based match order and a count-based skills line);
//  - each card: name, verified, earned badges, experience, distance or
//    area, price and days for a proposal, match, top reasons;
//  - one-tap Shortlist (Undo) / Hire (confirm, it shares contact) /
//    Decline (Undo window, then final);
//  - pick 2–4 to compare side by side;
//  - desktop: the list with a detail pane beside it; phone: cards whose
//    name opens the detail in place;
//  - after Hire: the shared contact, the conversation and "Start a
//    contract".
// Route = data + actions (useApplicantsBoard); markup = the components.
// Traces to: imp-backend-a §3, imp-backend-c §3
// ======================================================================

import { use as useParamsPromise, useState } from "react";
import { useTranslation } from "react-i18next";
import { APPLICANT_STAGES, type ApplicantCompare } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import { EmptyState } from "@/app/components/States";
import Sheet from "@/app/components/respond/Sheet";
import { useContractEligible } from "@/app/components/contracts/ContractEntry";
import { Segmented } from "@/app/components/composer/fields";
import ApplicantCard from "@/app/components/applicants/ApplicantCard";
import ApplicantDetail from "@/app/components/applicants/ApplicantDetail";
import CompareTable from "@/app/components/applicants/CompareTable";
import { useApplicantsBoard, type SortKey } from "@/app/components/applicants/useApplicantsBoard";

export default function ApplicantsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const b = useApplicantsBoard(id);
  // "Start a contract" follows FE2's one rule (ContractEntry.useContractEligible).
  const contractEligible = useContractEligible(id) === true;
  const [expanded, setExpanded] = useState<string | null>(null);
  const [compare, setCompare] = useState<ApplicantCompare | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  const opp = b.opportunity;
  const type = opp?.type ?? "employment";
  const noun = type === "freelance" ? "proposals" : type === "employment" ? "applicants" : "responses";

  async function openCompare() {
    setCompare(null);
    setCompareError(null);
    setCompareOpen(true);
    try {
      setCompare(await sdk.applicants.compare(id, b.compareIds));
    } catch {
      setCompareError(t("hiring:errors.compare_count"));
    }
  }

  if (b.opportunityError) {
    return (
      <Screen>
        <EmptyState mark="⚠" title={t("common:state.notFound")} body={t("hiring:errors.opportunity_not_found")} />
      </Screen>
    );
  }

  const selected = b.items.find((a) => a.enquiry_id === b.selectedId) ?? null;

  return (
    <Screen width="console">
      <div className="vy-board-head">
        <a href={`/opportunities/${id}`} style={{ fontSize: 14 }}>← {t("hiring:board.backToPost")}</a>
        <div className="vy-stack" style={{ gap: 4 }}>
          <h1>{t(`hiring:board.title.${noun}`)}</h1>
          {opp ? <p>{opp.title}{opp.compensation_label || opp.compensation ? ` · ${opp.compensation_label ?? opp.compensation}` : ""}</p> : <div className="vy-skeleton" style={{ height: 18, width: 260 }} />}
        </div>
        <div className="vy-board-bar">
          <div className="vy-stage-tabs" role="tablist" aria-label={t("hiring:board.stagesLabel")}>
            {APPLICANT_STAGES.map((s) => (
              <button key={s} type="button" role="tab" className="vy-chip vy-tab" aria-selected={b.stage === s} onClick={() => b.changeStage(s)}>
                {t(`hiring:board.stage.${s}`)} <span className="vy-stage-count">{b.counts[s] ?? 0}</span>
              </button>
            ))}
          </div>
          <Segmented<SortKey>
            options={["newest", "best"]}
            value={b.sort}
            onChange={b.setSort}
            label={(v) => t(`hiring:board.sort.${v}`)}
            ariaLabel={t("hiring:board.sortLabel")}
          />
        </div>
        {b.sort === "best" && (
          <p className="vy-field-hint" role="status">
            {b.ai.loading
              ? t("hiring:board.ranking")
              : b.ai.failed
                ? t("hiring:board.rankedBySkills")
                : b.ai.data
                  ? t(b.ai.data.source === "ai" ? "hiring:board.rankedByAi" : "hiring:board.rankedByRules")
                  : null}
          </p>
        )}
        {b.error && <p className="vy-error" role="alert">{b.error}</p>}
      </div>

      {b.loading ? (
        <div className="vy-applicants" aria-busy="true">
          {[0, 1, 2].map((i) => (
            <div key={i} className="vy-skeleton" style={{ height: 150, borderRadius: 24 }} />
          ))}
        </div>
      ) : b.items.length === 0 ? (
        b.total === 0 ? (
          <div className="vy-empty">
            <span className="vy-empty-mark" aria-hidden="true">◌</span>
            <strong style={{ color: "var(--text-primary)" }}>{t(`hiring:board.empty.${noun}`)}</strong>
            {b.suggestions.length > 0 && (
              <>
                <p>{t("hiring:board.emptyHelps")}</p>
                <ul className="vy-signal-list" style={{ textAlign: "left", maxWidth: 520 }}>
                  {b.suggestions.map((s) => (
                    <li key={s.code}>{s.message}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        ) : (
          <div className="vy-empty">
            <span className="vy-empty-mark" aria-hidden="true">◌</span>
            <p>{t(`hiring:board.emptyStage.${b.stage}`)}</p>
          </div>
        )
      ) : (
        <div className="vy-pane">
          <div className="vy-pane-list">
            <div className="vy-applicants">
              {b.items.map((a) => {
                const name = b.displayName(a);
                const ai = b.aiById.get(a.enquiry_id);
                const badges = b.badges[a.sender_id] ?? [];
                return (
                  <ApplicantCard
                    key={a.enquiry_id}
                    a={a}
                    name={name}
                    ai={b.sort === "best" ? ai : undefined}
                    badges={badges}
                    selected={b.selectedId === a.enquiry_id}
                    comparing={b.compareIds.includes(a.enquiry_id)}
                    compareFull={b.compareIds.length >= 4}
                    confirmingHire={b.confirmHireId === a.enquiry_id}
                    busy={b.busyId === a.enquiry_id}
                    opportunityType={type}
                    contractEligible={contractEligible}
                    onSelect={() => {
                      b.select(a.enquiry_id);
                      setExpanded((e) => (e === a.enquiry_id ? null : a.enquiry_id));
                    }}
                    onToggleCompare={() => b.toggleCompare(a.enquiry_id)}
                    onShortlist={() => b.shortlist(a)}
                    onAskHire={() => b.askHire(a.enquiry_id)}
                    onCancelHire={() => b.askHire(null)}
                    onHire={() => b.hire(a)}
                    onDecline={() => b.decline(a)}
                    onMoveBack={() => b.moveBack(a)}
                    onContact={(action) => b.contact(a, action)}
                    contactBusy={b.contactBusyFor(a)}
                    expandedDetail={
                      expanded === a.enquiry_id ? (
                        <div className="vy-inline-detail">
                          <ApplicantDetail
                            a={a}
                            name={name}
                            ai={ai}
                            badges={badges}
                            opportunityType={type}
                    contractEligible={contractEligible}
                            onContact={(action) => b.contact(a, action)}
                            contactBusy={b.contactBusyFor(a)}
                          />
                        </div>
                      ) : undefined
                    }
                  />
                );
              })}
            </div>
          </div>
          <div className="vy-pane-detail vy-console-only">
            {selected && (
              <div className="vy-card" style={{ position: "sticky", top: 24 }}>
                <ApplicantDetail
                  a={selected}
                  name={b.displayName(selected)}
                  ai={b.aiById.get(selected.enquiry_id)}
                  badges={b.badges[selected.sender_id] ?? []}
                  opportunityType={type}
                    contractEligible={contractEligible}
                  onContact={(action) => b.contact(selected, action)}
                  contactBusy={b.contactBusyFor(selected)}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {b.compareIds.length > 0 && (
        <div className="vy-compare-bar" role="region" aria-label={t("hiring:board.compare")}>
          <span>{t("hiring:board.pickedN", { count: b.compareIds.length })}</span>
          <span className="vy-row" style={{ gap: 6 }}>
            <button type="button" className="vy-btn vy-btn-ghost" onClick={b.clearCompare}>
              {t("hiring:board.clear")}
            </button>
            <button type="button" className="vy-btn vy-btn-primary" style={{ padding: "8px 18px" }} disabled={b.compareIds.length < 2} onClick={openCompare}>
              {b.compareIds.length < 2 ? t("hiring:board.pickOneMore") : t("hiring:board.compareN", { count: b.compareIds.length })}
            </button>
          </span>
        </div>
      )}

      {compareOpen && (
        <Sheet title={t("hiring:board.compareTitle")} wide onClose={() => setCompareOpen(false)}>
          {compareError ? (
            <p className="vy-error">{compareError}</p>
          ) : (
            <CompareTable
              data={compare}
              aiById={b.aiById}
              nameOf={b.displayName}
              onShortlist={(a) => {
                setCompareOpen(false);
                void b.shortlist(a);
              }}
              onHire={(a) => {
                setCompareOpen(false);
                if (b.stage !== a.stage) b.changeStage(a.stage);
                b.select(a.enquiry_id);
                b.askHire(a.enquiry_id);
              }}
            />
          )}
        </Sheet>
      )}

      {b.toast && (
        <div className="vy-toast" role="status">
          <span>{b.toast.text}</span>
          {b.toast.undo && (
            <button type="button" className="vy-btn vy-btn-secondary" onClick={b.toast.undo}>
              {t("hiring:board.undo")}
            </button>
          )}
        </div>
      )}
    </Screen>
  );
}
