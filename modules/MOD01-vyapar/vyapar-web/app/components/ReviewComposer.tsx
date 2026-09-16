"use client";

// [TR027] Submit a Review tied to a qualifying interaction (FR27).
// Lives in place on the enquiry/partnership thread — a "Write a review"
// banner that expands into the form, never a separate screen (fewer taps).
// Shown only while the member holds an open invite (the server is the gate;
// this just mirrors it). Yes/No is one tap; up to 3 tags from the configured
// list (positive and negative); comment optional, 20-500 characters. One
// Idempotency-Key per opened form so a double tap files one review.
// Traces to: FR27, TR027, UX16
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, api, ApiError } from "@/lib/api";

interface InviteStatus {
  can_review: boolean;
  expires_at: string | null;
  already_reviewed: boolean;
  review_state: string | null;
  tags_positive: string[];
  tags_negative: string[];
}

export default function ReviewComposer({
  interactionKind,
  interactionId,
}: {
  interactionKind: "enquiry" | "partnership";
  interactionId: string;
}) {
  const { t, i18n } = useTranslation(["reviews", "common"]);
  const [status, setStatus] = useState<InviteStatus | null>(null);
  const [open, setOpen] = useState(false);
  const [recommend, setRecommend] = useState<boolean | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now())));

  useEffect(() => {
    api
      .get<InviteStatus>(`/v1/reviews/invite/${interactionKind}/${interactionId}`)
      .then(setStatus)
      .catch(() => setStatus(null));
  }, [interactionKind, interactionId]);

  if (!status) return null;
  if (submitted) return <div className="vy-card"><p>{t("reviews:composer.submitted")}</p></div>;
  if (status.already_reviewed) return <p className="vy-muted">{t("reviews:composer.already")}</p>;
  if (!status.can_review) return null;

  if (!open) {
    return (
      <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} onClick={() => setOpen(true)}>
        ★ {t("reviews:composer.writeReview")}
        {status.expires_at && (
          <span className="vy-muted" style={{ marginLeft: 8, fontSize: 12 }}>
            {t("reviews:composer.closesOn", { date: new Date(status.expires_at).toLocaleDateString(i18n.language) })}
          </span>
        )}
      </button>
    );
  }

  const trimmed = comment.trim();
  const commentValid = trimmed.length === 0 || (trimmed.length >= 20 && trimmed.length <= 500);

  function toggleTag(tag: string) {
    setTags((current) => (current.includes(tag) ? current.filter((x) => x !== tag) : current.length < 3 ? [...current, tag] : current));
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await apiFetch("/v1/reviews", {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({
          interaction_kind: interactionKind,
          interaction_id: interactionId,
          recommend,
          tags,
          comment: trimmed || undefined,
        }),
      });
      setSubmitted(true);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  const choiceStyle = (active: boolean) => ({
    flex: 1,
    minHeight: 48,
    background: active ? "var(--accent)" : "var(--surface-overlay)",
    color: active ? "var(--accent-ink)" : "var(--text-primary)",
    border: "none",
  });

  return (
    <div className="vy-card vy-stack">
      <h2 style={{ fontSize: 16 }}>{t("reviews:composer.question")}</h2>
      <div className="vy-row" role="radiogroup" aria-label={t("reviews:composer.question")}>
        <button role="radio" aria-checked={recommend === true} className="vy-btn" style={choiceStyle(recommend === true)} onClick={() => setRecommend(true)}>
          {recommend === true ? "✓ " : ""}{t("reviews:composer.yes")}
        </button>
        <button role="radio" aria-checked={recommend === false} className="vy-btn" style={choiceStyle(recommend === false)} onClick={() => setRecommend(false)}>
          {recommend === false ? "✓ " : ""}{t("reviews:composer.no")}
        </button>
      </div>
      <p className="vy-muted" aria-live="polite" style={{ fontSize: 13 }}>{t("reviews:composer.pickTags", { n: tags.length })}</p>
      <div className="vy-row" style={{ flexWrap: "wrap" }}>
        {[...status.tags_positive, ...status.tags_negative].map((tag) => (
          <button
            key={tag}
            role="checkbox"
            aria-checked={tags.includes(tag)}
            className="vy-chip"
            style={{
              border: "none",
              cursor: "pointer",
              background: tags.includes(tag) ? "var(--accent)" : "var(--surface-overlay)",
              color: tags.includes(tag) ? "var(--accent-ink)" : "var(--text-primary)",
            }}
            onClick={() => toggleTag(tag)}
          >
            {t(`reviews:tag.${tag}` as "tag.on_time", { defaultValue: tag })}
          </button>
        ))}
      </div>
      <label className="vy-field">
        <span className="vy-label">{t("reviews:composer.comment")}</span>
        <textarea className="vy-textarea" rows={3} maxLength={500} value={comment} onChange={(e) => setComment(e.target.value)} />
        <span className={commentValid ? "vy-muted" : "vy-error"} style={{ fontSize: 12 }}>{trimmed.length}/500</span>
      </label>
      <p className="vy-muted" style={{ fontSize: 13 }}>{t("reviews:composer.identityNote")}</p>
      {error && <p className="vy-error">{error}</p>}
      <button className="vy-btn vy-btn-primary" disabled={recommend === null || !commentValid || busy} onClick={submit}>
        {t("reviews:composer.submit")}
      </button>
    </div>
  );
}
