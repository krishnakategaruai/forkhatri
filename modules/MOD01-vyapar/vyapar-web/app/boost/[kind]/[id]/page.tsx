"use client";

// [TR030/TR054] Choose a promotion and confirm the full disclosure on ONE
// screen (FR30, FR54, UX20). Duration and the optional audience narrowing
// sit beside a live order summary (product, price, GST, credit, total,
// dates) and the full disclosure (what changes, what never changes, no
// renewal, cancel/refund rules, receipt). The only button that can start a
// payment names the amount and sends `confirmed: true` to the separate
// confirm-purchase call. Nothing is pre-selected; there are no timers. An
// ineligible item shows its reason and the single next step. No reach
// estimate is shown (UX20 DEC-001).
// [Design language 2026-09-29] Glossary: "Promote", never "Boost". Pricing
// as radio cards with a check, ₹ from lib/money, the GST line in the
// summary, and a sticky summary column on desktop.
import { useEffect, useState, use as useParamsPromise } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { AlertTriangle, Check, Megaphone, Receipt, ShieldCheck, Users } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import { formatDate } from "@/lib/format";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import DisabledReason from "@/app/components/DisabledReason";
import "@/app/styles/deals-2026.css";

interface Product {
  id: string;
  version: number;
  duration_days: number;
  price_paise: number;
  tax_paise: number;
  total_paise: number;
}

interface Options {
  eligible: boolean;
  reason: string | null;
  target_title: string;
  // category_labels are the translated display names; categories stays raw
  // (the value sent back on select, never rendered).
  audience: { locality: string | null; categories: string[]; category_labels: string[] };
  products: Product[];
  credit_available_paise: number;
  // Any length between min and max days, priced from the packs by the server.
  custom_duration: { min_days: number; max_days: number } | null;
}

interface Quote {
  days: number;
  product_id: string;
  price_paise: number;
  tax_paise: number;
  total_paise: number;
}

const CUSTOM = "custom";

