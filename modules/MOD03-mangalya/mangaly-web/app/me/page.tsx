"use client";

import Link from "next/link";
import { useLoaderHold } from "@/lib/useLoaderHold";
import SacredLoader from "@/components/SacredLoader";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import OutlookGame from "@/components/OutlookGame";
import OutlookScene from "@/components/OutlookScene";
import PhotoCheckCard from "@/components/PhotoCheckCard";
import MemberMe from "@/components/MemberMe";
import {
  OUTLOOK,
  OUTLOOK_CATEGORY,
  readOutlook,
  type OutlookAnswers,
} from "@/lib/outlook";
import VoiceIntro from "@/components/VoiceIntro";
import { resolveMediaUrl } from "@/lib/api";
import AccountButton from "@/components/AccountButton";
import Icon from "@/components/Icon";
import "./me.css";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import { requireSession, logOut, type Session } from "@/lib/auth";
import { setManaging } from "@/lib/api";
import { entranceUrl } from "@/lib/platform";
import ClaimProfileNote from "@/components/ClaimProfileNote";
import { SUPPORTED_LANGUAGES, type Language } from "@/lib/i18n/config";
import { setPreferredLanguage } from "@/lib/i18n/provider";
import {
  findCategory,
  findField,
  type CategoryDef,
  type FieldDef,
} from "@/lib/profileCategoryConfig";
import {
  INTEREST_TAGS,
  formatClockTime,
  MAX_TAGS,
  parseTags,
  toTagKey,
} from "@/lib/profileFormat";
import {
  deletePhoto,
  getAllAttributeValues,
  getCompleteness,
  getOwnProfile,
  listPhotos,
  reorderPhotos,
  getVoiceIntro,
  setPrimaryPhoto,
  updateCategoryAttributes,
  uploadPhoto,
  type AttributeState,
  type AttributeValue,
  type CategoryAttributes,
  type CompletenessReport,
  type Photo,
  type Profile,
} from "@/lib/profile";
import {
  PROFILE_SECTIONS,
  PROMPT_CATEGORY,
  PROMPT_GROUPS,
  PROMPT_SLOTS,
  isPromptValue,
  type PromptSlot,
  type PromptValue,
  type SectionId,
} from "@/lib/profileSections";
import { getContexts } from "@/lib/homeCircle";
import { getStoredTheme, setPreferredTheme, type Theme } from "@/lib/theme";
import { TEXT_SIZES, getStoredTextSize, setPreferredTextSize, type TextSize } from "@/lib/textSize";
import PlaceSearch, { type PlaceValue } from "@/components/PlaceSearch";

/* FR001/FR002/FR003/FR005 · UX11 "Profile edit hub" — v3, built from
 * researched reference patterns rather than invented ones:
 *
 *   • Photo grid, up to six, main photo large — Hinge and Bumble both open
 *     their profile editor on a six-slot photo grid.
 *   • Prompts placed between photos and sections, not in one block — the
 *     way Hinge interleaves them through a profile, so a person can add one
 *     wherever it fits.
 *   • Edit / Preview toggle — Hinge's editor has exactly this. Mangalya's
 *     twist: two Preview lenses, "Before you connect" (the anonymized
 *     snippet a stranger actually sees) and "After you connect" (photos,
 *     prompts and full biodata), so the privacy promise is visible.
 *   • Value badges showing the real answer — Bumble's "My basics", Hinge's
 *     vitals — instead of filled/empty ticks.
 *   • Biodata section order familiar from Shaadi.com and Jeevansathi.
 *   • A "Next up" card (Bumble's "Complete my profile") and every edit in a
 *     bottom sheet: single-choice saves on tap, text/range fields on Save.
 */

const THEME_OPTIONS: Theme[] = ["light", "dark", "system"];

// Partner age range bounds for the slider (Baymard: pair a range slider with
// exact number fields; the slider sets an approximate range fast, the fields
// allow precision).
const AGE_MIN = 18;
const AGE_MAX = 70;

// Autocomplete suggestions for occupation — typing is faster than a long
// dropdown on mobile, and suggestions keep common answers consistent so
// matching isn't split across spellings. Free text still accepted.
const OCCUPATION_SUGGESTIONS = [
  "Software Engineer",
  "Doctor",
  "Teacher",
  "Professor",
  "Chartered Accountant",
  "Lawyer",
  "Civil Engineer",
  "Architect",
  "Banker",
  "Business Owner",
  "Entrepreneur",
  "Government Employee",
  "Civil Services (IAS/IPS)",
  "Defence Services",
  "Nurse",
  "Pharmacist",
  "Product Manager",
  "Data Scientist",
  "Designer",
  "Consultant",
];

type Values = Record<string, CategoryAttributes>;
type Status = "answered" | "hidden" | "empty";
type Draft = Record<string, { state: AttributeState; value: unknown }>;
type Sheet =
  | { kind: "section"; id: SectionId }
  | { kind: "prompt"; slot: PromptSlot }
  | { kind: "photo"; id: string }
  | { kind: "settings" }
  | { kind: "outlook" }
  | null;
type PageState =
  | { phase: "checking" }
  | { phase: "ready"; profile: Profile; values: Values; photos: Photo[] };

type EditBlock =
  | { kind: "outlook" }
  | { kind: "photos" }
  | { kind: "voice" }
  | { kind: "prompt"; slot: PromptSlot }
  | { kind: "section"; id: SectionId };
/* The profile is built in two parts, by the owner's instruction.

   Part 1 — DETAILS. The standard biodata a family reads, in the order a
   matrimonial profile is actually read: who you are, what you do, where you
   come from, how you live, your family, the horoscope, the forward-looking
   parts, and finally the private partner preference. Parents and relatives
   of a match see this part — and only as much of it as is shared.

   Part 2 — IN YOUR OWN WORDS. The Hinge/Bumble-style part: prompts, the
   voice introduction and the ten quick choices. Written for the person you
   might marry, seen only by candidates you connect with (or anything you
   choose to publish), never by their parents (migration 039). */
const DETAILS_LAYOUT: EditBlock[] = [
  { kind: "photos" },
  { kind: "section", id: "basics" },
  { kind: "section", id: "education_career" },
  { kind: "section", id: "community" },
  { kind: "section", id: "lifestyle" },
  { kind: "section", id: "family" },
  { kind: "section", id: "horoscope" },
  { kind: "section", id: "future" },
  { kind: "section", id: "partner" },
];

type PreviewBlock =
  | { kind: "photo"; index: number }
  | { kind: "identity" }
  | { kind: "prompt"; slot: PromptSlot }
  | { kind: "section"; id: SectionId };
const PREVIEW_LAYOUT: PreviewBlock[] = [
  { kind: "photo", index: 0 },
  { kind: "identity" },
  { kind: "prompt", slot: "prompt_1" },
  { kind: "photo", index: 1 },
  { kind: "section", id: "basics" },
  { kind: "section", id: "education_career" },
  { kind: "section", id: "lifestyle" },
  { kind: "prompt", slot: "prompt_2" },
  { kind: "photo", index: 2 },
  { kind: "section", id: "family" },
  { kind: "section", id: "community" },
  { kind: "section", id: "horoscope" },
  { kind: "section", id: "future" },
  { kind: "prompt", slot: "prompt_3" },
  { kind: "photo", index: 3 },
  { kind: "photo", index: 4 },
  { kind: "photo", index: 5 },
  { kind: "section", id: "partner" },
];

const ALL_CATEGORIES_IN_ORDER = PROFILE_SECTIONS.flatMap((s) => s.categories);

/* [D15, onboarding redesign 2026-10] "Next up" suggests the EASIEST missing
   answer first: one-tap choices, then a short number, in this order. Only
   when all of these are answered (or hidden) does it fall back to the first
   empty category in section order. The camera face check is never "Next
   up": it is its own optional card (owner, 2026-10-06: an optional trust
   step, never a gate). */
const EASY_NEXT: [category: string, key: string][] = [
  ["marital_history", "marital_status"],
  ["relocation", "relocation_willingness"],
  ["lifestyle", "diet"],
  ["education", "highest_education_level"],
  ["basics", "mother_tongue"],
  ["basics", "height_cm"],
  ["family", "family_type"],
  ["lifestyle", "smoking"],
  ["lifestyle", "drinking"],
  ["career_children_living_financial", "wants_children"],
];

function ageFromDob(dob: string): number {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const hadBirthday =
    now.getMonth() > birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() >= birth.getDate());
  if (!hadBirthday) age -= 1;
  return age;
}

function statusOf(values: Values, category: string): Status {
  // Only keys the config knows. A row stored under a stale key (a seed once
  // wrote marital_history/marital_history instead of .../marital_status)
  // otherwise counts as "answered" while the tile shows no value.
  const known = new Set(findCategory(category)?.fields.map((f) => f.key) ?? []);
  const attrs = Object.entries(values[category] ?? {})
    .filter(([key]) => known.has(key))
    .map(([, a]) => a);
  if (attrs.some((a) => a.state === "value")) return "answered";
  if (attrs.some((a) => a.state === "declined")) return "hidden";
  return "empty";
}

function emptyValue(f: FieldDef): unknown {
  if (f.kind === "ageRange") return { min: "", max: "" };
  return f.kind === "tags" ? [] : "";
}

/* The draft for a whole section. Keys are "<category>::<key>": two
   categories can share a key ("preference" is both pets and independence). */
const dkey = (category: string, key: string) => `${category}::${key}`;

