"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import Icon from "@/components/Icon";
import SacredLoader from "@/components/SacredLoader";
import SharePlaceSheet from "@/components/SharePlaceSheet";
import { useActiveContext } from "@/lib/activeContext";
import { requireSession } from "@/lib/auth";
import { listConversations } from "@/lib/messages";
import {
  STAGES,
  getStages,
  getSuggestions,
  PHOTO_CREDITS,
  categoryPhoto,
  mapLink,
  placeMessage,
  setStage,
  type Stage,
  type StageInfo,
  type Suggestions,
} from "@/lib/wedding";

import "../wedding.css";

/* One match's arrangements: the stage both families share, the kinds of
 * place that help at that stage, and places near them — Mangalya partner
 * offers first and always marked, then OpenStreetMap places nearest first,
 * with how the list is ordered said in plain words under it. */

export default function WeddingPlanPage() {
  const { connectionId } = useParams<{ connectionId: string }>();
  const router = useRouter();
  const { t, i18n } = useTranslation(["wedding", "common"]);
  const { active, loaded } = useActiveContext();
  const forId =
    active?.kind === "family" ? active.circle.candidate_account_id : undefined;

  const [name, setName] = useState<string | null>(null);
  const [stage, setStageInfo] = useState<StageInfo | null | "missing">(null);
  const [category, setCategory] = useState<string | null>(null);
  const [near, setNear] = useState<string | undefined>(undefined);
  // Keyed by what was asked for, so a new category shows the loader until
  // its own answer arrives (never the previous category's places).
  const [loadedData, setLoadedData] = useState<{
    key: string;
    value: Suggestions | "error";
  } | null>(null);
  const [saving, setSaving] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sharing, setSharing] = useState<{ name: string; text: string } | null>(
    null,
  );

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      const session = await requireSession();
      if (!session || !alive) return;
      setSessionId(session.account_id);
      const [stages, conversations] = await Promise.all([
        getStages([connectionId], forId),
        listConversations(forId),
      ]);
      if (!alive) return;
      const s = stages[0];
      setStageInfo(s ?? "missing");
      setName(
        conversations.find((c) => c.connection_id === connectionId)
          ?.other_name ?? null,
      );
      if (s) setCategory(s.categories[0] ?? null);
    })();
    return () => {
      alive = false;
    };
  }, [loaded, forId, connectionId]);

  useEffect(() => {
    if (!category) return;
    let alive = true;
    const key = `${category}|${near ?? ""}`;
    void getSuggestions(connectionId, category, near, forId).then((d) => {
      if (alive) setLoadedData({ key, value: d ?? "error" });
    });
    return () => {
      alive = false;
    };
  }, [connectionId, category, near, forId]);

  async function moveTo(next: Stage) {
    if (stage === null || stage === "missing" || stage.stage === next || saving)
      return;
    setSaving(true);
    const outcome = await setStage(connectionId, next, forId);
    setSaving(false);
    if (outcome.ok && outcome.data) {
      setStageInfo(outcome.data);
      setCategory(outcome.data.categories[0] ?? null);
    }
  }

  const header = (
    <header className="topbar topbar--wrap">
      <button
        type="button"
        className="icon-btn"
        onClick={() => router.back()}
        aria-label={t("common:action.back")}
      >
        <Icon name="back" />
      </button>
      <h1>{name ? t("wedding:with", { name }) : t("wedding:title")}</h1>
      <span style={{ width: 44 }} aria-hidden="true" />
    </header>
  );

  if (stage === null) {
    return (
      <>
        {header}
        <main className="screen wedding">
          <SacredLoader />
        </main>
      </>
    );
  }
  if (stage === "missing") {
    return (
      <>
        {header}
        <main className="screen wedding">
          <p className="caption">{t("wedding:notAvailable")}</p>
        </main>
      </>
    );
  }

  const dataKey = `${category}|${near ?? ""}`;
  const data =
    loadedData && loadedData.key === dataKey ? loadedData.value : null;
  const centreLabel =
    data && data !== "error" ? (data.centre?.label ?? "") : "";
  function openShare(placeName: string, km: number, lat: number, lon: number) {
    // Written in the sender's language; it reads as a normal message anywhere.
    const detail = [
      t(`wedding:category.${category}`),
      t("wedding:places.km", { km }),
      centreLabel,
    ]
      .filter(Boolean)
      .join(" · ");
    setSharing({
      name: placeName,
      text: placeMessage(placeName, detail, lat, lon),
    });
  }
  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(i18n.language, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });

  return (
    <>
      {header}
      <main className="screen wedding">
        <section className="wstage" aria-labelledby="wstage-title">
          <h2 id="wstage-title" className="wedding__label">
            {t("wedding:stageTitle")}
          </h2>
          <ol className="wstage__steps">
            {STAGES.map((s, i) => {
              const at = STAGES.indexOf(stage.stage);
              return (
                <li key={s}>
                  <button
                    type="button"
                    className={`wstage__step${s === stage.stage ? " is-current" : ""}${i < at ? " is-done" : ""}`}
                    aria-pressed={s === stage.stage}
                    disabled={saving}
                    onClick={() => moveTo(s)}
                  >
                    <span className="wstage__dot" aria-hidden="true">
                      {i + 1}
                    </span>
                    <span>{t(`wedding:stage.${s}`)}</span>
                  </button>
                </li>
              );
            })}
          </ol>
          <p className="wstage__hint">
            {t(`wedding:stageHint.${stage.stage}`)}
          </p>
          <p className="caption wstage__shared">{t("wedding:stageShared")}</p>
          {stage.stage === "first_meeting" && (
            <Link href="/guides/the-first-meeting" className="wedding__guide">
              <Icon name="guides" size={16} />
              {t("wedding:guide")}
            </Link>
          )}
        </section>

        <div className="wcats" role="tablist">
          {stage.categories.map((c) => (
            <button
              key={c}
              type="button"
              role="tab"
              aria-selected={c === category}
              className={`quick-pick__chip${c === category ? " is-on" : ""}`}
              onClick={() => setCategory(c)}
            >
              {t(`wedding:category.${c}`)}
            </button>
          ))}
        </div>

        {data === null ? (
          <SacredLoader />
        ) : data === "error" ? (
          <p className="caption">{t("wedding:error")}</p>
        ) : !data.centre ? (
          <p className="caption">{t("wedding:places.noTown")}</p>
        ) : (
          <>
            {data.centres.length > 1 && (
              <div className="wnear" role="radiogroup">
                {data.centres.map((c) => (
                  <button
                    key={c.kind}
                    type="button"
                    role="radio"
                    aria-checked={c.kind === data.centre?.kind}
                    className={`wnear__opt${c.kind === data.centre?.kind ? " is-on" : ""}`}
                    onClick={() => setNear(c.kind)}
                  >
                    {t(`wedding:near.${c.kind}`)} · {c.label}
                  </button>
                ))}
              </div>
            )}

            {data.partners.length > 0 && (
              <section className="wpartners">
                <h3 className="wedding__label">
                  {t("wedding:partners.title")}
                </h3>
                <ul className="wcards">
                  {data.partners.map((p, i) => (
                    <PlaceCard
                      key={p.id}
                      index={i}
                      partner
                      name={p.name}
                      photo={p.photo}
                      category={category!}
                      offer={
                        p.offer
                          ? `${p.discount_percent ? `${t("wedding:partners.off", { n: p.discount_percent })} · ` : ""}${p.offer}`
                          : null
                      }
                      meta={[
                        t("wedding:places.km", { km: p.distance_km }),
                        p.verified ? t("wedding:partners.verified") : null,
                        p.valid_until
                          ? t("wedding:partners.until", {
                              date: formatDate(p.valid_until),
                            })
                          : null,
                      ]}
                      note={p.terms}
                      lat={p.latitude}
                      lon={p.longitude}
                      phone={p.phone}
                      website={p.website}
                      onShare={() =>
                        openShare(
                          p.name,
                          p.distance_km,
                          p.latitude,
                          p.longitude,
                        )
                      }
                    />
                  ))}
                </ul>
              </section>
            )}

            <section>
              <h3 className="wedding__label">
                {t("wedding:places.title", { city: centreLabel })}
              </h3>
              {data.places.length === 0 ? (
                <p className="caption">
                  {t("wedding:places.none", { city: centreLabel })}
                </p>
              ) : (
                <ul className="wcards">
                  {data.places.map((p, i) => (
                    <PlaceCard
                      key={p.ref}
                      index={i}
                      name={p.name}
                      photo={p.photo}
                      photoSource={p.photo_source}
                      category={category!}
                      meta={[
                        t("wedding:places.km", { km: p.distance_km }),
                        p.vegetarian ? t("wedding:places.veg") : null,
                        p.address,
                      ]}
                      lat={p.latitude}
                      lon={p.longitude}
                      phone={p.phone}
                      website={p.website}
                      onShare={() =>
                        openShare(
                          p.name,
                          p.distance_km,
                          p.latitude,
                          p.longitude,
                        )
                      }
                    />
                  ))}
                </ul>
              )}
              <p className="caption wedding__ordered">
                {t("wedding:places.ordered")}
              </p>
              {data.partners.length === 0 && (
                <p className="caption wedding__ordered">
                  {t("wedding:partners.none", { city: centreLabel })}
                </p>
              )}
              <p className="caption wedding__credit">
                <a
                  href="https://www.openstreetmap.org/copyright"
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("wedding:places.credit")}
                </a>
                {data.places_updated
                  ? ` · ${t("wedding:places.updated", { date: formatDate(data.places_updated) })}`
                  : ""}
              </p>
              <PhotoCredits categories={stage.categories} />
            </section>
          </>
        )}
      </main>
      {sharing && (
        <SharePlaceSheet
          connectionId={connectionId}
          candidateId={forId ?? sessionId ?? ""}
          viewerIsCandidate={!forId}
          matchName={name}
          placeName={sharing.name}
          text={sharing.text}
          onClose={() => setSharing(null)}
        />
      )}
    </>
  );
}

