"use client";

// ======================================================================
// [FE1 — 2026-09-29] FieldSelect / MultiFieldSelect — the shared dropdown
// used to collapse a single-choice or multi-choice field that used to be a
// permanently-open row of chips (owner, live review of the Job composer:
// "all tags are seen and its really looking bad, can we keep them in
// dropdowns"). Closed by default: a button shows the current value (or a
// placeholder), and a small popover opens on tap — same vy-popover /
// vy-menu-item visual language already used by the top-bar menus
// (LanguageSwitcher, NotificationBell), so this reads as one system, not a
// bespoke control. Presentational: value in, onChange out.
//
// Usable on mobile: 44px tap targets (vy-menu-item), closes on outside tap
// or Escape, and is keyboard operable — every option is a real <button>, so
// Tab/Shift+Tab moves through them and Enter/Space activates one; arrow
// keys additionally roam the open list without leaving the popover.
// ======================================================================

import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";

export interface FieldSelectOption<T extends string | number> {
  value: T;
  label: string;
}

// [Design system 2026-09-30] the shared dismiss rule (outside tap, Escape,
// route change, another popover opening) — lib/usePopoverDismiss.ts.
function useOutsideClose(open: boolean, onClose: () => void) {
  return usePopoverDismiss<HTMLDivElement>(open, onClose);
}

/**
 * [FE1 — 2026-09-29, owner: "open emulator and check them" / "an open
 * listbox never falls off-screen or under the bottom hub"] Flip the popover
 * above the trigger when there isn't room below — common on a phone where a
 * field near the sticky action bar would otherwise open a list that runs
 * off the bottom of the screen. Re-measured every time the popover opens.
 */
function usePlacement(open: boolean, anchorRef: React.RefObject<HTMLDivElement | null>): "down" | "up" {
  const [placement, setPlacement] = useState<"down" | "up">("down");
  useEffect(() => {
    if (!open || !anchorRef.current) return;
    const rect = anchorRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;
    // 260px covers a handful of options before the internal scroll takes
    // over; below that, prefer whichever side actually has more room.
    setPlacement(spaceBelow < 260 && spaceAbove > spaceBelow ? "up" : "down");
  }, [open, anchorRef]);
  return placement;
}

/** Arrow-key roaming across the option buttons inside an open popover. */
function useRoving(containerRef: React.RefObject<HTMLDivElement | null>, open: boolean) {
  return (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp" && e.key !== "Home" && e.key !== "End") return;
    const root = containerRef.current;
    if (!root) return;
    const items = Array.from(root.querySelectorAll<HTMLButtonElement>('[role="option"]'));
    if (items.length === 0) return;
    e.preventDefault();
    const active = document.activeElement as HTMLElement | null;
    const i = items.findIndex((el) => el === active);
    let next = 0;
    if (e.key === "Home") next = 0;
    else if (e.key === "End") next = items.length - 1;
    else if (e.key === "ArrowDown") next = i < 0 ? 0 : (i + 1) % items.length;
    else next = i < 0 ? items.length - 1 : (i - 1 + items.length) % items.length;
    items[next]?.focus();
  };
}

/**
 * A single-choice dropdown. Closed, it reads "placeholder" when value is
 * null, else the chosen option's label — no separate field label inside
 * the control, since the surrounding FieldBlock already shows one above it.
 */
export function FieldSelect<T extends string | number>({
  options,
  value,
  onChange,
  placeholder,
  allowClear = true,
  ariaLabel,
}: {
  options: readonly FieldSelectOption<T>[];
  value: T | null;
  onChange: (next: T | null) => void;
  placeholder: string;
  allowClear?: boolean;
  ariaLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useOutsideClose(open, () => setOpen(false));
  const onRoam = useRoving(ref, open);
  const placement = usePlacement(open, ref);
  const current = useMemo(() => options.find((o) => o.value === value) ?? null, [options, value]);

  return (
    <div ref={ref} className="vy-menu-anchor vy-field-select" onKeyDown={onRoam}>
      <button
        type="button"
        className="vy-field-select-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <span className={current ? "vy-field-select-value" : "vy-field-select-value vy-muted"}>{current ? current.label : placeholder}</span>
        <ChevronDown size={16} aria-hidden="true" className="vy-field-select-chevron" data-open={open || undefined} />
      </button>
      {open && (
        <div className="vy-popover vy-field-select-popover" data-placement={placement} role="listbox" aria-label={ariaLabel}>
          {allowClear && (
            <button
              type="button"
              role="option"
              aria-selected={value === null}
              className="vy-menu-item"
              onClick={() => {
                onChange(null);
                setOpen(false);
              }}
            >
              <span>{placeholder}</span>
              {value === null && <Check size={18} aria-hidden="true" />}
            </button>
          )}
          {options.map((o) => (
            <button
              key={String(o.value)}
              type="button"
              role="option"
              aria-selected={value === o.value}
              className="vy-menu-item"
              onClick={() => {
                onChange(o.value);
                setOpen(false);
              }}
            >
              <span>{o.label}</span>
              {value === o.value && <Check size={18} aria-hidden="true" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * A multi-choice checklist dropdown. Closed, it reads "placeholder" when
 * nothing is picked, the single label when exactly one is, else a
 * "{{count}} selected" summary — never a permanently-open row of toggles.
 */
export function MultiFieldSelect<T extends string>({
  options,
  value,
  onChange,
  placeholder,
  selectedCountLabel,
  ariaLabel,
}: {
  options: readonly FieldSelectOption<T>[];
  value: readonly string[];
  onChange: (next: string[]) => void;
  placeholder: string;
  /** "{{count}} selected" already interpolated by the caller. */
  selectedCountLabel: (count: number) => string;
  ariaLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useOutsideClose(open, () => setOpen(false));
  const onRoam = useRoving(ref, open);
  const placement = usePlacement(open, ref);
  const chosen = options.filter((o) => value.includes(o.value));

  function toggle(v: T) {
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  }

  const summary = chosen.length === 0 ? placeholder : chosen.length === 1 ? chosen[0].label : selectedCountLabel(chosen.length);

  return (
    <div ref={ref} className="vy-menu-anchor vy-field-select" onKeyDown={onRoam}>
      <button
        type="button"
        className="vy-field-select-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <span className={chosen.length ? "vy-field-select-value" : "vy-field-select-value vy-muted"}>{summary}</span>
        <ChevronDown size={16} aria-hidden="true" className="vy-field-select-chevron" data-open={open || undefined} />
      </button>
      {open && (
        <div className="vy-popover vy-field-select-popover" data-placement={placement} role="listbox" aria-multiselectable="true" aria-label={ariaLabel}>
          {options.map((o) => {
            const on = value.includes(o.value);
            return (
              <button key={o.value} type="button" role="option" aria-selected={on} className="vy-menu-item" onClick={() => toggle(o.value)}>
                <span>{o.label}</span>
                {on && <Check size={18} aria-hidden="true" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
