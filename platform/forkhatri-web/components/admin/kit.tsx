"use client";

/**
 * Shared pieces of the Admin & Governance Console: the console context (who is acting,
 * in which language), date formatting in Indian order, a modal dialog built on <dialog>,
 * and the small visual primitives every section uses.
 */
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { ApiError, NetworkError, type Lang } from "@/lib/api";
import type { AdminMe, Person, RoleKey } from "@/lib/admin-api";
import { adminLabel, type AdminKey, type AdminT } from "@/lib/admin-i18n";

export type Console = {
  me: AdminMe;
  lang: Lang;
  t: AdminT;
  can: (permission: string) => boolean;
  /** Bumped after any change so the badges in the navigation refresh. */
  version: number;
  changed: () => void;
};

export const ConsoleContext = createContext<Console | null>(null);

export function useConsole(): Console {
  const value = useContext(ConsoleContext);
  if (!value) throw new Error("useConsole outside the admin console");
  return value;
}

const LOCALES: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

/** 29 Sep 2026: day first, as Indian readers expect. */
export function formatDate(iso: string | null | undefined, lang: Lang): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat(LOCALES[lang], { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export function formatDateTime(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALES[lang], { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}

/** "in 5 hours", "3 days ago". */
export function relative(iso: string | null | undefined, lang: Lang, t: AdminT): string {
  if (!iso) return "";
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000;
  const abs = Math.abs(seconds);
  if (abs < 45) return t("justNow");
  const rtf = new Intl.RelativeTimeFormat(LOCALES[lang], { numeric: "auto" });
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["minute", 60],
    ["hour", 3600],
    ["day", 86400],
    ["month", 2592000],
    ["year", 31536000],
  ];
  let unit: Intl.RelativeTimeFormatUnit = "minute";
  let size = 60;
  for (const [u, s] of units) if (abs >= s) [unit, size] = [u, s];
  return rtf.format(Math.round(seconds / size), unit);
}

export function formatNumber(n: number, lang: Lang): string {
  return new Intl.NumberFormat(LOCALES[lang]).format(n);
}

export function roleName(t: AdminT, role: RoleKey | string): string {
  return adminLabel(t, `role_${role}`);
}

export function reasonName(t: AdminT, code: string | null | undefined): string {
  return code ? adminLabel(t, `reason_${code}`) : "";
}

/** "President · National", "Moderator · Milavn", "Chapter head · Hyderabad". */
export function scopeName(t: AdminT, scope_kind: string, scope_name: string | null | undefined, scope_key: string | null | undefined): string {
  if (scope_kind === "platform") return t("national");
  return scope_name || scope_key || "";
}

export function errorMessage(t: AdminT, error: unknown): string {
  if (error instanceof NetworkError) return t("err_network");
  if (error instanceof ApiError) {
    if (error.code === "module_refused") return t("err_module_refused", { message: error.message });
    const key = `err_${error.code}` as AdminKey;
    const text = t(key);
    if (text !== key) return text;
  }
  return t("err_generic");
}

export function initials(name: string | null | undefined): string {
  const parts = (name ?? "?").trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "?") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

export function Avatar({ person, size = 36 }: { person: Person | { display_name: string | null } | null; size?: number }) {
  return (
    <span className="adm-avatar" style={{ width: size, height: size, fontSize: size * 0.38 }} aria-hidden="true">
      {initials(person?.display_name)}
    </span>
  );
}

export function Badge({ tone = "neutral", children }: { tone?: "neutral" | "danger" | "warn" | "ok" | "accent"; children: ReactNode }) {
  return <span className={`adm-badge tone-${tone}`}>{children}</span>;
}

export function PageHead({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <header className="adm-pagehead">
      <div>
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {actions && <div className="adm-pagehead-actions">{actions}</div>}
    </header>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="adm-empty">{children}</p>;
}

export function Loading() {
  return (
    <div className="adm-loading" aria-busy="true">
      <span className="adm-sk" />
      <span className="adm-sk" />
      <span className="adm-sk short" />
    </div>
  );
}

export function ErrorLine({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <p className="adm-error" role="alert">
      {error}
    </p>
  );
}

/** A modal dialog on the native <dialog> element: focus trap, Escape and backdrop come for free. */
export function Dialog({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      className="adm-dialog"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
      aria-label={title}
    >
      {open && (
        <div className="adm-dialog-body">
          <h2>{title}</h2>
          {children}
        </div>
      )}
    </dialog>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="adm-field">
      <span className="adm-field-label">{label}</span>
      {children}
      {hint && <span className="adm-field-hint">{hint}</span>}
    </label>
  );
}

/** Chips for a small set of choices (lengths, filters). */
export function Chips<T extends string | number | null>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: { value: T; label: string; count?: number }[];
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div className="adm-chips" role="radiogroup" aria-label={label}>
      {options.map((option) => (
        <button
          key={String(option.value)}
          type="button"
          role="radio"
          aria-checked={option.value === value}
          className={`adm-chip${option.value === value ? " is-on" : ""}`}
          onClick={() => onChange(option.value)}
        >
          {option.label}
          {option.count !== undefined && <span className="adm-chip-count">{option.count}</span>}
        </button>
      ))}
    </div>
  );
}

export function Section({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="adm-section">
      <div className="adm-section-head">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** Whether a moment has passed (kept out of render bodies so they stay pure). */
export function isPast(iso: string): boolean {
  return new Date(iso).getTime() < Date.now();
}

/**
 * Loads data for a screen. State is only ever set from the promise callbacks, never
 * synchronously inside the effect, and a stale answer (after deps change) is dropped.
 * `reload()` fetches again; `set` lets a screen apply the result of its own action.
 */
export function useLoad<T>(fn: () => Promise<T>, deps: readonly unknown[]) {
  const key = JSON.stringify(deps);
  const [state, setState] = useState<{ key: string; data: T | null; error: unknown }>({ key: "", data: null, error: null });
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    let live = true;
    fn().then(
      (data) => live && setState({ key, data, error: null }),
      (error) => live && setState((prev) => ({ key, data: prev.key === key ? prev.data : null, error })),
    );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, nonce]);
  // An answer for other inputs (a different tab or filter) is never shown as this one's.
  const current = state.key === key;
  return {
    data: current ? state.data : null,
    error: current ? state.error : null,
    reload: () => setNonce((n) => n + 1),
    set: (data: T) => setState({ key, data, error: null }),
  };
}
