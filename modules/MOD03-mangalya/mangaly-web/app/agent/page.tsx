"use client";

import Link from "next/link";
import { useMounted } from "@/lib/useMounted";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import AgentPlanCheckout from "@/components/AgentPlanCheckout";
import { Avatar } from "@/components/Avatar";
import ContactReveal from "@/components/ContactReveal";
import OfflineBiodataCard, { OFFLINE_FIELDS } from "@/components/OfflineBiodataCard";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import {
  STAGES,
  addClient,
  addOffline,
  applyAsAgent,
  archiveOffline,
  downloadExcel,
  downloadTemplate,
  formatDay,
  getMyAgentRecord,
  getQuota,
  importClients,
  listClients,
  listOffline,
  setStage,
  type AgentRecord,
  type Client,
  type ImportRow,
  type OfflineProfile,
  type Quota,
  type Stage,
} from "@/lib/agents";
import { resolveMediaUrl } from "@/lib/api";
import { getSession } from "@/lib/auth";
import { getVerification } from "@/lib/verification";

import "./agent.css";

/* [DEC-V1-033] The marriage agent's workspace. The owner (2026-09-29): a
 * marriage agent "exists without the app too, so I don't want to kill his
 * job, rather I want to enhance him." One page walks the agent from applying,
 * through Mangalya's check and the membership, into the workspace: every
 * family with its stage, adding families one by one or from an Excel sheet,
 * the biodata of people not on Mangalya, numbers and exports. Each family's
 * own desk (search as the family, share, calls and meetings) is the
 * relationship-manager console, which agents share with Mangalya's own RMs. */

type Tab = "clients" | "add" | "offline";

function AgentWorkspace() {
  const { t, i18n } = useTranslation(["agents", "common"]);
  const params = useSearchParams();
  const router = useRouter();
  const [record, setRecord] = useState<AgentRecord | null | undefined>(undefined);
  const [editing, setEditing] = useState(false);
  const tab = (params.get("tab") as Tab | null) ?? "clients";

  const reload = useCallback(async () => {
    setRecord(await getMyAgentRecord(true));
  }, []);

  useEffect(() => {
    let alive = true;
    getMyAgentRecord(true).then((r) => alive && setRecord(r));
    return () => {
      alive = false;
    };
  }, []);

  const go = (next: Tab) => router.replace(next === "clients" ? "/agent" : `/agent?tab=${next}`, { scroll: false });

  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("agents:workspace.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen ag-screen">
        {record === undefined ? (
          <p className="caption">{t("agents:workspace.loading")}</p>
        ) : record === null || record.kind !== "agent" || editing || record.verification_status === "rejected" ? (
          <Join
            record={record && record.kind === "agent" ? record : null}
            onSaved={async () => {
              setEditing(false);
              await reload();
            }}
          />
        ) : record.verification_status === "suspended" ? (
          <div className="ag-status">
            <p className="ag-eyebrow">{t("agents:workspace.eyebrow")}</p>
            <h2 className="ag-title">{t("agents:suspendedStatus.title")}</h2>
            <p className="ag-lede">{t("agents:suspendedStatus.body")}</p>
          </div>
        ) : record.verification_status === "pending" ? (
          <div className="ag-status">
            <p className="ag-eyebrow">{t("agents:workspace.eyebrow")}</p>
            <h2 className="ag-title">{t("agents:status.pending.title")}</h2>
            <p className="ag-lede">{t("agents:status.pending.body")}</p>
            <div>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(true)}>
                {t("agents:status.editDetails")}
              </button>
            </div>
          </div>
        ) : !record.live ? (
          <div className="ag-status">
            <span className="ag-pill ag-pill--ok">{t("agents:status.verified")}</span>
            <h2 className="ag-title">{t("agents:membership.title")}</h2>
            <p className="ag-lede">{t("agents:membership.lede")}</p>
            <AgentPlanCheckout code="AGENT" onPaid={reload} />
          </div>
        ) : (
          <>
            <div className="ag-bar">
              <div className="ag-head">
                <p className="ag-eyebrow">{record.business_name ?? record.display_name}</p>
                <div className="ag-row">
                  <span className="ag-pill ag-pill--ok">{t("agents:status.verified")}</span>
                  <span className="caption">
                    {t("agents:membership.until", { date: formatDay(record.membership_until, i18n.language) })}
                  </span>
                </div>
              </div>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(true)}>
                {t("agents:status.editDetails")}
              </button>
            </div>
            <FairUse />
            <div className="ag-tabs" role="tablist">
              {(["clients", "add", "offline"] as Tab[]).map((x) => (
                <button key={x} type="button" role="tab" className="ag-tab" aria-selected={tab === x} onClick={() => go(x)}>
                  {t(`agents:tabs.${x}`)}
                </button>
              ))}
            </div>
            {tab === "clients" && <Clients onAdd={() => go("add")} />}
            {tab === "add" && <AddClients />}
            {tab === "offline" && <Offline />}
          </>
        )}
      </main>
    </>
  );
}

