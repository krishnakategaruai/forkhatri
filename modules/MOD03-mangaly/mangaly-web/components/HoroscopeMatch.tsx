"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getJson, query } from "@/lib/api";

/* Horoscope match on a profile: the traditional Guna Milan out of 36, each of
 * the eight kootas with what it is based on and what each side has, and Mangal
 * Dosha for both with exactly where Mars sits. Shown as it is — no verdict,
 * no colour for "good" or "bad" — with the notice that it is a traditional
 * calculation the family interprets. Numbers come from the horoscope service
 * (Mangaly's tables, checked against Drik Panchang and AstroSage). */

type Koota = {
  koota: string;
  score: number;
  maxScore: number;
  groomClass: string;
  brideClass: string;
  exceptionApplied: boolean | null;
  explanation: { code: string; params: Record<string, string | number | boolean> };
};
type Mangal = {
  status: "PRESENT" | "ABSENT" | "CANCELLED" | "INDETERMINATE";
  marsRashi: number | null;
  relevantPlacements: { reference: "LAGNA" | "MOON" | "VENUS"; house: number }[];
  level: "HIGH" | "LOW" | null;
};
type PoruthamItem = { porutham: string; agrees: boolean; brideClass: string; groomClass: string; essential: boolean };
type Match = {
  ashtakoota: { status: "CALCULATED" | "NOT_DETERMINABLE"; totalScore: number | null; maxScore: number; kootas: Koota[] };
  porutham?: { status: "CALCULATED" | "NOT_DETERMINABLE"; agreed: number | null; outOf: number; essentialsAgree: boolean | null; items: PoruthamItem[] };
  mangal: { groom: Mangal; bride: Mangal };
  warnings: { code: string }[];
};
export type HoroscopeMatchResponse = Response;
type Response = {
  available: boolean;
  missing: string | null;
  match: Match | null;
  /** The family's matching style: their choice, else by mother tongue. */
  preferred_system?: "ashtakoota" | "porutham" | "both";
};

const RASHI_KEYS = ["mesh", "vrishabh", "mithun", "kark", "simha", "kanya", "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen"];
const RASHI_CODES = ["MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA", "TULA", "VRISHCHIKA", "DHANU", "MAKARA", "KUMBHA", "MEENA"];
const NAKSHATRA_KEYS = [
  "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
  "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
  "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
  "purva_bhadrapada", "uttara_bhadrapada", "revati",
];

type Props = {
  /** Profile mode: the match between the candidate in context and this person. */
  otherAccountId?: string;
  /** The candidate a family member is acting for, with their name, if any. */
  forCandidate?: { accountId: string; name: string };
  /** Checker mode: a result already calculated (the Kundli matching page). */
  result?: Response;
  /** Inside the compatibility panel: the panel carries the title. */
  bare?: boolean;
};

const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));

/* One koota as a ring: how much of its points the pair has. One accent,
 * no red/green verdict — the family reads the numbers. */
function Ring({ score, max, label }: { score: number; max: number; label: string }) {
  const r = 22;
  const c = 2 * Math.PI * r;
  const share = max > 0 ? Math.max(0, Math.min(1, score / max)) : 0;
  return (
    <li className="hring">
      <svg className="hring__svg" viewBox="0 0 56 56" aria-hidden="true">
        <circle className="hring__track" cx="28" cy="28" r={r} />
        <circle
          className="hring__fill"
          cx="28"
          cy="28"
          r={r}
          strokeDasharray={`${share * c} ${c}`}
          transform="rotate(-90 28 28)"
        />
      </svg>
      <span className="hring__label">{label}</span>
      <span className="hring__pts">
        {fmt(score)}
        <span className="hmatch__of">/{max}</span>
      </span>
    </li>
  );
}

