"use client";

// [TR055] Opportunity detail, member actions (FR55). Combines: title/type/
// status, description, poster trust context (kept minimal — FR28
// reputation isn't built, slice 7), "Why this?" entry, a primary action
// adapted to type (server-computed label, never a second front-end
// mapping — reuses the exact `type_action_label` the API already sends),
// and secondary actions Save/Share/Not interested/Report. For a Draft the
// poster sees confirm-fields + Publish instead of the viewer actions.
// [Product-owner i18n rule] Converted to useTranslation(); `type_action_
// label`/`signals`/`gap` from the API are i18n KEYS (opportunities.py's/
// feed.py's own i18n conversion), translated here via opportunities.json/
// ranking.json — never rendered as raw key text.
// Traces to: FR55, FR12 (confirm), FR13 (lifecycle), TR055
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";
import ReportSheet from "@/app/components/ReportSheet";
import SponsoredBadge from "@/app/components/SponsoredBadge";
import PerformanceReport from "@/app/components/PerformanceReport";

interface Opportunity {
  sponsored: boolean;
  id: string;
  is_poster: boolean;
  poster_id: string;
  title: string;
  type: string;
  type_action_label: string;
  description: string | null;
  compensation: string | null;
  location: string | null;
  work_mode: string | null;
  source_segment: string;
  source_url: string | null;
  response_method: string | null;
  unconfirmed_fields: string[];
  confirmed_fields: string[];
  state: string;
  saved: boolean;
}

interface WhyResponse {
  signals: string[];
  gap: string | null;
  gap_skills: string | null;
  sponsored_note: string | null;
}

const NOT_INTERESTED_REASON_KEYS: Record<string, string> = {
  too_far: "notInterestedTooFar",
  wrong_type: "notInterestedWrongType",
  not_my_capability: "notInterestedNotMyCapability",
  value_too_low: "notInterestedValueTooLow",
  wrong_timing: "notInterestedWrongTiming",
  already_found: "notInterestedAlreadyFound",
  not_interested: "notInterestedGeneric",
};