/* ---------------------------------------------------------------------------
 * Fair use (DEC-V1-034): what the agent has used today, and why the limits
 * exist. Own clients never count.
 * ------------------------------------------------------------------------- */

function FairUse() {
  const { t } = useTranslation(["agents"]);
  const [quota, setQuota] = useState<Quota | null>(null);

  useEffect(() => {
    let alive = true;
    getQuota().then((q) => alive && setQuota(q));
    return () => {
      alive = false;
    };
  }, []);

  if (!quota) return null;
  return (
    <section className={`ag-fair${quota.contact_suspended ? " is-warning" : ""}`}>
      {quota.contact_suspended && <p className="ag-fair__warn">{t("agents:quota.suspended")}</p>}
      <div className="ag-fair__row">
        <span className="label">{t("agents:quota.title")}</span>
        <span>{t("agents:quota.contacts", { used: quota.contacts_today, limit: quota.contacts_per_day })}</span>
        <span className="caption">{t("agents:quota.month", { used: quota.contacts_month, limit: quota.contacts_per_month })}</span>
      </div>
      <details className="ag-fair__rules">
        <summary>{t("agents:quota.rules")}</summary>
        <p className="caption">
          {t("agents:quota.exports", { used: quota.exported_others_today, limit: quota.export_others_per_day })}
        </p>
        <ul>
          <li>{t("agents:quota.rule1")}</li>
          <li>{t("agents:quota.rule2")}</li>
          <li>{t("agents:quota.rule3", { limit: quota.export_others_per_day })}</li>
          <li>{t("agents:quota.rule4")}</li>
          <li>{t("agents:quota.rule5")}</li>
        </ul>
      </details>
    </section>
  );
}

/* ---------------------------------------------------------------------------
 * Applying (and editing the details later)
 * ------------------------------------------------------------------------- */

const LANGUAGE_CHOICES = ["te", "hi", "en", "ta", "kn", "mr"];

