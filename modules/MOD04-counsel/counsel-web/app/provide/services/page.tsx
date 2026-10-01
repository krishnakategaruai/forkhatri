"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus } from "lucide-react";
import { api, ApiError, type Expertise, type Service } from "@/lib/api";
import { money } from "@/lib/format";
import { Dialog, Empty, Skeleton, useToast } from "@/components/ui";

const FORMATS = ["video", "audio", "screen", "files"];
const blank = { title: "", description: "", outcomes: "", area_id: "", duration_min: 45, price: "", formats: ["video"], min_notice_hours: 12, max_advance_days: 30, buffer_min: 10, recording_allowed: false, allow_custom_time: false, status: "active" };

export default function ServicesPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const [list, setList] = useState<Service[] | null>(null);
  const [areas, setAreas] = useState<Expertise[]>([]);
  const [mine, setMine] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [f, setF] = useState(blank);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    const [s, a, p] = await Promise.all([api<Service[]>("/provide/services"), api<Expertise[]>("/expertise"), api<{ expertise: { id: string }[] } | null>("/provide/profile")]);
    setList(s); setAreas(a); setMine(p?.expertise.map((e) => e.id) ?? []);
  };
  useEffect(() => { void load().catch(() => setList([])); }, []);

  const startNew = () => { setEditing(null); setF({ ...blank, area_id: mine[0] ?? "" }); setErr(null); setOpen(true); };
  const startEdit = (s: Service) => { setEditing(s.id); setF({ title: s.title, description: s.description, outcomes: s.outcomes.join("\n"), area_id: s.area_id, duration_min: s.duration_min, price: String(s.price_minor / 100), formats: s.formats, min_notice_hours: s.min_notice_hours, max_advance_days: s.max_advance_days, buffer_min: s.buffer_min, recording_allowed: s.recording_allowed, allow_custom_time: !!s.allow_custom_time, status: s.status }); setErr(null); setOpen(true); };
  const save = async () => {
    setErr(null);
    const body = { ...f, outcomes: f.outcomes.split("\n").map((s) => s.trim()).filter(Boolean), price_minor: Math.round(Number(f.price) * 100) };
    try {
      await api(editing ? `/provide/services/${editing}` : "/provide/services", { method: editing ? "PUT" : "POST", body });
      setOpen(false); toast(t("common.saved")); await load();
    } catch (e) {
      const ae = e as ApiError;
      const missing = (ae.detail as { missing?: string[] })?.missing;
      setErr(missing ? t("services.verification_required", { dims: missing.map((d) => t(`verify.${d}`)).join(", ") }) : ae.message);
    }
  };
  const [offers, setOffers] = useState<Service | null>(null);
  const [of, setOf] = useState({ qprice: "", qdays: 3, instant: false, pkSessions: 2, pkPrice: "", pkDays: 60 });
  const [pkgs, setPkgs] = useState<{ id: string; sessions: number; price_minor: number; valid_days: number }[]>([]);
  const openOffers = async (s: Service) => {
    setOffers(s);
    const d = await api<{ question_price_minor: number | null; question_answer_days: number; instant_allowed: boolean }>(`/services/${s.id}`);
    setOf({ qprice: d.question_price_minor ? String(d.question_price_minor / 100) : "", qdays: d.question_answer_days, instant: d.instant_allowed, pkSessions: 2, pkPrice: "", pkDays: 60 });
    setPkgs(await api(`/services/${s.id}/packages`));
  };
  const saveOffers = async () => {
    if (!offers) return;
    try {
      await api(`/provide/services/${offers.id}/offers`, { method: "PUT", body: { question_price_minor: of.qprice ? Math.round(Number(of.qprice) * 100) : null, question_answer_days: of.qdays, instant_allowed: of.instant } });
      toast(t("common.saved")); setOffers(null);
    } catch (e) { toast((e as Error).message); }
  };
  const addPkg = async () => {
    if (!offers) return;
    try {
      await api(`/provide/services/${offers.id}/packages`, { body: { sessions: of.pkSessions, price_minor: Math.round(Number(of.pkPrice) * 100), valid_days: of.pkDays } });
      setPkgs(await api(`/services/${offers.id}/packages`)); setOf({ ...of, pkPrice: "" });
    } catch (e) { const ae = e as ApiError; toast(t(`errors.${ae.code}`, { defaultValue: ae.message })); }
  };
  const pause = async (s: Service) => {
    await api(`/provide/services/${s.id}`, { method: "PUT", body: { title: s.title, description: s.description, outcomes: s.outcomes, area_id: s.area_id, duration_min: s.duration_min, price_minor: s.price_minor, formats: s.formats, min_notice_hours: s.min_notice_hours, max_advance_days: s.max_advance_days, buffer_min: s.buffer_min, recording_allowed: s.recording_allowed, allow_custom_time: !!s.allow_custom_time, status: s.status === "active" ? "paused" : "active" } });
    await load();
  };

  if (!list) return <Skeleton h={100} n={2} />;
  const areaOptions = areas.filter((a) => mine.includes(a.id));

  return (
    <div className="stack">
      <div className="between"><p className="muted small" style={{ maxWidth: "60ch" }}>{t("services.intro")}</p><button className="btn btn-primary" onClick={startNew} disabled={!mine.length}><Plus size={16} />{t("services.new")}</button></div>
      {!mine.length && <p className="tiny" style={{ color: "var(--warn)" }}>{t("services.need_expertise")}</p>}
      {!list.length ? <Empty title={t("services.empty")} body={t("services.empty_body")} /> : (
        <div className="grid grid-2">
          {list.map((s) => (
            <div key={s.id} className="card card-pad stack" style={{ gap: 8 }}>
              <div className="between" style={{ alignItems: "flex-start" }}><h3>{s.title}</h3><span className={`tag ${s.status === "active" ? "tag-ok" : "tag-warn"}`}>{t(`services.status.${s.status}`)}</span></div>
              <div className="tiny muted">{s.area_name} · {t("service.minutes", { n: s.duration_min })} · {s.formats.map((x) => t(`format.${x}`)).join(", ")}{s.allow_custom_time ? ` · ${t("services.custom_on")}` : ""}</div>
              <div className="serif" style={{ fontSize: "1.3rem" }}>{money(s.price_minor, s.currency, lang)}</div>
              <div className="row"><button className="btn btn-secondary btn-sm" onClick={() => startEdit(s)}>{t("common.edit")}</button><button className="btn btn-secondary btn-sm" onClick={() => void openOffers(s)}>{t("offers.more_ways")}</button><button className="btn btn-ghost btn-sm" onClick={() => void pause(s)}>{s.status === "active" ? t("services.pause") : t("services.resume")}</button></div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={!!offers} onClose={() => setOffers(null)} title={offers ? t("offers.more_ways_title", { title: offers.title }) : ""}>
        {offers && (
          <>
            <span className="eyebrow">{t("offers.packages")}</span>
            <p className="tiny muted">{t("offers.followups_hint")}</p>
            {pkgs.map((p) => (
              <div key={p.id} className="between small"><span>{t("offers.sessions", { count: p.sessions })} · {money(p.price_minor, offers.currency, lang)} · {t("offers.valid_days", { n: p.valid_days })}</span>
                <button className="link" onClick={() => void api(`/provide/packages/${p.id}`, { method: "DELETE" }).then(async () => setPkgs(await api(`/services/${offers.id}/packages`)))}>{t("common.remove")}</button></div>
            ))}
            <div className="grid grid-3">
              <label className="field"><span className="label">{t("offers.pk_sessions")}</span><select className="select" value={of.pkSessions} onChange={(e) => setOf({ ...of, pkSessions: Number(e.target.value) })}>{[1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
              <label className="field"><span className="label">{t("offers.pk_price")}</span><input className="input" inputMode="decimal" value={of.pkPrice} onChange={(e) => setOf({ ...of, pkPrice: e.target.value.replace(/[^\d.]/g, "") })} placeholder={money(offers.price_minor * of.pkSessions * 0.85, offers.currency, lang)} /></label>
              <label className="field"><span className="label">{t("offers.pk_days")}</span><select className="select" value={of.pkDays} onChange={(e) => setOf({ ...of, pkDays: Number(e.target.value) })}>{[30, 60, 90].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
            </div>
            <div><button className="btn btn-secondary btn-sm" disabled={!Number(of.pkPrice)} onClick={() => void addPkg()}>{t("offers.add_package")}</button></div>
            <div className="divider" />
            <span className="eyebrow">{t("offers.ask")}</span>
            <div className="grid grid-2">
              <label className="field"><span className="label">{t("offers.q_price")}</span><input className="input" inputMode="decimal" value={of.qprice} onChange={(e) => setOf({ ...of, qprice: e.target.value.replace(/[^\d.]/g, "") })} placeholder={t("offers.q_off")} /></label>
              <label className="field"><span className="label">{t("offers.q_days")}</span><select className="select" value={of.qdays} onChange={(e) => setOf({ ...of, qdays: Number(e.target.value) })}>{[1, 2, 3, 5, 7].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
            </div>
            <div className="divider" />
            <label className="check"><input type="checkbox" checked={of.instant} onChange={(e) => setOf({ ...of, instant: e.target.checked })} /><span className="small">{t("offers.instant_allowed")}<span className="tiny muted" style={{ display: "block" }}>{t("offers.instant_hint")}</span></span></label>
            <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn btn-ghost" onClick={() => setOffers(null)}>{t("common.cancel")}</button><button className="btn btn-primary" onClick={() => void saveOffers()}>{t("common.save")}</button></div>
          </>
        )}
      </Dialog>

      <Dialog open={open} onClose={() => setOpen(false)} title={editing ? t("services.edit") : t("services.new")}>
        <label className="field"><span className="label">{t("services.title")}</span><input className="input" maxLength={100} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder={t("services.title_placeholder")} /></label>
        <label className="field"><span className="label">{t("services.area")}</span><select className="select" value={f.area_id} onChange={(e) => setF({ ...f, area_id: e.target.value })}>{areaOptions.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
        <label className="field"><span className="label">{t("services.description")}</span><textarea className="textarea" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} placeholder={t("services.description_placeholder")} style={{ minHeight: 80 }} /></label>
        <label className="field"><span className="label">{t("services.outcomes")}</span><textarea className="textarea" value={f.outcomes} onChange={(e) => setF({ ...f, outcomes: e.target.value })} placeholder={t("services.outcomes_placeholder")} style={{ minHeight: 70 }} /><span className="hint">{t("services.outcomes_hint")}</span></label>
        <div className="grid grid-2">
          <label className="field"><span className="label">{t("services.duration")}</span><select className="select" value={f.duration_min} onChange={(e) => setF({ ...f, duration_min: Number(e.target.value) })}>{[15, 30, 45, 60, 90, 120].map((n) => <option key={n} value={n}>{t("service.minutes", { n })}</option>)}</select></label>
          <label className="field"><span className="label">{t("services.price")}</span><input className="input" inputMode="decimal" value={f.price} onChange={(e) => setF({ ...f, price: e.target.value.replace(/[^\d.]/g, "") })} placeholder="₹" /></label>
        </div>
        <div className="field"><span className="label">{t("services.formats")}</span><div className="row">{FORMATS.map((x) => <button key={x} type="button" className="chip" aria-pressed={f.formats.includes(x)} onClick={() => setF({ ...f, formats: f.formats.includes(x) ? f.formats.filter((y) => y !== x) : [...f.formats, x] })}>{t(`format.${x}`)}</button>)}</div></div>
        <label className="check"><input type="checkbox" checked={f.allow_custom_time} onChange={(e) => setF({ ...f, allow_custom_time: e.target.checked })} /><span className="small">{t("services.allow_custom_time")}<span className="tiny muted" style={{ display: "block" }}>{t("services.allow_custom_time_hint")}</span></span></label>
        <details><summary className="small link">{t("services.advanced")}</summary>
          <div className="grid grid-3" style={{ marginTop: 10 }}>
            <label className="field"><span className="label">{t("services.min_notice")}</span><input className="input" inputMode="numeric" value={f.min_notice_hours} onChange={(e) => setF({ ...f, min_notice_hours: Number(e.target.value) || 0 })} /></label>
            <label className="field"><span className="label">{t("services.max_advance")}</span><input className="input" inputMode="numeric" value={f.max_advance_days} onChange={(e) => setF({ ...f, max_advance_days: Number(e.target.value) || 1 })} /></label>
            <label className="field"><span className="label">{t("services.buffer")}</span><input className="input" inputMode="numeric" value={f.buffer_min} onChange={(e) => setF({ ...f, buffer_min: Number(e.target.value) || 0 })} /></label>
          </div>
          <label className="check" style={{ marginTop: 10 }}><input type="checkbox" checked={f.recording_allowed} onChange={(e) => setF({ ...f, recording_allowed: e.target.checked })} /><span className="small">{t("services.recording_allowed")}</span></label>
        </details>
        <p className="tiny muted">{t("services.fee_note")}</p>
        {err && <p className="error">{err}</p>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button><button className="btn btn-primary" disabled={!f.title || !f.area_id || !Number(f.price)} onClick={() => void save()}>{t("common.save")}</button></div>
      </Dialog>
    </div>
  );
}
