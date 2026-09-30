"use client";

// [Trust pack §2, 2026-09-30] /paid-on-time/{ask_id} — where the
// "Were you paid on time?" notification lands. One question, Yes or No,
// then a quiet thank-you, with a way back to the contract or the thread it
// is about. The API has no single-ask read, so the member's own questions
// are listed (state=all) and this one picked; someone else's question is
// simply "not available" (the API would refuse the answer with 404).
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ChevronRight, CircleHelp } from "lucide-react";
import type { PaidOnTimeAsk } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import PageHeader from "@/app/components/account/PageHeader";
import { PaidOnTimeQuestion } from "@/app/components/trust/PaidOnTime";

export default function PaidOnTimePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const sdk = useSdk();
  const [ask, setAsk] = useState<PaidOnTimeAsk | null | undefined>(undefined);

  useEffect(() => {
    let live = true;
    sdk.trustPack
      .paidOnTimeAsks("all")
      .then((rows) => live && setAsk(rows.find((a) => a.id === id) ?? null))
      .catch(() => live && setAsk(null));
    return () => {
      live = false;
    };
  }, [sdk, id, i18n.language]);

  return (
    <Screen>
      <PageHeader title={t("trustSafety:paidOnTime.title")} backHref="/activity" backLabel={t("common:nav.activity")} />
      {ask === undefined && <div className="vy-skeleton" style={{ height: 180, borderRadius: "var(--radius-card)" }} aria-hidden="true" />}
      {ask === null && (
        <div className="vy-empty">
          <span className="vy-empty-mark" aria-hidden="true">
            <CircleHelp size={26} strokeWidth={1.9} />
          </span>
          <h3 style={{ color: "var(--text-primary)" }}>{t("trustSafety:paidOnTime.notAvailable")}</h3>
        </div>
      )}
      {ask && (
        <div className="vy-stack" style={{ gap: 12 }}>
          <PaidOnTimeQuestion ask={ask} />
          {ask.link && (
            <Link className="vy-pot-context" href={ask.link} transitionTypes={["vy-forward"]}>
              <span>{ask.title}</span>
              <ChevronRight size={18} strokeWidth={2} aria-hidden="true" />
            </Link>
          )}
        </div>
      )}
    </Screen>
  );
}
