"use client";

// [FE1 — 2026-09-29] In-place legal acceptance. Sending a response or
// publishing a post is refused with 403 `acceptance_required` when the
// member has not accepted the latest privacy notice or terms (FR53). Found
// live: a proposal simply failed with "Something went wrong". Instead of a
// detour to another screen, the document is shown here (collapsed, readable)
// with one "Accept and continue" that accepts it and retries the action.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

export type LegalKind = "privacy" | "terms";

/** The document kind when `e` is an acceptance_required refusal, else null. */
export function acceptanceKind(e: unknown): LegalKind | null {
  if (!(e instanceof ApiError) || e.code !== "acceptance_required") return null;
  const k = (e.details?.kind ?? (e.detail as { kind?: string } | null)?.kind) as string | undefined;
  return k === "terms" ? "terms" : "privacy";
}

export default function AcceptancePrompt({ kind, onAccepted }: { kind: LegalKind; onAccepted: () => void }) {
  const { t } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const [doc, setDoc] = useState<{ title: string; body: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    sdk.client.get<{ title: string; body: string }>(`/v1/legal/${kind}`).then(setDoc).catch(() => setDoc(null));
  }, [sdk, kind]);

  async function accept() {
    setBusy(true);
    setError(null);
    try {
      await sdk.client.post(`/v1/legal/${kind}/accept`);
      onAccepted();
    } catch {
      setError(t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vy-confirm-inline" role="alert">
      <strong style={{ color: "var(--text-primary)" }}>{t(`hiring:accept.title.${kind}`)}</strong>
      <p style={{ fontSize: 13 }}>{t("hiring:accept.why")}</p>
      {doc && (
        <details>
          <summary style={{ cursor: "pointer", fontSize: 13, fontWeight: 600 }}>{t("hiring:accept.read", { title: doc.title })}</summary>
          <p style={{ fontSize: 13, whiteSpace: "pre-wrap", marginTop: 8, maxHeight: 220, overflow: "auto" }}>{doc.body}</p>
        </details>
      )}
      {error && <p className="vy-error">{error}</p>}
      <button type="button" className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={accept}>
        {busy ? t("hiring:apply.sending") : t("hiring:accept.acceptAndContinue")}
      </button>
    </div>
  );
}
