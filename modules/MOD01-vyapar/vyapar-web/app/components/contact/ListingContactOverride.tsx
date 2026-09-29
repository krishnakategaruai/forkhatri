"use client";

// [FE2 — imp-backend-b §1] Per-listing calling hours on the owner's listing
// view. By default a listing follows the account settings; "Own hours for
// this profile" reveals the same compact form and saves every field on the
// listing; switching back sends `reset` for every field so the listing
// inherits again. The live sentence always shows what callers will get.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { ContactPreferenceField } from "@/lib/sdk";
import { errorText, useListingContactPreferences } from "@/app/hooks/trade";
import ContactPreferencesForm, { ContactPreview, toValue, type ContactPrefsValue } from "./ContactPreferencesForm";

const FIELDS: ContactPreferenceField[] = ["call_hours_start", "call_hours_end", "call_days", "max_calls_per_day", "calls_from", "whatsapp_ok", "call_ok"];

export default function ListingContactOverride({ listingId }: { listingId: string }) {
  const { t } = useTranslation(["contact", "common"]);
  const prefs = useListingContactPreferences(listingId);
  const [draft, setDraft] = useState<ContactPrefsValue | null>(null);
  const [customOpen, setCustomOpen] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!prefs.data) return null;

  const hasOverrides = prefs.data.overrides.length > 0;
  const custom = customOpen ?? hasOverrides;
  const value = draft ?? toValue(prefs.data.effective);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setDraft(null);
    } catch (e) {
      setError(errorText(e, t("common:state.actionFailed")));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="vy-card vy-card-nested vy-stack" style={{ gap: 14 }} aria-labelledby="listing-calls-title">
      <div className="vy-stack" style={{ gap: 4 }}>
        <h2 id="listing-calls-title" className="vy-card-title">{t("contact:prefs.listingTitle")}</h2>
        <p className="vy-muted">{t("contact:prefs.listingHint")}</p>
      </div>
      <div className="vy-segmented" role="group" aria-label={t("contact:prefs.listingTitle")}>
        <button
          type="button"
          aria-pressed={!custom}
          disabled={busy}
          onClick={() => {
            setCustomOpen(false);
            if (hasOverrides) void run(() => prefs.save({ reset: FIELDS }));
          }}
        >
          {t("contact:prefs.useAccount")}
        </button>
        <button type="button" aria-pressed={custom} disabled={busy} onClick={() => setCustomOpen(true)}>
          {t("contact:prefs.custom")}
        </button>
      </div>
      {custom ? (
        <>
          <ContactPreferencesForm value={value} onChange={setDraft} disabled={busy} />
          <ContactPreview value={value} />
          <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={busy || (!draft && hasOverrides)} onClick={() => run(() => prefs.save({ ...value }))}>
            {busy ? t("contact:prefs.saving") : t("contact:prefs.save")}
          </button>
        </>
      ) : (
        <>
          <ContactPreview value={value} />
          <Link href="/profile/contact" className="vy-link-btn">{t("contact:prefs.editAccount")}</Link>
        </>
      )}
      {error && <p className="vy-error">{error}</p>}
    </section>
  );
}
