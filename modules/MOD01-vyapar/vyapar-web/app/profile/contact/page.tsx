"use client";

// [FE2 — imp-backend-b §1] Profile → Contact & calling: the member's
// account-wide calling preferences. Every profile follows these unless the
// owner sets its own hours on that profile (see ListingContactOverride).
// Desktop: the form on the left, the live "what people see" sentence in a
// sticky right column; phone: the sentence sits right under the form, above
// the Save button, so the effect is read before saving.
// [Design language 2026-09-29] Page header with the way back; the form in
// one card; Save is the one brand button.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Check } from "lucide-react";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DisabledReason from "@/app/components/DisabledReason";
import PageHeader from "@/app/components/account/PageHeader";
import ContactPreferencesForm, { ContactPreview, toValue, type ContactPrefsValue } from "@/app/components/contact/ContactPreferencesForm";
import { errorText, useContactPreferences } from "@/app/hooks/trade";
import "@/app/styles/account-2026.css";

export default function ContactPreferencesPage() {
  const { t } = useTranslation(["contact", "common"]);
  const prefs = useContactPreferences();
  const [draft, setDraft] = useState<ContactPrefsValue | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const value = draft ?? (prefs.data ? toValue(prefs.data) : null);
  const dirty = draft !== null;

  async function save() {
    if (!value) return;
    setSaving(true);
    setError(null);
    try {
      await prefs.save({ ...value, reset: [] });
      setDraft(null);
      setSaved(true);
    } catch (e) {
      setError(errorText(e, t("common:state.actionFailed")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Screen width="wide">
      <PageHeader title={t("contact:prefs.title")} purpose={t("contact:prefs.subtitle")} backHref="/profile" backLabel={t("contact:prefs.back")} />
      {!value ? (
        <SkeletonGrid count={2} grid={false} />
      ) : (
        <div className="vy-prefs">
          <div className="vy-card vy-acct-card" style={{ gap: 20 }}>
            <ContactPreferencesForm
              value={value}
              onChange={(v) => {
                setDraft(v);
                setSaved(false);
              }}
              disabled={saving}
            />
            <div className="vy-mobile-only">
              <ContactPreview value={value} />
            </div>
            {error && <p className="vy-error" role="alert">{error}</p>}
            <div className="vy-row" style={{ gap: 12, flexWrap: "wrap" }}>
              <button className="vy-btn vy-btn-primary" aria-describedby={!dirty && !saved ? "why-contact" : undefined} disabled={!dirty || saving} onClick={save}>
                {saving ? t("contact:prefs.saving") : t("contact:prefs.save")}
              </button>
              {saved && !dirty && (
                <span className="vy-acct-trust" role="status">
                  <Check size={16} strokeWidth={2.25} aria-hidden="true" />
                  {t("contact:prefs.saved")}
                </span>
              )}
            </div>
            <DisabledReason id="why-contact" show={!dirty && !saved}>{t("common:disabled.noChanges")}</DisabledReason>
          </div>
          <aside className="vy-prefs-aside vy-desktop-only">
            <ContactPreview value={value} />
          </aside>
        </div>
      )}
    </Screen>
  );
}
