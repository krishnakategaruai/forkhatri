"use client";

// [FE2 — imp-backend-d] /contracts/new?enquiry=<id> — start a contract from
// an accepted request. Reads the request first: only the paying side (the
// client, per getContractRoles / isClientOf — critique N1) sees the form;
// the other side is told who starts it, and a request that is not accepted
// yet says so instead of offering a form the server would refuse. The draft
// is pre-filled from the conversation (the proposal's price and stages).
import { use, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { ChevronLeft, FileSignature, Info } from "lucide-react";
import type { ContractCreateInput, EnquiryDetail } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { paiseToInput } from "@/lib/format";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { useResource } from "@/app/hooks/useResource";
import { errorText } from "@/app/hooks/trade";
import ContractCreateForm, { emptyMilestone, type ContractDraft } from "@/app/components/contracts/ContractCreateForm";
import { isClientOf, useContractEligible } from "@/app/components/contracts/ContractEntry";
import "@/app/styles/deals-2026.css";

function addDays(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function draftFrom(e: EnquiryDetail): { draft: ContractDraft; fromProposal: boolean } {
  const proposal = e.milestones && e.milestones.length > 0 ? e.milestones : null;
  const hourly = e.bid_type === "hourly";
  return {
    fromProposal: !!(e.bid_amount_paise || proposal),
    draft: {
      // a post's title names the work; a profile's name does not
      title: e.opportunity_id ? (e.target_name ?? "") : "",
      description: "",
      kind: hourly ? "hourly" : "fixed",
      total: hourly ? "" : paiseToInput(e.bid_amount_paise ?? null),
      rate: hourly ? paiseToInput(e.bid_amount_paise ?? null) : "",
      cap: hourly ? "10" : "",
      milestones: proposal
        ? proposal.map((m) => ({ title: m.title, amount: paiseToInput(m.amount_paise), due: m.due_days ? addDays(m.due_days) : "" }))
        : [emptyMilestone()],
    },
  };
}

export default function NewContractPage({ searchParams }: { searchParams: Promise<{ enquiry?: string }> }) {
  const { enquiry: enquiryId = "" } = use(searchParams);
  const { t } = useTranslation(["contracts", "common"]);
  const sdk = useSdk();
  const router = useRouter();
  // The detail read carries ids only; the names come from the member's own
  // request list row (the same source the thread's context card uses).
  const enquiry = useResource<EnquiryDetail>(
    async () => {
      const detail = await sdk.enquiries.get(enquiryId);
      if (detail.counterpart_name && detail.target_name) return detail;
      const rows = await sdk.enquiries.mine(detail.is_sender ? "sent" : "received").catch(() => []);
      const row = rows.find((r) => r.id === enquiryId);
      return { ...detail, counterpart_name: detail.counterpart_name ?? row?.counterpart_name ?? null, target_name: detail.target_name ?? row?.target_name ?? null };
    },
    [enquiryId, sdk],
    { enabled: !!enquiryId },
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now())));
  const e = enquiry.data;
  const prefill = useMemo(() => (e ? draftFrom(e) : null), [e]);
  // [Critique L5] salaried jobs are not paid through contracts
  const eligible = useContractEligible(e ? (e.opportunity_id ?? null) : undefined);

  async function create(body: Omit<ContractCreateInput, "enquiry_id">) {
    setBusy(true);
    setError(null);
    try {
      const c = await sdk.contracts.create({ ...body, enquiry_id: enquiryId }, idempotencyKey);
      router.push(`/contracts/${c.id}`);
    } catch (err) {
      setError(errorText(err, t("common:state.actionFailed")));
      setBusy(false);
    }
  }

  const name = e?.counterpart_name ?? "";
  const infoIcon = <Info size={24} strokeWidth={1.75} aria-hidden="true" />;
  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href={enquiryId ? `/enquiries/${enquiryId}` : "/contracts"} transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {t("contracts:new.back")}
        </Link>
        {!enquiryId || enquiry.error ? (
          <DealsEmpty tone="neutral" icon={infoIcon} title={t("common:state.notFound")} />
        ) : !e || !prefill || eligible === null ? (
          <SkeletonGrid count={2} grid={false} />
        ) : !isClientOf(e) ? (
          <DealsEmpty tone="neutral" icon={infoIcon} title={t("contracts:new.notClientTitle", { name })} body={t("contracts:new.notClientBody")} />
        ) : eligible === false ? (
          <DealsEmpty tone="neutral" icon={infoIcon} title={t("contracts:new.title")} body={t("contracts:new.notForJobs")} />
        ) : e.state !== "in_progress" ? (
          <DealsEmpty tone="neutral" icon={infoIcon} title={t("contracts:new.title")} body={t("contracts:new.notAccepted")} />
        ) : (
          <>
            <div className="vy-dl-head">
              <div className="vy-dl-tags">
                <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true">
                  <FileSignature size={20} strokeWidth={1.75} />
                </span>
              </div>
              <h1>{t("contracts:new.title")}</h1>
              <p>{t("contracts:new.subtitle", { name })}</p>
            </div>
            <ContractCreateForm initial={prefill.draft} counterpart={name} target={e.target_name ?? null} fromProposal={prefill.fromProposal} busy={busy} error={error} onSubmit={create} />
          </>
        )}
      </div>
    </Screen>
  );
}
