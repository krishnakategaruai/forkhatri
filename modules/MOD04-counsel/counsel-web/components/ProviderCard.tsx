"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Bookmark, Clock, Languages, MapPin, MessageCircle } from "lucide-react";
import type { TFunction } from "i18next";
import { api, type Card } from "@/lib/api";
import { money, dateShort, timeShort } from "@/lib/format";
import { Avatar, Stars, VerifiedTags, useToast } from "@/components/ui";
import { BadgeRow } from "@/components/Badges";
import { useIdentity } from "@/lib/identity";
import { useState } from "react";

/** "Usually replies within …" from the consultant's median reply time (hours). */
export function replyLabel(t: TFunction, hours: number | null | undefined): string | null {
  if (hours === null || hours === undefined) return null;
  if (hours <= 1) return t("reply.hour");
  if (hours < 24) return t("reply.hours", { count: Math.ceil(hours) });
  return t("reply.days", { count: Math.ceil(hours / 24) });
}

/** "In your city" or "About 250 km away" when the viewer has chosen a city. */
export function distanceLabel(t: TFunction, km: number | null | undefined): string | null {
  if (km === null || km === undefined) return null;
  return km <= SAME_CITY_KM ? t("near.same_city") : t("near.km_away", { n: km });
}
const SAME_CITY_KM = 30;

export function ProviderCard({ c }: { c: Card }) {
  const { t, i18n } = useTranslation();
  const { me } = useIdentity();
  const toast = useToast();
  const [saved, setSaved] = useState(c.saved);
  const lang = i18n.language;
  const primary = c.expertise.find((e) => e.primary) ?? c.expertise[0];

  const toggleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!me) { toast(t("auth.signin_to_save")); return; }
    const next = !saved;
    setSaved(next);
    try { await api(`/me/saved/${c.id}`, { method: next ? "PUT" : "DELETE" }); } catch { setSaved(!next); }
  };

  return (
    <Link href={`/p/${c.id}`} className="pcard fade-in">
      <Avatar name={c.name} url={c.photo_url} size={72} />
      <div style={{ minWidth: 0 }}>
        <div className="between" style={{ alignItems: "flex-start" }}>
          <div style={{ minWidth: 0 }}>
            <div className="name">{c.name}{c.available_now && <span className="live-tag" style={{ marginLeft: 8 }}><span className="presence" data-on="true" />{t("offers.available_now")}</span>}</div>
            {primary && <div className="tiny muted">{primary.name}{primary.years ? ` · ${t("card.years", { n: primary.years })}` : ""}</div>}
          </div>
          <button className="icon-btn" onClick={toggleSave} aria-label={saved ? t("card.unsave") : t("card.save")} aria-pressed={saved}>
            <Bookmark size={18} strokeWidth={1.6} fill={saved ? "currentColor" : "none"} />
          </button>
        </div>
        <p className="headline clamp-2">{c.headline}</p>
        <div style={{ marginTop: 8 }}><VerifiedTags dims={c.verified} /></div>
        {c.badges && c.badges.length > 0 && <div style={{ marginTop: 6 }}><BadgeRow badges={c.badges} small /></div>}
        <div className="meta">
          <Stars value={c.rating} count={c.review_count} />
          {c.completed > 0 && <span>{t("card.completed_count", { count: c.completed })}</span>}
          {c.city && <span className="row" style={{ gap: 4 }}><MapPin size={12} />{c.city}{distanceLabel(t, c.distance_km) && <span> · {distanceLabel(t, c.distance_km)}</span>}</span>}
          {replyLabel(t, c.reply_hours) && <span className="row" style={{ gap: 4 }}><MessageCircle size={12} />{replyLabel(t, c.reply_hours)}</span>}
          <span className="row" style={{ gap: 4 }}><Languages size={12} />{c.languages.map((l) => t(`lang.${l}`)).join(", ")}</span>
        </div>
        {c.why && c.why.length > 0 && (
          <div className="row tiny" style={{ marginTop: 6, gap: 6 }}>
            {c.why.map((w) => <span key={w} className="tag">{t(`why.${w}`)}</span>)}
          </div>
        )}
        <div className="foot">
          <div>
            <span className="tiny muted">{t("card.from")} </span>
            <span className="price">{money(c.from_minor, c.currency, lang)}</span>
          </div>
          {c.available_now ? (
            <span className="tiny row" style={{ gap: 4, color: "var(--ok)" }}><Clock size={12} />{t("offers.start_now")}</span>
          ) : c.next_slot ? (
            <span className="tiny muted row" style={{ gap: 4 }}><Clock size={12} />{t("card.next", { when: `${dateShort(c.next_slot, lang)} ${timeShort(c.next_slot, lang)}` })}</span>
          ) : (
            <span className="tiny muted">{t("card.no_slots")}</span>
          )}
          <span className="btn btn-primary btn-sm">{t("card.book")}</span>
        </div>
      </div>
    </Link>
  );
}
