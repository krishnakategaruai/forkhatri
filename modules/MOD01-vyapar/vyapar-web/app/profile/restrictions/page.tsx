"use client";

// [Trust pack §3, 2026-09-30] "Restrictions" — everything of the member's
// that Vyapar restricts right now (listMyRestrictions), each with its
// reason and Appeal in place. Reached from Profile → Settings, where the
// row appears only when something is restricted; opened directly with
// nothing restricted, it says so in one calm line instead of an empty list.
// Traces to: FR41, FR53, imp-trust-pack §3
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ShieldCheck } from "lucide-react";
import type { Restriction } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import PageHeader from "@/app/components/account/PageHeader";
import RestrictionCard from "@/app/components/trust/RestrictionCard";

export default function RestrictionsPage() {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const sdk = useSdk();
  const [items, setItems] = useState<Restriction[] | null>(null);

  const load = useCallback(() => sdk.trustPack.myRestrictions().then(setItems).catch(() => setItems([])), [sdk]);

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load, i18n.language]);

  return (
    <Screen>
      <PageHeader title={t("trustSafety:restrictions.title")} purpose={t("trustSafety:restrictions.purpose")} backHref="/profile" backLabel={t("common:nav.profile")} />
      {items === null && <SkeletonGrid count={2} grid={false} />}
      {items?.length === 0 && (
        <div className="vy-empty">
          <span className="vy-empty-mark" aria-hidden="true">
            <ShieldCheck size={26} strokeWidth={1.9} />
          </span>
          <h3 style={{ color: "var(--text-primary)" }}>{t("trustSafety:restrictions.none")}</h3>
        </div>
      )}
      {items && items.length > 0 && (
        <div className="vy-stack" style={{ gap: 12 }}>
          {items.map((r) => (
            <RestrictionCard key={`${r.object_kind}-${r.object_id}`} item={r} onChanged={load} />
          ))}
        </div>
      )}
    </Screen>
  );
}
