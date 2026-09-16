"use client";

// [TR030/TR054] Choose a boost and confirm the full disclosure on ONE screen
// (FR30, FR54, UX20). Fewer taps than UX20's two push screens without
// weakening the rule: duration and the optional audience narrowing sit above
// a live disclosure list (product, price, GST, credit, total, dates, what
// changes, what never changes, no renewal, cancel/refund rules, receipt),
// and the only button that can start a payment names the amount and sends
// `confirmed: true` to the separate confirm-purchase call. Nothing is
// pre-selected; there are no timers. An ineligible item shows its reason and
// the single next step instead. No reach estimate is shown (UX20 DEC-001;
// pricing doc §5.2 — only when defensible).
// Traces to: FR30, FR51, FR54, TR030, TR054, UX20
import { useEffect, useState, use as useParamsPromise } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";

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
  audience: { locality: string | null; categories: string[] };
  products: Product[];
  credit_available_paise: number;
}

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

  useEffect(() => {
    api
      .get<Options>(`/v1/promotions/options?target_kind=${kind}&target_id=${id}`)
      .then(setOpts)
      .catch((e) => setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, id]);

  const money = (p: number) => formatPaise(p, i18n.language);

  if (!opts) {
    return <main className="vy-shell">{notice ? <p className="vy-error">{notice}</p> : <p className="vy-muted">{t("common:state.loading")}</p>}</main>;
  }

  if (!opts.eligible) {
    const reason = opts.reason ?? "notFound";
    return (
      <main className="vy-shell">
        <h1>{t("commercial:boost.title", { name: opts.target_title })}</h1>
        <div className="vy-card vy-stack">
          <p>{t(`commercial:ineligible.${reason}` as "ineligible.notActive")}</p>
          {reason === "verifyFirst" && (
            <a className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={kind === "listing" ? `/listings/${id}` : "/listings/mine"}>
              {t("commercial:ineligible.getVerified")}
            </a>
          )}
        </div>
      </main>
    );
  }

  const product = opts.products.find((p) => p.id === productId) ?? null;
  const credit = product ? Math.min(opts.credit_available_paise, product.total_paise) : 0;
  const due = product ? product.total_paise - credit : 0;
  const endsOn = product ? new Date(Date.now() + product.duration_days * 86400000).toLocaleDateString(i18n.language) : "";
  const audienceLocality = opts.audience.locality;

  async function confirm() {
    if (!product) return;
    setBusy(true);
    setNotice(null);
    try {
      const draft = await api.post<{ id: string }>("/v1/promotions", {
        target_kind: kind,
        target_id: id,
        product_id: product.id,
        audience_locality: onlyLocality && audienceLocality ? audienceLocality : undefined,
        audience_category: onlyCategory ?? undefined,
      });
      const res = await api.post<{ state: string; checkout_url: string | null; notice: string | null }>(
        `/v1/promotions/${draft.id}/confirm-purchase`,
        { confirmed: true },
      );
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

  const chipStyle = (active: boolean) => ({
    border: "none",
    cursor: "pointer",
    background: active ? "var(--accent)" : "var(--surface-overlay)",
    color: active ? "var(--accent-ink)" : "var(--text-primary)",
  });

  const disclosureRows: [string, string][] = product
    ? [
        [t("commercial:disclosure.product"), t(`commercial:product.${product.id}` as "product.boost_7d", { defaultValue: product.id })],
        [t("commercial:disclosure.price"), money(product.price_paise)],
        [t("commercial:disclosure.tax"), money(product.tax_paise)],
        ...(credit > 0 ? ([[t("commercial:disclosure.credit"), `− ${money(credit)}`]] as [string, string][]) : []),
        [t("commercial:disclosure.total"), money(due)],
        [t("commercial:disclosure.starts"), t("commercial:disclosure.startsOnPayment")],
        [t("commercial:disclosure.ends"), endsOn],
        [t("commercial:disclosure.changes"), t("commercial:disclosure.changesText")],
        [t("commercial:disclosure.doesNot"), t("commercial:disclosure.doesNotText")],
        [t("commercial:disclosure.renewal"), t("commercial:disclosure.renewalText")],
        [t("commercial:disclosure.refund"), t("commercial:disclosure.refundText")],
        [t("commercial:disclosure.receipt"), t("commercial:disclosure.receiptText")],
      ]
    : [];

  return (
    <main className="vy-shell">
      <h1>{t("commercial:boost.title", { name: opts.target_title })}</h1>

      <section className="vy-stack">
        <h2 id="boost-duration" style={{ fontSize: 16 }}>{t("commercial:boost.duration")}</h2>
        <div className="vy-stack" role="radiogroup" aria-labelledby="boost-duration" style={{ gap: 8 }}>
          {opts.products.map((p) => (
            <button
              key={p.id}
              role="radio"
              aria-checked={productId === p.id}
              className="vy-card vy-row"
              style={{ justifyContent: "space-between", cursor: "pointer", borderColor: productId === p.id ? "var(--accent)" : undefined, color: "inherit" }}
              onClick={() => setProductId(p.id)}
            >
              <strong>{productId === p.id ? "● " : "○ "}{t("commercial:boost.days", { n: p.duration_days })}</strong>
              <span className="vy-muted">{t("commercial:boost.inclTax", { amount: money(p.total_paise) })}</span>
            </button>
          ))}
        </div>
      </section>

      {(audienceLocality || opts.audience.categories.length > 0) && (
        <section className="vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("commercial:boost.audience")}</h2>
          <p className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:boost.audienceHelp")}</p>
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {audienceLocality && (
              <button className="vy-chip" aria-pressed={onlyLocality} style={chipStyle(onlyLocality)} onClick={() => setOnlyLocality((v) => !v)}>
                {t("commercial:boost.onlyLocality", { locality: audienceLocality })}
              </button>
            )}
            {opts.audience.categories.map((c) => (
              <button key={c} className="vy-chip" aria-pressed={onlyCategory === c} style={chipStyle(onlyCategory === c)} onClick={() => setOnlyCategory((v) => (v === c ? null : c))}>
                {t("commercial:boost.onlyCategory", { category: c.replace(/_/g, " ") })}
              </button>
            ))}
          </div>
        </section>
      )}

      {!product ? (
        <p className="vy-muted">{t("commercial:boost.chooseDuration")}</p>
      ) : (
        <section className="vy-card vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("commercial:disclosure.title")}</h2>
          <dl className="vy-stack" style={{ gap: 10, margin: 0 }}>
            {disclosureRows.map(([label, value]) => (
              <div key={label}>
                <dt className="vy-label">{label}</dt>
                <dd style={{ margin: 0 }}>{value}</dd>
              </div>
            ))}
          </dl>
          {notice && <p className={busy ? "vy-muted" : "vy-error"}>{notice}</p>}
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={confirm}>
            {due > 0 ? t("commercial:disclosure.confirmPay", { amount: money(due) }) : t("commercial:disclosure.confirmCredit")}
          </button>
          <button className="vy-btn vy-btn-ghost" onClick={() => router.back()}>
            {t("common:action.cancel")}
          </button>
        </section>
      )}
    </main>
  );
}
