"use client";

// [TR036] Six contextual privacy controls, one screen (FR36).
// [TR037] Data export, correction, deletion, consent withdrawal (FR37).
// [TR038] Inspect and confirm derived preferences (FR38).
// One screen, per FR36's own "single Privacy screen" requirement, rather
// than three separate pages — fewer taps to see and change everything about
// what Vyapar shares. Each of the six controls carries a one-sentence
// explanation of who sees what (FR36's own contextual-explainer rule,
// satisfied here as a permanent visible caption rather than a one-time
// interstitial the member would have to remember). Data rights and derived
// preferences sit below as their own sections on the same screen.
// Traces to: FR36, FR37, FR38, TR036, TR037, TR038
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

interface PrivacySettings {
  capability_visible: boolean;
  seeking_visible: boolean;
  contact_disclosure: "public" | "after_accept" | "hidden";
  discoverable: boolean;
  notifications_enabled: boolean;
  commercial_comms: boolean;
  behavioral_analytics: boolean;
  digest_enabled: boolean;
  digest_hour: number;
}

interface DataRequest {
  id: string;
  kind: string;
  state: string;
  created_at: string;
  completed_at: string | null;
}

interface Preference {
  id: string;
  key: string;
  value: Record<string, unknown>;
  evidence: string;
  source: string;
  state: string;
  proposed_at: string;
}

