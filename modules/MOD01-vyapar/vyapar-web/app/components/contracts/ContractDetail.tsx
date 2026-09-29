"use client";

// [FE2] Contract detail, behavioural half: useContract + every action
// through the SDK. Funding (a milestone, or an approved hourly week) reuses
// the Payment Bridge checkout boosts use: the API returns `checkout_url`,
// the browser goes there, and the checkout sends the person back to this
// contract (`?return=`). Whether that checkout is the development sandbox is
// read from the order itself (`sandbox`), never assumed.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Funding } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useContract } from "@/app/hooks/trade";
import { EmptyState, SkeletonGrid } from "@/app/components/States";
import ContractDetailView from "./ContractDetailView";
import { checkoutHref } from "./model";

export default function ContractDetail({ id, embedded = false, onChanged }: { id: string; embedded?: boolean; onChanged?: () => void }) {
  const { t } = useTranslation(["contracts", "common"]);
  const sdk = useSdk();
  const { data: contract, error, busy, actionError, setActionError, run } = useContract(id);
  const [sandbox, setSandbox] = useState<boolean | null>(null);

  // Any order this contract has already opened tells us whether payments are sandboxed.
  const orderId = contract?.milestones.find((m) => m.funded_order_id)?.funded_order_id ?? null;
  useEffect(() => {
    if (!orderId) return;
    let live = true;
    sdk.commercial
      .getOrder<{ sandbox: boolean }>(orderId)
      .then((o) => live && setSandbox(!!o.sandbox))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [orderId, sdk]);

  if (error) return <EmptyState mark="⚠" title={t("common:state.notFound")} />;
  if (!contract) return <SkeletonGrid count={3} grid={false} />;

  const fail = t("common:state.actionFailed");
  const act = async <T,>(fn: () => Promise<T>) => {
    const out = await run(fn, fail);
    if (out !== undefined) onChanged?.();
    return out;
  };

  function goPay(f: Funding | undefined) {
    if (!f) return;
    setSandbox(f.sandbox);
    if (f.checkout_url) {
      window.location.assign(checkoutHref(f.checkout_url, id));
    } else if (f.notice === "gatewayUnavailable") {
      setActionError(t("contracts:action.gatewayUnavailable"));
    }
  }

  return (
    <ContractDetailView
      contract={contract}
      busy={busy}
      error={actionError}
      sandbox={sandbox}
      embedded={embedded}
      onPropose={() => act(() => sdk.contracts.propose(id))}
      onAccept={() => act(() => sdk.contracts.accept(id))}
      onCancel={(reason) => act(() => sdk.contracts.cancel(id, reason))}
      onComplete={() => act(() => sdk.contracts.complete(id))}
      onFund={async (mid) => goPay(await act(() => sdk.contracts.fundMilestone(id, mid)))}
      onSubmit={(mid, note) => act(() => sdk.contracts.submitMilestone(id, mid, note))}
      onApprove={(mid) => act(() => sdk.contracts.approveMilestone(id, mid))}
      onReject={(mid, note) => act(() => sdk.contracts.rejectMilestone(id, mid, note))}
      onOpenDispute={(reason, mid) => act(() => sdk.contracts.openDispute(id, reason, mid))}
      onSubmitTimesheet={(input) => act(() => sdk.contracts.submitTimesheet(id, input))}
      onApproveTimesheet={async (tid) => goPay(await act(() => sdk.contracts.approveTimesheet(id, tid)))}
      onRejectTimesheet={(tid, note) => act(() => sdk.contracts.rejectTimesheet(id, tid, note))}
    />
  );
}
