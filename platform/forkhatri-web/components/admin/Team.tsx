"use client";

/**
 * Team and roles: who holds which role, over which area, until when. Appointing a
 * senior office bearer goes to Approvals unless an owner does it; every appointment
 * and its end is in the audit log.
 */
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { admin, type Assignment, type Chapter, type MemberRow, type RoleKey } from "@/lib/admin-api";
import { adminLabel, type AdminKey } from "@/lib/admin-i18n";
import { Avatar, Badge, Chips, Dialog, errorMessage, ErrorLine, Field, formatDate, Loading, PageHead, roleName, scopeName, Section, useConsole, useLoad } from "./kit";

export default function Team() {
  const { t, can, me, changed, version } = useConsole();
  const list = useLoad(() => admin.roles(), [version]);
  const rows = list.data;
  const error = list.error ? errorMessage(t, list.error) : null;
  const [appointing, setAppointing] = useState(false);
  const [ending, setEnding] = useState<Assignment | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const canAppoint = can("roles.manage") || me.managed_chapters.length > 0;
  const groups = useMemo(() => {
    const order = me.catalogue?.roles.map((r) => r.key) ?? [];
    const map = new Map<RoleKey, Assignment[]>();
    for (const row of rows ?? []) map.set(row.role, [...(map.get(row.role) ?? []), row]);
    return order.filter((key) => map.has(key)).map((key) => ({ role: key, rows: map.get(key)! }));
  }, [rows, me.catalogue]);

  const mayEnd = (a: Assignment) =>
    a.member.member_id === me.member.member_id
      ? a.role !== "owner" || me.roles.some((r) => r.role === "owner")
      : a.role === "owner"
        ? me.roles.some((r) => r.role === "owner")
        : can("roles.manage") || (a.scope_kind === "chapter" && !!a.scope_key && me.managed_chapters.includes(a.scope_key));

  return (
    <div className="adm-page">
      <PageHead
        title={t("teamTitle")}
        sub={t("teamSub")}
        actions={
          canAppoint && (
            <button type="button" className="adm-btn primary" onClick={() => setAppointing(true)}>
              {t("appoint")}
            </button>
          )
        }
      />
      {notice && (
        <p className="adm-success" role="status">
          {notice}
        </p>
      )}
      <ErrorLine error={error} />
      {!rows ? (
        <Loading />
      ) : (
        groups.map((group) => (
          <Section key={group.role} title={roleName(t, group.role)} aside={<span className="adm-muted">{adminLabel(t, `roleHelp_${group.role}`, "")}</span>}>
            <ul className="adm-list adm-card">
              {group.rows.map((a) => (
                <AssignmentRow key={a.id} a={a} onEnd={mayEnd(a) ? () => setEnding(a) : undefined} />
              ))}
            </ul>
          </Section>
        ))
      )}
      <AppointDialog
        open={appointing}
        onClose={() => setAppointing(false)}
        onDone={(message) => {
          setAppointing(false);
          setNotice(message);
          changed();
        }}
      />
      <EndDialog
        a={ending}
        onClose={() => setEnding(null)}
        onDone={() => {
          setEnding(null);
          changed();
        }}
      />
    </div>
  );
}

export function AssignmentRow({ a, onEnd }: { a: Assignment; onEnd?: () => void }) {
  const { t, lang } = useConsole();
  return (
    <li className="adm-row is-static">
      <Avatar person={a.member} />
      <span className="adm-row-main">
        <span className="adm-row-title">
          <Link href={`/admin/members/${a.member.member_id}`} className="adm-plain-link">
            {a.member.display_name}
          </Link>
          {a.title && <span className="adm-muted"> · {a.title}</span>}
        </span>
        <span className="adm-row-sub">
          {roleName(t, a.role)} · {scopeName(t, a.scope_kind, a.scope_name, a.scope_key)} · {a.ends_at ? t("untilDate", { date: formatDate(a.ends_at, lang) }) : t("noEndDate")}
        </span>
        <span className="adm-row-note">{a.granted_by ? t("appointedBy", { name: a.granted_by.display_name ?? "" }) : t("appointedBySystem")}</span>
      </span>
      {onEnd && (
        <button type="button" className="adm-btn small" onClick={onEnd}>
          {t("endAppointment")}
        </button>
      )}
    </li>
  );
}

