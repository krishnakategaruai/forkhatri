"use client";

// ======================================================================
// [Voice interview 2026-09-30] The conversation engine.
//
// REQUIREMENT (owner): "Voice should like, we ask questions in their
// perspective and waits until we receive answer!" A guided conversation,
// one question at a time, not a mic that transcribes a paragraph.
//
// THE LOOP, per question (the server picks the question and its words):
//   speak the question in the member's language (only with a voice FOR that
//   language; never Telugu through an English voice)
//   → listen automatically, interim words shown live
//   → WAIT. No timer ever moves on. 8 s of silence: gently say it again
//     (take your time + the question, then the hint); after 3 silent rounds
//     stop the mic and show "Tap the mic when you're ready"
//   → final words → interpret → repeat / skip (optional only) / unclear
//     (speak the server's reprompt, listen again) / understood
//   → speak the readback ("I heard ₹15,000 a month — is that right?") with
//     Yes / Change, and listen for yes / no (interpret, same field, intent)
//   → Yes stores the value and asks the server for the next question.
// Typing is always one tap away ("Type instead"), and is the whole
// conversation when the browser can't listen or the mic is blocked.
// Barge-in: tapping the mic while a question is spoken stops speaking and
// listens. On desktop (fine pointer) the mic also listens while speaking and
// cuts in when it hears words that aren't our own question echoing back; on
// phones that is left to the tap, because starting recognition during speech
// ducks or stops the speech on Android.
//
// APPROACH: a plain class owns the timers, the recogniser and the speech
// (none of it is render state); React reads its snapshot through
// useSyncExternalStore.
//
// Test hook (development builds only): window.__vyVoice.inject(text) hands
// the engine a final transcript, and .log records every step, so headless
// checks can prove speak → listen → readback → yes → next.
// ======================================================================

import { useEffect, useState, useSyncExternalStore } from "react";
import type { TFunction } from "i18next";
import type { VoiceAnswers, VoiceApi, VoiceDone, VoiceFlow, VoiceInterpretation, VoiceQuestion } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import {
  isEcho,
  loadVoices,
  pickVoice,
  recognitionCtor,
  speak,
  SPEECH_LOCALE,
  speechLang,
  synthesisSupported,
  type Recognition,
  type SpeakHandle,
} from "./speech";

export const KIND_FIELD = "__kind";
const POST_FLOWS: VoiceFlow[] = ["post_job", "post_project", "post_local"];
const SILENCE_MS = 8000;
const MAX_SILENT_ROUNDS = 3;
const AUTO_ACCEPT_TYPED = 0.8;

export type Activity = "idle" | "loading" | "speaking" | "listening" | "thinking";

export type Step =
  | { type: "intro" }
  | { type: "ask"; q: VoiceQuestion }
  | { type: "confirm"; q: VoiceQuestion; value: unknown; readback: string; also: VoiceAnswers }
  | { type: "summary"; done: VoiceDone }
  | { type: "error" };

export interface Answered {
  q: VoiceQuestion;
  value: unknown;
  label: string;
}

export interface InterviewState {
  step: Step;
  activity: Activity;
  /** "voice": speak + listen; "typing": one question at a time with an answer box. */
  mode: "voice" | "typing";
  /** Why typing was forced, for a one-line note. */
  typingReason: "unsupported" | "blocked" | "nomic" | "network" | "chosen" | null;
  /** The "Type instead" box is open for this one answer. */
  typing: boolean;
  interim: string;
  heard: string;
  /** A spoken reprompt or a gentle "take your time", shown under the question. */
  note: string | null;
  silentRounds: number;
  waitingTap: boolean;
  /** No speech voice for the member's language: text only. */
  voiceMissing: boolean;
  flow: VoiceFlow | null;
  answers: VoiceAnswers;
  skipped: string[];
  history: Answered[];
}

interface EngineContext {
  t: TFunction;
  language: string;
  onFlow?: (flow: VoiceFlow) => void;
}

/**
 * A short chip label for a confirmed answer. Values are the server's shapes
 * ({title,…}, {min_paise,max_paise}, {job_timings,shift}, ["two_wheeler"]…);
 * anything without an obvious short form falls back to the read-back words.
 */