function Join({ record, onSaved }: { record: AgentRecord | null; onSaved: () => void }) {
  const { t } = useTranslation(["agents", "common"]);
  const [name, setName] = useState(record?.display_name ?? "");
  const [business, setBusiness] = useState(record?.business_name ?? "");
  const [phone, setPhone] = useState(record?.business_phone ?? "");
  const [city, setCity] = useState(record?.city ?? "");
  const [languages, setLanguages] = useState<string[]>(record?.languages ?? []);
  const [communities, setCommunities] = useState((record?.communities ?? []).join(", "));
  const [years, setYears] = useState(record?.years_active != null ? String(record.years_active) : "");
  const [about, setAbout] = useState(record?.about ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Never ask for what Mangalya already knows: a new applicant's name comes
  // from their ForKhatri account.
  useEffect(() => {
    if (record) return;
    let alive = true;
    getSession()
      .then((s) => alive && s?.display_name && setName((n) => n || s.display_name))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [record]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const out = await applyAsAgent({
      display_name: name.trim(),
      business_name: business.trim() || null,
      business_phone: phone.trim() || null,
      city: city.trim(),
      languages,
      communities: communities.split(",").map((x) => x.trim()).filter(Boolean),
      years_active: years ? Number(years) : null,
      about: about.trim() || null,
    });
    setBusy(false);
    if (!out.ok) {
      setError(out.message ?? t("common:state.error", { defaultValue: "Something went wrong." }));
      return;
    }
    onSaved();
  };

  return (
    <div className="ag-join">
      <div className="ag-head" style={{ gap: "var(--space-4)" }}>
        <p className="ag-eyebrow">{t("agents:workspace.eyebrow")}</p>
        {record?.verification_status === "rejected" ? (
          <>
            <h2 className="ag-title">{t("agents:status.rejected.title")}</h2>
            <p className="ag-lede">{t("agents:status.rejected.body")}</p>
          </>
        ) : (
          <>
            <h2 className="ag-title">{t("agents:join.title")}</h2>
            <p className="ag-lede">{t("agents:join.lede")}</p>
          </>
        )}
        <ul className="ag-benefits">
          {(["clients", "search", "offline", "export"] as const).map((k, i) => (
            <li key={k}>
              <span className="ag-benefits__mark">{i + 1}</span>
              <span>{t(`agents:join.benefit.${k}`)}</span>
            </li>
          ))}
        </ul>
        <p className="ag-promise">{t("agents:join.form.promise")}</p>
      </div>
      <form className="card ag-form" onSubmit={submit}>
        <h3 className="h3" style={{ margin: 0 }}>
          {t("agents:join.form.title")}
        </h3>
        <div className="ag-grid2">
          <label className="field">
            <span className="label">{t("agents:join.form.name")}</span>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} />
          </label>
          <label className="field">
            <span className="label">{t("agents:join.form.business")}</span>
            <input
              className="input"
              value={business}
              onChange={(e) => setBusiness(e.target.value)}
              placeholder={t("agents:join.form.businessPlaceholder")}
            />
          </label>
          <label className="field">
            <span className="label">{t("agents:join.form.phone")}</span>
            <input className="input" type="tel" inputMode="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">{t("agents:join.form.city")}</span>
            <input className="input" value={city} onChange={(e) => setCity(e.target.value)} required minLength={2} />
          </label>
        </div>
        <fieldset className="field" style={{ border: 0, padding: 0 }}>
          <legend className="label">{t("agents:join.form.languages")}</legend>
          <div className="ag-chips" style={{ flexWrap: "wrap" }}>
            {LANGUAGE_CHOICES.map((l) => {
              const on = languages.includes(l);
              return (
                <button
                  key={l}
                  type="button"
                  className="ag-chip"
                  aria-pressed={on}
                  onClick={() => setLanguages(on ? languages.filter((x) => x !== l) : [...languages, l])}
                >
                  {t(`agents:join.language.${l}`)}
                </button>
              );
            })}
          </div>
        </fieldset>
        <div className="ag-grid2">
          <label className="field">
            <span className="label">{t("agents:join.form.communities")}</span>
            <input
              className="input"
              value={communities}
              onChange={(e) => setCommunities(e.target.value)}
              placeholder={t("agents:join.form.communitiesPlaceholder")}
            />
          </label>
          <label className="field">
            <span className="label">{t("agents:join.form.years")}</span>
            <input
              className="input"
              inputMode="numeric"
              value={years}
              onChange={(e) => setYears(e.target.value.replace(/\D/g, "").slice(0, 2))}
            />
          </label>
        </div>
        <label className="field">
          <span className="label">{t("agents:join.form.about")}</span>
          <textarea
            className="textarea"
            value={about}
            onChange={(e) => setAbout(e.target.value)}
            maxLength={1200}
            placeholder={t("agents:join.form.aboutPlaceholder")}
          />
        </label>
        {error && <p className="ag-error">{error}</p>}
        <div>
          <button type="submit" className="btn btn--primary" disabled={busy}>
            {record ? t("agents:join.form.save") : t("agents:join.form.submit")}
          </button>
        </div>
      </form>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Clients
 * ------------------------------------------------------------------------- */

function Clients({ onAdd }: { onAdd: () => void }) {
  const { t } = useTranslation(["agents", "common"]);
  const [clients, setClients] = useState<Client[] | null | undefined>(undefined);
  const [stage, setStageFilter] = useState<Stage | "all">("all");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [withNumbers, setWithNumbers] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    listClients().then(setClients);
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: clients?.length ?? 0 };
    for (const x of clients ?? []) c[x.stage] = (c[x.stage] ?? 0) + 1;
    return c;
  }, [clients]);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (clients ?? []).filter(
      (c) =>
        (stage === "all" || c.stage === stage) &&
        (!needle || `${c.name ?? ""} ${c.city ?? ""}`.toLowerCase().includes(needle)),
    );
  }, [clients, stage, q]);

  if (clients === undefined) return <p className="caption">{t("common:state.loading")}</p>;
  if (clients === null) return <p className="ag-error">{t("common:state.error", { defaultValue: "Something went wrong." })}</p>;

  const liked = clients.reduce((n, c) => n + c.liked, 0);
  const married = counts.married ?? 0;

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const changeStage = async (c: Client, next: Stage) => {
    setClients((prev) => (prev ?? []).map((x) => (x.assignment_id === c.assignment_id ? { ...x, stage: next } : x)));
    await setStage(c.assignment_id, next);
  };

  const ids = [...selected];
  const exportExcel = async () => {
    const out = await downloadExcel(ids, withNumbers);
    setNotice(out.ok ? t("agents:clients.exported") : out.message ?? null);
  };

  return (
    <>
      <div className="ag-stats">
        <div className="ag-stat">
          <span className="ag-stat__n">{clients.length}</span>
          <span className="ag-stat__l">{t("agents:stats.clients")}</span>
        </div>
        <div className="ag-stat">
          <span className="ag-stat__n">{liked}</span>
          <span className="ag-stat__l">{t("agents:stats.liked")}</span>
        </div>
        <div className="ag-stat">
          <span className="ag-stat__n">{married}</span>
          <span className="ag-stat__l">{t("agents:stats.married")}</span>
        </div>
      </div>

      {clients.length === 0 ? (
        <div className="ag-status">
          <p className="ag-lede">{t("agents:clients.empty")}</p>
          <div>
            <button type="button" className="btn btn--primary" onClick={onAdd}>
              {t("agents:tabs.add")}
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="ag-bar">
            <div className="ag-chips" role="group" aria-label={t("agents:stage.label")}>
              {(["all", ...STAGES] as const).map((s) =>
                s !== "all" && !counts[s] ? null : (
                  <button key={s} type="button" className="ag-chip" aria-pressed={stage === s} onClick={() => setStageFilter(s)}>
                    {t(`agents:stage.${s}`)}
                    <span className="ag-chip__n">{counts[s] ?? 0}</span>
                  </button>
                ),
              )}
            </div>
            <input
              className="input"
              style={{ maxWidth: 260 }}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("agents:clients.searchPlaceholder")}
              aria-label={t("agents:clients.searchPlaceholder")}
            />
          </div>

          <ul className="ag-clients">
            {shown.map((c) => {
              return (
                <li key={c.assignment_id} className={`ag-client${selected.has(c.account_id) ? " is-selected" : ""}`}>
                  <input
                    type="checkbox"
                    className="ag-client__check"
                    checked={selected.has(c.account_id)}
                    onChange={() => toggle(c.account_id)}
                    aria-label={t("agents:clients.select", { name: c.name ?? "" })}
                  />
                  <Link href={`/rm/console/${c.assignment_id}`} className="ag-client__photo" prefetch={false}>
                    {c.photo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={resolveMediaUrl(c.photo_url) ?? ""} alt="" loading="lazy" decoding="async" />
                    ) : (
                      <Avatar name={c.name ?? ""} size={48} />
                    )}
                  </Link>
                  <div className="ag-client__body">
                    <span className="ag-client__name">{c.name}</span>
                    <span className="ag-client__line">
                      {[c.age != null ? t("agents:clients.age", { age: c.age }) : null, c.city?.split(",")[0]]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    <span className="ag-client__line">
                      {[
                        c.looking_for ? t(`agents:clients.lookingFor.${c.looking_for}`) : null,
                        // "Took over" only means something for a profile the agent made.
                        c.made_by_me && c.claimed ? t("agents:origin.claimed") : t(`agents:origin.${c.origin}`),
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    <span className="ag-client__line">
                      {t("agents:clients.shared", { count: c.suggestions })} · {t("agents:clients.liked", { count: c.liked })}
                    </span>
                    <div className="ag-client__actions">
                      <select
                        value={c.stage}
                        onChange={(e) => changeStage(c, e.target.value as Stage)}
                        aria-label={t("agents:stage.label")}
                      >
                        {STAGES.map((s) => (
                          <option key={s} value={s}>
                            {t(`agents:stage.${s}`)}
                          </option>
                        ))}
                      </select>
                      <Link href={`/rm/console/${c.assignment_id}`} className="btn btn--secondary btn--sm" prefetch={false}>
                        {t("agents:clients.open")}
                      </Link>
                      {c.made_by_me && !c.claimed && (
                        <Link href={`/me?manage=${c.account_id}`} className="btn btn--ghost btn--sm" prefetch={false}>
                          {t("agents:clients.edit")}
                        </Link>
                      )}
                    </div>
                    <ContactReveal memberAccountId={c.account_id} isClient />
                  </div>
                </li>
              );
            })}
          </ul>

          {selected.size > 0 && (
            <div className="ag-selection">
              <span className="ag-selection__count">{t("agents:clients.selected", { count: selected.size })}</span>
              <label className="ag-consent">
                <input type="checkbox" checked={withNumbers} onChange={(e) => setWithNumbers(e.target.checked)} />
                {t("agents:clients.withNumbers")}
              </label>
              <button type="button" className="btn btn--secondary btn--sm" onClick={exportExcel}>
                {t("agents:clients.exportExcel")}
              </button>
              <button
                type="button"
                className="btn btn--primary btn--sm"
                onClick={() => router.push(`/agent/biodata?ids=${ids.join(",")}${withNumbers ? "" : "&numbers=0"}`)}
              >
                {t("agents:clients.printBiodata")}
              </button>
            </div>
          )}
          {notice && <p className="caption">{notice}</p>}
        </>
      )}
    </>
  );
}

