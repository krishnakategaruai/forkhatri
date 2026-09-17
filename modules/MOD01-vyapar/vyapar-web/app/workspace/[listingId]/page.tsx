"use client";

// [TR033/TR034] Business Workspace on one screen (FR33, FR34, UX21): the plan
// with its full disclosure, the team, and the campaigns — no separate plan,
// team and billing screens to walk through.
// - The plan section is the FR54 disclosure: price with tax, renewal date,
//   what is included, an explicit "never included" line (verification,
//   reputation, ranking, eligibility, private member data), and the
//   cancellation terms — then one Confirm button that names the amount.
// - Renewal is honest: cancelling stops it at period end and can be turned
//   back on; a Paused plan says why, keeps all data, and offers to complete
//   the payment.
// - Team: invite by phone with a role, pending invites shown with their expiry,
//   role change and revoke in place. What each role may do is stated, not
//   implied.
// - Campaigns: create inline (name, package, up to 10 items, duration) and
//   open any campaign's own screen.
// The API decides every permission; this screen only renders what the
// Authorization Engine reported in `capabilities`.
// Traces to: FR33, FR34, FR35, FR54, TR033, TR034, UX21
import { useCallback, useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import { formatPaise } from "@/lib/money";

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

  const money = (p: number) => formatPaise(p, i18n.language);
  const fmt = (d: string) => new Date(d).toLocaleDateString(i18n.language);

  const load = useCallback(async () => {
    try {
      const data = await api.get<Workspace>(`/v1/workspace/${listingId}`);
      setWs(data);
      if (data.capabilities.includes("campaigns")) {
        api.get<CampaignOptions>(`/v1/campaigns/options?listing_id=${listingId}`).then(setOptions).catch(() => setOptions(null));
      }
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("workspace:error.notFound"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  useEffect(() => {
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

  if (error) return <main className="vy-shell"><h1>{t("workspace:title")}</h1><p className="vy-error">{error}</p></main>;
  if (!ws) return <main className="vy-shell"><p className="vy-muted">{t("common:state.loading")}</p></main>;

  const plan = ws.plans.find((p) => p.id === planId) ?? null;
  const chipStyle = (active: boolean) => ({
    border: "none",
    cursor: "pointer",
    background: active ? "var(--accent)" : "var(--surface-overlay)",
    color: active ? "var(--accent-ink)" : "var(--text-primary)",
  });

  return (
    <main className="vy-shell">
      <div>
        <span className="vy-badge vy-badge-member-provided">{t(`workspace:role.${ws.role}` as "role.owner")}</span>
        <h1 style={{ marginTop: 8 }}>{t("workspace:title")}</h1>
        <p className="vy-muted">{ws.listing_name}</p>
      </div>
      {notice && <p className="vy-error">{notice}</p>}

      {/* [FR33] plan state, or the disclosure + purchase when there is none */}
      {ws.entitlement?.active && (
        <section className="vy-card vy-stack">
          <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
            <strong>{t("workspace:plan.active")}</strong>
            <span className="vy-muted">{ws.entitlement.renews_at ? t("workspace:plan.renewsOn", { date: fmt(ws.entitlement.renews_at) }) : ""}</span>
          </div>
          {ws.entitlement.grace_until && (
            <p className="vy-error">{t("workspace:plan.graceBanner", { date: fmt(ws.entitlement.grace_until) })}</p>
          )}
          <p className="vy-muted">{t("workspace:plan.neverIncluded")}</p>
          {ws.capabilities.includes("billing") && (
            <>
              {ws.entitlement.cancel_at_period_end ? (
                <div className="vy-stack" style={{ gap: 4 }}>
                  <p className="vy-muted">{t("workspace:plan.cancelScheduled", { date: ws.entitlement.renews_at ? fmt(ws.entitlement.renews_at) : "" })}</p>
                  <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy}
                          onClick={() => act(() => api.post(`/v1/entitlements/${ws.entitlement!.id}/renewal`, { cancel_at_period_end: false }))}>
                    {t("workspace:plan.resumeRenewal")}
                  </button>
                </div>
              ) : (
                <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start" }} disabled={busy}
                        onClick={() => act(() => api.post(`/v1/entitlements/${ws.entitlement!.id}/renewal`, { cancel_at_period_end: true }))}>
                  {t("workspace:plan.cancelRenewal")}
                </button>
              )}
            </>
          )}
        </section>
      )}

      {ws.entitlement && !ws.entitlement.active && (
        <section className="vy-card vy-stack">
          <strong>{t(`workspace:plan.state.${ws.entitlement.state}` as "plan.state.paused")}</strong>
          <p className="vy-muted">{t("workspace:plan.pausedHelp")}</p>
          {ws.capabilities.includes("billing") && ws.is_owner && (
            <button className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={completePayment}>
              {t("workspace:plan.completePayment")}
            </button>
          )}
        </section>
      )}

      {!ws.entitlement && ws.is_owner && (
        <section className="vy-card vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("workspace:plan.chooseTitle")}</h2>
          <div className="vy-stack" role="radiogroup" aria-label={t("workspace:plan.chooseTitle")} style={{ gap: 8 }}>
            {ws.plans.map((p) => (
              <button key={p.id} role="radio" aria-checked={planId === p.id} className="vy-card vy-row"
                      style={{ justifyContent: "space-between", cursor: "pointer", color: "inherit", borderColor: planId === p.id ? "var(--accent)" : undefined }}
                      onClick={() => setPlanId(p.id)}>
                <strong>{planId === p.id ? "● " : "○ "}{t(`workspace:plan.billing.${p.billing}` as "plan.billing.monthly")}</strong>
                <span className="vy-muted">{t("commercial:boost.inclTax", { amount: money(p.total_paise) })}</span>
              </button>
            ))}
          </div>
          {plan && (
            <dl className="vy-stack" style={{ gap: 10, margin: 0 }}>
              <div><dt className="vy-label">{t("commercial:disclosure.price")}</dt><dd style={{ margin: 0 }}>{money(plan.price_paise)}</dd></div>
              <div><dt className="vy-label">{t("commercial:disclosure.tax")}</dt><dd style={{ margin: 0 }}>{money(plan.tax_paise)}</dd></div>
              <div><dt className="vy-label">{t("commercial:disclosure.total")}</dt><dd style={{ margin: 0 }}>{money(plan.total_paise)}</dd></div>
              <div><dt className="vy-label">{t("workspace:plan.included")}</dt><dd style={{ margin: 0 }}>{t("workspace:plan.includedText")}</dd></div>
              <div><dt className="vy-label">{t("workspace:plan.notIncluded")}</dt><dd style={{ margin: 0 }}>{t("workspace:plan.neverIncluded")}</dd></div>
              <div><dt className="vy-label">{t("commercial:disclosure.renewal")}</dt><dd style={{ margin: 0 }}>{t("workspace:plan.renewalTerms", { days: plan.duration_days ?? 30 })}</dd></div>
              <div><dt className="vy-label">{t("commercial:disclosure.refund")}</dt><dd style={{ margin: 0 }}>{t("workspace:plan.cancelTerms")}</dd></div>
            </dl>
          )}
          <button className="vy-btn vy-btn-primary" disabled={!plan || busy} onClick={buyPlan}>
            {plan ? t("commercial:disclosure.confirmPay", { amount: money(plan.total_paise) }) : t("workspace:plan.choosePrompt")}
          </button>
        </section>
      )}

      {/* [FR34] team */}
      {ws.capabilities.includes("team") && (
        <section className="vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("workspace:team.title")}</h2>
          <p className="vy-muted" style={{ fontSize: 13 }}>{t("workspace:team.roleHelp")}</p>
          {ws.members.length === 0 && <p className="vy-muted">{t("workspace:team.empty")}</p>}
          {ws.members.map((m) => (
            <div key={m.id} className="vy-card vy-stack" style={{ gap: 6 }}>
              <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                <strong>{m.display_name ?? m.phone_masked}</strong>
                <span className="vy-badge vy-badge-member-provided">{t(`workspace:role.${m.role}` as "role.admin")}</span>
              </div>
              <span className="vy-muted" style={{ fontSize: 13 }}>
                {t(`workspace:team.state.${m.state}` as "team.state.active")}
                {m.state === "pending" && m.expires_at ? ` · ${t("workspace:team.expires", { date: fmt(m.expires_at) })}` : ""}
              </span>
              {["pending", "active"].includes(m.state) && (
                <div className="vy-row" style={{ flexWrap: "wrap" }}>
                  <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} disabled={busy}
                          onClick={() => act(() => api.post(`/v1/workspace/members/${m.id}/role`, { state: "revoked" }))}>
                    {t("workspace:team.revoke")}
                  </button>
                  {m.state === "active" && (
                    <button className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} disabled={busy}
                            onClick={() => act(() => api.post(`/v1/workspace/members/${m.id}/role`, { state: "active", role: m.role === "admin" ? "operator" : "admin" }))}>
                      {t("workspace:team.switchTo", { role: t(`workspace:role.${m.role === "admin" ? "operator" : "admin"}` as "role.admin") })}
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
          <div className="vy-card vy-stack">
            <label className="vy-field">
              <span className="vy-label">{t("workspace:team.invitePhone")}</span>
              <input className="vy-input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t("workspace:team.phonePlaceholder")} />
            </label>
            <div className="vy-row" role="radiogroup" aria-label={t("workspace:team.roleLabel")}>
              {(["admin", "operator"] as const).map((r) => (
                <button key={r} role="radio" aria-checked={inviteRole === r} className="vy-chip" style={chipStyle(inviteRole === r)} onClick={() => setInviteRole(r)}>
                  {t(`workspace:role.${r}` as "role.admin")}
                </button>
              ))}
            </div>
            <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy || phone.trim().length < 8}
                    onClick={() => act(async () => { await api.post(`/v1/workspace/${listingId}/invite`, { phone: phone.trim(), role: inviteRole }); setPhone(""); })}>
              {t("workspace:team.sendInvite")}
            </button>
            <p className="vy-muted" style={{ fontSize: 12 }}>{t("workspace:team.inviteHelp")}</p>
          </div>
        </section>
      )}

      {/* [FR35] campaigns */}
      {ws.capabilities.includes("campaigns") && (
        <section className="vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("workspace:campaigns.title")}</h2>
          {ws.campaigns.length === 0 && <p className="vy-muted">{t("workspace:campaigns.empty")}</p>}
          {ws.campaigns.map((c) => (
            <a key={c.id} className="vy-card" href={`/campaigns/${c.id}`} style={{ textDecoration: "none" }}>
              <div className="vy-row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                <strong>{c.name}</strong>
                <span className="vy-badge vy-badge-member-provided">{t(`commercial:state.${c.state}` as "state.active")}</span>
              </div>
              {c.ends_at && <p className="vy-muted" style={{ fontSize: 13 }}>{t("commercial:list.endsOn", { date: fmt(c.ends_at) })}</p>}
            </a>
          ))}
          {options && options.items.length > 0 && (
            <div className="vy-card vy-stack">
              <h3 style={{ fontSize: 14 }}>{t("workspace:campaigns.newTitle")}</h3>
              <label className="vy-field">
                <span className="vy-label">{t("workspace:campaigns.name")}</span>
                <input className="vy-input" value={campaignName} maxLength={120} onChange={(e) => setCampaignName(e.target.value)} />
              </label>
              <span className="vy-label">{t("workspace:campaigns.package")}</span>
              <div className="vy-row" style={{ flexWrap: "wrap" }}>
                {options.packages.map((p) => (
                  <button key={p.id} className="vy-chip" aria-pressed={packageId === p.id} style={chipStyle(packageId === p.id)} onClick={() => setPackageId(p.id)}>
                    {t("workspace:campaigns.packageOption", { days: p.duration_days, amount: money(p.total_paise) })}
                  </button>
                ))}
              </div>
              <span className="vy-label">{t("workspace:campaigns.items", { n: chosenItems.length, max: options.max_items })}</span>
              <div className="vy-stack" style={{ gap: 4 }}>
                {options.items.map((item) => {
                  const key = `${item.kind}:${item.id}`;
                  const checked = chosenItems.includes(key);
                  return (
                    <label key={key} className="vy-row" style={{ justifyContent: "space-between" }}>
                      <span>{item.title}</span>
                      <input type="checkbox" checked={checked} disabled={!checked && chosenItems.length >= options.max_items}
                             onChange={() => setChosenItems((c) => (checked ? c.filter((x) => x !== key) : [...c, key]))} />
                    </label>
                  );
                })}
              </div>
              <p className="vy-muted" style={{ fontSize: 12 }}>{t("workspace:campaigns.disclosure")}</p>
              <button className="vy-btn vy-btn-primary" disabled={busy || !packageId || chosenItems.length === 0 || campaignName.trim().length < 2} onClick={createCampaign}>
                {t("workspace:campaigns.createAndPay")}
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
