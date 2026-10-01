"use client";

import Link from "next/link";
import { useLoaderHold } from "@/lib/useLoaderHold";
import SacredLoader from "@/components/SacredLoader";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { clockTime, formatDayDate } from "@forkhatri/chat-core";
import { ThreadBody, bubbleClassName, useComposer } from "@forkhatri/chat-ui";

import { Avatar } from "@/components/Avatar";
import { requireSession, type Session } from "@/lib/auth";
import { relationKey } from "@/lib/homeCircle";
import {
  closeConversation,
  listMessages,
  listPeople,
  openFamilyConversation,
  reportInThread,
  sendMessage,
  type ConversationKind,
  type Message,
  type ThreadPerson,
} from "@/lib/messages";
import { viewProfile } from "@/lib/profile";
import { REPORT_REASONS, block } from "@/lib/safety";
import MessageText from "@/components/MessageText";

/* FR049/FR050 · UX21 · DEC-V1-018/021/024/026 — one thread screen, three kinds.
 *
 * `candidate` (default): the two connected candidates' incognito session.
 * It is a session, not a history: leaving the thread (closing the tab,
 * switching away, going back, "End chat") deletes everything the two wrote,
 * for both, and the server also clears a session nobody has written in for
 * 30 minutes. The screen takes on a darker "incognito" mood so nobody
 * forgets which kind of chat they are in, the way Instagram's vanish mode
 * does, and says the one thing a browser cannot do: stop a screenshot.
 *
 * `direct` (`?kind=direct`, id = conversation id): an ordinary one-to-one
 * chat, kept like any messenger's (owner: "general chat for individual
 * account like Instagram / FB"). The header says how the two are linked
 * ("father of Divya").
 *
 * `family` (`?kind=family`): the optional group of both candidates and both
 * Home Circles, kept, every message labelled with its writer and their
 * relation, because in a group of two families a first name is not enough.
 *
 * Every kind refreshes while on screen, so a reply appears by itself. A
 * report stores the thread as it stands with the report (migration 044). */

const POLL_MS = 3000;

function kindOf(value: string | null): ConversationKind {
  return value === "family" ? "family" : value === "direct" ? "direct" : "candidate";
}

