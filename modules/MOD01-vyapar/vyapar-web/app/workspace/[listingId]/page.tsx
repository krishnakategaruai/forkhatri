"use client";

// [TR033/TR034] Business Workspace on one screen (FR33, FR34, UX21): the plan
// with its full disclosure, the team, and the campaigns — no separate plan,
// team and billing screens to walk through.
// - The plan section is the FR54 disclosure: price with tax, renewal date,
//   what is included, an explicit "never included" line, and the
//   cancellation terms — then one Confirm button that names the amount.
// - Renewal is honest: cancelling stops it at period end and can be turned
//   back on; a Paused plan says why, keeps all data, and offers to complete
//   the payment.
// - Team: invite by phone with a role, pending invites shown with their
//   expiry, role change and revoke in place. What each role may do is stated.
// - Campaigns: create inline (name, package, up to 10 items) and open any
//   campaign's own screen.
// The API decides every permission; this screen only renders what the
// Authorization Engine reported in `capabilities`.
// [Design language 2026-09-29] A page head, a facts strip, then section
// cards (plan · team · campaigns) each with an icon tile and a one-line
// hint; pricing as radio cards with a check; one filled button per screen.
// Traces to: FR33, FR34, FR35, FR54, TR033, TR034, UX21
import { useCallback, useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { useRouter } from "next/navigation";
import { AlertTriangle, BadgeCheck, Check, ChevronRight, Layers, Plus, ShieldCheck, Users } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import DisabledReason from "@/app/components/DisabledReason";
import { formatDate } from "@/lib/format";
import { promotionTone } from "@/app/promotions/tone";
import "@/app/styles/deals-2026.css";

interface Plan {
  id: string;
  version: number;
  billing: string;
  duration_days: number | null;
  price_paise: number;
  tax_paise: number;
  total_paise: number;
  capabilities: string[];
}

interface Member {
  id: string;
  member_id: string | null;
  display_name: string | null;
  phone_masked: string;
  role: string;
  state: string;
  invited_at: string;
  expires_at: string | null;
}

interface CampaignRow {
  id: string;
  name: string;
  state: string;
  starts_at: string | null;
  ends_at: string | null;
}

interface Workspace {
  listing_id: string;
  listing_name: string | null;
  role: string;
  is_owner: boolean;
  entitlement: {
    id: string;
    state: string;
    active: boolean;
    renews_at: string | null;
    grace_until: string | null;
    cancel_at_period_end: boolean;
    product_id: string | null;
    product_version: number | null;
  } | null;
  capabilities: string[];
  plans: Plan[];
  members: Member[];
  campaigns: CampaignRow[];
}

interface CampaignOptions {
  packages: { id: string; version: number; duration_days: number; price_paise: number; tax_paise: number; total_paise: number }[];
  max_items: number;
  locality: string | null;
  items: { kind: "listing" | "opportunity"; id: string; title: string }[];
}

export default function WorkspacePage({ params }: { params: Promise<{ listingId: string }> }) {
  const { listingId } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["workspace", "commercial", "common"]);
  const router = useRouter();
  const [ws, setWs] = useState<Workspace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [planId, setPlanId] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "operator">("operator");
  const [options, setOptions] = useState<CampaignOptions | null>(null);
  const [campaignName, setCampaignName] = useState("");
  const [packageId, setPackageId] = useState<string | null>(null);
  const [chosenItems, setChosenItems] = useState<string[]>([]);
  const [newCampaign, setNewCampaign] = useState(false);

  const money = (p: number) => formatPaise(p, i18n.language);
  const fmt = (d: string) => formatDate(d, i18n.language);

  const load = useCallback(async () => {
    try {
      const data = await api.get<Workspace>(`/v1/workspace/${listingId}`);
      setWs(data);
      if (data.capabilities.includes("campaigns")) {
        api.get<CampaignOptions>(`/v1/campaigns/options?listing_id=${listingId}`).then(setOptions).catch(() => setOptions(null));
      }
    } catch (e) {
      // One profile per member: an old link to a merged listing's workspace
      // answers 404 with the surviving profile id — go there instead.
      const mergedInto = e instanceof ApiError && e.code === "workspace_not_found" ? e.details?.merged_into : null;
      if (typeof mergedInto === "string" && mergedInto !== listingId) {
        router.replace(`/workspace/${mergedInto}`);
        return;
      }
      setError(e instanceof ApiError ? String(e.detail) : t("workspace:error.notFound"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  useEffect(() => {
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function buyPlan() {
    if (!planId) return;
    setBusy(true);
    setNotice(null);
    try {
      const created = await api.post<{ id: string }>("/v1/entitlements", { listing_id: listingId, product_id: planId });
      const res = await api.post<{ checkout_url: string | null; notice: string | null }>(`/v1/entitlements/${created.id}/confirm-purchase`, { confirmed: true });
      if (res.checkout_url) {
        window.location.assign(res.checkout_url);
        return;
      }
      setNotice(t("commercial:promotion.resultUnavailable"));
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function completePayment() {
    if (!ws?.entitlement) return;
    setBusy(true);
    try {
      const res = await api.post<{ checkout_url: string | null }>(`/v1/entitlements/${ws.entitlement.id}/confirm-purchase`, { confirmed: true });
      if (res.checkout_url) window.location.assign(res.checkout_url);
      else setNotice(t("commercial:promotion.resultUnavailable"));
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function createCampaign() {
    if (!packageId || chosenItems.length === 0 || campaignName.trim().length < 2 || !options) return;
    setBusy(true);
    setNotice(null);
    try {
      const items = chosenItems.map((key) => {
        const [kind, id] = key.split(":");
        return { kind, id };
      });
      const created = await api.post<{ id: string; rejected_items: string[] }>("/v1/campaigns", {
        listing_id: listingId,
        name: campaignName.trim(),
        product_id: packageId,
        items,
        days: options.packages.find((p) => p.id === packageId)?.duration_days ?? 14,
        audience_locality: undefined,
      });
      const res = await api.post<{ checkout_url: string | null }>(`/v1/campaigns/${created.id}/confirm-purchase`, { confirmed: true });
      if (res.checkout_url) {
        window.location.assign(res.checkout_url);
        return;
      }
      setNotice(t("commercial:promotion.resultUnavailable"));
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (error)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <DealsEmpty tone="neutral" icon={<AlertTriangle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("workspace:title")} body={error} />
        </div>
      </Screen>
    );
  if (!ws)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <SkeletonGrid count={3} grid={false} />
        </div>
      </Screen>
    );

  const plan = ws.plans.find((p) => p.id === planId) ?? null;
  const planFact = ws.entitlement ? (ws.entitlement.active ? t("workspace:dash.planOn") : t(`workspace:plan.state.${ws.entitlement.state}` as "plan.state.paused")) : t("workspace:dash.noPlan");
  const activeMembers = ws.members.filter((m) => m.state === "active" || m.state === "pending").length;
  const hasTeam = ws.capabilities.includes("team");
  const hasCampaigns = ws.capabilities.includes("campaigns");
  const campaignBlocker = !campaignName.trim() || campaignName.trim().length < 2 ? t("workspace:campaigns.needName") : !packageId ? t("workspace:campaigns.needPackage") : chosenItems.length === 0 ? t("workspace:campaigns.needItems") : null;

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <div className="vy-dl-head">
          <div className="vy-dl-tags">
            <span className="vy-dl-state">{t(`workspace:role.${ws.role}` as "role.owner")}</span>
            <span className="vy-dl-state" data-tone={ws.entitlement?.active ? "done" : ws.entitlement ? "warn" : undefined}>{planFact}</span>
          </div>
          <h1>{t("workspace:title")}</h1>
          <p>{ws.listing_name ? t("workspace:subtitle", { name: ws.listing_name }) : t("workspace:subtitlePlain")}</p>
        </div>
        {notice && (
          <p className="vy-dl-notice" data-tone="bad" role="alert">
            <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
            <span>{notice}</span>
          </p>
        )}

        <div className="vy-dl-metrics">
          <div className="vy-dl-metric">
            <span className="vy-dl-metric-label">{t("workspace:dash.plan")}</span>
            <span className="vy-dl-metric-value" data-empty={ws.entitlement?.active ? undefined : true}>{planFact}</span>
            {ws.entitlement?.active && ws.entitlement.renews_at && <span className="vy-dl-metric-sub">{t("workspace:plan.renewsOn", { date: fmt(ws.entitlement.renews_at) })}</span>}
          </div>
          <div className="vy-dl-metric">
            <span className="vy-dl-metric-label">{t("workspace:dash.team")}</span>
            <span className="vy-dl-metric-value" data-empty={hasTeam ? undefined : true}>{hasTeam ? activeMembers : t("workspace:dash.withPlan")}</span>
          </div>
          <div className="vy-dl-metric">
            <span className="vy-dl-metric-label">{t("workspace:dash.campaigns")}</span>
            <span className="vy-dl-metric-value" data-empty={hasCampaigns ? undefined : true}>{hasCampaigns ? ws.campaigns.length : t("workspace:dash.withPlan")}</span>
          </div>
        </div>

        {/* [FR33] plan state, or the disclosure + purchase when there is none */}
        {ws.entitlement?.active && (
          <section className="vy-dl-sec" aria-labelledby="ws-plan">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><BadgeCheck size={20} strokeWidth={1.75} /></span>
              <h2 id="ws-plan" className="vy-card-title">{t("workspace:plan.active")}</h2>
              <span className="vy-dl-sec-hint">{ws.entitlement.renews_at ? t("workspace:plan.renewsOn", { date: fmt(ws.entitlement.renews_at) }) : ""}</span>
            </div>
            {ws.entitlement.grace_until && (
              <p className="vy-dl-notice" data-tone="warn">
                <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
                <span>{t("workspace:plan.graceBanner", { date: fmt(ws.entitlement.grace_until) })}</span>
              </p>
            )}
            <p className="vy-dl-fine">{t("workspace:plan.neverIncluded")}</p>
            {ws.capabilities.includes("billing") &&
              (ws.entitlement.cancel_at_period_end ? (
                <div className="vy-dl-page" style={{ gap: 6 }}>
                  <p className="vy-dl-hint">{t("workspace:plan.cancelScheduled", { date: ws.entitlement.renews_at ? fmt(ws.entitlement.renews_at) : "" })}</p>
                  <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => act(() => api.post(`/v1/entitlements/${ws.entitlement!.id}/renewal`, { cancel_at_period_end: false }))}>
                    {t("workspace:plan.resumeRenewal")}
                  </button>
                </div>
              ) : (
                <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => act(() => api.post(`/v1/entitlements/${ws.entitlement!.id}/renewal`, { cancel_at_period_end: true }))}>
                  {t("workspace:plan.cancelRenewal")}
                </button>
              ))}
          </section>
        )}

        {ws.entitlement && !ws.entitlement.active && (
          <section className="vy-dl-sec" aria-labelledby="ws-paused">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-amber" aria-hidden="true"><AlertTriangle size={20} strokeWidth={1.75} /></span>
              <h2 id="ws-paused" className="vy-card-title">{t(`workspace:plan.state.${ws.entitlement.state}` as "plan.state.paused")}</h2>
              <span className="vy-dl-sec-hint">{t("workspace:plan.pausedHelp")}</span>
            </div>
            {ws.capabilities.includes("billing") && ws.is_owner && (
              <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={completePayment}>
                {t("workspace:plan.completePayment")}
              </button>
            )}
          </section>
        )}

        {!ws.entitlement && ws.is_owner && (
          <section className="vy-dl-sec" aria-labelledby="ws-choose">
            <div className="vy-dl-sec-head">
              <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><ShieldCheck size={20} strokeWidth={1.75} /></span>
              <h2 id="ws-choose" className="vy-card-title">{t("workspace:plan.chooseTitle")}</h2>
              <span className="vy-dl-sec-hint">{t("workspace:plan.chooseHint")}</span>
            </div>
            <div className="vy-detail" style={{ gap: "var(--space-4)" }}>
              <div className="vy-detail-main">
                <div className="vy-dl-price-grid" role="radiogroup" aria-labelledby="ws-choose">
                  {ws.plans.map((p) => (
                    <button key={p.id} type="button" role="radio" aria-checked={planId === p.id} className="vy-dl-price" onClick={() => setPlanId(p.id)}>
                      <span className="vy-dl-price-check" aria-hidden="true"><Check size={14} strokeWidth={3} /></span>
                      <span className="vy-dl-price-name">{t(`workspace:plan.billing.${p.billing}` as "plan.billing.monthly")}</span>
                      <span className="vy-dl-price-amt">{money(p.total_paise)}</span>
                      <span className="vy-dl-price-sub">{t("commercial:boost.inclTaxShort")}</span>
                    </button>
                  ))}
                </div>
                <dl className="vy-dl-terms">
                  <div><dt>{t("workspace:plan.included")}</dt><dd>{t("workspace:plan.includedText")}</dd></div>
                  <div><dt>{t("workspace:plan.notIncluded")}</dt><dd>{t("workspace:plan.neverIncluded")}</dd></div>
                  {plan && <div><dt>{t("commercial:disclosure.renewal")}</dt><dd>{t("workspace:plan.renewalTerms", { days: plan.duration_days ?? 30 })}</dd></div>}
                  {plan && <div><dt>{t("commercial:disclosure.refund")}</dt><dd>{t("workspace:plan.cancelTerms")}</dd></div>}
                </dl>
              </div>
              <div className="vy-detail-aside">
                <div className="vy-dl-panel">
                  <span className="vy-label">{t("commercial:disclosure.title")}</span>
                  {plan ? (
                    <dl className="vy-dl-receipt">
                      <dt>{t("commercial:disclosure.price")}</dt>
                      <dd>{money(plan.price_paise)}</dd>
                      <dt>{t("commercial:disclosure.tax")}</dt>
                      <dd>{money(plan.tax_paise)}</dd>
                      <dt className="vy-dl-receipt-total">{t("commercial:disclosure.total")}</dt>
                      <dd className="vy-dl-receipt-total"><strong>{money(plan.total_paise)}</strong></dd>
                    </dl>
                  ) : (
                    <p className="vy-dl-hint">{t("workspace:plan.choosePrompt")}</p>
                  )}
                  <button className="vy-btn vy-btn-primary" aria-describedby={!plan ? "ws-plan-why" : undefined} disabled={!plan || busy} onClick={buyPlan}>
                    {plan ? t("commercial:disclosure.confirmPay", { amount: money(plan.total_paise) }) : t("commercial:disclosure.confirmPayPlain")}
                  </button>
                  <DisabledReason id="ws-plan-why" show={!plan && !busy}>{t("workspace:plan.choosePrompt")}</DisabledReason>
                </div>
              </div>
            </div>
          </section>
        )}

        <div className="vy-dl-console-2">
          {/* [FR34] team */}
          {hasTeam && (
            <section className="vy-dl-sec" aria-labelledby="ws-team">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-teal" aria-hidden="true"><Users size={20} strokeWidth={1.75} /></span>
                <h2 id="ws-team" className="vy-card-title">{t("workspace:team.title")}</h2>
                <span className="vy-dl-sec-hint">{t("workspace:team.roleHelp")}</span>
              </div>
              {ws.members.length === 0 && <p className="vy-dl-hint">{t("workspace:team.empty")}</p>}
              <div>
                {ws.members.map((m) => {
                  const name = m.display_name ?? m.phone_masked;
                  return (
                    <div key={m.id} className="vy-dl-person">
                      <span className="vy-dl-avatar" aria-hidden="true">{(name.trim().charAt(0) || "?").toUpperCase()}</span>
                      <span className="vy-dl-row-body">
                        <span className="vy-dl-row-title">{name}</span>
                        <span className="vy-dl-row-meta">
                          <span>
                            {t(`workspace:role.${m.role}` as "role.admin")} · {t(`workspace:team.state.${m.state}` as "team.state.active")}
                            {m.state === "pending" && m.expires_at ? ` · ${t("workspace:team.expires", { date: fmt(m.expires_at) })}` : ""}
                          </span>
                        </span>
                      </span>
                      {["pending", "active"].includes(m.state) && (
                        <span className="vy-dl-actions vy-dl-actions-end">
                          {m.state === "active" && (
                            <button className="vy-btn vy-btn-ghost vy-dl-btn-sm" disabled={busy} onClick={() => act(() => api.post(`/v1/workspace/members/${m.id}/role`, { state: "active", role: m.role === "admin" ? "operator" : "admin" }))}>
                              {t("workspace:team.switchTo", { role: t(`workspace:role.${m.role === "admin" ? "operator" : "admin"}` as "role.admin") })}
                            </button>
                          )}
                          <button className="vy-btn vy-btn-ghost vy-dl-btn-sm" disabled={busy} onClick={() => act(() => api.post(`/v1/workspace/members/${m.id}/role`, { state: "revoked" }))}>
                            {t("workspace:team.revoke")}
                          </button>
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="vy-dl-panel">
                <span className="vy-label">{t("workspace:team.inviteTitle")}</span>
                <label className="vy-field">
                  <span className="vy-label">{t("workspace:team.invitePhone")}</span>
                  <input className="vy-input" inputMode="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t("workspace:team.phonePlaceholder")} />
                </label>
                <div className="vy-dl-choice-row" role="radiogroup" aria-label={t("workspace:team.roleLabel")}>
                  {(["admin", "operator"] as const).map((r) => (
                    <button key={r} type="button" role="radio" aria-checked={inviteRole === r} className="vy-dl-choice" onClick={() => setInviteRole(r)}>
                      {t(`workspace:role.${r}` as "role.admin")}
                    </button>
                  ))}
                </div>
                <button
                  className="vy-btn vy-btn-secondary"
                  style={{ alignSelf: "flex-start" }}
                  disabled={busy || phone.trim().length < 8}
                  onClick={() =>
                    act(async () => {
                      await api.post(`/v1/workspace/${listingId}/invite`, { phone: phone.trim(), role: inviteRole });
                      setPhone("");
                    })
                  }
                >
                  {t("workspace:team.sendInvite")}
                </button>
                <p className="vy-dl-fine">{t("workspace:team.inviteHelp")}</p>
              </div>
            </section>
          )}

          {/* [FR35] campaigns */}
          {hasCampaigns && (
            <section className="vy-dl-sec" aria-labelledby="ws-campaigns">
              <div className="vy-dl-sec-head">
                <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Layers size={20} strokeWidth={1.75} /></span>
                <h2 id="ws-campaigns" className="vy-card-title">{t("workspace:campaigns.title")}</h2>
                <span className="vy-dl-sec-hint">{t("workspace:campaigns.hint")}</span>
              </div>
              {ws.campaigns.length === 0 && <p className="vy-dl-hint">{t("workspace:campaigns.empty")}</p>}
              {ws.campaigns.length > 0 && (
                <div className="vy-dl-list">
                  {ws.campaigns.map((c) => (
                    <a key={c.id} className="vy-dl-row" href={`/campaigns/${c.id}`} style={{ boxShadow: "none" }}>
                      <span className="vy-dl-row-body" style={{ gridColumn: "1 / span 2" }}>
                        <span className="vy-dl-row-title">{c.name}</span>
                        <span className="vy-dl-row-meta">
                          <span>{c.ends_at ? t("commercial:list.endsOn", { date: fmt(c.ends_at) }) : ""}</span>
                        </span>
                        <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                          <span className="vy-dl-state" data-tone={promotionTone(c.state)}>{t(`commercial:state.${c.state}` as "state.active")}</span>
                        </span>
                      </span>
                      <span className="vy-dl-row-aside">
                        <ChevronRight size={18} strokeWidth={2} aria-hidden="true" style={{ color: "var(--text-tertiary)" }} />
                      </span>
                    </a>
                  ))}
                </div>
              )}
              {options && options.items.length > 0 && !newCampaign && (
                <button type="button" className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => setNewCampaign(true)}>
                  <Plus size={16} strokeWidth={2} aria-hidden="true" /> {t("workspace:campaigns.newTitle")}
                </button>
              )}
              {options && options.items.length > 0 && newCampaign && (
                <div className="vy-dl-panel">
                  <span className="vy-label">{t("workspace:campaigns.newTitle")}</span>
                  <label className="vy-field">
                    <span className="vy-label">{t("workspace:campaigns.name")}</span>
                    <input className="vy-input" value={campaignName} maxLength={120} onChange={(e) => setCampaignName(e.target.value)} />
                  </label>
                  <div className="vy-field">
                    <span className="vy-label">{t("workspace:campaigns.package")}</span>
                    <div className="vy-dl-price-grid" role="radiogroup" aria-label={t("workspace:campaigns.package")}>
                      {options.packages.map((p) => (
                        <button key={p.id} type="button" role="radio" aria-checked={packageId === p.id} className="vy-dl-price" onClick={() => setPackageId(p.id)}>
                          <span className="vy-dl-price-check" aria-hidden="true"><Check size={14} strokeWidth={3} /></span>
                          <span className="vy-dl-price-name">{t("commercial:boost.days", { n: p.duration_days })}</span>
                          <span className="vy-dl-price-amt">{money(p.total_paise)}</span>
                          <span className="vy-dl-price-sub">{t("commercial:boost.inclTaxShort")}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="vy-field">
                    <span className="vy-label">{t("workspace:campaigns.items", { n: chosenItems.length, max: options.max_items })}</span>
                    <div className="vy-dl-tags">
                      {options.items.map((item) => {
                        const key = `${item.kind}:${item.id}`;
                        const checked = chosenItems.includes(key);
                        return (
                          <button
                            key={key}
                            type="button"
                            className="vy-chip"
                            aria-pressed={checked}
                            disabled={!checked && chosenItems.length >= options.max_items}
                            onClick={() => setChosenItems((c) => (checked ? c.filter((x) => x !== key) : [...c, key]))}
                          >
                            {checked && <Check size={14} strokeWidth={2.5} aria-hidden="true" />}
                            {item.title}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  <p className="vy-dl-fine">{t("workspace:campaigns.disclosure")}</p>
                  <div className="vy-dl-actions">
                    <button className="vy-btn vy-btn-primary" aria-describedby={campaignBlocker ? "ws-camp-why" : undefined} disabled={busy || !!campaignBlocker} onClick={createCampaign}>
                      {t("workspace:campaigns.createAndPay")}
                    </button>
                    <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => setNewCampaign(false)}>{t("common:action.cancel")}</button>
                  </div>
                  <DisabledReason id="ws-camp-why" show={!!campaignBlocker && !busy}>{campaignBlocker}</DisabledReason>
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </Screen>
  );
}