function answerLabel(q: VoiceQuestion, value: unknown, readback: string | undefined, language: string): string {
  const locale = `${language}-IN`;
  const rupees = (paise: unknown) => `₹${Math.round(Number(paise) / 100).toLocaleString(locale)}`;
  const optionLabel = (v: unknown) => q.options?.find((o) => o.value === String(v))?.label ?? String(v);
  if (q.kind === "choice" && !Array.isArray(value) && (typeof value === "string" || typeof value === "number")) return optionLabel(value);
  if (Array.isArray(value)) return value.length ? value.map(optionLabel).join(", ") : (q.options?.find((o) => o.value === "none")?.label ?? readback ?? "—");
  if (typeof value === "number") return value.toLocaleString(locale);
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const v = value as Record<string, unknown>;
    for (const k of ["title", "job_timings", "compensation", "deadline", "preferred_date"]) if (typeof v[k] === "string" && v[k]) return v[k] as string;
    const lo = v.min_paise ?? v.budget_paise;
    const hi = v.max_paise ?? lo;
    if (typeof lo === "number") return lo === hi || typeof hi !== "number" ? rupees(lo) : `${rupees(lo)}–${rupees(hi)}`;
  }
  return readback ?? String(value ?? "");
}

export class InterviewEngine {
  private s: InterviewState;
  private listeners = new Set<() => void>();
  private rec: Recognition | null = null;
  private recPurpose: "listen" | "barge" = "listen";
  private gotFinal = false;
  private speech: SpeakHandle | null = null;
  private spokenText = "";
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private bargeTimer: ReturnType<typeof setTimeout> | null = null;
  private voice: SpeechSynthesisVoice | null = null;
  private run = 0;
  private startToken = 0;
  readonly log: string[] = [];

  constructor(
    private api: VoiceApi,
    private ctx: EngineContext,
    flow: VoiceFlow | null,
    initialAnswers: VoiceAnswers = {},
  ) {
    this.s = {
      step: { type: "intro" },
      activity: "idle",
      mode: "voice",
      typingReason: null,
      typing: false,
      interim: "",
      heard: "",
      note: null,
      silentRounds: 0,
      waitingTap: false,
      voiceMissing: false,
      flow,
      answers: { ...initialAnswers },
      skipped: [],
      history: [],
    };
  }

  // ---- store --------------------------------------------------------------------
  subscribe = (fn: () => void) => {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  };
  snapshot = () => this.s;
  setContext(ctx: EngineContext) {
    this.ctx = ctx;
  }
  private set(patch: Partial<InterviewState> | ((s: InterviewState) => Partial<InterviewState>)) {
    const p = typeof patch === "function" ? patch(this.s) : patch;
    this.s = { ...this.s, ...p };
    this.listeners.forEach((l) => l());
  }
  private note(entry: string) {
    this.log.push(`${new Date().toISOString().slice(11, 23)} ${entry}`);
    if (this.log.length > 300) this.log.shift();
    if (process.env.NODE_ENV !== "production") console.debug("[voice]", entry);
  }
  private get t() {
    return this.ctx.t;
  }
  private get lang() {
    return speechLang(this.ctx.language);
  }

  // ---- resources ----------------------------------------------------------------
  private clearSilence() {
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    this.silenceTimer = null;
  }
  private armSilence(token: number) {
    this.clearSilence();
    this.silenceTimer = setTimeout(() => {
      if (token === this.run && this.recPurpose === "listen") this.silence();
    }, SILENCE_MS);
  }
  private stopRecognition() {
    this.clearSilence();
    if (this.bargeTimer) clearTimeout(this.bargeTimer);
    this.bargeTimer = null;
    const r = this.rec;
    this.rec = null;
    if (!r) return;
    r.onresult = null;
    r.onend = null;
    r.onerror = null;
    try {
      r.abort();
    } catch {
      /* already stopped */
    }
  }
  private stopSpeech() {
    this.speech?.cancel();
    this.speech = null;
  }
  stopAll = () => {
    this.run++;
    this.stopRecognition();
    this.stopSpeech();
  };

  private canListen() {
    return this.s.mode === "voice" && recognitionCtor() !== null;
  }
  private canSpeak() {
    return this.s.mode === "voice" && this.voice !== null;
  }
  private toTyping(reason: InterviewState["typingReason"]) {
    this.stopRecognition();
    this.note(`typing:${reason}`);
    this.set({ mode: "typing", typingReason: reason, typing: true, activity: "idle", waitingTap: false, interim: "" });
  }

