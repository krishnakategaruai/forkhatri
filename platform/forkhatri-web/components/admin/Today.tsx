"use client";

/**
 * Today: "what needs me", before any chart (Discourse / Reddit mod home pattern).
 * Open and urgent items from every module queue the person is appointed to, requests
 * waiting for a second person, suspensions and terms about to end; then a few
 * numbers and the latest recorded actions.
 */
import Link from "next/link";
import { admin, type QueueView } from "@/lib/admin-api";
import { humanise } from "@/lib/admin-i18n";
import { AuditLine } from "./AuditLog";
import { Badge, Empty, errorMessage, ErrorLine, formatNumber, isPast, Loading, relative, roleName, scopeName, Section, useConsole, useLoad } from "./kit";
import { isOpen } from "./Queues";

export default function Today() {
  const { me, t, lang, can, version } = useConsole();
  const overview = useLoad(() => admin.overview(), [version]);
  const queueLoad = useLoad(() => (me.module_scopes.length ? admin.queues(lang).catch(() => [] as QueueView[]) : Promise.resolve([] as QueueView[])), [lang, me.module_scopes.length, version]);
  const data = overview.data;
  const queues = queueLoad.data;
  const error = overview.error ? errorMessage(t, overview.error) : null;

  const firstName = (me.member.display_name ?? "").split(" ")[0];

  if (error) return <ErrorLine error={error} />;
  if (!data || !queues) return <Loading />;

  const queueRows = queues
    .map((view) => {
      const open = view.items.filter((i) => isOpen(i.status));
      const overdue = open.filter((i) => i.due_at && isPast(i.due_at)).length;
      const urgent = open.filter((i) => i.priority === "urgent").length;
      return { view, open: open.length, urgent, overdue };
    })
    .filter((row) => row.open > 0 || (row.view.error && row.view.error !== "not_connected"));
  const approvals = data.approvals.filter((a) => a.can_decide);
  const needs = queueRows.length + (approvals.length ? 1 : 0) + data.suspensions_ending.length + data.terms_ending.length;

  return (
    <div className="adm-page">
      <header className="adm-pagehead">
        <div>
          <h1>{t("greeting", { name: firstName })}</h1>
          <p>{t("todaySub")}</p>
          <div className="adm-myroles" aria-label={t("yourRoles")}>
            {me.roles.map((r) => (
              <Badge key={r.assignment_id} tone="accent">
                {roleName(t, r.role)} · {scopeName(t, r.scope_kind, null, r.scope_key)}
                {r.title && r.title !== roleName(t, r.role) ? ` · ${r.title}` : ""}
              </Badge>
            ))}
          </div>
        </div>
      </header>

      <Section title={t("needsYou")}>
        {needs === 0 ? (
          <Empty>{t("allClear")}</Empty>
        ) : (
          <ul className="adm-list">
            {queueRows.map(({ view, open, urgent, overdue }) => (
              <li key={`${view.module_id}/${view.view_id}`}>
                <Link className="adm-row" href={`/admin/queues?view=${view.module_id}/${view.view_id ?? ""}`}>
                  <span className={`adm-dot ${urgent || overdue ? "is-urgent" : view.error ? "is-warn" : ""}`} aria-hidden="true" />
                  <span className="adm-row-main">
                    <span className="adm-row-title">
                      {view.error ? t("queueNotReachable", { queue: humanise(view.module_id) }) : t("queueOpen", { n: open, queue: view.title })}
                    </span>
                  </span>
                  {urgent > 0 && <Badge tone="danger">{t("queueUrgent", { n: urgent })}</Badge>}
                  {overdue > 0 && <Badge tone="danger">{t("queueOverdue", { n: overdue })}</Badge>}
                </Link>
              </li>
            ))}
            {approvals.length > 0 && (
              <li>
                <Link className="adm-row" href="/admin/approvals">
                  <span className="adm-dot is-warn" aria-hidden="true" />
                  <span className="adm-row-main">
                    <span className="adm-row-title">{t("approvalsWaiting", { n: approvals.length })}</span>
                  </span>
                </Link>
              </li>
            )}
            {data.suspensions_ending.map((s) => (
              <li key={`s-${s.member.member_id}`}>
                <Link className="adm-row" href={`/admin/members/${s.member.member_id}`}>
                  <span className="adm-dot" aria-hidden="true" />
                  <span className="adm-row-main">
                    <span className="adm-row-title">{t("suspensionEnds", { name: s.member.display_name ?? "", when: relative(s.ends_at, lang, t) })}</span>
                  </span>
                </Link>
              </li>
            ))}
            {data.terms_ending.map((term) => (
              <li key={term.assignment_id}>
                <Link className="adm-row" href={can("roles.view") ? "/admin/team" : `/admin/members/${term.member.member_id}`}>
                  <span className="adm-dot" aria-hidden="true" />
                  <span className="adm-row-main">
                    <span className="adm-row-title">
                      {t("termEnds", { name: term.member.display_name ?? "", role: roleName(t, term.role), when: relative(term.ends_at, lang, t) })}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <div className="adm-kpis">
        <Kpi label={t("kpiMembers")} value={formatNumber(data.members.total, lang)} note={t("kpiNotJoined", { n: formatNumber(data.members.not_joined, lang) })} />
        <Kpi label={t("kpiActive")} value={formatNumber(data.members.active_7d, lang)} />
        <Kpi label={t("kpiNew")} value={formatNumber(data.members.new_7d, lang)} />
        <Kpi label={t("kpiSuspended")} value={formatNumber(data.members.suspended, lang)} href={can("members.view") ? "/admin/members?status=suspended" : undefined} />
      </div>

      {can("audit.view") && (
        <Section
          title={t("recentActivity")}
          aside={
            <Link className="adm-link" href="/admin/audit">
              {t("seeAll")}
            </Link>
          }
        >
          {data.recent.length === 0 ? (
            <Empty>{t("auditEmpty")}</Empty>
          ) : (
            <ul className="adm-timeline">
              {data.recent.map((event) => (
                <AuditLine key={event.id} event={event} />
              ))}
            </ul>
          )}
        </Section>
      )}
    </div>
  );
}

function Kpi({ label, value, note, href }: { label: string; value: string; note?: string; href?: string }) {
  const body = (
    <>
      <span className="adm-kpi-label">{label}</span>
      <span className="adm-kpi-value">{value}</span>
      {note && <span className="adm-kpi-note">{note}</span>}
    </>
  );
  return href ? (
    <Link className="adm-kpi is-link" href={href}>
      {body}
    </Link>
  ) : (
    <div className="adm-kpi">{body}</div>
  );
}
