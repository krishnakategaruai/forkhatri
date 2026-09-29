"use client";

// ======================================================================
// [FE1 — 2026-09-28] One-tap job application (WorkIndia / Apna / Indeed
// Apply pattern, research §2): not a form — a confirmation of the profile
// that will be sent, an optional note (voice or typed), and one "Apply".
//
// The snapshot shown is built the way the server builds `profile_snapshot`
// (imp-backend-a §2): the most recent non-archived listing, a professional
// profile first, plus the member's name — so what the person confirms is
// what the poster will see. The request is {opportunity_id, message: note,
// applied_via: "one_tap"}; an empty note is allowed for a job.
// After sending, the confirmation is replaced by a compact "Sent" card
// (no success modal), with a link to the conversation.
// ======================================================================

import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import AcceptancePrompt, { acceptanceKind, type LegalKind } from "@/app/components/respond/AcceptancePrompt";
import { useRoutes } from "@/app/host/HostProvider";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";

interface MyListing {
  id: string;
  kind: "business" | "professional";
  name: string;
  headline: string | null;
  locality: string;
  state: string;
  experience_years?: number | null;
  capability_labels: string[];
  availability?: "now" | "this_week" | "later" | null;
}

export interface ApplyTarget {
  id: string;
  title: string;
  pay?: string | null;
  location?: string | null;
}

export default function ApplyConfirm({ target, onDone }: { target: ApplyTarget; onDone?: (enquiryId: string) => void }) {
  const { t } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const routes = useRoutes();
  const [listings, setListings] = useState<MyListing[] | null>(null);
  const [myName, setMyName] = useState("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existing, setExisting] = useState<string | null>(null);
  const [sentId, setSentId] = useState<string | null>(null);
  // One key per confirmation: a double tap or a retried request never applies twice.
  const [needsAccept, setNeedsAccept] = useState<LegalKind | null>(null);
  const [idemKey] = useState(() => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `apply-${Date.now()}`));

  useEffect(() => {
    sdk.client.get<MyListing[]>("/v1/listings/mine").then(setListings).catch(() => setListings([]));
    sdk.members.me().then((m) => setMyName(m.display_name)).catch(() => undefined);
  }, [sdk]);

  const snapshot = useMemo(() => {
    const live = (listings ?? []).filter((l) => l.state !== "archived" && l.state !== "removed");
    return live.find((l) => l.kind === "professional") ?? live[0] ?? null;
  }, [listings]);

  async function apply() {
    setSending(true);
    setError(null);
    setExisting(null);
    try {
      const r = await sdk.responses.create({ opportunity_id: target.id, message: note.trim(), applied_via: "one_tap" }, idemKey);
      setSentId(r.id);
      onDone?.(r.id);
    } catch (e) {
      const legal = acceptanceKind(e);
      if (legal) {
        setNeedsAccept(legal);
        return;
      }
      if (e instanceof ApiError && e.status === 409 && e.detail && typeof e.detail === "object") {
        setExisting((e.detail as { existing_enquiry_id?: string }).existing_enquiry_id ?? null);
        setError(e.code === "already_declined" ? t("hiring:errors.already_declined") : t("hiring:apply.alreadyApplied"));
      } else if (e instanceof ApiError && e.status === 429) {
        setError(t("hiring:apply.dailyCap"));
      } else if (e instanceof ApiError && e.code) {
        setError(t(`hiring:errors.${e.code}`, { defaultValue: typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong") }));
      } else {
        setError(t("common:state.somethingWentWrong"));
      }
    } finally {
      setSending(false);
    }
  }

  if (sentId) {
    return (
      <div className="vy-sent" role="status">
        <span className="vy-sent-mark" aria-hidden="true">✓</span>
        <strong style={{ color: "var(--text-primary)", fontSize: 17 }}>{t("hiring:apply.sentTitle")}</strong>
        <p style={{ fontSize: 14 }}>{t("hiring:apply.sentBody", { title: target.title })}</p>
        <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={routes.enquiry(sentId)}>
          {t("hiring:apply.openConversation")}
        </a>
      </div>
    );
  }

  const name = snapshot && snapshot.kind === "professional" ? myName || snapshot.name : myName;

  return (
    <div className="vy-stack" style={{ gap: 16 }}>
      <div className="vy-stack" style={{ gap: 4 }}>
        <span className="vy-eyebrow">{t("hiring:apply.youreApplyingFor")}</span>
        <strong style={{ color: "var(--text-primary)", fontSize: 17 }}>{target.title}</strong>
        {(target.pay || target.location) && <span className="vy-field-hint" style={{ fontSize: 13 }}>{[target.pay, target.location].filter(Boolean).join(" · ")}</span>}
      </div>

      <div className="vy-card vy-card-nested vy-stack" style={{ gap: 10, padding: 16 }}>
        <span className="vy-fact-label">{t("hiring:apply.posterSees")}</span>
        {listings === null ? (
          <div className="vy-skeleton" style={{ height: 56 }} />
        ) : snapshot ? (
          <div className="vy-snapshot">
            <span className="vy-monogram" aria-hidden="true">{(name || "?").trim().charAt(0).toUpperCase()}</span>
            <div className="vy-snapshot-body">
              <strong>{name}</strong>
              {snapshot.headline && <span style={{ fontSize: 14, color: "var(--text-secondary)" }}>{snapshot.headline}</span>}
              <span className="vy-field-hint" style={{ fontSize: 13 }}>
                {[
                  snapshot.experience_years != null ? t("hiring:apply.years", { count: snapshot.experience_years }) : null,
                  snapshot.locality,
                  snapshot.availability ? t(`hiring:apply.availability.${snapshot.availability}`) : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </span>
              {snapshot.capability_labels.length > 0 && (
                <div className="vy-options" style={{ marginTop: 4 }}>
                  {snapshot.capability_labels.slice(0, 4).map((c) => (
                    <span key={c} className="vy-chip">{c}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <p style={{ fontSize: 14 }}>{t("hiring:apply.noProfile", { name: myName })}</p>
        )}
        <a href={routes.myListings} style={{ fontSize: 13 }}>{t("hiring:apply.editProfile")}</a>
      </div>

      <div className="vy-field">
        <label className="vy-label" htmlFor="vy-apply-note">
          {t("hiring:apply.noteLabel")} <span className="vy-optional">· {t("hiring:fields.optional")}</span>
        </label>
        <VoiceInput fieldLabel={t("hiring:apply.noteLabel")} onConfirm={(text) => setNote((v) => appendSpoken(v, text))}>
          <textarea
            id="vy-apply-note"
            className="vy-textarea"
            rows={3}
            maxLength={1000}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("hiring:apply.notePlaceholder")}
          />
        </VoiceInput>
      </div>

      {needsAccept && (
        <AcceptancePrompt
          kind={needsAccept}
          onAccepted={() => {
            setNeedsAccept(null);
            void apply();
          }}
        />
      )}
      {error && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <p className="vy-error" role="alert">{error}</p>
          {existing && (
            <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={routes.enquiry(existing)}>
              {t("hiring:apply.openConversation")}
            </a>
          )}
        </div>
      )}

      <button type="button" className="vy-btn vy-btn-primary" disabled={sending || listings === null} onClick={apply}>
        {sending ? t("hiring:apply.sending") : t("hiring:apply.apply")}
      </button>
      <p className="vy-field-hint">🔒 {t("hiring:apply.privacy")}</p>
    </div>
  );
}
