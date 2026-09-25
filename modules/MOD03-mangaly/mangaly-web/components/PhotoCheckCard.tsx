"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getVerification, monthYear, type VerificationStatus } from "@/lib/verification";

import "@/app/me/verify/verify.css";

/* DEC-V1-016 · The quiet entry point on the Me screen: an invitation to the
 * photo check, or — once done — the fact itself with its month. Never a score.
 * Rendered only for the member's own profile, never while a parent is
 * filling in a profile for someone else. */
export default function PhotoCheckCard() {
  const { t, i18n } = useTranslation("verify");
  const [status, setStatus] = useState<VerificationStatus | null>(null);

  useEffect(() => {
    let active = true;
    void getVerification().then((s) => {
      if (active) setStatus(s);
    });
    return () => {
      active = false;
    };
  }, []);

  if (!status || !status.has_profile) return null;
  // Nothing to confirm yet: with no photo the check could only say "add a
  // photo first", a dead end. The invitation appears once a photo exists.
  if (!status.verified && !status.has_photos) return null;

  return (
    <Link href="/me/verify" className="photo-check">
      <span
        className={`photo-check__icon${status.verified ? " is-done" : ""}`}
        aria-hidden="true"
      >
        <svg viewBox="0 0 24 24" width="18" height="18">
          <path
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
            d={
              status.verified
                ? "M5 12.5l4.2 4.2L19 7"
                : "M4 8V6a2 2 0 0 1 2-2h2 M16 4h2a2 2 0 0 1 2 2v2 M20 16v2a2 2 0 0 1-2 2h-2 M8 20H6a2 2 0 0 1-2-2v-2 M9 10h.01 M15 10h.01 M9.5 15a3.5 3.5 0 0 0 5 0"
            }
          />
        </svg>
      </span>
      <span className="photo-check__text">
        <span className="photo-check__title">
          {status.verified ? t("card.confirmed") : t("card.title")}
        </span>
        <span className="caption">
          {status.verified
            ? t("card.since", { date: monthYear(status.verified_at, i18n.language) })
            : t("card.hint")}
        </span>
      </span>
      <span aria-hidden="true" className="photo-check__chev">
        ›
      </span>
    </Link>
  );
}
