/* The short game-like assessment (BR07 / FR033, baseline §12).
 *
 * Ten forced choices, about five minutes, phrased as "which is more you?"
 * rather than a Likert scale — §12 asks for something game-like, and a
 * five-point agree/disagree grid is the opposite of that.
 *
 * WHERE THE DIMENSIONS COME FROM. Not invented. Each maps to an axis from an
 * instrument that actually predicts marital outcomes:
 *   - Olson's Circumplex model — cohesion (how much togetherness) and
 *     flexibility (how much a couple can change their arrangements). It is
 *     the backbone of PREPARE/ENRICH, the most-researched premarital
 *     assessment there is, with over 1,200 published papers behind it.
 *   - PREPARE/ENRICH's SCOPE personality scales — Social, Change, Organized,
 *     Pleasing, Emotionally Stable.
 *   - Gottman — how a disagreement starts, and whether a repair attempt is
 *     accepted, predict outcomes better than almost anything else.
 * Mangalya's own §12 list (communication, conflict, independence, family
 * involvement, career orientation, decision-making, money, social
 * preferences) is covered by these ten.
 *
 * WHAT THIS IS NOT. There is no score, no total, no percentage and no
 * ranking, and there must never be one: §3 forbids a trust or compatibility
 * score and §4.8 makes trust evidence rather than a number. Nothing here is
 * summed. Each answer is simply a word about how a person is, shown beside
 * the reader's own word for the same question.
 *
 * Neither pole is the better one. The Circumplex model is explicit that the
 * unhealthy positions are the extremes at BOTH ends — disengaged and
 * enmeshed, rigid and chaotic — so a result must never read as a grade. The
 * copy treats a difference as something to talk about, never as a mismatch.
 */

export const OUTLOOK_CATEGORY = "outlook";

/* The third answer, available on every question.
 *
 * A two-way forced choice asserts a position the person may not actually
 * hold — and a profile must never state that someone said something they did
 * not say. "It depends" is a real answer to most of these, and often the
 * honest one: whether you would rather sort out a disagreement now or take
 * time genuinely does depend on the disagreement.
 *
 * The baseline already models uncertainty as first-class. The Verification
 * Circle (M01-F §5) accepts "Don't know" and "Cannot confirm" alongside yes
 * and no, for the same reason: forcing a binary manufactures false certainty.
 *
 * A question left unanswered stores nothing and renders nothing. Silence is
 * not a position either. */
export const OUTLOOK_DEPENDS = "depends";

export type OutlookDimension = {
  id: string;
  /** The two poles. Order is presentation only and implies no ranking. */
  poles: readonly [string, string];
};

export const OUTLOOK: readonly OutlookDimension[] = [
  // Gottman — how a disagreement begins.
  { id: "conflict_timing", poles: ["talk_now", "need_time"] },
  // Gottman — repair attempts, and who offers one first.
  { id: "repair", poles: ["say_sorry_first", "heard_first"] },
  // Circumplex — cohesion.
  { id: "closeness", poles: ["mostly_together", "own_space"] },
  // Circumplex — flexibility. SCOPE — Organized.
  { id: "planning", poles: ["plan_it", "as_we_go"] },
  // §12 — family involvement.
  { id: "family_voice", poles: ["family_in_the_room", "us_first"] },
  // §12 — decision-making. SCOPE — Emotionally Stable adjacent.
  { id: "deciding", poles: ["decide_and_move", "sit_with_it"] },
  // §12 — money attitudes. Named by divorce research as a leading friction.
  { id: "money", poles: ["save_first", "spend_on_now"] },
  // SCOPE — Social.
  { id: "people", poles: ["full_house", "few_close"] },
  // SCOPE — Change.
  { id: "change", poles: ["try_the_new", "keep_what_works"] },
  // §12 — career orientation.
  { id: "work", poles: ["work_is_me", "work_funds_life"] },
];

export const OUTLOOK_IDS: readonly string[] = OUTLOOK.map((d) => d.id);

/** The answers a member has given, as `{ dimensionId: poleKey }`. */
export type OutlookAnswers = Record<string, string>;

/** How one dimension compares between the reader and the person they are
 *  reading. `unanswered` on either side means there is nothing to say —
 *  which is not the same as a difference, and must not be shown as one. */
export type OutlookComparison = {
  id: string;
  theirs: string;
  mine: string | null;
  same: boolean;
};

export function compareOutlook(
  theirs: OutlookAnswers,
  mine: OutlookAnswers,
): OutlookComparison[] {
  // Only dimensions they actually answered. An unanswered question is not a
  // position and must never be rendered as one.
  return OUTLOOK.filter((d) => theirs[d.id]).map((d) => ({
    id: d.id,
    theirs: theirs[d.id],
    mine: mine[d.id] ?? null,
    // "It depends" on either side is a real answer, so two people who both
    // said it do agree — but it is never treated as matching a pole.
    same: !!mine[d.id] && mine[d.id] === theirs[d.id],
  }));
}

/** Pull the answers out of the `{ state, value }` attribute shape. */
export function readOutlook(
  attributes: Record<string, Record<string, unknown>> | undefined,
): OutlookAnswers {
  const raw = attributes?.[OUTLOOK_CATEGORY] ?? {};
  const out: OutlookAnswers = {};
  for (const [key, entry] of Object.entries(raw)) {
    const value =
      entry && typeof entry === "object" && "value" in entry
        ? (entry as { value: unknown }).value
        : entry;
    if (typeof value === "string" && value) out[key] = value;
  }
  return out;
}
