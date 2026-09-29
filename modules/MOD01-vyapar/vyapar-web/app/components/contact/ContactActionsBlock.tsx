"use client";

// [FE2] The self-loading contact block for a thread: useContactActions +
// ContactActionsView, plus the one piece of behaviour that must happen in a
// specific order — record the attempt, THEN open the link.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ContactAction, ContactChannel } from "@/lib/sdk";
import { errorText, useContactActions } from "@/app/hooks/trade";
import { ContactActionsView } from "./ContactActions";
import { openContactNow } from "@/lib/contactTap";

// open/awaiting too: a shortlisted applicant's number can be revealed before hire
const REVEALED_STATES = ["open", "awaiting_response", "in_progress", "resolved"];

export default function ContactActionsBlock({
  enquiryId,
  enquiryState,
  disclosedContacts = [],
  safetyLine,
  fallback = null,
}: {
  enquiryId: string;
  enquiryState: string;
  /** The thread's revealed contacts; the phone becomes the Call button, the rest are listed in the card. */
  disclosedContacts?: { channel: string; value: string }[];
  safetyLine?: string;
  /** What to show when there are no contact actions (the thread's old plain contact block). */
  fallback?: React.ReactNode;
}) {
  const { t } = useTranslation(["contact", "common"]);
  const enabled = REVEALED_STATES.includes(enquiryState);
  const { data, error: loadError, record } = useContactActions(enquiryId, enabled);
  const [busy, setBusy] = useState<ContactChannel | null>(null);
  const [error, setError] = useState<string | null>(null);

  // still loading: render nothing rather than flashing the fallback block
  if (enabled && !data && !loadError) return null;
  // One-way reveal (a shortlisted applicant): say so from this side, calmly.
  if (data && !data.revealed && data.counterpart_can_contact) {
    return <p className="vy-muted">{t("contact:thread.theyMayCall", { name: data.counterpart_name ?? t("contact:thread.them") })}</p>;
  }
  if (!enabled || !data || !data.revealed || data.contact_actions.length === 0) return <>{fallback}</>;

  // Critique L4: open the link inside the tap, then record the attempt
  // (keepalive) without making the person wait for it.
  function contact(action: ContactAction) {
    const channel = action.channel as ContactChannel;
    const href = action.href;
    if (!href) return;
    setError(null);
    setBusy(channel);
    openContactNow(channel, href);
    record(channel)
      .catch((e) => setError(errorText(e, t("common:state.actionFailed"))))
      .finally(() => setBusy(null));
  }

  const hasPhoneAction = data.contact_actions.some((a) => a.channel === "call" || a.channel === "whatsapp");
  const otherContacts = disclosedContacts.filter((c) => !(hasPhoneAction && ["phone", "whatsapp", "mobile"].includes(c.channel)));
  return (
    <ContactActionsView data={data} busy={busy} error={error} onContact={contact} otherContacts={otherContacts} safetyLine={safetyLine} />
  );
}
