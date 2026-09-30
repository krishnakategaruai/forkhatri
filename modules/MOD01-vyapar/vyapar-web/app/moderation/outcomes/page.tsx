"use client";

// [TR041] Appeals and outcome communication (FR41) — member side. Every
// decision on the member's own content, with its reason, date and appeal
// deadline; Appeal opens in place on the card (no separate form screen).
// The grievance channel and appeal process are shown on this outcome screen
// itself, as FR53 requires. Reporter identity is never part of this data.
// [Design language 2026-09-29] Page header, the process and grievance lines
// as quiet notes (the Profile hub's "Help & grievance" lands on #grievance),
// each outcome a card with a tinted tile for the action taken. Words per
// GLOSSARY.md: "Post", "Profile", "Request" — never listing/opportunity/
// enquiry.
// Traces to: FR41, FR53, TR041
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { LifeBuoy, ShieldCheck, ShieldAlert, ShieldOff, Scale } from "lucide-react";
import { api } from "@/lib/api";
import AppealForm from "@/app/components/trust/AppealForm";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import PageHeader from "@/app/components/account/PageHeader";
import { formatDate } from "@/lib/format"; // [FE2] Indian date order
import "@/app/styles/account-2026.css";

interface Outcome {
  case_id: string;
  object_kind: string;
  object_id: string;
  action: string;
  reason_code: string | null;
  action_duration_days: number | null;
  decided_at: string;
  appeal_deadline: string;
  appeal_state: string | null;
  can_appeal: boolean;
}

function actionVisual(action: string) {
  switch (action) {
    case "remove":
    case "suspend":
      return { icon: ShieldOff, tint: "danger" as const };
    case "limit":
    case "request_verification":
      return { icon: ShieldAlert, tint: "warning" as const };
    case "restore":
    case "dismiss":
      return { icon: ShieldCheck, tint: "verified" as const };
    default:
      return { icon: Scale, tint: undefined };
  }
}

function OutcomeCard({ item, onDone }: { item: Outcome; onDone: () => void }) {
  const { t, i18n } = useTranslation(["trustSafety", "common"]);
  const [open, setOpen] = useState(false);
  const fmt = (d: string) => formatDate(d, i18n.language);
  const v = actionVisual(item.action);
  const Icon = v.icon;

  return (
    <article className="vy-card vy-acct-outcome">
      <div className="vy-acct-outcome-head">
        <span className="vy-acct-tile" data-tint={v.tint} aria-hidden="true">
          <Icon size={20} strokeWidth={1.9} />
        </span>
        <strong>
          {t(`trustSafety:objectKind.${item.object_kind}` as "objectKind.listing")} · {t(`trustSafety:action.${item.action}` as "action.limit")}
        </strong>
        <span>{t("trustSafety:outcomes.decidedOn", { date: fmt(item.decided_at) })}</span>
      </div>
      {item.reason_code && <p className="vy-acct-hint" style={{ color: "var(--text-secondary)" }}>{t(`trustSafety:reasonCode.${item.reason_code}` as "reasonCode.spam", { defaultValue: item.reason_code })}</p>}
      {item.appeal_state && (
        <span className="vy-badge vy-badge-member-provided" style={{ alignSelf: "flex-start" }}>
          {t(`trustSafety:outcomes.appealState.${item.appeal_state}` as "outcomes.appealState.open")}
        </span>
      )}
      {!item.appeal_state && !item.can_appeal && item.action !== "restore" && <p className="vy-acct-hint">{t("trustSafety:outcomes.windowClosed")}</p>}
      {item.can_appeal && !open && (
        <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => setOpen(true)}>
          {t("trustSafety:outcomes.appeal")} · {t("trustSafety:outcomes.appealBy", { date: fmt(item.appeal_deadline) })}
        </button>
      )}
      {/* [Trust pack] the one appeal form, shared with the Restrictions screen */}
      {item.can_appeal && open && <AppealForm caseId={item.case_id} onDone={onDone} onCancel={() => setOpen(false)} />}
    </article>
  );
}

export default function OutcomesPage() {
  const { t } = useTranslation(["trustSafety", "common", "profile"]);
  const [items, setItems] = useState<Outcome[] | null>(null);

  function load() {
    return api.get<Outcome[]>("/v1/moderation/outcomes").then(setItems);
  }

  useEffect(() => {
    // started after the effect body (no synchronous setState in an effect)
    queueMicrotask(() => void load().catch(() => setItems([])));
  }, []);

  return (
    <Screen>
      <PageHeader title={t("trustSafety:outcomes.title")} purpose={t("trustSafety:outcomes.purpose")} backHref="/profile" backLabel={t("common:nav.profile")} />

      {items === null && <SkeletonGrid count={2} grid={false} />}
      {items?.length === 0 && (
        <div className="vy-empty">
          <span className="vy-empty-mark" aria-hidden="true">
            <ShieldCheck size={26} strokeWidth={1.9} />
          </span>
          <h3 style={{ color: "var(--text-primary)" }}>{t("trustSafety:outcomes.empty")}</h3>
          <p>{t("trustSafety:outcomes.emptyBody")}</p>
        </div>
      )}
      {items && items.length > 0 && (
        <div className="vy-stack" style={{ gap: 12 }}>
          {items.map((o) => (
            <OutcomeCard key={o.case_id} item={o} onDone={load} />
          ))}
        </div>
      )}

      <div className="vy-acct-note" role="note">
        <Scale size={18} strokeWidth={2} aria-hidden="true" />
        <span>{t("trustSafety:outcomes.process")}</span>
      </div>
      <section id="grievance" className="vy-card vy-acct-card" aria-labelledby="grievance-title">
        <div className="vy-acct-card-head">
          <span className="vy-acct-tile" data-tint="teal" aria-hidden="true">
            <LifeBuoy size={20} strokeWidth={1.9} />
          </span>
          <h2 id="grievance-title">{t("trustSafety:outcomes.grievanceTitle")}</h2>
          <p>{t("trustSafety:report.grievance")}</p>
        </div>
      </section>
    </Screen>
  );
}
