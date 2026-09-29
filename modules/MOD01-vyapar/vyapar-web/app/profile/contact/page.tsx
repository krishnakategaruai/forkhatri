"use client";

// [FE2 — imp-backend-b §1] Profile → Calls & WhatsApp: the member's
// account-wide calling preferences. Every listing follows these unless the
// owner sets its own hours on that listing (see ListingContactOverride).
// Desktop: the form on the left, the live "what people see" sentence in a
// sticky right column; phone: the sentence sits right under the form, above
// the Save button, so the effect is read before saving.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import ContactPreferencesForm, { ContactPreview, toValue, type ContactPrefsValue } from "@/app/components/contact/ContactPreferencesForm";
import { errorText, useContactPreferences } from "@/app/hooks/trade";

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
      <Link href="/profile" transitionTypes={["vy-back"]} className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", textDecoration: "none" }}>
        ← {t("contact:prefs.back")}
      </Link>
      <div className="vy-page-head">
        <h1>{t("contact:prefs.title")}</h1>
        <p>{t("contact:prefs.subtitle")}</p>
      </div>
      {!value ? (
        <SkeletonGrid count={2} grid={false} />
      ) : (
        <div className="vy-prefs">
          <div className="vy-card vy-stack" style={{ gap: 20 }}>
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
            {error && <p className="vy-error">{error}</p>}
            <div className="vy-row" style={{ gap: 12 }}>
              <button className="vy-btn vy-btn-primary" disabled={!dirty || saving} onClick={save}>
                {saving ? t("contact:prefs.saving") : t("contact:prefs.save")}
              </button>
              {saved && !dirty && <span className="vy-muted" role="status">✓ {t("contact:prefs.saved")}</span>}
            </div>
          </div>
          <aside className="vy-prefs-aside vy-desktop-only">
            <ContactPreview value={value} />
          </aside>
        </div>
      )}
    </Screen>
  );
}
