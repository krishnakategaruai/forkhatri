"use client";

// ======================================================================
// [FE1 — 2026-09-28] SkillPicker — the two-level category → skill/role
// picker, built on GET /v1/taxonomy/tree.
//
// REQUIREMENT: posting (skills needed) and first run (what you can do)
// both pick from the real taxonomy, never a typed comma list or a
// hard-coded array (closes the IntentBar hard-coded-list finding).
// Research §5: Fiverr/WorkIndia scope the second level by the first;
// Toptal/Upwork give every group a plain one-line description; on desktop
// a list + chips split with keyboard support (Linear).
//
// LAYOUT, chosen by CSS only (no viewport reads, no hydration mismatch):
//  - phone: drill-in. A two-column grid of categories (name + one line);
//    tapping one shows only its skills/roles, with a Back button.
//  - desktop (≥900px): two columns side by side — categories on the left,
//    the active category's skills on the right, each with its one line.
// A search box on top matches both levels at once and lists matching
// skills directly, so "driver" or "टेली" is one tap from anywhere.
// Selected skills sit above as removable chips. Presentational: the tree
// comes in as a prop, changes go out through onChange.
// ======================================================================

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { TaxonomyCategory, TaxonomyTree } from "@/lib/sdk";

export interface SkillPickerProps {
  tree: TaxonomyTree | null;
  selected: string[];
  onChange: (next: string[]) => void;
  /** Upper bound on selections (Upwork caps a post at 10 skills). */
  max?: number;
  /** Accessible label for the search box. */
  searchLabel?: string;
  /** slug → English name, so "driver" or "mali" finds a role while the app is in Hindi or Telugu. */
  aliases?: ReadonlyMap<string, string>;
  /**
   * What "Use '<query>' as written" does when nothing in the tree fits.
   * Default: the text itself is added as a skill (posts accept free-text
   * skills; it is shown as typed and matched as text). Pass false to hide it.
   */
  onFreeText?: ((text: string) => void) | false;
  /**
   * Fold the tree away once something is picked (the chips plus a "Change"
   * button), so a chosen role does not keep a long list in the middle of a
   * form. The tree opens again on "Change".
   */
  collapsible?: boolean;
  /**
   * [FE1 — 2026-09-29, owner: "all tags are seen and its really looking
   * bad"] Show the category/spec grid immediately. Default false: the
   * picker starts as a single search box (the grid and its "Browse
   * categories" opener stay closed until tapped or the search box is
   * focused), so it does not dump the whole taxonomy into a form. First-run
   * — where picking a skill IS the whole screen — passes true to keep its
   * existing always-open behaviour.
   */
  startOpen?: boolean;
  /**
   * [Start flow 2026-10, decision 5] Trades added "as written" (free text)
   * shown as removable chips beside the picked ones, so "borewell motor" is
   * no longer an "Added: …" line the person cannot take back.
   */
  others?: readonly string[];
  onRemoveOther?: (text: string) => void;
}

interface Flat {
  slug: string;
  label: string;
  description: string | null;
  category: TaxonomyCategory;
}

function norm(s: string): string {
  return s.toLocaleLowerCase().normalize("NFKC");
}

