"use client";

// ======================================================================
// [TR011 → FE1 rebuild, 2026-09-28] Post an opportunity — AI-first,
// structured, type-specific.
//
// REQUIREMENT (owner): minimise typing on both sides; one structured
// composer per action; a genuine desktop layout; every string translated.
// Research (references/2026-screen-research.md §1, §5, §9):
//  - Start with one box, "Describe what you need", with a mic and "Read
//    from a photo". draftOpportunity / readOpportunityImage turn it into a
//    typed draft; values the draft is unsure of are marked "please check",
//    and each missing detail is asked as one question chip answered in
//    place. "Fill in myself" opens the empty form; the old share and
//    upload modes (FR11) stay available.
//  - Type-specific sections in the researched order (see ComposerForm).
//  - Skills from the real taxonomy (SkillPicker).
//  - Before publishing, "Get more responses": getOpportunitySuggestions +
//    getPostingTips merged into one-tap cards (ReviewStep).
//  - A live preview of what applicants will see: side panel on desktop,
//    collapsible on a phone.
//  - Publish-gate errors (salary_required, budget_required,
//    seeker_charge_not_allowed) land on the field they concern, localized.
// Two steps after the start (Details, Check & publish); NN/g: a step label
// is enough for two steps, no progress bar.
// Prefill: /opportunities/new?type=<employment|freelance|local_service>&skills=a,b
// (FE2's outcome pages link here).
// Traces to: FR11, FR12, FR14, TR011, TR014, imp-backend-a §1, imp-backend-c §1–4
// ======================================================================

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { ApiError, type Me, type Opportunity, type OpportunitySuggestion, type PostingTip } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import ProfileSetup from "@/app/components/ProfileSetup";
import { useTaxonomyAliases, useTaxonomyTree } from "@/app/hooks/hiring";
import ComposerForm, { fieldLabel, useComposerControls } from "@/app/components/composer/ComposerForm";
import OpportunityPreview from "@/app/components/composer/OpportunityPreview";
import ReviewStep from "@/app/components/composer/ReviewStep";
import StartPanel from "@/app/components/composer/StartPanel";
import LegacyComposer from "@/app/components/composer/LegacyComposer";
import AcceptancePrompt, { acceptanceKind, type LegalKind } from "@/app/components/respond/AcceptancePrompt";
import { fieldAnchor } from "@/app/components/composer/fields";
import {
  draftFromAi,
  retypeAiDraft,
  emptyDraft,
  isPostKind,
  mergeFixes,
  MUST_CHECK,
  toWrite,
  validate,
  type ComposerDraft,
  type FieldCode,
  type FixKey,
  type PostKind,
} from "@/app/components/composer/draft";

type Stage = "start" | "form" | "review";

/** Which form field a server error code belongs to. */
const ERROR_FIELD: Record<string, FieldCode> = {
  salary_required: "salary",
  salary_range_invalid: "salary",
  budget_required: "budget",
  budget_range_invalid: "budget",
  budget_fields_mismatch: "budget",
  experience_range_invalid: "experience",
  too_many_screening_questions: "screening_questions",
};

