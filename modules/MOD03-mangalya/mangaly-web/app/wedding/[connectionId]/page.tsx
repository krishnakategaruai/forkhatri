"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import Icon from "@/components/Icon";
import SacredLoader from "@/components/SacredLoader";
import { useActiveContext } from "@/lib/activeContext";
import { requireSession } from "@/lib/auth";
import { listConversations } from "@/lib/messages";
import {
  STAGES,
  getStages,
  getSuggestions,
  mapLink,
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
  const forId = active?.kind === "family" ? active.circle.candidate_account_id : undefined;

  const [name, setName] = useState<string | null>(null);
  const [stage, setStageInfo] = useState<StageInfo | null | "missing">(null);
  const [category, setCategory] = useState<string | null>(null);
  const [near, setNear] = useState<string | undefined>(undefined);
  // Keyed by what was asked for, so a new category shows the loader until
  // its own answer arrives (never the previous category's places).
  const [loadedData, setLoadedData] = useState<{ key: string; value: Suggestions | "error" } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    (async () => {
      if (!(await requireSession()) || !alive) return;
      const [stages, conversations] = await Promise.all([
        getStages([connectionId], forId),
        listConversations(forId),
      ]);
      if (!alive) return;
      const s = stages[0];
      setStageInfo(s ?? "missing");
      setName(conversations.find((c) => c.connection_id === connectionId)?.other_name ?? null);
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
    if (stage === null || stage === "missing" || stage.stage === next || saving) return;
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
      <button type="button" className="icon-btn" onClick={() => router.back()} aria-label={t("common:action.back")}>
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
  const data = loadedData && loadedData.key === dataKey ? loadedData.value : null;
  const centreLabel = data && data !== "error" ? data.centre?.label ?? "" : "";
  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(i18n.language, { day: "numeric", month: "short", year: "numeric" });

  return (
    <>
      {header}
      <main className="screen wedding">
        <section className="wstage" aria-labelledby="wstage-title">
          <h2 id="wstage-title" className="wedding__label">{t("wedding:stageTitle")}</h2>
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
                    <span className="wstage__dot" aria-hidden="true">{i + 1}</span>
                    <span>{t(`wedding:stage.${s}`)}</span>
                  </button>
                </li>
              );
            })}
          </ol>
          <p className="wstage__hint">{t(`wedding:stageHint.${stage.stage}`)}</p>
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
                <h3 className="wedding__label">{t("wedding:partners.title")}</h3>
                <ul className="wplaces">
                  {data.partners.map((p) => (
                    <li key={p.id} className="wplace wplace--partner">
                      <span className="wplace__badge">
                        <Icon name="offer" size={16} />
                        {t("wedding:partners.badge")}
                      </span>
                      <span className="wplace__name">{p.name}</span>
                      {p.offer && (
                        <span className="wplace__offer">
                          {p.discount_percent ? `${t("wedding:partners.off", { n: p.discount_percent })} · ` : ""}
                          {p.offer}
                        </span>
                      )}
                      <span className="wplace__meta">
                        {t("wedding:places.km", { km: p.distance_km })}
                        {p.verified ? ` · ${t("wedding:partners.verified")}` : ""}
                        {p.valid_until ? ` · ${t("wedding:partners.until", { date: formatDate(p.valid_until) })}` : ""}
                      </span>
                      {p.terms && <span className="caption">{p.terms}</span>}
                      <PlaceActions lat={p.latitude} lon={p.longitude} phone={p.phone} website={p.website} />
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section>
              <h3 className="wedding__label">{t("wedding:places.title", { city: centreLabel })}</h3>
              {data.places.length === 0 ? (
                <p className="caption">{t("wedding:places.none", { city: centreLabel })}</p>
              ) : (
                <ul className="wplaces">
                  {data.places.map((p) => (
                    <li key={p.ref} className="wplace">
                      <span className="wplace__name">{p.name}</span>
                      <span className="wplace__meta">
                        {t("wedding:places.km", { km: p.distance_km })}
                        {p.vegetarian ? ` · ${t("wedding:places.veg")}` : ""}
                        {p.address ? ` · ${p.address}` : ""}
                      </span>
                      <PlaceActions lat={p.latitude} lon={p.longitude} phone={p.phone} website={p.website} />
                    </li>
                  ))}
                </ul>
              )}
              <p className="caption wedding__ordered">{t("wedding:places.ordered")}</p>
              {data.partners.length === 0 && (
                <p className="caption wedding__ordered">{t("wedding:partners.none", { city: centreLabel })}</p>
              )}
              <p className="caption wedding__credit">
                <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
                  {t("wedding:places.credit")}
                </a>
                {data.places_updated ? ` · ${t("wedding:places.updated", { date: formatDate(data.places_updated) })}` : ""}
              </p>
            </section>
          </>
        )}
      </main>
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
      <a className="wplace__act" href={mapLink(lat, lon)} target="_blank" rel="noreferrer">
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
        <a className="wplace__act" href={website} target="_blank" rel="noreferrer">
          <Icon name="web" size={16} />
          {t("wedding:places.site")}
        </a>
      )}
    </span>
  );
}
