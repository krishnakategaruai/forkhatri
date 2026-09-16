"use client";

// [TR015/TR017] Businesses & Professionals — standalone search/browse
// surface (FR15 DEC-001: distinct from the Opportunity feed, works with
// zero Opportunities in the system). Uses <IntentBar> instead of a
// conventional multi-dropdown filter form per the design direction — fewer
// taps for the common case ("plumber near Ameerpet" is one field, not four
// separate pickers). Zero-result responses render FR17's explicit,
// labelled broadening chips — never a silent filter relaxation.
// [Product-owner i18n rule] `notice`/`broadening_options[].label`/
// `relevance_reason` from the API are now i18n KEYS (discovery.py's own
// i18n conversion) — this page translates them via discover.json/
// ranking.json, never renders them as raw English/key text.
// Traces to: FR15, FR16, FR17, TR015, TR016, TR017
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import IntentBar, { ParsedIntent } from "@/app/components/IntentBar";
import LivingCard from "@/app/components/LivingCard";
import { useReputationText, type Reputation } from "@/app/components/Reputation";

interface SearchListing {
  id: string;
  name: string;
  locality: string;
  categories: string[];
  capabilities: string[];
  verification_state: string;
  contact_verified: boolean;
  reputation?: Reputation | null; // [FR28] reputation line on every result card
}

interface SearchResult {
  listing: SearchListing;
  relevance_reason: string;
}

interface BroadeningOption {
  id: string;
  label: string;
}

interface SearchResponse {
  results: SearchResult[];
  total_considered: number;
  degraded?: boolean;
  notice?: string | null;
  broadening_options: BroadeningOption[];
  fallback?: { post_link: string; notify_link: string } | null;
  sponsored?: SearchResult[]; // [FR30] labelled extra slot; organic results unchanged
}

const RANKING_SIGNAL_KEYS = [
  "capability_fit", "intent_fit", "location_fit", "timing_fit", "value_fit", "experience_fit", "freshness_fit", "trust_fit",
];

export default function BusinessesPage() {
  const { t } = useTranslation(["discover", "common", "ranking"]);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [lastQuery, setLastQuery] = useState<ParsedIntent | null>(null);
  const [broadenAttempt, setBroadenAttempt] = useState(0);
  const [loading, setLoading] = useState(false);
  const reputationText = useReputationText();

  async function runSearch(intent: ParsedIntent, attempt = 0, extraParams: Record<string, string> = {}) {
    setLoading(true);
    setLastQuery(intent);
    setBroadenAttempt(attempt);
    try {
      const params = new URLSearchParams();
      if (intent.text) params.set("q", intent.text);
      if (intent.category) params.set("category", intent.category.replace(" ", "_"));
      if (intent.locality) params.set("locality", intent.locality);
      params.set("broaden_attempt", String(attempt));
      Object.entries(extraParams).forEach(([k, v]) => params.set(k, v));
      const res = await api.get<SearchResponse>(`/v1/listings/search?${params.toString()}`);
      setResponse(res);
    } finally {
      setLoading(false);
    }
  }

  function applyBroadening(optionId: string) {
    if (!lastQuery) return;
    const extra: Record<string, string> = {};
    if (optionId.startsWith("radius_")) extra.radius_km = optionId.replace("radius_", "");
    if (optionId === "include_unverified") extra.verified_only = "false";
    if (optionId === "remove_filter") {
      runSearch({ text: lastQuery.text }, broadenAttempt + 1);
      return;
    }
    runSearch(lastQuery, broadenAttempt + 1, extra);
  }

  function broadeningLabel(o: BroadeningOption): string {
    if (o.label === "radius") return t("discover:broaden.radius", { km: o.id.replace("radius_", "") });
    return t(`discover:broaden.${o.label}` as "broaden.remove_filter");
  }

  function relevanceLabel(key: string): string {
    if (RANKING_SIGNAL_KEYS.includes(key)) return t(`ranking:signal.${key}` as "signal.capability_fit");
    return t(`ranking:fallback.${key}` as "fallback.matchesFilters");
  }

  return (
    <main className="vy-shell">
      <div className="vy-row" style={{ justifyContent: "space-between" }}>
        <h1>{t("discover:businesses.title")}</h1>
        <a className="vy-btn vy-btn-ghost" href="/listings/mine" style={{ fontSize: 13 }}>
          {t("common:action.myListings")}
        </a>
      </div>
      <IntentBar onSearch={(intent) => runSearch(intent)} />

      {loading && <p className="vy-muted">{t("common:state.searching")}</p>}

      {response?.sponsored && response.sponsored.length > 0 && (
        <div className="vy-stack">
          {response.sponsored.map((r) => (
            <LivingCard
              key={`sponsored-${r.listing.id}`}
              href={`/listings/${r.listing.id}`}
              title={r.listing.name}
              subtitle={`${r.listing.locality} · ${[...r.listing.categories, ...r.listing.capabilities].join(", ") || "—"}`}
              verified={r.listing.verification_state === "verified"}
              verificationLabel={t("discover:businesses.verifiedLabel")}
              sponsored
              meta={reputationText(r.listing.reputation)}
            />
          ))}
        </div>
      )}

      {response && response.results.length > 0 && (
        <div className="vy-stack">
          {response.degraded && response.notice && <p className="vy-muted">{t(`discover:notice.${response.notice}` as "notice.degraded")}</p>}
          {response.results.map((r) => (
            <LivingCard
              key={r.listing.id}
              href={`/listings/${r.listing.id}`}
              title={r.listing.name}
              subtitle={`${r.listing.locality} · ${[...r.listing.categories, ...r.listing.capabilities].join(", ") || "—"}`}
              verified={r.listing.verification_state === "verified"}
              verificationLabel={t("discover:businesses.verifiedLabel")}
              meta={[reputationText(r.listing.reputation), relevanceLabel(r.relevance_reason)].filter(Boolean).join(" · ")}
            />
          ))}
        </div>
      )}

      {response && response.results.length === 0 && (
        <div className="vy-card vy-stack">
          <p>{t(`discover:notice.${response.notice ?? "noMatch"}` as "notice.noMatch")}</p>
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {response.broadening_options.map((o) => (
              <button key={o.id} className="vy-chip" style={{ border: "none", cursor: "pointer" }} onClick={() => applyBroadening(o.id)}>
                {broadeningLabel(o)}
              </button>
            ))}
          </div>
          {response.fallback && (
            <div className="vy-row" style={{ flexWrap: "wrap" }}>
              <a className="vy-btn vy-btn-secondary" href={response.fallback.post_link}>
                {t("discover:businesses.postWhatYouNeed")}
              </a>
            </div>
          )}
        </div>
      )}

      {!response && !loading && (
        <p className="vy-muted">{t("discover:businesses.hint")}</p>
      )}
    </main>
  );
}
