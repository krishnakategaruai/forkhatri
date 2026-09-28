"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import HoroscopeMatch, { type HoroscopeMatchResponse } from "@/components/HoroscopeMatch";
import PlaceSearch, { type PlaceValue } from "@/components/PlaceSearch";
import { postJson } from "@/lib/api";
import { BIRTH_TIME_ACCURACY } from "@/lib/profileCategoryConfig";
import { getCategoryAttributes, getOwnProfile } from "@/lib/profile";

import "../../me/me.css";

/* Kundli matching: any two people's birth details — a proposal that came
 * from outside Mangaly, relatives — calculated with exactly the same rules as
 * the profiles (Guna Milan as AstroSage, Porutham as ProKerala, Mangal Dosha)
 * and shown the same way. Nothing typed here is saved. Traditional matching
 * only: no predictions. A candidate's own saved details fill their side. */

type Person = { date: string; time: string; accuracy: string; place: PlaceValue | null };
const EMPTY: Person = { date: "", time: "", accuracy: "exact", place: null };

export default function KundliCheckPage() {
  const { t } = useTranslation(["horoscope", "profile", "common"]);
  const [groom, setGroom] = useState<Person>(EMPTY);
  const [bride, setBride] = useState<Person>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HoroscopeMatchResponse | null>(null);
  const [prefilled, setPrefilled] = useState<"groom" | "bride" | null>(null);

  // A candidate's own saved birth details fill their side.
  useEffect(() => {
    let alive = true;
    (async () => {
      const me = await getOwnProfile().catch(() => null);
      if (!me || !alive) return;
      const h = await getCategoryAttributes("horoscope").catch(() => ({}) as Awaited<ReturnType<typeof getCategoryAttributes>>);
      const val = (k: string) => (h[k]?.state === "value" ? h[k]?.value : null);
      const geo = val("birth_place_geo") as { id?: string; label?: string } | null;
      if (!alive) return;
      const mine: Person = {
        date: me.date_of_birth,
        time: typeof val("birth_time") === "string" ? (val("birth_time") as string) : "",
        accuracy: typeof val("birth_time_accuracy") === "string" ? (val("birth_time_accuracy") as string) : "exact",
        place: geo?.id ? { label: geo.label ?? "", place_id: String(geo.id) } : null,
      };
      if (me.gender === "male") setGroom(mine);
      else setBride(mine);
      setPrefilled(me.gender === "male" ? "groom" : "bride");
    })();
    return () => {
      alive = false;
    };
  }, []);

  const ready = (p: Person) => !!p.date && !!p.place?.place_id && (p.accuracy === "unknown" || !!p.time);

  async function calculate() {
    setError(null);
    setResult(null);
    if (!ready(groom) || !ready(bride)) {
      setError(t("horoscope:check.incomplete"));
      return;
    }
    setBusy(true);
    const body = (p: Person) => ({
      birth_date: p.date,
      birth_time: p.accuracy === "unknown" ? null : p.time,
      accuracy: p.accuracy,
      place_id: p.place?.place_id,
    });
    const out = await postJson<HoroscopeMatchResponse>("/horoscope/check", { groom: body(groom), bride: body(bride) });
    setBusy(false);
    if (out.ok) setResult(out.data);
    else setError(t(out.status === 422 ? "horoscope:check.invalid" : "horoscope:unavailable"));
  }

  const side = (who: "groom" | "bride", p: Person, set: (next: Person) => void) => (
    <section className="kcheck__person" aria-labelledby={`kcheck-${who}`}>
      <h2 className="kcheck__who" id={`kcheck-${who}`}>
        {t(`horoscope:${who}`)}
        {prefilled === who && <span className="kcheck__mine">{t("horoscope:check.yourDetails")}</span>}
      </h2>
      <label className="label" htmlFor={`${who}-date`}>{t("horoscope:check.dateOfBirth")}</label>
      <input id={`${who}-date`} className="field__input" type="date" value={p.date} max={new Date().toISOString().slice(0, 10)} onChange={(e) => set({ ...p, date: e.target.value })} />
      <label className="label" htmlFor={`${who}-accuracy`}>{t("profile:field.horoscope.birth_time_accuracy")}</label>
      <select id={`${who}-accuracy`} className="field__input" value={p.accuracy} onChange={(e) => set({ ...p, accuracy: e.target.value })}>
        {BIRTH_TIME_ACCURACY.map((a) => (
          <option key={a} value={a}>
            {t(`profile:option.birth_time_accuracy.${a}`)}
          </option>
        ))}
      </select>
      {p.accuracy !== "unknown" && (
        <>
          <label className="label" htmlFor={`${who}-time`}>{t("profile:field.horoscope.birth_time")}</label>
          <input id={`${who}-time`} className="field__input field__input--time" type="time" value={p.time} onChange={(e) => set({ ...p, time: e.target.value })} />
        </>
      )}
      <span className="label">{t("profile:field.horoscope.birth_place")}</span>
      <PlaceSearch label={t("profile:field.horoscope.birth_place")} value={p.place} onChange={(next) => set({ ...p, place: next })} />
    </section>
  );

  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("horoscope:check.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen kcheck">
        <p className="caption kcheck__intro">{t("horoscope:check.intro")}</p>
        <div className="kcheck__people">
          {side("groom", groom, setGroom)}
          {side("bride", bride, setBride)}
        </div>
        {error && <p className="kcheck__error" role="alert">{error}</p>}
        <button type="button" className="cta kcheck__go" disabled={busy} onClick={() => void calculate()}>
          {busy ? t("horoscope:check.calculating") : t("horoscope:check.calculate")}
        </button>
        <p className="caption">{t("horoscope:check.notSaved")}</p>
        {result && <HoroscopeMatch result={result} />}
      </main>
    </>
  );
}
