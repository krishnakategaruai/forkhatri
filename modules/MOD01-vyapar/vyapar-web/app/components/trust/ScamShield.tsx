"use client";

// ======================================================================
// [Trust pack §1, 2026-09-30] Scam shield while the poster writes.
//
// REQUIREMENT: a poster who writes "registration fees ₹500" or "pehle 500
// rupay jama karo" learns it is not allowed under the very field, before
// Publish or Send — not from a refusal after the tap. The server's
// pre-check (checkScamShield, POST /v1/trust/scam-check) never raises and
// stores nothing, so it is safe to call as the person types.
// APPROACH:
//  - useScamShieldFields(): one debounced (700 ms) check per changed field,
//    remembered by text so an unchanged field is never asked twice; the
//    previous round is aborted when the person keeps typing. Short text
//    (under 8 characters) is not checked.
//  - <ScamShieldNote>: a calm note under the field (warning tint, no red
//    alarm): the server's localized message, its explanation, and the
//    phrase it matched, underlined, so the person sees exactly what to take
//    out. It replaces nothing: the field stays editable and the note goes
//    away the moment the text is clean.
//  - scamFromError(): the same note from a 422 `seeker_charge_not_allowed`,
//    for the case the pre-check could not run (offline, a pasted field).
// ======================================================================

import { useEffect, useRef, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { ApiError, type ScamCheck, type ScamSurface } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

const DEBOUNCE_MS = 700;
const MIN_LENGTH = 8;

/** A refusal found in a field: what to show under it. */
export type ScamFinding = Pick<ScamCheck, "message" | "explanation" | "matched" | "rule">;

/**
 * Checks each named text field as the person types. Returns the findings
 * for the fields that would be refused (clean fields are absent).
 */
export function useScamShieldFields(
  fields: Record<string, string>,
  surface: ScamSurface,
  opportunityType?: string | null,
  enabled = true,
): Record<string, ScamFinding> {
  const sdk = useSdk();
  const [findings, setFindings] = useState<Record<string, ScamFinding>>({});
  // text → result, per surface/type, so retyping a checked text is instant.
  const cache = useRef(new Map<string, ScamCheck>());
  const key = JSON.stringify(fields);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const entries = Object.entries(JSON.parse(key) as Record<string, string>);
      const next: Record<string, ScamFinding> = {};
      await Promise.all(
        entries.map(async ([name, raw]) => {
          const text = raw.trim();
          if (text.length < MIN_LENGTH) return;
          const cacheKey = `${surface}|${opportunityType ?? ""}|${text}`;
          let result = cache.current.get(cacheKey);
          if (!result) {
            try {
              result = await sdk.trustPack.scamCheck({ text, surface, opportunity_type: opportunityType ?? null }, controller.signal);
              cache.current.set(cacheKey, result);
            } catch {
              return; // offline or aborted: the server still refuses on save
            }
          }
          if (!result.allowed) next[name] = result;
        }),
      );
      if (!controller.signal.aborted) setFindings(next);
    }, DEBOUNCE_MS);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [key, surface, opportunityType, enabled, sdk]);

  // A field that became empty or short clears at once, without waiting.
  const current = JSON.parse(key) as Record<string, string>;
  const visible: Record<string, ScamFinding> = {};
  for (const [name, f] of Object.entries(enabled ? findings : {})) {
    if ((current[name] ?? "").trim().length >= MIN_LENGTH) visible[name] = f;
  }
  return visible;
}

/** One field's check. */
export function useScamShield(text: string, surface: ScamSurface, opportunityType?: string | null, enabled = true): ScamFinding | null {
  return useScamShieldFields({ text }, surface, opportunityType, enabled).text ?? null;
}

/** The refusal carried by a 422 `seeker_charge_not_allowed`, with the field it names. */
export function scamFromError(e: unknown): (ScamFinding & { field: string | null }) | null {
  if (!(e instanceof ApiError) || e.code !== "seeker_charge_not_allowed") return null;
  const detail = (e.detail && typeof e.detail === "object" ? e.detail : {}) as Record<string, unknown>;
  const details = e.details ?? {};
  const str = (v: unknown) => (typeof v === "string" && v ? v : null);
  const envelope = (e.body && typeof e.body === "object" ? (e.body as { error?: { message?: unknown } }).error : null) ?? null;
  return {
    message: str(detail.message) ?? str(envelope?.message) ?? str(e.detail),
    explanation: str(details.explanation) ?? str(detail.explanation),
    matched: str(details.matched) ?? str(detail.matched),
    rule: str(details.rule) ?? str(detail.rule),
    field: str(details.field) ?? str(detail.field),
  };
}

/** The calm note under a field. */
export function ScamShieldNote({ finding, id }: { finding: ScamFinding | null | undefined; id?: string }) {
  if (!finding) return null;
  return (
    <div id={id} className="vy-shield-note" role="status" aria-live="polite">
      <ShieldAlert size={18} strokeWidth={2} aria-hidden="true" />
      <div className="vy-shield-note-text">
        {finding.message && <strong>{finding.message}</strong>}
        {finding.matched && (
          <span className="vy-shield-note-matched">
            “<mark>{finding.matched}</mark>”
          </span>
        )}
        {finding.explanation && <span>{finding.explanation}</span>}
      </div>
    </div>
  );
}
