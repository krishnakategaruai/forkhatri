"use client";

// [TR001/TR004] Set up the member's Vyapar profile (FR04) or its optional
// business section (FR01). One endpoint today (POST /v1/listings).
//
// [Owner, 2026-09-30: "each user will get one profile"] This screen never
// makes a second profile. With no `kind`, or kind=professional, it sets up
// THE work profile; if that already exists it opens it instead. With
// kind=business it adds the business section; if that exists, it opens it.
// A 409 `profile_exists` from the API (backend A's one-profile rule) sends
// the member back to their profile.
//
// [Owner, 2026-09-30: "i already logged in as user, but still it is asking
// me this" / "locality can be taken current right"] Nothing already known is
// asked again. Name, locality, skills picked at first run and how the member
// works are prefilled from useMyProfile (identity + first run). When name and
// locality are both known, the "who you are" step disappears and the member
// lands on "What you do", with one quiet line "Meena Sahni · Himayatnagar ·
// Change". A missing locality offers "Use my current location" first.
//
// [Owner, 2026-09-29: "real ugly"] Short steps in the 2026 language: the
// taxonomy SkillPicker in its closed, search-first mode (no chip wall), a
// segmented control instead of a native <select>, +91 inside the phone
// field, one brand button per step in a thumb-zone action bar (the hub steps
// aside), "Save and finish later" as a quiet action, and the reason a button
// is disabled written under it. No AI drafting: the API has no draft-listing
// endpoint yet (only opportunities).
// Traces to: FR01, FR04, TR001, TR004
import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import DisabledReason from "@/app/components/DisabledReason";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import { SkeletonGrid } from "@/app/components/States";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";
import PageHeader from "@/app/components/account/PageHeader";
import Steps from "@/app/components/account/Steps";
import Segmented from "@/app/components/account/Segmented";
import LocalityField from "@/app/components/account/LocalityField";
import { useMyProfile } from "@/app/components/account/useMyProfile";
import { useTaxonomyAliases, useTaxonomyTree } from "@/app/hooks/hiring";
import "@/app/styles/account-2026.css";

type Kind = "business" | "professional";
type ServiceMode = "on_site" | "remote" | "both";
type StepId = "who" | "what" | "contact";

interface TaxonomyOption {
  slug: string;
  label: string;
}

const CATEGORIES_FOLDED = 8;

