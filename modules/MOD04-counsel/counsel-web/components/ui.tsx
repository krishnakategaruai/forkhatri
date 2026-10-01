"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Star, ShieldCheck } from "lucide-react";
import { initials } from "@/lib/format";
import { mediaUrl } from "@/lib/api";

/* ---------- Toast ---------- */
const ToastCtx = createContext<(msg: string) => void>(() => {});
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const timer = useRef<number | null>(null);
  const show = useCallback((m: string) => {
    setMsg(m);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setMsg(null), 2800);
  }, []);
  return (
    <ToastCtx.Provider value={show}>
      {children}
      {msg && <div className="toast fade-in" role="status">{msg}</div>}
    </ToastCtx.Provider>
  );
}
export const useToast = () => useContext(ToastCtx);

/* ---------- Avatar ---------- */
export function Avatar({ name, url, size = 48 }: { name: string; url?: string | null; size?: number }) {
  return (
    <span className="avatar" style={{ width: size, height: size, fontSize: size * 0.38 }} aria-hidden>
      {url ? <img src={mediaUrl(url) ?? ""} alt="" /> : initials(name)}
    </span>
  );
}

/* ---------- Stars ---------- */
export function Stars({ value, count }: { value: number | null; count?: number }) {
  const { t } = useTranslation();
  if (value === null || value === undefined) return <span className="tiny muted">{t("card.new")}</span>;
  return (
    <span className="row" style={{ gap: 6 }}>
      <span className="stars" aria-label={t("a11y.rating", { value })}>
        {[1, 2, 3, 4, 5].map((i) => (
          <Star key={i} fill={i <= Math.round(value) ? "currentColor" : "none"} strokeWidth={1.5} />
        ))}
      </span>
      <span className="small num">{value.toFixed(1)}</span>
      {count !== undefined && <span className="tiny muted">({count})</span>}
    </span>
  );
}

export function StarInput({ value, onChange, label }: { value: number; onChange: (v: number) => void; label: string }) {
  return (
    <div className="between">
      <span className="small">{label}</span>
      <span className="stars-input" role="radiogroup" aria-label={label}>
        {[1, 2, 3, 4, 5].map((i) => (
          <button key={i} type="button" className={i <= value ? "on" : ""} onClick={() => onChange(i)} role="radio" aria-checked={i === value} aria-label={String(i)}>
            <Star fill={i <= value ? "currentColor" : "none"} strokeWidth={1.5} />
          </button>
        ))}
      </span>
    </div>
  );
}

/* ---------- Verification tags ---------- */
export function VerifiedTags({ dims, max = 3 }: { dims: string[]; max?: number }) {
  const { t } = useTranslation();
  if (!dims.length) return null;
  const shown = dims.slice(0, max);
  return (
    <span className="row" style={{ gap: 6 }}>
      {shown.map((d) => (
        <span key={d} className="tag tag-verified"><ShieldCheck size={12} strokeWidth={2} />{t(`verify.${d}`)}</span>
      ))}
      {dims.length > max && <span className="tag">+{dims.length - max}</span>}
    </span>
  );
}

/* ---------- Empty ---------- */
export function Empty({ title, body, action }: { title: string; body?: string; action?: React.ReactNode }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      {body && <p className="small">{body}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

export function Skeleton({ h = 90, n = 3 }: { h?: number; n?: number }) {
  return <div className="stack">{Array.from({ length: n }).map((_, i) => <div key={i} className="skel" style={{ height: h }} />)}</div>;
}

/* ---------- Dialog ---------- */
export function Dialog({ open, onClose, children, title }: { open: boolean; onClose: () => void; children: React.ReactNode; title?: string }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} className="dialog" onClose={onClose} onClick={(e) => { if (e.target === ref.current) onClose(); }}>
      <div className="card-pad stack">
        {title && <h3>{title}</h3>}
        {children}
      </div>
    </dialog>
  );
}

/* ---------- Async data hook ---------- */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // The latest loader is read through a ref; `deps` decide when to load again.
  const fnRef = useRef(fn);
  useEffect(() => { fnRef.current = fn; });
  const key = JSON.stringify(deps);
  const run = useCallback(async () => {
    setLoading(true);
    try { setData(await fnRef.current()); setError(null); } catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void run(); }, [run, key]);
  return { data, error, loading, reload: run, setData };
}

/** The current time, refreshed every `ms` — keeps time checks out of render. */
export function useNow(ms = 30000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => { const h = window.setInterval(() => setNow(Date.now()), ms); return () => window.clearInterval(h); }, [ms]);
  return now;
}

/* ---------- Booking status ---------- */
export function StatusTag({ status, role }: { status: string; role?: "seeker" | "provider" }) {
  const { t } = useTranslation();
  const cls = status === "confirmed" || status === "in_progress" ? "tag-ok" : status === "completed" ? "tag" : status.startsWith("cancel") || status.startsWith("no_show") ? "tag-danger" : "tag-warn";
  // Who cancelled or missed it reads differently for each side ("Cancelled by you" vs "Cancelled by the client").
  const label = role ? t(`status_for.${role}.${status}`, { defaultValue: t(`status.${status}`) }) : t(`status.${status}`);
  return <span className={`tag ${cls}`}>{label}</span>;
}