/* ---------------------------------------------------------------------------
 * Adding families
 * ------------------------------------------------------------------------- */

function AddClients() {
  const { t } = useTranslation(["agents", "common"]);
  const [verified, setVerified] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    getVerification().then((v) => setVerified(!!v?.verified));
  }, []);

  if (verified === undefined) return <p className="caption">{t("common:state.loading")}</p>;
  if (!verified) {
    return (
      <div className="ag-status">
        <p className="ag-lede">{t("agents:add.faceCheck")}</p>
        <div>
          <Link className="btn btn--primary" href={`/me/verify?next=${encodeURIComponent("/agent?tab=add")}`}>
            {t("agents:add.faceCheckButton")}
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="ag-screen" style={{ display: "flex", flexDirection: "column" }}>
      <AddOne />
      <AddMany />
    </div>
  );
}

function AddOne() {
  const { t } = useTranslation(["agents", "common"]);
  const [added, setAdded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    data.set("consent", (form.elements.namedItem("consent") as HTMLInputElement).checked ? "true" : "false");
    setBusy(true);
    setError(null);
    setAdded(null);
    const out = await addClient(data);
    setBusy(false);
    if (!out.ok) {
      setError(out.message ?? t("agents:add.error.unexpected"));
      return;
    }
    setAdded(String(data.get("name") ?? ""));
    form.reset();
  };

  return (
    <section className="card ag-form">
      <h3 className="h3" style={{ margin: 0 }}>
        {t("agents:add.one.title")}
      </h3>
      <p className="caption" style={{ margin: 0 }}>
        {t("agents:add.one.lede")}
      </p>
      <form className="ag-form" onSubmit={submit}>
        <div className="ag-grid3">
          <label className="field">
            <span className="label">{t("agents:add.name")}</span>
            <input className="input" name="name" required />
          </label>
          <label className="field">
            <span className="label">{t("agents:add.mobile")}</span>
            <input className="input" name="mobile" type="tel" inputMode="tel" required minLength={10} />
          </label>
          <label className="field">
            <span className="label">{t("agents:add.dob")}</span>
            <input className="input" name="date_of_birth" type="date" required />
          </label>
          <label className="field">
            <span className="label">{t("agents:add.gender")}</span>
            <select className="input" name="gender" required defaultValue="">
              <option value="" disabled />
              <option value="female">{t("agents:add.female")}</option>
              <option value="male">{t("agents:add.male")}</option>
            </select>
          </label>
          <label className="field">
            <span className="label">{t("agents:add.lookingFor")}</span>
            <select className="input" name="looking_for" required defaultValue="">
              <option value="" disabled />
              <option value="groom">{t("agents:add.groom")}</option>
              <option value="bride">{t("agents:add.bride")}</option>
            </select>
          </label>
          <label className="field">
            <span className="label">{t("agents:add.city")}</span>
            <input className="input" name="city" required />
          </label>
        </div>
        <label className="field">
          <span className="label">{t("agents:add.photo")}</span>
          <input className="input" name="photo" type="file" accept="image/jpeg,image/png,image/webp" required />
        </label>
        <label className="ag-consent">
          <input type="checkbox" name="consent" required />
          {t("agents:add.consent")}
        </label>
        {error && <p className="ag-error">{error}</p>}
        {added && <p className="ag-ok">{t("agents:add.added", { name: added })}</p>}
        <div>
          <button type="submit" className="btn btn--primary" disabled={busy}>
            {t("agents:add.submit")}
          </button>
        </div>
      </form>
    </section>
  );
}