  // ---- the turn -----------------------------------------------------------------
  private listen(barge = false) {
    if (!this.canListen() || this.s.typing) {
      this.set({ activity: "idle" });
      return;
    }
    const Ctor = recognitionCtor()!;
    this.stopRecognition();
    const r = new Ctor();
    r.lang = SPEECH_LOCALE[this.lang];
    r.continuous = false;
    r.interimResults = true;
    this.recPurpose = barge ? "barge" : "listen";
    this.gotFinal = false;
    const token = this.run;

    r.onresult = (e) => {
      if (token !== this.run) return;
      let live = "";
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) final += res[0].transcript;
        else live += res[0].transcript;
      }
      const heard = (final || live).trim();
      if (this.recPurpose === "barge") {
        // Our own question coming back through the speaker is not the person.
        if (!heard || isEcho(heard, this.spokenText)) return;
        this.note(`barge-in:"${heard}"`);
        this.stopSpeech();
        this.recPurpose = "listen";
        this.set({ activity: "listening" });
      }
      this.armSilence(token);
      if (final.trim()) {
        this.gotFinal = true;
        this.stopRecognition();
        this.set({ interim: "" });
        void this.transcript(final.trim(), false);
      } else {
        this.set({ interim: live });
      }
    };
    r.onerror = (e) => {
      if (token !== this.run) return;
      if (e.error === "aborted" || e.error === "no-speech") return; // onend decides
      if (this.recPurpose === "barge") return; // the listen after speaking reports it
      this.note(`recognition-error:${e.error}`);
      if (e.error === "not-allowed" || e.error === "service-not-allowed") this.toTyping("blocked");
      else if (e.error === "audio-capture") this.toTyping("nomic");
      else if (e.error === "network") this.toTyping("network");
    };
    r.onend = () => {
      if (token !== this.run || this.rec !== r) return;
      this.rec = null;
      if (this.gotFinal || this.recPurpose === "barge") return;
      // Ended without words: one silent round, never a reason to move on.
      this.clearSilence();
      this.silence();
    };
    this.rec = r;
    try {
      r.start();
      if (!barge) {
        this.note("listen");
        this.set({ activity: "listening", interim: "", waitingTap: false });
        this.armSilence(token);
      }
    } catch {
      this.rec = null;
      if (!barge) this.toTyping("unsupported");
    }
  }

  private say(text: string, then: () => void) {
    if (!this.canSpeak()) {
      then();
      return;
    }
    this.stopRecognition();
    this.stopSpeech();
    const token = this.run;
    this.spokenText = text;
    this.note(`speak:"${text}"`);
    this.set({ activity: "speaking", interim: "" });
    const h = speak(text, this.voice!);
    this.speech = h;
    const turn = this.s.step.type;
    const fine = typeof window !== "undefined" && window.matchMedia?.("(pointer: fine)").matches;
    if (this.canListen() && fine && (turn === "ask" || turn === "confirm")) {
      this.bargeTimer = setTimeout(() => {
        if (token === this.run && this.s.activity === "speaking") this.listen(true);
      }, 700);
    }
    void h.done.then((finished) => {
      if (token !== this.run || this.speech !== h) return;
      this.speech = null;
      if (!finished) return; // cancelled: whoever cancelled decides what's next
      if (this.rec && this.recPurpose === "barge") {
        // Already listening underneath: it simply becomes the listen.
        this.recPurpose = "listen";
        this.note("listen");
        this.set({ activity: "listening", waitingTap: false });
        this.armSilence(token);
        return;
      }
      then();
    });
  }

  private ask(q: VoiceQuestion, sayText?: string, noteText: string | null = null) {
    this.run++;
    this.stopRecognition();
    this.stopSpeech();
    this.note(`ask:${q.field}`);
    const typing = this.s.mode === "typing";
    this.set({ step: { type: "ask", q }, note: noteText, interim: "", waitingTap: false, typing });
    if (typing) {
      this.set({ activity: "idle" });
      return;
    }
    this.say(sayText ?? q.question, () => this.listen());
  }

  private confirm(q: VoiceQuestion, value: unknown, readback: string, also: VoiceAnswers = {}) {
    this.run++;
    this.stopRecognition();
    this.note(`readback:${q.field}=${JSON.stringify(value)} "${readback}"`);
    this.set({ step: { type: "confirm", q, value, readback, also }, note: null, interim: "", silentRounds: 0, waitingTap: false });
    if (this.s.mode === "typing") {
      this.set({ activity: "idle" });
      return;
    }
    this.say(readback, () => this.listen());
  }

  private silence() {
    this.stopRecognition();
    const s = this.s;
    const rounds = s.silentRounds + 1;
    this.note(`silence:${rounds}`);
    if (rounds >= MAX_SILENT_ROUNDS) {
      this.set({ silentRounds: rounds, waitingTap: true, activity: "idle", interim: "", note: null });
      return;
    }
    const gentle = this.t("voice:talk.takeYourTime");
    this.set({ silentRounds: rounds, note: gentle });
    if (s.step.type === "confirm") {
      this.say(`${gentle} ${s.step.readback}`, () => this.listen());
    } else if (s.step.type === "ask") {
      // First silence: the question again, gently. Second: the hint, as a rephrase.
      const q = s.step.q;
      this.say(`${gentle} ${rounds === 1 || !q.hint ? q.question : q.hint}`, () => this.listen());
    }
  }

  private accept(q: VoiceQuestion, value: unknown, readback?: string, also: VoiceAnswers = {}) {
    this.run++;
    this.stopRecognition();
    this.stopSpeech();
    this.note(`yes:${q.field}=${JSON.stringify(value)}${Object.keys(also).length ? ` also=${JSON.stringify(also)}` : ""}`);
    if (q.field === KIND_FIELD) {
      const flow = String(value) as VoiceFlow;
      this.set({ flow, silentRounds: 0 });
      this.ctx.onFlow?.(flow);
      void this.next();
      return;
    }
    const label = answerLabel(q, value, readback, this.ctx.language);
    // `also`: what the answer already stated ("…in Kukatpally, 15 to 18
    // thousand") is kept, so those questions are never asked.
    this.set((s) => ({
      answers: { ...s.answers, ...also, [q.field]: value },
      skipped: s.skipped.filter((f) => f !== q.field && !(f in also)),
      history: s.history.some((h) => h.q.field === q.field)
        ? s.history.map((h) => (h.q.field === q.field ? { q, value, label } : h))
        : [...s.history, { q, value, label }],
      silentRounds: 0,
      heard: "",
    }));
    void this.next();
  }

  private async next() {
    const s = this.s;
    const token = ++this.run;
    if (!s.flow) {
      this.ask(kindQuestion(this.t));
      return;
    }
    this.set({ activity: "loading", note: null, interim: "" });
    try {
      const r = await this.api.next({ flow: s.flow, language: this.ctx.language, answers: s.answers, skipped: s.skipped });
      if (token !== this.run) return;
      if (r.done) {
        this.note(`done:${r.summary.length} answers`);
        this.set({ step: { type: "summary", done: r }, activity: "idle", typing: false, note: null });
        if (this.canSpeak()) this.say(this.t("voice:talk.summarySpoken"), () => this.set({ activity: "idle" }));
        return;
      }
      this.note(`next:${r.field} (${r.progress.asked}/${r.progress.total})`);
      this.set({ silentRounds: 0 });
      this.ask(r);
    } catch (e) {
      if (token !== this.run) return;
      this.note(`next-error:${String(e)}`);
      this.set({ step: { type: "error" }, activity: "idle" });
    }
  }

  private async transcript(text: string, typed: boolean) {
    const s = this.s;
    const step = s.step;
    if (step.type !== "ask" && step.type !== "confirm") return;
    const q = step.q;
    const token = ++this.run;
    this.stopRecognition();
    this.stopSpeech();
    this.note(`final:"${text}"${typed ? " (typed)" : ""}`);
    this.set({ activity: "thinking", heard: text, interim: "", waitingTap: false, silentRounds: 0 });

    if (q.field === KIND_FIELD) {
      const hit = matchKind(text, this.t);
      if (hit) this.accept(q, hit);
      else this.ask(q, this.t("voice:kind.again"), this.t("voice:kind.again"));
      return;
    }

    let r: VoiceInterpretation;
    try {
      r = await this.api.interpret({ flow: s.flow!, field: q.field, language: this.ctx.language, text, answers: s.answers });
    } catch (e) {
      if (token !== this.run) return;
      this.note(`interpret-error:${String(e)}`);
      this.set({ activity: "idle", note: this.t("voice:talk.networkTrouble"), waitingTap: s.mode === "voice" });
      return;
    }
    if (token !== this.run) return;
    this.note(`interpret:${r.intent}${r.understood ? ` value=${JSON.stringify(r.value)}` : ""}`);
    const hasValue = r.understood && r.value !== null && r.value !== undefined;
    const readback = r.readback ?? this.t("voice:talk.heardFallback", { value: text });

    // At the read-back, only `intent` counts: "no" rejects the read-back even
    // where "no" would be a real answer to the question itself.
    if (step.type === "confirm") {
      if (r.intent === "yes") return this.accept(q, step.value, step.readback, step.also);
      if (r.intent === "no") return this.ask(q, `${this.t("voice:talk.okAgain")} ${q.question}`);
      if (r.intent === "repeat") return this.confirm(q, step.value, step.readback, step.also);
      const line = this.t("voice:talk.sayYesOrNo");
      this.set({ note: line });
      if (this.s.mode === "typing") return this.set({ activity: "idle" });
      return this.say(line, () => this.listen());
    }

    if (hasValue) {
      // The answer was itself a yes/no ("no bike" → []): nothing to read back.
      if (!r.needs_confirmation) return this.accept(q, r.value, r.readback ?? undefined, r.also);
      if (typed && r.confidence >= AUTO_ACCEPT_TYPED && !Object.keys(r.also).length) return this.accept(q, r.value, readback);
      return this.confirm(q, r.value, readback, r.also);
    }
    if (r.intent === "repeat") return this.ask(q, r.reprompt ?? undefined);
    if (r.intent === "skip") {
      if (q.optional) {
        this.note(`skip:${q.field}`);
        this.set((x) => ({ skipped: x.skipped.includes(q.field) ? x.skipped : [...x.skipped, q.field] }));
        return void this.next();
      }
      const needed = r.reprompt ?? `${this.t("voice:talk.needed")} ${q.question}`;
      return this.ask(q, needed, needed);
    }
    const again = r.reprompt ?? this.t("voice:talk.didntCatch");
    this.ask(q, again, again);
  }

  // ---- public actions -------------------------------------------------------------

  /** Intro "Start": ask for the mic (explained first), find a voice, then begin. */
  start = async (preferTyping = false) => {
    // A later tap (e.g. "I'd rather type" while the browser's microphone
    // prompt is still open) wins; the earlier start is dropped when it returns.
    const token = ++this.startToken;
    this.api.reset();
    let mode: InterviewState["mode"] = preferTyping ? "typing" : "voice";
    let reason: InterviewState["typingReason"] = preferTyping ? "chosen" : null;
    this.set({ activity: "loading", mode: preferTyping ? "typing" : "voice" });
    if (!preferTyping) {
      if (!recognitionCtor()) {
        mode = "typing";
        reason = "unsupported";
      } else if (navigator.mediaDevices?.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach((tr) => tr.stop());
        } catch (e) {
          mode = "typing";
          reason = (e as DOMException)?.name === "NotFoundError" ? "nomic" : "blocked";
        }
      }
    }
    if (token !== this.startToken) return;
    const voices = synthesisSupported() ? await loadVoices() : [];
    if (token !== this.startToken) return;
    this.voice = pickVoice(voices, this.lang);
    this.note(`start:mode=${mode} voice=${this.voice?.lang ?? "none"} api=${this.api.mode()}`);
    this.set({ mode, typingReason: reason, typing: mode === "typing", voiceMissing: this.voice === null });
    await this.next();
  };

  /** The big mic: barge in while speaking, pause while listening, listen when idle. */
  tapMic = () => {
    const a = this.s.activity;
    if (a === "speaking") {
      this.note("barge-in:tap");
      this.run++;
      this.stopSpeech();
      this.listen();
    } else if (a === "listening") {
      this.stopRecognition();
      this.set({ activity: "idle", waitingTap: true, interim: "", note: null });
    } else if (a === "idle") {
      this.run++;
      this.set({ silentRounds: 0, note: null, typing: false });
      this.listen();
    }
  };

  answerTyped = (text: string) => {
    const v = text.trim();
    if (v) void this.transcript(v, true);
  };

  /** Test hook and recogniser both land here. */
  inject = (text: string) => void this.transcript(text, false);

  openTyping = () => {
    this.run++;
    this.stopRecognition();
    this.stopSpeech();
    this.set({ typing: true, activity: "idle", interim: "", waitingTap: false });
  };

  closeTyping = () => {
    if (this.s.mode === "typing") return;
    this.set({ typing: false });
    this.listen();
  };

  /** Switch the whole conversation to voice from typing (when the browser can listen). */
  switchToVoice = () => {
    if (!recognitionCtor()) return;
    this.set({ mode: "voice", typing: false, typingReason: null });
    const st = this.s.step;
    if (st.type === "ask") this.ask(st.q);
    else if (st.type === "confirm") this.confirm(st.q, st.value, st.readback, st.also);
  };

  choose = (value: unknown) => {
    const st = this.s.step;
    if (st.type === "ask" || st.type === "confirm") this.accept(st.q, value);
  };

  yes = () => {
    const st = this.s.step;
    if (st.type === "confirm") this.accept(st.q, st.value, st.readback, st.also);
  };

  change = () => {
    const st = this.s.step;
    if (st.type === "confirm") this.ask(st.q, `${this.t("voice:talk.okAgain")} ${st.q.question}`);
  };

  skip = () => {
    const st = this.s.step;
    if (st.type !== "ask" || !st.q.optional) return;
    const field = st.q.field;
    this.note(`skip:${field}`);
    this.set((x) => ({ skipped: [...x.skipped.filter((f) => f !== field), field] }));
    void this.next();
  };

  /** Tap a chip or a summary row: ask that question again. */
  edit = (field: string) => {
    const h = this.s.history.find((x) => x.q.field === field);
    if (h) return this.ask(h.q);
    // Stated along with another answer (`also`) or already known: forget it
    // and the server asks exactly that question next.
    if (!(field in this.s.answers)) return;
    this.set((x) => {
      const answers = { ...x.answers };
      delete answers[field];
      return { answers, skipped: x.skipped.filter((f) => f !== field) };
    });
    void this.next();
  };

  hearAgain = () => {
    const st = this.s.step;
    const text = st.type === "ask" ? st.q.question : st.type === "confirm" ? st.readback : "";
    if (!text || !this.voice) return;
    this.run++;
    this.stopRecognition();
    this.stopSpeech();
    const token = this.run;
    const h = speak(text, this.voice);
    this.speech = h;
    this.note(`speak:"${text}" (again)`);
    this.set({ activity: "speaking" });
    void h.done.then(() => {
      if (token !== this.run) return;
      this.speech = null;
      if (this.s.mode === "voice" && !this.s.typing) this.listen();
      else this.set({ activity: "idle" });
    });
  };

  retry = () => void this.next();
}

