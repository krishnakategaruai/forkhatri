"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Camera, FileCheck, Paperclip, Plus, ShieldCheck, Trash2 } from "lucide-react";
import { API_BASE, api, type Evidence, type Expertise } from "@/lib/api";
import { Avatar, Dialog, Skeleton, useToast } from "@/components/ui";
import { usePlaces } from "@/lib/places";
import { SUPPORTED_LANGUAGES } from "@/lib/i18n/config";

type Mine = {
  headline: string; intro: string; city: string | null; country: string; timezone: string; languages: string[]; links: Record<string, string>;
  photo_url: string | null; status: string; expertise: { id: string; years: number; primary: boolean }[]; verified: string[]; evidence: Evidence[];
  required_dimensions: string[]; display_name: string;
} | null;

const KINDS = ["experience", "qualification", "certification", "registration", "business", "portfolio"] as const;
const LINKS = ["linkedin", "website", "portfolio", "youtube", "instagram", "facebook"];

const OTHER_CITY = "__other";

export default function ProfileSetup() {
  const { t, i18n } = useTranslation();
  const places = usePlaces(i18n.language);
  const [otherCity, setOtherCity] = useState(false);
  const toast = useToast();
  const [areas, setAreas] = useState<Expertise[]>([]);
  const [p, setP] = useState<Mine | undefined>(undefined);
  const [form, setForm] = useState({ headline: "", intro: "", city: "", country: "IN", timezone: "Asia/Kolkata", languages: ["en"] as string[], links: {} as Record<string, string>, photo_url: "", expertise: [] as { id: string; years: number; primary: boolean }[] });
  const [saving, setSaving] = useState(false);
  const [evOpen, setEvOpen] = useState(false);
  const [ev, setEv] = useState({ kind: "experience" as (typeof KINDS)[number], title: "", issuer: "", year_from: "", year_to: "", reference_no: "" });
  const [reqOpen, setReqOpen] = useState(false);
  const [req, setReq] = useState({ name: "", parent_id: "", note: "" });

  const load = async () => {
    const [a, mine] = await Promise.all([api<Expertise[]>("/expertise"), api<Mine>("/provide/profile")]);
    setAreas(a); setP(mine);
    if (mine) setForm({ headline: mine.headline, intro: mine.intro, city: mine.city ?? "", country: mine.country, timezone: mine.timezone, languages: mine.languages, links: mine.links ?? {}, photo_url: mine.photo_url ?? "", expertise: mine.expertise.map((e) => ({ id: e.id, years: e.years, primary: e.primary })) });
  };
  useEffect(() => { void load(); }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api("/provide/profile", { method: "PUT", body: { ...form, photo_url: form.photo_url || null, city: form.city || null } });
      toast(t("common.saved")); await load();
    } catch (e) { toast((e as Error).message); } finally { setSaving(false); }
  };
  const submit = async () => { try { await api("/provide/submit", { method: "POST" }); toast(t("provide.submitted")); await load(); } catch (e) { toast((e as Error).message); } };
  const toggleArea = (id: string) => setForm((f) => {
    const has = f.expertise.some((e) => e.id === id);
    const next = has ? f.expertise.filter((e) => e.id !== id) : [...f.expertise, { id, years: 0, primary: f.expertise.length === 0 }];
    if (!next.some((e) => e.primary) && next[0]) next[0].primary = true;
    return { ...f, expertise: next };
  });
  const addEvidence = async () => {
    await api("/provide/evidence", { body: { ...ev, year_from: ev.year_from ? Number(ev.year_from) : null, year_to: ev.year_to ? Number(ev.year_to) : null, issuer: ev.issuer || null, reference_no: ev.reference_no || null } });
    setEvOpen(false); setEv({ kind: "experience", title: "", issuer: "", year_from: "", year_to: "", reference_no: "" }); toast(t("common.saved")); await load();
  };
  const uploadPhoto = async (file: File) => {
    const form = new FormData(); form.append("file", file);
    try { const r = await api<{ photo_url: string }>("/provide/photo", { form }); setForm((f) => ({ ...f, photo_url: r.photo_url })); toast(t("common.saved")); }
    catch (e) { toast((e as Error).message); }
  };
  const uploadProof = async (id: string, file: File) => {
    const form = new FormData(); form.append("file", file);
    try { await api(`/provide/evidence/${id}/document`, { form }); toast(t("profile.proof_added")); await load(); }
    catch (e) { toast((e as Error).message); }
  };
  const requestArea = async () => { await api("/provide/expertise-requests", { body: { ...req, parent_id: req.parent_id || null } }); setReqOpen(false); toast(t("provide.area_requested")); };

  if (p === undefined) return <Skeleton h={90} n={4} />;

  return (
    <div className="two-col">
      <div className="stack-lg">
        <section className="card card-pad stack">
          <h2>{t("profile.who")}</h2>
          <p className="tiny muted">{t("profile.name_note", { name: p?.display_name ?? "" })}</p>
          <label className="field"><span className="label">{t("profile.headline")}</span><input className="input" maxLength={120} value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder={t("profile.headline_placeholder")} /><span className="hint">{t("profile.headline_hint")}</span></label>
          <label className="field"><span className="label">{t("profile.intro")}</span><textarea className="textarea" maxLength={2000} value={form.intro} onChange={(e) => setForm({ ...form, intro: e.target.value })} placeholder={t("profile.intro_placeholder")} /></label>
          <div className="grid grid-2">
            {(() => {
              const listed = places?.cities.find((c) => c.value.toLowerCase() === form.city.trim().toLowerCase());
              const other = otherCity || (!!form.city && !listed && !!places);
              return (
                <div className="field"><span className="label">{t("profile.city")}</span>
                  <select className="select" value={listed ? listed.value : other ? OTHER_CITY : ""} onChange={(e) => {
                    const val = e.target.value;
                    setOtherCity(val === OTHER_CITY);
                    setForm({ ...form, city: val === OTHER_CITY ? (listed ? "" : form.city) : val });
                  }}>
                    <option value="">{t("profile.city_choose")}</option>
                    {places?.cities.map((c) => <option key={c.id} value={c.value}>{c.name}</option>)}
                    <option value={OTHER_CITY}>{t("profile.city_other")}</option>
                  </select>
                  {other && <input className="input" maxLength={80} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder={t("profile.city_other_placeholder")} aria-label={t("profile.city_other")} />}
                  <span className="hint">{other ? t("profile.city_other_hint") : t("profile.city_hint")}</span>
                </div>
              );
            })()}
            <label className="field"><span className="label">{t("profile.country")}</span>
              <select className="select" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}>
                {["IN", "US", "GB", "AE", "SG", "AU", "CA"].map((c) => <option key={c} value={c}>{t(`country.${c}`)}</option>)}
              </select></label>
            <label className="field"><span className="label">{t("profile.timezone")}</span>
              <select className="select" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })}>
                {["Asia/Kolkata", "Asia/Dubai", "Asia/Singapore", "Europe/London", "America/New_York", "America/Los_Angeles", "Australia/Sydney"].map((z) => <option key={z} value={z}>{z}</option>)}
              </select></label>
            <div className="field"><span className="label">{t("profile.languages")}</span>
              <div className="row">{SUPPORTED_LANGUAGES.map((l) => <button key={l} type="button" className="chip" aria-pressed={form.languages.includes(l)} onClick={() => setForm({ ...form, languages: form.languages.includes(l) ? form.languages.filter((x) => x !== l) : [...form.languages, l] })}>{t(`lang.${l}`)}</button>)}</div>
            </div>
          </div>
          <div className="row" style={{ gap: 14 }}>
            <Avatar name={p?.display_name ?? ""} url={form.photo_url || null} size={72} />
            <div className="stack" style={{ gap: 4 }}>
              {p ? (
                <label className="btn btn-secondary btn-sm" style={{ justifySelf: "start" }}><Camera size={15} />{form.photo_url ? t("profile.photo_change") : t("profile.photo_add")}
                  <input type="file" accept="image/jpeg,image/png,image/webp" className="sr" onChange={(e) => { const f = e.target.files?.[0]; if (f) void uploadPhoto(f); e.target.value = ""; }} /></label>
              ) : <span className="tiny muted">{t("profile.save_first_photo")}</span>}
              <span className="hint">{t("profile.photo_hint")}</span>
            </div>
          </div>
        </section>

        <section className="card card-pad stack">
          <h2>{t("profile.what")}</h2>
          <p className="small muted">{t("profile.expertise_hint")}</p>
          <div className="row">
            {areas.map((a) => <button key={a.id} type="button" className="chip" aria-pressed={form.expertise.some((e) => e.id === a.id)} onClick={() => toggleArea(a.id)}>{a.name}{a.regulated ? " ·" : ""}</button>)}
          </div>
          {form.expertise.length > 0 && (
            <div className="list">
              {form.expertise.map((e) => (
                <div key={e.id} className="item" style={{ padding: "8px 0" }}>
                  <div className="grow small">{areas.find((a) => a.id === e.id)?.name}</div>
                  <label className="row tiny muted" style={{ gap: 6 }}>{t("profile.years")}<input className="input" style={{ width: 70, padding: "6px 8px" }} inputMode="numeric" value={e.years} onChange={(ev2) => setForm({ ...form, expertise: form.expertise.map((x) => (x.id === e.id ? { ...x, years: Number(ev2.target.value.replace(/\D/g, "")) || 0 } : x)) })} /></label>
                  <button type="button" className={`chip ${e.primary ? "on" : ""}`} onClick={() => setForm({ ...form, expertise: form.expertise.map((x) => ({ ...x, primary: x.id === e.id })) })}>{t("profile.primary")}</button>
                </div>
              ))}
            </div>
          )}
          <button type="button" className="link small" onClick={() => setReqOpen(true)}>{t("profile.request_area")}</button>
        </section>

        <section className="card card-pad stack">
          <h2>{t("profile.elsewhere")}</h2>
          <div className="grid grid-2">
            {LINKS.map((k) => <label key={k} className="field"><span className="label">{t(`links.${k}`)}</span><input className="input" value={form.links[k] ?? ""} onChange={(e) => setForm({ ...form, links: { ...form.links, [k]: e.target.value } })} placeholder="https://" /></label>)}
          </div>
        </section>

        <div className="row">
          <button className="btn btn-primary btn-lg" disabled={saving || !form.headline || !form.expertise.length} onClick={() => void save()}>{t("common.save")}</button>
          {p && (p.status === "draft" || p.status === "changes_requested") && <button className="btn btn-secondary btn-lg" onClick={() => void submit()}>{t("provide.submit")}</button>}
        </div>

        <section className="card card-pad stack" id="evidence">
          <div className="between"><h2>{t("profile.why_trust")}</h2><button className="btn btn-secondary btn-sm" disabled={!p} onClick={() => setEvOpen(true)}><Plus size={14} />{t("profile.add_evidence")}</button></div>
          <p className="small muted">{t("profile.evidence_hint")}</p>
          {!p && <p className="tiny muted">{t("profile.save_first")}</p>}
          {p && p.required_dimensions.length > 0 && (
            <div className="tag tag-warn" style={{ display: "inline-flex", alignSelf: "start" }}>{t("profile.required", { dims: p.required_dimensions.map((d) => t(`verify.${d}`)).join(", ") })}</div>
          )}
          <div className="list">
            {p?.evidence.map((e) => (
              <div key={e.id} className="item" style={{ padding: "10px 0" }}>
                <div className="grow"><div className="tiny muted">{t(`evidence.${e.kind}`)}</div><div className="small">{e.title}</div><div className="tiny muted">{[e.issuer, e.year_from ? `${e.year_from}${e.year_to ? `–${e.year_to}` : ""}` : null].filter(Boolean).join(" · ")}</div>{e.review_note && <div className="tiny" style={{ color: "var(--warn)" }}>{e.review_note}</div>}</div>
                {e.has_document ? (
                  <a className="tag" href={`${API_BASE}/provide/evidence/${e.id}/document`} target="_blank" rel="noopener noreferrer"><FileCheck size={12} />{e.document_name ?? t("profile.proof")}</a>
                ) : e.status !== "verified" && (
                  <label className="btn btn-ghost btn-sm"><Paperclip size={14} />{t("profile.attach_proof")}
                    <input type="file" accept="application/pdf,image/jpeg,image/png,image/webp" className="sr" onChange={(ev) => { const f = ev.target.files?.[0]; if (f) void uploadProof(e.id, f); ev.target.value = ""; }} /></label>
                )}
                <span className={`tag ${e.status === "verified" ? "tag-verified" : e.status === "rejected" ? "tag-danger" : ""}`}>{e.status === "verified" && <ShieldCheck size={12} />}{t(`evidence.status.${e.status}`)}</span>
                {e.status !== "verified" && <button className="icon-btn" aria-label={t("common.remove")} onClick={() => void api(`/provide/evidence/${e.id}`, { method: "DELETE" }).then(load)}><Trash2 size={15} /></button>}
              </div>
            ))}
          </div>
        </section>
      </div>

      <aside className="card card-pad stack">
        <span className="eyebrow">{t("profile.tips")}</span>
        <ul className="small" style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
          <li>{t("profile.tip1")}</li><li>{t("profile.tip2")}</li><li>{t("profile.tip3")}</li><li>{t("profile.tip4")}</li>
        </ul>
        {p && <div className="stack" style={{ gap: 4 }}><span className="eyebrow">{t("profile.verified_so_far")}</span>{p.verified.length ? <div className="row">{p.verified.map((d) => <span key={d} className="tag tag-verified"><ShieldCheck size={12} />{t(`verify.${d}`)}</span>)}</div> : <span className="small muted">{t("profile.none_yet")}</span>}</div>}
      </aside>

      <Dialog open={evOpen} onClose={() => setEvOpen(false)} title={t("profile.add_evidence")}>
        <label className="field"><span className="label">{t("evidence.kind")}</span><select className="select" value={ev.kind} onChange={(e) => setEv({ ...ev, kind: e.target.value as (typeof KINDS)[number] })}>{KINDS.map((k) => <option key={k} value={k}>{t(`evidence.${k}`)}</option>)}</select></label>
        <label className="field"><span className="label">{t("evidence.title")}</span><input className="input" value={ev.title} onChange={(e) => setEv({ ...ev, title: e.target.value })} placeholder={t(`evidence.title_placeholder.${ev.kind}`)} /></label>
        <label className="field"><span className="label">{t("evidence.issuer")}</span><input className="input" value={ev.issuer} onChange={(e) => setEv({ ...ev, issuer: e.target.value })} /></label>
        <div className="grid grid-2">
          <label className="field"><span className="label">{t("evidence.from")}</span><input className="input" inputMode="numeric" value={ev.year_from} onChange={(e) => setEv({ ...ev, year_from: e.target.value.replace(/\D/g, "").slice(0, 4) })} /></label>
          <label className="field"><span className="label">{t("evidence.to")}</span><input className="input" inputMode="numeric" value={ev.year_to} onChange={(e) => setEv({ ...ev, year_to: e.target.value.replace(/\D/g, "").slice(0, 4) })} placeholder={t("evidence.present")} /></label>
        </div>
        {(ev.kind === "registration" || ev.kind === "certification") && <label className="field"><span className="label">{t("evidence.reference")}</span><input className="input" value={ev.reference_no} onChange={(e) => setEv({ ...ev, reference_no: e.target.value })} /><span className="hint">{t("evidence.reference_hint")}</span></label>}
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn btn-ghost" onClick={() => setEvOpen(false)}>{t("common.cancel")}</button><button className="btn btn-primary" disabled={!ev.title} onClick={() => void addEvidence()}>{t("common.add")}</button></div>
      </Dialog>

      <Dialog open={reqOpen} onClose={() => setReqOpen(false)} title={t("profile.request_area")}>
        <p className="small muted">{t("profile.request_body")}</p>
        <label className="field"><span className="label">{t("profile.area_name")}</span><input className="input" value={req.name} onChange={(e) => setReq({ ...req, name: e.target.value })} /></label>
        <label className="field"><span className="label">{t("profile.area_parent")}</span><select className="select" value={req.parent_id} onChange={(e) => setReq({ ...req, parent_id: e.target.value })}><option value="">—</option>{areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
        <label className="field"><span className="label">{t("profile.area_note")}</span><textarea className="textarea" value={req.note} onChange={(e) => setReq({ ...req, note: e.target.value })} style={{ minHeight: 70 }} /></label>
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn btn-ghost" onClick={() => setReqOpen(false)}>{t("common.cancel")}</button><button className="btn btn-primary" disabled={!req.name} onClick={() => void requestArea()}>{t("common.send")}</button></div>
      </Dialog>
    </div>
  );
}
