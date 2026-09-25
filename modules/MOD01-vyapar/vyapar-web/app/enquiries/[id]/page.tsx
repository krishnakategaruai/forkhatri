"use client";

// [TR023/TR024] Provider manages the Enquiry lifecycle (FR23); consent-
// based contact disclosure and blocking (FR24).
// [IMP33] The thread itself now lives in <EnquiryThread> so the exact
// same implementation can render here (the phone route, the notification
// target, the shareable URL) and in the ≥1024px split pane on
// /enquiries/mine — one implementation, two placements. See that
// component's header for why this is an extraction and not a second
// rendering path.
// Traces to: FR23, FR24, TR023, TR024; 04-ui.md F4
import { use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import Screen from "@/app/components/Screen";
import EnquiryThread from "@/app/components/EnquiryThread";

export default function EnquiryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["enquiries", "common"]);

  // [IMP39] wide shell: the thread lays itself out as conversation + context
  // aside once it has the room (see EnquiryThread's header).
  return (
    <Screen width="wide">
      {/* [IMP33] `transitionTypes={["vy-back"]}` makes this a *backward*
          navigation, so the route slides in the opposite direction to the
          one that brought the person here — the directional convention
          documented in the Next.js view-transitions guide. Without it,
          going back looked identical to going deeper. */}
      <Link
        href="/enquiries/mine"
        transitionTypes={["vy-back"]}
        className="vy-btn vy-btn-ghost"
        style={{ alignSelf: "flex-start", textDecoration: "none" }}
      >
        ← {t("enquiries:mine.title")}
      </Link>
      <EnquiryThread id={id} />
    </Screen>
  );
}