export default function ThreadPage() {
  // [owner 2026-09-25] The loader stays at least a second, never a flash.
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["common", "messages", "circle"]);
  const language = i18n.language || "en";

  const router = useRouter();
  const params = useParams<{ connectionId: string }>();
  const threadId = params.connectionId;
  const kind = kindOf(useSearchParams().get("kind"));
  const isFamily = kind === "family";
  const isIncognito = kind === "candidate";

  const [session, setSession] = useState<Session | null>(null);
  const [people, setPeople] = useState<ThreadPerson[]>([]);
  const [otherProfileId, setOtherProfileId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<"checking" | "ready" | "gone">("checking");
  const [panel, setPanel] = useState<null | "menu" | "report" | "block">(null);
  const [reportWho, setReportWho] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [details, setDetails] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    const rows = await listMessages(threadId, kind);
    setMessages((prev) =>
      prev.length === rows.length && prev.at(-1)?.id === rows.at(-1)?.id ? prev : rows,
    );
  }, [threadId, kind]);

  /* The incognito session ends when either person leaves it. `pagehide`
     covers closing the tab, `visibilitychange` switching apps on a phone,
     and the unmount going back inside the app. The unmount only counts once
     the thread has been open a moment, so React's development double-mount
     never wipes a conversation someone just opened. */
  useEffect(() => {
    if (!isIncognito) return;
    const openedAt = Date.now();
    const end = () => void closeConversation(threadId);
    const onHidden = () => {
      if (document.visibilityState === "hidden") end();
    };
    window.addEventListener("pagehide", end);
    document.addEventListener("visibilitychange", onHidden);
    return () => {
      window.removeEventListener("pagehide", end);
      document.removeEventListener("visibilitychange", onHidden);
      if (Date.now() - openedAt > 1500) end();
    };
  }, [threadId, isIncognito]);

  useEffect(() => {
    let active = true;
    (async () => {
      const s = await requireSession();
      if (!active || !s) return; // requireSession() has already handed off (TR16).
      setSession(s);
      const roster = await listPeople(threadId, kind);
      if (!active) return;
      if (roster.length === 0) {
        setPhase("gone");
        return;
      }
      setPeople(roster);
      const other = roster.find((p) => !p.is_me);
      if (!isFamily && other && other.role === "candidate") {
        const profile = await viewProfile(other.account_id).catch(() => null);
        if (active) setOtherProfileId(profile?.id ?? null);
      }
      await refresh();
      if (active) setPhase("ready");
    })();
    return () => {
      active = false;
    };
  }, [threadId, kind, isFamily, refresh]);

  // A reply appears on its own while the thread is on screen.
  useEffect(() => {
    if (phase !== "ready") return;
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, POLL_MS);
    return () => window.clearInterval(id);
  }, [phase, refresh]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  const composer = useComposer({
    onSend: async (text) => {
      setError(null);
      const outcome = await sendMessage(threadId, text, kind);
      if (!outcome.ok) {
        setError(
          outcome.message ??
            (outcome.status === 0
              ? t("messages:error.network")
              : t("messages:error.rateLimited")),
        );
        throw new Error("send failed");
      }
      await refresh();
    },
  });

  if (phase === "checking" || !session || loaderHold) {
    return (
      <div className="chat chat--loading">
        <SacredLoader inline />
      </div>
    );
  }
  if (phase === "gone") {
    return (
      <div className="chat chat--loading">
        <p className="caption">{t("messages:error.notAvailable")}</p>
        <Link className="link" href="/messages">
          {t("messages:title")}
        </Link>
      </div>
    );
  }

  const byId = new Map(people.map((p) => [p.account_id, p]));
  const first = (name: string | null | undefined) => (name ?? "").split(" ")[0];
  const candidates = people.filter((p) => p.role === "candidate");
  const other = people.find((p) => !p.is_me) ?? null;
  const others = people.filter((p) => !p.is_me);
  const wrote = messages.some((m) => m.kind === "member");

  /* "father of Divya": how a person sits in the families. */
  function linkOf(p: ThreadPerson | null | undefined): string {
    if (!p || p.role === "candidate") return "";
    const relation = t(relationKey(p.relation, p.role)).toLocaleLowerCase(language);
    const sideName = p.side_name ?? (p.side_account_id ? byId.get(p.side_account_id)?.display_name : null);
    return sideName ? t("messages:thread.relationOf", { relation, name: first(sideName) }) : relation;
  }
  const whoIs = (p: ThreadPerson | undefined) =>
    p ? [first(p.display_name), linkOf(p)].filter(Boolean).join(" · ") : "";

  const otherCandidate = candidates.find((p) => p.account_id !== session?.account_id);
  const iAmCandidate = candidates.some((p) => p.account_id === session?.account_id);
  const title = isFamily
    ? iAmCandidate && otherCandidate
      ? t("messages:thread.familyWithYou", { name: first(otherCandidate.display_name) })
      : t("messages:thread.familyTitle", {
          a: first(candidates[0]?.display_name),
          b: first(candidates[1]?.display_name),
        })
    : (other?.display_name ?? t("messages:title"));
  const subtitle = isFamily
    ? t("messages:thread.familySubtitle", { count: people.length })
    : isIncognito
      ? t("messages:thread.incognitoSub")
      : linkOf(other) || t("messages:list.candidate");

  const reportTarget = reportWho ? byId.get(reportWho) : null;

  async function sendReport() {
    if (!reportWho || !reason) return;
    const outcome = await reportInThread(threadId, kind, reportWho, reason, details);
    if (outcome.ok) {
      setNotice(t("messages:thread.reportSent"));
      setPanel(null);
      setReason(null);
      setDetails("");
    } else {
      setError(outcome.message ?? t("messages:error.network"));
    }
  }

  const starters = [
    t("messages:thread.starter1"),
    t("messages:thread.starter2", { name: first(other?.display_name) }),
    t("messages:thread.starter3"),
  ];

  return (
    <div className={`chat chat--${kind}`}>
      <header className="chat__head">
        <button
          className="icon-btn chat__back"
          onClick={() => router.push("/messages")}
          aria-label={t("common:action.back")}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" /></svg>
        </button>
        <div className="chat__who">
          {isFamily ? (
            <span className="chat__faces">
              {/* Others only — you are not shown to yourself. */}
              {people
                .filter((p) => p.account_id !== session?.account_id)
                .slice(0, 3)
                .map((p) => (
                  <Avatar key={p.account_id} photoUrl={p.photo_url} name={p.display_name} size={34} />
                ))}
            </span>
          ) : other?.role === "candidate" && !isIncognito ? (
            <Link href={`/profile/${other.account_id}`} className="chat__avatar-link">
              <Avatar photoUrl={other.photo_url} name={other.display_name} size={40} />
            </Link>
          ) : (
            <span className="chat__avatar">
              <Avatar photoUrl={other?.photo_url} name={other?.display_name} size={40} />
              {isIncognito && (
                <span className="chat__lock" aria-hidden="true">
                  <svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
                </span>
              )}
            </span>
          )}
          <span className="chat__text">
            <span className="chat__name">{title}</span>
            <span className="chat__sub">{subtitle}</span>
          </span>
        </div>
        <button
          type="button"
          className="icon-btn chat__more"
          aria-label={t("messages:thread.more")}
          aria-expanded={panel === "menu"}
          onClick={() => setPanel(panel === "menu" ? null : "menu")}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="19" cy="12" r="1.6" /></svg>
        </button>

        {panel === "menu" && (
          <div className="chat-menu" role="menu">
            {isIncognito && (
              <button
                type="button"
                role="menuitem"
                className="chat-menu__item"
                onClick={async () => {
                  await openFamilyConversation(threadId);
                  router.push(`/messages/${threadId}?kind=family`);
                }}
              >
                <strong>{t("messages:thread.bringFamilies")}</strong>
                <span>{t("messages:thread.bringFamiliesHint")}</span>
              </button>
            )}
            {!isFamily && other?.role === "candidate" && (
              <Link role="menuitem" className="chat-menu__item" href={`/profile/${other.account_id}`}>
                <strong>{t("messages:thread.viewProfile")}</strong>
              </Link>
            )}
            <button
              type="button"
              role="menuitem"
              className="chat-menu__item"
              onClick={() => {
                setReportWho(isFamily ? null : (other?.account_id ?? null));
                setPanel("report");
              }}
            >
              <strong>{t("messages:thread.report")}</strong>
            </button>
            {!isFamily && otherProfileId && (
              <button
                type="button"
                role="menuitem"
                className="chat-menu__item chat-menu__item--danger"
                onClick={() => setPanel("block")}
              >
                <strong>{t("messages:thread.block")}</strong>
              </button>
            )}
            {isIncognito && (
              <button
                type="button"
                role="menuitem"
                className="chat-menu__item chat-menu__item--danger"
                onClick={async () => {
                  await closeConversation(threadId);
                  router.push("/messages");
                }}
              >
                <strong>{t("messages:thread.endSession")}</strong>
                <span>{t("messages:thread.endSessionHint")}</span>
              </button>
            )}
          </div>
        )}
      </header>

      <div className="chat__scroll">
        {panel === "block" && other && otherProfileId && (
          <div className="chat-panel">
            <p style={{ margin: 0 }}>
              {t("messages:thread.blockConfirm", { name: first(other.display_name) })}
            </p>
            <div className="chat-panel__actions">
              <button type="button" className="btn" onClick={() => setPanel(null)}>
                {t("messages:thread.cancel")}
              </button>
              <button
                type="button"
                className="btn btn--danger"
                onClick={async () => {
                  await block(otherProfileId);
                  if (isIncognito) await closeConversation(threadId);
                  router.push("/messages");
                }}
              >
                {t("messages:thread.blockYes")}
              </button>
            </div>
          </div>
        )}

        {panel === "report" && (
          <div className="chat-panel">
            {isFamily && (
              <>
                <p className="chat-panel__label">{t("messages:thread.reportWho")}</p>
                <div className="chip-row">
                  {others.map((p) => (
                    <button
                      key={p.account_id}
                      type="button"
                      className={`quick-pick__chip${reportWho === p.account_id ? " is-on" : ""}`}
                      aria-pressed={reportWho === p.account_id}
                      onClick={() => setReportWho(p.account_id)}
                    >
                      {whoIs(p)}
                    </button>
                  ))}
                </div>
              </>
            )}
            {reportTarget && (
              <>
                <p className="chat-panel__label">
                  {t("messages:thread.reportTitle", { name: first(reportTarget.display_name) })}
                </p>
                <div className="chip-row">
                  {REPORT_REASONS.map((r) => (
                    <button
                      key={r}
                      type="button"
                      className={`quick-pick__chip${reason === r ? " is-on" : ""}`}
                      aria-pressed={reason === r}
                      onClick={() => setReason(r)}
                    >
                      {t(`messages:reason.${r}`)}
                    </button>
                  ))}
                </div>
                <div className="field__box">
                  <textarea
                    className="field__input"
                    rows={2}
                    placeholder={t("messages:thread.reportDetails")}
                    value={details}
                    onChange={(e) => setDetails(e.target.value)}
                  />
                </div>
                <p className="caption" style={{ margin: 0 }}>
                  {t("messages:thread.reportNote", { name: first(reportTarget.display_name) })}
                </p>
              </>
            )}
            <div className="chat-panel__actions">
              <button type="button" className="btn" onClick={() => setPanel(null)}>
                {t("messages:thread.cancel")}
              </button>
              <button
                type="button"
                className="btn btn--primary"
                disabled={!reportTarget || !reason}
                onClick={sendReport}
              >
                {t("messages:thread.reportSend")}
              </button>
            </div>
          </div>
        )}

        {notice && (
          <p className="chat-notice" role="status">
            {notice}
          </p>
        )}

        {/* Who is in this chat, and what happens to it, said once at the top
            the way a messenger opens a new thread. */}
        <div className="chat__intro">
          {isFamily ? (
            <span className="chat__faces chat__faces--lg">
              {people
                .filter((p) => p.account_id !== session?.account_id)
                .slice(0, 6)
                .map((p) => (
                  <Avatar key={p.account_id} photoUrl={p.photo_url} name={p.display_name} size={44} />
                ))}
            </span>
          ) : (
            <Avatar photoUrl={other?.photo_url} name={other?.display_name} size={72} />
          )}
          <p className="chat__intro-name">{title}</p>
          <p className="chat__intro-note">
            {isFamily
              ? t("messages:thread.familyNote")
              : isIncognito
                ? t("messages:thread.sessionNote")
                : t("messages:thread.directNote")}
          </p>
        </div>

        {messages.length > 0 && (
          <ThreadBody
            className="chat__body"
            dayClassName="chat__day"
            messages={messages}
            read={(m) => ({
              id: m.id,
              // A system line has no sender and never merges with a neighbour.
              senderId: m.sender_account_id ?? "system",
              sentAt: m.sent_at,
              kind: m.kind,
            })}
            dayLabels={{
              today: t("messages:thread.today"),
              yesterday: t("messages:thread.yesterday"),
              date: (isoDate) => formatDayDate(isoDate, language),
            }}
          >
            {({ message: m, joinsAbove, joinsBelow }) => {
              if (m.kind === "system") {
                return (
                  <p className="chat__system" role="status">
                    {t(`messages:${m.content}`)}
                  </p>
                );
              }
              const mine = m.sender_account_id === session.account_id;
              const sender = m.sender_account_id ? byId.get(m.sender_account_id) : undefined;
              const sideA = sender?.side_account_id === candidates[0]?.account_id;
              return (
                <div className={`msg${mine ? " msg--mine" : ""}${joinsBelow ? "" : " msg--last"}`}>
                  {isFamily && !mine && (
                    <span className="msg__face" aria-hidden="true">
                      {!joinsBelow && (
                        <Avatar photoUrl={sender?.photo_url} name={sender?.display_name} size={28} />
                      )}
                    </span>
                  )}
                  <div className="msg__stack">
                    {isFamily && !mine && !joinsAbove && (
                      <span className={`msg__who${sideA ? " msg__who--a" : " msg__who--b"}`}>
                        {whoIs(sender) || m.sender_name}
                      </span>
                    )}
                    <div
                      className={bubbleClassName(
                        { joinsAbove, joinsBelow },
                        {
                          base: "msg__bubble",
                          mine: "msg__bubble--mine",
                          joinedAbove: "is-joined-above",
                          joinedBelow: "is-joined-below",
                          isMine: mine,
                        },
                      )}
                    >
                      <MessageText content={m.content} />
                    </div>
                    {!joinsBelow && (
                      <span className="msg__time">{clockTime(m.sent_at, language)}</span>
                    )}
                  </div>
                </div>
              );
            }}
          </ThreadBody>
        )}

        {!wrote && !isFamily && (
          <div className="chat__starters">
            {starters.map((s) => (
              <button key={s} type="button" className="chat__starter" onClick={() => composer.setValue(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat__compose" onSubmit={composer.submit}>
        {error && <p className="chat__error">{error}</p>}
        <div className="chat__field">
          <input
            className="chat__input"
            placeholder={
              isIncognito ? t("messages:thread.placeholderIncognito") : t("messages:thread.placeholder")
            }
            value={composer.value}
            onChange={(e) => composer.setValue(e.target.value)}
            onKeyDown={composer.onKeyDown}
            disabled={composer.sending}
            aria-label={t("messages:thread.placeholder")}
          />
          <button className="chat__send" disabled={!composer.canSend} aria-label={t("messages:thread.send")}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12l16-8-6 16-2.5-6.5L4 12z" /></svg>
          </button>
        </div>
      </form>
    </div>
  );
}
