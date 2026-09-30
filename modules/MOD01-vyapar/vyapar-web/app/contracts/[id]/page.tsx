"use client";

// [FE2 — imp-backend-d] /contracts/[id] — the contract page (the phone
// route, the notification target and the shareable URL). The detail itself
// is <ContractDetail>, which the ≥1024px split pane on /contracts also uses.
import { use } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ChevronLeft } from "lucide-react";
import Screen from "@/app/components/Screen";
import ContractDetail from "@/app/components/contracts/ContractDetail";
import "@/app/styles/deals-2026.css";

export default function ContractPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { t } = useTranslation(["contracts"]);
  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href="/contracts" transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {t("contracts:detail.back")}
        </Link>
        <ContractDetail id={id} />
      </div>
    </Screen>
  );
}
