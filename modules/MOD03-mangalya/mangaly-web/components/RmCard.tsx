"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import { resolveMediaUrl } from "@/lib/api";
import { openDirect, threadHref } from "@/lib/messages";
import { formatWhen, getMyRm, type MyRm } from "@/lib/rm";

import "@/app/rm/rm.css";

/* [DEC-V1-032] The family's relationship manager, on Home. A real, named
 * person — face, name, the languages they speak — with the two things a
 * family wants at hand: message them, and see what they have put forward.
 * Renders nothing when nobody is assigned, so Home is never padded. */

export default function RmCard({ forCandidate }: { forCandidate?: string }) {
  const { t, i18n } = useTranslation(["rm"]);
  const router = useRouter();
  const [mine, setMine] = useState<MyRm | null>(null);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    let alive = true;
    getMyRm(forCandidate)
      .then((r) => alive && setMine(r))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [forCandidate]);

  if (!mine) return null;

  const { rm, suggestions, interactions } = mine;
  const nextCall = interactions
    .filter((i) => i.scheduled_at && new Date(i.scheduled_at).getTime() > Date.now())
    .sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""))[0];
  const open = suggestions.filter((s) => !s.member_decision);
  const languages = rm.languages
    .map((l) => t(`rm:language.${l.toLowerCase()}`, { defaultValue: l }))
    .join(", ");

  const message = async () => {
    setOpening(true);
    const r = await openDirect(rm.account_id);
    setOpening(false);
    if (r.ok) router.push(threadHref(r.data.conversation_id, "direct"));
  };

  return (
    <section className="section">
      <div className="section__head">
        <h3 className="h3" style={{ margin: 0 }}>
          {t("rm:card.title")}
        </h3>
        <Link className="link" href="/rm">
          {t("rm:card.seeAll")}
        </Link>
      </div>
      <div className="card rm-card">
        <div className="rm-card__who">
          <Avatar name={rm.display_name} photoUrl={resolveMediaUrl(rm.photo_url)} size={56} />
          <div className="rm-card__text">
            <span className="rm-card__name">{rm.display_name}</span>
            <span className="caption">
              {languages ? t("rm:card.speaks", { languages }) : ""}
              {rm.region ? ` · ${rm.region}` : ""}
            </span>
            {nextCall && (
              <span className="rm-card__next">
                {t(`rm:interaction.kind.${nextCall.kind}`)} · {formatWhen(nextCall.scheduled_at, i18n.language)}
              </span>
            )}
          </div>
        </div>
        <div className="rm-card__actions">
          <button type="button" className="btn btn--primary btn--sm" onClick={message} disabled={opening}>
            {t("rm:card.message")}
          </button>
          <Link className="btn btn--secondary btn--sm" href="/rm">
            {open.length > 0
              ? t("rm:card.suggestions", { count: open.length })
              : t("rm:card.log")}
          </Link>
        </div>
        {open.length > 0 && (
          <Link className="rm-card__strip" href="/rm" aria-label={t("rm:card.suggestions", { count: open.length })}>
            {open.slice(0, 5).map((s) => (
              <span key={s.id} className="rm-card__face">
                <Avatar
                  name={s.person?.open_name ?? ""}
                  photoUrl={resolveMediaUrl(s.person?.photo_url)}
                  anonymized={!s.person?.open_name}
                  size={40}
                />
              </span>
            ))}
            <span className="caption">{t("rm:card.suggestedBy")}</span>
          </Link>
        )}
      </div>
    </section>
  );
}