export default function OpportunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t } = useTranslation(["opportunities", "common", "ranking", "commercial"]);
  const [opp, setOpp] = useState<Opportunity | null>(null);
  const [why, setWhy] = useState<WhyResponse | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hidden, setHidden] = useState(false);

  async function refresh() {
    try {
      setOpp(await api.get<Opportunity>(`/v1/opportunities/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.notFound"));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  function signalLabel(key: string): string {
    if (["capability_fit", "intent_fit", "location_fit", "timing_fit", "value_fit", "experience_fit", "freshness_fit", "trust_fit"].includes(key)) {
      return t(`ranking:signal.${key}` as "signal.capability_fit");
    }
    return t(`ranking:fallback.${key}` as "fallback.matchedSearch");
  }

  if (error) return <main className="vy-shell"><h1>{t("common:state.notFound")}</h1><p>{error}</p></main>;
  if (!opp) return <main className="vy-shell"><p>{t("common:state.loading")}</p></main>;
  if (hidden) return <main className="vy-shell"><p className="vy-muted">{t("opportunities:detail.hiddenFromFeed")}</p></main>;

  return (
    <main className="vy-shell">
      <h1>{opp.title}</h1>
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        <span className="vy-badge vy-badge-member-provided">{opp.state === "active" ? t("opportunities:detail.stateActive") : opp.state}</span>
        <span className="vy-badge vy-badge-member-provided">{opp.source_segment === "community" ? t("opportunities:detail.segmentCommunity") : t("opportunities:detail.segmentPublic")}</span>
        {opp.sponsored && <SponsoredBadge />}
      </div>

      <div className="vy-card">
        {opp.description && <p>{opp.description}</p>}
        <p className="vy-muted" style={{ marginTop: 8 }}>
          {/* [Bug fix] work_mode is a raw enum column (on_site/remote/both) — never
              render it directly; the same class of bug as the taxonomy-slug leak. */}
          {[opp.location, opp.work_mode ? t(`opportunities:workMode.${opp.work_mode}` as "workMode.on_site") : null, opp.compensation].filter(Boolean).join(" · ") || t("opportunities:detail.noDetailsYet")}
        </p>
      </div>

      {notice && <p className="vy-error">{notice}</p>}

      {opp.is_poster && opp.state === "draft" && (
        <div className="vy-card vy-stack">
          <h2 style={{ fontSize: 16 }}>{t("opportunities:detail.confirmTitle")}</h2>
          {opp.unconfirmed_fields.length === 0 ? (
            <p className="vy-muted">{t("opportunities:detail.allConfirmed")}</p>
          ) : (
            opp.unconfirmed_fields.map((f) => (
              <div key={f} className="vy-row" style={{ justifyContent: "space-between" }}>
                <span>
                  <span className="vy-badge vy-badge-member-provided">{t("opportunities:detail.unconfirmed")}</span> {f}
                </span>
                <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act(() => api.patch(`/v1/opportunities/${id}/confirm`, { fields: [f] }))}>
                  {t("opportunities:detail.confirm")}
                </button>
              </div>
            ))
          )}
          <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/opportunities/${id}/publish`))}>
            {t("opportunities:detail.publish")}
          </button>
        </div>
      )}

      {opp.is_poster && opp.state !== "draft" && (
        <div className="vy-row" style={{ flexWrap: "wrap" }}>
          {(opp.state === "active" || opp.state === "stale") && (
            <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act(() => api.post(`/v1/opportunities/${id}/pause`))}>
              {t("opportunities:detail.pause")}
            </button>
          )}
          {opp.state === "paused" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/opportunities/${id}/resume`))}>
              {t("opportunities:detail.resume")}
            </button>
          )}
          {opp.state === "expired" && (
            <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act(() => api.post(`/v1/opportunities/${id}/renew`))}>
              {t("opportunities:detail.renew")}
            </button>
          )}
          {["active", "paused", "stale"].includes(opp.state) && (
            <button className="vy-btn vy-btn-ghost" disabled={busy} onClick={() => act(() => api.post(`/v1/opportunities/${id}/close`))}>
              {t("opportunities:detail.close")}
            </button>
          )}
          {/* [FR30] Boost — eligibility (verified poster listing) is explained on the boost screen */}
          {opp.state === "active" && (
            <a className="vy-btn vy-btn-secondary" href={`/boost/opportunity/${id}`} style={{ textDecoration: "none" }}>
              {t("commercial:action.boost")}
            </a>
          )}
        </div>
      )}
      {opp.is_poster && opp.state !== "draft" && <PerformanceReport targetKind="opportunity" targetId={id} />}

      {!opp.is_poster && opp.state === "active" && (
        <>
          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {opp.source_segment === "public" && opp.source_url ? (
              <a className="vy-btn vy-btn-primary" href={opp.source_url} target="_blank" rel="noopener noreferrer" onClick={() => api.post(`/v1/opportunities/${id}/external-open`).catch(() => {})}>
                {/* [FR55 fix] Employment public/external items must read "Apply on source
                    website" (the Naukri "Apply on Company Website" pattern), not the generic
                    "Open official website" used by every other public/external type. */}
                {t(opp.type === "employment" ? "opportunities:actionLabel.applyOnSource" : "opportunities:detail.openOfficialWebsite")}
              </a>
            ) : (
              <a className="vy-btn vy-btn-primary" href={`/enquiries/new?opportunity_id=${id}`} style={{ textDecoration: "none", display: "inline-block" }}>
                {t(`opportunities:actionLabel.${opp.type_action_label}` as "actionLabel.apply")}
              </a>
            )}
            <button
              className="vy-btn vy-btn-secondary"
              disabled={busy}
              onClick={() => act(() => (opp.saved ? api.delete(`/v1/opportunities/${id}/save`) : api.post(`/v1/opportunities/${id}/save`)))}
            >
              {opp.saved ? `★ ${t("common:action.saved")}` : `☆ ${t("common:action.save")}`}
            </button>
            <button className="vy-btn vy-btn-ghost" onClick={() => {
                setShowWhy((v) => !v);
                if (!why) api.get<WhyResponse>(`/v1/opportunities/${id}/why`).then(setWhy);
              }}>
              {t("opportunities:detail.whyThis")}
            </button>
          </div>

          {showWhy && why && (
            <div className="vy-card">
              {/* [TR020/FR30] paid reach is disclosed, never presented as relevance */}
              {why.sponsored_note && <p className="vy-muted" style={{ marginBottom: 6 }}>{t("commercial:why.sponsored")}</p>}
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {why.signals.map((s) => <li key={s}>{signalLabel(s)}</li>)}
              </ul>
              {why.gap && (
                <p className="vy-muted" style={{ marginTop: 6 }}>
                  {t(`ranking:gap.${why.gap}` as "gap.missingSkills", { skills: why.gap_skills })}
                </p>
              )}
            </div>
          )}

          <div className="vy-row" style={{ flexWrap: "wrap" }}>
            {Object.entries(NOT_INTERESTED_REASON_KEYS).map(([id_, key]) => (
              <button
                key={id_}
                className="vy-chip"
                style={{ border: "none", cursor: "pointer" }}
                onClick={() =>
                  act(async () => {
                    await api.post(`/v1/opportunities/${id}/not-interested`, { reason: id_ });
                    setHidden(true);
                  })
                }
              >
                {t(`opportunities:detail.${key}` as "detail.notInterestedTooFar")}
              </button>
            ))}
          </div>
          {/* [FR39/FR55] Report in place, deferred in IMP14 until moderation existed. */}
          <ReportSheet objectKind="opportunity" objectId={id} blockMemberId={opp.poster_id} />
        </>
      )}
    </main>
  );
}
