"use client";

/* The family's side of the eye (DEC-V1-033/034): the switch that closes their
 * number to agents, every time an agent opened or exported it, and the report
 * of an unwanted call. The owner (2026-09-29): a family that gets spam calls
 * reports it, and the record of who opened their number shows "who did
 * that". Used on the agent dashboard and on /me/contact-safety, which every
 * family can reach whether or not they work with an agent. */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  formatDay,
  getSuspects,
  listReports,
  reportUnwantedContact,
  type ContactReport,
  type Dashboard,
  type ReportChannel,
  type Suspect,
} from "@/lib/agents";

const CHANNELS: ReportChannel[] = ["call", "whatsapp", "sms", "email"];

/** Today in India as yyyy-mm-dd, and the earliest day a report may name. */
function indiaDay(offsetDays = 0): string {
  const d = new Date(Date.now() + offsetDays * 86_400_000);
  return d.toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
}

/** One line per agent, kind and day: "printed your biodata · 3 times". */
function groupActivity(items: Dashboard["activity"]) {
  const groups: { key: string; name: string; kind: string; at: string; count: number }[] = [];
  for (const a of items) {
    const key = `${a.agent_account_id}|${a.kind}|${a.at.slice(0, 10)}`;
    const found = groups.find((g) => g.key === key);
    if (found) found.count += 1;
    else groups.push({ key, name: a.business_name ?? a.display_name ?? "", kind: a.kind, at: a.at, count: 1 });
  }
  return groups;
}

