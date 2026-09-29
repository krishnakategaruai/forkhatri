"use client";

// [FE2] Packages on a listing: the owner edits, everyone else compares and
// requests. Loads through the SDK (sdk.packages) so a save is re-read from
// the server; a request is an ordinary enquiry with an Idempotency-Key, so a
// double tap sends one.
import { useTranslation } from "react-i18next";
import type { ServicePackage } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "@/app/hooks/useResource";
import { errorText } from "@/app/hooks/trade";
import PackagesCompare from "./PackagesCompare";
import PackagesEditor from "./PackagesEditor";

export default function ListingPackages({
  listingId,
  isOwner,
  providerName,
  initial,
}: {
  listingId: string;
  isOwner: boolean;
  providerName: string;
  initial?: ServicePackage[];
}) {
  const { t } = useTranslation(["common"]);
  const sdk = useSdk();
  const res = useResource<ServicePackage[]>(() => sdk.packages.list(listingId), [listingId, sdk], { fallback: initial ?? [] });
  const packages = res.data ?? initial ?? null;
  if (packages === null) return null;

  if (isOwner) {
    return (
      <PackagesEditor
        key={packages.map((p) => p.id).join(",")}
        packages={packages}
        onSave={async (input) => {
          try {
            res.setData(await sdk.packages.upsert(listingId, input));
          } catch (e) {
            throw new Error(errorText(e, t("common:state.actionFailed")));
          }
        }}
        onRemove={async (id) => {
          await sdk.packages.remove(listingId, id);
          await res.refresh();
        }}
      />
    );
  }

  return (
    <PackagesCompare
      packages={packages}
      providerName={providerName}
      onRequest={async (pkg, message) => {
        const key = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${pkg.id}-${Date.now()}`;
        try {
          const out = await sdk.packages.request(listingId, pkg.id, message, key);
          return out.enquiry.id;
        } catch (e) {
          throw new Error(errorText(e, t("common:state.actionFailed")));
        }
      }}
    />
  );
}