export default function BoostPage({ params }: { params: Promise<{ kind: string; id: string }> }) {
  const { kind, id } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["commercial", "common"]);
  const router = useRouter();
  const [opts, setOpts] = useState<Options | null>(null);
  const [productId, setProductId] = useState<string | null>(null);
  const [onlyLocality, setOnlyLocality] = useState(false);
  const [onlyCategory, setOnlyCategory] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [customDays, setCustomDays] = useState(10);
  const [quote, setQuote] = useState<Quote | null>(null);
  // "Ends on" is counted from when the screen opened, not re-read on every render.
  const [openedAt] = useState(() => Date.now());

  // Live quote while the person drags the slider; a small debounce so a drag
  // is one request, not thirty.
  useEffect(() => {
    if (productId !== CUSTOM) return;
    const h = setTimeout(() => {
      api.get<Quote>(`/v1/promotions/quote?days=${customDays}`).then(setQuote).catch(() => setQuote(null));
    }, 150);
    return () => clearTimeout(h);
  }, [productId, customDays]);

  useEffect(() => {
    api
      .get<Options>(`/v1/promotions/options?target_kind=${kind}&target_id=${id}`)
      .then(setOpts)
      .catch((e) => setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, id]);

  const money = (p: number) => formatPaise(p, i18n.language);

  if (!opts) {
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          {notice ? (
            <DealsEmpty tone="neutral" icon={<AlertTriangle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("commercial:ineligible.notFound")} body={notice} />
          ) : (
            <SkeletonGrid count={3} grid={false} />
          )}
        </div>
      </Screen>
    );
  }

  if (!opts.eligible) {
    const reason = opts.reason ?? "notFound";
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <div className="vy-dl-head">
            <h1>{t("commercial:boost.title", { name: opts.target_title })}</h1>
          </div>
          <DealsEmpty
            tone="neutral"
            icon={<Megaphone size={24} strokeWidth={1.75} aria-hidden="true" />}
            title={t(`commercial:ineligible.${reason}` as "ineligible.notActive")}
            action={
              reason === "verifyFirst" ? (
                <a className="vy-btn vy-btn-primary" style={{ textDecoration: "none" }} href={kind === "listing" ? `/listings/${id}` : "/listings/mine"}>
                  {t("commercial:ineligible.getVerified")}
                </a>
              ) : undefined
            }
          />
        </div>
      </Screen>
    );
  }

  const product: Product | null =
    productId === CUSTOM
      ? quote && quote.days === customDays
        ? { id: CUSTOM, version: 0, duration_days: quote.days, price_paise: quote.price_paise, tax_paise: quote.tax_paise, total_paise: quote.total_paise }
        : null
      : (opts.products.find((p) => p.id === productId) ?? null);
  const custom = opts.custom_duration;
  const credit = product ? Math.min(opts.credit_available_paise, product.total_paise) : 0;
  const due = product ? product.total_paise - credit : 0;
  const endsOn = product ? formatDate(new Date(openedAt + product.duration_days * 86400000), i18n.language) : "";
  const audienceLocality = opts.audience.locality;

  async function confirm() {
    if (!product) return;
    setBusy(true);
    setNotice(null);
    try {
      const draft = await api.post<{ id: string }>("/v1/promotions", {
        target_kind: kind,
        target_id: id,
        product_id: product.id === CUSTOM ? undefined : product.id,
        custom_days: product.id === CUSTOM ? product.duration_days : undefined,
        audience_locality: onlyLocality && audienceLocality ? audienceLocality : undefined,
        audience_category: onlyCategory ?? undefined,
      });
      const res = await api.post<{ state: string; checkout_url: string | null; notice: string | null }>(`/v1/promotions/${draft.id}/confirm-purchase`, { confirmed: true });
      if (res.checkout_url) {
        setNotice(t("commercial:disclosure.redirecting"));
        window.location.assign(res.checkout_url);
        return;
      }
      router.push(`/promotions/${draft.id}${res.notice ? "?result=unavailable" : ""}`);
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
      setBusy(false);
    }
  }

  const productName = product
    ? product.id === CUSTOM
      ? t("commercial:boost.customProduct", { n: product.duration_days })
      : t(`commercial:product.${product.id}` as "product.boost_7d", { defaultValue: product.id })
    : null;

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <h1>{t("commercial:boost.title", { name: opts.target_title })}</h1>
          <p>{t("commercial:boost.subtitle")}</p>
        </div>

        <div className="vy-split">
          <div className="vy-split-main">
            <section className="vy-dl-sec" aria-labelledby="boost-duration">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Megaphone size={20} strokeWidth={1.75} /></span>
                <h2 id="boost-duration" className="vy-card-title">{t("commercial:boost.duration")}</h2>
                <span className="vy-dl-sec-hint">{t("commercial:boost.durationHint")}</span>
              </div>
              <div className="vy-dl-price-grid" role="radiogroup" aria-labelledby="boost-duration">
                {opts.products.map((p) => (
                  <button key={p.id} type="button" role="radio" aria-checked={productId === p.id} className="vy-dl-price" onClick={() => setProductId(p.id)}>
                    <span className="vy-dl-price-check" aria-hidden="true"><Check size={14} strokeWidth={3} /></span>
                    <span className="vy-dl-price-name">{t("commercial:boost.days", { n: p.duration_days })}</span>
                    <span className="vy-dl-price-amt">{money(p.total_paise)}</span>
                    <span className="vy-dl-price-sub">{t("commercial:boost.inclTaxShort")}</span>
                  </button>
                ))}
                {custom && (
                  <button type="button" role="radio" aria-checked={productId === CUSTOM} className="vy-dl-price" onClick={() => setProductId(CUSTOM)}>
                    <span className="vy-dl-price-check" aria-hidden="true"><Check size={14} strokeWidth={3} /></span>
                    <span className="vy-dl-price-name">{t("commercial:boost.custom")}</span>
                    <span className="vy-dl-price-amt">{quote && productId === CUSTOM && quote.days === customDays ? money(quote.total_paise) : "—"}</span>
                    <span className="vy-dl-price-sub">{t("commercial:boost.customRange", { min: custom.min_days, max: custom.max_days })}</span>
                  </button>
                )}
              </div>
              {custom && productId === CUSTOM && (
                <div className="vy-dl-panel">
                  <div className="vy-dl-actions" style={{ justifyContent: "space-between" }}>
                    <label htmlFor="boost-custom-days" className="vy-label">{t("commercial:boost.customDays")}</label>
                    <strong className="vy-dl-money">{t("commercial:boost.days", { n: customDays })}</strong>
                  </div>
                  <input id="boost-custom-days" className="vy-dl-range" type="range" min={custom.min_days} max={custom.max_days} value={customDays} onChange={(e) => setCustomDays(Number(e.target.value))} />
                  <div className="vy-dl-actions" style={{ justifyContent: "space-between" }}>
                    <input
                      className="vy-input"
                      type="number"
                      inputMode="numeric"
                      min={custom.min_days}
                      max={custom.max_days}
                      value={customDays}
                      aria-label={t("commercial:boost.customDays")}
                      style={{ width: 96 }}
                      onChange={(e) => {
                        const n = Number(e.target.value);
                        if (Number.isFinite(n)) setCustomDays(Math.min(custom.max_days, Math.max(custom.min_days, Math.round(n))));
                      }}
                    />
                    <span className="vy-dl-hint" aria-live="polite">
                      {quote && quote.days === customDays ? t("commercial:boost.inclTax", { amount: money(quote.total_paise) }) : t("common:state.loading")}
                    </span>
                  </div>
                  <p className="vy-dl-fine">{t("commercial:boost.customHelp")}</p>
                </div>
              )}
            </section>

            {(audienceLocality || opts.audience.categories.length > 0) && (
              <section className="vy-dl-sec" aria-labelledby="boost-audience">
                <div className="vy-dl-sec-head">
                  <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Users size={20} strokeWidth={1.75} /></span>
                  <h2 id="boost-audience" className="vy-card-title">{t("commercial:boost.audience")}</h2>
                  <span className="vy-dl-sec-hint">{t("commercial:boost.audienceHelp")}</span>
                </div>
                <div className="vy-dl-tags">
                  {audienceLocality && (
                    <button type="button" className="vy-chip" aria-pressed={onlyLocality} onClick={() => setOnlyLocality((v) => !v)}>
                      {onlyLocality && <Check size={14} strokeWidth={2.5} aria-hidden="true" />}
                      {t("commercial:boost.onlyLocality", { locality: audienceLocality })}
                    </button>
                  )}
                  {opts.audience.categories.map((c, i) => (
                    <button key={c} type="button" className="vy-chip" aria-pressed={onlyCategory === c} onClick={() => setOnlyCategory((v) => (v === c ? null : c))}>
                      {onlyCategory === c && <Check size={14} strokeWidth={2.5} aria-hidden="true" />}
                      {t("commercial:boost.onlyCategory", { category: opts.audience.category_labels[i] ?? c })}
                    </button>
                  ))}
                </div>
              </section>
            )}

            <section className="vy-dl-sec" aria-labelledby="boost-terms">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile" aria-hidden="true"><ShieldCheck size={20} strokeWidth={1.75} /></span>
                <h2 id="boost-terms" className="vy-card-title">{t("commercial:disclosure.termsTitle")}</h2>
                <span className="vy-dl-sec-hint">{t("commercial:disclosure.termsHint")}</span>
              </div>
              <dl className="vy-dl-terms">
                <div><dt>{t("commercial:disclosure.changes")}</dt><dd>{t("commercial:disclosure.changesText")}</dd></div>
                <div><dt>{t("commercial:disclosure.doesNot")}</dt><dd>{t("commercial:disclosure.doesNotText")}</dd></div>
                <div><dt>{t("commercial:disclosure.renewal")}</dt><dd>{t("commercial:disclosure.renewalText")}</dd></div>
                <div><dt>{t("commercial:disclosure.refund")}</dt><dd>{t("commercial:disclosure.refundText")}</dd></div>
                <div><dt>{t("commercial:disclosure.receipt")}</dt><dd>{t("commercial:disclosure.receiptText")}</dd></div>
              </dl>
            </section>
          </div>

          <div className="vy-split-aside">
            <section className="vy-dl-sec" aria-labelledby="boost-summary">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Receipt size={20} strokeWidth={1.75} /></span>
                <h2 id="boost-summary" className="vy-card-title">{t("commercial:disclosure.title")}</h2>
                <span className="vy-dl-sec-hint">{product ? productName : t("commercial:disclosure.summaryEmpty")}</span>
              </div>
              {product && (
                <dl className="vy-dl-receipt">
                  <dt>{t("commercial:disclosure.price")}</dt>
                  <dd>{money(product.price_paise)}</dd>
                  <dt>{t("commercial:disclosure.tax")}</dt>
                  <dd>{money(product.tax_paise)}</dd>
                  {credit > 0 && (
                    <>
                      <dt>{t("commercial:disclosure.credit")}</dt>
                      <dd>− {money(credit)}</dd>
                    </>
                  )}
                  <dt className="vy-dl-receipt-total">{t("commercial:disclosure.total")}</dt>
                  <dd className="vy-dl-receipt-total"><strong>{money(due)}</strong></dd>
                  <dt>{t("commercial:disclosure.starts")}</dt>
                  <dd>{t("commercial:disclosure.startsOnPayment")}</dd>
                  <dt>{t("commercial:disclosure.ends")}</dt>
                  <dd>{endsOn}</dd>
                </dl>
              )}
              {notice && (
                <p className={busy ? "vy-dl-hint" : "vy-error"} role={busy ? "status" : "alert"}>{notice}</p>
              )}
              <button className="vy-btn vy-btn-primary" aria-describedby={!product ? "boost-why" : undefined} disabled={!product || busy} onClick={confirm}>
                {product ? (due > 0 ? t("commercial:disclosure.confirmPay", { amount: money(due) }) : t("commercial:disclosure.confirmCredit")) : t("commercial:disclosure.confirmPayPlain")}
              </button>
              <DisabledReason id="boost-why" show={!product && !busy}>{t("commercial:boost.chooseDuration")}</DisabledReason>
              <button className="vy-btn vy-btn-ghost" onClick={() => router.back()}>{t("common:action.cancel")}</button>
            </section>
          </div>
        </div>
      </div>
    </Screen>
  );
}
