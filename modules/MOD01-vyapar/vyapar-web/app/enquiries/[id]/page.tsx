"use client";

// [TR023/TR024] One request: its conversation, the lifecycle actions (FR23)
// and consent-based contact disclosure (FR24). The thread itself is
// <EnquiryThread>, shared with the ≥1024px split pane on /enquiries/mine
// (one implementation, two placements). This route is what a phone uses,
// what a notification opens and what a shared link lands on.
// Traces to: FR23, FR24, TR023, TR024; 04-ui.md F4
import { use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import Screen from "@/app/components/Screen";
import EnquiryThread from "@/app/components/EnquiryThread";
import "@/app/styles/deals-2026.css";

export default function EnquiryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["enquiries", "common"]);

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        {/* [IMP33] a backward navigation slides the other way (Next view-transitions guide). */}
        <Link href="/enquiries/mine" transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
          {t("enquiries:mine.title")}
        </Link>
        <EnquiryThread id={id} />
      </div>
    </Screen>
  );
}
