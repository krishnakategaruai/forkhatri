"use client";

// [Design direction] Conversational, intent-first search entry — a single
// free-text field that visibly parses into structured filter chips as the
// member types, instead of a traditional multi-dropdown filter form. V1
// "understanding" is simple client-side keyword matching (per the design
// direction's own explicit allowance — "does not need real NLP/AI, but the
// UI must show understanding happening"), not a backend AI call.
// [Real gap found via third critique pass, fixed here] this used to match
// against a hardcoded 14-item English category/locality array — the exact
// class of gap first-run's own capability picker already solved by
// fetching real data instead of a static guess list. Now fetches
// `GET /v1/listings/search-suggestions` once (real taxonomy categories +
// real seeded localities), matching the pattern first-run already uses for
// its own capability picker — one lookup, cached for the component's
// lifetime, never re-fetched per keystroke.
// [Product-owner i18n rule] Category/locality chip labels come straight
// from the fetched, already-labelled data — the category CHIP shows the
// real display label, while the value sent to search is the real slug
// (previously a lossy space<->underscore guess).
// Traces to: FR15 (search entry point), Design direction
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSdk } from "@/lib/sdk/react";

interface Suggestion {
  slug: string;
  label: string;
}

export interface ParsedIntent {
  text: string;
  category?: string; // real taxonomy slug, not a label guess
  categoryLabel?: string;
  locality?: string;
}

interface IntentBarProps {
  onSearch: (intent: ParsedIntent) => void;
  placeholder?: string;
}

export default function IntentBar({ onSearch, placeholder }: IntentBarProps) {
  const { t, i18n } = useTranslation("discover");
  const sdk = useSdk();
  const [value, setValue] = useState("");
  const [categories, setCategories] = useState<Suggestion[]>([]);
  const [localities, setLocalities] = useState<string[]>([]);

  // [Real bug found live by the product owner, audited across every
  // taxonomy-fetching screen and fixed here too] same anti-pattern — the
  // category labels this fetch returns depend on the request's language
  // header, but the effect had no `i18n.language` dependency, so a live
  // language switch left these chips in whatever language was active when
  // the component first mounted.
  useEffect(() => {
    sdk.listings
      .searchSuggestions<{ categories: Suggestion[]; localities: string[] }>()
      .then((d) => {
        setCategories(d.categories);
        setLocalities(d.localities);
      })
      .catch(() => {
        /* suggestions are an enhancement, not required for the field to work */
      });
  }, [i18n.language, sdk]);

  const parsed = useMemo<ParsedIntent>(() => {
    const lower = value.toLowerCase();
    const category = categories.find((c) => lower.includes(c.label.toLowerCase()) || lower.includes(c.slug.replace(/_/g, " ")));
    const locality = localities.find((l) => lower.includes(l.toLowerCase()));
    return { text: value, category: category?.slug, categoryLabel: category?.label, locality };
  }, [value, categories, localities]);

  return (
    <div className="vy-stack" style={{ gap: 8 }}>
      <input
        className="vy-input"
        style={{ fontSize: 16, padding: "14px 16px" }}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSearch(parsed)}
        placeholder={placeholder ?? t("businesses.searchPlaceholder")}
        // [FR43/TR043 — WCAG 1.3.1/4.1.2, found in the manual review pass] a
        // placeholder alone is never a valid accessible name — this is the
        // app's own primary search field, so it gets an explicit one.
        aria-label={placeholder ?? t("businesses.searchPlaceholder")}
      />
      {(parsed.category || parsed.locality) && (
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {parsed.category && <span className="vy-chip">{t("businesses.chipCategory", { category: parsed.categoryLabel ?? parsed.category })}</span>}
          {parsed.locality && <span className="vy-chip">{t("businesses.chipNear", { locality: parsed.locality })}</span>}
        </div>
      )}
      <button className="vy-btn vy-btn-primary vy-search-action" onClick={() => onSearch(parsed)}>
        {t("businesses.search")}
      </button>
    </div>
  );
}
