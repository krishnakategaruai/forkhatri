"use client";

// [Voice interview 2026-09-30] The way in: one prominent card, "Talk
// instead — answer a few questions" (posting) or "Set up by talking"
// (profile and first run). Typing stays the normal path right beside it.
import { useTranslation } from "react-i18next";
import { ChevronRight, Mic } from "lucide-react";

export default function VoiceEntry({ variant, onStart, compact = false }: { variant: "post" | "profile"; onStart: () => void; compact?: boolean }) {
  const { t } = useTranslation("voice");
  return (
    <button type="button" className="vy-talk-entry" data-compact={compact ? "" : undefined} onClick={onStart}>
      <span className="vy-talk-entry-icon" aria-hidden="true">
        <Mic size={compact ? 22 : 26} />
      </span>
      <span className="vy-talk-entry-text">
        <strong>{variant === "post" ? t("voice:entry.postTitle") : t("voice:entry.profileTitle")}</strong>
        <span>{variant === "post" ? t("voice:entry.postBody") : t("voice:entry.profileBody")}</span>
      </span>
      <ChevronRight size={20} aria-hidden="true" className="vy-talk-entry-go" />
    </button>
  );
}
