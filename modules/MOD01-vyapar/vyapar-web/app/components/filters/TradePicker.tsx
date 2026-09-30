"use client";

// [Design system 2026-09-30] The Trade filter's panel: a search box over the
// taxonomy (GET /v1/taxonomy/tree, localized by the server), then specialties
// grouped under a quiet category label; each specialty is a 48px row with a
// check box. Replaces the long,
// always-open list of skill tags the owner found "hard job for user to
// scroll": nothing is listed until the panel is open, and typing narrows it.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, Search } from "lucide-react";
import type { TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useResource } from "@/app/hooks/useResource";

export function useTaxonomy() {
  const sdk = useSdk();
  const tree = useResource<TaxonomyTree | null>(() => sdk.taxonomy.tree(), [sdk], { fallback: null });
  const categories = useMemo(() => tree.data?.categories ?? [], [tree.data]);
  const labelOf = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of categories) {
      m.set(c.slug, c.label);
      for (const s of c.children ?? []) m.set(s.slug, s.label);
    }
    return (slug: string) => m.get(slug) ?? slug.replace(/_/g, " ");
  }, [categories]);
  return { categories, labelOf };
}

/** "Plumbers", or "Plumbers +2" when several are chosen; a whole category reads as its name. */
export function tradeValue(
  skills: readonly string[],
  categories: ReturnType<typeof useTaxonomy>["categories"],
  labelOf: (s: string) => string,
  more: (first: string, count: number) => string,
): string | null {
  if (!skills.length) return null;
  const whole = categories.find((c) => {
    const kids = (c.children ?? []).map((k) => k.slug);
    return kids.length > 0 && kids.length === skills.length && kids.every((k) => skills.includes(k));
  });
  if (whole) return whole.label;
  return skills.length === 1 ? labelOf(skills[0]) : more(labelOf(skills[0]), skills.length - 1);
}

export default function TradePicker({ value, onChange }: { value: string[]; onChange: (next: string[]) => void }) {
  const { t } = useTranslation("explore");
  const { categories } = useTaxonomy();
  const [q, setQ] = useState("");
  const needle = q.trim().toLocaleLowerCase();

  const groups = useMemo(
    () =>
      categories
        .map((c) => {
          const catHit = !needle || c.label.toLocaleLowerCase().includes(needle);
          const kids = (c.children ?? []).filter((k) => catHit || k.label.toLocaleLowerCase().includes(needle));
          return { c, kids };
        })
        .filter((g) => g.kids.length > 0),
    [categories, needle],
  );

  const toggle = (slug: string) => onChange(value.includes(slug) ? value.filter((s) => s !== slug) : [...value, slug]);

  return (
    <div className="vy-trpick">
      <label className="vy-trpick-search">
        <Search size={18} strokeWidth={2} aria-hidden="true" />
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("fbar.tradeSearch")}
          aria-label={t("fbar.tradeSearch")}
          autoComplete="off"
        />
      </label>
      <div className="vy-trpick-list">
        {groups.length === 0 && <p className="vy-muted vy-trpick-none">{t("fbar.tradeNone", { q })}</p>}
        {groups.map(({ c, kids }) => {
          return (
            <div key={c.slug} className="vy-trpick-group" role="group" aria-label={c.label}>
              <span className="vy-trpick-cat">{c.label}</span>
              {kids.map((k) => {
                const on = value.includes(k.slug);
                return (
                  <button key={k.slug} type="button" role="checkbox" aria-checked={on} className="vy-menu-item vy-trpick-item" onClick={() => toggle(k.slug)}>
                    <span>{k.label}</span>
                    <span className="vy-trpick-box" aria-hidden="true">
                      {on && <Check size={14} strokeWidth={3} />}
                    </span>
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