function sectionDefs(id: SectionId): CategoryDef[] {
  const section = PROFILE_SECTIONS.find((s) => s.id === id);
  return (section?.categories ?? [])
    .map((c) => findCategory(c))
    .filter((d): d is CategoryDef => !!d);
}

function sectionOf(category: string): SectionId | undefined {
  return PROFILE_SECTIONS.find((s) => s.categories.includes(category))?.id;
}

function buildDraft(defs: CategoryDef[], values: Values): Draft {
  const next: Draft = {};
  for (const def of defs) {
    const saved = values[def.category] ?? {};
    for (const f of def.fields) {
      const k = dkey(def.category, f.key);
      const row = saved[f.key];
      if (!row) next[k] = { state: "unset", value: emptyValue(f) };
      else if (row.state !== "value")
        next[k] = { state: row.state, value: emptyValue(f) };
      else if (f.kind === "place") {
        // The label is what shows; the stored place id is what makes it usable for a chart.
        const geo = saved["birth_place_geo"];
        const placeId =
          geo?.state === "value" && geo.value && typeof geo.value === "object"
            ? // `id` as the server stores it; `place_id` as this screen sent it before a reload.
              String((geo.value as { id?: unknown; place_id?: unknown }).id ?? (geo.value as { place_id?: unknown }).place_id ?? "")
            : "";
        next[k] = {
          state: "value",
          value: { label: String(row.value ?? ""), place_id: placeId || undefined },
        };
      } else
        next[k] = {
          state: "value",
          value: f.kind === "tags" ? parseTags(row.value) : row.value,
        };
    }
  }
  return next;
}

function promptAt(values: Values, slot: PromptSlot): PromptValue | null {
  const row = values[PROMPT_CATEGORY]?.[slot];
  return row && row.state === "value" && isPromptValue(row.value)
    ? row.value
    : null;
}

/* Answers are capped short on purpose — a prompt is a line, not an essay —
   but long enough for a real sentence about a hard subject. */
const PROMPT_MAX = 220;

/* Answer coaching, the pattern Bumble ships as "Add a bit more detail".
 *
 * It exists because the failure mode is so common: a prompt answered with
 * "Forgetting" or "Being honest" is a dead end, and on a matrimonial profile
 * a one-word answer to "On working after marriage, I think" tells a family
 * nothing at all. The nudge is advisory — it never blocks saving, because
 * someone who wants to write two words is allowed to.
 *
 * Rule-based, not AI: ADR-009 defers the AI Service, and counting words and
 * looking for something concrete does not need one. */
function AnswerCoach({ answer }: { answer: string }) {
  const { t } = useTranslation(["profile"]);
  const text = answer.trim();
  if (text.length === 0) return null;

  const words = text.split(/\s+/).filter(Boolean).length;
  // A concrete answer tends to carry a proper noun, a number, or simply
  // enough clause structure to contain a reason.
  const hasSpecific =
    /\d/.test(text) || /\s[A-Z][a-z]{2,}/.test(text) || /[,;—-]/.test(text);

  const state =
    words < 6
      ? "tooShort"
      : !hasSpecific && words < 14
        ? "addSpecific"
        : "good";

  return (
    <div className={`coach coach--${state === "good" ? "good" : "nudge"}`}>
      <span className="coach__title">
        {t(`profile:hub.prompts.coach.${state}`)}
      </span>
      <p className="coach__body">
        {t(`profile:hub.prompts.coach.${state}Body`)}
      </p>
    </div>
  );
}

