"use client";

// [FE2 — imp-backend-b §2] "Nobody charges job seekers" — a calm notice on
// an employment opportunity. The title, body and report label come from the
// server already translated (seeker_protection on the detail read), so the
// wording is the same one the moderation rules enforce. The report action
// does not open a new screen: it asks the page's own report sheet (in place,
// further down) to open with "Asked me for money" already chosen, and
// scrolls to it.
import type { SeekerProtection } from "@/lib/sdk";
import Icon from "@/app/components/Icon";
import { requestReport } from "@/app/components/ReportSheet";

export default function SeekerProtectionNotice({
  protection,
  objectId,
}: {
  protection: SeekerProtection | null | undefined;
  objectId: string;
}) {
  if (!protection || !protection.applies) return null;
  return (
    <aside className="vy-card vy-card-nested vy-seeker-notice" aria-label={protection.title}>
      <span className="vy-seeker-notice-mark" aria-hidden="true">
        <Icon name="shield" size={18} />
      </span>
      <div className="vy-stack" style={{ gap: 4 }}>
        <strong>{protection.title}</strong>
        <p style={{ fontSize: 14 }}>{protection.body}</p>
        <button
          type="button"
          className="vy-link-btn"
          onClick={() => requestReport(objectId, protection.report_reason ?? "asked_for_money")}
        >
          {protection.report_label}
        </button>
      </div>
    </aside>
  );
}
