"use client";

// [FE2 — imp-backend-d] "Start a contract" on an accepted enquiry thread.
//
// Who may start one follows the backend rule exactly: the client is the
// side that pays — the poster for an `apply` enquiry (a hired applicant),
// otherwise the sender. When a live contract already exists for this thread
// the button becomes "Open contract" for both sides instead, so no one tries
// to create a duplicate (the server would refuse it with 409 anyway).
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { useContracts } from "@/app/hooks/trade";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "@/app/hooks/useResource";

/**
 * [Critique L5] Contracts (milestones, timesheets) are for freelance projects
 * and local services. A salaried job is paid by the employer's payroll, so a
 * job thread never offers one. A profile enquiry (no opportunity) is a
 * service request and qualifies.
 */
export const CONTRACT_TYPES = ["freelance", "local_service"];

export function useContractEligible(opportunityId: string | null | undefined): boolean | null {
  const sdk = useSdk();
  const opp = useResource<{ type: string } | null>(
    () => (opportunityId ? sdk.opportunities.get(opportunityId) : Promise.resolve(null)),
    [opportunityId ?? "", sdk],
    { language: false },
  );
  if (!opportunityId) return true;
  if (opp.data) return CONTRACT_TYPES.includes(opp.data.type);
  return opp.error ? false : null; // null while loading
}

const LIVE = ["draft", "proposed", "active", "disputed"];

export function isClientOf(enquiry: { action_type: string; is_sender: boolean }): boolean {
  return enquiry.action_type === "apply" ? !enquiry.is_sender : enquiry.is_sender;
}

export default function ContractEntry({
  enquiryId,
  enquiryState,
  isClient,
  opportunityId,
}: {
  enquiryId: string;
  enquiryState: string;
  isClient: boolean;
  /** The enquiry's opportunity, when it answers one (decides eligibility). */
  opportunityId?: string | null;
}) {
  const { t } = useTranslation(["contracts"]);
  const { data } = useContracts({ role: "all", limit: 50 });
  const existing = data?.items.filter((c) => c.enquiry_id === enquiryId) ?? [];
  const live = existing.find((c) => LIVE.includes(c.state));
  const latest = live ?? existing[0];

  const eligible = useContractEligible(opportunityId);
  if (!data) return null;
  if (latest) {
    return (
      <Link className="vy-btn vy-btn-secondary" href={`/contracts/${latest.id}`} transitionTypes={["vy-forward"]} style={{ textDecoration: "none" }}>
        {t("contracts:entry.open")}
      </Link>
    );
  }
  if (enquiryState !== "in_progress" || !isClient || eligible !== true) return null;
  return (
    <Link
      className="vy-btn vy-btn-secondary"
      href={`/contracts/new?enquiry=${enquiryId}`}
      transitionTypes={["vy-forward"]}
      style={{ textDecoration: "none" }}
    >
      {t("contracts:entry.start")}
    </Link>
  );
}
