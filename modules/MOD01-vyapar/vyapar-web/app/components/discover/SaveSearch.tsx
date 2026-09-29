"use client";

// [FE2 — imp-backend-b §5] "Save this search", in place under the applied
// filters: one toggle ("Tell me when new ones match", on by default) and one
// Save — no name to type (the server keeps the filters; the list names it
// from them), the alert bell on by default. Once saved it says so and links to the list under Activity.
import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { FeedFilterValues } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { errorText } from "@/app/hooks/trade";
import Icon from "@/app/components/Icon";

export default function SaveSearch({ value, name }: { value: FeedFilterValues; name: string }) {
  const { t } = useTranslation(["explore", "common"]);
  const sdk = useSdk();
  const [alert, setAlert] = useState(true);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const key = JSON.stringify(value);
  const [savedFor, setSavedFor] = useState<string | null>(null);

  if (saved && savedFor === key) {
    return (
      <p className="vy-muted" role="status">
        ✓ {alert ? t("explore:saved.doneAlert") : t("explore:saved.done")}{" "}
        <Link className="vy-link-btn" href="/activity#saved-searches">{t("explore:saved.seeAll")}</Link>
      </p>
    );
  }

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const { q, ...filters } = value;
      const s = await sdk.savedSearches.create({ query: q ?? "", name, alert, filters });
      setSaved(s.id);
      setSavedFor(key);
    } catch (e) {
      setError(errorText(e, t("common:state.actionFailed")));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-save-search">
      <button type="button" className="vy-btn vy-btn-secondary" disabled={busy} onClick={save}>
        {t("explore:saved.save")}
      </button>
      <button
        type="button"
        className="vy-bell-toggle"
        aria-pressed={alert}
        title={t("explore:saved.alert")}
        aria-label={t("explore:saved.alert")}
        onClick={() => setAlert((v) => !v)}
      >
        <Icon name="alert" size={16} />
        <span>{alert ? t("explore:saved.alertOn") : t("explore:saved.alertOff")}</span>
      </button>
      {error && <p className="vy-error">{error}</p>}
    </div>
  );
}
