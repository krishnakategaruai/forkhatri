"use client";

// ======================================================================
// [Trust pack §3, 2026-09-30] Every restriction has a reason and a human
// appeal. One card per restricted post or profile: what happened
// ("Paused by Vyapar"), why ("reported by people who were asked for
// money"), what happens next (the server's `message`), and Appeal in place
// while `can_appeal`. Used on the Restrictions screen and as the banner on
// the restricted post or profile itself (`compact`). All wording arrives
// localized from the API; nothing here maps an enum.
// ======================================================================

import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ChevronRight, EyeOff, PauseCircle, ShieldAlert, ShieldOff } from "lucide-react";
import type { Restriction } from "@/lib/sdk";
import { formatDate } from "@/lib/format";
import AppealForm from "./AppealForm";

function visual(kind: string) {
  switch (kind) {
    case "removed":
    case "suspended":
      return { icon: ShieldOff, tint: "danger" as const };
    case "paused":
    case "held":
      return { icon: PauseCircle, tint: "warning" as const };
    case "hidden":
      return { icon: EyeOff, tint: "warning" as const };
    default:
      return { icon: ShieldAlert, tint: "warning" as const };
  }
}

export default function RestrictionCard({ item, onChanged, compact = false }: { item: Restriction; onChanged?: () => void; compact?: boolean }) {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const [open, setOpen] = useState(false);
  const [sent, setSent] = useState(false);
  const v = visual(item.restriction);
  const Icon = v.icon;
  const href = item.object_kind === "opportunity" ? `/opportunities/${item.object_id}` : item.object_kind === "listing" ? `/listings/${item.object_id}` : null;
  const canAppeal = item.can_appeal && !!item.case_id && !item.appeal_state && !sent;

  return (
    <article className={`vy-card vy-restrict${compact ? " vy-restrict-compact" : ""}`} aria-label={item.restriction_label}>
      <div className="vy-restrict-head">
        <span className="vy-acct-tile" data-tint={v.tint} aria-hidden="true">
          <Icon size={20} strokeWidth={1.9} />
        </span>
        <div className="vy-restrict-text">
          <span className="vy-restrict-label">{item.restriction_label}</span>
          {!compact && item.title && (
            <strong className="vy-restrict-title">
              {href ? (
                <Link href={href} transitionTypes={["vy-forward"]}>
                  {item.title}
                  <ChevronRight size={15} strokeWidth={2} aria-hidden="true" />
                </Link>
              ) : (
                item.title
              )}
            </strong>
          )}
          {item.reason_label && <span className="vy-restrict-reason">{t("trustSafety:restrictions.reason", { reason: item.reason_label })}</span>}
        </div>
      </div>
      {(sent || item.appeal_state) ? (
        <p className="vy-restrict-message">{t("trustSafety:restrictions.appealSent")}</p>
      ) : (
        item.message && <p className="vy-restrict-message">{item.message}</p>
      )}
      {canAppeal && !open && (
        <button type="button" className="vy-btn vy-btn-secondary vy-restrict-appeal" onClick={() => setOpen(true)}>
          {item.appeal_deadline
            ? `${t("trustSafety:outcomes.appeal")} · ${t("trustSafety:outcomes.appealBy", { date: formatDate(item.appeal_deadline, i18n.language) })}`
            : t("trustSafety:outcomes.appeal")}
        </button>
      )}
      {canAppeal && open && item.case_id && (
        <AppealForm
          caseId={item.case_id}
          onCancel={() => setOpen(false)}
          onDone={() => {
            setOpen(false);
            setSent(true);
            onChanged?.();
          }}
        />
      )}
    </article>
  );
}
