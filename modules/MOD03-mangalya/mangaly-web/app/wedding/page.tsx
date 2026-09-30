"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import { Avatar } from "@/components/Avatar";
import ContextChip from "@/components/ContextChip";
import Icon from "@/components/Icon";
import MotionTitle from "@/components/MotionTitle";
import SacredLoader from "@/components/SacredLoader";
import { useActiveContext } from "@/lib/activeContext";
import { requireSession } from "@/lib/auth";
import { listConversations, type ConversationSummary } from "@/lib/messages";
import { getStages, type StageInfo } from "@/lib/wedding";

import "./wedding.css";

/* Wedding arrangements (owner, 2026-10-01; migration 062). Every accepted
 * match — a connection with a conversation — with the stage the two
 * families have reached. Nothing here before a match: the page says plainly
 * that it opens once a family accepts. */

type Row = { connectionId: string; name: string | null; photo: string | null; stage: StageInfo | null };

export default function WeddingPage() {
  const { t } = useTranslation(["wedding", "common"]);
  const { contexts, active, choose, loaded } = useActiveContext();
  const forId = active?.kind === "family" ? active.circle.candidate_account_id : undefined;
  const [rows, setRows] = useState<Row[] | null>(null);

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      if (!(await requireSession()) || !alive) return;
      const conversations = await listConversations(forId);
      // One row per match: the candidates' chat and the families' chat share a connection.
      const byConnection = new Map<string, ConversationSummary>();
      for (const c of conversations) {
        if (c.kind === "direct" || byConnection.has(c.connection_id)) continue;
        byConnection.set(c.connection_id, c);
      }
      const stages = await getStages([...byConnection.keys()], forId);
      const stageOf = new Map(stages.map((s) => [s.connection_id, s]));
      if (!alive) return;
      setRows(
        [...byConnection.values()]
          // Only matches the service confirms are accepted and ours.
          .filter((c) => stageOf.has(c.connection_id))
          .map((c) => ({
            connectionId: c.connection_id,
            name: c.other_name,
            photo: c.other_photo_url,
            stage: stageOf.get(c.connection_id) ?? null,
          })),
      );
    })();
    return () => {
      alive = false;
    };
  }, [loaded, forId]);

  return (
    <>
      <header className="topbar">
        <MotionTitle as="h1" className="royal-title" text={t("wedding:title")} />
        <div className="topbar__actions">
          <AccountButton />
        </div>
      </header>
      {contexts && active && (
        <div className="page-context">
          <ContextChip contexts={contexts} active={active} onChoose={choose} />
        </div>
      )}
      <main className="screen wedding">
        {rows === null ? (
          <SacredLoader />
        ) : rows.length === 0 ? (
          <section className="wedding__empty">
            <Icon name="wedding" size={40} />
            <h2 className="h3">{t("wedding:empty.title")}</h2>
            <p className="caption">{t("wedding:empty.body")}</p>
            <Link href="/discover" className="btn btn--primary">
              {t("wedding:empty.cta")}
            </Link>
          </section>
        ) : (
          <>
            <p className="caption wedding__intro">{t("wedding:intro")}</p>
            <ul className="wedding__matches">
              {rows.map((r) => (
                <li key={r.connectionId}>
                  <Link href={`/wedding/${r.connectionId}`} className="wmatch">
                    <Avatar photoUrl={r.photo} name={r.name} size={56} />
                    <span className="wmatch__text">
                      <span className="wmatch__name">{t("wedding:with", { name: r.name ?? "" })}</span>
                      {r.stage && (
                        <span className="wmatch__stage">{t(`wedding:stage.${r.stage.stage}`)}</span>
                      )}
                    </span>
                    <Icon name="caretRight" />
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </main>
    </>
  );
}
