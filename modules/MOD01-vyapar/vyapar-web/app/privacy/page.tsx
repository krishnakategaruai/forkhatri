"use client";

// [TR036] Six contextual privacy controls, one screen (FR36).
// [TR037] Data export, correction, deletion, consent withdrawal (FR37).
// [TR038] Inspect and confirm derived preferences (FR38).
// One screen, per FR36's own "single Privacy screen" requirement. Each
// control carries a one-sentence explanation of who sees what, as a
// permanent visible caption. Data rights and learned preferences sit below
// as their own sections on the same screen.
// [Design language 2026-09-29] A page header; each section a card with a
// tinted icon tile, a title and one line; each control a full-row switch
// (the whole 52px row is the tap target, not a 16px checkbox); the contact
// choice as chips instead of a native <select>; the export as a nested
// block. The desktop "On this page" nav (globals .vy-settings) stays.
// Traces to: FR36, FR37, FR38, TR036, TR037, TR038
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { BarChart3, ChevronRight, Download, Eye, Sparkles, Trash } from "lucide-react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import PageHeader from "@/app/components/account/PageHeader";
import SwitchRow from "@/app/components/account/SwitchRow";
import { formatDate } from "@/lib/format"; // [FE2] Indian date order
import "@/app/styles/account-2026.css";