export default function PrivacyPage() {
  const { t, i18n } = useTranslation(["privacy", "common"]);
  const [settings, setSettings] = useState<PrivacySettings | null>(null);
  const [requests, setRequests] = useState<DataRequest[]>([]);
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [exportDoc, setExportDoc] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  async function load() {
    const [s, r, p] = await Promise.all([
      api.get<PrivacySettings>("/v1/privacy"),
      api.get<DataRequest[]>("/v1/privacy/requests"),
      api.get<Preference[]>("/v1/preferences/mine"),
    ]);
    setSettings(s);
    setRequests(r);
    setPreferences(p.filter((x) => x.state !== "removed"));
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function update(field: string, value: unknown) {
    setBusy(true);
    setNotice(null);
    try {
      const updated = await api.patch<PrivacySettings>("/v1/privacy", { [field]: value });
      setSettings(updated);
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function doExport() {
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ document: unknown }>("/v1/privacy/export", {});
      setExportDoc(JSON.stringify(res.document, null, 2));
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function doDelete() {
    setBusy(true);
    setNotice(null);
    try {
      const res = await api.post<{ state: string; reason?: string }>("/v1/privacy/delete", {});
      if (res.state === "blocked") {
        setNotice(res.reason ?? t("privacy:delete.blocked"));
      } else {
        setNotice(t("privacy:delete.done"));
      }
      setConfirmingDelete(false);
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function decidePreference(id: string, action: "confirm" | "decline" | "remove") {
    setBusy(true);
    try {
      await api.post(`/v1/preferences/${id}/${action}`, {});
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (!settings) return <main className="vy-shell"><p className="vy-muted">{t("common:state.loading")}</p></main>;

  const toggleRow = (labelKey: string, helpKey: string, field: keyof PrivacySettings, value: boolean) => (
    <div className="vy-row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
      <div>
        <div>{t(`privacy:control.${labelKey}` as "control.discoverable")}</div>
        <p className="vy-muted" style={{ fontSize: 12, marginTop: 2 }}>{t(`privacy:control.${helpKey}` as "control.discoverableHelp")}</p>
      </div>
      <input type="checkbox" checked={value} disabled={busy} onChange={(e) => update(field, e.target.checked)} />
    </div>
  );

  return (
    <main className="vy-shell">
      <h1>{t("privacy:title")}</h1>
      {notice && <p className="vy-error">{notice}</p>}

      <section className="vy-card vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("privacy:controlsTitle")}</h2>
        {toggleRow("discoverable", "discoverableHelp", "discoverable", settings.discoverable)}
        {toggleRow("capabilityVisible", "capabilityVisibleHelp", "capability_visible", settings.capability_visible)}
        {toggleRow("seekingVisible", "seekingVisibleHelp", "seeking_visible", settings.seeking_visible)}
        <div>
          <div>{t("privacy:control.contactDisclosure")}</div>
          <p className="vy-muted" style={{ fontSize: 12, marginTop: 2, marginBottom: 6 }}>{t("privacy:control.contactDisclosureHelp")}</p>
          <select className="vy-select" value={settings.contact_disclosure} disabled={busy} onChange={(e) => update("contact_disclosure", e.target.value)}>
            <option value="public">{t("privacy:contactOption.public")}</option>
            <option value="after_accept">{t("privacy:contactOption.after_accept")}</option>
            <option value="hidden">{t("privacy:contactOption.hidden")}</option>
          </select>
        </div>
        {toggleRow("notificationsEnabled", "notificationsEnabledHelp", "notifications_enabled", settings.notifications_enabled)}
        {toggleRow("commercialComms", "commercialCommsHelp", "commercial_comms", settings.commercial_comms)}
      </section>

      <section className="vy-card vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("privacy:analyticsTitle")}</h2>
        {toggleRow("behavioralAnalytics", "behavioralAnalyticsHelp", "behavioral_analytics", settings.behavioral_analytics)}
        {toggleRow("digestEnabled", "digestEnabledHelp", "digest_enabled", settings.digest_enabled)}
      </section>

      <section className="vy-stack">
        <h2 style={{ fontSize: 16 }}>{t("privacy:dataRights.title")}</h2>
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={doExport}>{t("privacy:dataRights.export")}</button>
          {!confirmingDelete ? (
            <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => setConfirmingDelete(true)}>{t("privacy:dataRights.delete")}</button>
          ) : (
            <>
              <button className="vy-btn vy-btn-primary" disabled={busy} onClick={doDelete}>{t("privacy:dataRights.confirmDelete")}</button>
              <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => setConfirmingDelete(false)}>{t("common:action.cancel")}</button>
            </>
          )}
        </div>
        {confirmingDelete && <p className="vy-error" style={{ fontSize: 13 }}>{t("privacy:dataRights.deleteWarning")}</p>}
        {exportDoc && (
          <details className="vy-card">
            <summary>{t("privacy:dataRights.exportReady")}</summary>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 11, marginTop: 8 }}>{exportDoc}</pre>
          </details>
        )}
        {requests.length > 0 && (
          <div className="vy-stack" style={{ gap: 4 }}>
            {requests.map((r) => (
              <p key={r.id} className="vy-muted" style={{ fontSize: 13 }}>
                {t(`privacy:requestKind.${r.kind}` as "requestKind.export")} · {t(`privacy:requestState.${r.state}` as "requestState.completed")} · {new Date(r.created_at).toLocaleDateString(i18n.language)}
              </p>
            ))}
          </div>
        )}
      </section>

      {preferences.length > 0 && (
        <section className="vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("privacy:preferences.title")}</h2>
          {preferences.map((p) => (
            <div key={p.id} className="vy-card vy-stack" style={{ gap: 6 }}>
              <strong>{t(`privacy:preferences.key.${p.key}` as "preferences.key.max_distance_km", { defaultValue: p.key })}</strong>
              <span className="vy-muted" style={{ fontSize: 13 }}>{p.evidence}</span>
              {p.state === "proposed" && (
                <div className="vy-row">
                  <button className="vy-btn vy-btn-primary" style={{ fontSize: 13 }} disabled={busy} onClick={() => decidePreference(p.id, "confirm")}>{t("privacy:preferences.confirm")}</button>
                  <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} disabled={busy} onClick={() => decidePreference(p.id, "decline")}>{t("privacy:preferences.decline")}</button>
                </div>
              )}
              {p.state === "active" && (
                <div className="vy-row" style={{ justifyContent: "space-between" }}>
                  <span className="vy-badge vy-badge-member-provided">{t("privacy:preferences.active")}</span>
                  <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} disabled={busy} onClick={() => decidePreference(p.id, "remove")}>{t("privacy:preferences.remove")}</button>
                </div>
              )}
            </div>
          ))}
        </section>
      )}
    </main>
  );
}
