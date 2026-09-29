"use client";

/** The append-only audit log: who did what, to whom, why and when. Nobody can edit it. */
import Link from "next/link";
import { useState } from "react";
import { admin, type AuditEvent } from "@/lib/admin-api";
import { adminLabel, humanise, type AdminKey } from "@/lib/admin-i18n";
import { Chips, Empty, errorMessage, ErrorLine, formatDateTime, Loading, PageHead, reasonName, roleName, useConsole, useLoad } from "./kit";

const FILTERS: { value: string; label: AdminKey }[] = [
  { value: "", label: "auditAll" },
  { value: "member.", label: "auditMembers" },
  { value: "role.", label: "auditRoles" },
  { value: "approval.", label: "auditApprovals" },
  { value: "queue.", label: "auditQueues" },
  { value: "org.", label: "auditOrg" },
  { value: "module.", label: "auditModules" },
];

export function AuditLine({ event, linkTarget = true }: { event: AuditEvent; linkTarget?: boolean }) {
  const { t, lang } = useConsole();
  const d = event.details ?? {};
  const role = typeof d.role === "string" ? roleName(t, d.role) : "";
  const vars = {
    actor: event.actor?.display_name ?? t("systemActor"),
    target: event.target?.display_name ?? "",
    role,
    module: event.module_key ? humanise(event.module_key) : "",
    action: typeof d.action === "string" ? humanise(d.action) : humanise(event.action),
    availability: typeof d.to === "string" ? adminLabel(t, `availability_${d.to}`) : "",
    subject: event.subject ?? "",
  };
  const key = `audit_${event.action}` as AdminKey;
  const sentence = t(key, vars) === key ? t("auditFallback", vars) : t(key, vars);
  const detail = [reasonName(t, event.reason_code), event.note].filter(Boolean).join(" · ");
  return (
    <li className="adm-tl-item">
      <span className="adm-tl-dot" aria-hidden="true" />
      <div className="adm-tl-body">
        <p className="adm-tl-text">
          {linkTarget && event.target ? (
            <Link href={`/admin/members/${event.target.member_id}`} className="adm-plain-link">
              {sentence}
            </Link>
          ) : (
            sentence
          )}
        </p>
        {detail && <p className="adm-tl-note">{detail}</p>}
        <time className="adm-tl-time" dateTime={event.at}>
          {formatDateTime(event.at, lang)}
        </time>
      </div>
    </li>
  );
}

export default function AuditLog() {
  const { t } = useConsole();
  const [filter, setFilter] = useState("");
  const first = useLoad(() => admin.audit({ action: filter || undefined }), [filter]);
  const [older, setOlder] = useState<{ filter: string; events: AuditEvent[]; next: number | null } | null>(null);
  const [loadError, setError] = useState<string | null>(null);
  const extra = older?.filter === filter ? older : null;
  const events = first.data ? [...first.data.events, ...(extra?.events ?? [])] : null;
  const next = extra ? extra.next : (first.data?.next_before ?? null);
  const error = loadError ?? (first.error ? errorMessage(t, first.error) : null);

  async function loadOlder(before: number) {
    try {
      const page = await admin.audit({ action: filter || undefined, before });
      setOlder({ filter, events: [...(extra?.events ?? []), ...page.events], next: page.next_before });
    } catch (e) {
      setError(errorMessage(t, e));
    }
  }

  return (
    <div className="adm-page">
      <PageHead title={t("auditTitle")} sub={t("auditSub")} />
      <Chips label={t("auditTitle")} value={filter} onChange={setFilter} options={FILTERS.map((f) => ({ value: f.value, label: t(f.label) }))} />
      <ErrorLine error={error} />
      {!events ? (
        <Loading />
      ) : events.length === 0 ? (
        <Empty>{t("auditEmpty")}</Empty>
      ) : (
        <ul className="adm-timeline adm-card">
          {events.map((event) => (
            <AuditLine key={event.id} event={event} />
          ))}
        </ul>
      )}
      {next && (
        <button type="button" className="adm-btn" onClick={() => void loadOlder(next)}>
          {t("loadOlder")}
        </button>
      )}
    </div>
  );
}
