"use client";

// [FE2 — imp-backend-b "Pre-accept calling", owner-approved critique L1]
// Call and WhatsApp straight from an opportunity, before applying — the way
// WorkIndia and Apna candidates reach an HR number — but only inside the
// poster's own rules (their hours, their daily cap, matching skills only).
//
// Call is the filled accent button (it is the primary way this audience
// responds to a job); WhatsApp is a quiet icon button beside it. tel: / wa.me
// opens inside the tap and the attempt is recorded right after (keepalive). When a
// button can't be used right now, the reason is one calm line with the next
// window or the alternative ("Calls open tomorrow, 10 am", "Daily call limit
// reached — apply instead"). When the poster doesn't take calls before an
// application (`precall_off`), nothing renders at all.
//
// Exports the presentational <PrecallActionsView> and a self-loading default
// <PrecallActions opportunityId=…> (usePrecallActions + the record-then-open
// order is "open, then record": critique L4). FE1 mounts the default export in the opportunity action bar next
// to Apply.
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import type { ContactAction, ContactChannel, PrecallActions as PrecallData, PrecallAttemptResult } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { formatClock, formatDayMonth } from "@/lib/format";
import Icon from "@/app/components/Icon";
import { useResource } from "@/app/hooks/useResource";
import { errorText } from "@/app/hooks/trade";
import { openContactNow } from "@/lib/contactTap";

// ---- data hook ---------------------------------------------------------------

export function usePrecallActions(opportunityId: string, enabled = true) {
  const sdk = useSdk();
  const res = useResource<PrecallData>(() => sdk.contact.precallActions(opportunityId), [opportunityId, sdk], { enabled });
  const record = useCallback(
    async (channel: ContactChannel) => {
      const next = await sdk.contact.recordPrecallAttempt(opportunityId, channel);
      res.setData(next);
      return next;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [opportunityId, sdk],
  );
  return { ...res, record };
}

// ---- words ---------------------------------------------------------------------

/** "today, 10 am" / "tomorrow, 10 am" / "29 Sep, 10 am" — India time. */
function useWhen() {
  const { t, i18n } = useTranslation(["contact"]);
  return (iso: string): string => {
    const lang = i18n.language;
    const at = new Date(iso);
    const ist = (d: Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
    const hm = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: false }).format(at);
    const time = formatClock(hm, lang);
    const today = ist(new Date());
    const tomorrow = ist(new Date(Date.now() + 86_400_000));
    const day = ist(at);
    if (day === today) return t("contact:precall.today", { time });
    if (day === tomorrow) return t("contact:precall.tomorrow", { time });
    return t("contact:precall.onDay", { day: formatDayMonth(day, lang), time });
  };
}

export function usePrecallReason() {
  const { t } = useTranslation(["contact"]);
  const when = useWhen();
  // With an application already open, "apply instead" would be wrong advice:
  // point to the application's messages instead.
  return (a: ContactAction, hasApplication = false): string | null => {
    if (a.available_now && a.href) return null;
    switch (a.reason) {
      case "outside_hours":
      case "day_off":
        return a.next_window ? t("contact:precall.opensAt", { when: when(a.next_window) }) : t("contact:precall.closedNow");
      case "daily_cap_reached":
        return hasApplication ? t("contact:precall.capReachedApplied") : t("contact:precall.capReached");
      case "caller_limit_reached":
        return hasApplication ? t("contact:precall.callerLimitApplied") : t("contact:precall.callerLimit");
      case "not_matching":
        return t("contact:precall.notMatching");
      default:
        return a.reason_label ?? t("contact:thread.unavailable");
    }
  };
}

// ---- view -----------------------------------------------------------------------

export function PrecallActionsView({
  data,
  busy,
  error,
  onContact,
  applicationId,
}: {
  data: PrecallData;
  busy: ContactChannel | null;
  error: string | null;
  onContact: (action: ContactAction) => void;
  /** Set after a tap opened an application for the caller: links to it. */
  applicationId?: string | null;
}) {
  const { t } = useTranslation(["contact"]);
  const reasonOf = usePrecallReason();
  const actions = data.contact_actions.filter((a) => a.reason !== "precall_off");
  // Nothing to offer: switch off, own post, no usable number, or a block (reads as off).
  if (!data.allow_precall || (data.reason && !data.available) || actions.length === 0) return null;
  const call = actions.find((a) => a.channel === "call");
  const wa = actions.find((a) => a.channel === "whatsapp");
  const usable = (a?: ContactAction) => !!a && a.available_now && !!a.href;
  // One line: the call's reason if Call is blocked, else WhatsApp's.
  const openApplication = applicationId ?? data.application_enquiry_id ?? null;
  const reason = (call && reasonOf(call, !!openApplication)) || (wa && !usable(wa) ? reasonOf(wa, !!openApplication) : null);

  return (
    <div className="vy-precall">
      <div className="vy-precall-row">
        {call && (
          <button
            type="button"
            // a blocked call must not look like the page's main action
            className={usable(call) ? "vy-btn vy-btn-primary" : "vy-btn vy-btn-secondary"}
            disabled={!usable(call) || busy !== null}
            aria-describedby={reason ? "precall-why" : undefined}
            onClick={() => onContact(call)}
          >
            <Icon name="phone" size={17} /> {busy === "call" ? t("contact:thread.opening") : t("contact:precall.call")}
          </button>
        )}
        {wa && (
          <button
            type="button"
            className="vy-btn vy-btn-secondary vy-precall-wa"
            disabled={!usable(wa) || busy !== null}
            aria-label={t("contact:precall.whatsapp")}
            title={t("contact:precall.whatsapp")}
            onClick={() => onContact(wa)}
          >
            <Icon name="whatsapp" size={19} />
          </button>
        )}
      </div>
      {reason && (
        <p id="precall-why" className="vy-contact-reason">
          {reason}
        </p>
      )}
      {/* Only the fresh confirmation: an application that already existed is
          shown by the action bar's own "Applied ✓ · Open conversation". */}
      {applicationId && (
        <p className="vy-muted">
          {t("contact:precall.applied")}{" "}
          <Link className="vy-link-btn" href={`/enquiries/${applicationId}`}>{t("contact:precall.openApplication")}</Link>
        </p>
      )}
      {error && <p className="vy-error">{error}</p>}
    </div>
  );
}

// ---- self-loading block -------------------------------------------------------

export default function PrecallActions({ opportunityId, enabled = true }: { opportunityId: string; enabled?: boolean }) {
  const { t } = useTranslation(["common"]);
  const { data, record } = usePrecallActions(opportunityId, enabled);
  const [busy, setBusy] = useState<ContactChannel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [applicationId, setApplicationId] = useState<string | null>(null);
  if (!data) return null;

  // Critique L4: the dialler / WhatsApp opens inside the tap; the attempt
  // is recorded right after (keepalive), not before.
  function contact(action: ContactAction) {
    const channel = action.channel as ContactChannel;
    const href = action.href;
    if (!href) return;
    setError(null);
    setBusy(channel);
    openContactNow(channel, href);
    record(channel)
      .then((res: PrecallAttemptResult) => {
        if (res.application_created && res.application_enquiry_id) setApplicationId(res.application_enquiry_id);
      })
      .catch((e) => setError(errorText(e, t("common:state.actionFailed"))))
      .finally(() => setBusy(null));
  }

  return <PrecallActionsView data={data} busy={busy} error={error} onContact={contact} applicationId={applicationId} />;
}
