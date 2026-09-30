"use client";

import { useTranslation } from "react-i18next";

/* Mangalya's loading state (owner, 2026-09-24: "Seeta Rama image to be used
 * as loading"). The same Seeta–Rama Kalyanam as the splash, small and
 * breathing inside a turning kolam ring, so a wait reads as the brand's
 * moment rather than a bare "Loading…". Used for whole-screen waits only;
 * lists keep their skeletons, which show the shape of what is coming. */
export default function SacredLoader({ inline = false }: { inline?: boolean }) {
  const { t } = useTranslation("common");
  return (
    <div
      className={`sloader${inline ? " sloader--inline" : ""}`}
      role="status"
      aria-live="polite"
    >
      <span className="sloader__ring" aria-hidden="true" />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="sloader__art"
        src="/art/seeta-rama-kalyanam-sm.webp"
        alt=""
        width={420}
        height={504}
      />
      <span className="sloader__text">{t("common:state.loading")}</span>
    </div>
  );
}
