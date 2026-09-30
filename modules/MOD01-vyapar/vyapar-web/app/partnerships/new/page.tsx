"use client";

// [TR025] Create a business partnership request (FR25). Category and
// locality are prefilled from the recipient's own profile (editable), the
// sender's profile is auto-chosen when they have exactly one, and Send stays
// disabled until every field meets its minimum — with the reason under the
// button (critique P2). No business profile shows the "create one first"
// prompt in place of the form; the pending-cap error links to Activity.
// [Design language 2026-09-29] Three section cards (who you are writing to
// · what you each bring · where and when), a live preview beside them on
// desktop, one filled button.
// Traces to: FR25, TR025, UX17
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { AlertTriangle, Building2, ChevronLeft, Handshake, Lock, MapPin } from "lucide-react";
import { api, apiFetch, ApiError } from "@/lib/api";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import DisabledReason from "@/app/components/DisabledReason";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";
import "@/app/styles/deals-2026.css";

interface ListingLite {
  id: string;
  name: string;
  locality: string;
  categories: string[];
  category_labels?: string[];
  state: string;
}

const LONG_FIELDS = ["need", "offer", "expectations", "timing", "next_step"] as const;
type LongField = (typeof LONG_FIELDS)[number];
const LABEL_KEY: Record<LongField, string> = { need: "need", offer: "offer", expectations: "expectations", timing: "timing", next_step: "nextStep" };
const MIN = 10;

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
      setCategory((c) => c || l.category_labels?.[0] || l.categories[0] || "");
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
      <Screen width="wide">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("partnerships:compose.title")}</h1>
          </div>
          <DealsEmpty
            icon={<Building2 size={24} strokeWidth={1.75} aria-hidden="true" />}
            title={t("partnerships:compose.needListingTitle")}
            body={t("partnerships:compose.needListing")}
            action={
              <Link className="vy-btn vy-btn-primary" href="/listings/new" style={{ textDecoration: "none" }}>
                {t("partnerships:compose.createListing")}
              </Link>
            }
          />
        </div>
      </Screen>
    );
  }

  const missing = LONG_FIELDS.filter((f) => values[f].trim().length < MIN);
  const valid = missing.length === 0 && category.trim().length >= 2 && locality.trim().length >= 2 && !!fromId;
  const blocker = !valid
    ? missing.length > 0
      ? t("partnerships:compose.blockerFields", { count: missing.length })
      : t("partnerships:compose.blockerWhere")
    : null;

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

  const fromListing = mine?.find((l) => l.id === fromId) ?? null;
  const previewBody = LONG_FIELDS.filter((f) => values[f].trim())
    .map((f) => `${t(`partnerships:compose.${LABEL_KEY[f]}` as "compose.need")}: ${values[f].trim()}`)
    .join("\n\n");

  const field = (f: LongField, rows: number) => (
    <label key={f} className="vy-field">
      <span className="vy-label">{t(`partnerships:compose.${LABEL_KEY[f]}` as "compose.need")}</span>
      <textarea className="vy-textarea" rows={rows} maxLength={500} value={values[f]} placeholder={t(`partnerships:compose.${LABEL_KEY[f]}Placeholder` as "compose.nextStepPlaceholder")} onChange={(e) => setValues((v) => ({ ...v, [f]: e.target.value }))} />
      <span className="vy-dl-counter">
        <span>{values[f].trim().length < MIN ? t("partnerships:compose.minHint") : ""}</span>
        <span>{t("partnerships:compose.counter", { n: values[f].length })}</span>
      </span>
    </label>
  );

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        {target && (
          <Link href={`/listings/${target.id}`} transitionTypes={["vy-back"]} className="vy-dl-back">
            <ChevronLeft size={18} strokeWidth={2} aria-hidden="true" />
            {target.name}
          </Link>
        )}
        <div className="vy-dl-head">
          <h1>{t("partnerships:compose.title")}</h1>
          <p>{target ? t("partnerships:compose.subtitle", { name: target.name }) : t("partnerships:compose.subtitlePlain")}</p>
        </div>
        <div className="vy-compose">
          <div className="vy-compose-main">
            <div className="vy-dl-page" style={{ gap: "var(--space-4)" }}>
              {mine === null || !target ? (
                <SkeletonGrid count={2} grid={false} />
              ) : (
                <>
                  <section className="vy-dl-sec" aria-label={t("partnerships:compose.secWho")}>
                    <div className="vy-dl-sec-head">
                      <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Building2 size={20} strokeWidth={1.75} /></span>
                      <h2 className="vy-card-title">{target.name}</h2>
                      <span className="vy-dl-sec-hint">{[target.category_labels?.[0], target.locality].filter(Boolean).join(" · ")}</span>
                    </div>
                    {mine.length > 1 ? (
                      <label className="vy-field">
                        <span className="vy-label">{t("partnerships:compose.fromListing")}</span>
                        <select className="vy-select" value={fromId} onChange={(e) => setFromId(e.target.value)}>
                          {mine.map((l) => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                          ))}
                        </select>
                      </label>
                    ) : (
                      fromListing && <p className="vy-dl-hint">{t("partnerships:compose.fromLine", { name: fromListing.name })}</p>
                    )}
                  </section>

                  <section className="vy-dl-sec" aria-label={t("partnerships:compose.secBring")}>
                    <div className="vy-dl-sec-head">
                      <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Handshake size={20} strokeWidth={1.75} /></span>
                      <h2 className="vy-card-title">{t("partnerships:compose.secBring")}</h2>
                      <span className="vy-dl-sec-hint">{t("partnerships:compose.guide1")}</span>
                    </div>
                    {field("need", 2)}
                    {field("offer", 2)}
                    {field("expectations", 2)}
                  </section>

                  <section className="vy-dl-sec" aria-label={t("partnerships:compose.secWhere")}>
                    <div className="vy-dl-sec-head">
                      <span className="vy-dl-tile" aria-hidden="true"><MapPin size={20} strokeWidth={1.75} /></span>
                      <h2 className="vy-card-title">{t("partnerships:compose.secWhere")}</h2>
                      <span className="vy-dl-sec-hint">{t("partnerships:compose.secWhereHint")}</span>
                    </div>
                    <div className="vy-field-pair">
                      <label className="vy-field">
                        <span className="vy-label">{t("partnerships:compose.category")}</span>
                        <input className="vy-input" value={category} maxLength={120} onChange={(e) => setCategory(e.target.value)} />
                      </label>
                      <label className="vy-field">
                        <span className="vy-label">{t("partnerships:compose.locality")}</span>
                        <input className="vy-input" value={locality} maxLength={120} onChange={(e) => setLocality(e.target.value)} />
                      </label>
                    </div>
                    {field("timing", 1)}
                    {field("next_step", 1)}
                  </section>

                  {error && (
                    <div className="vy-dl-notice" data-tone="bad" role="alert">
                      <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
                      <div className="vy-dl-row-body">
                        <span>{error}</span>
                        {showPendingLink && (
                          <a href="/activity" className="vy-dl-link" style={{ marginTop: 4 }}>{t("partnerships:compose.viewPending")}</a>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>
                    <button className="vy-btn vy-btn-primary" aria-describedby={blocker ? "pn-why" : undefined} disabled={!valid || sending} onClick={send}>
                      {sending ? t("common:state.saving") : t("partnerships:compose.send")}
                    </button>
                    <DisabledReason id="pn-why" show={!!blocker && !sending}>{blocker}</DisabledReason>
                    <p className="vy-dl-safety">
                      <Lock size={13} strokeWidth={2} aria-hidden="true" />
                      <span>{t("partnerships:compose.contactNote")}</span>
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
          <ComposerPreview caption={t("partnerships:compose.previewCaption", { name: target?.name ?? "" })} guide={[t("partnerships:compose.guide1"), t("partnerships:compose.guide2")]}>
            <PreviewCard title={fromListing?.name ?? ""} subtitle={[category.trim(), locality.trim()].filter(Boolean).join(" · ") || undefined} body={previewBody} bodyEmpty={t("partnerships:compose.previewEmpty")} />
          </ComposerPreview>
        </div>
      </div>
    </Screen>
  );
}

export default function NewPartnershipPage() {
  return (
    <Suspense fallback={null}>
      <ComposeInner />
    </Suspense>
  );
}
