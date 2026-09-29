"use client";

/* The eye button (DEC-V1-034). A family's number and email stay hidden until
 * the agent taps the eye; that tap is written down where the family can see
 * it and, for a family who is not the agent's client, uses one of the day's
 * opens (opening them again within 30 days is free). Once open, the agent can
 * call, WhatsApp or email straight from here. */

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { contactFor, type ContactPerson } from "@/lib/agents";

function EyeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

/** "+91 98000 00002": how Indian numbers are read aloud and written. */
function showPhone(phone: string): string {
  const m = /^\+91(\d{5})(\d{5})$/.exec(phone.replace(/\s/g, ""));
  return m ? `+91 ${m[1]} ${m[2]}` : phone;
}

/** Digits only, for wa.me links (India's numbers keep their 91). */
function waDigits(phone: string): string {
  return phone.replace(/[^\d]/g, "");
}

export default function ContactReveal({
  memberAccountId,
  isClient = false,
  openedBefore = false,
  onOpened,
}: {
  memberAccountId: string;
  isClient?: boolean;
  /** Opened by this agent in the last 30 days: free to see again. */
  openedBefore?: boolean;
  /** Told after a successful open, so the caller can refresh its counts. */
  onOpened?: (counted: boolean) => void;
}) {
  const { t } = useTranslation(["agents"]);
  const [people, setPeople] = useState<ContactPerson[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const open = async () => {
    setBusy(true);
    const out = await contactFor(memberAccountId);
    setBusy(false);
    if (out.ok) {
      setPeople(out.data);
      setError(null);
      onOpened?.(!isClient && !openedBefore);
    } else {
      setError(out.message ?? t("agents:reveal.failed"));
    }
  };

  if (people) {
    const any = people.some((p) => p.phone || p.email);
    return (
      <div className="ag-reveal ag-reveal--open">
        {!any && <span className="caption">{t("agents:reveal.none")}</span>}
        {people.map((p) => (
          <div key={p.account_id} className="ag-reveal__person">
            <span className="ag-reveal__who">
              {p.display_name}
              {p.relation !== "self" && ` (${t(`agents:clients.relation.${p.relation}`, { defaultValue: p.relation })})`}
            </span>
            {p.phone && (
              <span className="ag-reveal__ways">
                <a href={`tel:${p.phone}`} aria-label={`${t("agents:reveal.call")} ${showPhone(p.phone)}`}>
                  {showPhone(p.phone)}
                </a>
                <a href={`https://wa.me/${waDigits(p.phone)}`} target="_blank" rel="noreferrer" className="ag-reveal__link">
                  {t("agents:reveal.whatsapp")}
                </a>
              </span>
            )}
            {p.email && (
              <span className="ag-reveal__ways">
                <a href={`mailto:${p.email}`}>{p.email}</a>
              </span>
            )}
          </div>
        ))}
        <span className="caption">{t("agents:reveal.logged")}</span>
      </div>
    );
  }

  const hint = isClient
    ? t("agents:reveal.client")
    : openedBefore
      ? t("agents:reveal.free")
      : null;

  return (
    <div className="ag-reveal">
      <button type="button" className="btn btn--secondary btn--sm ag-reveal__eye" onClick={open} disabled={busy}>
        <EyeIcon />
        <span className="ag-reveal__mask" aria-hidden="true">
          ••••• •••••
        </span>
        <span>{t("agents:reveal.show")}</span>
      </button>
      {hint && <span className="caption">{hint}</span>}
      {error && <p className="ag-error">{error}</p>}
    </div>
  );
}
