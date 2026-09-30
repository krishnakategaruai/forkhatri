"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import MotionTitle from "@/components/MotionTitle";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { conversationTime } from "@forkhatri/chat-core";

import AccountButton from "@/components/AccountButton";
import { Avatar } from "@/components/Avatar";
import { requireSession, type Session } from "@/lib/auth";
import { relationKey } from "@/lib/homeCircle";
import {
  listContacts,
  listConversations,
  openDirect,
  threadHref,
  type Contact,
  type ConversationSummary,
} from "@/lib/messages";

/* DEC-V1-026 — the inbox, as every messenger has taught people to read one.
 *
 * One list, newest first: one-to-one chats (kept, like Instagram or
 * Facebook), the two candidates' incognito session (marked with a lock), and
 * the optional families' group (marked with its group of faces). Each row
 * answers who, what was said last and by whom, and when. "New message"
 * opens the people you may write to in place, grouped by family, because in
 * Mangalya a chat always rests on a real link: your own family, or the other
 * family of a connection. */

const REFRESH_MS = 8000;

export default function ConversationList({
  activeId,
  activeKind = "candidate",
}: {
  activeId: string | null;
  activeKind?: string;
}) {
  const { t, i18n } = useTranslation(["common", "messages", "circle"]);
  const language = i18n.language || "en";
  const router = useRouter();

  const [session, setSession] = useState<Session | null>(null);
  const [rows, setRows] = useState<ConversationSummary[] | null>(null);
  const [picking, setPicking] = useState(false);
  const [contacts, setContacts] = useState<Contact[] | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      const list = await listConversations();
      if (active) setRows(list);
    };
    (async () => {
      const s = await requireSession();
      if (!active || !s) return;
      setSession(s);
      await load();
    })();
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") void load();
    }, REFRESH_MS);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [activeId]);

  useEffect(() => {
    if (!picking || contacts) return;
    void listContacts().then(setContacts);
  }, [picking, contacts]);

  function listTime(value: string): string {
    const stamp = conversationTime(value, language);
    return stamp.kind === "yesterday" ? t("messages:thread.yesterday") : stamp.text;
  }
  const first = (name: string | null | undefined) => (name ?? "").split(" ")[0];

  /* "father of Divya", or "Your mother" style: how this person is linked. */
  function linkOf(c: { role: string; relation?: string | null; side_name?: string | null }): string {
    if (c.role === "candidate") return t("messages:list.candidate");
    const relation = t(relationKey(c.relation, c.role)).toLocaleLowerCase(language);
    return c.side_name
      ? t("messages:thread.relationOf", { relation, name: first(c.side_name) })
      : relation;
  }

  const groups = useMemo(() => {
    const q = query.trim().toLocaleLowerCase(language);
    const matchQ = (c: Contact) => !q || (c.display_name ?? "").toLocaleLowerCase(language).includes(q);
    const map = new Map<string, { title: string; mine: boolean; people: Contact[] }>();
    for (const c of (contacts ?? []).filter(matchQ)) {
      const key = c.mine ? "mine" : (c.side_account_id ?? "other");
      if (!map.has(key)) {
        map.set(key, {
          title: c.mine
            ? t("messages:list.yourFamily")
            : t("messages:list.familyOf", { name: first(c.side_name) }),
          mine: c.mine,
          people: [],
        });
      }
      map.get(key)!.people.push(c);
    }
    return [...map.values()].sort((a, b) => Number(b.mine) - Number(a.mine));
  }, [contacts, query, language, t]);

  async function startWith(accountId: string) {
    const outcome = await openDirect(accountId);
    if (outcome.ok && outcome.data) {
      setPicking(false);
      router.push(`/messages/${outcome.data.conversation_id}?kind=direct`);
    }
  }

  return (
    <div className="inbox">
      <header className="inbox__head">
        <MotionTitle as="h1" className="inbox__title royal-title" text={t("messages:title")} />
        {/* One compose action: the pencil once there are conversations; an
            empty inbox offers it as the empty state's own button instead. */}
        {(picking || (rows !== null && rows.length > 0)) && (
        <button
          type="button"
          className={`inbox__new${picking ? " is-on" : ""}`}
          aria-expanded={picking}
          onClick={() => setPicking((p) => !p)}
          aria-label={picking ? t("messages:thread.cancel") : t("messages:list.newMessage")}
          title={t("messages:list.newMessage")}
        >
          {picking ? (
            <Icon name="close" />
          ) : (
            <Icon name="compose" />
          )}
        </button>
        )}
        <div className="inbox__account">
          <AccountButton />
        </div>
      </header>

      {picking ? (
        <div className="picker">
          {/* Nobody can be messaged yet: say why and offer the one step
              that changes it, instead of a search box that finds no one. */}
          {contacts !== null && contacts.length === 0 ? (
            <div className="picker__none">
              <p className="caption">{t("messages:list.noContacts")}</p>
              <Link className="btn btn--primary" href="/circle">
                {t("messages:list.inviteFamily")}
              </Link>
            </div>
          ) : (
          <>
          <label className="picker__search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="M20 20l-4-4" /></svg>
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("messages:list.searchPeople")}
              aria-label={t("messages:list.searchPeople")}
            />
          </label>
          {contacts === null ? (
            <p className="caption inbox__hint">{t("common:state.loading")}</p>
          ) : groups.length === 0 ? (
            <p className="caption inbox__hint">{t("messages:list.noContacts")}</p>
          ) : (
            groups.map((g) => (
              <section key={g.title} className="picker__group">
                <h2 className="picker__title">{g.title}</h2>
                <ul className="picker__list">
                  {g.people.map((c) => (
                    <li key={c.account_id}>
                      <button type="button" className="picker__person" onClick={() => startWith(c.account_id)}>
                        <Avatar photoUrl={c.photo_url} name={c.display_name} size={44} />
                        <span className="picker__text">
                          <span className="picker__name">{c.display_name}</span>
                          <span className="picker__link">{linkOf(c)}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ))
          )}
          <p className="caption inbox__hint">{t("messages:list.whoCanNote")}</p>
          </>
          )}
        </div>
      ) : rows === null ? (
        <ul className="inbox__list" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <li key={i} className="convo convo--skeleton">
              <span className="sk sk--round" />
              <span className="convo__body"><span className="sk sk--line" /><span className="sk sk--line sk--short" /></span>
            </li>
          ))}
        </ul>
      ) : rows.length === 0 ? (
        <div className="inbox__empty">
          <span className="inbox__empty-mark" aria-hidden="true">
            <Icon name="chats" size={40} />
          </span>
          <p className="inbox__empty-title">{t("messages:list.emptyTitle")}</p>
          <p className="caption">{t("messages:list.emptyBody")}</p>
          <button type="button" className="btn btn--primary" onClick={() => setPicking(true)}>
            {t("messages:list.newMessage")}
          </button>
        </div>
      ) : (
        <ul className="inbox__list">
          {rows.map((c) => {
            const unread = c.unread_count ?? 0;
            const family = c.kind === "family";
            const pair = (c.participants ?? []).filter((p) => p.role === "candidate");
            const other = (c.participants ?? []).find((p) => p.account_id === c.other_account_id);
            const last = typeof c.last_message === "string" ? null : c.last_message;
            const text =
              typeof c.last_message === "string"
                ? c.last_message
                : last?.kind === "system"
                  ? t(`messages:${last.content}`)
                  : (last?.content ?? null);
            const mineLast = !!last && !!session && last.sender_account_id === session.account_id;
            const byLine =
              family && last && last.kind !== "system" && !mineLast && last.sender_name
                ? `${first(last.sender_name)}: `
                : mineLast
                  ? t("messages:list.you")
                  : "";
            // Seen by one of the two candidates, the families' chat is named
            // from their side: "Varun's family & yours", with his face.
            const otherCandidate = pair.find((p) => p.account_id !== session?.account_id);
            const iAmCandidate = pair.some((p) => p.account_id === session?.account_id);
            const name = family
              ? iAmCandidate && otherCandidate
                ? t("messages:thread.familyWithYou", { name: first(otherCandidate.display_name) })
                : t("messages:thread.familyTitle", { a: first(pair[0]?.display_name), b: first(pair[1]?.display_name) })
              : (c.other_name ?? other?.display_name ?? t("messages:title"));
            const id = c.kind === "direct" ? (c.conversation_id ?? c.connection_id) : c.connection_id;
            return (
              <li key={`${c.kind}:${id}`}>
                <Link
                  href={threadHref(id, c.kind)}
                  className={`convo${unread > 0 ? " is-unread" : ""}`}
                  aria-current={activeId === id && activeKind === c.kind ? "true" : undefined}
                >
                  {family ? (
                    <span className="convo__faces" aria-hidden="true">
                      {(iAmCandidate && otherCandidate ? [otherCandidate] : pair.slice(0, 2)).map((p) => (
                        <Avatar key={p.account_id} photoUrl={p.photo_url} name={p.display_name} size={36} />
                      ))}
                    </span>
                  ) : (
                    <span className="convo__avatar">
                      <Avatar photoUrl={c.other_photo_url ?? other?.photo_url} name={name} size={52} />
                      {c.kind === "candidate" && (
                        <span className="convo__lock" title={t("messages:kind.candidate")}>
                          <Icon name="lock" size={16} />
                        </span>
                      )}
                    </span>
                  )}
                  <span className="convo__body">
                    <span className="convo__top">
                      <span className="convo__name">{name}</span>
                      {c.last_message_at && <span className="convo__time">{listTime(c.last_message_at)}</span>}
                    </span>
                    <span className="convo__bottom">
                      <span className="convo__preview">
                        {c.kind !== "direct" && (
                          <span className={`convo__kind convo__kind--${c.kind}`}>{t(`messages:kind.${c.kind}`)}</span>
                        )}
                        {byLine}
                        {text ?? t("messages:thread.empty")}
                      </span>
                      {unread > 0 && (
                        <span className="convo__badge" aria-label={String(unread)}>
                          {unread}
                        </span>
                      )}
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
