"use client";

// [Start flow 2026-10 — decision 12] Results first: the one line that says
// what just happened. A worker reads "You're on Vyapar. Hirers near
// Kukatpally can now find you as a plumber." A seller reads "You're visible
// to customers near Lajpat Nagar" with a WhatsApp share. When the profile
// stayed a draft the card says so plainly and names the way out.
import { useTranslation } from "react-i18next";
import { Share2, Sparkles } from "lucide-react";
import type { MyProfile } from "@/app/components/account/useMyProfile";

export default function StartOutcomeCard({ kind, me, live, blocked, skillLabel }: {
  kind: "work" | "visible";
  me: MyProfile | null;
  live: boolean;
  blocked: string | null;
  skillLabel: (slug: string) => string;
}) {
  const { t } = useTranslation(["firstRun"]);
  const place = me?.locality ?? "";
  const trades = (me?.skills ?? []).slice(0, 3).map(skillLabel).join(", ");
  const profileId = me?.business?.id ?? me?.work?.id ?? null;
  const url = typeof window !== "undefined" && profileId ? `${window.location.origin}/listings/${profileId}` : "";
  const shareText = t("firstRun:outcome.shareText", { name: me?.business?.name ?? me?.name ?? "", trades, place, url });

  const line = live
    ? kind === "visible"
      ? t("firstRun:outcome.visible", { place })
      : t("firstRun:outcome.work", { place, trades })
    : t(`firstRun:outcome.draft.${blocked === "verify_contact_first" ? "verifyContact" : blocked === "acceptance_required" ? "acceptance" : "review"}`);

  return (
    <section className={`vy-card vy-outcome${live ? " vy-outcome-live" : ""}`} role="status">
      <span className="vy-trade-tile vy-trade-green" aria-hidden="true">
        <Sparkles size={20} strokeWidth={1.9} />
      </span>
      <div className="vy-outcome-text">
        <p>{line}</p>
        {kind === "visible" && live && url && (
          <a className="vy-btn vy-btn-secondary vy-outcome-share" href={`https://wa.me/?text=${encodeURIComponent(shareText)}`} target="_blank" rel="noopener noreferrer">
            <Share2 size={16} aria-hidden="true" /> {t("firstRun:outcome.shareWhatsApp")}
          </a>
        )}
      </div>
    </section>
  );
}
