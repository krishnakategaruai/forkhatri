"use client";

// [TR028] Contextual reputation display (FR28) and [TR029] the subject's
// one action on a review — Dispute (FR29).
// ReputationLine: counts and top tags only, never a score or stars; below 3
// interactions it reads "New on Vyapar" with no negative styling; "Responds
// in ~X" from FR23; disputed reviews appear only as "N under review".
// ReviewList: "Recommends · Priya · verified interaction · date · tags ·
// comment" rows (UX16). The review's subject gets "Dispute this review",
// which opens reason chips in place on that row — no modal, one tap to send.
// There is deliberately no edit/hide control for the subject anywhere
// (SP029 StructAbsence).
// Traces to: FR28, FR29, TR028, TR029, UX16, UX07
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

export interface Reputation {
  interactions: number;
  recommends: number;
  top_tags: string[];
  under_review: number;
  response_minutes: number | null;
  new_on_vyapar: boolean;
}

interface ReviewRow {
  id: string;
  recommend: boolean;
  tags: string[];
  comment: string | null;
  created_at: string;
  state: string;
  author_first_name: string | null;
  is_subject: boolean;
  is_author: boolean;
  disputed: boolean;
}

const DISPUTE_REASONS = ["retaliation", "manipulation", "not_the_interaction", "abusive"] as const;

export function useReputationText() {
  const { t } = useTranslation(["reviews"]);
  return (rep: Reputation | null | undefined): string => {
    if (!rep) return "";
    const parts: string[] = [];
    if (rep.new_on_vyapar) {
      parts.push(t("reviews:newOnVyapar"));
    } else {
      parts.push(t("reviews:counts", { n: rep.interactions, m: rep.recommends }));
      if (rep.top_tags.length > 0) {
        parts.push(rep.top_tags.map((tag) => t(`reviews:tag.${tag}` as "tag.on_time", { defaultValue: tag })).join(", "));
      }
    }
    if (rep.response_minutes != null) {
      const m = rep.response_minutes;
      // [Grammar bug fix] "Responds in ~1 days" — English (and Hindi/Telugu
      // day-count wording) needs the singular form at n=1; picking the key
      // explicitly here avoids relying on i18next's plural-suffix machinery
      // that this catalog was never wired for.
      const days = Math.round(m / 1440);
      const time =
        m < 60
          ? t("reviews:minutes", { n: Math.max(1, m) })
          : m < 1440
            ? t("reviews:hours", { n: Math.round(m / 60) })
            : days === 1
              ? t("reviews:oneDay")
              : t("reviews:days", { n: days });
      parts.push(t("reviews:respondsIn", { time }));
    }
    if (rep.under_review > 0) parts.push(t("reviews:underReview", { count: rep.under_review }));
    return parts.join(" · ");
  };
}

export function ReputationLine({ rep }: { rep: Reputation | null | undefined }) {
  const text = useReputationText()(rep);
  if (!text) return null;
  return <p className="vy-muted" style={{ marginTop: 6 }}>{text}</p>;
}

export function ReviewList({ listingId }: { listingId: string }) {
  const { t, i18n } = useTranslation(["reviews", "common"]);
  const [rows, setRows] = useState<ReviewRow[] | null>(null);
  const [disputing, setDisputing] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    setRows(await api.get<ReviewRow[]>(`/v1/listings/${listingId}/reviews`));
  }

  useEffect(() => {
    load().catch(() => setRows([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  async function sendDispute(reviewId: string) {
    if (!reason) return;
    setBusy(true);
    setNotice(null);
    try {
      await api.post(`/v1/reviews/${reviewId}/dispute`, { reason });
      setDisputing(null);
      setReason(null);
      setNotice(t("reviews:disputed"));
      await load();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  if (rows === null) return null;

  return (
    <section className="vy-stack" aria-labelledby="reviews-title">
      <h2 id="reviews-title" style={{ fontSize: 16 }}>{t("reviews:sectionTitle")}</h2>
      {rows.length === 0 && <p className="vy-muted">{t("reviews:empty")}</p>}
      {notice && <p className="vy-muted">{notice}</p>}
      {rows.map((r) => (
        <article key={r.id} className="vy-card vy-stack" style={{ gap: 6 }}>
          <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
            <strong>{r.recommend ? t("reviews:recommends") : t("reviews:doesNotRecommend")}</strong>
            <span className="vy-muted">
              {[r.author_first_name, t("reviews:verifiedInteraction"), new Date(r.created_at).toLocaleDateString(i18n.language)]
                .filter(Boolean)
                .join(" · ")}
            </span>
            {r.state === "disputed" && <span className="vy-badge vy-badge-member-provided">{t("reviews:chipUnderReview")}</span>}
            {r.state === "hidden" && <span className="vy-badge vy-badge-member-provided">{t("reviews:chipHidden")}</span>}
          </div>
          {r.tags.length > 0 && (
            <p className="vy-muted" style={{ fontSize: 13 }}>
              {r.tags.map((tag) => t(`reviews:tag.${tag}` as "tag.on_time", { defaultValue: tag })).join(", ")}
            </p>
          )}
          {r.comment && <p>{r.comment}</p>}
          {r.is_subject && r.state === "published" && !r.disputed && disputing !== r.id && (
            <button className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", fontSize: 13 }} onClick={() => setDisputing(r.id)}>
              {t("reviews:dispute")}
            </button>
          )}
          {disputing === r.id && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <p className="vy-muted" style={{ fontSize: 13 }}>{t("reviews:disputeHelp")}</p>
              <div className="vy-row" role="radiogroup" aria-label={t("reviews:dispute")} style={{ flexWrap: "wrap" }}>
                {DISPUTE_REASONS.map((d) => (
                  <button
                    key={d}
                    role="radio"
                    aria-checked={reason === d}
                    className="vy-chip"
                    style={{
                      border: "none",
                      cursor: "pointer",
                      background: reason === d ? "var(--accent)" : "var(--surface-overlay)",
                      color: reason === d ? "var(--accent-ink)" : "var(--text-primary)",
                    }}
                    onClick={() => setReason(d)}
                  >
                    {t(`reviews:disputeReason.${d}` as "disputeReason.abusive")}
                  </button>
                ))}
              </div>
              <div className="vy-row">
                <button className="vy-btn vy-btn-primary" disabled={!reason || busy} onClick={() => sendDispute(r.id)}>
                  {t("reviews:disputeSubmit")}
                </button>
                <button className="vy-btn vy-btn-ghost" onClick={() => { setDisputing(null); setReason(null); }}>
                  {t("common:action.cancel")}
                </button>
              </div>
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
