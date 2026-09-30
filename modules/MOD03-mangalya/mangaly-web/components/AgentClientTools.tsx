"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import ContactReveal from "@/components/ContactReveal";
import OfflineBiodataCard from "@/components/OfflineBiodataCard";
import {
  STAGES,
  getMyAgentRecord,
  listClients,
  listOffline,
  setStage,
  share,
  sharedWithClient,
  type OfflineProfile,
  type Shared,
  type Stage,
} from "@/lib/agents";

/* [DEC-V1-033] What an agent adds to a family's desk on the RM console: the
 * family's stage, their numbers (each look written down for them), a
 * printable biodata, and sharing biodata of people not on Mangalya — plus the
 * family's answers and questions on everything shared. Mangalya profiles are
 * searched and shared with the console's own search, as Mangalya's RMs do.
 * Renders nothing for Mangalya's own relationship managers. */

export default function AgentClientTools({
  assignmentId,
  memberAccountId,
  memberName,
}: {
  assignmentId: string;
  memberAccountId: string;
  memberName: string;
}) {
  const { t } = useTranslation(["agents", "common"]);
  const [isAgent, setIsAgent] = useState(false);
  const [stage, setStageValue] = useState<Stage | null>(null);
  const [offline, setOffline] = useState<OfflineProfile[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [note, setNote] = useState("");
  const [shared, setShared] = useState<Shared[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reloadShared = useCallback(async () => {
    setShared((await sharedWithClient(assignmentId)) ?? []);
  }, [assignmentId]);

  useEffect(() => {
    let alive = true;
    getMyAgentRecord().then(async (r) => {
      if (!alive || !r || r.kind !== "agent" || !r.live) return;
      setIsAgent(true);
      const [clients, off] = await Promise.all([listClients(), listOffline()]);
      if (!alive) return;
      setStageValue(clients?.find((c) => c.assignment_id === assignmentId)?.stage ?? "searching");
      setOffline(off ?? []);
      await reloadShared();
    });
    return () => {
      alive = false;
    };
  }, [assignmentId, reloadShared]);

  if (!isAgent) return null;

  const first = memberName.split(" ")[0];
  const alreadyOffline = new Set(shared.map((s) => s.offline?.id).filter(Boolean));
  const offlineShared = shared.filter((s) => s.offline);
  const answered = shared.filter((s) => s.decision);

  const shareOffline = async () => {
    if (picked.size === 0) {
      setResult(t("agents:share.choose"));
      return;
    }
    setBusy(true);
    const out = await share({ assignment_ids: [assignmentId], offline_ids: [...picked], note: note.trim() || null });
    setBusy(false);
    if (out.ok) {
      setResult(out.data.shared ? t("agents:share.sent", { count: out.data.shared }) : t("agents:share.none"));
      setPicked(new Set());
      setNote("");
      await reloadShared();
    } else {
      setResult(out.message ?? null);
    }
  };

  return (
    <section className="section card ag-form" style={{ background: "var(--family-tint)" }}>
      <div className="ag-bar">
        <h3 className="h3" style={{ margin: 0 }}>
          {t("agents:tools.title")}
        </h3>
        <div className="ag-row">
          <select
            className="input"
            style={{ width: "auto" }}
            value={stage ?? "searching"}
            onChange={async (e) => {
              const next = e.target.value as Stage;
              setStageValue(next);
              await setStage(assignmentId, next);
            }}
            aria-label={t("agents:stage.label")}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {t(`agents:stage.${s}`)}
              </option>
            ))}
          </select>
          <Link className="btn btn--secondary btn--sm" href={`/agent/biodata?ids=${memberAccountId}`} prefetch={false}>
            {t("agents:tools.exportOne")}
          </Link>
        </div>
      </div>
      <ContactReveal memberAccountId={memberAccountId} isClient />

      {/* ---- the family's answers ---- */}
      <div className="ag-head">
        <span className="label">{t("agents:tools.answers")}</span>
        {answered.length === 0 ? (
          <span className="caption">{t("agents:tools.noAnswers")}</span>
        ) : (
          <ul className="ag-activity">
            {answered.map((s) => (
              <li key={s.suggestion_id}>
                <span>
                  <strong>{s.offline?.name ?? s.person?.open_name ?? s.person?.locality ?? ""}</strong>
                  {" · "}
                  {s.decision === "ask"
                    ? t("agents:tools.question", { question: s.question ?? "" })
                    : t(`agents:family.answer.${s.decision}`)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ---- share biodata of people not on Mangalya ---- */}
      <div className="ag-head">
        <span className="label">{t("agents:share.offlineTitle")}</span>
        {offline.length === 0 ? (
          <span className="caption">
            {t("agents:share.offlineEmpty")}{" "}
            <Link href="/agent?tab=offline">{t("agents:tabs.offline")}</Link>
          </span>
        ) : (
          <>
            <ul className="ag-offline-list">
              {offline.map((o) => {
                const done = alreadyOffline.has(o.id);
                return (
                  <li key={o.id} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <OfflineBiodataCard profile={o} />
                    {done ? (
                      <span className="ag-ok">{t("agents:share.none")}</span>
                    ) : (
                      <label className="ag-consent">
                        <input
                          type="checkbox"
                          checked={picked.has(o.id)}
                          onChange={() =>
                            setPicked((prev) => {
                              const next = new Set(prev);
                              if (next.has(o.id)) next.delete(o.id);
                              else next.add(o.id);
                              return next;
                            })
                          }
                        />
                        {t("agents:share.title", { name: first })}
                      </label>
                    )}
                  </li>
                );
              })}
            </ul>
            <label className="field">
              <span className="label">{t("agents:share.note")}</span>
              <textarea
                className="textarea"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={1000}
                placeholder={t("agents:share.notePlaceholder")}
              />
            </label>
            <div className="ag-row">
              <button type="button" className="btn btn--primary btn--sm" disabled={busy} onClick={shareOffline}>
                {t("agents:share.send")}
              </button>
              {result && <span className="caption">{result}</span>}
            </div>
          </>
        )}
        {offlineShared.length > 0 && (
          <span className="caption">{t("agents:clients.shared", { count: offlineShared.length })}</span>
        )}
      </div>
    </section>
  );
}
