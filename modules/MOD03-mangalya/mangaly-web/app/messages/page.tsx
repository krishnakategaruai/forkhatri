"use client";

import { useTranslation } from "react-i18next";

/* FR049 · UX21 · DEC-V1-026. The inbox itself is drawn by the layout; this is
 * the right-hand pane on a desktop before a conversation is chosen. */
export default function MessagesPage() {
  const { t } = useTranslation(["messages"]);
  return (
    <div className="mpane__empty">
      <svg viewBox="0 0 64 64" aria-hidden="true">
        <path d="M10 14h32v22H22l-10 8V14z" />
        <path d="M46 24h8v22l-8-6H30v-4" />
      </svg>
      <p className="mpane__empty-title">{t("messages:list.pickTitle")}</p>
      <p className="caption">{t("messages:list.pickBody")}</p>
    </div>
  );
}
