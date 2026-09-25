"use client";

// [TR001/TR004] Create a BusinessProfile (FR01 — three-question minimum:
// what, where, how to contact) or a ProfessionalListingProfile (FR04 —
// three required steps: capability, where/how, contact preference). Both
// share one form here because both share one endpoint (POST /v1/listings)
// and one underlying table — presenting them as two forms would duplicate
// logic the backend already treats as one Listing concept.
// Approach: kind picker first (large tap targets, per design direction),
// then exactly the fields each kind's FR names as mandatory — nothing else
// is required to reach Discover, matching FR01/FR04's own "reach value
// fast" intent.
// [Real gap found via third critique pass, fixed here] category/capability
// used to be a raw comma-separated text field the member had to type
// correctly with no guidance on what the taxonomy actually recognises —
// the exact problem first-run's own capability picker already solved with
// real tap-only taxonomy chips. Now uses that same pattern: chips fetched
// from the same shared taxonomy endpoints first-run/IntentBar already use,
// plus a free-text "other" field for anything not listed — server-side
// resolution against the taxonomy is unchanged (unmatched terms still save).
// Traces to: FR01, FR04, TR001, TR004
//
// [Product-owner reference check, 2026-09-15] "Vyapar is inspired from
// Upwork + WorkIndia" — checked live via web search, not memory. Upwork's
// own freelancer-profile guidance: "the title of your profile is your
// first impression... spotlights your top skills" (support.upwork.com/hc/
// en-us/articles/360016252373) — a short professional headline distinct
// from the person's name. Vyapar already modeled this (`listings.headline`)
// but the composer wasn't exposing it for the professional path — added
// below. The business path stays WorkIndia-fast (name/category/locality/
// contact only — "simple design... most actions in a few taps", per
// WorkIndia's own reviewed UX), deliberately NOT given the same headline
// field, since a shop doesn't need a personal "first impression" line the
// way an individual professional does.
// [Product-owner i18n rule] Converted to useTranslation() — every string
// is a key in locales/<lang>/listings.json; backend error `detail` strings
// are already localized server-side (X-Vyapar-Language header) so they're
// rendered as-is, only this file's OWN fallback strings needed keys.
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import Icon from "@/app/components/Icon";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";

type Kind = "business" | "professional";

interface TaxonomyOption {
  slug: string;
  label: string;
}

