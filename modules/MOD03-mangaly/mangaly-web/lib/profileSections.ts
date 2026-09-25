/* Profile layout — how the attribute categories are grouped on screen, the
 * biodata order the family lens reads them in, and the "In my words" prompts.
 *
 * Grouping follows the biodata order Indian matrimony sites already use
 * (Shaadi.com's "About Myself" → lifestyle → family → partner preference;
 * Jeevansathi's About / Education & Career / Family / Desired Partner), so a
 * parent filling this in recognises the structure. Prompts follow Hinge and
 * Bumble (up to three short answers that give someone something real to
 * reply to). Stored as category `in_my_words`, keys prompt_1..3 — the
 * backend's PATCH /profile/{category} accepts any category, and prompts are
 * deliberately NOT in the enhanced-matching tier, so they never affect
 * discoverability or completeness.
 *
 * [2026-09-17 rework, contract §2] `BIODATA_SECTIONS` is the conventional
 * order the biodata lens shows: Basics, Religion & community, Education &
 * career, Family, Lifestyle, Horoscope, About, Partner expectations. */

export type SectionId =
  | "basics"
  | "community"
  | "education_career"
  | "lifestyle"
  | "family"
  | "horoscope"
  | "future"
  | "partner";

/** The edit hub's grouping (what the owner fills in). */
export const PROFILE_SECTIONS: { id: SectionId; categories: string[] }[] = [
  { id: "basics", categories: ["basics", "marital_history", "relocation"] },
  { id: "community", categories: ["community"] },
  {
    id: "education_career",
    categories: ["education", "profession", "education_career"],
  },
  {
    id: "family",
    categories: ["family", "family_involvement_expectations", "independence"],
  },
  {
    id: "lifestyle",
    categories: [
      "lifestyle",
      "food_travel_hobbies",
      "pets",
      "communication_style",
    ],
  },
  { id: "horoscope", categories: ["horoscope"] },
  { id: "future", categories: ["career_children_living_financial"] },
  { id: "partner", categories: ["partner_preference"] },
];

/** The biodata lens order (contract §2). `about` is prompts + voice, rendered apart. */
export const BIODATA_ORDER: SectionId[] = [
  "basics",
  "community",
  "education_career",
  "family",
  "lifestyle",
  "horoscope",
  "future",
  "partner",
];

export const PROMPT_CATEGORY = "in_my_words";
export const PROMPT_SLOTS = ["prompt_1", "prompt_2", "prompt_3"] as const;
export type PromptSlot = (typeof PROMPT_SLOTS)[number];

/* Prompts: Hinge's FORMAT, matrimony's AGENDA.
 *
 * The format is borrowed deliberately. A prompt is first-person, voluntary
 * and specific, and it leaves the reader something to reply to (Bumble's
 * rule against dead ends). That format solves matrimony's central UX
 * problem: the subjects that actually decide whether a marriage works —
 * living with in-laws, whether she keeps working, children, money, which
 * city — are exactly the subjects that turn a first meeting into an
 * interrogation. Research on real arranged-marriage meetings lands on the
 * same tension: cover these topics, but "rather than making it feel like an
 * interview with questions only, let it flow like a conversation." A prompt
 * makes a hard question feel like something you chose to say.
 *
 * The agenda is NOT Hinge's. Hinge and Bumble optimise for a spark, so their
 * prompts are banter — "Two truths and a lie", "the key to my heart". Those
 * were tried here and removed: they tell two families nothing about whether
 * a marriage would work. Four of the six groups below are the deal-breaker
 * conversations the research names; two keep enough warmth that a profile
 * still reads as a person rather than a questionnaire.
 *
 * A constraint neither dating app has: a parent may read this profile, so
 * every prompt must be answerable without embarrassment when a prospective
 * mother-in-law is the reader.
 *
 * The original six keys are all still here. Changing a key would orphan
 * answers members have already written. */
