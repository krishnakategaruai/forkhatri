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
// fast" intent. Free-text category/capability input is comma-separated and
// resolved server-side against the taxonomy (unmatched terms still save).
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
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

type Kind = "business" | "professional";

export default function NewListingPage() {
  const { t } = useTranslation(["listings", "common"]);
  const router = useRouter();
  const [kind, setKind] = useState<Kind | null>(null);
  const [name, setName] = useState("");
  const [headline, setHeadline] = useState("");
  const [categories, setCategories] = useState("");
  const [capabilities, setCapabilities] = useState("");
  const [locality, setLocality] = useState("");
  const [serviceMode, setServiceMode] = useState<"on_site" | "remote" | "both">("both");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [existingId, setExistingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
        categories: kind === "business" ? splitList(categories) : [],
        capabilities: kind === "professional" ? splitList(capabilities) : splitList(capabilities),
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
      <main className="vy-shell">
        <h1>{t("listings:new.chooseType")}</h1>
        <div className="vy-stack">
          <button className="vy-card" style={{ textAlign: "left", border: "none", cursor: "pointer" }} onClick={() => setKind("business")}>
            <h2 style={{ fontSize: 17 }}>{t("listings:new.kindBusiness")}</h2>
            <p>{t("listings:new.kindBusinessDesc")}</p>
          </button>
          <button className="vy-card" style={{ textAlign: "left", border: "none", cursor: "pointer" }} onClick={() => setKind("professional")}>
            <h2 style={{ fontSize: 17 }}>{t("listings:new.kindProfessional")}</h2>
            <p>{t("listings:new.kindProfessionalDesc")}</p>
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="vy-shell">
      <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", padding: 0 }} onClick={() => setKind(null)}>
        ← {t("listings:new.changeType")}
      </button>
      <h1>{kind === "business" ? t("listings:new.titleBusiness") : t("listings:new.titleProfessional")}</h1>

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
            <input className="vy-input" value={categories} onChange={(e) => setCategories(e.target.value)} placeholder={t("listings:new.categoriesPlaceholder")} />
          </div>
        )}

        <div className="vy-field">
          <label className="vy-label">{kind === "business" ? t("listings:new.capabilitiesLabelBusiness") : t("listings:new.capabilitiesLabelProfessional")}</label>
          <input className="vy-input" value={capabilities} onChange={(e) => setCapabilities(e.target.value)} placeholder={t("listings:new.capabilitiesPlaceholder")} />
        </div>

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

        <button className="vy-btn vy-btn-primary" disabled={!name || !locality || saving} onClick={submit}>
          {saving ? t("common:state.saving") : t("listings:new.saveDraft")}
        </button>
      </div>
    </main>
  );
}

function splitList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}
