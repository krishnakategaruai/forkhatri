"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Vignette from "@/components/Vignette";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { Field } from "@/components/form/Field";
import MangalyaStory, { markStorySeen, storySeen } from "@/components/MangalyaStory";
import { SubmitButton } from "@/components/form/SubmitButton";
import { requireSession } from "@/lib/auth";
import Icon from "@/components/Icon";
import PhotoChoice from "@/components/PhotoChoice";
import PlaceSearch, { type PlaceValue } from "@/components/PlaceSearch";
import RelationChips from "@/components/RelationChips";
import { setManaging } from "@/lib/api";
import { writeBrowseLookingFor } from "@/lib/activeContext";
import { clearDraft, listDrafts, loadDraft, newDraftKey, saveDraft, type DraftFile, type ProfileDraft } from "@/lib/draft";
import { RELATION_ROLE, invite, type Relation } from "@/lib/homeCircle";
import {
  attachDocument,
  biodataReaderAvailable,
  createProfile,
  createProfileForChild,
  readBiodata,
  updateCategoryAttributes,
  uploadPhoto,
  type BiodataFields,
} from "@/lib/profile";
import { useMounted } from "@/lib/useMounted";
import { getVerification } from "@/lib/verification";

/* FR001 · TR001 · UX11 · UI11 · DEC-V1-001 · DEC-V1-019 · DEC-V1-025
 * Rebuilt 2026-10-06 per ONBOARDING-REDESIGN-2026-10.md §6 (D1–D13) and §8.
 *
 * What changed, and what did not:
 *  - Who-for adds "My sister or brother", "Start from a biodata" and "Just
 *    look around first" (D1, D3, D13). The story is three cards (D2).
 *  - Name, date of birth (three dropdowns, age checked right there) and
 *    gender are one "About" card (D6, D7). The city uses the place search
 *    (D8). Several photos can be chosen at once; "add later" keeps a draft
 *    (D11). Work and studies can be skipped (D9) and education gains Diploma,
 *    Professional and "Other: type" (D10).
 *  - Every answer, photo and attached biodata is saved ON THIS DEVICE at each
 *    step and resumed on return (D12) — nothing about a child reaches the
 *    server before the family publishes.
 *  - A parent is no longer stopped at the first tap: the child's number, the
 *    relation and the one-minute check that it's you are asked on "Check and
 *    publish", after the work is done (D4, D5). The server rules are
 *    unchanged: one photo to save a profile (DEC-V1-001), the child's number
 *    (DEC-V1-019), and the maker's face check before anything is provisioned
 *    (DEC-V1-025).
 */

type Gender = "female" | "male" | "other";
type ForWhom = "self" | "son" | "daughter" | "sibling" | "relative";
type Step = "about" | "where" | "photos" | "work" | "publish";

const SELF_STEPS: Step[] = ["about", "where", "photos", "work"];
const CHILD_STEPS: Step[] = ["about", "where", "photos", "work", "publish"];
const ART: Record<Step, string> = {
  about: "basics",
  where: "community",
  photos: "photos",
  work: "lifestyle",
  publish: "family",
};
const EDUCATION = ["high_school", "diploma", "bachelors", "professional", "masters", "doctorate", "other"] as const;
const MARITAL = ["never_married", "divorced", "widowed", "awaiting_divorce"] as const;
const RELOCATION = ["yes", "no", "open_to_discussion"] as const;
// Prohibition of Child Marriage Act, 2006 — the same figures the server enforces.
const REQUIRED_AGE: Record<Gender, number> = { female: 18, male: 21, other: 21 };

function ageOn(y: number, m: number, d: number, today = new Date()): number {
  let years = today.getFullYear() - y;
  if (today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d)) years -= 1;
  return years;
}

function daysIn(y: number, m: number): number {
  return new Date(y || 2000, m, 0).getDate();
}

export default function CreateProfilePage() {
  return (
    <Suspense fallback={null}>
      <CreateProfileWizard />
    </Suspense>
  );
}

type Screen = "who" | "biodata" | "biodataCheck" | "form" | "drafts";