function NewListingInner() {
  const { t, i18n } = useTranslation(["listings", "common", "discover"]);
  const router = useRouter();
  const params = useSearchParams();
  const kind: Kind = params.get("kind") === "business" ? "business" : "professional";
  const business = kind === "business";
  const profile = useMyProfile();
  const me = profile.data;

  // Edited values; null = "not touched, use what the app already knows".
  const [nameEdit, setName] = useState<string | null>(null);
  const [localityEdit, setLocality] = useState<string | null>(null);
  const [capsEdit, setCapabilities] = useState<string[] | null>(null);
  const [modeEdit, setServiceMode] = useState<ServiceMode | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [editWho, setEditWho] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [headline, setHeadline] = useState("");
  const [categoryOptions, setCategoryOptions] = useState<TaxonomyOption[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [allCategories, setAllCategories] = useState(false);
  const [capabilitiesOther, setCapabilitiesOther] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [existingId, setExistingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const tree = useTaxonomyTree();
  const aliases = useTaxonomyAliases();

  const name = nameEdit ?? (business ? "" : (me?.name ?? ""));
  const locality = localityEdit ?? me?.locality ?? "";
  const capabilities = capsEdit ?? (business ? [] : (me?.skills ?? []));
  const serviceMode: ServiceMode = modeEdit ?? me?.workMode ?? "both";

  // One profile: if the thing being set up already exists, open it.
  const existing = me ? (business ? me.business : me.work) : null;
  useEffect(() => {
    if (existing) router.replace(`/listings/${existing.id}`);
  }, [existing, router]);

  // Labels come from the API in the reader's language.
  useEffect(() => {
    if (!business) return;
    api.get<{ categories: TaxonomyOption[] }>("/v1/listings/search-suggestions").then((d) => setCategoryOptions(d.categories));
  }, [business, i18n.language]);

  const skillLabel = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of tree.data?.categories ?? []) for (const s of c.children ?? []) m.set(s.slug, s.label);
    return m;
  }, [tree.data]);

  if (!me || existing) {
    return (
      <Screen>
        <div className="vy-skeleton" style={{ height: 40, width: 260, maxWidth: "70%" }} aria-hidden="true" />
        <SkeletonGrid count={2} grid={false} />
      </Screen>
    );
  }

  // The "who" step only when something is missing (always for a business:
  // its name is not the member's name) or the member asked to change it.
  const whoKnown = !business && !!me.name.trim() && !!(me.locality ?? "").trim();
  // The phone is known from the ForKhatri identity: nothing to ask then.
  const phoneKnown = !!me.phone;
  const steps: StepId[] = [
    ...(whoKnown && !editWho ? [] : (["who"] as StepId[])),
    "what",
    ...(phoneKnown ? [] : (["contact"] as StepId[])),
  ];
  const step = steps[Math.min(stepIndex, steps.length - 1)];
  const requiredOk = name.trim().length > 0 && locality.trim().length > 0;
  const stepTitle: Record<StepId, string> = {
    who: business ? t("listings:new.step.whoBusiness") : t("listings:new.step.who"),
    what: business ? t("listings:new.step.whatBusiness") : t("listings:new.step.what"),
    contact: t("listings:new.step.contact"),
  };
  const blockedReason = !name.trim()
    ? business
      ? t("listings:new.reasonNameBusiness")
      : t("listings:new.reasonName")
    : !locality.trim()
      ? t("listings:new.reasonLocality")
      : null;

  function toggleCategory(slug: string) {
    setCategories((c) => (c.includes(slug) ? c.filter((x) => x !== slug) : [...c, slug]));
  }

  async function submit() {
    setSaving(true);
    setError(null);
    setExistingId(null);
    const tel = phone ? `+91${digits(phone)}` : undefined;
    try {
      // [Owner, 2026-09-30: one profile] PATCH /v1/me/profile creates the one
      // profile on its first call, or adds the business section; never POST
      // a second listing when the one-profile endpoint is live.
      if (me?.source === "me-profile") {
        const skills = [...capabilities, ...splitList(capabilitiesOther)];
        const body: Record<string, unknown> = business
          ? {
              business: { name: name.trim() },
              ...(categories.length ? { categories } : {}),
              ...(skills.length ? { capabilities: Array.from(new Set([...(me.skills ?? []), ...skills])) } : {}),
              ...(me.exists ? {} : { locality: locality.trim(), lat: coords?.lat ?? me.lat ?? undefined, lng: coords?.lng ?? me.lng ?? undefined }),
            }
          : {
              name: name.trim(),
              headline: headline.trim() || undefined,
              capabilities: skills,
              locality: locality.trim(),
              lat: coords?.lat ?? me.lat ?? undefined,
              lng: coords?.lng ?? me.lng ?? undefined,
              service_mode: serviceMode,
              ...(tel ? { primary_phone: tel } : {}),
            };
        const r = await api.patch<{ profile?: { id?: string } | null }>("/v1/me/profile", body);
        router.push(r?.profile?.id ? `/listings/${r.profile.id}` : "/profile");
        return;
      }
      const listing = await api.post<{ id: string }>("/v1/listings", {
        kind,
        name: name.trim(),
        headline: !business ? headline.trim() || undefined : undefined,
        categories: business ? categories : [],
        capabilities: [...capabilities, ...splitList(capabilitiesOther)],
        locality: locality.trim(),
        lat: coords?.lat ?? me?.lat ?? undefined,
        lng: coords?.lng ?? me?.lng ?? undefined,
        service_mode: serviceMode,
        primary_phone: tel,
        contacts: tel ? [{ channel: "phone", value: tel, disclosure: "after_accept" }] : [],
      });
      router.push(`/listings/${listing.id}`);
    } catch (e) {
      if (e instanceof ApiError) {
        const detail = e.detail as unknown;
        const code = typeof detail === "object" && detail ? (detail as { code?: string }).code : undefined;
        if (e.status === 409 && code === "profile_exists") {
          router.replace("/profile");
          return;
        }
        if (e.status === 409 && typeof detail === "object" && detail && "existing_listing_id" in detail) {
          const d = detail as { message: string; existing_listing_id: string };
          setError(d.message);
          setExistingId(d.existing_listing_id);
        } else {
          setError(typeof detail === "string" ? detail : t("common:state.somethingWentWrong"));
        }
      } else {
        setError(t("common:state.somethingWentWrong"));
      }
    } finally {
      setSaving(false);
    }
  }

  const pickedLabels = [
    ...(business ? categoryOptions.filter((c) => categories.includes(c.slug)).map((c) => c.label) : []),
    ...capabilities.map((s) => skillLabel.get(s) ?? s),
    ...splitList(capabilitiesOther),
  ];
  const serviceModeOptions = [
    { value: "on_site" as ServiceMode, label: t("listings:new.serviceModeOnSite") },
    { value: "remote" as ServiceMode, label: t("listings:new.serviceModeRemote") },
    { value: "both" as ServiceMode, label: t("listings:new.serviceModeBoth") },
  ];
  const serviceModeLabel = serviceModeOptions.find((o) => o.value === serviceMode)?.label;
  const visibleCategories = allCategories ? categoryOptions : categoryOptions.slice(0, CATEGORIES_FOLDED);
  const hiddenPicked = categoryOptions.slice(CATEGORIES_FOLDED).filter((c) => categories.includes(c.slug));
  const last = stepIndex >= steps.length - 1;

  function back() {
    if (stepIndex > 0) setStepIndex(stepIndex - 1);
    else router.push("/profile");
  }

  return (
    <Screen width="wide">
      <PageHeader
        title={business ? t("listings:new.titleBusiness") : t("listings:new.titleProfessional")}
        backLabel={stepIndex > 0 ? t("common:action.back") : t("common:nav.profile")}
        onBack={back}
      />

      <div className="vy-compose">
        <div className="vy-compose-main">
          <div className="vy-acct-form">
            <Steps
              step={stepIndex + 1}
              total={steps.length}
              label={stepTitle[step]}
              stepLabel={t("listings:new.step.of", { step: stepIndex + 1, total: steps.length })}
            />

            {step === "what" && whoKnown && !editWho && (
              <p className="vy-acct-meta" style={{ marginTop: -4 }}>
                <span className="vy-acct-strong">{name}</span>
                <span aria-hidden="true">·</span>
                <span>{locality}</span>
                {me.phone && (
                  <>
                    <span aria-hidden="true">·</span>
                    <span className="vy-num">{me.phone}</span>
                  </>
                )}
                <button type="button" className="vy-acct-quiet" style={{ minHeight: 44, paddingInline: 8 }} onClick={() => { setEditWho(true); setStepIndex(0); }}>
                  {t("listings:new.change")}
                </button>
              </p>
            )}

            {step === "who" && (
              <>
                <div className="vy-acct-field">
                  <label className="vy-label" htmlFor="np-name">
                    {business ? t("listings:new.nameLabelBusiness") : t("listings:new.nameLabelProfessional")}
                  </label>
                  <input
                    id="np-name"
                    className="vy-input"
                    value={name}
                    autoComplete={business ? "organization" : "name"}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={business ? t("listings:new.namePlaceholderBusiness") : t("listings:new.namePlaceholderProfessional")}
                  />
                </div>
                <LocalityField
                  id="np-locality"
                  value={locality}
                  onChange={setLocality}
                  onCoords={(lat, lng) => setCoords({ lat, lng })}
                  label={t("listings:new.localityLabel")}
                  placeholder={t("listings:new.localityPlaceholder")}
                  hint={t("listings:new.localityHint")}
                />
              </>
            )}

            {step === "what" && (
              <>
                {!business && (
                  <div className="vy-acct-field">
                    <label className="vy-label" htmlFor="np-headline">
                      {t("listings:new.headlineLabel")} <span className="vy-acct-field-optional">· {t("listings:new.optional")}</span>
                    </label>
                    <input id="np-headline" className="vy-input" value={headline} maxLength={120} onChange={(e) => setHeadline(e.target.value)} placeholder={t("listings:new.headlinePlaceholder")} />
                    <span className="vy-acct-hint">{t("listings:new.headlineHint")}</span>
                  </div>
                )}

                {business && (
                  <div className="vy-acct-field">
                    <span className="vy-label">{t("listings:new.categoriesLabel")}</span>
                    <span className="vy-acct-hint">{t("listings:new.categoriesHint")}</span>
                    <div className="vy-acct-fold" role="group" aria-label={t("listings:new.categoriesLabel")}>
                      {visibleCategories.map((c) => (
                        <button key={c.slug} type="button" className="vy-chip" aria-pressed={categories.includes(c.slug)} onClick={() => toggleCategory(c.slug)}>
                          {categories.includes(c.slug) ? "✓ " : ""}
                          {c.label}
                        </button>
                      ))}
                      {!allCategories &&
                        hiddenPicked.map((c) => (
                          <button key={c.slug} type="button" className="vy-chip" aria-pressed onClick={() => toggleCategory(c.slug)}>
                            ✓ {c.label}
                          </button>
                        ))}
                      {categoryOptions.length > CATEGORIES_FOLDED && (
                        <button type="button" className="vy-acct-fold-more" aria-expanded={allCategories} onClick={() => setAllCategories((v) => !v)}>
                          {allCategories ? t("listings:new.showFewer") : t("listings:new.showAll", { count: categoryOptions.length })}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <div className="vy-acct-field">
                  <span className="vy-label">{business ? t("listings:new.capabilitiesLabelBusiness") : t("listings:new.capabilitiesLabelProfessional")}</span>
                  <span className="vy-acct-hint">{t("listings:new.capabilitiesHint")}</span>
                  <SkillPicker
                    tree={tree.data}
                    selected={capabilities}
                    onChange={setCapabilities}
                    max={15}
                    aliases={aliases}
                    collapsible
                    searchLabel={business ? t("listings:new.capabilitiesLabelBusiness") : t("listings:new.capabilitiesLabelProfessional")}
                    onFreeText={(text) => setCapabilitiesOther((prev) => (prev ? `${prev}, ${text}` : text))}
                  />
                  {capabilitiesOther && (
                    <div className="vy-acct-chips" aria-label={t("listings:new.otherAdded")}>
                      {splitList(capabilitiesOther).map((x) => (
                        <button
                          key={x}
                          type="button"
                          className="vy-chip vy-chip-selected"
                          onClick={() => setCapabilitiesOther(splitList(capabilitiesOther).filter((y) => y !== x).join(", "))}
                          aria-label={`${t("common:action.remove")} ${x}`}
                        >
                          {x} <span aria-hidden="true">×</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="vy-acct-field">
                  <span className="vy-label">{t("listings:new.serviceModeLabel")}</span>
                  <Segmented options={serviceModeOptions} value={serviceMode} onChange={setServiceMode} ariaLabel={t("listings:new.serviceModeLabel")} />
                </div>
              </>
            )}

            {step === "contact" && (
              <div className="vy-acct-field">
                <label className="vy-label" htmlFor="np-phone">
                  {t("listings:new.phoneLabel")} <span className="vy-acct-field-optional">· {t("listings:new.optional")}</span>
                </label>
                <div className="vy-acct-prefixed">
                  <span aria-hidden="true" className="vy-num">+91</span>
                  <input
                    id="np-phone"
                    className="vy-num"
                    type="tel"
                    inputMode="numeric"
                    autoComplete="tel-national"
                    maxLength={12}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, ""))}
                    placeholder={t("listings:new.phonePlaceholder")}
                  />
                </div>
                <span className="vy-acct-hint">{t("listings:new.phoneHint")}</span>
              </div>
            )}

            {error && (
              <div className="vy-error" role="alert">
                {error}
                {existingId && (
                  <>
                    {" "}
                    <button className="vy-acct-quiet" style={{ textDecoration: "underline", padding: 0, minHeight: 0 }} onClick={() => router.push(`/listings/${existingId}`)}>
                      {t("listings:new.editExisting")}
                    </button>
                  </>
                )}
              </div>
            )}

            <div className="vy-acct-actionbar">
              <div className="vy-acct-actionbar-row">
                {!last ? (
                  <button
                    className="vy-btn vy-btn-primary"
                    aria-describedby={step === "who" && blockedReason ? "np-reason" : undefined}
                    disabled={step === "who" && !requiredOk}
                    onClick={() => setStepIndex(stepIndex + 1)}
                  >
                    {t("common:action.continue")}
                  </button>
                ) : (
                  <button className="vy-btn vy-btn-primary" disabled={!requiredOk || saving} onClick={submit}>
                    {saving ? t("common:state.saving") : t("listings:new.saveProfile")}
                  </button>
                )}
                {step !== "who" && !last && (
                  <button type="button" className="vy-acct-quiet" disabled={!requiredOk || saving} onClick={submit}>
                    {t("listings:new.saveLater")}
                  </button>
                )}
              </div>
              <DisabledReason id="np-reason" show={step === "who" && !!blockedReason && !saving}>
                {blockedReason}
              </DisabledReason>
            </div>
          </div>
        </div>

        <ComposerPreview guide={[t("listings:new.guide1"), t("listings:new.guide2"), t("listings:new.guide3")]}>
          <PreviewCard
            title={name.trim()}
            subtitle={[locality.trim(), pickedLabels.join(", ")].filter(Boolean).join(" · ") || undefined}
            body={!business && headline.trim() ? headline.trim() : undefined}
            badges={<span className="vy-badge vy-badge-member-provided">{t("listings:new.previewUnverified")}</span>}
            meta={serviceModeLabel}
          />
        </ComposerPreview>
      </div>
    </Screen>
  );
}

function splitList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function digits(s: string): string {
  return s.replace(/\D/g, "");
}

export default function NewListingPage() {
  return (
    <Suspense fallback={null}>
      <NewListingInner />
    </Suspense>
  );
}