export const PROMPT_GROUPS = [
  {
    id: "where_we_live",
    questions: [
      "living_with_family",
      "which_city",
      "moving_abroad",
      "parents_nearby",
      "our_first_home",
      "home_should_feel",
    ],
  },
  {
    id: "work_and_ambition",
    questions: [
      "work_after_marriage",
      "my_work_means",
      "working_towards",
      "supporting_your_work",
      "when_work_is_heavy",
      "life_goal",
    ],
  },
  {
    id: "children_and_family",
    questions: [
      "on_children",
      "raising_children",
      "family_means",
      "my_family_in_words",
      "in_laws_role",
      "caring_for_parents",
    ],
  },
  {
    id: "money_and_home",
    questions: [
      "about_money",
      "saving_or_spending",
      "joint_or_separate",
      "running_the_home",
      "on_housework",
      "big_decisions",
    ],
  },
  {
    id: "who_i_am",
    questions: [
      "non_negotiable",
      "faith_looks_like",
      "when_we_disagree",
      "feel_supported",
      "friends_say",
      "quietly_proud",
    ],
  },
  {
    /* The subjects that sound trivial and end marriages, every one of them
       picked from divorce research rather than guessed:
         - Housework. A Harvard Business School study of 3,000 couples found
           25% of divorcing couples named disagreements about housework as
           the top reason — roughly one divorce in four. It is never about
           the cleaning; it is about power and respect.
         - Money, but the small kind. Money Magazine found 70% of couples
           argue about finances more than chores, sex or snoring, and named
           frivolous purchases, budgeting and undisclosed debt specifically.
         - India-specific: research on Indian divorces names "pressure on
           women to leave their jobs and pressure on men to leave their
           parents", in-laws controlling daily routines, and the joint-to-
           nuclear adjustment mismatch as leading causes.
       Nobody raises these before a wedding because they feel too small to
       mention. That is precisely why they belong on the profile. */
    id: "easy_to_skip",
    questions: [
      "daily_chores",
      "small_spending",
      "money_i_owe",
      "joint_or_nuclear",
      "daily_routine_say",
      "festivals_and_visits",
    ],
  },
  {
    /* The pressures, named out loud. Gottman's finding that 69% of conflicts
       in even happy couples are perpetual — never resolved, only managed —
       reframes what a matrimonial profile should ask. You are not looking
       for someone frictionless; you are looking for friction you can live
       with. These are the only prompts that ask a person to be unflattering
       about themselves, and they are the most useful ones on the profile. */
    id: "real_pressures",
    questions: [
      "perpetual_argument",
      "difficult_about",
      "when_i_am_upset",
      "how_i_say_sorry",
      "when_money_is_tight",
      "if_families_disagree",
    ],
  },
  {
    id: "everyday_life",
    questions: [
      "ideal_weekend",
      "simple_pleasures",
      "at_my_table",
      "i_wind_down_by",
      "together_we",
      "looking_for",
    ],
  },
] as const;

export type PromptGroupId = (typeof PROMPT_GROUPS)[number]["id"];

/** Flat list, for validation and for anything that does not care about grouping. */
export const PROMPT_QUESTIONS = PROMPT_GROUPS.flatMap((g) => g.questions);

/* `public` carries the visibility of this one answer (migration 039).
 *
 * Prompts are written by a candidate for another candidate, so by default
 * they are readable only once a connection is accepted — "she requests, he
 * accepts, then she can see them". Publishing a single answer opts that one
 * sentence out, and a published answer is readable by anyone signed in,
 * parents included. Absent means not published: the safe default is the
 * silent one. */
export type PromptValue = { q: string; a: string; public?: boolean };

export function isPromptValue(v: unknown): v is PromptValue {
  return (
    !!v &&
    typeof v === "object" &&
    typeof (v as PromptValue).q === "string" &&
    typeof (v as PromptValue).a === "string"
  );
}
