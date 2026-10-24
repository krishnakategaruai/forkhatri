"use client";

// [Start flow 2026-10 — ONBOARDING-REDESIGN-2026-10.md, decision 5 and the
// owner's "Trade tiles" note] Picture tiles for the trades people actually
// do, in Vyapar's own line-icon style (the same icons Discover's TradeRail
// uses, tinted by family of work), a label in the member's language under
// each, and "Other — add your own" as the last tile. Several picks allowed.
// The full category grid stays behind "More trades" (collapse-option-fields
// rule), and a search box with the mic finds anything by typing or saying it.
// Free-text trades are kept as written and shown as removable chips.
// Presentational apart from the tile list it fetches for the goal.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp, Plus, X } from "lucide-react";
import type { StartGoal, TradeTile } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import { specialtyVisual } from "@/app/components/discover/trades";
import { useTaxonomyAliases, useTaxonomyTree } from "@/app/hooks/hiring";

export interface TradeTilesProps {
  goal: Exclude<StartGoal, "hire">;
  selected: string[];
  onChange: (next: string[]) => void;
  others: string[];
  onOthers: (next: string[]) => void;
  max?: number;
}

const SHOWN = 8;

export default function TradeTiles({ goal, selected, onChange, others, onOthers, max = 15 }: TradeTilesProps) {
  const { t, i18n } = useTranslation(["firstRun", "hiring", "common"]);
  const sdk = useSdk();
  const tree = useTaxonomyTree();
  const aliases = useTaxonomyAliases();
  const [tiles, setTiles] = useState<TradeTile[] | null>(null);
  const [more, setMore] = useState(false);
  const [otherOpen, setOtherOpen] = useState(false);
  const [otherText, setOtherText] = useState("");

  useEffect(() => {
    let live = true;
    sdk.firstRun
      .tradeTiles(goal)
      .then((rows) => live && setTiles(rows))
      .catch(() => live && setTiles([]));
    return () => {
      live = false;
    };
  }, [sdk, goal, i18n.language]);

  const labelOf = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of tree.data?.categories ?? []) for (const s of c.children ?? []) m.set(s.slug, s.label);
    for (const tile of tiles ?? []) m.set(tile.slug, tile.label);
    return m;
  }, [tree.data, tiles]);

  const total = selected.length + others.length;
  const atMax = total >= max;

  function toggle(slug: string) {
    if (selected.includes(slug)) onChange(selected.filter((s) => s !== slug));
    else if (!atMax) onChange([...selected, slug]);
  }

  function addOther(text: string) {
    const clean = text.trim().replace(/\s+/g, " ").slice(0, 60);
    if (clean.length < 2 || atMax) return;
    if (!others.some((o) => o.toLocaleLowerCase() === clean.toLocaleLowerCase())) onOthers([...others, clean]);
    setOtherText("");
    setOtherOpen(false);
  }

  const shown = (tiles ?? []).slice(0, SHOWN);
  // A tile picked from "More trades" that is not among the first eight still
  // shows as a tile, so the person sees what they chose.
  const extra = (tiles ?? []).slice(SHOWN).filter((x) => selected.includes(x.slug));

  return (
    <div className="vy-start-trades">
      {total > 0 && (
        <div className="vy-options vy-start-chips" aria-label={t("hiring:picker.selected")}>
          {selected.map((slug) => (
            <button key={slug} type="button" className="vy-chip vy-chip-selected" onClick={() => toggle(slug)} aria-label={t("hiring:picker.remove", { skill: labelOf.get(slug) ?? slug })}>
              {labelOf.get(slug) ?? slug} <X size={14} aria-hidden="true" />
            </button>
          ))}
          {others.map((text) => (
            <button key={text} type="button" className="vy-chip vy-chip-selected" onClick={() => onOthers(others.filter((o) => o !== text))} aria-label={t("hiring:picker.remove", { skill: text })}>
              {text} <X size={14} aria-hidden="true" />
            </button>
          ))}
        </div>
      )}

      {tiles === null ? (
        <div className="vy-tiles" aria-busy="true">
          {Array.from({ length: SHOWN + 1 }, (_, i) => (
            <div key={i} className="vy-skeleton vy-tile-skeleton" />
          ))}
        </div>
      ) : (
        <div className="vy-tiles" role="group" aria-label={t("firstRun:start.trades.groupLabel")}>
          {[...shown, ...extra].map((tile) => {
            const v = specialtyVisual(tile.slug);
            const Icon = v.icon;
            const on = selected.includes(tile.slug);
            return (
              <button key={tile.slug} type="button" className="vy-tile" aria-pressed={on} disabled={!on && atMax} onClick={() => toggle(tile.slug)}>
                <span className={`vy-trade-tile vy-trade-${v.family}`} aria-hidden="true">
                  <Icon size={22} strokeWidth={1.8} />
                </span>
                <span className="vy-tile-label">{tile.label}</span>
              </button>
            );
          })}
          <button type="button" className="vy-tile vy-tile-other" aria-expanded={otherOpen} disabled={atMax} onClick={() => setOtherOpen((v) => !v)}>
            <span className="vy-trade-tile vy-trade-neutral" aria-hidden="true">
              <Plus size={22} strokeWidth={1.8} />
            </span>
            <span className="vy-tile-label">{t("hiring:picker.other")}</span>
          </button>
        </div>
      )}

      {otherOpen && (
        <div className="vy-stack" style={{ gap: 8 }}>
          <VoiceInput fieldLabel={t("firstRun:start.trades.otherLabel")} compact onConfirm={(spoken) => setOtherText((v) => appendSpoken(v, spoken))}>
            <input
              className="vy-input"
              value={otherText}
              autoFocus
              maxLength={60}
              enterKeyHint="done"
              onChange={(e) => setOtherText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addOther(otherText);
                }
              }}
              placeholder={t("firstRun:start.trades.otherPlaceholder")}
              aria-label={t("firstRun:start.trades.otherLabel")}
            />
          </VoiceInput>
          <div className="vy-row" style={{ gap: 10, flexWrap: "wrap" }}>
            <button type="button" className="vy-btn vy-btn-secondary" style={{ padding: "9px 16px", fontSize: 14 }} disabled={otherText.trim().length < 2} onClick={() => addOther(otherText)}>
              {t("hiring:picker.otherAdd")}
            </button>
            <button type="button" className="vy-btn vy-btn-ghost" style={{ padding: "9px 16px", fontSize: 14 }} onClick={() => { setOtherOpen(false); setOtherText(""); }}>
              {t("hiring:picker.otherCancel")}
            </button>
          </div>
        </div>
      )}

      <button type="button" className="vy-acct-quiet vy-start-more" aria-expanded={more} onClick={() => setMore((v) => !v)}>
        {more ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
        {more ? t("firstRun:start.trades.fewerTrades") : t("firstRun:start.trades.moreTrades")}
      </button>

      {more && (
        <SkillPicker
          tree={tree.data}
          selected={selected}
          onChange={onChange}
          max={max}
          aliases={aliases}
          onFreeText={(text) => addOther(text)}
          others={others}
          onRemoveOther={(text) => onOthers(others.filter((o) => o !== text))}
          startOpen
        />
      )}
      {atMax && <p className="vy-acct-hint">{t("hiring:picker.max", { count: max })}</p>}
    </div>
  );
}
