"use client";

// ======================================================================
// [Trust pack §2, 2026-09-30] "Were you paid on time?"
//
// REQUIREMENT: only the person who was paid is asked, once, with one tap
// (Yes / No); the payer never sees the answer and others see only the
// total once three people have answered ("Paid on time: 2 of 3").
// APPROACH:
//  - <PaidOnTimeQuestion ask>: the one-tap card. Two equal buttons (no
//    brand fill on either — neither answer is the "right" one), a single
//    line on privacy, then a quiet "Thank you" in place. The answer is final
//    (the API returns 409 on a second one), so there is no undo.
//  - <PaidOnTimeForLink link>: finds the caller's open question for this
//    contract or hired-job thread (the ask's `link`) and shows the card, so
//    it meets the person where the work happened. Nothing when there is none.
//  - <PaidOnTimeLine value>: the public count, shown only when the API
//    returns it (`shown` / `label`), with a quiet icon — never stars.
// ======================================================================

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CalendarCheck, Check, Lock } from "lucide-react";
import { ApiError, type PaidOnTime, type PaidOnTimeAsk } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

export function PaidOnTimeQuestion({ ask, onAnswered, headingLevel = "h2" }: { ask: PaidOnTimeAsk; onAnswered?: (a: PaidOnTimeAsk) => void; headingLevel?: "h1" | "h2" }) {
  const { t } = useTranslation(["trustSafety", "common"]);
  const sdk = useSdk();
  const [state, setState] = useState<PaidOnTimeAsk>(ask);
  const [justAnswered, setJustAnswered] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const Heading = headingLevel;

  async function answer(yes: boolean) {
    setBusy(true);
    setError(null);
    try {
      const next = await sdk.trustPack.answerPaidOnTime(ask.id, yes);
      setState(next);
      setJustAnswered(true);
      onAnswered?.(next);
    } catch (e) {
      if (e instanceof ApiError && e.code === "paid_on_time_already_answered") {
        setState({ ...state, answered: true });
      } else {
        setError(e instanceof ApiError && typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"));
      }
    } finally {
      setBusy(false);
    }
  }

  if (state.answered) {
    return (
      <section className="vy-card vy-pot" aria-live="polite">
        <div className="vy-pot-head">
          <span className="vy-acct-tile" data-tint="verified" aria-hidden="true">
            <Check size={20} strokeWidth={2} />
          </span>
          <div className="vy-pot-text">
            <Heading className="vy-pot-title">{justAnswered ? t("trustSafety:paidOnTime.thanks") : t("trustSafety:paidOnTime.answered")}</Heading>
            <p>{t("trustSafety:paidOnTime.thanksBody")}</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="vy-card vy-pot" aria-labelledby={`pot-${ask.id}`}>
      <div className="vy-pot-head">
        <span className="vy-acct-tile" data-tint="teal" aria-hidden="true">
          <CalendarCheck size={20} strokeWidth={1.9} />
        </span>
        <div className="vy-pot-text">
          <Heading id={`pot-${ask.id}`} className="vy-pot-title">
            {ask.question}
          </Heading>
          {ask.payer_name && <p>{t("trustSafety:paidOnTime.paidBy", { name: ask.payer_name })}</p>}
        </div>
      </div>
      <div className="vy-pot-actions" role="group" aria-labelledby={`pot-${ask.id}`}>
        <button type="button" className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => answer(true)}>
          {t("trustSafety:paidOnTime.yes")}
        </button>
        <button type="button" className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => answer(false)}>
          {t("trustSafety:paidOnTime.no")}
        </button>
      </div>
      {error && (
        <p className="vy-error" role="alert">
          {error}
        </p>
      )}
      <p className="vy-pot-private">
        <Lock size={14} strokeWidth={2} aria-hidden="true" />
        <span>{t("trustSafety:paidOnTime.private")}</span>
      </p>
    </section>
  );
}

/** The caller's open question for this contract or thread (`/contracts/{id}`, `/enquiries/{id}`). */
export function PaidOnTimeForLink({ link }: { link: string }) {
  const sdk = useSdk();
  const { i18n } = useTranslation();
  const [ask, setAsk] = useState<PaidOnTimeAsk | null>(null);

  useEffect(() => {
    let live = true;
    sdk.trustPack
      .paidOnTimeAsks("open")
      .then((rows) => {
        if (live) setAsk(rows.find((a) => a.link === link) ?? null);
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [sdk, link, i18n.language]);

  if (!ask) return null;
  return <PaidOnTimeQuestion key={ask.id} ask={ask} />;
}

/** "Paid on time: 2 of 3", only when the API shows it. */
export function PaidOnTimeLine({ value, className }: { value: PaidOnTime | null | undefined; className?: string }) {
  if (!value || !value.shown || !value.label) return null;
  return (
    <span className={`vy-pot-line${className ? ` ${className}` : ""}`} data-numeric="">
      <CalendarCheck size={15} strokeWidth={2} aria-hidden="true" />
      <span>{value.label}</span>
    </span>
  );
}
