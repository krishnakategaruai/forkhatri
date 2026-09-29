"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";

import type { UpgradeRequiredDetail } from "@/lib/billing";
import "./upgrade-nudge.css";

/* [DEC-V1-031] Shown in place where a gated action was refused (HTTP 402,
 * code `upgrade_required`): the daily request allowance, a contact request,
 * the full kundli report. One quiet card, the plan named, a way to the Plans
 * page and a way to say not now. Never a modal. */

type Props = {
  detail: UpgradeRequiredDetail;
  onDismiss?: () => void;
};

export default function UpgradeNudge({ detail, onDismiss }: Props) {
  const { t } = useTranslation(["billing"]);
  const planName = t(`billing:planName.${detail.plan_needed}`);
  const daily = detail.feature === "daily_requests" && detail.limit != null;
  return (
    <div className="card upgrade-nudge" role="status">
      <p className="upgrade-nudge__title">
        {daily ? t("billing:nudge.dailyTitle") : t("billing:nudge.title", { plan: planName })}
      </p>
      <p className="caption upgrade-nudge__body">
        {daily
          ? t("billing:nudge.dailyBody", { limit: detail.limit })
          : detail.message || t("billing:nudge.body", { plan: planName })}
      </p>
      <div className="upgrade-nudge__actions">
        <Link href={`/plans?plan=${detail.plan_needed}`} className="btn btn--primary btn--sm">
          {t("billing:nudge.cta", { plan: planName })}
        </Link>
        {onDismiss && (
          <button type="button" className="btn btn--ghost btn--sm" onClick={onDismiss}>
            {t("billing:action.notNow")}
          </button>
        )}
      </div>
    </div>
  );
}
