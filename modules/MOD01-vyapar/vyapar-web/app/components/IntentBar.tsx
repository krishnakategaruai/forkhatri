"use client";

// [Design direction] Conversational, intent-first search entry — a single
// free-text field that visibly parses into structured filter chips as the
// member types, instead of a traditional multi-dropdown filter form. V1
// "understanding" is simple client-side keyword matching against a small
// known category/locality list (per the design direction's own explicit
// allowance — "does not need real NLP/AI, but the UI must show
// understanding happening"), not a backend AI call.
// [Product-owner i18n rule] Converted to useTranslation() — placeholder,
// chip prefixes and the Search button all read from discover.json's
// businesses.* keys (shared with the /businesses page since both render
// the same intent-bar concept).
// Traces to: FR15 (search entry point), Design direction
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

const KNOWN_CATEGORIES = [
  "accounting", "legal", "plumbing", "electrical", "catering", "events",
  "textiles", "software", "tutoring", "bakery", "architecture", "photography",
  "car repair", "home repair",
];
const KNOWN_LOCALITIES = [
  "ameerpet", "begumpet", "banjara hills", "secunderabad", "charminar",
  "madhapur", "kukatpally", "himayatnagar", "dilsukhnagar", "jubilee hills",
  "abids", "kondapur", "gachibowli", "uppal",
];

export interface ParsedIntent {
  text: string;
  category?: string;
  locality?: string;
}

interface IntentBarProps {
  onSearch: (intent: ParsedIntent) => void;
  placeholder?: string;
}

export default function IntentBar({ onSearch, placeholder }: IntentBarProps) {
  const { t } = useTranslation("discover");
  const [value, setValue] = useState("");

  const parsed = useMemo<ParsedIntent>(() => {
    const lower = value.toLowerCase();
    const category = KNOWN_CATEGORIES.find((c) => lower.includes(c));
    const locality = KNOWN_LOCALITIES.find((l) => lower.includes(l));
    return { text: value, category, locality };
  }, [value]);

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
          {parsed.category && <span className="vy-chip">{t("businesses.chipCategory", { category: parsed.category })}</span>}
          {parsed.locality && <span className="vy-chip">{t("businesses.chipNear", { locality: parsed.locality })}</span>}
        </div>
      )}
      <button className="vy-btn vy-btn-primary" onClick={() => onSearch(parsed)}>
        {t("businesses.search")}
      </button>
    </div>
  );
}
