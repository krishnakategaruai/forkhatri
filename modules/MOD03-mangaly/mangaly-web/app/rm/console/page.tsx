"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import { Avatar } from "@/components/Avatar";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { resolveMediaUrl } from "@/lib/api";
import { assignMember, formatDay, isRelationshipManager, listAssignments, type RmAssignment } from "@/lib/rm";

import "../rm.css";

/* [DEC-V1-032] The relationship manager's console: the families they help,
 * and (v1) taking on a member themselves. Real allocation — a queue, a
 * supervisor in operations, routing by language and region — is backlog. */

export default function RmConsolePage() {
  const { t, i18n } = useTranslation(["rm", "common"]);
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [rows, setRows] = useState<RmAssignment[]>([]);
  const [memberId, setMemberId] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      const ok = await isRelationshipManager();
      if (!alive) return;
      setAllowed(ok);
      if (ok) setRows((await listAssignments()) ?? []);
    })();
    return () => {
      alive = false;
    };
  }, []);

  const take = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    const r = await assignMember(memberId.trim(), note.trim());
    setSaving(false);
    if (!r.ok) {
      setError(r.message ?? t("rm:console.take.failed"));
      return;
    }
    setRows((prev) => [r.data, ...prev]);
    setMemberId("");
    setNote("");
  };

  const active = rows.filter((a) => a.status === "active");
  const ended = rows.filter((a) => a.status !== "active");

  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("rm:console.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen rm-console">
        {allowed === null ? (
          <p className="caption">{t("common:state.loading")}</p>
        ) : !allowed ? (
          <div className="empty rm-empty">
            <h2 className="h3">{t("rm:console.notRm.title")}</h2>
            <p className="muted">{t("rm:console.notRm.body")}</p>
          </div>
        ) : (
          <>
            <p className="caption rm-console__intro">{t("rm:console.intro")}</p>

            <section className="section">
              <div className="section__head">
                <h3 className="h3" style={{ margin: 0 }}>
                  {t("rm:console.families.title")}
                  {active.length > 0 && <span className="section-card__count"> · {active.length}</span>}
                </h3>
              </div>
              {active.length === 0 ? (
                <p className="caption">{t("rm:console.families.empty")}</p>
              ) : (
                <ul className="rm-assignments">
                  {active.map((a) => (
                    <li key={a.id}>
                      <Link className="rm-assignment" href={`/rm/console/${a.id}`}>
                        <Avatar name={a.member_name ?? ""} photoUrl={resolveMediaUrl(a.member_photo_url)} size={48} />
                        <span className="rm-assignment__text">
                          <span className="rm-assignment__name">{a.member_name ?? t("rm:console.families.unnamed")}</span>
                          <span className="caption">
                            {t("rm:console.families.since", { date: formatDay(a.assigned_at, i18n.language) })}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="section">
              <h3 className="h3" style={{ margin: 0 }}>
                {t("rm:console.take.title")}
              </h3>
              <form className="card rm-take" onSubmit={take}>
                <p className="caption" style={{ margin: 0 }}>
                  {t("rm:console.take.hint")}
                </p>
                <label className="field">
                  <span className="label">{t("rm:console.take.member")}</span>
                  <input
                    className="input"
                    value={memberId}
                    onChange={(e) => setMemberId(e.target.value)}
                    placeholder={t("rm:console.take.memberPlaceholder")}
                    required
                  />
                </label>
                <label className="field">
                  <span className="label">{t("rm:console.take.note")}</span>
                  <textarea
                    className="textarea"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder={t("rm:console.take.notePlaceholder")}
                    maxLength={1000}
                  />
                </label>
                {error && <p className="rm-inline-error">{error}</p>}
                <div>
                  <button type="submit" className="btn btn--primary" disabled={saving || !memberId.trim()}>
                    {t("rm:console.take.submit")}
                  </button>
                </div>
              </form>
            </section>

            {ended.length > 0 && (
              <section className="section">
                <h3 className="h3" style={{ margin: 0 }}>
                  {t("rm:console.families.ended")}
                </h3>
                <ul className="rm-assignments">
                  {ended.map((a) => (
                    <li key={a.id}>
                      <Link className="rm-assignment rm-assignment--ended" href={`/rm/console/${a.id}`}>
                        <Avatar name={a.member_name ?? ""} photoUrl={resolveMediaUrl(a.member_photo_url)} size={40} />
                        <span className="rm-assignment__text">
                          <span className="rm-assignment__name">{a.member_name ?? t("rm:console.families.unnamed")}</span>
                          <span className="caption">
                            {t("rm:console.families.endedOn", { date: formatDay(a.ended_at, i18n.language) })}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}
