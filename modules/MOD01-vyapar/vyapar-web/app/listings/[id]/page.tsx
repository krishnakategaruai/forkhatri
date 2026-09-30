"use client";

// [TR002/TR003/TR005/TR007] Listing manage screen — combines four FRs on
// one screen because that is how an owner actually experiences their own
// listing (04-ui.md's "everything needed on one screen" pattern, applied
// here to owner management rather than a viewer's read):
//  - FR02: per-channel contact disclosure + discoverable toggle
//  - FR03: lifecycle actions (submit / archive), state + reason display
//  - FR05: (professional only) capability vs. seeking-visibility, kept as
//    two visibly separate controls, never combined into one switch
//  - FR07: listing-contact OTP verification gate before submit
// Approach: one GET on mount, optimistic-ish refetch after each mutating
// action (no separate confirmation dialog per the "no unnecessary
// intermediate screens" standing preference) — every action re-fetches the
// canonical listing state from the server rather than guessing the new state
// client-side, so the UI can never drift from what RLS/the state machine
// actually allowed.
// [Product-owner i18n rule] Converted to useTranslation(); backend error
// `detail` strings are already localized server-side (X-Vyapar-Language),
// rendered as-is — only this file's own JSX text/labels needed keys.
// [IMP38 — Refactor C] Now only the route: the Screen frame per state,
// with the data + actions in useListingDetailController and the markup in
// <ListingDetailView> (app/components/listing/). Self-loading blocks are
// passed in as slots.
// Traces to: FR02, FR03, FR05, FR07, TR002, TR003, TR005, TR007
import { use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";
import { VerificationPanel } from "@/app/components/Verification";
import ReportSheet from "@/app/components/ReportSheet";
import ProfileRecommendations from "@/app/components/ProfileRecommendations";
import { ReviewList } from "@/app/components/Reputation";
import PerformanceReport from "@/app/components/PerformanceReport";
import Screen from "@/app/components/Screen";
import { SkeletonGrid, EmptyState } from "@/app/components/States";
import ListingDetailView from "@/app/components/listing/ListingDetailView";
import { useListingDetailController } from "@/app/components/listing/useListingDetailController";
import ListingPackages from "@/app/components/packages/ListingPackages";
import ListingContactOverride from "@/app/components/contact/ListingContactOverride";
import { CouncilCredentialsPanel } from "@/app/components/trust/Council";

// ==================================================================
// [IMP33 — desktop layout for Listing detail]
// REQUIREMENT (owner, 2026-09-17): "Listing/Opportunity detail:
// two-column — primary content left, trust/actions/meta in a sticky
// right column." Before this pass the entire screen was one 480px
// column at any width, so on a 1440px display the primary action
// ("Enquire Now") could be scrolled completely out of sight behind
// reviews and owner panels.
// APPROACH: the identity header (name, state, trust badges,
// reputation) stays full-width at the top — it is the screen's
// subject and must not be squeezed into a column. Everything else
// splits: the *content* a person reads (about, credential, reviews,
// and, for an owner, the management panels) goes left; the things a
// person ACTS on or checks trust against go into a sticky right
// column so they stay reachable at any scroll position. Below 900px
// the grid collapses to one column in source order, which is the
// exact order the phone build already had — no regression.
// Traces to: 04-ui.md F4 (≥900 layout), FR16, FR22, product-owner
// direction 2026-09-17.
// ==================================================================
export default function ListingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["listings", "common", "discover"]);
  const sdk = useSdk();
  const { listing, error, busy, notice, otpRequested, devCode, actions, refresh } = useListingDetailController(id);

  if (error) {
    return (
      <Screen>
        <EmptyState mark="⚠" title={t("common:state.notFound")} body={error} />
      </Screen>
    );
  }
  // [IMP33] Skeleton in the real content's shape instead of a bare
  // "Loading…" line, so the page resolves in place.
  if (!listing)
    return (
      <Screen width="wide">
        <div className="vy-skeleton" style={{ height: 40, width: 280, maxWidth: "70%" }} aria-hidden="true" />
        <SkeletonGrid count={2} grid={false} />
      </Screen>
    );

  return (
    <Screen width="wide">
      <ListingDetailView
        listing={listing}
        busy={busy}
        notice={notice}
        otpRequested={otpRequested}
        devCode={devCode}
        {...actions}
        reviewsSlot={<ReviewList listingId={id} />}
        similarSlot={
          <ProfileRecommendations load={() => sdk.listings.similar(id)} loadKey={`similar-${id}`} title={t("discover:profiles.similarTitle")} />
        }
        reportSlot={<ReportSheet objectKind="listing" objectId={id} blockMemberId={listing.owner_id} />}
        verificationSlot={
          <VerificationPanel
            listingId={id}
            kind={listing.kind}
            verificationState={listing.verification_state}
            onChanged={() => {
              void refresh();
            }}
          />
        }
        performanceSlot={<PerformanceReport targetKind="listing" targetId={id} />}
        packagesSlot={<ListingPackages listingId={id} isOwner={listing.is_owner} providerName={listing.name} initial={listing.packages} />}
        contactPrefsSlot={<ListingContactOverride listingId={id} />}
        credentialsSlot={listing.is_owner ? <CouncilCredentialsPanel onChanged={() => void refresh()} /> : undefined}
      />
    </Screen>
  );
}
