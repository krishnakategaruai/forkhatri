"use client";

import { useTranslation } from "react-i18next";

import Icon from "@/components/Icon";
import { categoryPhoto, parsePlaceMessage } from "@/lib/wedding";

/* A chat message's words — or, when it is a place shared from Wedding
 * arrangements (lib/wedding `placeMessage`), a small place card: the kind of
 * place's photo, the name, what it is, and a button to open the map. The
 * message itself stays plain text, so a notification or any other screen
 * still reads it. */
export default function MessageText({ content }: { content: string }) {
  const { t, i18n } = useTranslation("wedding");
  const place = parsePlaceMessage(content);
  if (!place) return <>{content}</>;

  // The sender wrote the kind of place in their own language; find it in any.
  const label = place.detail.split(" · ")[0];
  let category: string | null = null;
  for (const lang of ["en", "hi", "te"]) {
    const labels = (i18n.getResource(lang, "wedding", "category") ?? {}) as Record<string, string>;
    const hit = Object.entries(labels).find(([, v]) => v === label);
    if (hit) {
      category = hit[0];
      break;
    }
  }
  const photo = category ? categoryPhoto(category) : null;

  return (
    <span className="msgplace">
      {photo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="msgplace__img" src={photo} alt="" loading="lazy" />
      )}
      <span className="msgplace__kicker">
        <Icon name="pin" size={16} />
        {t("wedding:chat.sharedPlace")}
      </span>
      <span className="msgplace__name">{place.name}</span>
      <span className="msgplace__detail">{place.detail}</span>
      <a className="msgplace__map" href={place.map} target="_blank" rel="noreferrer">
        {t("wedding:chat.openMap")}
      </a>
    </span>
  );
}