function EndDialog({ a, onClose, onDone }: { a: Assignment | null; onClose: () => void; onDone: () => void }) {
  const { t } = useConsole();
  return (
    <Dialog open={!!a} onClose={onClose} title={a ? t("endAppointmentTitle", { name: a.member.display_name ?? "", role: roleName(t, a.role) }) : ""}>
      {a && <EndForm key={a.id} a={a} onClose={onClose} onDone={onDone} />}
    </Dialog>
  );
}

function EndForm({ a, onClose, onDone }: { a: Assignment; onClose: () => void; onDone: () => void }) {
  const { t } = useConsole();
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <Field label={t("noteLabel")}>
        <textarea className="adm-input" rows={3} value={note} placeholder={t("notePlaceholder")} onChange={(e) => setNote(e.target.value)} />
      </Field>
      <ErrorLine error={error} />
      <div className="adm-actions end">
        <button type="button" className="adm-btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button
          type="button"
          className="adm-btn danger"
          disabled={note.trim().length < 3}
          onClick={async () => {
            try {
              await admin.revoke(a.id, note);
              onDone();
            } catch (e) {
              setError(errorMessage(t, e));
            }
          }}
        >
          {t("endAppointment")}
        </button>
      </div>
    </>
  );
}

type Term = "year" | "none" | "date";

/** Appoint someone. `preset` fixes the area when opened from a chapter on the Organisation page. */
type Preset = { scope_kind: "chapter" | "module"; scope_key: string; scope_name: string };

export function AppointDialog({ open, onClose, onDone, preset }: { open: boolean; onClose: () => void; onDone: (message: string) => void; preset?: Preset }) {
  const { t } = useConsole();
  return (
    <Dialog open={open} onClose={onClose} title={preset ? `${t("appointTitle")} · ${preset.scope_name}` : t("appointTitle")}>
      {open && <AppointForm onClose={onClose} onDone={onDone} preset={preset} />}
    </Dialog>
  );
}

function endsAt(term: Term, endDate: string): string | null {
  if (term === "year") return new Date(Date.now() + 365 * 86400000).toISOString();
  if (term === "date") return new Date(`${endDate}T23:59:00`).toISOString();
  return null;
}

