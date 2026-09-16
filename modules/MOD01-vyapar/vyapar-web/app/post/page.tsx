"use client";

// [Design direction / coordinator's "fewer taps" refinement] A single Post
// entry point that asks the one real ambiguity (listing vs. opportunity)
// once, instead of the CommandHub's Post destination silently assuming
// one or the other. Not its own FR — a navigation-clarity fix sitting in
// front of FR01/FR04 (listings/new) and FR11 (opportunities/new).
// [Product-owner i18n rule] Converted to useTranslation().
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";

export default function PostChooserPage() {
  const { t } = useTranslation("discover");
  const router = useRouter();
  return (
    <main className="vy-shell">
      <h1>{t("post.title")}</h1>
      <div className="vy-stack">
        <button className="vy-card" style={{ textAlign: "left", border: "none", cursor: "pointer" }} onClick={() => router.push("/listings/new")}>
          <h2 style={{ fontSize: 17 }}>{t("post.listingTitle")}</h2>
          <p>{t("post.listingDesc")}</p>
        </button>
        <button className="vy-card" style={{ textAlign: "left", border: "none", cursor: "pointer" }} onClick={() => router.push("/opportunities/new")}>
          <h2 style={{ fontSize: 17 }}>{t("post.opportunityTitle")}</h2>
          <p>{t("post.opportunityDesc")}</p>
        </button>
      </div>
    </main>
  );
}
