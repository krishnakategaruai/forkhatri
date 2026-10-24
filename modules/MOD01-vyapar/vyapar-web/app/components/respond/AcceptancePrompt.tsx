"use client";

// [FE1 — 2026-09-29] In-place legal acceptance. Sending a response or
// publishing a post is refused with 403 `acceptance_required` when the
// member has not accepted the latest privacy notice or terms (FR53). Instead
// of a detour to another screen, the document is shown here (collapsed,
// readable) with one "Accept and continue" that accepts it and retries.
// [Critique N12] Both documents are checked up front (`GET /v1/legal/{kind}`
// carries `accepted`), and every one still outstanding is shown and accepted
// with the same single tap — never two prompts one after the other.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

export type LegalKind = "privacy" | "terms";
const KINDS: LegalKind[] = ["privacy", "terms"];

interface LegalDoc {
  kind: LegalKind;
  title: string;
  body: string;
  accepted: boolean;
}

/** The document kind when `e` is an acceptance_required refusal, else null. */
export function acceptanceKind(e: unknown): LegalKind | null {
  if (!(e instanceof ApiError) || e.code !== "acceptance_required") return null;
  const k = (e.details?.kind ?? (e.detail as { kind?: string } | null)?.kind) as string | undefined;
  return k === "terms" ? "terms" : "privacy";
}

export default function AcceptancePrompt({ kind, onAccepted }: { kind: LegalKind; onAccepted: () => void }) {
  const { t } = useTranslation(["hiring", "common"]);
  const sdk = useSdk();
  const [docs, setDocs] = useState<LegalDoc[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // [Audit 2026-10-06, decision 9] The prompt used to appear under the
  // floating bar, where a tap meant for Accept hit the Businesses tab and a
  // quote was lost. It now scrolls itself into view, keeps the form it sits
  // in, and re-sends the action itself through onAccepted.
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    box.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    box.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    Promise.all(KINDS.map((k) => sdk.client.get<LegalDoc>(`/v1/legal/${k}`).catch(() => null))).then((rows) =>
      setDocs(rows.filter((d): d is LegalDoc => !!d)),
    );
  }, [sdk]);

  // The refused kind is always outstanding; the other one only if not yet accepted.
  const pending = (docs ?? []).filter((d) => d.kind === kind || !d.accepted);
  const kinds = pending.length ? pending.map((d) => d.kind) : [kind];

  async function accept() {
    setBusy(true);
    setError(null);
    try {
      for (const k of kinds) await sdk.client.post(`/v1/legal/${k}/accept`);
      onAccepted();
    } catch {
      setError(t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div ref={box} className="vy-confirm-inline vy-accept-prompt" role="alert" tabIndex={-1}>
      <strong style={{ color: "var(--text-primary)" }}>{kinds.length > 1 ? t("hiring:accept.title.both") : t(`hiring:accept.title.${kinds[0]}`)}</strong>
      <p style={{ fontSize: 13 }}>{t("hiring:accept.why")}</p>
      {pending.map((doc) => (
        <details key={doc.kind}>
          <summary style={{ cursor: "pointer", fontSize: 13, fontWeight: 600 }}>{t("hiring:accept.read", { title: doc.title })}</summary>
          <p style={{ fontSize: 13, whiteSpace: "pre-wrap", marginTop: 8, maxHeight: 220, overflow: "auto" }}>{doc.body}</p>
        </details>
      ))}
      {error && <p className="vy-error">{error}</p>}
      <button type="button" className="vy-btn vy-btn-primary" style={{ alignSelf: "flex-start" }} disabled={busy || docs === null} onClick={accept}>
        {busy ? t("hiring:apply.sending") : t("hiring:accept.acceptAndContinue")}
      </button>
    </div>
  );
}
