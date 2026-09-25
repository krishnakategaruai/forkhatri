"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Vignette from "@/components/Vignette";
import { Suspense, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { Field } from "@/components/form/Field";
import { SubmitButton } from "@/components/form/SubmitButton";
import { requireSession } from "@/lib/auth";
import RelationChips from "@/components/RelationChips";
import { type Relation } from "@/lib/homeCircle";
import { createProfile, createProfileForChild } from "@/lib/profile";
import { getVerification } from "@/lib/verification";

/* FR001 · TR001 · UX11 · UI11 · TS001-002/TS010 · SP001 · DEC-V1-001
 *
 * [UX11] "Existence-tier wizard... a short linear sequence of only the fields
 * required to save at all — one or two fields per screen, progress indicator
 * ... no skip — these are the true minimum." DEC-V1-001 fixes the exact
 * field list: name, DOB, gender, city/locality, at least one photo.
 *
 * [UI11] Full-screen takeover, one field centered upper-middle third, steps
 * cross-fade into each other (fragments of one save action, never a slide
 * between separate destinations) — implemented here as a single mounted form
 * with a `step` index, so there is no route change (and no back-button
 * history entry) between steps, matching "fragments of one action."
 */

type Gender = "female" | "male" | "other";

const TOTAL_STEPS = 4;

const WIZARD_ART: Record<number, string> = {
  0: "family",
  1: "basics",
  2: "photos",
  3: "community",
  4: "partner",
};

/* [DEC-V1-019] `?for=child`: a parent (or other relation) creates the profile
 * for their son or daughter, as Shaadi.com's "profile for: son / daughter"
 * does. One extra step first — the child's mobile number, which is how the
 * child takes the profile over later, and how the creator is related — then
 * the same four steps, asked about the child. */
export default function CreateProfilePage() {
  return (
    <Suspense fallback={null}>
      <CreateProfileWizard />
    </Suspense>
  );
}

function CreateProfileWizard() {
  const { t } = useTranslation(["profile", "common", "circle", "verify"]);
  const router = useRouter();
  const forChild = useSearchParams().get("for") === "child";
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState(forChild ? 0 : 1);
  const [childPhone, setChildPhone] = useState("");
  const [relation, setRelation] = useState<Relation | null>(null);
  const offset = forChild ? 1 : 0;
  const totalSteps = TOTAL_STEPS + offset;
  const stepsKey = forChild ? "forSteps" : "steps";
  const [name, setName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState<Gender | "">("");
  const [lookingFor, setLookingFor] = useState<"bride" | "groom" | "">("");
  const [cityLocality, setCityLocality] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // [ForKhatri TR16] Confirm the ForKhatri session on arrival: signed out →
  // entrance; unreachable → the shared retry state. A failure while SAVING
  // keeps the inline error below so the member's answers are not lost.
  useEffect(() => {
    void requireSession();
  }, []);

  /* [DEC-V1-025] Only a verified person may create a profile for someone
     else: phone (sign-in OTP) and photos (the live face match). Checked
     before the form, so a parent is not asked to fill in five steps and be
     refused at the end. The server enforces the same rule. */
  const [gate, setGate] = useState<"checking" | "required" | "open">(
    forChild ? "checking" : "open",
  );
  useEffect(() => {
    if (!forChild) return;
    let active = true;
    void getVerification().then((s) => {
      // An unreachable check leaves the form open; the server still decides.
      if (active) setGate(s && !s.verified ? "required" : "open");
    });
    return () => {
      active = false;
    };
  }, [forChild]);

  function onPhotoChange(file: File | null) {
    setPhoto(file);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return file ? URL.createObjectURL(file) : null;
    });
  }

  const stepValid =
    (step === 0 &&
      relation !== null &&
      childPhone.replace(/\D/g, "").length >= 10) ||
    (step === 1 && name.trim().length > 0) ||
    (step === 2 && dateOfBirth !== "" && gender !== "" && lookingFor !== "") ||
    (step === 3 && cityLocality.trim().length > 0) ||
    (step === 4 && photo !== null);

  async function onNext(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (step < TOTAL_STEPS) {
      setStep((s) => s + 1);
      return;
    }
    if (!photo || !gender || !lookingFor) return;

    setBusy(true);
    if (forChild && relation) {
      const made = await createProfileForChild({
        name,
        dateOfBirth,
        gender,
        lookingFor,
        cityLocality,
        photo,
        childPhone,
        relation,
      });
      setBusy(false);
      if (made.ok) {
        router.push(`/me?manage=${made.accountId}`);
        return;
      }
      setError(
        made.kind === "network"
          ? t("profile:error.network")
          : (made.message ?? t("profile:error.network")),
      );
      return;
    }
    const result = await createProfile({
      name,
      dateOfBirth,
      gender,
      lookingFor,
      cityLocality,
      photo,
    });
    setBusy(false);

    if (result.ok) {
      router.push("/");
      return;
    }
    setError(
      result.kind === "network"
        ? t("profile:error.network")
        : (result.message ?? t("profile:error.network")),
    );
  }

  if (gate !== "open") {
    return (
      <main className="screen screen--form">
        {gate === "required" && (
          <div className="form wizard-step">
            <Vignette id="family" className="wizard-step__art" />
            <div className="wizard-step__head">
              <h1 className="h2">{t("verify:gate.title")}</h1>
              <p className="caption">{t("verify:gate.body")}</p>
            </div>
            <div className="form__actions">
              <button
                type="button"
                className="btn btn--primary"
                onClick={() =>
                  router.push(
                    `/me/verify?next=${encodeURIComponent("/profile/create?for=child")}`,
                  )
                }
              >
                {t("verify:gate.cta")}
              </button>
              <button
                type="button"
                className="link link--button"
                onClick={() => router.back()}
              >
                {t("verify:gate.later")}
              </button>
            </div>
          </div>
        )}
      </main>
    );
  }

  return (
    <>
      <main className="screen screen--form">
        {/* The step label sits in the same column as the question. It used
            to be in a full-width top bar, which on a desktop put it in the
            far corner of an otherwise empty page. */}
        <div className="wizard-top">
          <span className="caption">
            {t("profile:wizard.step", {
              current: step + offset,
              total: totalSteps,
            })}
          </span>
          <div className="progress" aria-hidden="true">
            <div
              className="progress__bar"
              style={{ width: `${((step + offset) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* [UI11] Steps cross-fade — a `key`-driven remount on the wizard body
            gives each step its own fade-in without a route change. */}
        <form
          className="form wizard-step"
          key={step}
          onSubmit={onNext}
          noValidate
        >
          {/* Each step asks its question out loud. Without a heading the
              screen was a lone input above a Next button, which says nothing
              about what is being asked or why it is worth answering. */}
          {/* One drawn moment per step: the kolam at the doorstep for the
              name, the photograph, the gopuram for where you live, and the
              garlands for who you are looking for. */}
          <Vignette
            id={WIZARD_ART[step] ?? "basics"}
            className="wizard-step__art"
          />
          <div className="wizard-step__head">
            <h1 className="h2">
              {t(`profile:wizard.${stepsKey}.${step}.title`)}
            </h1>
            <p className="caption">
              {t(`profile:wizard.${stepsKey}.${step}.hint`)}
            </p>
          </div>

          {step === 0 && (
            <>
              <Field
                label={t("profile:wizard.childPhone")}
                value={childPhone}
                onChange={setChildPhone}
                type="tel"
                autoComplete="off"
                disabled={busy}
                required
              />
              <span className="relpick__q">{t("circle:invite.askJoin")}</span>
              <RelationChips
                value={relation}
                busy={busy}
                onPick={setRelation}
              />
            </>
          )}

          {step === 1 && (
            <Field
              label={
                forChild
                  ? t("profile:wizard.childName")
                  : t("profile:field.name")
              }
              value={name}
              onChange={setName}
              type="text"
              autoComplete="name"
              disabled={busy}
              required
            />
          )}

          {step === 2 && (
            <>
              <label className="date-field">
                <span className="caption">
                  {t("profile:field.dateOfBirth")}
                </span>
                <input
                  type="date"
                  className="field__input date-field__input"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  max={new Date().toISOString().slice(0, 10)}
                  disabled={busy}
                  required
                />
              </label>
              <div
                className="segmented segmented--3"
                role="radiogroup"
                aria-label={t("profile:field.gender")}
              >
                {(["female", "male", "other"] as Gender[]).map((g) => (
                  <button
                    key={g}
                    type="button"
                    role="radio"
                    aria-checked={gender === g}
                    className={`segmented__opt${gender === g ? " is-active" : ""}`}
                    onClick={() => setGender(g)}
                    disabled={busy}
                  >
                    {t(`profile:field.genderOption.${g}`)}
                  </button>
                ))}
              </div>
              <span className="caption">
                {t("profile:field.partner_preference.looking_for")}
              </span>
              <div
                className="segmented"
                role="radiogroup"
                aria-label={t("profile:field.partner_preference.looking_for")}
              >
                {(["bride", "groom"] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    role="radio"
                    aria-checked={lookingFor === option}
                    className={`segmented__opt${lookingFor === option ? " is-active" : ""}`}
                    onClick={() => setLookingFor(option)}
                    disabled={busy}
                  >
                    {t(`profile:option.looking_for.${option}`)}
                  </button>
                ))}
              </div>
            </>
          )}

          {step === 3 && (
            <Field
              label={t("profile:field.cityLocality")}
              value={cityLocality}
              onChange={setCityLocality}
              type="text"
              autoComplete="address-level2"
              disabled={busy}
              required
            />
          )}

          {step === 4 && (
            <div className="photo-picker">
              <button
                type="button"
                className="photo-picker__dropzone"
                onClick={() => fileInputRef.current?.click()}
                disabled={busy}
              >
                {photoPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={photoPreview}
                    alt=""
                    className="photo-picker__preview"
                  />
                ) : (
                  <span className="caption">{t("profile:photo.empty")}</span>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                onChange={(e) => onPhotoChange(e.target.files?.[0] ?? null)}
              />
              {photoPreview && (
                <button
                  type="button"
                  className="link link--button"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {t("profile:photo.change")}
                </button>
              )}
            </div>
          )}

          <p className="form__error" role="status" aria-live="polite">
            {error ?? ""}
          </p>

          <div className="form__actions">
            <SubmitButton
              label={
                busy
                  ? t("profile:wizard.saving")
                  : step < TOTAL_STEPS
                    ? t("profile:wizard.next")
                    : t("profile:wizard.save")
              }
              busy={busy}
              disabled={!stepValid}
            />
          </div>
        </form>
      </main>
    </>
  );
}