export default function SkillPicker({ tree, selected, onChange, max = 10, searchLabel, aliases, onFreeText, collapsible = false, startOpen = false, others = [], onRemoveOther }: SkillPickerProps) {
  const { t } = useTranslation("hiring");
  const [expanded, setExpanded] = useState(startOpen);
  const [active, setActive] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  // "Other — add your own": a visible way to add what is not in the list, in
  // every category, not only after a search finds nothing.
  const [otherOpen, setOtherOpen] = useState(false);
  const [otherText, setOtherText] = useState("");

  const categories = useMemo(() => tree?.categories ?? [], [tree]);
  const flat = useMemo<Flat[]>(
    () =>
      categories.flatMap((c) =>
        (c.children ?? []).map((s) => ({ slug: s.slug, label: s.label, description: s.description ?? null, category: c })),
      ),
    [categories],
  );
  const labelOf = useMemo(() => new Map(flat.map((f) => [f.slug, f.label])), [flat]);

  // Desktop always shows a category on the right: the one tapped, else the
  // category of the first selected skill, else the first category.
  const firstSelectedCategory = flat.find((f) => selected.includes(f.slug))?.category.slug ?? null;
  const shownSlug = active ?? firstSelectedCategory ?? categories[0]?.slug ?? null;
  const shown = categories.find((c) => c.slug === shownSlug) ?? null;

  const q = norm(query.trim());
  // [Critique L3] match the label, the category, the one-line description,
  // the slug read as words ("security guard") and the English name.
  const matches = q
    ? flat.filter(
        (f) =>
          norm(f.label).includes(q) ||
          norm(f.category.label).includes(q) ||
          norm(f.description ?? "").includes(q) ||
          norm(f.slug.replace(/_/g, " ")).includes(q) ||
          norm(aliases?.get(f.slug) ?? "").includes(q),
      )
    : [];
  const freeText = query.trim();
  function addAsWritten() {
    if (!freeText || onFreeText === false) return;
    if (onFreeText) onFreeText(freeText);
    else if (!selected.includes(freeText) && selected.length < max) onChange([...selected, freeText]);
    setQuery("");
  }

  function addOther() {
    const text = otherText.trim();
    if (text.length < 2 || onFreeText === false) return;
    if (onFreeText) onFreeText(text);
    else if (!selected.includes(text) && selected.length < max) onChange([...selected, text]);
    setOtherText("");
    setOtherOpen(false);
  }

  function toggle(slug: string) {
    if (selected.includes(slug)) onChange(selected.filter((s) => s !== slug));
    else if (selected.length < max) {
      onChange([...selected, slug]);
      // [FE1 — 2026-09-30] A pick from search results is done with the
      // search: clear it, and in a form (collapsible) fold back to the chip.
      if (query) {
        setQuery("");
        if (collapsible) setExpanded(false);
      }
    }
  }

  const countIn = (c: TaxonomyCategory) => (c.children ?? []).filter((s) => selected.includes(s.slug)).length;
  const atMax = selected.length >= max;

  if (!tree) {
    return (
      <div className="vy-picker" aria-busy="true">
        <div className="vy-skeleton" style={{ height: 44 }} />
        <div className="vy-picker-cats">
          {Array.from({ length: 6 }, (_, i) => (
            <div key={i} className="vy-skeleton" style={{ height: 64 }} />
          ))}
        </div>
      </div>
    );
  }

  const specButton = (f: { slug: string; label: string; description: string | null }, context?: string) => {
    const on = selected.includes(f.slug);
    return (
      <button
        key={f.slug}
        type="button"
        className="vy-picker-spec"
        aria-pressed={on}
        disabled={!on && atMax}
        onClick={() => toggle(f.slug)}
      >
        <span className="vy-picker-spec-mark" aria-hidden="true">{on ? "✓" : ""}</span>
        <span className="vy-picker-spec-text">
          <strong>{f.label}</strong>
          {(context || f.description) && <span>{[context, f.description].filter(Boolean).join(" · ")}</span>}
        </span>
      </button>
    );
  };

  if (collapsible && !expanded && selected.length > 0) {
    return (
      <div className="vy-picker">
        <div className="vy-options" aria-label={t("picker.selected")}>
          {selected.map((slug) => (
            <button key={slug} type="button" className="vy-chip vy-chip-selected" onClick={() => toggle(slug)} aria-label={t("picker.remove", { skill: labelOf.get(slug) ?? slug })}>
              {labelOf.get(slug) ?? slug} <span aria-hidden="true">×</span>
            </button>
          ))}
          <button type="button" className="vy-chip" onClick={() => setExpanded(true)}>
            + {t("picker.change")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="vy-picker" data-drilled={active ? "true" : "false"}>
      {(selected.length > 0 || others.length > 0) && (
        <div className="vy-options" aria-label={t("picker.selected")}>
          {selected.map((slug) => (
            <button key={slug} type="button" className="vy-chip vy-chip-selected" onClick={() => toggle(slug)} aria-label={t("picker.remove", { skill: labelOf.get(slug) ?? slug })}>
              {labelOf.get(slug) ?? slug} <span aria-hidden="true">×</span>
            </button>
          ))}
          {others.map((text) => (
            <button key={`other:${text}`} type="button" className="vy-chip vy-chip-selected" onClick={() => onRemoveOther?.(text)} aria-label={t("picker.remove", { skill: text })}>
              {text} <span aria-hidden="true">×</span>
            </button>
          ))}
        </div>
      )}

      <input
        className="vy-input"
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setExpanded(true)}
        placeholder={selected.length === 0 && !expanded ? t("picker.chooseTrigger") : t("picker.searchPlaceholder")}
        aria-label={searchLabel ?? t("picker.searchPlaceholder")}
      />

      {q ? (
        <div className="vy-picker-specs" style={{ display: "flex" }}>
          {matches.length === 0 ? (
            <p className="vy-field-hint">{t("picker.noMatch", { query: freeText })}</p>
          ) : (
            <div className="vy-picker-spec-list">{matches.slice(0, 24).map((f) => specButton(f, f.category.label))}</div>
          )}
          {onFreeText !== false && freeText.length >= 2 && !flat.some((f) => norm(f.label) === q) && (
            <button type="button" className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", padding: "9px 16px", fontSize: 14 }} disabled={atMax} onClick={addAsWritten}>
              {t("picker.useAsWritten", { query: freeText })}
            </button>
          )}
        </div>
      ) : expanded ? (
        <div className="vy-picker-body">
          <div className="vy-picker-cats" role="list">
            {categories.map((c) => {
              const n = countIn(c);
              return (
                <button
                  key={c.slug}
                  type="button"
                  role="listitem"
                  className={`vy-picker-cat${n > 0 ? " vy-picker-cat-has" : ""}`}
                  aria-current={active === c.slug ? "true" : undefined}
                  data-shown={shown?.slug === c.slug ? "true" : undefined}
                  onClick={() => setActive(c.slug)}
                >
                  <strong>
                    {c.label} {n > 0 && <em className="vy-picker-count" style={{ fontStyle: "normal" }}>· {n}</em>}
                  </strong>
                  {c.description && <span>{c.description}</span>}
                </button>
              );
            })}
          </div>

          {shown && (
            <div className="vy-picker-specs">
              <button type="button" className="vy-btn vy-btn-ghost vy-picker-back" onClick={() => setActive(null)}>
                ← {t("picker.allCategories")}
              </button>
              <div className="vy-stack" style={{ gap: 2 }}>
                <strong style={{ color: "var(--text-primary)" }}>{shown.label}</strong>
                {shown.description && <span className="vy-field-hint">{shown.description}</span>}
              </div>
              <div className="vy-picker-spec-list">{(shown.children ?? []).map((s) => specButton({ slug: s.slug, label: s.label, description: s.description ?? null }))}</div>
              {onFreeText !== false && (
                otherOpen ? (
                  <div className="vy-stack" style={{ gap: 8 }}>
                    <input
                      className="vy-input"
                      value={otherText}
                      autoFocus
                      maxLength={60}
                      onChange={(e) => setOtherText(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addOther(); } }}
                      placeholder={t("picker.otherPlaceholder", { category: shown.label })}
                      aria-label={t("picker.other")}
                    />
                    <div className="vy-row" style={{ gap: 10, flexWrap: "wrap" }}>
                      <button type="button" className="vy-btn vy-btn-secondary" style={{ padding: "9px 16px", fontSize: 14 }} disabled={atMax || otherText.trim().length < 2} onClick={addOther}>
                        {t("picker.otherAdd")}
                      </button>
                      <button type="button" className="vy-btn vy-btn-ghost" style={{ padding: "9px 16px", fontSize: 14 }} onClick={() => { setOtherOpen(false); setOtherText(""); }}>
                        {t("picker.otherCancel")}
                      </button>
                    </div>
                  </div>
                ) : (
                  <button type="button" className="vy-picker-spec" disabled={atMax} onClick={() => setOtherOpen(true)}>
                    <span className="vy-picker-spec-mark" aria-hidden="true">+</span>
                    <span className="vy-picker-spec-text">
                      <strong>{t("picker.other")}</strong>
                      <span>{t("picker.otherHint")}</span>
                    </span>
                  </button>
                )
              )}
            </div>
          )}
        </div>
      ) : (
        // [FE1 — 2026-09-29] Closed state: no grid dump. A single tap (or
        // focusing the search box above) opens the category/spec grid.
        <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => setExpanded(true)}>
          {t("picker.browseCategories")}
        </button>
      )}

      {atMax && <p className="vy-field-hint">{t("picker.max", { count: max })}</p>}
    </div>
  );
}