export default function ProfileHubPage() {
  // [owner 2026-09-25] The loader stays at least a second, never a flash.
  const loaderHold = useLoaderHold();
  const { t, i18n } = useTranslation(["common", "profile", "discover"]);
  const router = useRouter();
  const [state, setState] = useState<PageState>({ phase: "checking" });
  const [mode, setMode] = useState<"details" | "words" | "preview">("details");
  const [lens, setLens] = useState<"before" | "after">("after");
  // 'system' on first render so server and client markup agree; corrected
  // from localStorage after mount.
  const [theme, setTheme] = useState<Theme>("system");
  const [textSize, setTextSize] = useState<TextSize>("standard");
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [sheet, setSheet] = useState<Sheet>(null);
  const [savingOutlook, setSavingOutlook] = useState(false);
  const [completeness, setCompleteness] = useState<CompletenessReport | null>(
    null,
  );
  /* Remembers the milestone already reached, so crossing one can be marked
     the moment it happens. The research is specific about this: reward the
     completion of a meaningful milestone, not a click — and "you are now
     discoverable" is the only moment on this screen that genuinely changes
     what the product does for you. */
  const reachedRef = useRef<number>(-1);
  const [justReached, setJustReached] = useState<number | null>(null);
  // The owner's spoken introduction, recorded beside their photos.
  const [voiceIntroUrl, setVoiceIntroUrl] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft>({});
  const [promptDraft, setPromptDraft] = useState<PromptValue>({ q: "", a: "" });
  const [saving, setSaving] = useState(false);
  const [sheetError, setSheetError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const pressTimer = useRef<number | null>(null);
  const pressStart = useRef<{ x: number; y: number } | null>(null);
  const suppressClick = useRef(false);

  /* [DEC-V1-019] Whose profile this screen edits: the member's own, or one
     they created for their son or daughter who has not taken it over yet. */
  const [managing, setManagingState] = useState<{
    account_id: string;
    name: string;
  } | null>(null);
  const [me, setMe] = useState<Session | null>(null);
  const [memberView, setMemberView] = useState(false);
  // Leaving the screen stops acting on the child's profile.
  useEffect(() => () => setManaging(null), []);
  /* The Details tab speaks to the candidate ("What you studied"). When a
     parent is filling in their child's profile it names the child instead —
     `hub.for.*` variants, falling back to the usual text. */
  function optionLabel(key: string, opt: string): string {
    const them = `profile:option.${key}.${opt}Them`;
    if (managing && i18n.exists(them)) return t(them);
    return t(`profile:option.${key}.${opt}`);
  }

  /* Field labels, with the same managed-mode wording ("A few lines about them"). */
  function fieldLabel(labelKey: string): string {
    if (managing && i18n.exists(`profile:${labelKey}Them`))
      return t(`profile:${labelKey}Them`);
    return t(`profile:${labelKey}`);
  }

  function hubText(key: string): string {
    if (managing) {
      const forKey = `profile:hub.for.${key}`;
      if (i18n.exists(forKey))
        return t(forKey, { name: managing.name.split(" ")[0] });
    }
    return t(`profile:hub.${key}`);
  }

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setTheme(getStoredTheme());
    setTextSize(getStoredTextSize());
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    let active = true;
    (async () => {
      const session: Session | null = await requireSession();
      if (!active) return;
      if (!session) {
        // requireSession() has already handed off to the ForKhatri entrance (TR16).
        return;
      }
      setMe(session);
      // A profile this person created for their child: named in the URL, or —
      // for a parent with no profile of their own — the one they manage.
      const wanted = new URLSearchParams(window.location.search).get("manage");
      // [DEC-V1-027] Someone who is not a candidate has their own member
      // profile here; the child's profile they made opens with ?manage=.
      if (!session.own_profile && !wanted) {
        setMemberView(true);
        return;
      }
      const target =
        session.managed_profiles.find((m) => m.account_id === wanted) ??
        (!session.own_profile ? session.managed_profiles[0] : undefined);
      if (target) {
        setManaging(target.account_id);
        setManagingState({ account_id: target.account_id, name: target.name });
        setMode((m) => (m === "words" ? "details" : m));
      }
      const profile = await getOwnProfile();
      if (!active) return;
      if (!profile) {
        // A parent or relative helping someone else has no candidate profile of
        // their own; they belong in that candidate's circle, not the wizard.
        const contexts = await getContexts();
        if (!active) return;
        router.replace(
          contexts?.circles.length ? "/circle" : "/profile/create",
        );
        return;
      }
      const [values, photos, voice, report] = await Promise.all([
        getAllAttributeValues(),
        listPhotos(),
        getVoiceIntro(),
        getCompleteness().catch(() => null),
      ]);
      if (!active) return;
      setState({ phase: "ready", profile, values, photos });
      setCompleteness(report);
      setVoiceIntroUrl(voice);
      // Deep link from the completeness screen: /me?edit=<category> opens that sheet.
      const editDef = findCategory(
        new URLSearchParams(window.location.search).get("edit") ?? "",
      );
      if (editDef) {
        const sid = sectionOf(editDef.category);
        if (sid) {
          setDraft(buildDraft(sectionDefs(sid), values));
          setSheet({ kind: "section", id: sid });
        }
        window.history.replaceState(null, "", "/me");
      }
    })();
    return () => {
      active = false;
    };
  }, [router]);

  useEffect(() => {
    if (!sheet) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setSheet(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sheet]);

  /* Three real milestones, not a percentage of fields. Each one changes
     something concrete: the profile exists, it appears in search, it is
     filled in enough to match well. */
  const milestones = [
    { id: "saved", done: completeness?.existence_complete ?? true },
    { id: "discoverable", done: !!completeness?.discoverability_complete },
    {
      id: "complete",
      done:
        !!completeness &&
        completeness.enhanced_filled_categories >=
          completeness.enhanced_total_categories,
    },
  ];
  const reached = milestones.filter((m) => m.done).length;

  /* Never zero: reaching this screen means the profile is saved. That is the
     endowed-progress effect, and here it is simply true. */
  const enhancedShare = completeness
    ? completeness.enhanced_filled_categories /
      Math.max(1, completeness.enhanced_total_categories)
    : 0;
  const pct = Math.round(
    ((reached + enhancedShare) / (milestones.length + 1)) * 100,
  );

  /* Mark the crossing once, when it happens, and never on first load. */
  useEffect(() => {
    if (!completeness) return;
    if (reachedRef.current === -1) {
      reachedRef.current = reached;
      return;
    }
    if (reached > reachedRef.current) {
      setJustReached(reached);
      reachedRef.current = reached;
      const timer = window.setTimeout(() => setJustReached(null), 6000);
      return () => window.clearTimeout(timer);
    }
    reachedRef.current = reached;
  }, [completeness, reached]);

  if (memberView && me) {
    return <MemberMe session={me} />;
  }

  if (state.phase === "checking" || loaderHold) {
    return (
      <main className="screen screen--centered">
        <SacredLoader />
      </main>
    );
  }

  const { profile, values, photos } = state;
  const outlookAnswers: OutlookAnswers = readOutlook(values);

  /* The activity writes one category in a single PATCH, like every other
     editor here — ten keys, one request. */
  async function saveOutlook(answers: OutlookAnswers) {
    setSavingOutlook(true);
    /* Every dimension is sent, not just the answered ones. A question that
       was answered before and skipped now has to be actively cleared —
       omitting it would leave the old answer standing on the profile, which
       is exactly the "said something they did not say" problem. `declined`
       is the state that clears a stored value. */
    await persist(
      OUTLOOK_CATEGORY,
      Object.fromEntries(
        OUTLOOK.map((d) => [
          d.id,
          answers[d.id]
            ? { state: "value" as AttributeState, value: answers[d.id] }
            : { state: "declined" as AttributeState },
        ]),
      ),
    );
    setSavingOutlook(false);
  }

  function tagLabel(tag: string): string {
    return INTEREST_TAGS.includes(tag) ? t(`profile:tag.${tag}`) : tag;
  }

  function formatField(field: FieldDef, value: AttributeValue): string | null {
    if (value === null || value === undefined || value === "") return null;
    if (field.kind === "select")
      return t(`profile:option.${field.key}.${String(value)}`);
    if (field.kind === "time") return formatClockTime(String(value), i18n.language);
    if (field.kind === "tags") {
      const tags = parseTags(value);
      return tags.length ? tags.map(tagLabel).join(", ") : null;
    }
    if (field.kind === "ageRange" && typeof value === "object") {
      const { min, max } = value as {
        min?: number | null;
        max?: number | null;
      };
      if (!min && !max) return null;
      return t("profile:hub.ageRange", { min: min ?? "–", max: max ?? "–" });
    }
    return String(value);
  }

  function summaryOf(def: CategoryDef): string | null {
    const attrs = values[def.category] ?? {};
    const parts = def.fields
      .map((f) =>
        attrs[f.key]?.state === "value"
          ? formatField(f, attrs[f.key].value)
          : null,
      )
      .filter((p): p is string => !!p);
    return parts.length ? parts.join(" · ") : null;
  }

  function applyLocal(
    category: string,
    payload: Record<string, { state: AttributeState; value?: AttributeValue }>,
  ) {
    setState((prev) => {
      if (prev.phase !== "ready") return prev;
      const merged: CategoryAttributes = { ...(prev.values[category] ?? {}) };
      for (const [key, entry] of Object.entries(payload)) {
        merged[key] = {
          state: entry.state,
          value: entry.state === "value" ? (entry.value ?? null) : null,
        };
      }
      return { ...prev, values: { ...prev.values, [category]: merged } };
    });
  }

  async function persist(
    category: string,
    payload: Record<string, { state: AttributeState; value?: AttributeValue }>,
  ) {
    setSaving(true);
    setSheetError(null);
    const outcome = await updateCategoryAttributes(category, payload);
    setSaving(false);
    if (!outcome.ok) {
      setSheetError(
        t(
          outcome.kind === "network"
            ? "profile:error.network"
            : "profile:editor.saveError",
        ),
      );
      return;
    }
    applyLocal(category, payload);
    setSheet(null);
  }

  async function refreshPhotos() {
    const next = await listPhotos();
    setState((prev) =>
      prev.phase !== "ready"
        ? prev
        : {
            ...prev,
            photos: next,
            profile: {
              ...prev.profile,
              photo_url:
                next.find((p) => p.is_primary)?.url ?? prev.profile.photo_url,
            },
          },
    );
  }

  async function onFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    setFileInputKey((k) => k + 1);
    if (!file) return;
    setUploading(true);
    setPhotoError(null);
    const outcome = await uploadPhoto(file);
    setUploading(false);
    if (!outcome.ok) {
      setPhotoError(outcome.message ?? t("profile:error.network"));
      return;
    }
    await refreshPhotos();
  }

  async function onPhotoAction(action: "main" | "remove", id: string) {
    setSaving(true);
    setSheetError(null);
    const outcome =
      action === "main" ? await setPrimaryPhoto(id) : await deletePhoto(id);
    setSaving(false);
    if (!outcome.ok) {
      setSheetError(outcome.message ?? t("profile:editor.saveError"));
      return;
    }
    await refreshPhotos();
    setSheet(null);
  }

  async function commitOrder(next: Photo[]) {
    setState((prev) =>
      prev.phase !== "ready"
        ? prev
        : {
            ...prev,
            photos: next.map((p, i) => ({ ...p, is_primary: i === 0 })),
            profile: {
              ...prev.profile,
              photo_url: next[0]?.url ?? prev.profile.photo_url,
            },
          },
    );
    const outcome = await reorderPhotos(next.map((p) => p.id));
    if (!outcome.ok) {
      setPhotoError(outcome.message ?? t("profile:editor.saveError"));
      await refreshPhotos();
    }
  }

  function movePhoto(from: number, to: number) {
    if (from < 0 || to < 0 || to >= photos.length || from === to) return;
    const next = [...photos];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    void commitOrder(next);
  }

  // Long-press (350 ms) then drag to reorder — Bumble's pattern. Moving more
  // than 8 px before the press completes is treated as a scroll and cancels
  // it; the photo sheet's Move buttons are the non-drag alternative.
  function clearPress() {
    if (pressTimer.current !== null) window.clearTimeout(pressTimer.current);
    pressTimer.current = null;
    pressStart.current = null;
  }

  function onPhotoPointerDown(
    e: React.PointerEvent<HTMLButtonElement>,
    id: string,
  ) {
    // A finished drag never produces a click, so the suppression flag from
    // the previous gesture must be cleared here — otherwise the first real
    // tap after any reorder is silently swallowed (found live).
    suppressClick.current = false;
    pressStart.current = { x: e.clientX, y: e.clientY };
    const target = e.currentTarget;
    const pointerId = e.pointerId;
    pressTimer.current = window.setTimeout(() => {
      suppressClick.current = true;
      setDragId(id);
      setDropIndex(photos.findIndex((p) => p.id === id));
      try {
        target.setPointerCapture(pointerId);
      } catch {
        // The pointer may already be released or cancelled; the drag still
        // tracks pointermove events delivered to the slot itself.
      }
    }, 350);
  }

  function onPhotoPointerMove(e: React.PointerEvent<HTMLButtonElement>) {
    if (!dragId) {
      const start = pressStart.current;
      if (start && Math.hypot(e.clientX - start.x, e.clientY - start.y) > 8)
        clearPress();
      return;
    }
    const over = document
      .elementFromPoint(e.clientX, e.clientY)
      ?.closest<HTMLElement>("[data-photo-index]");
    if (over)
      setDropIndex(
        Math.min(Number(over.dataset.photoIndex), photos.length - 1),
      );
  }

  function onPhotoPointerUp() {
    clearPress();
    if (dragId !== null && dropIndex !== null) {
      movePhoto(
        photos.findIndex((p) => p.id === dragId),
        dropIndex,
      );
    }
    setDragId(null);
    setDropIndex(null);
  }

  function openSection(id: SectionId) {
    setDraft(buildDraft(sectionDefs(id), values));
    setTagInput("");
    setSheetError(null);
    setSheet({ kind: "section", id });
  }

  function openPrompt(slot: PromptSlot) {
    setPromptDraft(promptAt(values, slot) ?? { q: "", a: "" });
    setSheetError(null);
    setSheet({ kind: "prompt", slot });
  }

  function payloadFor(
    def: CategoryDef,
  ): Record<string, { state: AttributeState; value?: AttributeValue }> {
    const payload: Record<
      string,
      { state: AttributeState; value?: AttributeValue }
    > = {};
    for (const f of def.fields) {
      const entry = draft[dkey(def.category, f.key)];
      if (!entry || entry.state !== "value") continue;
      if (f.kind === "place") {
        // Only a place picked from the list is sent; the server fills in
        // its label, coordinates and time zone.
        const v = entry.value as PlaceValue | string;
        if (typeof v === "object" && v?.place_id) {
          payload.birth_place_geo = { state: "value", value: { place_id: v.place_id } };
          payload[f.key] = { state: "value", value: v.label };
        }
        continue;
      }
      if (f.kind === "time" && draft[dkey(def.category, "birth_time_accuracy")]?.value === "unknown") {
        payload[f.key] = { state: "declined", value: null };
        continue;
      }
      if (f.kind === "ageRange") {
        const v = (entry.value ?? {}) as { min?: unknown; max?: unknown };
        const min = Number(v.min) || null;
        const max = Number(v.max) || null;
        if (min || max)
          payload[f.key] = { state: "value", value: { min, max } };
      } else if (f.kind === "tags") {
        const tags = parseTags(entry.value);
        if (tags.length) payload[f.key] = { state: "value", value: tags };
      } else if (typeof entry.value === "number") {
        payload[f.key] = { state: "value", value: entry.value };
      } else if (typeof entry.value === "string" && entry.value.trim()) {
        payload[f.key] = { state: "value", value: entry.value.trim() };
      }
    }
    return payload;
  }

  /* One Save for the section; underneath, one PATCH per storage category
     that actually changed. */
  async function saveSection(defs: CategoryDef[]) {
    // A stated accuracy needs a time, unless the time is unknown.
    const accuracy = draft[dkey("horoscope", "birth_time_accuracy")];
    const time = draft[dkey("horoscope", "birth_time")];
    if (
      defs.some((d) => d.category === "horoscope") &&
      accuracy?.state === "value" &&
      accuracy.value !== "unknown" &&
      !(time?.state === "value" && typeof time.value === "string" && time.value)
    ) {
      setSheetError(t("profile:editor.birthTimeNeeded"));
      return;
    }
    const work = defs
      .map((def) => [def, payloadFor(def)] as const)
      .filter(([, payload]) => Object.keys(payload).length > 0);
    if (work.length === 0) {
      setSheet(null);
      return;
    }
    setSaving(true);
    setSheetError(null);
    for (const [def, payload] of work) {
      const outcome = await updateCategoryAttributes(def.category, payload);
      if (!outcome.ok) {
        setSaving(false);
        setSheetError(
          t(
            outcome.kind === "network"
              ? "profile:error.network"
              : "profile:editor.saveError",
          ),
        );
        return;
      }
      applyLocal(def.category, payload);
    }
    setSaving(false);
    setSheet(null);
  }

  /* "Prefer not to say" for the parts of the section not yet answered;
     what is already answered stays. */
  async function hideSection(defs: CategoryDef[]) {
    setSaving(true);
    for (const def of defs.filter(
      (d) => statusOf(values, d.category) === "empty",
    )) {
      const payload = Object.fromEntries(
        def.fields.map((f) => [
          f.key,
          { state: "declined" as const, value: null },
        ]),
      );
      const outcome = await updateCategoryAttributes(def.category, payload);
      if (outcome.ok) applyLocal(def.category, payload);
    }
    setSaving(false);
    setSheet(null);
  }

  const nextEmpty = ALL_CATEGORIES_IN_ORDER.find(
    (c) => statusOf(values, c) === "empty",
  );
  // [D15] The easiest unanswered question; a declined (hidden) one counts as answered.
  const nextEasy = EASY_NEXT.map(([c, k]) => findField(c, k)).find(
    (f): f is FieldDef => {
      if (!f) return false;
      const row = values[f.category]?.[f.key];
      return !row || (row.state !== "value" && row.state !== "declined");
    },
  );
  const nextCategory = nextEasy?.category ?? nextEmpty;

  const sheetDefs = sheet?.kind === "section" ? sectionDefs(sheet.id) : [];
  const sheetItems = sheetDefs.flatMap((def) =>
    def.fields.map((f) => ({ def, f, dk: dkey(def.category, f.key) })),
  );
  const usedQuestions = PROMPT_SLOTS.filter(
    (s) => sheet?.kind !== "prompt" || s !== sheet.slot,
  )
    .map((s) => promptAt(values, s)?.q)
    .filter(Boolean);
  const sheetPhoto =
    sheet?.kind === "photo" ? photos.find((p) => p.id === sheet.id) : undefined;

  function renderVoice() {
    return <VoiceIntro key="voice" initialUrl={voiceIntroUrl} />;
  }

  /* The person comes first, as on Hinge, Bumble and Shaadi: a photo grid
     (one large slot and five small), then the name. With no photo yet the
     large slot itself is the invitation. */
  function renderPhotos() {
    return (
      <div className="me-photos" aria-label={t("profile:hub.photos.title")}>
        <div className="photo-grid me-pgrid">
          {Array.from({ length: 6 }, (_, i) => {
            const photo = photos[i];
            if (photo) {
              return (
                <button
                  key={photo.id}
                  type="button"
                  data-photo-index={i}
                  className={`photo-slot${i === 0 ? " photo-slot--main" : ""}${dragId === photo.id ? " is-dragging" : ""}${dragId && dropIndex === i && dragId !== photo.id ? " is-drop-target" : ""}`}
                  aria-label={`${t("profile:hub.photos.title")} ${i + 1}${photo.is_primary ? ` · ${t("profile:hub.photos.main")}` : ""}`}
                  onPointerDown={(e) => onPhotoPointerDown(e, photo.id)}
                  onPointerMove={onPhotoPointerMove}
                  onPointerUp={onPhotoPointerUp}
                  onPointerCancel={onPhotoPointerUp}
                  onContextMenu={(e) => e.preventDefault()}
                  onClick={() => {
                    if (suppressClick.current) {
                      suppressClick.current = false;
                      return;
                    }
                    setSheetError(null);
                    setSheet({ kind: "photo", id: photo.id });
                  }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={resolveMediaUrl(photo.url) ?? ""} alt="" />
                  {photo.is_primary && (
                    <span className="photo-slot__badge">
                      {t("profile:hub.photos.main")}
                    </span>
                  )}
                </button>
              );
            }
            const isNext = i === photos.length;
            return (
              <button
                key={`empty-${i}`}
                type="button"
                className={`photo-slot photo-slot--empty${i === 0 ? " photo-slot--main me-first" : ""}`}
                aria-label={
                  i === 0
                    ? t("profile:hub.photos.firstPhoto")
                    : t("profile:hub.photos.add")
                }
                disabled={!isNext || uploading}
                onClick={() => fileRef.current?.click()}
              >
                {isNext && uploading ? (
                  <span className="caption">
                    {t("profile:hub.photos.uploading")}
                  </span>
                ) : i === 0 ? (
                  <span className="me-first__in">
                    <Icon name="camera" />
                    <span className="me-first__title">
                      {t("profile:hub.photos.firstPhoto")}
                    </span>
                  </span>
                ) : (
                  <span aria-hidden="true">+</span>
                )}
              </button>
            );
          })}
        </div>
        {photos.length > 1 && (
          <p className="me-quiet">{t("profile:hub.photosReorderHint")}</p>
        )}
        {photoError && (
          <p className="form__error" role="status">
            {photoError}
          </p>
        )}
        <input
          key={fileInputKey}
          ref={fileRef}
          type="file"
          name="photo"
          accept="image/jpeg,image/png,image/webp"
          hidden
          onChange={onFileChosen}
        />
      </div>
    );
  }

  const pencil = <Icon name="edit" size={16} />;

  /* A written prompt: the question quiet, the answer in the serif. Short
     answers are set in italic; long ones only on their first line. */
  function renderPromptEdit(slot: PromptSlot) {
    const p = promptAt(values, slot);
    if (!p) return null;
    return (
      <button
        key={slot}
        type="button"
        className="me-prompt"
        onClick={() => openPrompt(slot)}
      >
        <span className="me-prompt__q">
          {t(`profile:hub.prompts.q.${p.q}`)}
        </span>
        <span
          className={`me-prompt__a${p.a.length <= 90 ? " is-short" : ""}`}
        >
          {p.a}
        </span>
        <span className="me-edit">
          {pencil}
          {t("profile:hub.edit")}
        </span>
      </button>
    );
  }

  /* The ten quick choices: one thing you do once, then see on your
     profile. */
  function renderOutlook() {
    const answered = OUTLOOK.filter((d) => outlookAnswers[d.id]).length;
    const complete = answered === OUTLOOK.length;
    return (
      <section
        key="outlook"
        className="me-block"
        aria-label={t("profile:outlook.title")}
      >
        <div className="me-block__head">
          <h3 className="me-block__title">{t("profile:outlook.title")}</h3>
          {answered > 0 && !complete && (
            <span className="me-count">
              {answered}/{OUTLOOK.length}
            </span>
          )}
        </div>
        {answered === 0 && (
          <p className="me-quiet">{t("profile:outlook.intro")}</p>
        )}
        {answered > 0 && (
          <ul className="portrait portrait--compact">
            {OUTLOOK.filter((d) => outlookAnswers[d.id]).map((d) => (
              <li key={d.id} className="portrait__tile">
                <OutlookScene id={outlookAnswers[d.id]} />
                <span className="portrait__label">
                  {t(`profile:outlook.pole.${outlookAnswers[d.id]}`)}
                </span>
              </li>
            ))}
          </ul>
        )}
        <button
          type="button"
          className="me-textbtn"
          onClick={() => setSheet({ kind: "outlook" })}
        >
          {answered === 0
            ? t("profile:outlook.cta")
            : complete
              ? t("profile:outlook.redo")
              : t("profile:outlook.resume")}
          <Icon name="caretRight" size={16} className="me-chev" />
        </button>
      </section>
    );
  }

  /* One section of the biodata: its name, then what it says. Filled values
     lead; an empty section recedes to its one-line hint. "2/6" appears only
     while a section is part filled. */
  function renderSectionEdit(id: SectionId) {
    const defs = sectionDefs(id);
    if (defs.length === 0) return null;
    /* Every field under its own label — never the storage category's name,
       which used to put tiles called "Education", "Profession" and
       "Education & career" inside the section "Education & career". */
    const facts = defs.flatMap((def) =>
      def.fields.map((f) => {
        const row = values[def.category]?.[f.key];
        return {
          key: dkey(def.category, f.key),
          state: row?.state ?? "unset",
          text: row?.state === "value" ? formatField(f, row.value) : null,
        };
      }),
    );
    const filled = facts.filter((x) => x.text).length;
    const missing = facts.filter((x) => x.state === "unset").length;
    const summary = facts
      .filter((x) => x.text)
      .map((x) => x.text)
      .join(" · ");
    return (
      <button
        key={id}
        type="button"
        className={`me-sec${filled === 0 ? " is-empty" : ""}`}
        aria-label={`${hubText(`section.${id}`)} · ${
          filled === 0
            ? t("profile:hub.addDetails")
            : missing > 0
              ? t("profile:hub.addMore", { count: missing })
              : t("profile:hub.edit")
        }`}
        onClick={() => openSection(id)}
      >
        <span className="me-sec__title">
          <span className="me-long">{hubText(`section.${id}`)}</span>
          <span className="me-short">
            {i18n.exists(`profile:hub.sectionShortTitle.${id}`)
              ? t(`profile:hub.sectionShortTitle.${id}`)
              : hubText(`section.${id}`)}
          </span>
          {id === "partner" && (
            <Icon name="lock" size={16} />
          )}
        </span>
        {filled > 0 ? (
          <span className="me-sec__text">{summary}</span>
        ) : (
          <span className="me-sec__text">
            <span className="me-long">{hubText(`sectionHint.${id}`)}</span>
            <span className="me-short">
              {t(`profile:hub.sectionShortHint.${id}`)}
            </span>
          </span>
        )}
        <span className="me-sec__side">
          {filled > 0 && missing > 0 && (
            <span className="me-count">
              {filled}/{facts.length}
            </span>
          )}
          {filled === 0 ? (
            <span className="me-sec__add">
              <span className="me-long">+ {t("profile:hub.addDetails")}</span>
              <span className="me-short">+ {t("profile:hub.addShort")}</span>
            </span>
          ) : (
            <Icon name="caretRight" size={16} className="me-chev" />
          )}
        </span>
      </button>
    );
  }

  /* One age rule everywhere: the age sits in italic beside a word. When
     the name is not shown, the profession (or education, or city) is that
     word, so a bare number never stands as a title. */
  const firstOpen =
    values.openly?.first_name?.state === "value" &&
    values.openly.first_name.value === true;
  const occupationRow = values.profession?.occupation;
  const occupation =
    occupationRow?.state === "value" && occupationRow.value
      ? String(occupationRow.value)
      : null;
  const eduDef = findCategory("education");
  const education = eduDef ? summaryOf(eduDef) : null;
  const city = profile.city_locality?.split(",")[0]?.trim() || null;
  const showName = lens === "after" || firstOpen;
  const pvName = showName
    ? profile.name.split(" ")[0]
    : (occupation ?? education ?? city ?? "");
  const pvChips = (
    showName
      ? [city, education, occupation]
      : occupation
        ? [city, education]
        : education
          ? [city]
          : []
  ).filter((c): c is string => !!c);
  const initials = profile.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  /* The preview is drawn the way the real profile reads: the main photo
     full-bleed with the name set on it, then the words and the biodata. */
  function renderPreviewBlock(block: PreviewBlock, index: number) {
    if (block.kind === "photo") {
      if (block.index === 0) return null;
      const photo = photos[block.index];
      if (!photo) return null;
      return (
        <div key={`photo-${index}`} className="me-pv__photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={resolveMediaUrl(photo.url) ?? ""} alt="" />
        </div>
      );
    }
    if (block.kind === "identity") return null;
    if (block.kind === "prompt") {
      const p = promptAt(values, block.slot);
      if (!p) return null;
      return (
        <div key={block.slot} className="me-pv__prompt">
          <span className="me-prompt__q">
            {t(`profile:hub.prompts.q.${p.q}`)}
          </span>
          <p className={`me-prompt__a${p.a.length <= 90 ? " is-short" : ""}`}>
            {p.a}
          </p>
        </div>
      );
    }
    // Partner preferences are private matching filters, never shown to
    // anyone else — Hinge treats preferences the same way.
    if (block.id === "partner") return null;
    const rows = sectionDefs(block.id).flatMap((d) =>
      d.fields
        .map((f) => {
          const row = values[d.category]?.[f.key];
          return row?.state === "value"
            ? {
                key: dkey(d.category, f.key),
                label: fieldLabel(f.labelKey),
                text: formatField(f, row.value),
              }
            : null;
        })
        .filter(
          (r): r is { key: string; label: string; text: string } => !!r?.text,
        ),
    );
    if (rows.length === 0) return null;
    return (
      <div key={block.id} className="me-pv__sec">
        <h4 className="me-pv__h">{t(`profile:hub.section.${block.id}`)}</h4>
        <dl className="me-pv__dl">
          {rows.map((r) => (
            <div key={r.key} className="me-pv__row">
              <dt>{r.label}</dt>
              <dd>{r.text}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  const emptyPrompt = PROMPT_SLOTS.find((s) => !promptAt(values, s));
  const writtenPrompts = PROMPT_SLOTS.filter((s) => promptAt(values, s)).length;
  const chevronRight = <Icon name="caretRight" size={16} className="me-chev" />;

  /* Who sees what, grouped the way the preview lenses are: before you
     connect, and after. On a desktop it sits under your name; on a phone,
     after the profile. */
  function renderWho(where: "side" | "main") {
    return (
      <details className={`me-who me-who--${where}`}>
        <summary className="me-row me-who__sum">
          <Icon name="eye" className="me-row__icon" />
          <span className="me-row__body">
            <span className="me-row__title">{t("profile:hub.whoSees")}</span>
          </span>
          {chevronRight}
        </summary>
        <div className="me-who__body">
          <div className="me-who__group">
            <h4 className="me-who__h">{t("profile:hub.preview.before")}</h4>
            <p className="me-quiet">{t("profile:openly.always")}</p>
            {/* [Migration 043] What this person shows before anyone
                connects. Closed by default; each switch is one tap and
                saves at once. Only the candidate decides — never a parent
                filling it in. */}
            {!managing && (
              <div className="openly me-openly">
                        {(["first_name", "photos"] as const).map((key) => {
                          const on =
                            values.openly?.[key]?.state === "value" &&
                            values.openly?.[key]?.value === true;
                          return (
                            <label key={key} className="openly__row">
                              <span className="openly__text">
                                <span className="openly__name">
                                  {t(`profile:openly.${key}`)}
                                </span>
                                <span className="me-quiet">
                                  {t(`profile:openly.${key}Hint`)}
                                </span>
                              </span>
                              <input
                                type="checkbox"
                                role="switch"
                                className="switch"
                                checked={on}
                                disabled={saving}
                                onChange={(e) =>
                                  void persist("openly", {
                                    [key]: {
                                      state: "value",
                                      value: e.target.checked,
                                    },
                                  })
                                }
                              />
                            </label>
                          );
                        })}
                        <button
                          type="button"
                          className="openly__row openly__row--link"
                          onClick={() => setMode("words")}
                        >
                          <span className="openly__text">
                            <span className="openly__name">
                              {t("profile:openly.prompts")}
                            </span>
                            <span className="me-quiet">
                              {t("profile:openly.promptsCount", {
                                count: Object.values(
                                  values.in_my_words ?? {},
                                ).filter(
                                  (e) =>
                                    e.state === "value" &&
                                    !!e.value &&
                                    typeof e.value === "object" &&
                                    (e.value as { public?: boolean }).public ===
                                      true,
                                ).length,
                              })}
                            </span>
                          </span>
                          {chevronRight}
                        </button>
              </div>
            )}
          </div>
          <div className="me-who__group">
            <h4 className="me-who__h">{t("profile:hub.preview.after")}</h4>
            <p className="me-quiet">{t("profile:hub.part.details.hint")}</p>
            {!managing && (
              <p className="me-quiet">{t("profile:hub.part.words.hint")}</p>
            )}
            <p className="me-quiet">{t("profile:hub.photos.hint")}</p>
          </div>
          <p className="me-quiet">{hubText("partnerPrivate")}</p>
          <button
            type="button"
            className="me-textbtn"
            onClick={() => setMode("preview")}
          >
            {t("profile:hub.seeInPreview")}
          </button>
        </div>
      </details>
    );
  }

  return (
    <>
      {/* Title left, settings right. On a phone the account avatar stays in
          the header as on every screen; on a desktop the sidebar and the
          settings sheet carry the account, so your own face is not repeated
          beside the one this page is about. */}
      <header className="topbar me-top">
        <h1>
          {managing
            ? t("profile:hub.titleFor", { name: managing.name.split(" ")[0] })
            : t("profile:hub.title")}
        </h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <button
            type="button"
            className="icon-btn"
            aria-label={t("common:settings.title")}
            aria-haspopup="dialog"
            onClick={() => {
              setConfirmLogout(false);
              setSheet({ kind: "settings" });
            }}
          >
            <Icon name="settings" />
          </button>
          <span className="me-account">
            <AccountButton />
          </span>
        </div>
      </header>

      <main className={`screen me${mode === "preview" ? " is-preview" : ""}`}>
        {/* [DEC-V1-019] Say plainly whose profile this is. */}
        {managing && (
          <div className="managed-note" role="status">
            <strong>
              {t("profile:managed.editingTitle", {
                name: managing.name.split(" ")[0],
              })}
            </strong>
            <span>
              {t("profile:managed.editingBody", {
                name: managing.name.split(" ")[0],
              })}
            </span>
          </div>
        )}
        {!managing && me && <ClaimProfileNote session={me} />}

        <div className="me-grid">
          {/* The person: photos, name, and the one next step. Sticky beside
              the content on a desktop. */}
          <section className="me-grid__side me-person" aria-label={profile.name}>
            {renderPhotos()}
            <div className="me-person__id">
              <h2 className="me-person__name">
                {profile.name}{" "}
                <em className="me-person__age">
                  {ageFromDob(profile.date_of_birth)}
                </em>
              </h2>
              {city && <p className="me-person__meta">{city}</p>}
              <Link
                href="/me/completeness"
                className="me-person__pct"
                aria-label={t("profile:hub.completenessCta")}
              >
                <span
                  className="me-pct"
                  style={{ "--pct": `${pct}%` } as React.CSSProperties}
                  aria-hidden="true"
                />
                {t("profile:hub.complete", { pct })}
              </Link>
            </div>
            {justReached !== null && (
              <p className="me-hero__cheer" role="status">
                {t(
                  `profile:hub.milestone.reached.${milestones[justReached - 1]?.id}`,
                )}
              </p>
            )}
            {/* One next step. While there is no photo, the large photo slot
                above is that step, so nothing else competes with it. */}
            {photos.length > 0 && nextCategory && (
              <button
                type="button"
                className="me-row me-next"
                onClick={() => {
                  const sid = sectionOf(nextCategory);
                  if (sid) openSection(sid);
                }}
              >
                <span className="me-row__body">
                  <span className="me-row__label">{t("profile:hub.nextUp")}</span>
                  <span className="me-row__title">
                    {/* [D15] The one question itself ("Marital status"), else the section. */}
                    {nextEasy
                      ? fieldLabel(nextEasy.labelKey)
                      : hubText(`section.${sectionOf(nextCategory) ?? "basics"}`)}
                  </span>
                </span>
                {chevronRight}
              </button>
            )}
            {/* [DEC-V1-016, D15] Photo check: its own optional card — an
                invitation, never the "Next up" step — or the fact once done. */}
            {!managing && (
              // Re-checks once the first photo is added (it hides at 0).
              <PhotoCheckCard key={photos.length > 0 ? "photos" : "none"} />
            )}
            {renderWho("side")}
          </section>

          <div className="me-grid__main">
            <div
              className="me-tabs"
              role="tablist"
              aria-label={t("profile:hub.title")}
            >
              {/* The "In my words" part is the candidate's own voice: a
                  parent filling in the profile never writes it. */}
              {(managing
                ? (["details", "preview"] as const)
                : (["details", "words", "preview"] as const)
              ).map((m) => (
                <button
                  key={m}
                  type="button"
                  role="tab"
                  aria-selected={mode === m}
                  className={`me-tab${mode === m ? " is-active" : ""}`}
                  onClick={() => setMode(m)}
                >
                  {t(
                    m === "details"
                      ? "profile:hub.tabDetails"
                      : m === "words"
                        ? "profile:hub.tabWords"
                        : "profile:hub.tabPreview",
                  )}
                </button>
              ))}
            </div>

            {mode === "details" && (
              <div className="me-secs">
                {DETAILS_LAYOUT.map((block) =>
                  block.kind === "section" ? renderSectionEdit(block.id) : null,
                )}
                {/* [DEC-V1-031] The partner you hope for, in your own words —
                    read by the AI matchmaker, private like the preferences. */}
                <Link
                  href={managing ? `/me/matchmaker?manage=${managing.account_id}` : "/me/matchmaker"}
                  className="me-sec"
                >
                  <span className="me-sec__title">
                    {managing
                      ? t("discover:matchmaker.titleFor", { name: managing.name.split(" ")[0] })
                      : t("discover:matchmaker.title")}
                    <Icon name="lock" size={16} />
                  </span>
                  <span className="me-sec__text">{t("discover:matchmaker.entry.body")}</span>
                  <span className="me-sec__side">
                    <Icon name="caretRight" size={16} className="me-chev" />
                  </span>
                </Link>
              </div>
            )}

            {mode === "words" && (
              <>
                <div className="me-prompts">
                  {PROMPT_SLOTS.map((slot) => renderPromptEdit(slot))}
                  {emptyPrompt && (
                    <button
                      type="button"
                      className="me-row me-addprompt"
                      onClick={() => openPrompt(emptyPrompt)}
                    >
                      <span className="me-row__body">
                        <span className="me-row__title">
                          + {t("profile:hub.prompts.add")}
                        </span>
                        {writtenPrompts === 0 && (
                          <span className="me-quiet">
                            {t("profile:hub.prompts.emptyHint")}
                          </span>
                        )}
                      </span>
                      <span className="me-count">
                        {t("profile:hub.prompts.limit", {
                          count: writtenPrompts,
                          max: PROMPT_SLOTS.length,
                        })}
                      </span>
                    </button>
                  )}
                </div>
                <div className="me-duo">
                  {renderVoice()}
                  {renderOutlook()}
                </div>
              </>
            )}

            {mode === "preview" && (
              <div className="me-preview">
                {/* One toggle: whose eyes the preview is seen through. */}
                <button
                  type="button"
                  role="switch"
                  aria-checked={lens === "after"}
                  className="me-viewas"
                  onClick={() => setLens(lens === "before" ? "after" : "before")}
                >
                  <span className="me-viewas__label">
                    {t("profile:hub.preview.viewingAs")}
                  </span>
                  <span className="me-viewas__value">
                    {t(
                      lens === "before"
                        ? "profile:hub.preview.asBefore"
                        : "profile:hub.preview.asAfter",
                    )}
                  </span>
                  <Icon name="swap" size={16} />
                </button>

                <div className="me-phone">
                  <div className="me-pv">
                    <div className="me-pv__hero">
                      {photos[0] ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={resolveMediaUrl(photos[0].url) ?? ""} alt="" />
                      ) : (
                        <>
                          {/* No photo yet: initials on a soft wash, and the
                              one thing to do about it. */}
                          <span className="me-pv__nophoto" aria-hidden="true">
                            {initials}
                          </span>
                          <button
                            type="button"
                            className="me-pv__addphoto"
                            onClick={() => fileRef.current?.click()}
                          >
                            <Icon name="camera" size={16} />
                            {t("profile:hub.preview.addPhotoHere")}
                          </button>
                        </>
                      )}
                      <div className="me-pv__over">
                        <span className="me-pv__name">
                          {pvName}
                          {" "}
                          <em className="me-pv__age">
                            {ageFromDob(profile.date_of_birth)}
                          </em>
                        </span>
                        {pvChips.length > 0 && (
                          <span className="me-pv__chips">
                            {pvChips.map((c) => (
                              <span key={c} className="me-pv__chip">
                                {c}
                              </span>
                            ))}
                          </span>
                        )}
                      </div>
                    </div>
                    {lens === "before" ? (
                      <p className="me-pv__lock">
                        <Icon name="lock" size={16} />
                        {t("discover:identityProtected")}
                      </p>
                    ) : (
                      PREVIEW_LAYOUT.map((block, i) =>
                        renderPreviewBlock(block, i),
                      )
                    )}
                  </div>
                </div>
                <p className="me-quiet me-pv__note">
                  {t(
                    lens === "before"
                      ? "profile:hub.preview.beforeNote"
                      : "profile:hub.preview.afterNote",
                  )}
                </p>
              </div>
            )}

            {mode !== "preview" && (
              <>
                {renderWho("main")}

                {/* The way on to the next part: a quiet full-width row. */}
                <button
                  type="button"
                  className="me-row me-nextpart"
                  onClick={() =>
                    setMode(
                      mode === "details" && !managing ? "words" : "preview",
                    )
                  }
                >
                  <span className="me-row__body">
                    <span className="me-row__title">
                      {t(
                        mode === "details" && !managing
                          ? "profile:hub.part.toWords"
                          : "profile:hub.part.toPreview",
                      )}
                    </span>
                  </span>
                </button>
              </>
            )}
          </div>
        </div>
      </main>

      {sheet && (
        <div className="sheet-backdrop" onClick={() => setSheet(null)}>
          <div
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sheet-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sheet__handle" aria-hidden="true" />
            <div className="sheet__head">
              <h2 id="sheet-title" className="h2">
                {sheet.kind === "section"
                  ? hubText(`section.${sheet.id}`)
                  : sheet.kind === "photo"
                    ? t("profile:hub.photos.title")
                    : sheet.kind === "outlook"
                      ? t("profile:outlook.title")
                      : sheet.kind === "settings"
                        ? t("common:settings.title")
                        : t("profile:hub.section.prompts")}
              </h2>
              <button
                type="button"
                className="icon-btn"
                aria-label={t("common:action.cancel")}
                onClick={() => setSheet(null)}
              >
                <Icon name="close" />
              </button>
            </div>

            {sheet.kind === "outlook" && (
              <OutlookGame
                initial={outlookAnswers}
                saving={savingOutlook}
                onSave={(a) => void saveOutlook(a)}
                onCancel={() => setSheet(null)}
              />
            )}

            {sheet.kind === "settings" && (
              <>
                {/* [Owner rule: collapse option fields] Five languages no longer
                    fit a three-column row, so the choice is one dropdown, each
                    language written in its own script. */}
                <label className="date-field">
                  <span className="label">{t("common:settings.language")}</span>
                  <select
                    className="field__input select"
                    value={SUPPORTED_LANGUAGES.includes(i18n.language as Language) ? i18n.language : "en"}
                    onChange={(e) => {
                      const lang = e.target.value as Language;
                      void i18n.changeLanguage(lang);
                      setPreferredLanguage(lang);
                    }}
                  >
                    {SUPPORTED_LANGUAGES.map((lang) => (
                      <option key={lang} value={lang}>
                        {t(`common:language.${lang}`)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="label" style={{ marginTop: 16 }}>
                  {t("common:settings.theme")}
                </div>
                <div className="segmented segmented--3" role="radiogroup">
                  {THEME_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`segmented__opt${theme === opt ? " is-active" : ""}`}
                      aria-pressed={theme === opt}
                      onClick={() => {
                        setTheme(opt);
                        setPreferredTheme(opt);
                      }}
                    >
                      {t(`common:settings.themeOption.${opt}`)}
                    </button>
                  ))}
                </div>
                <div className="label" style={{ marginTop: 16 }}>
                  {t("common:settings.textSize")}
                </div>
                <div className="segmented segmented--3" role="radiogroup" aria-label={t("common:settings.textSize")}>
                  {TEXT_SIZES.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`segmented__opt${textSize === opt ? " is-active" : ""}`}
                      aria-pressed={textSize === opt}
                      onClick={() => {
                        setTextSize(opt);
                        setPreferredTextSize(opt);
                      }}
                    >
                      {t(`common:settings.textSizeOption.${opt}`)}
                    </button>
                  ))}
                </div>
                {/* The account links from the header avatar, which a desktop
                    does not show on this page. */}
                <nav className="me-sheetlinks">
                  <Link href="/profile/create?for=child" className="me-row">
                    <span className="me-row__body">
                      <span className="me-row__title">
                        {t("common:account.createForChild")}
                      </span>
                    </span>
                    <Icon name="caretRight" size={16} className="me-chev" />
                  </Link>
                  <a href={entranceUrl()} className="me-row">
                    <span className="me-row__body">
                      <span className="me-row__title">
                        {t("common:platform.backToHub")}
                      </span>
                    </span>
                    <Icon name="caretRight" size={16} className="me-chev" />
                  </a>
                </nav>
                <div className="sheet__stack" style={{ marginTop: 16 }}>
                  {confirmLogout ? (
                    <>
                      <p className="caption" style={{ margin: 0 }}>
                        {t("common:settings.logOutConfirm")}
                      </p>
                      <button
                        type="button"
                        className="sheet__danger"
                        onClick={() => void logOut()}
                      >
                        {t("common:action.logOut")}
                      </button>
                      <button
                        type="button"
                        className="quick-pick__chip"
                        onClick={() => setConfirmLogout(false)}
                      >
                        {t("common:action.cancel")}
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="sheet__danger"
                      onClick={() => setConfirmLogout(true)}
                    >
                      {t("common:action.logOut")}
                    </button>
                  )}
                </div>
              </>
            )}

            {sheet.kind === "photo" && sheetPhoto && (
              <>
                <div className="sheet__photo">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={resolveMediaUrl(sheetPhoto.url) ?? ""} alt="" />
                </div>
                <div className="sheet__stack">
                  <div className="sheet__row">
                    <button
                      type="button"
                      className="quick-pick__chip"
                      disabled={saving || photos.indexOf(sheetPhoto) === 0}
                      onClick={() =>
                        movePhoto(
                          photos.indexOf(sheetPhoto),
                          photos.indexOf(sheetPhoto) - 1,
                        )
                      }
                    >
                      ← {t("profile:hub.photos.moveEarlier")}
                    </button>
                    <button
                      type="button"
                      className="quick-pick__chip"
                      disabled={
                        saving ||
                        photos.indexOf(sheetPhoto) === photos.length - 1
                      }
                      onClick={() =>
                        movePhoto(
                          photos.indexOf(sheetPhoto),
                          photos.indexOf(sheetPhoto) + 1,
                        )
                      }
                    >
                      {t("profile:hub.photos.moveLater")} →
                    </button>
                  </div>
                  {!sheetPhoto.is_primary && (
                    <button
                      type="button"
                      className="cta"
                      disabled={saving}
                      onClick={() => void onPhotoAction("main", sheetPhoto.id)}
                    >
                      {t("profile:hub.photos.makeMain")}
                    </button>
                  )}
                  <button
                    type="button"
                    className="sheet__danger"
                    disabled={saving}
                    onClick={() => void onPhotoAction("remove", sheetPhoto.id)}
                  >
                    {t("profile:hub.photos.remove")}
                  </button>
                </div>
              </>
            )}

            {sheet.kind === "section" && sheetItems.length > 0 && (
              <>
                {sheetItems.map(({ f, dk }) => {
                  const entry = draft[dk];
                  return (
                    <div key={f.key} className="sheet__field">
                      {sheetItems.length > 1 && (
                        <div className="label">{fieldLabel(f.labelKey)}</div>
                      )}
                      {f.kind === "select" && (f.options?.length ?? 0) >= 12 ? (
                        // A long list (the 27 nakshatras, the 12 rashis) reads better as one
                        // dropdown than as chips. [D16] Rashi was 12 open chips; the collapse
                        // rule puts it in a dropdown like the other long single choices.
                        <select
                          className="field__input"
                          name={f.key}
                          aria-label={fieldLabel(f.labelKey)}
                          value={entry?.state === "value" && typeof entry.value === "string" ? entry.value : ""}
                          disabled={saving}
                          onChange={(e) =>
                            setDraft((d) => ({
                              ...d,
                              [dk]: e.target.value
                                ? { state: "value", value: e.target.value }
                                : { state: "unset", value: "" },
                            }))
                          }
                        >
                          <option value="">{t("profile:editor.selectPlaceholder")}</option>
                          {(f.options ?? []).map((opt) => (
                            <option key={opt} value={opt}>
                              {optionLabel(f.key, opt)}
                            </option>
                          ))}
                        </select>
                      ) : f.kind === "time" ? (
                        draft[dkey("horoscope", "birth_time_accuracy")]?.value === "unknown" ? (
                          <p className="caption">{t("profile:editor.birthTimeUnknown")}</p>
                        ) : (
                          <input
                            className="field__input field__input--time"
                            type="time"
                            name={f.key}
                            step={60}
                            aria-label={fieldLabel(f.labelKey)}
                            value={typeof entry?.value === "string" ? entry.value : ""}
                            disabled={saving}
                            onChange={(e) =>
                              setDraft((d) => ({
                                ...d,
                                [dk]: { state: "value", value: e.target.value },
                              }))
                            }
                          />
                        )
                      ) : f.kind === "place" ? (
                        <PlaceSearch
                          label={fieldLabel(f.labelKey)}
                          disabled={saving}
                          value={
                            entry?.state === "value" && entry.value
                              ? typeof entry.value === "string"
                                ? { label: entry.value }
                                : (entry.value as PlaceValue)
                              : null
                          }
                          onChange={(next) =>
                            setDraft((d) => ({
                              ...d,
                              [dk]: next
                                ? { state: "value", value: next }
                                : { state: "unset", value: "" },
                            }))
                          }
                        />
                      ) : f.kind === "select" ? (
                        <div className="quick-pick__chips">
                          {(f.options ?? []).map((opt) => {
                            const active =
                              entry?.state === "value" && entry.value === opt;
                            return (
                              <button
                                key={opt}
                                type="button"
                                className={`quick-pick__chip${active ? " quick-pick__chip--active" : ""}`}
                                disabled={saving}
                                onClick={() =>
                                  setDraft((d) => ({
                                    ...d,
                                    [dk]: { state: "value", value: opt },
                                  }))
                                }
                              >
                                {optionLabel(f.key, opt)}
                              </button>
                            );
                          })}
                        </div>
                      ) : f.kind === "tags" ? (
                        (() => {
                          const chosen = parseTags(entry?.value);
                          const full = chosen.length >= MAX_TAGS;
                          const setTags = (next: string[]) =>
                            setDraft((d) => ({
                              ...d,
                              [dk]: { state: "value", value: next },
                            }));
                          const toggle = (tag: string) =>
                            setTags(
                              chosen.includes(tag)
                                ? chosen.filter((c) => c !== tag)
                                : full
                                  ? chosen
                                  : [...chosen, tag],
                            );
                          const addCustom = () => {
                            const tag = toTagKey(tagInput);
                            if (tag && !chosen.includes(tag) && !full)
                              setTags([...chosen, tag]);
                            setTagInput("");
                          };
                          return (
                            <>
                              <div className="label">
                                {t("profile:hub.tags.pick", {
                                  max: MAX_TAGS,
                                  count: chosen.length,
                                })}
                              </div>
                              <div className="quick-pick__chips">
                                {[
                                  ...INTEREST_TAGS,
                                  ...chosen.filter(
                                    (c) => !INTEREST_TAGS.includes(c),
                                  ),
                                ].map((tag) => {
                                  const active = chosen.includes(tag);
                                  return (
                                    <button
                                      key={tag}
                                      type="button"
                                      aria-pressed={active}
                                      className={`quick-pick__chip${active ? " quick-pick__chip--active" : ""}`}
                                      disabled={saving || (!active && full)}
                                      onClick={() => toggle(tag)}
                                    >
                                      {tagLabel(tag)}
                                    </button>
                                  );
                                })}
                              </div>
                              <div className="sheet__row sheet__row--add">
                                <input
                                  className="field__input"
                                  type="text"
                                  name="custom-interest"
                                  maxLength={30}
                                  autoComplete="off"
                                  aria-label={t("profile:hub.tags.custom")}
                                  placeholder={t("profile:hub.tags.custom")}
                                  value={tagInput}
                                  disabled={full}
                                  onChange={(e) => setTagInput(e.target.value)}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                      e.preventDefault();
                                      addCustom();
                                    }
                                  }}
                                />
                                <button
                                  type="button"
                                  className="quick-pick__chip"
                                  disabled={full || !tagInput.trim()}
                                  onClick={addCustom}
                                >
                                  {t("profile:hub.tags.addCustom")}
                                </button>
                              </div>
                            </>
                          );
                        })()
                      ) : f.kind === "ageRange" ? (
                        <>
                          {(() => {
                            const rv =
                              (entry?.value as
                                Record<string, unknown> | undefined) ?? {};
                            const lo = Number(rv.min) || AGE_MIN;
                            const hi = Number(rv.max) || AGE_MAX;
                            const pct = (n: number) =>
                              ((n - AGE_MIN) / (AGE_MAX - AGE_MIN)) * 100;
                            return (
                              <div className="range-dual">
                                <div
                                  className="range-dual__track"
                                  style={{
                                    background: `linear-gradient(to right, var(--surface-sunken) ${pct(lo)}%, var(--saffron-500) ${pct(lo)}%, var(--saffron-500) ${pct(hi)}%, var(--surface-sunken) ${pct(hi)}%)`,
                                  }}
                                />
                                {(["min", "max"] as const).map((bound) => (
                                  <input
                                    key={bound}
                                    type="range"
                                    min={AGE_MIN}
                                    max={AGE_MAX}
                                    step={1}
                                    name={`${f.key}-${bound}-slider`}
                                    aria-label={t(
                                      bound === "min"
                                        ? "profile:editor.ageRangeFrom"
                                        : "profile:editor.ageRangeTo",
                                    )}
                                    value={bound === "min" ? lo : hi}
                                    onChange={(e) => {
                                      const next = Number(e.target.value);
                                      setDraft((d) => {
                                        const prev =
                                          (d[dk]?.value as Record<
                                            string,
                                            unknown
                                          >) ?? {};
                                        const otherKey =
                                          bound === "min" ? "max" : "min";
                                        const other =
                                          Number(prev[otherKey]) ||
                                          (bound === "min" ? AGE_MAX : AGE_MIN);
                                        const clamped =
                                          bound === "min"
                                            ? Math.min(next, other)
                                            : Math.max(next, other);
                                        return {
                                          ...d,
                                          [dk]: {
                                            state: "value",
                                            value: {
                                              ...prev,
                                              [otherKey]: other,
                                              [bound]: clamped,
                                            },
                                          },
                                        };
                                      });
                                    }}
                                  />
                                ))}
                              </div>
                            );
                          })()}
                          <div className="age-range">
                            {(["min", "max"] as const).map((bound, i) => (
                              <span key={bound} style={{ display: "contents" }}>
                                {i === 1 && <span aria-hidden="true">–</span>}
                                <input
                                  className="field__input"
                                  type="number"
                                  inputMode="numeric"
                                  name={`${f.key}-${bound}`}
                                  aria-label={t(
                                    bound === "min"
                                      ? "profile:editor.ageRangeFrom"
                                      : "profile:editor.ageRangeTo",
                                  )}
                                  placeholder={t(
                                    bound === "min"
                                      ? "profile:editor.ageRangeFrom"
                                      : "profile:editor.ageRangeTo",
                                  )}
                                  value={String(
                                    (
                                      entry?.value as
                                        Record<string, unknown> | undefined
                                    )?.[bound] ?? "",
                                  )}
                                  onChange={(e) =>
                                    setDraft((d) => ({
                                      ...d,
                                      [dk]: {
                                        state: "value",
                                        value: {
                                          ...((d[dk]?.value as Record<
                                            string,
                                            unknown
                                          >) ?? {}),
                                          [bound]: e.target.value,
                                        },
                                      },
                                    }))
                                  }
                                />
                              </span>
                            ))}
                          </div>
                        </>
                      ) : f.kind === "textarea" ? (
                        <textarea
                          className="field__input field__input--area"
                          name={f.key}
                          rows={5}
                          maxLength={1200}
                          aria-label={fieldLabel(f.labelKey)}
                          placeholder={fieldLabel(f.labelKey)}
                          value={
                            typeof entry?.value === "string" ? entry.value : ""
                          }
                          onChange={(e) =>
                            setDraft((d) => ({
                              ...d,
                              [dk]: {
                                state: "value",
                                value: e.target.value,
                              },
                            }))
                          }
                        />
                      ) : (
                        <input
                          className="field__input"
                          type="text"
                          name={f.key}
                          list={
                            f.key === "occupation"
                              ? "occupation-suggestions"
                              : undefined
                          }
                          autoComplete="off"
                          aria-label={fieldLabel(f.labelKey)}
                          placeholder={fieldLabel(f.labelKey)}
                          value={
                            typeof entry?.value === "string" ? entry.value : ""
                          }
                          onChange={(e) =>
                            setDraft((d) => ({
                              ...d,
                              [dk]: {
                                state: "value",
                                value: e.target.value,
                              },
                            }))
                          }
                        />
                      )}
                    </div>
                  );
                })}
                {sheetDefs.some((d) => d.category === "horoscope") && (
                  <Link className="link" href="/horoscope/check">
                    {t("horoscope:check.link")}
                  </Link>
                )}
                <datalist id="occupation-suggestions">
                  {OCCUPATION_SUGGESTIONS.map((o) => (
                    <option key={o} value={o} />
                  ))}
                </datalist>
                <div className="sheet__actions">
                  <button
                    type="button"
                    className="quick-pick__chip quick-pick__chip--decline"
                    disabled={saving}
                    onClick={() => void hideSection(sheetDefs)}
                  >
                    {t("profile:editor.decline")}
                  </button>
                  {
                    <button
                      type="button"
                      className="cta sheet__save"
                      disabled={saving}
                      onClick={() => void saveSection(sheetDefs)}
                    >
                      {saving
                        ? t("profile:editor.saving")
                        : t("profile:editor.save")}
                    </button>
                  }
                </div>
              </>
            )}

            {sheet.kind === "prompt" && (
              <>
                <div className="label">{t("profile:hub.prompts.pick")}</div>
                {/* Grouped, because there are three dozen of these now and a
                    single run of chips would be a wall to read. The groups are
                    the same shape Hinge uses, so someone can go straight to
                    the kind of thing they want to say. */}
                {PROMPT_GROUPS.map((group) => (
                  <div key={group.id} className="prompt-group">
                    <div className="prompt-group__title">
                      {t(`profile:hub.prompts.group.${group.id}`)}
                    </div>
                    <div className="quick-pick__chips">
                      {group.questions.map((q) => (
                        <button
                          key={q}
                          type="button"
                          className={`quick-pick__chip${promptDraft.q === q ? " quick-pick__chip--active" : ""}`}
                          disabled={usedQuestions.includes(q)}
                          onClick={() => setPromptDraft((p) => ({ ...p, q }))}
                        >
                          {t(`profile:hub.prompts.q.${q}`)}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {promptDraft.q && (
                  <div className="sheet__field">
                    <label className="label" htmlFor="prompt-answer">
                      {t("profile:hub.prompts.answer")}
                    </label>
                    <textarea
                      id="prompt-answer"
                      className="field__input prompt-textarea"
                      maxLength={PROMPT_MAX}
                      value={promptDraft.a}
                      onChange={(e) =>
                        setPromptDraft((p) => ({ ...p, a: e.target.value }))
                      }
                    />
                    <span className="caption">
                      {promptDraft.a.length}/{PROMPT_MAX}
                    </span>
                    <AnswerCoach answer={promptDraft.a} />

                    {/* Who may read this one answer. Default is connected
                        candidates only — publishing is a deliberate act, not
                        something that happens by forgetting a setting. */}
                    <div className="visibility">
                      <div className="label">
                        {t("profile:hub.prompts.visibility")}
                      </div>
                      {(
                        [
                          ["connectedOnly", false],
                          ["publicOne", true],
                        ] as const
                      ).map(([key, isPublic]) => (
                        <button
                          key={key}
                          type="button"
                          className={`visibility__opt${
                            !!promptDraft.public === isPublic
                              ? " is-chosen"
                              : ""
                          }`}
                          aria-pressed={!!promptDraft.public === isPublic}
                          onClick={() =>
                            setPromptDraft((p) => ({ ...p, public: isPublic }))
                          }
                        >
                          <span className="visibility__name">
                            {t(`profile:hub.prompts.${key}`)}
                          </span>
                          <span className="caption">
                            {t(`profile:hub.prompts.${key}Hint`)}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <div className="sheet__actions">
                  {promptAt(values, sheet.slot) ? (
                    <button
                      type="button"
                      className="quick-pick__chip quick-pick__chip--decline"
                      disabled={saving}
                      onClick={() =>
                        void persist(PROMPT_CATEGORY, {
                          [sheet.slot]: { state: "declined", value: null },
                        })
                      }
                    >
                      {t("profile:hub.prompts.remove")}
                    </button>
                  ) : (
                    <span />
                  )}
                  <button
                    type="button"
                    className="cta sheet__save"
                    disabled={saving || !promptDraft.q || !promptDraft.a.trim()}
                    onClick={() =>
                      void persist(PROMPT_CATEGORY, {
                        [sheet.slot]: {
                          state: "value",
                          value: { q: promptDraft.q, a: promptDraft.a.trim() },
                        },
                      })
                    }
                  >
                    {saving
                      ? t("profile:editor.saving")
                      : t("profile:editor.save")}
                  </button>
                </div>
              </>
            )}

            {sheetError && (
              <p className="form__error" role="status">
                {sheetError}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