export function NumberPrivacy({
  dash,
  onToggle,
  showTitle = true,
}: {
  dash: Dashboard;
  onToggle: (open: boolean) => void;
  showTitle?: boolean;
}) {
  const { t, i18n } = useTranslation(["agents"]);
  const open = dash.agents_may_see_contact !== false;
  const groups = groupActivity(dash.activity);
  return (
    <div className="ag-head">
      {showTitle && <span className="label">{t("agents:family.privacy.title")}</span>}
      <label className="ag-switch">
        <input type="checkbox" checked={open} disabled={!dash.may_decide} onChange={(e) => onToggle(e.target.checked)} />
        {t("agents:family.privacy.toggle")}
      </label>
      <span className="caption">{open ? t("agents:family.privacy.on") : t("agents:family.privacy.off")}</span>
      <span className="label" style={{ marginTop: "var(--space-2)" }}>
        {t("agents:family.activity.title")}
      </span>
      {groups.length === 0 ? (
        <span className="caption">{t("agents:family.activity.empty")}</span>
      ) : (
        <ul className="ag-activity">
          {groups.slice(0, 12).map((g) => (
            <li key={g.key}>
              <span>{t(`agents:family.activity.${g.kind}`, { name: g.name })}</span>
              <span className="caption">
                {formatDay(g.at, i18n.language)}
                {g.count > 1 && ` · ${t("agents:family.activity.times", { count: g.count })}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ReportUnwanted({
  forCandidate,
  numberOpen,
  mayDecide,
  onCloseNumber,
}: {
  forCandidate?: string;
  numberOpen: boolean;
  mayDecide: boolean;
  onCloseNumber: () => void;
}) {
  const { t, i18n } = useTranslation(["agents"]);
  const [open, setOpen] = useState(false);
  const [channel, setChannel] = useState<ReportChannel>("call");
  const [day, setDay] = useState(indiaDay());
  const [suspects, setSuspects] = useState<Suspect[] | null>(null);
  const [named, setNamed] = useState<string>("");
  const [note, setNote] = useState("");
  const [closeToo, setCloseToo] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [reports, setReports] = useState<ContactReport[]>([]);

  useEffect(() => {
    let alive = true;
    listReports(forCandidate).then((r) => alive && setReports(r ?? []));
    return () => {
      alive = false;
    };
  }, [forCandidate]);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    getSuspects(day, forCandidate).then((s) => {
      if (!alive) return;
      setSuspects(s ?? []);
      setNamed((prev) => (s ?? []).some((x) => x.agent_account_id === prev) ? prev : "");
    });
    return () => {
      alive = false;
    };
  }, [open, day, forCandidate]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    const out = await reportUnwantedContact({
      channel,
      happened_on: day,
      note: note.trim() || null,
      named_agent_id: named || null,
      for_candidate: forCandidate,
    });
    setBusy(false);
    if (!out.ok) {
      setMessage(out.message ?? null);
      return;
    }
    if (closeToo && numberOpen && mayDecide) onCloseNumber();
    setMessage(t("agents:safety.report.sent"));
    setOpen(false);
    setNote("");
    setNamed("");
    setReports((await listReports(forCandidate)) ?? []);
  };

  return (
    <div className="ag-head ag-report">
      {!open ? (
        <button type="button" className="btn btn--secondary btn--sm" style={{ alignSelf: "flex-start" }} onClick={() => { setOpen(true); setMessage(null); }}>
          {t("agents:safety.report.open")}
        </button>
      ) : (
        <form className="ag-report__form" onSubmit={send}>
          <span className="label">{t("agents:safety.report.title")}</span>
          <fieldset className="ag-report__field">
            <legend className="caption">{t("agents:safety.report.channel")}</legend>
            <div className="ag-chips">
              {CHANNELS.map((c) => (
                <button key={c} type="button" className="ag-chip" aria-pressed={channel === c} onClick={() => setChannel(c)}>
                  {t(`agents:safety.report.channels.${c}`)}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="ag-report__field">
            <span className="caption">{t("agents:safety.report.day")}</span>
            <input className="input" type="date" value={day} min={indiaDay(-90)} max={indiaDay()} onChange={(e) => e.target.value && setDay(e.target.value)} />
          </label>
          <fieldset className="ag-report__field">
            <legend className="caption">{t("agents:safety.report.who")}</legend>
            {suspects && suspects.length === 0 ? (
              <span className="caption">{t("agents:safety.report.noSuspects")}</span>
            ) : (
              <>
                <span className="caption">{t("agents:safety.report.whoLede")}</span>
                {(suspects ?? []).map((s) => (
                  <label key={s.agent_account_id} className="ag-switch">
                    <input type="radio" name="named" checked={named === s.agent_account_id} onChange={() => setNamed(s.agent_account_id)} />
                    <span>
                      {s.business_name ?? s.display_name}
                      {s.city ? ` · ${s.city}` : ""}
                      <span className="caption"> · {formatDay(s.last_at, i18n.language)}</span>
                    </span>
                  </label>
                ))}
                <label className="ag-switch">
                  <input type="radio" name="named" checked={named === ""} onChange={() => setNamed("")} />
                  {t("agents:safety.report.notSure")}
                </label>
              </>
            )}
          </fieldset>
          <label className="ag-report__field">
            <span className="caption">{t("agents:safety.report.note")}</span>
            <textarea className="textarea" value={note} maxLength={2000} onChange={(e) => setNote(e.target.value)} placeholder={t("agents:safety.report.notePlaceholder")} />
          </label>
          {numberOpen && mayDecide && (
            <label className="ag-switch">
              <input type="checkbox" checked={closeToo} onChange={(e) => setCloseToo(e.target.checked)} />
              {t("agents:safety.report.closeToo")}
            </label>
          )}
          <div className="ag-row">
            <button type="submit" className="btn btn--primary btn--sm" disabled={busy}>
              {t("agents:safety.report.send")}
            </button>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => setOpen(false)}>
              {t("agents:family.hide")}
            </button>
          </div>
        </form>
      )}
      {message && <p className="caption">{message}</p>}
      {reports.length > 0 && (
        <>
          <span className="label" style={{ marginTop: "var(--space-2)" }}>
            {t("agents:safety.report.mine")}
          </span>
          <ul className="ag-activity">
            {reports.map((r) => (
              <li key={r.id}>
                <span>
                  {t("agents:safety.report.onDay", {
                    channel: t(`agents:safety.report.channels.${r.channel}`),
                    date: formatDay(r.happened_on, i18n.language),
                  })}
                </span>
                <span className="caption">{t(`agents:safety.report.status.${r.status}`)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
