"use client";

/**
 * One person, across the whole of ForKhatri: their platform account, each module's own
 * view of them (pricing tiers differ per module and are shown side by side, never merged),
 * their roles, suspensions and every recorded action about them. Actions that change
 * someone's access carry a reason and are audited; a ban always needs a second person.
 */
import Link from "next/link";
import { useState } from "react";
import { admin, type MemberDetail as Data, type ModuleSummary } from "@/lib/admin-api";
import { humanise } from "@/lib/admin-i18n";
import { AuditLine } from "./AuditLog";
import {
  Avatar,
  Badge,
  Chips,
  Dialog,
  Empty,
  errorMessage,
  ErrorLine,
  Field,
  formatDate,
  Loading,
  reasonName,
  relative,
  roleName,
  scopeName,
  Section,
  useConsole,
  useLoad,
} from "./kit";

type Act = "suspend" | "lift" | "signOut" | "ban" | "contact" | null;
const LANG_NAMES: Record<string, string> = { en: "English", hi: "हिन्दी", te: "తెలుగు" };

export default function MemberDetail({ memberId }: { memberId: string }) {
  const { t, lang, can, me, changed } = useConsole();
  const detail = useLoad(() => admin.member(memberId), [memberId]);
  const summaries = useLoad(
    () => (me.module_scopes.length ? admin.memberModules(memberId, lang).catch(() => [] as ModuleSummary[]) : Promise.resolve([] as ModuleSummary[])),
    [memberId, lang, me.module_scopes.length],
  );
  const data = detail.data;
  const modules = summaries.data;
  const error = detail.error ? errorMessage(t, detail.error) : null;
  const [act, setAct] = useState<Act>(null);
  const [contact, setContact] = useState<{ phone_e164: string | null; email: string | null } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (error && !data) return <ErrorLine error={error} />;
  if (!data) return <Loading />;

  const m = data.member;
  const open = data.suspensions.find((s) => !s.lifted_at);
  const isSelf = m.member_id === me.member.member_id;
  const banPending = data.pending_approvals.some((a) => a.kind === "ban");

  return (
    <div className="adm-page">
      <Link href="/admin/members" className="adm-back">
        ← {t("membersTitle")}
      </Link>
      <header className="adm-person">
        <Avatar person={m} size={64} />
        <div className="adm-person-main">
          <h1>{m.display_name}</h1>
          <div className="adm-person-badges">
            {open ? (
              <Badge tone="danger">{open.kind === "ban" ? t("status_banned") : t("status_suspended")}</Badge>
            ) : m.status === "active" ? (
              <Badge tone="ok">{t("status_active")}</Badge>
            ) : (
              <Badge tone="danger">{t(m.status === "suspended" ? "status_suspended" : "status_deleted")}</Badge>
            )}
            {!m.joined && <Badge>{t("status_not_joined")}</Badge>}
            {data.roles.map((r) => (
              <Badge key={r.id} tone="accent">
                {roleName(t, r.role)} · {scopeName(t, r.scope_kind, r.scope_name, r.scope_key)}
              </Badge>
            ))}
            {banPending && <Badge tone="warn">{t("pendingOnMember")}</Badge>}
          </div>
          <p className="adm-person-contact" dir="ltr">
            {contact ? [contact.phone_e164, contact.email].filter(Boolean).join(" · ") : [m.phone_hint, m.email_hint].filter(Boolean).join(" · ")}
          </p>
        </div>
      </header>

      {notice && (
        <p className="adm-success" role="status">
          {notice}
        </p>
      )}
      <ErrorLine error={error} />

      {isSelf ? (
        <p className="adm-muted">{t("cannotActSelf")}</p>
      ) : (
        <div className="adm-actions adm-person-actions">
          {can("members.contact") && !contact && (
            <button type="button" className="adm-btn" onClick={() => setAct("contact")}>
              {t("showContact")}
            </button>
          )}
          {can("members.suspend") && !open && m.status !== "deleted" && (
            <button type="button" className="adm-btn danger-outline" onClick={() => setAct("suspend")}>
              {t("actSuspend")}
            </button>
          )}
          {can("members.suspend") && open && (open.kind === "suspension" || can("approvals.decide")) && (
            <button type="button" className="adm-btn" onClick={() => setAct("lift")}>
              {open.kind === "ban" ? t("actLiftBan") : t("actLift")}
            </button>
          )}
          {can("members.suspend") && data.sessions.active > 0 && (
            <button type="button" className="adm-btn" onClick={() => setAct("signOut")}>
              {t("actSignOut")}
            </button>
          )}
          {can("members.ban") && open?.kind !== "ban" && !banPending && (
            <button type="button" className="adm-btn danger-outline" onClick={() => setAct("ban")}>
              {t("actBan")}
            </button>
          )}
        </div>
      )}

      <div className="adm-grid-2">
        <Section title={t("accountTitle")}>
          <dl className="adm-facts">
            <div className="adm-fact">
              <dt>{t("memberSince")}</dt>
              <dd>{formatDate(m.created_at, lang)}</dd>
            </div>
            <div className="adm-fact">
              <dt>{t("lastSeen", { when: "" }).trim()}</dt>
              <dd>{data.sessions.last_seen_at ? relative(data.sessions.last_seen_at, lang, t) : t("neverSignedIn")}</dd>
            </div>
            <div className="adm-fact">
              <dt>{t("devicesSignedIn")}</dt>
              <dd>{t("devicesN", { n: data.sessions.active })}</dd>
            </div>
            <div className="adm-fact">
              <dt>{t("language")}</dt>
              <dd>{LANG_NAMES[m.preferred_language] ?? m.preferred_language}</dd>
            </div>
            <div className="adm-fact">
              <dt>{t("verification")}</dt>
              <dd>{t("verificationLevel", { n: m.identity_level })}</dd>
            </div>
          </dl>
        </Section>

        <Section title={t("modulesUsed")}>
          {data.modules.length === 0 ? (
            <Empty>{t("noModulesUsed")}</Empty>
          ) : (
            <ul className="adm-list">
              {data.modules.map((mod) => (
                <li key={mod.key} className="adm-row is-static">
                  <span className="adm-row-main">
                    <span className="adm-row-title">{mod.name}</span>
                    <span className="adm-row-sub">{t("visitsN", { n: mod.visits, when: relative(mod.last_entered_at, lang, t) })}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      {modules && modules.length > 0 && (
        <Section title={t("inEachModule")}>
          <p className="adm-muted adm-section-note">{t("inEachModuleNote")}</p>
          <div className="adm-module-cards">
            {modules.map((summary) => (
              <ModuleCard key={summary.module_id} summary={summary} />
            ))}
          </div>
        </Section>
      )}

      <Section title={t("suspensionHistory")}>
        {data.suspensions.length === 0 ? (
          <Empty>{t("noSuspensions")}</Empty>
        ) : (
          <ul className="adm-list">
            {data.suspensions.map((s) => (
              <li key={s.id} className="adm-row is-static">
                <span className={`adm-dot ${s.lifted_at ? "" : "is-urgent"}`} aria-hidden="true" />
                <span className="adm-row-main">
                  <span className="adm-row-title">
                    {t("suspendedBy", { kind: t(s.kind === "ban" ? "kind_ban" : "kind_suspension"), name: s.by?.display_name ?? t("systemActor"), reason: reasonName(t, s.reason_code) })}
                  </span>
                  <span className="adm-row-sub">
                    {formatDate(s.starts_at, lang)} → {s.ends_at ? formatDate(s.ends_at, lang) : t("untilLifted")}
                    {s.lifted_at &&
                      ` · ${s.lifted_by ? t("liftedBy", { name: s.lifted_by.display_name ?? "", date: formatDate(s.lifted_at, lang) }) : t("liftedAuto", { date: formatDate(s.lifted_at, lang) })}`}
                  </span>
                  <span className="adm-row-note">{s.note}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title={t("history")}>
        {data.history.length === 0 ? (
          <Empty>{t("noHistory")}</Empty>
        ) : (
          <ul className="adm-timeline">
            {data.history.map((event) => (
              <AuditLine key={event.id} event={event} linkTarget={false} />
            ))}
          </ul>
        )}
      </Section>

      <ActionDialog
        act={act}
        name={m.display_name}
        onClose={() => setAct(null)}
        onDone={(next, message) => {
          if (next) detail.set(next);
          else detail.reload();
          setNotice(message);
          setAct(null);
          changed();
        }}
        onContact={setContact}
        memberId={m.member_id}
      />
    </div>
  );
}

function ModuleCard({ summary }: { summary: ModuleSummary }) {
  const { t, lang } = useConsole();
  return (
    <article className="adm-module-card">
      <h3>{humanise(summary.module_id)}</h3>
      {summary.error ? (
        <p className="adm-muted">{t("moduleSummaryError")}</p>
      ) : (
        <>
          <p className="adm-module-plan">
            <span className="adm-muted">{t("planLabel")}</span>
            <strong>{summary.plan ? summary.plan.name || humanise(summary.plan.tier) : t("noPlan")}</strong>
            {summary.plan?.status && <Badge>{humanise(summary.plan.status)}</Badge>}
            {summary.plan?.renews_at && <span className="adm-muted">{formatDate(summary.plan.renews_at, lang)}</span>}
          </p>
          {summary.facts && summary.facts.length > 0 && (
            <dl className="adm-facts">
              {summary.facts.map((f) => (
                <div key={f.label} className="adm-fact">
                  <dt>{f.label}</dt>
                  <dd>{f.value}</dd>
                </div>
              ))}
            </dl>
          )}
          {summary.flags && summary.flags.length > 0 && (
            <div className="adm-person-badges">
              {summary.flags.map((f) => (
                <Badge key={f} tone="warn">
                  {humanise(f)}
                </Badge>
              ))}
            </div>
          )}
        </>
      )}
    </article>
  );
}

function ActionDialog({
  act,
  name,
  memberId,
  onClose,
  onDone,
  onContact,
}: {
  act: Act;
  name: string;
  memberId: string;
  onClose: () => void;
  onDone: (next: Data | null, message: string | null) => void;
  onContact: (c: { phone_e164: string | null; email: string | null }) => void;
}) {
  const { t } = useConsole();
  const titles: Record<Exclude<Act, null>, string> = {
    suspend: t("suspendTitle", { name }),
    lift: t("liftTitle", { name }),
    signOut: t("signOutTitle", { name }),
    ban: t("banTitle", { name }),
    contact: t("showContact"),
  };
  return (
    <Dialog open={act !== null} onClose={onClose} title={act ? titles[act] : ""}>
      {act && <ActionForm key={act} act={act} name={name} memberId={memberId} onClose={onClose} onDone={onDone} onContact={onContact} />}
    </Dialog>
  );
}

/** Mounted fresh for each action, so every form starts empty. */
function ActionForm({
  act,
  name,
  memberId,
  onClose,
  onDone,
  onContact,
}: {
  act: Exclude<Act, null>;
  name: string;
  memberId: string;
  onClose: () => void;
  onDone: (next: Data | null, message: string | null) => void;
  onContact: (c: { phone_e164: string | null; email: string | null }) => void;
}) {
  const { me, t } = useConsole();
  const reasons = me.catalogue?.reason_codes ?? [];
  const lengths = me.catalogue?.suspension_days ?? [1, 3, 7, 30];
  const [reason, setReason] = useState("");
  const [days, setDays] = useState<number | null>(7);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const needsReason = act === "suspend" || act === "ban";

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      if (act === "suspend") onDone(await admin.suspend(memberId, { reason_code: reason, days, note }), null);
      else if (act === "lift") onDone(await admin.lift(memberId, note), null);
      else if (act === "signOut") onDone(await admin.signOut(memberId, note), null);
      else if (act === "ban") {
        await admin.ban(memberId, { reason_code: reason, note });
        onDone(null, t("sentForApproval"));
      } else if (act === "contact") {
        onContact(await admin.contact(memberId, note));
        onDone(null, null);
      }
    } catch (e) {
      setError(errorMessage(t, e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {act === "suspend" && <p className="adm-muted">{t("suspendHelp", { name })}</p>}
      {act === "ban" && <p className="adm-muted">{t("banHelp")}</p>}
      {act === "signOut" && <p className="adm-muted">{t("signOutHelp")}</p>}
      {act === "contact" && <p className="adm-muted">{t("contactNote")}</p>}
      {needsReason && (
        <Field label={t("reasonLabel")}>
          <select className="adm-input" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="" disabled>
              —
            </option>
            {reasons.map((code) => (
              <option key={code} value={code}>
                {reasonName(t, code)}
              </option>
            ))}
          </select>
        </Field>
      )}
      {act === "suspend" && (
        <Field label={t("lengthLabel")}>
          <Chips
            label={t("lengthLabel")}
            value={days}
            onChange={setDays}
            options={[...lengths.map((d) => ({ value: d as number | null, label: d === 1 ? t("days1") : t("daysN", { n: d }) })), { value: null, label: t("untilLifted") }]}
          />
        </Field>
      )}
      <Field label={act === "contact" ? t("contactReason") : t("noteLabel")}>
        <textarea className="adm-input" rows={3} value={note} placeholder={t("notePlaceholder")} onChange={(e) => setNote(e.target.value)} />
      </Field>
      <ErrorLine error={error} />
      <div className="adm-actions end">
        <button type="button" className="adm-btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button
          type="button"
          className={`adm-btn ${act === "suspend" || act === "ban" ? "danger" : "primary"}`}
          disabled={busy || note.trim().length < 3 || (needsReason && !reason)}
          onClick={() => void submit()}
        >
          {act === "suspend" ? t("actSuspend") : act === "ban" ? t("actBan") : act === "lift" ? t("confirm") : act === "signOut" ? t("actSignOut") : t("showContact")}
        </button>
      </div>
    </>
  );
}

