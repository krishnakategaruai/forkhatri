// [Voice interview 2026-09-30] Guided voice conversation for posting and
// profile setup. Owner: "Voice should like, we ask questions in their
// perspective and waits until we receive answer!"
//
// Two stateless calls (the client carries `answers` and `skipped`):
//   POST /v1/voice/interview/next       → the next question, or done + summary + draft
//   POST /v1/voice/interview/interpret  → what one spoken/typed answer means
// Contract: references/imp-voice-interview.md.
//
// Until the backend ships these routes, a DEVELOPMENT build falls back to a
// small typed mock (./voiceMock) when the live route answers 404/405. A
// production build never uses the mock, and every new interview probes the
// live API first, so the switch happens by itself when it responds.
import { ApiError } from "../errors";
import type { VyaparClient } from "../client";

export type VoiceFlow = "post_job" | "post_project" | "post_local" | "profile";
export type VoiceQuestionKind = "text" | "choice" | "number" | "yesno";
export type VoiceIntent = "answer" | "skip" | "yes" | "no" | "repeat" | "unclear";

export interface VoiceOption {
  value: string;
  label: string;
}

/** Answer values are whatever interpret returned for the field (string, number, boolean, list). */
export type VoiceAnswers = Record<string, unknown>;

export interface VoiceNextRequest {
  flow: VoiceFlow;
  language: string;
  answers: VoiceAnswers;
  skipped: string[];
}

export interface VoiceQuestion {
  done: false;
  field: string;
  question: string;
  hint: string | null;
  kind: VoiceQuestionKind;
  options: VoiceOption[] | null;
  optional: boolean;
  /** asked is 1-based: the current question's number. total counts only what this interview asks. */
  progress: { asked: number; total: number };
}

export interface VoiceSummaryItem {
  field: string;
  label: string;
  value_label: string;
}

export interface VoiceDone {
  done: true;
  summary: VoiceSummaryItem[];
  /**
   * draft_type "opportunity": the draftOpportunity (AiDraft) shape plus
   * deadline and compensation. draft_type "profile": the PATCH /v1/me/profile
   * body (null fields = unchanged), e.g. name, locality, capabilities,
   * headline, experience_years, own_assets.
   */
  draft: Record<string, unknown> & { draft_type?: "opportunity" | "profile" };
}

export type VoiceNextResponse = VoiceQuestion | VoiceDone;

export interface VoiceInterpretRequest {
  flow: VoiceFlow;
  field: string;
  language: string;
  text: string;
  answers: VoiceAnswers;
}

export interface VoiceAlternative {
  value: unknown;
  readback: string;
}

export interface VoiceInterpretation {
  understood: boolean;
  value: unknown;
  readback: string | null;
  confidence: number;
  alternatives: VoiceAlternative[];
  intent: VoiceIntent;
  reprompt: string | null;
  /** false: the answer was itself a yes/no (e.g. "no bike" → []), so no read-back. */
  needs_confirmation: boolean;
  /** Other fields the answer already stated; merged into answers once the person says yes. */
  also: VoiceAnswers;
  source?: "rules" | "ai";
}

/** Options may arrive as plain strings or {value,label}; the UI always gets {value,label}. */
function normalizeQuestion(q: VoiceNextResponse): VoiceNextResponse {
  if (q.done) return q;
  const raw = (q.options ?? null) as unknown[] | null;
  const options = raw
    ? raw.map((o) =>
        typeof o === "string"
          ? { value: o, label: o }
          : { value: String((o as VoiceOption).value), label: String((o as VoiceOption).label ?? (o as VoiceOption).value) },
      )
    : null;
  return { ...q, hint: q.hint ?? null, options, optional: !!q.optional };
}

function normalizeInterpretation(r: VoiceInterpretation): VoiceInterpretation {
  const alts = Array.isArray(r.alternatives) ? r.alternatives : [];
  return {
    ...r,
    readback: r.readback ?? null,
    reprompt: r.reprompt ?? null,
    confidence: typeof r.confidence === "number" ? r.confidence : 0,
    needs_confirmation: r.needs_confirmation !== false,
    also: r.also && typeof r.also === "object" ? r.also : {},
    alternatives: alts
      .map((a) => (a && typeof a === "object" && "readback" in a ? (a as VoiceAlternative) : null))
      .filter((a): a is VoiceAlternative => a !== null),
  };
}

type Mode = "unknown" | "live" | "mock";

/** Development only (and never when NEXT_PUBLIC_VYAPAR_VOICE_MOCK=0): use the mock while the routes 404. */
function mockAllowed(): boolean {
  const flag = process.env.NEXT_PUBLIC_VYAPAR_VOICE_MOCK;
  if (flag === "0") return false;
  if (flag === "1") return true;
  return process.env.NODE_ENV === "development";
}

export function voiceApi(c: VyaparClient) {
  let mode: Mode = "unknown";

  async function call<Req, Res>(path: string, body: Req, mock: (b: Req) => Promise<Res>): Promise<Res> {
    if (mode === "mock") return mock(body);
    try {
      const r = await c.post<Res>(path, body);
      mode = "live";
      return r;
    } catch (e) {
      if (mode !== "live" && mockAllowed() && e instanceof ApiError && (e.status === 404 || e.status === 405)) {
        mode = "mock";
        console.info("[voice] %s is not on this API yet; using the development mock", path);
        return mock(body);
      }
      throw e;
    }
  }

  return {
    /** nextInterviewQuestion — the next question, or done with a summary and a draft */
    next: async (body: VoiceNextRequest) =>
      normalizeQuestion(
        await call<VoiceNextRequest, VoiceNextResponse>("/v1/voice/interview/next", body, async (b) => (await import("../voiceMock")).mockNext(b)),
      ),
    /** interpretInterviewAnswer — what one answer means, with a readback to confirm */
    interpret: async (body: VoiceInterpretRequest) =>
      normalizeInterpretation(
        await call<VoiceInterpretRequest, VoiceInterpretation>("/v1/voice/interview/interpret", body, async (b) =>
          (await import("../voiceMock")).mockInterpret(b),
        ),
      ),
    /** Start of a new interview: probe the live API again (it may have shipped since). */
    reset: () => {
      if (mode === "mock") mode = "unknown";
    },
    /** "live" | "mock" | "unknown" — for diagnostics and the test hook. */
    mode: () => mode,
  };
}

export type VoiceApi = ReturnType<typeof voiceApi>;
