"use client";

// [Design direction / coordinator's "fewer taps" refinement] A single Post
// entry point that asks the one real ambiguity (listing vs. opportunity)
// once, instead of the CommandHub's Post destination silently assuming
// one or the other. Not its own FR — a navigation-clarity fix sitting in
// front of FR01/FR04 (listings/new) and FR11 (opportunities/new).
// [Product-owner i18n rule] Converted to useTranslation().
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import Screen from "@/app/components/Screen";
import Icon from "@/app/components/Icon";

export default function PostChooserPage() {
  const { t } = useTranslation("discover");
  const router = useRouter();
  // [IMP39] On desktop the two choices sit side by side as real cards
  // (glyph, title, description, arrow); on a phone the glyph and arrow are
  // display:none and the stack is exactly as before.
  return (
    <Screen>
      <h1>{t("post.title")}</h1>
      <div className="vy-stack vy-choice-grid">
        <button className="vy-card vy-choice" onClick={() => router.push("/listings/new")}>
          <span className="vy-choice-mark" aria-hidden="true"><Icon name="listing" size={22} /></span>
          <h2 style={{ fontSize: 17 }}>{t("post.listingTitle")}</h2>
          <p>{t("post.listingDesc")}</p>
          <span className="vy-choice-arrow" aria-hidden="true">→</span>
        </button>
        <button className="vy-card vy-choice" onClick={() => router.push("/opportunities/new")}>
          <span className="vy-choice-mark" aria-hidden="true"><Icon name="opportunity" size={22} /></span>
          <h2 style={{ fontSize: 17 }}>{t("post.opportunityTitle")}</h2>
          <p>{t("post.opportunityDesc")}</p>
          <span className="vy-choice-arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </Screen>
  );
}