function CreateProfileWizard() {
  const { t, i18n } = useTranslation(["profile", "common", "circle", "verify"]);
  const router = useRouter();
  const params = useSearchParams();
  const forParam = params.get("for") === "child";
  const whoParam = params.get("who");
  const initialWho: ForWhom | null =
    forParam && (whoParam === "son" || whoParam === "daughter") ? whoParam : null;

  // The first paint is in the member's own language, read in the browser:
  // rendering nothing on the server keeps its English out of hydration.
  const mounted = useMounted();
  const [screen, setScreen] = useState<Screen>(initialWho ? "form" : "who");
  const [forWhom, setForWhom] = useState<ForWhom | null>(initialWho);
  const [showStory, setShowStory] = useState(false);
  const [step, setStep] = useState<Step>("about");

  const [name, setName] = useState("");
  const [dobDay, setDobDay] = useState("");
  const [dobMonth, setDobMonth] = useState("");
  const [dobYear, setDobYear] = useState("");
  const [gender, setGender] = useState<Gender | "">(
    initialWho === "son" ? "male" : initialWho === "daughter" ? "female" : "",
  );
  const [lookingFor, setLookingFor] = useState<"bride" | "groom" | "">(
    initialWho === "son" ? "bride" : initialWho === "daughter" ? "groom" : "",
  );
  const [place, setPlace] = useState<PlaceValue | null>(null);
  const [educationLevel, setEducationLevel] = useState("");
  const [educationOther, setEducationOther] = useState("");
  const [occupation, setOccupation] = useState("");
  const [maritalStatus, setMaritalStatus] = useState("");
  const [relocation, setRelocation] = useState("");
  const [childPhone, setChildPhone] = useState("");
  const [relation, setRelation] = useState<Relation | null>(null);
  const [photos, setPhotos] = useState<DraftFile[]>([]);
  const [biodata, setBiodata] = useState<DraftFile | null>(null);
  const [attachBiodata, setAttachBiodata] = useState(false);
  const [extras, setExtras] = useState<Record<string, string | number>>({});

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<"draftKept" | "alreadyJoined" | null>(null);
  const [askState, setAskState] = useState<"idle" | "sending" | "sent">("idle");
  const [askError, setAskError] = useState<string | null>(null);
  const [ownName, setOwnName] = useState("");
  // The key this draft is saved under: one per profile being made.
  const [memberKey, setMemberKey] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<{ key: string; draft: ProfileDraft }[]>([]);
  const [resumed, setResumed] = useState(false);
  const [lookAroundOpen, setLookAroundOpen] = useState(false);
  const [verified, setVerified] = useState<boolean | null>(null);

  // Biodata screen state.
  const [readerOn, setReaderOn] = useState(false);
  const [consent, setConsent] = useState(false);
  const [readFields, setReadFields] = useState<BiodataFields | null>(null);

  const forChild = forWhom !== null && forWhom !== "self";
  const steps = forChild ? CHILD_STEPS : SELF_STEPS;
  const stepIndex = steps.indexOf(step);

  /* Sign-in, the member's own name, and any draft kept on this device. */
  useEffect(() => {
    let alive = true;
    void (async () => {
      const s = await requireSession();
      if (!alive || !s) return;
      if (s.display_name) setOwnName(s.display_name);
      const base = s.account_id || "member";
      const all = await listDrafts(base);
      if (!alive) return;
      const wanted = params.get("draft");
      let key = base;
      let d: ProfileDraft | null = null;
      if (params.get("start") === "1") {
        key = all.length > 0 ? newDraftKey(base) : base;
      } else if (wanted && all.some((x) => x.key === wanted)) {
        key = wanted;
        d = await loadDraft(wanted);
      } else if (all.length > 1 && !forParam) {
        setDrafts(all);
        setScreen("drafts");
        return;
      } else if (all.length >= 1) {
        key = all[0].key;
        d = all[0].draft;
      }
      setMemberKey(key);
      if (!alive) return;
      if (d) {
        setForWhom(d.forWhom as ForWhom);
        setStep((d.step >= 0 ? (d.forWhom === "self" ? SELF_STEPS : CHILD_STEPS)[d.step] : "about") ?? "about");
        setName(d.name);
        setDobDay(d.dobDay);
        setDobMonth(d.dobMonth);
        setDobYear(d.dobYear);
        setGender(d.gender as Gender | "");
        setLookingFor(d.lookingFor as "bride" | "groom" | "");
        setPlace(d.cityLocality ? { label: d.cityLocality, place_id: "draft" } : null);
        setEducationLevel(d.educationLevel);
        setEducationOther(d.educationOther);
        setOccupation(d.occupation);
        setMaritalStatus(d.maritalStatus);
        setRelocation(d.relocation);
        setChildPhone(d.childPhone);
        setRelation(d.relation as Relation | null);
        setPhotos(d.photos ?? []);
        setBiodata(d.biodata);
        setAttachBiodata(d.attachBiodata);
        setExtras(d.extras ?? {});
        setScreen("form");
        setResumed(true);
      } else if (!forParam && !storySeen()) {
        setShowStory(true);
      }
    })();
    return () => {
      alive = false;
    };
    // Runs once on arrival; the params are read only then.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* [D12] Save to the device on every change, once someone has started. */
  const draft: ProfileDraft | null = useMemo(
    () =>
      forWhom && screen === "form"
        ? {
            forWhom,
            step: stepIndex,
            name,
            dobDay,
            dobMonth,
            dobYear,
            gender,
            lookingFor,
            cityLocality: place?.label ?? "",
            educationLevel,
            educationOther,
            occupation,
            maritalStatus,
            relocation,
            childPhone,
            relation,
            photos,
            biodata,
            attachBiodata,
            extras,
            savedAt: 0,
          }
        : null,
    [forWhom, screen, stepIndex, name, dobDay, dobMonth, dobYear, gender, lookingFor, place, educationLevel,
      educationOther, occupation, maritalStatus, relocation, childPhone, relation, photos, biodata, attachBiodata, extras],
  );
  const publishedRef = useRef(false);
  useEffect(() => {
    if (!draft || !memberKey || publishedRef.current) return;
    const timer = window.setTimeout(() => void saveDraft(memberKey, { ...draft, savedAt: Date.now() }), 300);
    return () => window.clearTimeout(timer);
  }, [draft, memberKey]);

  /* The maker's check (DEC-V1-025) is looked up only on "Check and publish". */
  useEffect(() => {
    if (step !== "publish" || !forChild) return;
    let alive = true;
    void getVerification().then((s) => {
      if (alive) setVerified(s ? s.verified : null);
    });
    return () => {
      alive = false;
    };
  }, [step, forChild]);

  useEffect(() => {
    if (screen !== "biodata") return;
    void biodataReaderAvailable().then(setReaderOn);
  }, [screen]);

  // Object URLs for photo thumbnails, released when the list changes.
  const thumbs = useMemo(() => photos.map((p) => URL.createObjectURL(p.blob)), [photos]);
  useEffect(() => () => thumbs.forEach((u) => URL.revokeObjectURL(u)), [thumbs]);

  function applyWho(who: ForWhom) {
    setForWhom(who);
    if (who === "self") setName((n) => n || ownName);
    else setName("");
    const g: Gender | "" = who === "son" ? "male" : who === "daughter" ? "female" : "";
    setGender(g);
    setLookingFor(g === "male" ? "bride" : g === "female" ? "groom" : "");
  }

  function chooseForWhom(who: ForWhom) {
    applyWho(who);
    setStep("about");
    setScreen("form");
    window.history.pushState({ wizard: true }, "");
  }

  function chooseGender(g: Gender) {
    setGender(g);
    setLookingFor(g === "male" ? "bride" : g === "female" ? "groom" : "");
  }

  function lookAround(v: "bride" | "groom") {
    writeBrowseLookingFor(v);
    router.push("/discover");
  }

  async function startAgain() {
    if (memberKey) await clearDraft(memberKey);
    // A full reload, so every answer held in memory is dropped too.
    window.location.replace(`${window.location.pathname}?start=1`);
  }

  /** One step back; from the first step, back to "who is this for". */
  function goBack() {
    setError(null);
    setNotice(null);
    if (screen === "biodataCheck") return setScreen("biodata");
    if (screen === "biodata") return setScreen("who");
    if (screen === "form" && stepIndex > 0) return setStep(steps[stepIndex - 1]);
    if (screen === "form" && initialWho === null) return setScreen("who");
    router.back();
  }
  const goBackRef = useRef(goBack);
  useEffect(() => {
    goBackRef.current = goBack;
  });
  useEffect(() => {
    const onPop = () => goBackRef.current();
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const dob = dobYear && dobMonth && dobDay
    ? `${dobYear}-${dobMonth.padStart(2, "0")}-${dobDay.padStart(2, "0")}`
    : "";
  const age = dob ? ageOn(Number(dobYear), Number(dobMonth), Number(dobDay)) : null;
  const requiredAge = REQUIRED_AGE[(gender || "other") as Gender];
  const tooYoung = age !== null && gender !== "" && age < requiredAge;

  const aboutValid = name.trim().length > 0 && dob !== "" && gender !== "" && lookingFor !== "" && !tooYoung;
  const whereValid = !!place?.label;
  const workDone = educationLevel !== "" && occupation.trim() !== "" && maritalStatus !== "" && relocation !== "";
  const workValid = workDone && (educationLevel !== "other" || educationOther.trim() !== "");
  const phoneValid = childPhone.replace(/\D/g, "").length >= 10;

  const firstName = name.trim().split(" ")[0] || "";
  const kin = forWhom === "daughter" ? "daughter" : forWhom === "son" ? "son" : forWhom === "self" ? "self" : "other";

  function next() {
    setError(null);
    const i = steps.indexOf(step);
    if (i < steps.length - 1) {
      setStep(steps[i + 1]);
      window.history.pushState({ wizard: true }, "");
    }
  }

  /** Not published: keep the draft and let the family look around meanwhile. */
  function keepDraft() {
    if (lookingFor) writeBrowseLookingFor(lookingFor);
    setNotice("draftKept");
  }

  /** After the profile exists: the extra photos, an attached biodata and the
   *  facts read from it. Each is optional; a failure never undoes the profile. */
  async function afterPublish() {
    for (const p of photos.slice(1)) {
      await uploadPhoto(new File([p.blob], p.name, { type: p.type })).catch(() => null);
    }
    if (biodata && attachBiodata) await attachDocument("biodata", biodata.blob, biodata.name).catch(() => null);
    const horoscope: Record<string, { state: "value"; value: string }> = {};
    if (typeof extras.rashi === "string") horoscope.rashi = { state: "value", value: extras.rashi };
    if (typeof extras.nakshatra === "string") horoscope.nakshatra = { state: "value", value: extras.nakshatra };
    if (typeof extras.birth_time === "string") horoscope.birth_time = { state: "value", value: extras.birth_time };
    if (Object.keys(horoscope).length) await updateCategoryAttributes("horoscope", horoscope).catch(() => null);
    const community: Record<string, { state: "value"; value: string }> = {};
    if (typeof extras.gotra === "string") community.gotra = { state: "value", value: extras.gotra };
    if (typeof extras.native_place === "string") community.native_place = { state: "value", value: extras.native_place };
    if (Object.keys(community).length) await updateCategoryAttributes("community", community).catch(() => null);
    if (typeof extras.height_cm === "number")
      await updateCategoryAttributes("basics", { height_cm: { state: "value", value: extras.height_cm } }).catch(() => null);
  }

  async function publish(skipWork = false) {
    setError(null);
    setNotice(null);
    if (photos.length === 0) {
      keepDraft();
      return;
    }
    if (!gender || !lookingFor || !place) return;
    const first = photos[0];
    const base = {
      name: name.trim(),
      dateOfBirth: dob,
      gender,
      lookingFor,
      cityLocality: place.label,
      photo: new File([first.blob], first.name, { type: first.type }),
      ...(skipWork || !workValid
        ? {}
        : {
            educationLevel,
            educationOther,
            occupation,
            maritalStatus,
            relocationWillingness: relocation,
          }),
    };
    setBusy(true);
    if (forChild) {
      if (!relation || !phoneValid) {
        setBusy(false);
        return;
      }
      const made = await createProfileForChild({ ...base, childPhone, relation });
      if (made.ok) {
        publishedRef.current = true;
        setManaging(made.accountId);
        await afterPublish();
        setManaging(null);
        if (memberKey) await clearDraft(memberKey);
        router.push(`/me/matchmaker?setup=1&manage=${made.accountId}`);
        return;
      }
      setBusy(false);
      if (made.kind === "alreadyJoined") return setNotice("alreadyJoined");
      if (made.kind === "verificationRequired") return setVerified(false);
      setError(made.kind === "network" ? t("profile:error.network") : (made.message ?? t("profile:error.network")));
      return;
    }
    const result = await createProfile(base);
    if (result.ok) {
      publishedRef.current = true;
      await afterPublish();
      if (memberKey) await clearDraft(memberKey);
      router.push("/me/matchmaker?setup=1");
      return;
    }
    setBusy(false);
    setError(result.kind === "network" ? t("profile:error.network") : (result.message ?? t("profile:error.network")));
  }

  /** The number is already on ForKhatri: ask to join their Home Circle instead. */
  async function askToJoin() {
    if (!relation) return;
    setAskState("sending");
    setAskError(null);
    const outcome = await invite({
      invitee_identifier: childPhone.replace(/[\s-]/g, ""),
      relation,
      relationship_type: RELATION_ROLE[relation],
      direction: "to_candidate",
    });
    if (outcome.ok) return setAskState("sent");
    setAskState("idle");
    setAskError(outcome.message ?? t("profile:error.network"));
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (step === "work" && !forChild) return void publish(false);
    if (step === "publish") {
      if (verified === false) {
        router.push(`/me/verify?next=${encodeURIComponent("/profile/create")}`);
        return;
      }
      return void publish(!workValid);
    }
    next();
  }

  const addPhotos = useCallback((files: File[]) => {
    setPhotos((prev) =>
      [...prev, ...files.map((f) => ({ blob: f as Blob, name: f.name || "photo.jpg", type: f.type || "image/jpeg" }))].slice(0, 6),
    );
  }, []);

  /* ---------------- Biodata: read, then check each line ---------------- */
  async function onReadBiodata() {
    if (!biodata) return;
    setBusy(true);
    setError(null);
    const out = await readBiodata(biodata.blob, biodata.name);
    setBusy(false);
    if (!out.ok) {
      setError(out.message ?? t("profile:error.network"));
      return;
    }
    setReadFields(out.fields);
    setScreen("biodataCheck");
  }

  function applyBiodata(f: BiodataFields) {
    if (f.name) setName(f.name);
    if (f.date_of_birth) {
      const [y, m, d] = f.date_of_birth.split("-");
      setDobYear(String(Number(y)));
      setDobMonth(String(Number(m)));
      setDobDay(String(Number(d)));
    }
    if (f.gender && (forWhom === "self" || forWhom === "sibling" || forWhom === "relative")) chooseGender(f.gender);
    if (f.city) setPlace({ label: f.city, place_id: "biodata" });
    if (f.education_level) setEducationLevel(f.education_level);
    if (f.education_other) setEducationOther(f.education_other);
    if (f.occupation) setOccupation(f.occupation);
    if (f.marital_status) setMaritalStatus(f.marital_status);
    const ex: Record<string, string | number> = {};
    for (const k of ["rashi", "nakshatra", "birth_time", "gotra", "native_place", "height_cm"] as const) {
      const v = f[k];
      if (v !== undefined) ex[k] = v;
    }
    setExtras(ex);
  }

  function continueFromBiodata(f: BiodataFields | null) {
    if (f) applyBiodata(f);
    setStep("about");
    setScreen("form");
    window.history.pushState({ wizard: true }, "");
  }

  const months = useMemo(() => {
    const fmt = new Intl.DateTimeFormat(i18n.language || "en", { month: "long" });
    return Array.from({ length: 12 }, (_, i) => fmt.format(new Date(2000, i, 1)));
  }, [i18n.language]);
  const thisYear = new Date().getFullYear();
  const years = Array.from({ length: 63 }, (_, i) => thisYear - 18 - i);

  /* ---------------- Screens ---------------- */

  if (!mounted) return null;

  if (showStory) {
    return (
      <MangalyaStory
        short
        onDone={() => {
          markStorySeen();
          setShowStory(false);
        }}
      />
    );
  }

  if (screen === "drafts") {
    return (
      <main className="screen screen--form">
        <div className="form wizard-step">
          <div className="wizard-step__head">
            <h1 className="h2">{t("circle:drafts.title")}</h1>
          </div>
          <ul className="category-list">
            {drafts.map(({ key, draft: d }) => (
              <li key={key} className="category-card" style={{ width: "100%" }}>
                <span className="category-card__body">
                  <span className="category-card__title">{d.name.trim() || t("circle:drafts.unnamed")}</span>
                  <span className="category-card__preview">{t("circle:drafts.kept")}</span>
                </span>
                <a className="btn btn--primary" href={`${window.location.pathname}?draft=${encodeURIComponent(key)}`}>
                  {t("circle:drafts.continue")}
                </a>
              </li>
            ))}
          </ul>
          <div className="form__actions">
            <a className="link link--button" href={`${window.location.pathname}?start=1`}>
              {t("circle:drafts.newOne")}
            </a>
          </div>
        </div>
      </main>
    );
  }

  if (notice === "draftKept" || notice === "alreadyJoined") {
    return (
      <main className="screen screen--form">
        <div className="form wizard-step">
          <Vignette id="family" className="wizard-step__art" />
          <div className="wizard-step__head">
            <h1 className="h2">
              {notice === "draftKept" ? t("profile:onboard.publish.draftKeptTitle") : t("profile:onboard.publish.alreadyTitle")}
            </h1>
            <p className="caption">
              {notice === "draftKept"
                ? t("profile:onboard.publish.draftKept")
                : t("profile:onboard.publish.alreadyJoined", { name: firstName })}
            </p>
          </div>
          {notice === "alreadyJoined" && relation && (
            <div className="form__actions">
              {askState === "sent" ? (
                <p className="caption" role="status">{t("profile:onboard.publish.askSent", { name: firstName })}</p>
              ) : (
                <button type="button" className="btn btn--primary" disabled={askState === "sending"} onClick={() => void askToJoin()}>
                  {t("profile:onboard.publish.askToJoin", { name: firstName })}
                </button>
              )}
              {askError && <p className="form__error" role="alert">{askError}</p>}
            </div>
          )}
          <div className="form__actions">
            <button type="button" className="btn btn--primary" onClick={() => router.push("/discover")}>
              {t("profile:onboard.publish.lookAroundMeanwhile")}
            </button>
            <button type="button" className="link link--button" onClick={() => setNotice(null)}>
              {t("profile:onboard.publish.backToDraft")}
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (screen === "who") {
    const options: ForWhom[] = forParam
      ? ["daughter", "son", "sibling", "relative"]
      : ["self", "daughter", "son", "sibling", "relative"];
    return (
      <main className="screen screen--form">
        <div className="form wizard-step">
          <Vignette id="family" className="wizard-step__art" />
          <div className="wizard-step__head">
            <h1 className="h2">{t("profile:onboard.who.title")}</h1>
            <p className="caption">{t("profile:onboard.who.hint")}</p>
          </div>
          <div className="forwhom">
            {options.map((who) => (
              <button key={who} type="button" className="forwhom__opt" onClick={() => chooseForWhom(who)}>
                {t(`profile:onboard.who.${who}`)}
              </button>
            ))}
            <button
              type="button"
              className="forwhom__opt forwhom__opt--biodata"
              onClick={() => {
                setScreen("biodata");
                window.history.pushState({ wizard: true }, "");
              }}
            >
              {t("profile:onboard.who.biodata")}
              <small className="forwhom__sub">{t("profile:onboard.who.biodataHint")}</small>
            </button>
          </div>
          {!forParam && (
            <div className="forwhom__look">
              {lookAroundOpen ? (
                <div className="forwhom__lookask" role="group" aria-label={t("profile:onboard.who.lookAroundAsk")}>
                  <span className="caption">{t("profile:onboard.who.lookAroundAsk")}</span>
                  <div className="segmented">
                    {(["bride", "groom"] as const).map((v) => (
                      <button key={v} type="button" className="segmented__opt" onClick={() => lookAround(v)}>
                        {t(`profile:onboard.who.see_${v}`)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <button type="button" className="link link--button" onClick={() => setLookAroundOpen(true)}>
                  {t("profile:onboard.who.lookAround")}
                </button>
              )}
            </div>
          )}
          <p className="caption forwhom__already">{t("profile:wizard.forWhom.already")}</p>
        </div>
      </main>
    );
  }

  if (screen === "biodata") {
    return (
      <main className="screen screen--form">
        <div className="wizard-top">
          <div className="wizard-top__row">
            <button type="button" className="icon-btn wizard-back" onClick={() => window.history.back()} aria-label={t("common:action.back")}>
              <Icon name="back" />
            </button>
            <span className="caption">{t("profile:onboard.biodata.title")}</span>
          </div>
        </div>
        <div className="form wizard-step">
          <div className="wizard-step__head">
            <h1 className="h2">{t("profile:onboard.biodata.title")}</h1>
            <p className="caption">{t("profile:onboard.biodata.hint")}</p>
          </div>
          <label className="date-field">
            <span className="caption">{t("profile:onboard.biodata.whose")}</span>
            <select
              className="field__input select"
              value={forWhom ?? ""}
              onChange={(e) => applyWho(e.target.value as ForWhom)}
            >
              <option value="">{t("profile:wizard.pick")}</option>
              {((forParam ? [] : ["self"]) as ForWhom[]).concat(["daughter", "son", "sibling", "relative"]).map((w) => (
                <option key={w} value={w}>{t(`profile:onboard.who.${w}`)}</option>
              ))}
            </select>
          </label>
          <label className="btn biodata__pick">
            {biodata ? t("profile:onboard.biodata.chosen", { name: biodata.name }) : t("profile:onboard.biodata.choose")}
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/webp"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0];
                e.target.value = "";
                if (f) setBiodata({ blob: f, name: f.name || "biodata", type: f.type || "application/octet-stream" });
              }}
            />
          </label>
          {readerOn ? (
            <label className="check-line">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
              <span>{t("profile:onboard.biodata.consent")}</span>
            </label>
          ) : (
            <p className="caption">{t("profile:onboard.biodata.noReader")}</p>
          )}
          <label className="check-line">
            <input type="checkbox" checked={attachBiodata} onChange={(e) => setAttachBiodata(e.target.checked)} />
            <span>{t("profile:onboard.biodata.attach")}</span>
          </label>
          <p className="form__error" role="status" aria-live="polite">{error ?? ""}</p>
          <div className="form__actions">
            {readerOn && (
              <button
                type="button"
                className="btn btn--primary"
                disabled={!biodata || !forWhom || !consent || busy}
                onClick={() => void onReadBiodata()}
              >
                {busy ? t("profile:onboard.biodata.reading") : t("profile:onboard.biodata.read")}
              </button>
            )}
            <button
              type="button"
              className={readerOn ? "link link--button" : "btn btn--primary"}
              disabled={!biodata || !forWhom || busy}
              onClick={() => continueFromBiodata(null)}
            >
              {t("profile:onboard.biodata.typeInstead")}
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (screen === "biodataCheck") {
    const f = readFields ?? {};
    const rows: [string, string | null][] = [
      ["name", f.name ?? null],
      ["date_of_birth", f.date_of_birth ?? null],
      ["birth_time", f.birth_time ?? null],
      ["city", f.city ?? null],
      ["native_place", f.native_place ?? null],
      [
        "education_level",
        f.education_level
          ? f.education_level === "other" && f.education_other
            ? f.education_other
            : t(`profile:option.highest_education_level.${f.education_level}`)
          : null,
      ],
      ["occupation", f.occupation ?? null],
      ["marital_status", f.marital_status ? t(`profile:option.marital_status.${f.marital_status}`) : null],
      ["height_cm", f.height_cm ? `${f.height_cm} cm` : null],
      ["rashi", f.rashi ? t(`profile:option.rashi.${f.rashi}`, { defaultValue: f.rashi }) : null],
      ["nakshatra", f.nakshatra ? t(`profile:option.nakshatra.${f.nakshatra}`, { defaultValue: f.nakshatra }) : null],
      ["gotra", f.gotra ?? null],
    ];
    const anything = rows.some(([, v]) => v);
    return (
      <main className="screen screen--form">
        <div className="wizard-top">
          <div className="wizard-top__row">
            <button type="button" className="icon-btn wizard-back" onClick={() => window.history.back()} aria-label={t("common:action.back")}>
              <Icon name="back" />
            </button>
            <span className="caption">{t("profile:onboard.biodata.title")}</span>
          </div>
        </div>
        <div className="form wizard-step">
          <div className="wizard-step__head">
            <h1 className="h2">{t("profile:onboard.biodata.checkTitle")}</h1>
            <p className="caption">{anything ? t("profile:onboard.biodata.checkHint") : t("profile:onboard.biodata.nothingRead")}</p>
          </div>
          {anything && (
            <dl className="onb-facts">
              {rows.map(([k, v]) => (
                <div className="onb-facts__row" key={k}>
                  <dt>{t(`profile:onboard.biodata.f.${k}`)}</dt>
                  <dd className={v ? "" : "onb-facts__missing"}>{v ?? t("profile:onboard.biodata.notFound")}</dd>
                </div>
              ))}
            </dl>
          )}
          <div className="form__actions">
            <button type="button" className="btn btn--primary" onClick={() => continueFromBiodata(readFields)}>
              {t("profile:onboard.biodata.looksRight")}
            </button>
          </div>
        </div>
      </main>
    );
  }

  /* ---------------- The form steps ---------------- */
  const stepTitle =
    step === "about"
      ? t(`profile:onboard.about.title_${forWhom ?? "self"}`)
      : step === "where"
        ? kin === "self" ? t("profile:onboard.where.title_self") : t("profile:onboard.where.title_other", { name: firstName })
        : step === "photos"
          ? kin === "self" ? t("profile:onboard.photos.title_self") : t("profile:onboard.photos.title_other", { name: firstName })
          : step === "work"
            ? kin === "self" ? t("profile:onboard.work.title_self") : t("profile:onboard.work.title_other", { name: firstName })
            : t("profile:onboard.publish.title", { name: firstName });

  const primaryLabel = busy
    ? t("profile:onboard.publish.publishing")
    : step === "work" && !forChild
      ? photos.length
        ? t("profile:onboard.publish.selfPublish")
        : t("profile:onboard.publish.keepDraft")
      : step === "publish"
        ? verified === false
          ? t("profile:onboard.publish.checkStart")
          : t("profile:onboard.publish.publish")
        : t("profile:wizard.next");

  const stepValid =
    (step === "about" && aboutValid) ||
    (step === "where" && whereValid) ||
    (step === "photos" && photos.length > 0) ||
    (step === "work" && (forChild ? workValid : workValid || false)) ||
    (step === "publish" && photos.length > 0 && relation !== null && phoneValid && aboutValid && whereValid);

  return (
    <main className="screen screen--form">
      <div className="wizard-top">
        <div className="wizard-top__row">
          <button type="button" className="icon-btn wizard-back" onClick={() => window.history.back()} aria-label={t("common:action.back")}>
            <Icon name="back" />
          </button>
          <span className="caption">
            {t(`profile:onboard.stepName.${step}`)} · {t("profile:onboard.stepOf", { current: stepIndex + 1, total: steps.length })}
          </span>
          {resumed && (
            <button type="button" className="link link--button wizard-top__again" onClick={() => void startAgain()}>
              {t("profile:onboard.startAgain")}
            </button>
          )}
          {step !== "about" && (
            <button
              type="button"
              className="link link--button"
              onClick={() => setStep("about")}
            >
              {t("profile:onboard.editBasics")}
            </button>
          )}
        </div>
        <div className="progress" aria-hidden="true">
          <div className="progress__bar" style={{ width: `${((stepIndex + 1) / steps.length) * 100}%` }} />
        </div>
      </div>

      <form className="form wizard-step" key={step} onSubmit={onSubmit} noValidate>
        <Vignette id={ART[step]} className="wizard-step__art" />
        <div className="wizard-step__head">
          <h1 className="h2">{stepTitle}</h1>
          {resumed && step !== "publish" && <p className="caption">{t("profile:onboard.resumeNote")}</p>}
          {step === "photos" && <p className="caption">{t("profile:onboard.photos.hint")}</p>}
          {step === "work" && <p className="caption">{t("profile:onboard.work.hint")}</p>}
          {step === "where" && <p className="caption">{t("profile:onboard.where.hint")}</p>}
        </div>

        {step === "about" && (
          <>
            <Field
              label={t(`profile:onboard.about.name_${kin}`)}
              value={name}
              onChange={setName}
              type="text"
              autoComplete={kin === "self" ? "name" : "off"}
              disabled={busy}
              required
            />
            <fieldset className="dob">
              <legend className="caption">{t("profile:onboard.about.dob")}</legend>
              <div className="dob__row">
                <select className="field__input select" aria-label={t("profile:onboard.about.day")} value={dobDay} onChange={(e) => setDobDay(e.target.value)}>
                  <option value="">{t("profile:onboard.about.day")}</option>
                  {Array.from({ length: daysIn(Number(dobYear), Number(dobMonth) || 1) }, (_, i) => String(i + 1)).map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                <select className="field__input select" aria-label={t("profile:onboard.about.month")} value={dobMonth} onChange={(e) => setDobMonth(e.target.value)}>
                  <option value="">{t("profile:onboard.about.month")}</option>
                  {months.map((m, i) => (
                    <option key={m} value={String(i + 1)}>{m}</option>
                  ))}
                </select>
                <select className="field__input select" aria-label={t("profile:onboard.about.year")} value={dobYear} onChange={(e) => setDobYear(e.target.value)}>
                  <option value="">{t("profile:onboard.about.year")}</option>
                  {years.map((y) => (
                    <option key={y} value={String(y)}>{y}</option>
                  ))}
                </select>
              </div>
              {age !== null && !tooYoung && <p className="dob__age">{t("profile:onboard.about.age", { count: age })}</p>}
              {tooYoung && (
                <p className="form__error" role="alert">
                  {t(gender === "female" ? "profile:onboard.about.tooYoung_female" : "profile:onboard.about.tooYoung_male")}
                </p>
              )}
            </fieldset>
            {(forWhom === "self" || forWhom === "relative") && (
              <>
                <span className="caption">{t(forWhom === "self" ? "profile:wizard.iAm" : "profile:wizard.theyAre")}</span>
                <div className="segmented segmented--3" role="radiogroup">
                  {(["female", "male", "other"] as Gender[]).map((g) => (
                    <button key={g} type="button" role="radio" aria-checked={gender === g}
                      className={`segmented__opt${gender === g ? " is-active" : ""}`} onClick={() => chooseGender(g)} disabled={busy}>
                      {t(`profile:field.genderOption.${g}`)}
                    </button>
                  ))}
                </div>
              </>
            )}
            {forWhom === "sibling" && (
              <div className="segmented" role="radiogroup">
                {(["female", "male"] as Gender[]).map((g) => (
                  <button key={g} type="button" role="radio" aria-checked={gender === g}
                    className={`segmented__opt${gender === g ? " is-active" : ""}`} onClick={() => chooseGender(g)} disabled={busy}>
                    {t(g === "female" ? "profile:onboard.about.sister" : "profile:onboard.about.brother")}
                  </button>
                ))}
              </div>
            )}
            {gender === "other" && (
              <div className="segmented" role="radiogroup" aria-label={t("profile:field.partner_preference.looking_for")}>
                {(["bride", "groom"] as const).map((o) => (
                  <button key={o} type="button" role="radio" aria-checked={lookingFor === o}
                    className={`segmented__opt${lookingFor === o ? " is-active" : ""}`} onClick={() => setLookingFor(o)} disabled={busy}>
                    {t(`profile:option.looking_for.${o}`)}
                  </button>
                ))}
              </div>
            )}
            {lookingFor && (
              <p className="caption">
                {t(
                  kin === "self"
                    ? "profile:onboard.about.seesSelf"
                    : gender === "female"
                      ? "profile:onboard.about.seesHer"
                      : gender === "male"
                        ? "profile:onboard.about.seesHim"
                        : "profile:onboard.about.seesThem",
                  { value: t(`profile:option.looking_for.${lookingFor}`).toLowerCase() },
                )}
              </p>
            )}
          </>
        )}

        {step === "where" && (
          <PlaceSearch
            value={place}
            onChange={(v) => setPlace(v)}
            label={t("profile:onboard.where.label")}
            disabled={busy}
          />
        )}

        {step === "photos" && (
          <div className="onb-photos">
            <div className="onb-photos__grid">
              {photos.map((p, i) => (
                <div key={`${p.name}-${i}`} className="onb-photos__item">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={thumbs[i]} alt="" />
                  {i === 0 && <span className="onb-photos__main">{t("profile:onboard.photos.main")}</span>}
                  <button type="button" className="onb-photos__remove" aria-label={t("profile:onboard.photos.remove")}
                    onClick={() => setPhotos((prev) => prev.filter((_, k) => k !== i))}>
                    ×
                  </button>
                </div>
              ))}
            </div>
            <PhotoChoice quiet disabled={busy || photos.length >= 6} onFiles={addPhotos} />
          </div>
        )}

        {step === "work" && (
          <>
            <label className="date-field">
              <span className="caption">{t("profile:field.education.highest_education_level")}</span>
              <select className="field__input select" value={educationLevel} onChange={(e) => setEducationLevel(e.target.value)} disabled={busy}>
                <option value="">{t("profile:wizard.pick")}</option>
                {EDUCATION.map((o) => (
                  <option key={o} value={o}>{t(`profile:option.highest_education_level.${o}`)}</option>
                ))}
              </select>
            </label>
            {educationLevel === "other" && (
              <Field label={t("profile:onboard.work.educationOther")} value={educationOther} onChange={setEducationOther} type="text" disabled={busy} />
            )}
            <label className="date-field">
              <span className="caption">{t("profile:field.profession.occupation")}</span>
              <input
                className="field__input"
                list="onb-occupations"
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
                placeholder={t("profile:onboard.work.occupationHint")}
                disabled={busy}
                autoComplete="organization-title"
              />
              <datalist id="onb-occupations">
                {(t("profile:onboard.work.suggestions", { returnObjects: true }) as string[]).map((o) => (
                  <option key={o} value={o} />
                ))}
              </datalist>
            </label>
            <label className="date-field">
              <span className="caption">{t("profile:field.marital_history.marital_status")}</span>
              <select className="field__input select" value={maritalStatus} onChange={(e) => setMaritalStatus(e.target.value)} disabled={busy}>
                <option value="">{t("profile:wizard.pick")}</option>
                {MARITAL.map((o) => (
                  <option key={o} value={o}>{t(`profile:option.marital_status.${o}`)}</option>
                ))}
              </select>
            </label>
            <label className="date-field">
              <span className="caption">{t("profile:field.relocation.relocation_willingness")}</span>
              <select className="field__input select" value={relocation} onChange={(e) => setRelocation(e.target.value)} disabled={busy}>
                <option value="">{t("profile:wizard.pick")}</option>
                {RELOCATION.map((o) => (
                  <option key={o} value={o}>{t(`profile:option.relocation_willingness.${o}`)}</option>
                ))}
              </select>
            </label>
          </>
        )}

        {step === "publish" && (
          <>
            <dl className="onb-facts">
              <div className="onb-facts__row">
                <dt>{t("profile:onboard.publish.basics")}</dt>
                <dd>{aboutValid && whereValid ? t("profile:onboard.publish.done") : t("profile:onboard.publish.missing")}</dd>
              </div>
              <div className="onb-facts__row">
                <dt>{t("profile:onboard.publish.photo")}</dt>
                <dd className={photos.length ? "" : "onb-facts__missing"}>
                  {photos.length
                    ? t("profile:onboard.photos.count", { count: photos.length })
                    : t("profile:onboard.publish.photoMissing")}
                </dd>
              </div>
              <div className="onb-facts__row">
                <dt>{t("profile:onboard.publish.work")}</dt>
                <dd className={workValid ? "" : "onb-facts__missing"}>
                  {workValid ? t("profile:onboard.publish.done") : t("profile:onboard.publish.workMissing")}
                </dd>
              </div>
            </dl>
            <Field
              label={t(`profile:onboard.about.name_${kin}`)}
              value={name}
              onChange={setName}
              type="text"
              autoComplete="off"
              disabled={busy}
              required
            />
            <Field
              label={t(`profile:onboard.publish.phone_${kin === "self" ? "other" : kin}`)}
              value={childPhone}
              onChange={setChildPhone}
              type="tel"
              autoComplete="off"
              disabled={busy}
              required
            />
            <p className="caption onb-publish__hint">{t(`profile:onboard.publish.phoneHint_${kin === "self" ? "other" : kin}`)}</p>
            <span className="relpick__q">{t("circle:invite.askJoin")}</span>
            <RelationChips
              value={relation}
              busy={busy}
              role={forWhom === "son" || forWhom === "daughter" ? "parent" : forWhom === "sibling" ? "sibling" : undefined}
              onPick={setRelation}
            />
            <div className="onb-check">
              <span className={`onb-check__dot${verified ? " is-done" : ""}`} aria-hidden="true" />
              <span>
                <b>{t("profile:onboard.publish.checkTitle")}</b>
                <br />
                <span className="caption">
                  {verified ? t("profile:onboard.publish.checkDone") : t("profile:onboard.publish.checkHint")}
                </span>
              </span>
            </div>
          </>
        )}

        <p className="form__error" role="status" aria-live="polite">{error ?? ""}</p>

        <div className="form__actions">
          <SubmitButton
            label={primaryLabel}
            busy={busy}
            disabled={
              step === "work" && !forChild
                ? !(aboutValid && whereValid) || (!workValid && photos.length > 0)
                : step === "publish" && verified === false
                  ? !(photos.length > 0 && relation !== null && phoneValid && aboutValid && whereValid)
                  : !stepValid
            }
          />
          {step === "photos" && (
            <button type="button" className="link link--button" onClick={next}>
              {t("profile:onboard.photos.later")}
            </button>
          )}
          {step === "work" && (
            <>
              <button
                type="button"
                className="link link--button"
                disabled={busy}
                onClick={() => (forChild ? next() : void publish(true))}
              >
                {t("profile:onboard.work.skip")}
              </button>
              <p className="caption onb-skipnote">{t("profile:onboard.work.skipNote")}</p>
            </>
          )}
          {step === "publish" && (
            <button type="button" className="link link--button" onClick={keepDraft}>
              {t("profile:onboard.publish.notNow")}
            </button>
          )}
        </div>
      </form>
    </main>
  );
}