/** Mounted each time the dialog opens, so it always starts empty. */
function AppointForm({ onClose, onDone, preset }: { onClose: () => void; onDone: (message: string) => void; preset?: Preset }) {
  const { t, me, can } = useConsole();
  const isOwner = me.roles.some((r) => r.role === "owner");
  const [person, setPerson] = useState<MemberRow | null>(null);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<RoleKey | "">("");
  const [scopeKey, setScopeKey] = useState(preset?.scope_key ?? "");
  const [title, setTitle] = useState("");
  const [term, setTerm] = useState<Term>("year");
  const [endDate, setEndDate] = useState("");
  const [note, setNote] = useState("");
  const modules = useLoad(() => admin.modules().then((m) => m.filter((x) => x.availability !== "planned")), []).data ?? [];
  const chapters = useLoad(() => (can("org.view") ? admin.org().then((o) => o.chapters) : Promise.resolve([] as Chapter[])), []).data ?? [];
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [results, setResults] = useState<{ q: string; rows: MemberRow[] }>({ q: "", rows: [] });
  useEffect(() => {
    const q = search.trim();
    if (person || q.length < 2) return;
    const timer = setTimeout(() => {
      admin
        .members({ q, status: "active" })
        .then((page) => setResults({ q, rows: page.members.slice(0, 6) }))
        .catch(() => setResults({ q, rows: [] }));
    }, 200);
    return () => clearTimeout(timer);
  }, [search, person]);
  const matches = !person && results.q === search.trim() ? results.rows : [];

  const roles = (me.catalogue?.roles ?? []).filter((r) => {
    if (preset && r.scope_kind !== preset.scope_kind) return false;
    if (r.key === "owner") return isOwner;
    if (can("roles.manage")) return true;
    return r.scope_kind === "chapter";
  });
  const def = roles.find((r) => r.key === role);
  const scopeKind = def?.scope_kind;
  const needsApproval = !!def?.sensitive && !isOwner;
  const chapterChoices = can("roles.manage") ? chapters : chapters.filter((c) => me.managed_chapters.includes(c.key));
  const valid = person && def && (scopeKind === "platform" || scopeKey) && note.trim().length >= 3 && (term !== "date" || endDate);

  async function submit() {
    if (!person || !def) return;
    setBusy(true);
    setError(null);
    const ends_at = endsAt(term, endDate);
    try {
      const result = await admin.grant({
        member_id: person.member_id,
        role: def.key,
        scope_key: scopeKind === "platform" ? null : scopeKey,
        title: title.trim() || null,
        ends_at,
        note,
      });
      onDone(result.status === "granted" ? t("appointed") : t("sentForApproval"));
    } catch (e) {
      setError(errorMessage(t, e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Field label={t("pickPerson")}>
        {person ? (
          <div className="adm-picked">
            <Avatar person={person} size={32} />
            <span>
              {person.display_name} <span className="adm-muted" dir="ltr">{person.phone_hint}</span>
            </span>
            <button type="button" className="adm-btn small" onClick={() => setPerson(null)}>
              {t("change")}
            </button>
          </div>
        ) : (
          <>
            <input className="adm-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t("pickPersonPlaceholder")} autoComplete="off" />
            {matches.length > 0 && (
              <ul className="adm-picker">
                {matches.map((r) => (
                  <li key={r.member_id}>
                    <button type="button" onClick={() => setPerson(r)}>
                      <Avatar person={r} size={28} />
                      <span>{r.display_name}</span>
                      <span className="adm-muted" dir="ltr">
                        {r.phone_hint ?? r.email_hint}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </Field>
      <Field label={t("pickRole")} hint={def ? adminLabel(t, `roleHelp_${def.key}`, "") : undefined}>
        <select
          className="adm-input"
          value={role}
          onChange={(e) => {
            setRole(e.target.value as RoleKey);
            if (!preset) setScopeKey("");
          }}
        >
          <option value="" disabled>
            —
          </option>
          {roles.map((r) => (
            <option key={r.key} value={r.key}>
              {roleName(t, r.key)}
            </option>
          ))}
        </select>
      </Field>
      {scopeKind === "module" && !preset && (
        <Field label={t("pickModule")}>
          <select className="adm-input" value={scopeKey} onChange={(e) => setScopeKey(e.target.value)}>
            <option value="" disabled>
              —
            </option>
            {modules.map((m) => (
              <option key={m.key} value={m.key}>
                {m.name}
              </option>
            ))}
          </select>
        </Field>
      )}
      {scopeKind === "chapter" && !preset && (
        <Field label={t("pickChapter")}>
          <select className="adm-input" value={scopeKey} onChange={(e) => setScopeKey(e.target.value)}>
            <option value="" disabled>
              —
            </option>
            {chapterChoices.map((c) => (
              <option key={c.key} value={c.key}>
                {c.kind === "city" ? `${chapters.find((p) => p.key === c.parent_key)?.name ?? ""} › ${c.name}` : c.name}
              </option>
            ))}
          </select>
        </Field>
      )}
      <Field label={t("titleLabel")}>
        <input className="adm-input" value={title} maxLength={60} onChange={(e) => setTitle(e.target.value)} placeholder={t("titlePlaceholder")} />
      </Field>
      <Field label={t("termEndsLabel")}>
        <Chips
          label={t("termEndsLabel")}
          value={term}
          onChange={setTerm}
          options={(["year", "none", "date"] as Term[]).map((v) => ({ value: v, label: t(({ year: "termOneYear", none: "termNone", date: "termCustom" } as Record<Term, AdminKey>)[v]) }))}
        />
        {term === "date" && <input className="adm-input" type="date" value={endDate} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setEndDate(e.target.value)} />}
      </Field>
      <Field label={t("appointNote")}>
        <textarea className="adm-input" rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("appointNotePlaceholder")} />
      </Field>
      {needsApproval && <Badge tone="warn">{t("needsSecondPerson")}</Badge>}
      <ErrorLine error={error} />
      <div className="adm-actions end">
        <button type="button" className="adm-btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button type="button" className="adm-btn primary" disabled={!valid || busy} onClick={() => void submit()}>
          {t("appointAction")}
        </button>
      </div>
    </>
  );
}