function AddMany() {
  const { t } = useTranslation(["agents", "common"]);
  const [sheet, setSheet] = useState<File | null>(null);
  const [photos, setPhotos] = useState<File[]>([]);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rows, setRows] = useState<ImportRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sheet) return;
    const form = new FormData();
    form.set("sheet", sheet);
    photos.forEach((p) => form.append("photos", p));
    form.set("consent", consent ? "true" : "false");
    setBusy(true);
    setError(null);
    setRows(null);
    const out = await importClients(form);
    setBusy(false);
    if (!out.ok) {
      setError(out.message ?? t("agents:add.error.unexpected"));
      return;
    }
    setRows(out.data);
  };

  const errorText = (code: string) => {
    if (code.startsWith("missing:")) {
      return t("agents:add.error.missing", { fields: code.slice(8).replace(/_/g, " ") });
    }
    return t(`agents:add.error.${code}`, { defaultValue: t("agents:add.error.unexpected") });
  };

  const created = rows?.filter((r) => r.status === "created").length ?? 0;

  return (
    <section className="card ag-form">
      <h3 className="h3" style={{ margin: 0 }}>
        {t("agents:add.bulk.title")}
      </h3>
      <ol className="ag-steps">
        <li className="ag-step">
          <span className="ag-step__title">{t("agents:add.bulk.step1")}</span>
          <span className="caption">{t("agents:add.bulk.step1Body")}</span>
          <div>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => void downloadTemplate()}>
              mangaly-clients.xlsx
            </button>
          </div>
        </li>
        <li className="ag-step">
          <span className="ag-step__title">{t("agents:add.bulk.step2")}</span>
          <span className="caption">{t("agents:add.bulk.step2Body")}</span>
        </li>
        <li className="ag-step">
          <span className="ag-step__title">{t("agents:add.bulk.step3")}</span>
          <form className="ag-form" onSubmit={submit}>
            <label className="field">
              <span className="label">{t("agents:add.bulk.sheet")}</span>
              <input
                className="input"
                type="file"
                accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
                onChange={(e) => setSheet(e.target.files?.[0] ?? null)}
                required
              />
            </label>
            <label className="field">
              <span className="label">{t("agents:add.bulk.photos")}</span>
              <input
                className="input"
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => setPhotos(Array.from(e.target.files ?? []))}
              />
              {photos.length > 0 && (
                <span className="caption">{t("agents:add.bulk.photosChosen", { count: photos.length })}</span>
              )}
            </label>
            <label className="ag-consent">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
              {t("agents:add.consent")}
            </label>
            <div>
              <button type="submit" className="btn btn--primary" disabled={busy || !sheet || !consent}>
                {busy ? t("agents:add.bulk.working", { count: photos.length || 1 }) : t("agents:add.bulk.submit")}
              </button>
            </div>
          </form>
        </li>
      </ol>
      {error && <p className="ag-error">{error}</p>}
      {rows && (
        <>
          <p className="ag-ok">{t("agents:add.bulk.result", { created, failed: rows.length - created })}</p>
          <ul className="ag-results">
            {rows.map((r) => (
              <li key={r.row} className={`ag-result${r.status === "failed" ? " ag-result--failed" : ""}`}>
                <span className="ag-result__row">{t("agents:add.bulk.row", { row: r.row })}</span>
                <span>
                  <strong>{r.name}</strong>
                  {r.error ? ` · ${errorText(r.error)}` : ""}
                  {r.warnings.length > 0 ? ` · ${t("agents:add.bulk.warning", { fields: r.warnings.join(", ") })}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------------------
 * Biodata of people not on Mangalya
 * ------------------------------------------------------------------------- */


function Offline() {
  const { t, i18n } = useTranslation(["agents", "common"]);
  const [items, setItems] = useState<OfflineProfile[] | null | undefined>(undefined);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => setItems(await listOffline()), []);
  useEffect(() => {
    let alive = true;
    listOffline().then((x) => alive && setItems(x));
    return () => {
      alive = false;
    };
  }, []);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const raw = new FormData(form);
    const details: Record<string, string | number> = {};
    for (const [key] of OFFLINE_FIELDS) {
      const v = String(raw.get(key) ?? "").trim();
      if (v) details[key] = key === "height_cm" ? Number(v) : v;
      raw.delete(key);
    }
    const about = String(raw.get("about") ?? "").trim();
    if (about) details.about = about;
    raw.delete("about");
    raw.set("details", JSON.stringify(details));
    raw.set("consent", (form.elements.namedItem("consent") as HTMLInputElement).checked ? "true" : "false");
    if (!(raw.get("biodata") as File | null)?.size) raw.delete("biodata");
    // An empty file field is sent as an empty file; leave it out.
    const photos = (raw.getAll("photos") as File[]).filter((f) => f.size > 0);
    raw.delete("photos");
    photos.forEach((f) => raw.append("photos", f));
    if (!raw.get("date_of_birth")) raw.delete("date_of_birth");
    setBusy(true);
    setError(null);
    const out = await addOffline(raw);
    setBusy(false);
    if (!out.ok) {
      setError(out.message ?? t("agents:add.error.unexpected"));
      return;
    }
    form.reset();
    setAdding(false);
    await reload();
  };

  return (
    <>
      <div className="ag-bar">
        <div className="ag-head">
          <h2 className="h3" style={{ margin: 0 }}>
            {t("agents:offline.title")}
          </h2>
          <p className="caption" style={{ margin: 0, maxWidth: "62ch" }}>
            {t("agents:offline.lede")}
          </p>
        </div>
        {!adding && (
          <button type="button" className="btn btn--primary btn--sm" onClick={() => setAdding(true)}>
            {t("agents:offline.add")}
          </button>
        )}
      </div>
      {adding && (
        <form className="card ag-form" onSubmit={submit}>
          <div className="ag-grid3">
            <label className="field">
              <span className="label">{t("agents:offline.name")}</span>
              <input className="input" name="name" required />
            </label>
            <label className="field">
              <span className="label">{t("agents:add.gender")}</span>
              <select className="input" name="gender" required defaultValue="">
                <option value="" disabled />
                <option value="female">{t("agents:add.female")}</option>
                <option value="male">{t("agents:add.male")}</option>
              </select>
            </label>
            <label className="field">
              <span className="label">{t("agents:add.dob")}</span>
              <input className="input" name="date_of_birth" type="date" />
            </label>
            <label className="field">
              <span className="label">{t("agents:add.city")}</span>
              <input className="input" name="city" />
            </label>
            {OFFLINE_FIELDS.map(([key, label]) => (
              <label key={key} className="field">
                <span className="label">{t(`agents:offline.${label}`)}</span>
                <input className="input" name={key} inputMode={key === "height_cm" ? "numeric" : undefined} />
              </label>
            ))}
          </div>
          <label className="field">
            <span className="label">{t("agents:offline.about")}</span>
            <textarea className="textarea" name="about" maxLength={1000} />
          </label>
          <label className="field">
            <span className="label">{t("agents:offline.contactNote")}</span>
            <input className="input" name="contact_note" placeholder={t("agents:offline.contactNotePlaceholder")} />
          </label>
          <div className="ag-grid2">
            <label className="field">
              <span className="label">{t("agents:offline.photos")}</span>
              <input className="input" name="photos" type="file" multiple accept="image/jpeg,image/png,image/webp" />
            </label>
            <label className="field">
              <span className="label">{t("agents:offline.biodata")}</span>
              <input className="input" name="biodata" type="file" accept="application/pdf,image/jpeg,image/png,image/webp" />
            </label>
          </div>
          <label className="ag-consent">
            <input type="checkbox" name="consent" required />
            {t("agents:offline.consent")}
          </label>
          {error && <p className="ag-error">{error}</p>}
          <div className="ag-row">
            <button type="submit" className="btn btn--primary" disabled={busy}>
              {t("agents:offline.submit")}
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => setAdding(false)}>
              {t("common:action.cancel", { defaultValue: "Cancel" })}
            </button>
          </div>
        </form>
      )}
      {items === undefined ? (
        <p className="caption">{t("common:state.loading")}</p>
      ) : !items || items.length === 0 ? (
        !adding && <p className="caption">{t("agents:offline.empty")}</p>
      ) : (
        <ul className="ag-offline-list">
          {items.map((o) => (
            <li key={o.id}>
              <OfflineBiodataCard profile={o} />
              <div className="ag-row" style={{ marginTop: 6 }}>
                <span className="caption">{formatDay(o.created_at, i18n.language)}</span>
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  onClick={async () => {
                    await archiveOffline(o.id);
                    await reload();
                  }}
                >
                  {t("agents:offline.archive")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default function AgentPage() {
  // Client only: the first paint is in the member's own language.
  const mounted = useMounted();
  if (!mounted) return null;
  return (
    <Suspense fallback={null}>
      <AgentWorkspace />
    </Suspense>
  );
}
