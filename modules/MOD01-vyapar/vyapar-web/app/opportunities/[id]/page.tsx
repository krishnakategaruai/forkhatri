"use client";

// [TR055] Opportunity detail, member actions (FR55).
//
// [Rebuilt 2026-09-21 after product-owner review: "is this screen and
// details correct and enough? I don't think any of Upwork or WorkIndia works
// like this."] They were right, and the gap was not missing data: the API
// already returned requirements, duration, required skills, the apply-by
// deadline and the source site, and this screen showed none of them — only
// a description and one grey line. The two reference apps solve the same
// problem this screen has (a person deciding in seconds whether to act),
// and both answer the same four questions before anything else:
//   - WHAT is it — WorkIndia's labelled rows (Job Type, Role, Incentive,
//     Job Address), Upwork's facts strip (budget, experience, duration).
//     Here: a key-facts grid (pay, duration, work mode, location).
//   - AM I A FIT — WorkIndia's "Candidate Requirement" (qualification,
//     skills), Upwork's skills chips + experience level. Here: "What
//     they're looking for" with skill chips, experience, requirements text.
//   - WHO is behind it — WorkIndia's Company/Interview details, Upwork's
//     "About the client" (member since, jobs posted, payment verified).
//     Here: "About the person who posted", only facts Vyapar can vouch for
//     (member since, open opportunities, their VERIFIED business).
//   - HOW MANY others / how long — Upwork's proposals range, WorkIndia's
//     applicant pill. Here: a coarse response range and an apply-by date.
// Then both end with a way to keep going (WorkIndia "Similar jobs"). Built
// in Vyapar's own design language (near-monochrome, one accent), never a
// copy of either app's layout.
//
// Also removed: the "Active" / "Public" badges (system jargon — "Public"
// now reads as the actual source, "Found on Naukri") and the row of seven
// always-visible not-interested reasons, which now open in place from one
// "Not interested" button.
// [IMP38 — Refactor C] This file is now only the route: it picks the
// Screen frame for each state and hands everything else to
//   - useOpportunityDetailController (data hooks + every action, via the SDK)
//   - <OpportunityDetailView> (presentational; the markup that used to be here)
// The same pair powers the embeddable OpportunityDetailPanel (embed/).
// Traces to: FR55, FR12 (confirm), FR13 (lifecycle), FR16/FR28 (poster
// trust context), FR20 (Why this?), TR055, UX09
import { use as useParamsPromise, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";
import ReportSheet from "@/app/components/ReportSheet";
import PerformanceReport from "@/app/components/PerformanceReport";
import ProfileRecommendations from "@/app/components/ProfileRecommendations";
import Screen from "@/app/components/Screen";
import { SkeletonGrid, EmptyState } from "@/app/components/States";
import OpportunityDetailView from "@/app/components/opportunity/OpportunityDetailView";
import { useOpportunityDetailController } from "@/app/components/opportunity/useOpportunityDetailController";
import ApplicantsSummary from "@/app/components/applicants/ApplicantsSummary";
import ApplyConfirm from "@/app/components/respond/ApplyConfirm";
import Sheet from "@/app/components/respond/Sheet";
import { useMyResponse } from "@/app/hooks/hiring";
import PrecallActions from "@/app/components/contact/PrecallActions";

export default function OpportunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["opportunities", "common", "discover", "hiring"]);
  const sdk = useSdk();
  const { opportunity: opp, error, similar, why, busy, notice, hidden, actions } = useOpportunityDetailController(id);
  // [FE1] A job's Apply is one tap: the confirmation opens here, in place.
  const [applyOpen, setApplyOpen] = useState(false);
  const myResponse = useMyResponse(id, !!opp && !opp.is_poster);

  if (error)
    return (
      <Screen>
        <EmptyState mark="⚠" title={t("common:state.notFound")} body={error} />
      </Screen>
    );
  if (!opp)
    return (
      <Screen width="wide">
        <div className="vy-skeleton" style={{ height: 40, width: 280, maxWidth: "70%" }} aria-hidden="true" />
        <SkeletonGrid count={2} grid={false} />
      </Screen>
    );
  if (hidden)
    return (
      <Screen>
        <EmptyState mark="◌" title={t("opportunities:detail.hiddenFromFeed")} />
      </Screen>
    );

  return (
    <Screen width="wide">
      <OpportunityDetailView
        opportunity={opp}
        similar={similar}
        why={why}
        busy={busy}
        notice={notice}
        {...actions}
        matchingProfilesSlot={
          <ProfileRecommendations
            load={() => sdk.opportunities.matchingProfiles(id)}
            loadKey={`matching-${id}`}
            title={t("discover:profiles.matchingTitle")}
            help={t("discover:profiles.matchingHelp")}
          />
        }
        performanceSlot={<PerformanceReport targetKind="opportunity" targetId={id} />}
        reportSlot={<ReportSheet objectKind="opportunity" objectId={id} blockMemberId={opp.poster_id} />}
        applicantsSlot={<ApplicantsSummary opportunityId={id} type={opp.type} />}
        primaryActionSlot={
          myResponse.data ? (
            // Already responded: one calm row to the thread, never a second Apply.
            <a className="vy-btn vy-btn-secondary" href={`/enquiries/${myResponse.data.id}`} style={{ textDecoration: "none", textAlign: "center" }}>
              {myResponse.data.stage === "declined"
                ? t("hiring:apply.notSelected")
                : myResponse.data.stage === "hired"
                  ? t("hiring:apply.hiredOpen")
                  : t("hiring:apply.appliedOpen")}
            </a>
          ) : opp.type === "employment" && opp.source_segment !== "public" ? (
            // With pre-accept calling on, Apply and Call are two equal buttons:
            // Apply outlined, Call the one filled accent (WorkIndia/Apna).
            <button type="button" className={`vy-btn ${opp.allow_precall ? "vy-btn-secondary" : "vy-btn-primary"}`} onClick={() => setApplyOpen(true)}>
              {t("hiring:apply.apply")}
            </button>
          ) : undefined
        }
        precallSlot={opp.allow_precall && !opp.is_poster ? <PrecallActions opportunityId={id} /> : undefined}
      />
      {applyOpen && (
        <Sheet title={t("hiring:apply.sheetTitle")} onClose={() => setApplyOpen(false)}>
          <ApplyConfirm
            target={{ id: opp.id, title: opp.title, pay: opp.compensation_label ?? opp.compensation, location: opp.location }}
            onDone={() => void myResponse.refresh()}
          />
        </Sheet>
      )}
    </Screen>
  );
}