function PlaceActions({
  lat,
  lon,
  phone,
  website,
}: {
  lat: number;
  lon: number;
  phone: string | null;
  website: string | null;
}) {
  const { t } = useTranslation("wedding");
  const tel = phone?.split(/[;,]/)[0]?.trim();
  return (
    <span className="wplace__actions">
      <a
        className="wplace__act"
        href={mapLink(lat, lon)}
        target="_blank"
        rel="noreferrer"
      >
        <Icon name="pin" size={16} />
        {t("wedding:places.map")}
      </a>
      {tel && (
        <a className="wplace__act" href={`tel:${tel.replace(/\s+/g, "")}`}>
          <Icon name="phone" size={16} />
          {t("wedding:places.call")}
        </a>
      )}
      {website && /^https?:\/\//.test(website) && (
        <a
          className="wplace__act"
          href={website}
          target="_blank"
          rel="noreferrer"
        >
          <Icon name="web" size={16} />
          {t("wedding:places.site")}
        </a>
      )}
    </span>
  );
}

/* One place, as a card: its photo on top (the place's own when there is
 * one, otherwise a photo of that kind of place, labelled as such), a share
 * button on the photo, then the name, what matters, and how to reach it. */
function PlaceCard({
  index,
  partner = false,
  name,
  photo,
  photoSource = null,
  category,
  offer = null,
  meta,
  note = null,
  lat,
  lon,
  phone,
  website,
  onShare,
}: {
  index: number;
  partner?: boolean;
  name: string;
  photo: string | null;
  photoSource?: string | null;
  category: string;
  offer?: string | null;
  meta: (string | null)[];
  note?: string | null;
  lat: number;
  lon: number;
  phone: string | null;
  website: string | null;
  onShare: () => void;
}) {
  const { t } = useTranslation("wedding");
  const src = photo ?? categoryPhoto(category, index);
  return (
    <li className={`wcard${partner ? " wcard--partner" : ""}`}>
      <div className="wcard__media">
        {src && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt="" loading="lazy" decoding="async" />
        )}
        {partner && (
          <span className="wcard__badge">
            <Icon name="offer" size={16} />
            {t("wedding:partners.badge")}
          </span>
        )}
        {!photo ? (
          <span className="wcard__rep">
            {t("wedding:places.representative")}
          </span>
        ) : photoSource ? (
          <a
            className="wcard__rep"
            href={photoSource}
            target="_blank"
            rel="noreferrer"
          >
            {t("wedding:places.photoCredit")}
          </a>
        ) : null}
      </div>
      <button
        type="button"
        className="wcard__share"
        aria-label={t("wedding:share.button", { name })}
        title={t("wedding:share.button", { name })}
        onClick={onShare}
      >
        <Icon name="share" />
      </button>
      <div className="wcard__body">
        <span className="wcard__name">{name}</span>
        {offer && <span className="wcard__offer">{offer}</span>}
        <span className="wcard__meta">{meta.filter(Boolean).join(" · ")}</span>
        {note && <span className="caption">{note}</span>}
        <PlaceActions lat={lat} lon={lon} phone={phone} website={website} />
      </div>
    </li>
  );
}

/* The free licences ask for the photographer's name; it sits under the list. */
function PhotoCredits({ categories }: { categories: string[] }) {
  const { t } = useTranslation("wedding");
  const shown = categories.filter((c) => PHOTO_CREDITS[c]?.length);
  if (!shown.length) return null;
  return (
    <details className="wcredits">
      <summary>{t("wedding:places.photoCredits")}</summary>
      <ul>
        {shown.map((c) => (
          <li key={c}>
            {t(`wedding:category.${c}`)}:{" "}
            {PHOTO_CREDITS[c].map((credit, i) => (
              <span key={credit.source}>
                {i > 0 && "; "}
                <a href={credit.source} target="_blank" rel="noreferrer">
                  {credit.author}
                </a>{" "}
                ({credit.license})
              </span>
            ))}
            {" · Wikimedia Commons"}
          </li>
        ))}
      </ul>
    </details>
  );
}
