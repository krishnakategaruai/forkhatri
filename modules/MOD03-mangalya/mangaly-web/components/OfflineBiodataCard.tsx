"use client";

import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import type { OfflineProfile } from "@/lib/agents";
import { resolveMediaUrl } from "@/lib/api";

/* [DEC-V1-033] The biodata of someone who is not on Mangaly, as a card: always
 * marked "Not on Mangaly", so a family never mistakes it for a checked member.
 * Closed, it shows the photo and two facts; open, everything the agent entered,
 * the other photos and the biodata file as received. */

export const OFFLINE_FIELDS: [string, string][] = [
  ["occupation", "occupation"],
  ["education", "education"],
  ["mother_tongue", "motherTongue"],
  ["height_cm", "height"],
  ["caste", "community"],
  ["native_place", "nativePlace"],
  ["family", "family"],
  ["rashi", "rashi"],
  ["nakshatra", "nakshatra"],
];

export default function OfflineBiodataCard({
  profile,
  open = false,
  bare = false,
}: {
  profile: OfflineProfile;
  open?: boolean;
  /** Inside another card (the family's dashboard): no border of its own. */
  bare?: boolean;
}) {
  const { t } = useTranslation(["agents"]);
  const facts = OFFLINE_FIELDS.filter(([k]) => profile.details[k] != null && profile.details[k] !== "");
  return (
    <div className={`ag-card${bare ? " ag-card--bare" : ""}`}>
      <div className="ag-card__photo">
        {profile.photo_urls[0] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={resolveMediaUrl(profile.photo_urls[0]) ?? ""} alt="" loading="lazy" decoding="async" />
        ) : (
          <Avatar name={profile.name} size={56} />
        )}
      </div>
      <div className="ag-card__body">
        <span className="ag-pill ag-pill--offline" style={{ alignSelf: "flex-start" }}>
          {t("agents:family.notOnMangaly")}
        </span>
        <span className="ag-card__title">{profile.name}</span>
        <span className="ag-card__line">
          {[profile.age != null ? t("agents:family.age", { age: profile.age }) : null, profile.city].filter(Boolean).join(" · ")}
        </span>
        {(open ? facts : facts.slice(0, 2)).length > 0 && (
          <dl className="ag-facts">
            {(open ? facts : facts.slice(0, 2)).map(([k, label]) => (
              <FactRow key={k} label={t(`agents:offline.${label}`)} value={String(profile.details[k])} />
            ))}
            {open && profile.details.about && <FactRow label={t("agents:offline.about")} value={String(profile.details.about)} />}
            {open && profile.contact_note && <FactRow label={t("agents:offline.contactNote")} value={profile.contact_note} />}
          </dl>
        )}
        {open && profile.photo_urls.length > 1 && (
          <div className="ag-gallery">
            {profile.photo_urls.slice(1).map((u) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={u} src={resolveMediaUrl(u) ?? ""} alt="" loading="lazy" />
            ))}
          </div>
        )}
        {profile.biodata_url && (
          <a className="btn btn--ghost btn--sm" style={{ alignSelf: "flex-start" }} href={resolveMediaUrl(profile.biodata_url) ?? "#"} target="_blank" rel="noreferrer">
            {t("agents:offline.viewFile")}
          </a>
        )}
      </div>
    </div>
  );
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

