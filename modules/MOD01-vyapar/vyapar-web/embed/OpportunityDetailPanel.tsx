"use client";

// [IMP38 — Refactor C] The full opportunity detail as a self-contained
// panel: same controller and same view as the /opportunities/[id] route,
// minus the page frame, so another app can open an opportunity in a side
// panel or modal. Needs only <VyaparEmbedProvider> above it.
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";
import OpportunityDetailView from "@/app/components/opportunity/OpportunityDetailView";
import { useOpportunityDetailController } from "@/app/components/opportunity/useOpportunityDetailController";
import ProfileRecommendations from "@/app/components/ProfileRecommendations";
import PerformanceReport from "@/app/components/PerformanceReport";
import ReportSheet from "@/app/components/ReportSheet";
import { SkeletonGrid, EmptyState } from "@/app/components/States";

export interface OpportunityDetailPanelProps {
  opportunityId: string;
  className?: string;
  /** Show the poster's matching profiles and performance report (default true). */
  showPosterTools?: boolean;
  /** Show the report / block sheet to viewers (default true). */
  showReport?: boolean;
}

export default function OpportunityDetailPanel({ opportunityId, className, showPosterTools = true, showReport = true }: OpportunityDetailPanelProps) {
  const { t } = useTranslation(["opportunities", "common", "discover"]);
  const sdk = useSdk();
  const { opportunity: opp, error, similar, why, busy, notice, hidden, actions } = useOpportunityDetailController(opportunityId);
  const frame = `vy-stack ${className ?? ""}`.trim();

  if (error)
    return (
      <div className={frame}>
        <EmptyState mark="⚠" title={t("common:state.notFound")} body={error} />
      </div>
    );
  if (!opp)
    return (
      <div className={frame}>
        <div className="vy-skeleton" style={{ height: 40, width: 280, maxWidth: "70%" }} aria-hidden="true" />
        <SkeletonGrid count={2} grid={false} />
      </div>
    );
  if (hidden)
    return (
      <div className={frame}>
        <EmptyState mark="◌" title={t("opportunities:detail.hiddenFromFeed")} />
      </div>
    );

  return (
    <div className={frame}>
      <OpportunityDetailView
        opportunity={opp}
        similar={similar}
        why={why}
        busy={busy}
        notice={notice}
        {...actions}
        matchingProfilesSlot={
          showPosterTools ? (
            <ProfileRecommendations
              load={() => sdk.opportunities.matchingProfiles(opportunityId)}
              loadKey={`matching-${opportunityId}`}
              title={t("discover:profiles.matchingTitle")}
              help={t("discover:profiles.matchingHelp")}
            />
          ) : null
        }
        performanceSlot={showPosterTools ? <PerformanceReport targetKind="opportunity" targetId={opportunityId} /> : null}
        reportSlot={showReport ? <ReportSheet objectKind="opportunity" objectId={opportunityId} blockMemberId={opp.poster_id} /> : null}
      />
    </div>
  );
}