export function useInterview(opts: { flow: VoiceFlow | null; language: string; initialAnswers?: VoiceAnswers; t: TFunction; onFlow?: (f: VoiceFlow) => void }) {
  const sdk = useSdk();
  const [engine] = useState(() => new InterviewEngine(sdk.voice, { t: opts.t, language: opts.language, onFlow: opts.onFlow }, opts.flow, opts.initialAnswers));
  const { t, language, onFlow } = opts;
  useEffect(() => {
    engine.setContext({ t, language, onFlow });
  }, [engine, t, language, onFlow]);
  useEffect(() => engine.stopAll, [engine]);

  // Development test hook: inject a final transcript; read the log and state.
  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;
    const w = window as unknown as { __vyVoice?: unknown };
    w.__vyVoice = { inject: engine.inject, state: engine.snapshot, log: engine.log, apiMode: () => sdk.voice.mode() };
    return () => {
      delete w.__vyVoice;
    };
  }, [engine, sdk]);

  const state = useSyncExternalStore(engine.subscribe, engine.snapshot, engine.snapshot);
  return { state, engine };
}

/** The first question when posting and the kind isn't chosen yet (answered here, not by the server). */
export function kindQuestion(t: TFunction): VoiceQuestion {
  return {
    done: false,
    field: KIND_FIELD,
    question: t("voice:kind.question"),
    hint: t("voice:kind.hint"),
    kind: "choice",
    options: POST_FLOWS.map((f) => ({ value: f, label: t(`voice:kind.${f}`) })),
    optional: false,
    progress: { asked: 0, total: 0 },
  };
}

function matchKind(text: string, t: TFunction): VoiceFlow | null {
  const said = text.toLowerCase();
  for (const f of POST_FLOWS) {
    const words = [t(`voice:kind.${f}`), ...String(t(`voice:kind.words.${f}`)).split(",")]
      .map((w) => w.trim().toLowerCase())
      .filter(Boolean);
    if (words.some((w) => said.includes(w))) return f;
  }
  return null;
}
