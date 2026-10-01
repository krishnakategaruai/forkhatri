"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { dateLong, timeZoneLabel } from "@/lib/format";
import { Skeleton, useToast } from "@/components/ui";

type Rule = { weekday: number; start_time: string; end_time: string; kind: "window" | "slot" };
type Exc = { id: string; on_date: string; start_time: string | null; end_time: string | null; available: boolean; note: string | null };
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

export default function AvailabilityPage() {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const [rules, setRules] = useState<Rule[] | null>(null);
  const [exc, setExc] = useState<Exc[]>([]);
  const [tz, setTz] = useState("");
  const [ne, setNe] = useState({ on_date: "", available: false, start_time: "", end_time: "", note: "" });

  const load = async () => {
    const r = await api<{ rules: Rule[]; exceptions: Exc[]; timezone: string }>("/provide/availability");
    setRules(r.rules.map((x) => ({ ...x, kind: x.kind ?? "window", start_time: x.start_time.slice(0, 5), end_time: x.end_time.slice(0, 5) }))); setExc(r.exceptions); setTz(r.timezone);
  };
  useEffect(() => { void load().catch(() => setRules([])); }, []);

  const save = async () => { try { await api("/provide/availability/rules", { method: "PUT", body: rules }); toast(t("common.saved")); } catch (e) { toast((e as Error).message); } };
  const addWin = (d: number) => setRules((r) => [...(r ?? []), { weekday: d, start_time: "18:00", end_time: "20:00", kind: "window" }]);
  const addSlot = (d: number) => setRules((r) => [...(r ?? []), { weekday: d, start_time: "19:00", end_time: "19:01", kind: "slot" }]);
  const addExc = async () => {
    await api("/provide/availability/exceptions", { body: { on_date: ne.on_date, available: ne.available, start_time: ne.start_time || null, end_time: ne.end_time || null, note: ne.note || null } });
    setNe({ on_date: "", available: false, start_time: "", end_time: "", note: "" }); await load();
  };

  if (!rules) return <Skeleton h={80} n={3} />;
  return (
    <div className="two-col">
      <div className="stack-lg">
        <section className="card card-pad stack">
          <div className="between"><h2>{t("avail.weekly")}</h2><span className="tiny muted">{t("provider.tz", { tz: timeZoneLabel(i18n.language, tz || undefined) })}</span></div>
          <p className="small muted">{t("avail.weekly_hint")}</p>
          <div className="week">
            {DAYS.map((d, i) => {
              const wins = rules.map((r, idx) => ({ r, idx })).filter((x) => x.r.weekday === i);
              return (
                <div key={d} className="week-row">
                  <div className="small strong" style={{ paddingTop: 8 }}>{t(`day.${d}`)}</div>
                  <div className="windows">
                    {wins.map(({ r, idx }) => (
                      <div key={idx} className="win">
                        <input type="time" className="input" value={r.start_time} onChange={(e) => setRules(rules.map((x, j) => (j === idx ? { ...x, start_time: e.target.value } : x)))} />
                        {r.kind === "slot" ? <span className="tag">{t("avail.exact")}</span> : (<>
                        <span className="muted">–</span>
                        <input type="time" className="input" value={r.end_time} onChange={(e) => setRules(rules.map((x, j) => (j === idx ? { ...x, end_time: e.target.value } : x)))} /></>)}
                        <button className="icon-btn" aria-label={t("common.remove")} onClick={() => setRules(rules.filter((_, j) => j !== idx))}><Trash2 size={15} /></button>
                      </div>
                    ))}
                    <div className="row" style={{ gap: 4 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => addWin(i)}><Plus size={14} />{t("avail.add_window_short")}</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => addSlot(i)}><Plus size={14} />{t("avail.add_slot")}</button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div><button className="btn btn-primary" onClick={() => void save()}>{t("common.save")}</button></div>
        </section>

        <section className="card card-pad stack">
          <h2>{t("avail.exceptions")}</h2>
          <p className="small muted">{t("avail.exceptions_hint")}</p>
          <div className="grid grid-3">
            <label className="field"><span className="label">{t("avail.date")}</span><input type="date" className="input" value={ne.on_date} onChange={(e) => setNe({ ...ne, on_date: e.target.value })} /></label>
            <label className="field"><span className="label">{t("avail.kind")}</span><select className="select" value={ne.available ? "open" : "off"} onChange={(e) => setNe({ ...ne, available: e.target.value === "open" })}><option value="off">{t("avail.day_off")}</option><option value="open">{t("avail.extra_hours")}</option></select></label>
            <label className="field"><span className="label">{t("avail.note")}</span><input className="input" value={ne.note} onChange={(e) => setNe({ ...ne, note: e.target.value })} /></label>
            {ne.available && (<>
              <label className="field"><span className="label">{t("avail.from")}</span><input type="time" className="input" value={ne.start_time} onChange={(e) => setNe({ ...ne, start_time: e.target.value })} /></label>
              <label className="field"><span className="label">{t("avail.to")}</span><input type="time" className="input" value={ne.end_time} onChange={(e) => setNe({ ...ne, end_time: e.target.value })} /></label>
            </>)}
          </div>
          <div><button className="btn btn-secondary btn-sm" disabled={!ne.on_date || (ne.available && (!ne.start_time || !ne.end_time))} onClick={() => void addExc()}><Plus size={14} />{t("common.add")}</button></div>
          <div className="list">
            {exc.map((e) => (
              <div key={e.id} className="item" style={{ padding: "8px 0" }}>
                <div className="grow small">{dateLong(e.on_date, i18n.language)} · {e.available ? `${t("avail.extra_hours")} ${e.start_time?.slice(0, 5)}–${e.end_time?.slice(0, 5)}` : t("avail.day_off")}{e.note ? ` · ${e.note}` : ""}</div>
                <button className="icon-btn" aria-label={t("common.remove")} onClick={() => void api(`/provide/availability/exceptions/${e.id}`, { method: "DELETE" }).then(load)}><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        </section>
      </div>
      <aside className="card card-pad stack">
        <span className="eyebrow">{t("avail.how")}</span>
        <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}><li>{t("avail.how1")}</li><li>{t("avail.how_slot")}</li><li>{t("avail.how2")}</li><li>{t("avail.how3")}</li><li>{t("avail.how4")}</li></ul>
      </aside>
    </div>
  );
}
