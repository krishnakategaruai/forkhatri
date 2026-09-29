"use client";

// [FE1 — 2026-09-28] Small, presentational form controls shared by the
// posting composer and the response composers: a labelled field block
// (optional marker, "please check" flag, inline error, anchor for jumps),
// single/multi option chips (one tap instead of a dropdown), a segmented
// control, and rupee inputs that read back in Indian format.
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { formatRupees, rupeesToPaise } from "@/lib/money";

export function fieldAnchor(code: string): string {
  return `vy-field-${code}`;
}

export function FieldBlock({
  code,
  label,
  optional = false,
  flagged = false,
  onLooksRight,
  error,
  hint,
  children,
  htmlFor,
}: {
  code: string;
  label: string;
  optional?: boolean;
  flagged?: boolean;
  onLooksRight?: () => void;
  error?: string | null;
  hint?: string;
  children: ReactNode;
  htmlFor?: string;
}) {
  const { t } = useTranslation("hiring");
  return (
    <div id={fieldAnchor(code)} className={`vy-field${flagged ? " vy-field-flagged" : ""}`} style={{ scrollMarginTop: 96 }}>
      <div className="vy-field-head">
        <label className="vy-label" htmlFor={htmlFor}>
          {label} {optional && <span className="vy-optional">· {t("fields.optional")}</span>}
        </label>
        {flagged && (
          <span className="vy-row" style={{ gap: 4 }}>
            <span className="vy-badge vy-badge-check">{t("composer.pleaseCheck")}</span>
            {onLooksRight && (
              <button type="button" className="vy-check-ok" onClick={onLooksRight}>
                ✓ {t("composer.looksRight")}
              </button>
            )}
          </span>
        )}
      </div>
      {children}
      {hint && !error && <span className="vy-field-hint">{hint}</span>}
      {error && (
        <span className="vy-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export function OptionChips<T extends string | number>({
  options,
  value,
  onChange,
  label,
  allowClear = true,
  ariaLabel,
}: {
  options: readonly T[];
  value: T | null;
  onChange: (next: T | null) => void;
  label: (v: T) => string;
  allowClear?: boolean;
  ariaLabel?: string;
}) {
  return (
    <div className="vy-options" role="group" aria-label={ariaLabel}>
      {options.map((o) => (
        <button
          key={String(o)}
          type="button"
          className="vy-chip"
          aria-pressed={value === o}
          onClick={() => onChange(value === o && allowClear ? null : o)}
        >
          {label(o)}
        </button>
      ))}
    </div>
  );
}

export function MultiChips<T extends string>({
  options,
  value,
  onChange,
  label,
  ariaLabel,
}: {
  options: readonly T[];
  value: readonly string[];
  onChange: (next: string[]) => void;
  label: (v: T) => string;
  ariaLabel?: string;
}) {
  return (
    <div className="vy-options" role="group" aria-label={ariaLabel}>
      {options.map((o) => {
        const on = value.includes(o);
        return (
          <button
            key={o}
            type="button"
            className="vy-chip"
            aria-pressed={on}
            onClick={() => onChange(on ? value.filter((x) => x !== o) : [...value, o])}
          >
            {on ? "✓ " : ""}
            {label(o)}
          </button>
        );
      })}
    </div>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
  ariaLabel,
}: {
  options: readonly T[];
  value: T;
  onChange: (next: T) => void;
  label: (v: T) => string;
  ariaLabel?: string;
}) {
  return (
    <div className="vy-seg" role="group" aria-label={ariaLabel}>
      {options.map((o) => (
        <button key={o} type="button" aria-pressed={value === o} onClick={() => onChange(o)}>
          {label(o)}
        </button>
      ))}
    </div>
  );
}

/**
 * Plain digits are shown with Indian grouping as they are typed
 * ("150000" → "1,50,000"); anything else ("15k", "1.5 lakh") is left as
 * typed and read back under the field.
 */
export function groupDigits(value: string): string {
  const bare = value.replace(/,/g, "");
  if (!/^\d+$/.test(bare)) return value;
  const n = bare.replace(/^0+(?=\d)/, "");
  if (n.length <= 3) return n;
  const last3 = n.slice(-3);
  const rest = n.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${rest},${last3}`;
}

/**
 * A rupee input: ₹ inside the field, the numeric keypad on a phone, and
 * whatever people actually type understood — "15k", "1.5 lakh", "15 हज़ार",
 * "15 వేలు", Devanagari/Telugu digits (lib/money.ts rupeesToPaise). When
 * the text is anything but plain digits, the amount it was read as is shown
 * under the field ("= ₹15,000"), so nothing is saved on a guess; text that
 * cannot be read as one amount says so instead.
 */
export function MoneyInput({
  value,
  onChange,
  placeholder,
  ariaLabel,
  id,
  invalid,
  readbackSuffix,
}: {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  id?: string;
  invalid?: boolean;
  /** Appended to the read-back, e.g. "a month". */
  readbackSuffix?: string;
}) {
  const { t, i18n } = useTranslation("hiring");
  const raw = value.trim();
  const parsed = raw ? rupeesToPaise(raw) : null;
  const plain = /^[\d,]+$/.test(raw);
  return (
    <div className="vy-stack" style={{ gap: 4, minWidth: 0 }}>
      <div className="vy-money">
        <span aria-hidden="true">₹</span>
        <input
          id={id}
          className="vy-input"
          inputMode="numeric"
          autoComplete="off"
          value={groupDigits(value)}
          maxLength={24}
          placeholder={placeholder}
          aria-label={ariaLabel}
          aria-invalid={invalid || (!!raw && parsed === null) || undefined}
          onChange={(e) => onChange(groupDigits(e.target.value))}
        />
      </div>
      {raw && parsed === null && <span className="vy-error">{t("fields.amountUnreadable")}</span>}
      {raw && parsed !== null && !plain && (
        <span className="vy-readback">= {formatRupees(parsed, i18n.language)}{readbackSuffix ? ` ${readbackSuffix}` : ""}</span>
      )}
    </div>
  );
}

export function MoneyRange({
  min,
  max,
  onMin,
  onMax,
  minLabel,
  maxLabel,
  invalid,
}: {
  min: string;
  max: string;
  onMin: (v: string) => void;
  onMax: (v: string) => void;
  minLabel: string;
  maxLabel: string;
  invalid?: boolean;
}) {
  return (
    <div className="vy-range">
      <MoneyInput value={min} onChange={onMin} placeholder={minLabel} ariaLabel={minLabel} invalid={invalid} />
      <span className="vy-range-sep" aria-hidden="true">–</span>
      <MoneyInput value={max} onChange={onMax} placeholder={maxLabel} ariaLabel={maxLabel} invalid={invalid} />
    </div>
  );
}

/** "₹15,000 – ₹18,000" from two typed rupee strings, or null when neither is set. */
export function readbackRange(min: string, max: string, language: string): string | null {
  const lo = rupeesToPaise(min);
  const hi = rupeesToPaise(max);
  if (lo === null && hi === null) return null;
  if (lo === null || hi === null || lo === hi) return formatRupees((lo ?? hi) as number, language);
  return `${formatRupees(lo, language)} – ${formatRupees(hi, language)}`;
}