function Composer() {
  const { t, i18n } = useTranslation(["hiring", "opportunities", "common"]);
  const sdk = useSdk();
  const router = useRouter();
  const params = useSearchParams();
  const tree = useTaxonomyTree();
  const aliases = useTaxonomyAliases();

  // Prefill from ?type=&skills= (outcome pages, "Post a similar job").
  const prefillType = params.get("type");
  const prefillSkills = (params.get("skills") ?? "").split(",").map((s) => s.trim()).filter(Boolean);
  const initialKind: PostKind | null = isPostKind(prefillType) ? prefillType : null;

  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    sdk.members.me().then(setMe).catch(() => setMe(null));
  }, [sdk, i18n.language]);

  // [FE1 — 2026-09-30, owner: "never ask what we know"] The member's saved
  // locality (set at first run; else the one on their work/business
  // profile) prefills the post's area once, on entering the form. Anything
  // they then type or clear is theirs — it is never re-filled.
  const [firstRunLocality, setFirstRunLocality] = useState<string | null>(null);
  useEffect(() => {
    sdk.firstRun
      .state()
      .then((s) => setFirstRunLocality(((s as unknown as { locality?: string | null }).locality ?? "").trim() || null))
      .catch(() => setFirstRunLocality(null));
  }, [sdk]);
  const savedLocality = firstRunLocality ?? me?.profiles?.professional?.locality ?? me?.profiles?.business?.locality ?? null;

  // [FE1 — 2026-09-29, owner: "that is too worst" — the floating hub sat on
  // top of mid-form fields] Phone: a sticky bottom bar carries the primary
  // action for the whole of the form/review stage (same `.vy-actionbar` used
  // by OpportunityDetailView), and the bottom hub lifts clear of it via the
  // existing `body:has(.vy-actionbar-in)` rule, so the hub never sits over
  // the fields. The in-page row stays for desktop, where `.vy-actionbar` is
  // CSS-hidden (≥900px already has a persistent side layout).
  const [stage, setStage] = useState<Stage>("start");
  const [legacy, setLegacy] = useState<{ mode: "share" | "upload"; imageUrl?: string; notice?: string } | null>(null);
  const [kind, setKind] = useState<PostKind | null>(initialKind);
  const [text, setText] = useState("");
  const [spoken, setSpoken] = useState(false);
  const [busy, setBusy] = useState<"draft" | "photo" | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  // [Critique L7] One photo button. When reading photos isn't available here
  // (501/503 — learnt once per session), the same tap simply attaches the
  // photo on this screen; the text box becomes its note and the photo is
  // kept with the post. No detour to another screen.
  const [attachedImage, setAttachedImage] = useState<string | null>(null);

  const [draft, setDraft] = useState<ComposerDraft>(() => emptyDraft(initialKind ?? "employment", prefillSkills));
  const [flagged, setFlagged] = useState<Set<FieldCode>>(new Set());
  const [questions, setQuestions] = useState<{ code: FieldCode; question: string }[]>([]);
  const [openQuestion, setOpenQuestion] = useState<FieldCode | null>(null);
  const [fromAi, setFromAi] = useState<"ai" | "rules" | null>(null);
  const [errors, setErrors] = useState<Partial<Record<FieldCode, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);

  const [saved, setSaved] = useState<Opportunity | null>(null);
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState<OpportunitySuggestion[]>([]);
  const [tips, setTips] = useState<PostingTip[]>([]);
  const [loadingFixes, setLoadingFixes] = useState(false);
  const [applying, setApplying] = useState<FixKey | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [needsAccept, setNeedsAccept] = useState<LegalKind | null>(null);

  const skillLabel = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of tree.data?.categories ?? []) for (const s of c.children ?? []) m.set(s.slug, s.label);
    return (slug: string) => m.get(slug) ?? slug;
  }, [tree.data]);

  function change(patch: Partial<ComposerDraft>) {
    setDraft((d) => ({ ...d, ...patch }));
    // Touching a field is looking at it: drop its "please check" and its error.
    const touched = Object.keys(patch);
    const codes = new Set<FieldCode>();
    const map: Record<string, FieldCode[]> = {
      title: ["title"], location: ["location"], description: ["description"], skills: ["required_capabilities"],
      salaryMin: ["salary"], salaryMax: ["salary"], incentiveType: ["incentive_type"], incentiveMax: ["incentive_type"],
      openings: ["openings"], shift: ["shift"], jobTimings: ["job_timings"], experienceMonths: ["experience"],
      qualification: ["min_qualification"], english: ["english_level"], assets: ["requires_assets"], interview: ["interview_details"],
      budgetType: ["budget"], budgetMin: ["budget"], budgetMax: ["budget"], localBudget: ["budget"], duration: ["duration"],
      experienceLevel: ["experience_level"], questions: ["screening_questions"], urgency: ["urgency"], preferredDate: ["preferred_date"],
      type: ["type"], workMode: ["work_mode"], deadline: ["deadline"], allowPrecall: [], precallChannel: [], segment: ["type"], sourceName: ["type"], timing: ["timing"],
    };
    for (const k of touched) for (const c of map[k] ?? []) codes.add(c);
    if (codes.size) {
      setFlagged((f) => new Set([...f].filter((c) => !codes.has(c))));
      setErrors((e) => Object.fromEntries(Object.entries(e).filter(([c]) => !codes.has(c as FieldCode))));
    }
  }

  function errorText(e: unknown): string {
    if (e instanceof ApiError) {
      const matched = typeof e.details?.matched === "string" ? e.details.matched : "";
      if (e.code) return t(`hiring:errors.${e.code}`, { defaultValue: typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"), matched });
      if (typeof e.detail === "string") return e.detail;
    }
    return t("common:state.somethingWentWrong");
  }

  function goToField(code: FieldCode) {
    setStage("form");
    requestAnimationFrame(() => {
      const el = document.getElementById(fieldAnchor(code));
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
      (el?.querySelector("input, textarea, button") as HTMLElement | null)?.focus({ preventScroll: true });
    });
  }

  /** Put a server error next to its field (and go back to the form) or show it under the button. */
  function placeError(e: unknown) {
    const legal = acceptanceKind(e);
    if (legal) {
      setNeedsAccept(legal);
      return;
    }
    const msg = errorText(e);
    if (e instanceof ApiError && e.code) {
      let field: FieldCode | undefined = ERROR_FIELD[e.code];
      if (e.code === "seeker_charge_not_allowed" && e.details?.field !== "candidate_pays") {
        const m = String(e.details?.matched ?? "").toLowerCase();
        field = m && draft.title.toLowerCase().includes(m) ? "title" : m && draft.interview.toLowerCase().includes(m) ? "interview_details" : m && draft.jobTimings.toLowerCase().includes(m) ? "job_timings" : m && draft.questions.join(" ").toLowerCase().includes(m) ? "screening_questions" : "description";
      }
      if (field) {
        setErrors((x) => ({ ...x, [field as FieldCode]: msg }));
        goToField(field);
        return;
      }
    }
    setFormError(msg);
  }

  // ---- start: AI draft ------------------------------------------------------
  function applyAi(ai: Parameters<typeof draftFromAi>[0]) {
    const base = kind ? { ...draft, type: kind } : draft;
    // The type the poster tapped wins over the type the draft inferred.
    const r = draftFromAi(kind ? retypeAiDraft(ai, kind) : ai, base);
    setDraft(r.draft.location.trim() || !savedLocality ? r.draft : { ...r.draft, location: savedLocality });
    setFlagged(new Set(r.flagged));
    setQuestions(r.questions);
    setFromAi(ai.source);
    setErrors({});
    setStage("form");
    window.scrollTo({ top: 0 });
  }

  async function onDraft(entry: "text" | "voice") {
    setBusy("draft");
    setStartError(null);
    try {
      applyAi(await sdk.ai.draftOpportunity({ text: text.trim(), language: i18n.language, entry }));
    } catch (e) {
      setStartError(errorText(e));
    } finally {
      setBusy(null);
    }
  }

  function photoReadingOff(): boolean {
    try {
      return sessionStorage.getItem("vyapar.aiPhoto") === "off";
    } catch {
      return false;
    }
  }

  async function onPhoto(file: File) {
    setBusy("photo");
    setStartError(null);
    let url = "";
    try {
      url = (await sdk.uploads.upload(file)).url;
      setAttachedImage(url);
      if (photoReadingOff()) return;
      applyAi(await sdk.ai.readOpportunityImage({ image_url: url, language: i18n.language }));
    } catch (e) {
      if (url && e instanceof ApiError && (e.status === 501 || e.status === 503)) {
        try {
          sessionStorage.setItem("vyapar.aiPhoto", "off");
        } catch {
          /* private mode: ask again next time */
        }
      } else {
        setStartError(errorText(e));
      }
    } finally {
      setBusy(null);
    }
  }

  // ---- details → review -------------------------------------------------------
  async function saveDraft(d: ComposerDraft): Promise<Opportunity> {
    const body = toWrite(d);
    if (saved) return sdk.posting.update(saved.id, body);
    return sdk.posting.create({
      ...body,
      entry_mode: "create",
      raw_image_url: attachedImage ?? undefined,
      source_segment: d.segment,
      source_name: d.segment === "public" ? d.sourceName.trim() : undefined,
    });
  }

  async function loadFixes(id: string, withTips: boolean) {
    setLoadingFixes(true);
    const [s, tp] = await Promise.allSettled([
      sdk.posting.suggestions(id),
      withTips ? sdk.ai.getPostingTips({ opportunity_id: id, language: i18n.language }) : Promise.resolve(null),
    ]);
    if (s.status === "fulfilled") setSuggestions(s.value.suggestions);
    if (tp.status === "fulfilled" && tp.value) setTips(tp.value.tips);
    setLoadingFixes(false);
  }

  async function toReview() {
    setFormError(null);
    const problems = validate(draft);
    const localized = Object.fromEntries(Object.entries(problems).map(([c, k]) => [c, t(`hiring:composer.error.${k}`)])) as Partial<Record<FieldCode, string>>;
    if (Object.keys(localized).length) {
      setErrors(localized);
      goToField(Object.keys(localized)[0] as FieldCode);
      return;
    }
    setSaving(true);
    try {
      const opp = await saveDraft(draft);
      setSaved(opp);
      setStage("review");
      window.scrollTo({ top: 0 });
      void loadFixes(opp.id, true);
    } catch (e) {
      placeError(e);
    } finally {
      setSaving(false);
    }
  }

  async function applyFix(key: FixKey, patch: Partial<ComposerDraft>) {
    if (!saved) return;
    const next = { ...draft, ...patch };
    setApplying(key);
    change(patch);
    try {
      const opp = await sdk.posting.update(saved.id, toWrite(next));
      setSaved(opp);
      await loadFixes(opp.id, false);
    } catch (e) {
      placeError(e);
    } finally {
      setApplying(null);
    }
  }

  async function publish() {
    if (!saved) return;
    setPublishing(true);
    setFormError(null);
    try {
      // The poster has just reviewed every field on this screen, so any the
      // server still marks unconfirmed (title/location it defaulted) are
      // confirmed as seen — the FR12 gate is kept, not bypassed.
      if (saved.unconfirmed_fields.length) await sdk.posting.confirm(saved.id, saved.unconfirmed_fields);
      await sdk.posting.publish(saved.id);
      router.push(`/opportunities/${saved.id}`);
    } catch (e) {
      placeError(e);
      setPublishing(false);
    }
  }

  // [Critique L8] Amounts and openings the draft filled must be looked at
  // before publishing; the other "please check" marks stay advisory.
  const mustCheck = [...flagged].filter((c) => MUST_CHECK.includes(c));
  const fixes = useMemo(() => mergeFixes(suggestions, tips, draft), [suggestions, tips, draft]);
  const { renderControl } = useComposerControls({ draft, onChange: change, tree: tree.data, errors, aliases });
  const openQuestions = questions.filter((q) => {
    const val: Record<string, boolean> = {
      salary: !!draft.salaryMin && !!draft.salaryMax,
      openings: draft.openings !== null,
      shift: draft.shift !== null,
      job_timings: !!draft.jobTimings.trim(),
      interview_details: !!draft.interview.trim(),
      min_qualification: draft.qualification !== null,
      english_level: draft.english !== null,
      experience: draft.experienceMonths !== null,
      requires_assets: draft.assets.length > 0,
      budget: draft.type === "freelance" ? !!draft.budgetMin && !!draft.budgetMax : !!draft.localBudget,
      duration: draft.duration !== null,
      experience_level: draft.experienceLevel !== null,
      screening_questions: draft.questions.some(Boolean),
      preferred_date: !!draft.preferredDate,
      urgency: draft.urgency !== null,
      location: !!draft.location.trim(),
      title: !!draft.title.trim(),
      required_capabilities: draft.skills.length > 0,
      description: !!draft.description.trim(),
      incentive_type: draft.incentiveType !== "none",
      work_mode: !!draft.workMode,
      timing: !!draft.timing.trim(),
    };
    return !val[q.code];
  });

  if (me?.profiles && !me.profiles.complete) {
    return (
      <Screen width="wide">
        <h1>{t("hiring:composer.startTitle")}</h1>
        <ProfileSetup profiles={me.profiles} required />
      </Screen>
    );
  }

  if (legacy) {
    return (
      <Screen width="wide">
        <LegacyComposer
          mode={legacy.mode}
          initialImageUrl={legacy.imageUrl}
          initialType={kind ?? "employment"}
          tree={tree.data}
          notice={legacy.notice}
          onBack={() => setLegacy(null)}
        />
      </Screen>
    );
  }

  if (stage === "start") {
    return (
      <Screen width="wide">
        <div className="vy-compose">
          <div className="vy-compose-main">
            <StartPanel
              text={text}
              onText={(v) => {
                setText(v);
                if (!v.trim()) setSpoken(false);
              }}
              kind={kind}
              onKind={(k) => {
                setKind(k);
                if (k) setDraft((d) => ({ ...d, type: k }));
              }}
              busy={busy}
              error={startError}
              onDraft={onDraft}
              onPhoto={onPhoto}
              onManual={() => {
                setDraft((d) => ({ ...d, type: kind ?? d.type, location: d.location.trim() || savedLocality || "" }));
                setStage("form");
              }}
              onLegacy={(mode) => setLegacy({ mode })}
              spoken={spoken}
              onSpoken={() => setSpoken(true)}
              attachedImage={attachedImage}
              attachedImageSrc={attachedImage ? sdk.uploads.resolveUrl(attachedImage) : null}
              onRemoveImage={() => setAttachedImage(null)}
            />
          </div>
          <aside className="vy-compose-aside" aria-label={t("hiring:composer.howTitle")}>
            <span className="vy-preview-label">{t("hiring:composer.howTitle")}</span>
            <ol className="vy-howto">
              <li><span><strong>{t("hiring:composer.how1Title")}</strong>{t("hiring:composer.how1")}</span></li>
              <li><span><strong>{t("hiring:composer.how2Title")}</strong>{t("hiring:composer.how2")}</span></li>
              <li><span><strong>{t("hiring:composer.how3Title")}</strong>{t("hiring:composer.how3")}</span></li>
            </ol>
            <p className="vy-safety-line">{t("hiring:composer.freeNote")}</p>
          </aside>
        </div>
      </Screen>
    );
  }

  const preview = <OpportunityPreview draft={draft} skillLabel={skillLabel} posterName={me?.display_name} />;

  return (
    <Screen width="wide" className="vy-composer-screen">
      <div className="vy-stack" style={{ gap: 6 }}>
        <span className="vy-step-label">
          {stage === "form" ? t("hiring:composer.step1") : t("hiring:composer.step2")}
        </span>
        <h1>{stage === "form" ? t(`hiring:composer.formTitle.${draft.type}`, { defaultValue: t("hiring:composer.formTitle.other") }) : t("hiring:composer.reviewTitle")}</h1>
      </div>
      <div className="vy-compose">
        <div className="vy-compose-main">
          {stage === "form" && (
            <>
              {fromAi && (
                <div className="vy-card vy-card-nested vy-stack" style={{ gap: 10, padding: 16 }}>
                  <p style={{ color: "var(--text-primary)", fontSize: 14 }}>
                    {flagged.size > 0 ? t("hiring:composer.draftedCheck", { count: flagged.size }) : t("hiring:composer.drafted")}
                  </p>
                  {openQuestions.length > 0 && (
                    <div className="vy-questions">
                      <span className="vy-field-hint">{t("hiring:composer.questionsIntro")}</span>
                      {openQuestions.map((q) => (
                        <div key={q.code} className="vy-question">
                          <button type="button" aria-expanded={openQuestion === q.code} onClick={() => setOpenQuestion(openQuestion === q.code ? null : q.code)}>
                            <span>{q.question || t(`hiring:composer.ask.${q.code}`, { defaultValue: fieldLabel(t, q.code, draft.type) })}</span>
                            <span aria-hidden="true">{openQuestion === q.code ? "−" : "+"}</span>
                          </button>
                          {openQuestion === q.code && (
                            <div className="vy-stack" style={{ gap: 6 }}>
                              <span className="vy-visually-hidden">{fieldLabel(t, q.code, draft.type)}</span>
                              {renderControl(q.code)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <ComposerForm
                draft={draft}
                onChange={change}
                tree={tree.data}
                aliases={aliases}
                flagged={flagged}
                onLooksRight={(code) => setFlagged((f) => new Set([...f].filter((c) => c !== code)))}
                errors={errors}
              />

              <details className="vy-mobile-only vy-card vy-card-nested" style={{ padding: "14px 18px" }}>
                <summary style={{ cursor: "pointer", fontWeight: 600 }}>{t("hiring:preview.toggle")}</summary>
                <div style={{ marginTop: 12 }}>{preview}</div>
              </details>

              {formError && <p className="vy-error" role="alert">{formError}</p>}
              {/* Wrapped, not combined: .vy-row / .vy-btn set display too and
                  would out-cascade the breakpoint utility on the same element. */}
              <div className="vy-desktop-only">
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                  <button type="button" className="vy-btn vy-btn-primary vy-submit" disabled={saving} onClick={toReview}>
                    {saving ? t("common:state.saving") : t("hiring:composer.continueToCheck")}
                  </button>
                  <button type="button" className="vy-btn vy-btn-ghost" onClick={() => setStage("start")}>
                    ← {t("hiring:composer.backToStart")}
                  </button>
                </div>
              </div>
              <div className="vy-mobile-only">
                <button type="button" className="vy-btn vy-btn-ghost" onClick={() => setStage("start")}>
                  ← {t("hiring:composer.backToStart")}
                </button>
              </div>
            </>
          )}

          {stage === "review" && (
            <>
              <ReviewStep draft={draft} fixes={fixes} loadingFixes={loadingFixes} applying={applying} onApply={applyFix} onEdit={goToField} />
              {flagged.size > 0 && (
                <p className={mustCheck.length ? "vy-error" : "vy-field-hint"} role={mustCheck.length ? "alert" : undefined}>
                  {mustCheck.length
                    ? t("hiring:composer.checkBeforePublish", { fields: mustCheck.map((c) => fieldLabel(t, c, draft.type)).join(", "), ok: t("hiring:composer.looksRight") })
                    : t("hiring:composer.stillUnchecked", { fields: [...flagged].map((c) => fieldLabel(t, c, draft.type)).join(", ") })}{" "}
                  <button type="button" className="vy-check-ok" onClick={() => goToField([...flagged][0])}>
                    {t("hiring:composer.checkNow")}
                  </button>
                </p>
              )}
              <div className="vy-mobile-only">{preview}</div>
              {needsAccept && (
                <AcceptancePrompt
                  kind={needsAccept}
                  onAccepted={() => {
                    setNeedsAccept(null);
                    void publish();
                  }}
                />
              )}
              {formError && <p className="vy-error" role="alert">{formError}</p>}
              <div className="vy-desktop-only">
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                  <button type="button" className="vy-btn vy-btn-primary vy-submit" disabled={publishing || applying !== null || mustCheck.length > 0} onClick={publish}>
                    {publishing ? t("hiring:composer.publishing") : t("hiring:composer.publish")}
                  </button>
                  <button type="button" className="vy-btn vy-btn-secondary" onClick={() => setStage("form")}>
                    {t("hiring:composer.editDetails")}
                  </button>
                </div>
              </div>
              <div className="vy-mobile-only">
                <button type="button" className="vy-btn vy-btn-secondary" onClick={() => setStage("form")}>
                  {t("hiring:composer.editDetails")}
                </button>
              </div>
              <p className="vy-field-hint">{t("hiring:composer.draftSavedNote")}</p>
            </>
          )}
        </div>

        <aside className="vy-compose-aside" aria-label={t("hiring:preview.label")}>
          <span className="vy-preview-label">{t("hiring:preview.label")}</span>
          <p className="vy-preview-caption">{t("hiring:preview.caption")}</p>
          {preview}
        </aside>
      </div>

      {(stage === "form" || stage === "review") && (
        <div className="vy-actionbar vy-actionbar-in vy-mobile-only">
          <div className="vy-actionbar-main">
            {stage === "form" ? (
              <button type="button" className="vy-btn vy-btn-primary" disabled={saving} onClick={toReview}>
                {saving ? t("common:state.saving") : t("hiring:composer.continueToCheck")}
              </button>
            ) : (
              <button type="button" className="vy-btn vy-btn-primary" disabled={publishing || applying !== null || mustCheck.length > 0} onClick={publish}>
                {publishing ? t("hiring:composer.publishing") : t("hiring:composer.publish")}
              </button>
            )}
          </div>
        </div>
      )}
    </Screen>
  );
}

export default function NewOpportunityPage() {
  return (
    <Suspense fallback={null}>
      <Composer />
    </Suspense>
  );
}