interface PrivacySettings {
  capability_visible: boolean;
  seeking_visible: boolean;
  contact_disclosure: "public" | "after_accept" | "hidden";
  discoverable: boolean;
  notifications_enabled: boolean;
  commercial_comms: boolean;
  behavioral_analytics: boolean;
  /** [Recommendations 2026-09-30] learn from what I do to pick posts for me */
  personalised_recommendations?: boolean;
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

const DISCLOSURES: PrivacySettings["contact_disclosure"][] = ["public", "after_accept", "hidden"];

export default function PrivacyPage() {
  const { t, i18n } = useTranslation(["privacy", "common"]);
  const [settings, setSettings] = useState<PrivacySettings | null>(null);
  const [requests, setRequests] = useState<DataRequest[]>([]);
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [exportDoc, setExportDoc] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [typed, setTyped] = useState("");
  const [erased, setErased] = useState(false);

  function load() {
    return Promise.all([
      api.get<PrivacySettings>("/v1/privacy"),
      api.get<DataRequest[]>("/v1/privacy/requests"),
      api.get<Preference[]>("/v1/preferences/mine"),
    ]).then(([s, r, p]) => {
      setSettings(s);
      setRequests(r);
      setPreferences(p.filter((x) => x.state !== "removed"));
    });
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

  // Delete my data in Vyapar: everything Vyapar holds, typed DELETE, then leave the module.
  async function doDelete() {
    setBusy(true);
    setNotice(null);
    try {
      await api.post("/v1/privacy/delete-account-data", { confirm: typed });
      setErased(true);
      window.setTimeout(() => window.location.assign("/"), 2500);
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

  if (!settings)
    return (
      <Screen width="wide">
        <div className="vy-skeleton" style={{ height: 40, width: 200, maxWidth: "60%" }} aria-hidden="true" />
        <SkeletonGrid count={2} grid={false} />
      </Screen>
    );

  const toggle = (labelKey: string, helpKey: string, field: keyof PrivacySettings, value: boolean) => (
    <SwitchRow
      id={`privacy-${field}`}
      label={t(`privacy:control.${labelKey}` as "control.discoverable")}
      hint={t(`privacy:control.${helpKey}` as "control.discoverableHelp")}
      checked={value}
      disabled={busy}
      onChange={(next) => update(field, next)}
    />
  );

  // [IMP39 — desktop layout] A settings layout at ≥900px: a sticky list of
  // this screen's sections on the left (plain in-page anchors), the settings
  // on the right. Below 900px the nav is display:none and both wrappers are
  // display:contents.
  const sections = [
    { id: "privacy-controls", label: t("privacy:controlsTitle") },
    { id: "privacy-analytics", label: t("privacy:analyticsTitle") },
    { id: "privacy-data", label: t("privacy:dataRights.title") },
    ...(preferences.length > 0 ? [{ id: "privacy-preferences", label: t("privacy:preferences.title") }] : []),
  ];

  return (
    <Screen width="wide">
      <PageHeader title={t("privacy:title")} purpose={t("privacy:purpose")} backHref="/profile" backLabel={t("common:nav.profile")} />
      {notice && <p className="vy-error" role="status">{notice}</p>}

      <div className="vy-settings">
        <nav className="vy-settings-nav" aria-label={t("common:layout.onThisPage")}>
          <span className="vy-ctx-heading" style={{ padding: "0 12px 8px" }}>{t("common:layout.onThisPage")}</span>
          {sections.map((sec) => (
            <a key={sec.id} href={`#${sec.id}`}>{sec.label}</a>
          ))}
        </nav>
        <div className="vy-settings-main">
          <section id="privacy-controls" className="vy-card vy-acct-card" aria-labelledby="privacy-controls-title">
            <div className="vy-acct-card-head">
              <span className="vy-acct-tile" data-tint="sky" aria-hidden="true">
                <Eye size={20} strokeWidth={1.9} />
              </span>
              <h2 id="privacy-controls-title">{t("privacy:controlsTitle")}</h2>
              <p>{t("privacy:controlsHelp")}</p>
            </div>
            <div className="vy-acct-card-body" style={{ gap: 0 }}>
              {toggle("discoverable", "discoverableHelp", "discoverable", settings.discoverable)}
              {toggle("capabilityVisible", "capabilityVisibleHelp", "capability_visible", settings.capability_visible)}
              {toggle("seekingVisible", "seekingVisibleHelp", "seeking_visible", settings.seeking_visible)}
              <div className="vy-acct-switch" style={{ gridTemplateColumns: "minmax(0, 1fr)", cursor: "default" }}>
                <span className="vy-acct-switch-text">
                  <span className="vy-acct-switch-label">{t("privacy:control.contactDisclosure")}</span>
                  <span className="vy-acct-switch-hint">{t("privacy:control.contactDisclosureHelp")}</span>
                </span>
                <div className="vy-acct-inline-choices" role="group" aria-label={t("privacy:control.contactDisclosure")} style={{ marginTop: 6 }}>
                  {DISCLOSURES.map((d) => (
                    <button key={d} type="button" className="vy-chip" aria-pressed={settings.contact_disclosure === d} disabled={busy} onClick={() => update("contact_disclosure", d)}>
                      {t(`privacy:contactOption.${d}` as "contactOption.public")}
                    </button>
                  ))}
                </div>
              </div>
              {toggle("notificationsEnabled", "notificationsEnabledHelp", "notifications_enabled", settings.notifications_enabled)}
              {toggle("commercialComms", "commercialCommsHelp", "commercial_comms", settings.commercial_comms)}
            </div>
          </section>

          <section id="privacy-analytics" className="vy-card vy-acct-card" aria-labelledby="privacy-analytics-title">
            <div className="vy-acct-card-head">
              <span className="vy-acct-tile" data-tint="plum" aria-hidden="true">
                <BarChart3 size={20} strokeWidth={1.9} />
              </span>
              <h2 id="privacy-analytics-title">{t("privacy:analyticsTitle")}</h2>
              <p>{t("privacy:analyticsHelp")}</p>
            </div>
            <div className="vy-acct-card-body" style={{ gap: 0 }}>
              {toggle("behavioralAnalytics", "behavioralAnalyticsHelp", "behavioral_analytics", settings.behavioral_analytics)}
              {toggle("personalised", "personalisedHelp", "personalised_recommendations", settings.personalised_recommendations ?? true)}
              {/* [Recommendations 2026-09-30] what Vyapar learned from what the member did */}
              <Link href="/profile/learned" transitionTypes={["vy-forward"]} className="vy-acct-row vy-learned-link">
                <span className="vy-acct-tile" data-tint="amber" aria-hidden="true">
                  <Sparkles size={20} strokeWidth={1.9} />
                </span>
                <span className="vy-acct-row-text">
                  <span className="vy-acct-row-label">{t("privacy:learned.privacyLink")}</span>
                  <span className="vy-acct-row-hint">{t("privacy:learned.hubHint")}</span>
                </span>
                <span className="vy-acct-row-end">
                  <ChevronRight size={18} strokeWidth={2} aria-hidden="true" />
                </span>
              </Link>
              {toggle("digestEnabled", "digestEnabledHelp", "digest_enabled", settings.digest_enabled)}
            </div>
          </section>

          <section id="privacy-data" className="vy-card vy-acct-card" aria-labelledby="privacy-data-title">
            <div className="vy-acct-card-head">
              <span className="vy-acct-tile" data-tint="green" aria-hidden="true">
                <Download size={20} strokeWidth={1.9} />
              </span>
              <h2 id="privacy-data-title">{t("privacy:dataRights.title")}</h2>
              <p>{t("privacy:dataRights.exportHint")}</p>
            </div>
            <div className="vy-acct-card-body">
              <div className="vy-row" style={{ flexWrap: "wrap", gap: 10 }}>
                <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={doExport}>
                  <Download size={18} strokeWidth={2} aria-hidden="true" />
                  {t("privacy:dataRights.export")}
                </button>
                {!confirmingDelete && (
                  <button className="vy-btn vy-btn-ghost" style={{ color: "var(--danger-text)" }} disabled={busy} onClick={() => setConfirmingDelete(true)}>
                    <Trash size={18} strokeWidth={2} aria-hidden="true" />
                    {t("privacy:eraseData.button")}
                  </button>
                )}
              </div>
              {erased && (
                <div className="vy-acct-note" role="status">
                  <div className="vy-stack" style={{ gap: 6 }}>
                    <strong style={{ color: "var(--text-primary)" }}>{t("privacy:eraseData.doneTitle")}</strong>
                    <span>{t("privacy:eraseData.doneBody")}</span>
                  </div>
                </div>
              )}
              {confirmingDelete && !erased && (
                <div className="vy-acct-note" role="alertdialog" aria-label={t("privacy:eraseData.title")}>
                  <Trash size={18} strokeWidth={2} aria-hidden="true" />
                  <div className="vy-stack" style={{ gap: 10 }}>
                    <span style={{ color: "var(--text-primary)" }}>{t("privacy:eraseData.intro")}</span>
                    <strong>{t("privacy:eraseData.deletedHeading")}</strong>
                    <ul>{(t("privacy:eraseData.deletedList", { returnObjects: true }) as string[]).map((x) => <li key={x}>{x}</li>)}</ul>
                    <strong>{t("privacy:eraseData.retainedHeading")}</strong>
                    <ul>{(t("privacy:eraseData.retainedList", { returnObjects: true }) as string[]).map((x) => <li key={x}>{x}</li>)}</ul>
                    <span>{t("privacy:eraseData.otherPeople")}</span>
                    <label className="vy-stack" style={{ gap: 4 }}>
                      <span>{t("privacy:eraseData.typePrompt")}</span>
                      <input className="vy-input" value={typed} placeholder={t("privacy:eraseData.typePlaceholder")} onChange={(e) => setTyped(e.target.value)} autoComplete="off" />
                    </label>
                    <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                      <button className="vy-btn" style={{ background: "var(--danger-text)", color: "#fff" }} disabled={busy || typed.trim() !== "DELETE"} onClick={doDelete}>
                        {busy ? t("privacy:eraseData.working") : t("privacy:eraseData.button")}
                      </button>
                      <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => { setConfirmingDelete(false); setTyped(""); }}>
                        {t("common:action.cancel")}
                      </button>
                    </div>
                  </div>
                </div>
              )}
              {!confirmingDelete && !erased && <p className="vy-acct-hint">{t("privacy:dataRights.deleteHint")}</p>}
              {exportDoc && (
                <details>
                  <summary style={{ cursor: "pointer", minHeight: 44, display: "flex", alignItems: "center", fontWeight: 650 }}>{t("privacy:dataRights.exportReady")}</summary>
                  <pre className="vy-acct-pre">{exportDoc}</pre>
                </details>
              )}
              {requests.length > 0 && (
                <div className="vy-stack" style={{ gap: 6 }}>
                  <span className="vy-acct-group" style={{ padding: 0 }}>{t("privacy:dataRights.historyTitle")}</span>
                  {requests.map((r) => (
                    <p key={r.id} className="vy-acct-hint">
                      {t(`privacy:requestKind.${r.kind}` as "requestKind.export")} · {t(`privacy:requestState.${r.state}` as "requestState.completed")} · {formatDate(r.created_at, i18n.language)}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </section>

          {preferences.length > 0 && (
            <section id="privacy-preferences" className="vy-card vy-acct-card" aria-labelledby="privacy-preferences-title">
              <div className="vy-acct-card-head">
                <span className="vy-acct-tile" data-tint="amber" aria-hidden="true">
                  <Sparkles size={20} strokeWidth={1.9} />
                </span>
                <h2 id="privacy-preferences-title">{t("privacy:preferences.title")}</h2>
                <p>{t("privacy:preferences.help")}</p>
              </div>
              <div className="vy-acct-card-body">
                {preferences.map((p) => (
                  <div key={p.id} className="vy-card vy-card-nested vy-stack" style={{ gap: 8 }}>
                    <strong style={{ color: "var(--text-primary)" }}>{t(`privacy:preferences.key.${p.key}` as "preferences.key.max_distance_km", { defaultValue: p.key })}</strong>
                    <span className="vy-acct-hint">{p.evidence}</span>
                    {p.state === "proposed" && (
                      <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                        <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => decidePreference(p.id, "confirm")}>{t("privacy:preferences.confirm")}</button>
                        <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => decidePreference(p.id, "decline")}>{t("privacy:preferences.decline")}</button>
                      </div>
                    )}
                    {p.state === "active" && (
                      <div className="vy-row" style={{ justifyContent: "space-between" }}>
                        <span className="vy-badge vy-badge-member-provided">{t("privacy:preferences.active")}</span>
                        <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => decidePreference(p.id, "remove")}>{t("privacy:preferences.remove")}</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </Screen>
  );
}
