"use client";

// [FE2 — imp-backend-b §1, research §4] Call and WhatsApp on an accepted
// enquiry thread.
//
// Two equal-weight secondary buttons — the accent stays on the thread's own
// primary action. Numbers and links come only from the server after both
// sides accepted (`revealed`); nothing is shown before that. Each tap is
// recorded FIRST (POST contact-attempts) and only then is tel: / wa.me
// opened, so the callee's daily cap and the "You contacted X on …" line are
// always true (critique L4: the link now opens first, inside the tap, and
// the attempt is recorded straight after with fetch keepalive). When a call can't be made right now — outside their hours, a
// day off, their daily cap reached, or only matching people may call — the
// button stays visible but disabled, with the server's own sentence saying
// why and when the next window opens; WhatsApp is never capped by hours.
import { useTranslation } from "react-i18next";
import type { ContactAction, ContactActions as ContactActionsData, ContactChannel } from "@/lib/sdk";
import Icon from "@/app/components/Icon";
import { formatDateTime } from "@/lib/format";
import { describeWindow } from "./callWindow";

export interface ContactActionsViewProps {
  data: ContactActionsData;
  busy: ContactChannel | null;
  error: string | null;
  onContact: (action: ContactAction) => void;
  /** Other revealed channels (email…) that have no action button; phone is already the Call button. */
  otherContacts?: { channel: string; value: string }[];
  /** One calm safety line ("Never pay in advance…"), shown once, inside this card. */
  safetyLine?: string;
}

/** "tel:+919000000008" → "+91 90000 00008" (Indian grouping), shown small under the buttons. */
export function numberFromHref(href: string | null | undefined): string | null {
  if (!href || !href.startsWith("tel:")) return null;
  const raw = href.slice(4);
  const m = raw.match(/^\+91(\d{5})(\d{5})$/);
  return m ? `+91 ${m[1]} ${m[2]}` : raw;
}

export function ContactActionsView({ data, busy, error, onContact, otherContacts = [], safetyLine }: ContactActionsViewProps) {
  const { t, i18n } = useTranslation(["contact"]);
  if (!data.revealed || data.contact_actions.length === 0) return null;

  const name = data.counterpart_name ?? t("contact:thread.them");
  const ordered = [...data.contact_actions].sort((a, b) => (a.channel === "call" ? -1 : b.channel === "call" ? 1 : 0));
  const call = ordered.find((a) => a.channel === "call");
  const callWindow = call?.available_now ? describeWindow(call.window, i18n.language) : null;
  const windowLine =
    callWindow && (callWindow.days || callWindow.hours)
      ? t("contact:thread.takesCalls", {
          days: callWindow.days ?? t("contact:preview.everyDay"),
          hours: callWindow.hours ?? t("contact:preview.anyTime"),
        })
      : null;
  const blocked = ordered.filter((a) => !a.available_now || !a.href);
  const history = data.attempts.slice(0, 3);
  const number = numberFromHref(call?.href ?? null);

  return (
    <section className="vy-card vy-card-nested vy-contact" aria-labelledby="contact-title">
      <strong id="contact-title">{t("contact:thread.youCanCall", { name })}</strong>
      <div className="vy-contact-row">
        {ordered.map((a) => {
          const enabled = a.available_now && !!a.href;
          const label = a.channel === "call" ? t("contact:thread.call") : t("contact:thread.whatsapp");
          const icon = a.channel === "call" ? "phone" : "whatsapp";
          if (!enabled) {
            return (
              <button key={a.channel} type="button" className="vy-btn vy-btn-secondary" disabled aria-describedby={`contact-why-${a.channel}`}>
                <Icon name={icon} size={17} /> {label}
              </button>
            );
          }
          return (
            <a
              key={a.channel}
              href={a.href ?? undefined}
              className="vy-btn vy-btn-secondary"
              aria-busy={busy === a.channel}
              onClick={(e) => {
                e.preventDefault();
                if (!busy) onContact(a);
              }}
            >
              <Icon name={icon} size={17} /> {busy === a.channel ? t("contact:thread.opening") : label}
            </a>
          );
        })}
      </div>
      {blocked.map((a) => (
        <p key={a.channel} id={`contact-why-${a.channel}`} className="vy-contact-reason">
          {a.reason_label ?? t("contact:thread.unavailable")}
        </p>
      ))}
      {(number || windowLine) && (
        <p className="vy-muted">{[number, windowLine].filter(Boolean).join(" · ")}</p>
      )}
      {otherContacts.map((c) => (
        <p key={c.channel} className="vy-muted">
          {t(`contact:channel.${c.channel}`, { defaultValue: c.channel })}: {c.value}
        </p>
      ))}
      {error && <p className="vy-error">{error}</p>}
      {history.length > 0 && (
        <ul className="vy-contact-history" aria-label={t("contact:thread.historyLabel")}>
          {/* Written here rather than using the server's `summary`, whose
              clock is UTC: the time must read in India time. */}
          {history.map((h) => {
            const vars = {
              name,
              channel: h.channel === "call" ? t("contact:thread.byCall") : t("contact:thread.byWhatsapp"),
              when: formatDateTime(h.at, i18n.language),
            };
            return <li key={h.id}>{h.mine ? t("contact:thread.youContacted", vars) : t("contact:thread.theyContacted", vars)}</li>;
          })}
        </ul>
      )}
      <p className="vy-muted" style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
        <Icon name="lock" size={13} style={{ marginTop: 3 }} />
        <span>
          {t("contact:thread.sharedBecause", { name })}
          {safetyLine ? ` ${safetyLine}` : ""}
        </span>
      </p>
    </section>
  );
}
