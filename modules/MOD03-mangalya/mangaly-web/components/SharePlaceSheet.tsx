"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import Icon from "@/components/Icon";
import { relationKey } from "@/lib/homeCircle";
import { listContacts, type Contact } from "@/lib/messages";
import { sharePlace, type ShareTarget } from "@/lib/wedding";

/* [Owner, 2026-10-01] "keep share symbol on it, so once we click, it will go
 * to that particular person in home circle … based on our role, how it goes
 * to be planned."
 *
 * Who a place can go to depends on whose search this is and who is looking:
 *  - your own side of this match: the candidate and the Home Circle helping
 *    them (a parent sees their child and the rest of the circle; the
 *    candidate sees their parents, brothers, sisters) — one-to-one chats;
 *  - both families together — the families' chat of this match;
 *  - the match themself — only when the candidate is the one looking.
 * The other family is reached through the families' chat, never one by one.
 * Then the phone's own share (WhatsApp and the like) for anyone else. */

type Props = {
  connectionId: string;
  /** The candidate whose match this is (the viewer, or the child they help). */
  candidateId: string;
  /** True when the viewer is the candidate, not a family member. */
  viewerIsCandidate: boolean;
  matchName: string | null;
  placeName: string;
  text: string;
  onClose: () => void;
};

export default function SharePlaceSheet(props: Props) {
  const { connectionId, candidateId, viewerIsCandidate, matchName, placeName, text, onClose } = props;
  const { t, i18n } = useTranslation(["wedding", "circle", "messages"]);
  const [people, setPeople] = useState<Contact[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [sent, setSent] = useState<{ to: string; href: string } | null>(null);
  const [failed, setFailed] = useState(false);
  const canNativeShare = typeof navigator !== "undefined" && typeof navigator.share === "function";

  useEffect(() => {
    let alive = true;
    void listContacts().then((all) => {
      if (!alive) return;
      setPeople(all.filter((c) => c.mine && c.side_account_id === candidateId));
    });
    return () => {
      alive = false;
    };
  }, [candidateId]);

  async function send(key: string, to: string, target: ShareTarget) {
    setBusy(key);
    setFailed(false);
    const href = await sharePlace(target, text);
    setBusy(null);
    if (href) setSent({ to, href });
    else setFailed(true);
  }

  const first = (name: string | null | undefined) => (name ?? "").split(" ")[0];
  const who = (c: Contact) =>
    c.role === "candidate"
      ? t("wedding:share.candidate")
      : t(relationKey(c.relation, c.role)).toLocaleLowerCase(i18n.language);

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div
        className="sheet wshare"
        role="dialog"
        aria-modal="true"
        aria-labelledby="wshare-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheet__handle" aria-hidden="true" />
        <div className="sheet__head">
          <h2 id="wshare-title" className="sheet__title">
            {t("wedding:share.title")}
          </h2>
          <button type="button" className="icon-btn" aria-label={t("messages:thread.cancel")} onClick={onClose}>
            <Icon name="close" />
          </button>
        </div>
        <p className="caption wshare__place">
          <Icon name="pin" size={16} /> {placeName}
        </p>

        {sent ? (
          <div className="wshare__done" role="status">
            <p>{t("wedding:share.sent", { name: sent.to })}</p>
            <Link href={sent.href} className="btn btn--primary">
              {t("wedding:share.openChat")}
            </Link>
            <button type="button" className="btn" onClick={() => setSent(null)}>
              {t("wedding:share.more")}
            </button>
          </div>
        ) : (
          <>
            <h3 className="wedding__label">{t("wedding:share.yourSide")}</h3>
            <ul className="wshare__list">
              {people === null ? (
                <li className="caption">…</li>
              ) : people.length === 0 ? (
                <li className="caption">{t("wedding:share.noFamily")}</li>
              ) : (
                people.map((c) => (
                  <li key={c.account_id}>
                    <button
                      type="button"
                      className="wshare__row"
                      disabled={busy !== null}
                      onClick={() =>
                        send(c.account_id, first(c.display_name), { kind: "direct", accountId: c.account_id })
                      }
                    >
                      <Avatar photoUrl={c.photo_url} name={c.display_name} size={40} />
                      <span className="wshare__text">
                        <span className="wshare__name">{c.display_name}</span>
                        <span className="wshare__sub">{who(c)}</span>
                      </span>
                      <span className="wshare__go">{busy === c.account_id ? "…" : t("wedding:share.send")}</span>
                    </button>
                  </li>
                ))
              )}
            </ul>

            <h3 className="wedding__label">{t("wedding:share.together")}</h3>
            <ul className="wshare__list">
              <li>
                <button
                  type="button"
                  className="wshare__row"
                  disabled={busy !== null}
                  onClick={() => send("family", t("wedding:share.bothFamilies"), { kind: "family", connectionId })}
                >
                  <span className="wshare__icon" aria-hidden="true">
                    <Icon name="family" />
                  </span>
                  <span className="wshare__text">
                    <span className="wshare__name">{t("wedding:share.bothFamilies")}</span>
                    <span className="wshare__sub">{t("wedding:share.bothFamiliesSub")}</span>
                  </span>
                  <span className="wshare__go">{busy === "family" ? "…" : t("wedding:share.send")}</span>
                </button>
              </li>
              {viewerIsCandidate && matchName && (
                <li>
                  <button
                    type="button"
                    className="wshare__row"
                    disabled={busy !== null}
                    onClick={() => send("match", first(matchName), { kind: "candidate", connectionId })}
                  >
                    <span className="wshare__icon" aria-hidden="true">
                      <Icon name="lock" />
                    </span>
                    <span className="wshare__text">
                      <span className="wshare__name">{matchName}</span>
                      <span className="wshare__sub">{t("wedding:share.matchSub")}</span>
                    </span>
                    <span className="wshare__go">{busy === "match" ? "…" : t("wedding:share.send")}</span>
                  </button>
                </li>
              )}
            </ul>

            {canNativeShare && (
              <button
                type="button"
                className="btn wshare__native"
                onClick={() => void navigator.share({ title: placeName, text }).catch(() => undefined)}
              >
                {t("wedding:share.otherApps")}
              </button>
            )}
            {failed && (
              <p className="caption wshare__error" role="alert">
                {t("wedding:share.failed")}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
