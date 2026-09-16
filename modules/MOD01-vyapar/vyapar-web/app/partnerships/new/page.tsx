"use client";

// [TR025] Create a Partnership Request (FR25) — UX17's request form.
// Fewer actions: category and locality are prefilled from the recipient's
// own listing (editable), the sender's listing is auto-chosen when they have
// exactly one, and Send stays disabled until every field meets its minimum —
// so a member never submits into a validation error. No Active Listing shows
// the "create a listing first" prompt in place of the form; the pending-cap
// error links straight to Activity.
// Traces to: FR25, TR025, UX17
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, apiFetch, ApiError } from "@/lib/api";

interface ListingLite {
  id: string;
  name: string;
  locality: string;
  categories: string[];
  state: string;
}

const LONG_FIELDS = ["need", "offer", "expectations", "timing", "next_step"] as const;
type LongField = (typeof LONG_FIELDS)[number];
const LABEL_KEY: Record<LongField, string> = {
  need: "need",
  offer: "offer",
  expectations: "expectations",
  timing: "timing",
  next_step: "nextStep",
};

function ComposeInner() {
  const { t } = useTranslation(["partnerships", "common"]);
  const router = useRouter();
  const params = useSearchParams();
  const listingId = params.get("listing_id") ?? "";
  const [target, setTarget] = useState<ListingLite | null>(null);
  const [mine, setMine] = useState<ListingLite[] | null>(null);
  const [fromId, setFromId] = useState("");
  const [values, setValues] = useState<Record<LongField, string>>({ need: "", offer: "", expectations: "", timing: "", next_step: "" });
  const [category, setCategory] = useState("");
  const [locality, setLocality] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPendingLink, setShowPendingLink] = useState(false);
  const [idempotencyKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now())));

  useEffect(() => {
    if (!listingId) return;
    api.get<ListingLite>(`/v1/listings/${listingId}`).then((l) => {
      setTarget(l);
      setCategory((c) => c || l.categories[0] || "");
      setLocality((v) => v || l.locality);
    });
    api.get<ListingLite[]>("/v1/listings/mine").then((ls) => {
      const active = ls.filter((l) => l.state === "active_unverified" || l.state === "active_verified");
      setMine(active);
      if (active.length > 0) setFromId(active[0].id);
    });
  }, [listingId]);

  if (mine !== null && mine.length === 0) {
    return (
      <main className="vy-shell">
        <h1>{t("partnerships:compose.title")}</h1>
        <div className="vy-card vy-stack">
          <p>{t("partnerships:compose.needListing")}</p>
          <a className="vy-btn vy-btn-primary" href="/listings/new" style={{ textDecoration: "none", alignSelf: "flex-start" }}>
            {t("partnerships:compose.createListing")}
          </a>
        </div>
      </main>
    );
  }

  const valid =
    LONG_FIELDS.every((f) => values[f].trim().length >= 10) && category.trim().length >= 2 && locality.trim().length >= 2 && !!fromId;

  async function send() {
    setSending(true);
    setError(null);
    setShowPendingLink(false);
    try {
      const created = await apiFetch<{ id: string }>("/v1/partnership-requests", {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({ recipient_listing_id: listingId, sender_listing_id: fromId, category, locality, ...values }),
      });
      router.push(`/partnerships/${created.id}`);
    } catch (e) {
      if (e instanceof ApiError && typeof e.detail === "object" && e.detail !== null) {
        const detail = e.detail as unknown as { message: string; code?: string; existing_id?: string };
        setError(detail.message);
        setShowPendingLink(detail.code === "pending_cap");
        if (detail.existing_id) router.push(`/partnerships/${detail.existing_id}`);
      } else {
        setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
      }
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="vy-shell">
      <h1>{t("partnerships:compose.title")}</h1>
      {target && <p className="vy-muted">{t("partnerships:compose.to", { name: target.name })}</p>}
      <div className="vy-stack">
        {mine && mine.length > 1 && (
          <label className="vy-field">
            <span className="vy-label">{t("partnerships:compose.fromListing")}</span>
            <select className="vy-select" value={fromId} onChange={(e) => setFromId(e.target.value)}>
              {mine.map((l) => (
                <option key={l.id} value={l.id}>{l.name}</option>
              ))}
            </select>
          </label>
        )}
        {LONG_FIELDS.map((f) => (
          <label key={f} className="vy-field">
            <span className="vy-label">{t(`partnerships:compose.${LABEL_KEY[f]}` as "compose.need")}</span>
            <textarea
              className="vy-textarea"
              rows={f === "timing" || f === "next_step" ? 1 : 2}
              maxLength={500}
              value={values[f]}
              placeholder={f === "next_step" ? t("partnerships:compose.nextStepPlaceholder") : undefined}
              onChange={(e) => setValues((v) => ({ ...v, [f]: e.target.value }))}
            />
            <span className="vy-muted" style={{ fontSize: 12 }}>
              {values[f].trim().length < 10 ? t("partnerships:compose.minHint") : t("partnerships:compose.counter", { n: values[f].length })}
            </span>
          </label>
        ))}
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          <label className="vy-field" style={{ flex: 1, minWidth: 140 }}>
            <span className="vy-label">{t("partnerships:compose.category")}</span>
            <input className="vy-input" value={category} maxLength={120} onChange={(e) => setCategory(e.target.value)} />
          </label>
          <label className="vy-field" style={{ flex: 1, minWidth: 140 }}>
            <span className="vy-label">{t("partnerships:compose.locality")}</span>
            <input className="vy-input" value={locality} maxLength={120} onChange={(e) => setLocality(e.target.value)} />
          </label>
        </div>
        <p className="vy-muted">{t("partnerships:compose.contactNote")}</p>
        {error && <p className="vy-error">{error}</p>}
        {showPendingLink && (
          <a href="/activity" className="vy-muted">{t("partnerships:compose.viewPending")} →</a>
        )}
        <button className="vy-btn vy-btn-primary" disabled={!valid || sending} onClick={send}>
          {sending ? t("common:state.saving") : t("partnerships:compose.send")}
        </button>
      </div>
    </main>
  );
}

export default function NewPartnershipPage() {
  return (
    <Suspense fallback={null}>
      <ComposeInner />
    </Suspense>
  );
}
