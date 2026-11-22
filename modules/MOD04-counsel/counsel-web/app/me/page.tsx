"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Avatar, Dialog, useToast } from "@/components/ui";
import { API_BASE, api, ApiError } from "@/lib/api";
import { useIdentity } from "@/lib/identity";
import { FORKHATRI_ENTRANCE_URL } from "@/lib/platform";
import { LANGUAGE_NATIVE, SUPPORTED_LANGUAGES, type Language } from "@/lib/i18n/config";
import { chooseLanguage } from "@/lib/i18n/provider";

export default function MePage() {
  const { t, i18n } = useTranslation();
  const { me, signOut } = useIdentity();
  const [theme, setTheme] = useState<string>("auto");
  useEffect(() => { try { setTheme(localStorage.getItem("counsel.theme") ?? "auto"); } catch { /* ignore */ } }, []);
  const applyTheme = (v: string) => {
    setTheme(v);
    try { localStorage.setItem("counsel.theme", v); } catch { /* ignore */ }
    if (v === "auto") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = v;
  };
  const toast = useToast();
  const [del, setDel] = useState(false);
  const [blockers, setBlockers] = useState<string[] | null>(null);
  const [typed, setTyped] = useState("");
  const openDelete = async () => { setDel(true); setTyped(""); setBlockers((await api<{ blockers: string[] }>("/me/deletion-check")).blockers); };
  const doDelete = async () => {
    try { await api("/me/delete-account-data", { body: { confirm: typed } }); toast(t("privacy.deleted")); setDel(false); window.location.assign(FORKHATRI_ENTRANCE_URL); }
    catch (e) { toast(t(`errors.${(e as ApiError).code}`, { defaultValue: (e as Error).message })); }
  };
  if (!me) return null;
  return (
    <div className="wrap page stack" style={{ maxWidth: 640 }}>
      <div className="row" style={{ gap: 16 }}><Avatar name={me.display_name} size={64} /><div><h1 style={{ fontSize: "1.8rem" }}>{me.display_name}</h1><p className="tiny muted">{t("me.account_note")}</p></div></div>
      <section className="card card-pad stack">
        <span className="eyebrow">{t("me.language")}</span>
        <div className="row">{SUPPORTED_LANGUAGES.map((l) => <button key={l} className="chip" aria-pressed={i18n.language === l} onClick={() => chooseLanguage(l as Language)}>{LANGUAGE_NATIVE[l]}</button>)}</div>
        <span className="eyebrow" style={{ marginTop: 8 }}>{t("me.appearance")}</span>
        <div className="row">{["auto", "light", "dark"].map((v) => <button key={v} className="chip" aria-pressed={theme === v} onClick={() => applyTheme(v)}>{t(`me.theme_${v}`)}</button>)}</div>
      </section>
      <section className="card card-pad stack">
        <Link href="/provide" className="between"><span>{me.provider_status ? t("me.provider_dashboard") : t("me.become_provider")}</span><span className="muted">→</span></Link>
        <div className="divider" />
        <Link href="/saved" className="between"><span>{t("nav.saved")}</span><span className="muted">→</span></Link>
        <div className="divider" />
        <a href={`${FORKHATRI_ENTRANCE_URL}/account`} className="between"><span>{t("me.forkhatri_account")}</span><span className="muted">→</span></a>
        <div className="divider" />
        <a href={FORKHATRI_ENTRANCE_URL} className="between"><span>{t("me.back_to_hub")}</span><span className="muted">→</span></a>
      </section>
      <section className="card card-pad stack">
        <span className="eyebrow">{t("privacy.title")}</span>
        <p className="small muted">{t("privacy.body")}</p>
        <div className="row">
          <a className="btn btn-secondary btn-sm" href={`${API_BASE}/me/export`}>{t("privacy.download")}</a>
          <button className="btn btn-danger btn-sm" onClick={() => void openDelete()}>{t("privacy.delete")}</button>
        </div>
      </section>
      <div><button className="btn btn-secondary" onClick={() => void signOut()}>{t("me.sign_out")}</button></div>
      <Dialog open={del} onClose={() => setDel(false)} title={t("privacy.delete_title")}>
        {blockers === null ? <p className="small muted">…</p> : (
          <>
            {blockers.length > 0 && (
              <>
                <p className="small"><strong>{t("privacy.warn")}</strong></p>
                <ul className="small" style={{ margin: 0, paddingLeft: 18 }}>{blockers.map((b) => <li key={b}>{t(`privacy.blocker.${b}`)}</li>)}</ul>
              </>
            )}
            <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
              <li>{t("privacy.removes")}</li><li>{t("privacy.keeps")}</li><li>{t("privacy.account_stays")}</li>
            </ul>
            <label className="field"><span className="label">{t("privacy.type_delete")}</span><input className="input" value={typed} onChange={(e) => setTyped(e.target.value)} /></label>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setDel(false)}>{t("common.cancel")}</button>
              <button className="btn btn-danger" disabled={typed.trim().toUpperCase() !== "DELETE"} onClick={() => void doDelete()}>{t("privacy.delete_confirm")}</button>
            </div>
          </>
        )}
      </Dialog>
    </div>
  );
}