export default function HoroscopeMatch({ otherAccountId, forCandidate, result, bare }: Props) {
  const { t } = useTranslation(["horoscope", "profile"]);
  const [fetched, setData] = useState<Response | null | "error">(null);
  const data = result ?? fetched;

  useEffect(() => {
    if (result || !otherAccountId) return;
    let active = true;
    setData(null);
    getJson<Response>(`/horoscope/match/${otherAccountId}${query({ for_candidate: forCandidate?.accountId })}`).then((r) => {
      if (active) setData(r ?? "error");
    });
    return () => {
      active = false;
    };
  }, [otherAccountId, forCandidate?.accountId, result]);

  if (data === null) return null;

  const head = (
    <div className="hmatch__head">
      {!bare && <h2 className="hmatch__title">{t("horoscope:title")}</h2>}
      <p className="hmatch__layer">{t("horoscope:layer")}</p>
    </div>
  );

  if (data === "error") {
    return (
      <section className="hmatch" aria-label={t("horoscope:title")}>
        {head}
        <p className="caption">{t("horoscope:unavailable")}</p>
      </section>
    );
  }

  if (!data.available || !data.match) {
    // Two people of the same gender are not a match; nothing to show.
    if (data.missing === "SAME_GENDER" || !data.missing) return null;
    const self = data.missing === "NO_CHART_SELF" || data.missing === "NO_BIRTH_PLACE";
    const message =
      self && forCandidate
        ? t("horoscope:missing.NO_CHART_SELF_FAMILY", { name: forCandidate.name.split(" ")[0] })
        : t(`horoscope:missing.${data.missing}`);
    return (
      <section className="hmatch hmatch--empty" aria-label={t("horoscope:title")}>
        {head}
        <p className="hmatch__missing">{message}</p>
        {self && !forCandidate && (
          <Link className="btn btn--ghost hmatch__add" href="/me">
            {t("horoscope:addDetails")}
          </Link>
        )}
      </section>
    );
  }

  const { ashtakoota, mangal, warnings } = data.match;
  const cls = (c: string) => {
    const star = /^STAR_(\d+)$/.exec(c);
    if (star) return t(`profile:option.nakshatra.${NAKSHATRA_KEYS[Number(star[1]) - 1]}`);
    const sign = RASHI_CODES.indexOf(c);
    if (sign >= 0) return t(`profile:option.rashi.${RASHI_KEYS[sign]}`);
    return t(`horoscope:class.${c}`, { defaultValue: c });
  };

  const preferred = data.preferred_system ?? "ashtakoota";
  const both = preferred === "both";
  const order: ("ashtakoota" | "porutham")[] = preferred === "porutham" ? ["porutham"] : both ? ["porutham", "ashtakoota"] : ["ashtakoota"];
  const porutham = data.match.porutham;
  const poruthamBlock = porutham ? (
    <div className="hmatch__system" key="porutham">
      {both && <h3 className="hmatch__subtitle">{t("horoscope:system.porutham")}</h3>}
      {porutham.status === "CALCULATED" && porutham.agreed !== null ? (
        <>
          <div className="hmatch__score">
            <span className="hmatch__total">{porutham.agreed}</span>
            <span className="hmatch__max">{t("horoscope:porutham.outOf", { max: porutham.outOf })}</span>
          </div>
          <p className="hmatch__essential">
            {porutham.essentialsAgree ? t("horoscope:porutham.essentialsAgree") : t("horoscope:porutham.essentialsFail")}
          </p>
          <ul className="hmatch__agree">
            {porutham.items.map((p) => (
              <li key={p.porutham} className={`hmatch__agree-item${p.agrees ? " is-on" : ""}`}>
                <span aria-hidden="true">{p.agrees ? "✓" : "–"}</span>
                {t(`horoscope:porutham.name.${p.porutham}`)}
                <span className="sr-only">
                  {p.agrees ? t("horoscope:porutham.agrees") : t("horoscope:porutham.notAgrees")}
                </span>
              </li>
            ))}
          </ul>
          <details className="hmatch__details">
            <summary>{t("horoscope:details")}</summary>
          <table className="hmatch__table">
            <thead>
              <tr>
                <th scope="col" />
                <th scope="col">{t("horoscope:bride")}</th>
                <th scope="col">{t("horoscope:groom")}</th>
                <th scope="col" className="hmatch__pts" />
              </tr>
            </thead>
            <tbody>
              {porutham.items.map((p) => (
                <tr key={p.porutham}>
                  <th scope="row">
                    <span className="hmatch__koota">
                      {t(`horoscope:porutham.name.${p.porutham}`)}
                      {p.essential && <span className="hmatch__tag">{t("horoscope:porutham.essential")}</span>}
                    </span>
                    <span className="hmatch__basis">{t(`horoscope:porutham.basis.${p.porutham}`)}</span>
                  </th>
                  <td>{cls(p.brideClass)}</td>
                  <td>{cls(p.groomClass)}</td>
                  <td className="hmatch__pts">{p.agrees ? t("horoscope:porutham.agrees") : t("horoscope:porutham.notAgrees")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </details>
        </>
      ) : (
        <p className="hmatch__missing">{t("horoscope:notDeterminable")}</p>
      )}
    </div>
  ) : null;
  const ashtakootaBlock = (
    <div className="hmatch__system" key="ashtakoota">
      {both && <h3 className="hmatch__subtitle">{t("horoscope:system.ashtakoota")}</h3>}
      {ashtakoota.status === "CALCULATED" && ashtakoota.totalScore !== null ? (
        <>
          <div className="hmatch__score">
            <span className="hmatch__total">{fmt(ashtakoota.totalScore)}</span>
            <span className="hmatch__max">{t("horoscope:outOf", { max: ashtakoota.maxScore })}</span>
          </div>
          <ul className="hmatch__rings">
            {ashtakoota.kootas.map((k) => (
              <Ring key={k.koota} score={k.score} max={k.maxScore} label={t(`horoscope:koota.${k.koota}`)} />
            ))}
          </ul>
          <details className="hmatch__details">
            <summary>{t("horoscope:details")}</summary>
          <table className="hmatch__table">
            <thead>
              <tr>
                <th scope="col" />
                <th scope="col">{t("horoscope:groom")}</th>
                <th scope="col">{t("horoscope:bride")}</th>
                <th scope="col" className="hmatch__pts" />
              </tr>
            </thead>
            <tbody>
              {ashtakoota.kootas.map((k) => (
                <tr key={k.koota}>
                  <th scope="row">
                    <span className="hmatch__koota">{t(`horoscope:koota.${k.koota}`)}</span>
                    <span className="hmatch__basis">{t(`horoscope:basis.${k.koota}`)}</span>
                    {k.koota === "NADI" && k.explanation.params.sameSignOtherStar === true && (
                      <span className="hmatch__note">{t("horoscope:note.nadiSameSign")}</span>
                    )}
                    {k.koota === "BHAKOOT" && k.explanation.params.sameLord === true && (
                      <span className="hmatch__note">{t("horoscope:note.bhakootSameLord", { lord: cls(k.groomClass) })}</span>
                    )}
                  </th>
                  <td>{cls(k.groomClass)}</td>
                  <td>{cls(k.brideClass)}</td>
                  <td className="hmatch__pts">
                    {fmt(k.score)}
                    <span className="hmatch__of">/{k.maxScore}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </details>
        </>
      ) : (
        <p className="hmatch__missing">{t("horoscope:notDeterminable")}</p>
      )}

    </div>
  );

  const mangalCard = (who: "groom" | "bride", m: Mangal) => (
    <div className="hmatch__mangal-side" key={who}>
      <span className="hmatch__mangal-who">{t(`horoscope:${who}`)}</span>
      <strong className="hmatch__mangal-status">
        {m.status === "PRESENT" && m.level ? t(`horoscope:mangal.${m.level}`) : t(`horoscope:mangal.${m.status}`)}
      </strong>
      {m.status === "INDETERMINATE" ? (
        <span className="caption">{t("horoscope:mangal.indeterminate")}</span>
      ) : m.relevantPlacements.length === 0 ? (
        <span className="caption">{t("horoscope:mangal.none")}</span>
      ) : (
        <ul className="hmatch__placements">
          {m.relevantPlacements.map((p) => (
            <li key={p.reference} className="caption">
              {t("horoscope:mangal.placement", { house: p.house, ref: t(`horoscope:mangal.ref.${p.reference}`) })}
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <section className="hmatch" aria-label={t("horoscope:title")}>
      {head}

      {order.map((system) => (system === "porutham" ? poruthamBlock : ashtakootaBlock))}

      <div className="hmatch__mangal">
        <div className="hmatch__mangal-head">
          <h3 className="hmatch__subtitle">{t("horoscope:mangal.title")}</h3>
          <span className="caption">{t("horoscope:mangal.separate")}</span>
          <span className="caption">{t("horoscope:mangal.levelRule")}</span>
        </div>
        <div className="hmatch__mangal-grid">
          {mangalCard("groom", mangal.groom)}
          {mangalCard("bride", mangal.bride)}
        </div>
      </div>

      {warnings.length > 0 && (
        <ul className="hmatch__warnings">
          {warnings
            .filter((w) => ["BIRTH_TIME_APPROXIMATE", "BIRTH_TIME_UNKNOWN"].includes(w.code))
            .map((w) => (
              <li key={w.code} className="caption">
                {t(`horoscope:warning.${w.code}`)}
              </li>
            ))}
        </ul>
      )}
      <p className="hmatch__notice">{t("horoscope:notice")}</p>
    </section>
  );
}
