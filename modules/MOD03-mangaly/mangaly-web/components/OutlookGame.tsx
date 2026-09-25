"use client";

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import OutlookScene from "@/components/OutlookScene";
import {
  OUTLOOK,
  OUTLOOK_CATEGORY,
  OUTLOOK_DEPENDS,
  type OutlookAnswers,
} from "@/lib/outlook";

/* The ten-question activity (BR07 / FR033, baseline §12).
 *
 * One question on screen at a time, two big choices, a progress bar. §12 asks
 * for something "game-like, approximately five minutes or less", and the
 * point of the one-at-a-time card is that answering feels like moving rather
 * than filling in a form — a ten-row grid of radio buttons would collect the
 * same data and nobody would finish it.
 *
 * Deliberate design rules, all of them from the baseline rather than taste:
 *   - No score, no total, no percentage (§3, §4.8). The result is ten words.
 *   - Neither option is the better one, and the copy never implies otherwise.
 *     Olson's Circumplex model — the backbone of PREPARE/ENRICH — is explicit
 *     that the unhealthy positions are the EXTREMES AT BOTH ENDS, so a result
 *     that graded people would be wrong on the science as well as the spec.
 *   - You can go back, and you can redo the whole thing later. §12 calls this
 *     an aid to understanding, not a diagnosis.
 */

type Props = {
  initial: OutlookAnswers;
  saving: boolean;
  onSave: (answers: OutlookAnswers) => void;
  onCancel: () => void;
};

export default function OutlookGame({
  initial,
  saving,
  onSave,
  onCancel,
}: Props) {
  const { t } = useTranslation(["common", "profile"]);
  const [answers, setAnswers] = useState<OutlookAnswers>(initial);
  // Open on the first unanswered question, so returning resumes rather than
  // making someone click past what they have already done.
  const [index, setIndex] = useState(() => {
    const next = OUTLOOK.findIndex((d) => !initial[d.id]);
    return next === -1 ? OUTLOOK.length : next;
  });

  const answeredCount = useMemo(
    () => OUTLOOK.filter((d) => answers[d.id]).length,
    [answers],
  );
  const finished = index >= OUTLOOK.length;

  /* Skipping actively clears any earlier answer: someone who returns and
     skips a question is withdrawing that statement, not leaving it standing. */
  function skip(dimensionId: string) {
    setAnswers((prev) => {
      const next = { ...prev };
      delete next[dimensionId];
      return next;
    });
    setIndex((i) => i + 1);
  }

  function choose(dimensionId: string, pole: string) {
    setAnswers((prev) => ({ ...prev, [dimensionId]: pole }));
    // A short beat before advancing so the choice is visibly registered
    // rather than the next question appearing to arrive unprompted.
    window.setTimeout(() => setIndex((i) => i + 1), 140);
  }

  if (finished) {
    return (
      <div className="game">
        <div className="game__done">
          <h3 className="h2" style={{ margin: 0 }}>
            {t("profile:outlook.done", { count: answeredCount })}
          </h3>
          <p className="caption" style={{ margin: 0 }}>
            {t("profile:outlook.doneBody")}
          </p>
        </div>
        {/* The portrait: the ten scenes you chose, with your words under
            them. A picture of how you are, not a chart of how you scored. */}
        <ul className="portrait">
          {OUTLOOK.filter((d) => answers[d.id]).map((d) => (
            <li key={d.id} className="portrait__tile">
              <OutlookScene id={answers[d.id]} />
              <span className="portrait__label">
                {t(`profile:outlook.pole.${answers[d.id]}`)}
              </span>
            </li>
          ))}
        </ul>
        <p className="caption">{t("profile:outlook.disclaimer")}</p>
        <div className="sheet__row">
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => setIndex(0)}
          >
            {t("profile:outlook.redo")}
          </button>
          <button
            type="button"
            className="btn btn--primary"
            disabled={saving}
            onClick={() => onSave(answers)}
          >
            {saving ? t("profile:editor.saving") : t("profile:outlook.save")}
          </button>
        </div>
      </div>
    );
  }

  const dimension = OUTLOOK[index];
  return (
    <div className="game">
      <div className="game__progress" aria-hidden="true">
        <span
          className="game__progress-bar"
          style={{ width: `${(answeredCount / OUTLOOK.length) * 100}%` }}
        />
      </div>
      <span className="caption">
        {t("profile:outlook.progress", {
          done: index + 1,
          total: OUTLOOK.length,
        })}
      </span>

      {/* The words collect as you answer. This is the whole reason the
          activity is worth doing rather than filling a form: you watch a
          description of yourself being assembled, one choice at a time,
          instead of pushing data into a field and seeing nothing back. */}
      {answeredCount > 0 && (
        <ul className="game__collected" aria-live="polite">
          {OUTLOOK.filter((d) => answers[d.id]).map((d) => (
            <li
              key={d.id}
              className="game__mini game__mini--new"
              title={t(`profile:outlook.pole.${answers[d.id]}`)}
            >
              <OutlookScene id={answers[d.id]} />
            </li>
          ))}
        </ul>
      )}

      {/* Keyed on the question so each card mounts fresh and animates in —
          the movement is what makes ten questions feel like progress. */}
      <h3 key={dimension.id} className="game__q game__q--enter">
        {t(`profile:outlook.q.${dimension.id}`)}
      </h3>

      <div
        key={`c-${dimension.id}`}
        className="game__choices game__choices--enter"
        role="group"
      >
        {dimension.poles.map((pole) => (
          <button
            key={pole}
            type="button"
            className={`game__choice game__choice--scene${answers[dimension.id] === pole ? " is-chosen" : ""}`}
            onClick={() => choose(dimension.id, pole)}
          >
            <OutlookScene id={pole} />
            <span className="game__choice-label">
              {t(`profile:outlook.pole.${pole}`)}
            </span>
          </button>
        ))}
        {/* Always offered. A two-way forced choice would put a position in
            someone's mouth that they may not hold, and "it depends" is the
            honest answer to most of these. The Verification Circle already
            accepts "Don't know" for the same reason. */}
        <button
          type="button"
          className={`game__choice game__choice--depends${
            answers[dimension.id] === OUTLOOK_DEPENDS ? " is-chosen" : ""
          }`}
          onClick={() => choose(dimension.id, OUTLOOK_DEPENDS)}
        >
          <OutlookScene id={OUTLOOK_DEPENDS} />
          <span className="game__choice-label">
            {t(`profile:outlook.pole.${OUTLOOK_DEPENDS}`)}
          </span>
        </button>
      </div>

      {/* Skipping stores nothing at all, so the profile stays silent rather
          than asserting anything. */}
      <button
        type="button"
        className="link link--button"
        onClick={() => skip(dimension.id)}
      >
        {t("profile:outlook.skip")}
      </button>

      <div className="sheet__row">
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => (index === 0 ? onCancel() : setIndex((i) => i - 1))}
        >
          {index === 0 ? t("common:action.cancel") : t("common:action.back")}
        </button>
        {answeredCount > 0 && (
          <button
            type="button"
            className="btn btn--secondary"
            disabled={saving}
            onClick={() => onSave(answers)}
          >
            {t("profile:outlook.save")}
          </button>
        )}
      </div>
    </div>
  );
}

export { OUTLOOK_CATEGORY };