function NewListingInner() {
  const { t, i18n } = useTranslation(["listings", "common", "discover"]);
  const router = useRouter();
  // The profile hub links straight to one kind (`?kind=business|professional`)
  // so the person lands on the form, not the chooser.
  const params = useSearchParams();
  const presetKind = params.get("kind");
  const [kind, setKind] = useState<Kind | null>(presetKind === "business" || presetKind === "professional" ? presetKind : null);
  const [name, setName] = useState("");
  const [headline, setHeadline] = useState("");
  const [categoryOptions, setCategoryOptions] = useState<TaxonomyOption[]>([]);
  const [capabilityOptions, setCapabilityOptions] = useState<TaxonomyOption[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [categoriesOther, setCategoriesOther] = useState("");
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [capabilitiesOther, setCapabilitiesOther] = useState("");
  const [locality, setLocality] = useState("");
  const [serviceMode, setServiceMode] = useState<"on_site" | "remote" | "both">("both");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [existingId, setExistingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // [Real bug found live by the product owner on a sibling screen
  // (FilterSheet), audited and fixed here too] same anti-pattern — a
  // taxonomy fetch whose language comes from a request header, in an
  // effect with no `i18n.language` dependency, so it never re-fetched on
  // a live language switch.
  useEffect(() => {
    api.get<{ categories: TaxonomyOption[] }>("/v1/listings/search-suggestions").then((d) => setCategoryOptions(d.categories));
    api.get<TaxonomyOption[]>("/v1/first-run/capability-options").then(setCapabilityOptions);
  }, [i18n.language]);

  function toggleCategory(slug: string) {
    setCategories((c) => (c.includes(slug) ? c.filter((x) => x !== slug) : [...c, slug]));
  }

  function toggleCapability(slug: string) {
    setCapabilities((c) => (c.includes(slug) ? c.filter((x) => x !== slug) : [...c, slug]));
  }

  async function submit() {
    if (!kind) return;
    setSaving(true);
    setError(null);
    setExistingId(null);
    try {
      const listing = await api.post<{ id: string }>("/v1/listings", {
        kind,
        name,
        headline: kind === "professional" ? headline || undefined : undefined,
        categories: kind === "business" ? [...categories, ...splitList(categoriesOther)] : [],
        capabilities: [...capabilities, ...splitList(capabilitiesOther)],
        locality,
        service_mode: serviceMode,
        primary_phone: phone || undefined,
        contacts: phone ? [{ channel: "phone", value: phone, disclosure: "after_accept" }] : [],
      });
      router.push(`/listings/${listing.id}`);
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409 && typeof e.detail === "object" && e.detail && "existing_listing_id" in e.detail) {
          const detail = e.detail as unknown as { message: string; existing_listing_id: string };
          setError(detail.message);
          setExistingId(detail.existing_listing_id);
        } else {
          setError(typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"));
        }
      } else {
        setError(t("common:state.somethingWentWrong"));
      }
    } finally {
      setSaving(false);
    }
  }

  if (!kind) {
    return (
      <Screen>
        <h1>{t("listings:new.chooseType")}</h1>
        <div className="vy-stack vy-choice-grid">
          <button className="vy-card vy-choice" onClick={() => setKind("business")}>
            <span className="vy-choice-mark" aria-hidden="true"><Icon name="business" size={22} /></span>
            <h2 style={{ fontSize: 17 }}>{t("listings:new.kindBusiness")}</h2>
            <p>{t("listings:new.kindBusinessDesc")}</p>
            <span className="vy-choice-arrow" aria-hidden="true">→</span>
          </button>
          <button className="vy-card vy-choice" onClick={() => setKind("professional")}>
            <span className="vy-choice-mark" aria-hidden="true"><Icon name="professional" size={22} /></span>
            <h2 style={{ fontSize: 17 }}>{t("listings:new.kindProfessional")}</h2>
            <p>{t("listings:new.kindProfessionalDesc")}</p>
            <span className="vy-choice-arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </Screen>
    );
  }

  // [IMP39] Live preview (desktop): the directory card other members will
  // see, built from the values typed so far — same title/subtitle shape as
  // the Businesses & Professionals results.
  const pickedLabels = [
    ...(kind === "business" ? categoryOptions.filter((c) => categories.includes(c.slug)).map((c) => c.label) : []),
    ...(kind === "business" ? splitList(categoriesOther) : []),
    ...capabilityOptions.filter((c) => capabilities.includes(c.slug)).map((c) => c.label),
    ...splitList(capabilitiesOther),
  ];
  const serviceModeLabel =
    serviceMode === "on_site" ? t("discover:businesses.serviceModeOnSite") : serviceMode === "remote" ? t("discover:businesses.serviceModeRemote") : t("discover:businesses.serviceModeBoth");

  return (
    <Screen width="wide">
      <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", padding: 0 }} onClick={() => setKind(null)}>
        ← {t("listings:new.changeType")}
      </button>
      <h1>{kind === "business" ? t("listings:new.titleBusiness") : t("listings:new.titleProfessional")}</h1>

      <div className="vy-compose">
      <div className="vy-compose-main">
      <div className="vy-stack">
        <div className="vy-field">
          <label className="vy-label">{kind === "business" ? t("listings:new.nameLabelBusiness") : t("listings:new.nameLabelProfessional")}</label>
          <input className="vy-input" value={name} onChange={(e) => setName(e.target.value)} placeholder={kind === "business" ? t("listings:new.namePlaceholderBusiness") : t("listings:new.namePlaceholderProfessional")} />
        </div>

        {kind === "professional" && (
          <div className="vy-field">
            <label className="vy-label">{t("listings:new.headlineLabel")}</label>
            <input className="vy-input" value={headline} onChange={(e) => setHeadline(e.target.value)} placeholder={t("listings:new.headlinePlaceholder")} />
          </div>
        )}

        {kind === "business" && (
          <div className="vy-field">
            <label className="vy-label">{t("listings:new.categoriesLabel")}</label>
            <div className="vy-row" style={{ flexWrap: "wrap" }}>
              {categoryOptions.map((c) => (
                <button
                  key={c.slug}
                  type="button"
                  className="vy-chip"
                  aria-pressed={categories.includes(c.slug)}
                style={{ cursor: "pointer" }}
                  onClick={() => toggleCategory(c.slug)}
                >
                  {categories.includes(c.slug) ? "✓ " : ""}{c.label}
                </button>
              ))}
            </div>
            <input className="vy-input" style={{ marginTop: 6 }} value={categoriesOther} onChange={(e) => setCategoriesOther(e.target.value)} placeholder={t("listings:new.categoriesPlaceholder")} />
          </div>
        )}

        <div className="vy-field">
          <label className="vy-label">{kind === "business" ? t("listings:new.capabilitiesLabelBusiness") : t("listings:new.capabilitiesLabelProfessional")}</label>
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {capabilityOptions.map((c) => (
              <button
                key={c.slug}
                type="button"
                className="vy-chip"
                aria-pressed={capabilities.includes(c.slug)}
                style={{ cursor: "pointer" }}
                onClick={() => toggleCapability(c.slug)}
              >
                {capabilities.includes(c.slug) ? "✓ " : ""}{c.label}
              </button>
            ))}
          </div>
          <input className="vy-input" style={{ marginTop: 6 }} value={capabilitiesOther} onChange={(e) => setCapabilitiesOther(e.target.value)} placeholder={t("listings:new.capabilitiesPlaceholder")} />
        </div>

        <div className="vy-field-pair">
        <div className="vy-field">
          <label className="vy-label">{t("listings:new.localityLabel")}</label>
          <input className="vy-input" value={locality} onChange={(e) => setLocality(e.target.value)} placeholder={t("listings:new.localityPlaceholder")} />
        </div>

        <div className="vy-field">
          <label className="vy-label">{t("listings:new.serviceModeLabel")}</label>
          <select className="vy-select" value={serviceMode} onChange={(e) => setServiceMode(e.target.value as typeof serviceMode)}>
            <option value="on_site">{t("listings:new.serviceModeOnSite")}</option>
            <option value="remote">{t("listings:new.serviceModeRemote")}</option>
            <option value="both">{t("listings:new.serviceModeBoth")}</option>
          </select>
        </div>
        </div>

        <div className="vy-field">
          <label className="vy-label">{t("listings:new.phoneLabel")}</label>
          <input className="vy-input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t("listings:new.phonePlaceholder")} />
        </div>

        {error && (
          <div className="vy-error">
            {error}
            {existingId && (
              <>
                {" "}
                <button className="vy-btn vy-btn-ghost" style={{ padding: 0, textDecoration: "underline" }} onClick={() => router.push(`/listings/${existingId}`)}>
                  {t("listings:new.editExisting")}
                </button>
              </>
            )}
          </div>
        )}

        <button className="vy-btn vy-btn-primary vy-submit" disabled={!name || !locality || saving} onClick={submit}>
          {saving ? t("common:state.saving") : t("listings:new.saveDraft")}
        </button>
      </div>
      </div>
      <ComposerPreview guide={[t("listings:new.guide1"), t("listings:new.guide2"), t("listings:new.guide3")]}>
        <PreviewCard
          title={name.trim()}
          subtitle={[locality.trim(), pickedLabels.join(", ")].filter(Boolean).join(" · ") || undefined}
          body={kind === "professional" && headline.trim() ? headline.trim() : undefined}
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

export default function NewListingPage() {
  return (
    <Suspense fallback={null}>
      <NewListingInner />
    </Suspense>
  );
}
