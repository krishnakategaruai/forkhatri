"use client";

// ======================================================================
// [Voice interview 2026-09-30] The full-screen conversation view.
//
// Owner: "Voice should like, we ask questions in their perspective and
// waits until we receive answer!" One calm column (phone first, centred on
// desktop): the current question in large type, a small hint, a quiet
// progress bar ("3 of 7"), and one big round mic that shows whether we are
// speaking, listening or thinking. Confirmed answers stack above as small
// chips; tapping one asks that question again. Typing is always one tap away
// and is the whole conversation when the browser cannot listen.
//
// The engine (useInterview.ts) owns the loop; this file only draws it.
// On done: a summary card (tap any line to change it), then the caller's
// normal review screen, prefilled with the server's draft. Nothing is
// published from here.
// Styles: app/styles/voice-2026.css (imported from app/layout.tsx).
// ======================================================================

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Check, Keyboard, Mic, Pencil, Volume2, X } from "lucide-react";
import type { VoiceAnswers, VoiceDone, VoiceFlow } from "@/lib/sdk";
import { useVoiceSupported } from "@/app/components/VoiceInput";
import { useInterview, type InterviewState } from "./useInterview";

export interface VoiceInterviewProps {
  /** null while posting and the kind isn't chosen: the first question asks it. */
  flow: VoiceFlow | null;
  /** What the app already knows (never asked again). */
  initialAnswers?: VoiceAnswers;
  /** Heading of the conversation, e.g. "Post by talking". */
  title: string;
  /** The final button on the summary, e.g. "Continue to check". */
  doneLabel: string;
  onFlow?: (flow: VoiceFlow) => void;
  onDone: (result: { flow: VoiceFlow; draft: VoiceDone["draft"]; answers: VoiceAnswers }) => void;
  onClose: () => void;
}

export default function VoiceInterview(p: VoiceInterviewProps) {
  const { t, i18n } = useTranslation(["voice", "common"]);
  const { state: s, engine } = useInterview({ flow: p.flow, language: i18n.language, initialAnswers: p.initialAnswers, t, onFlow: p.onFlow });
  const titleId = useId();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [typed, setTyped] = useState("");
  const canListen = useVoiceSupported();

  const stepKey = s.step.type === "ask" || s.step.type === "confirm" ? `${s.step.type}:${s.step.q.field}` : s.step.type;
  // A new question takes focus (keyboard and screen-reader users land on it).
  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true });
  }, [stepKey]);
  useEffect(() => {
    if (s.typing) inputRef.current?.focus();
  }, [s.typing, stepKey]);

  const { onClose } = p;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        engine.stopAll();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [engine, onClose]);

  function close() {
    engine.stopAll();
    p.onClose();
  }

  function submitTyped(e: FormEvent) {
    e.preventDefault();
    if (!typed.trim()) return;
    engine.answerTyped(typed);
    setTyped("");
  }

  const step = s.step;
  const q = step.type === "ask" || step.type === "confirm" ? step.q : null;
  const inTurn = q !== null;
  const busy = s.activity === "thinking" || s.activity === "loading";
  const langName = t(`voice:langName.${i18n.language === "hi" || i18n.language === "te" ? i18n.language : "en"}`);
  // progress.asked is the current question's number (1-based); total counts
  // only what this interview asks (known things are not counted).
  const progress = q && q.progress.total > 0 ? q.progress : null;
  const live = step.type === "ask" ? step.q.question : step.type === "confirm" ? step.readback : step.type === "summary" ? t("voice:summary.title") : "";

  return (
    <div className="vy-talk" role="dialog" aria-modal="true" aria-labelledby={titleId} data-activity={s.activity}>
      <header className="vy-talk-top">
        <button type="button" className="vy-talk-close" onClick={close} aria-label={t("voice:talk.close")}>
          <X size={22} aria-hidden="true" />
        </button>
        <span id={titleId} className="vy-talk-title">
          {p.title}
        </span>
        {progress ? (
          <span className="vy-talk-count vy-num">{t("voice:talk.progress", { current: Math.min(Math.max(progress.asked, 1), progress.total), total: progress.total })}</span>
        ) : (
          <span className="vy-talk-count" aria-hidden="true" />
        )}
      </header>
      {progress && (
        <div className="vy-talk-bar" aria-hidden="true">
          <span style={{ width: `${Math.round((Math.max(progress.asked - 1, 0) / progress.total) * 100)}%` }} />
        </div>
      )}

      {/* Screen readers hear each question and readback once. */}
      <div className="vy-visually-hidden" aria-live="polite" aria-atomic="true">
        {live}
      </div>

      <div className="vy-talk-body">
        {inTurn && s.history.length > 0 && (
          <ul className="vy-talk-chips" aria-label={t("voice:talk.yourAnswers")}>
            {s.history.map((h) => (
              <li key={h.q.field}>
                <button
                  type="button"
                  className="vy-talk-chip"
                  aria-current={q?.field === h.q.field ? "step" : undefined}
                  onClick={() => engine.edit(h.q.field)}
                  aria-label={t("voice:talk.changeAnswer", { question: h.q.question, answer: h.label })}
                  title={h.q.question}
                >
                  <Check size={14} aria-hidden="true" />
                  <span>{h.label}</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {step.type === "intro" && <Intro s={s} canListen={canListen} langName={langName} onStart={engine.start} />}

        {step.type === "ask" && (
          <section className="vy-talk-turn">
            <h2 ref={headingRef} tabIndex={-1} className="vy-talk-question">
              {step.q.question}
            </h2>
            {step.q.hint && <p className="vy-talk-hint">{step.q.hint}</p>}
            {s.note && s.note !== step.q.question && <p className="vy-talk-note">{s.note}</p>}
            <Heard s={s} />
            {step.q.kind === "choice" && step.q.options && (
              <div className="vy-talk-options" role="group" aria-label={step.q.question}>
                {step.q.options.map((o) => (
                  <button key={o.value} type="button" className="vy-talk-option" disabled={busy} onClick={() => engine.choose(o.value)}>
                    {o.label}
                  </button>
                ))}
              </div>
            )}
            {step.q.kind === "yesno" && (
              <div className="vy-talk-options" role="group" aria-label={step.q.question}>
                <button type="button" className="vy-talk-option" disabled={busy} onClick={() => engine.answerTyped(t("voice:talk.yes"))}>
                  {t("voice:talk.yes")}
                </button>
                <button type="button" className="vy-talk-option" disabled={busy} onClick={() => engine.answerTyped(t("voice:talk.no"))}>
                  {t("voice:talk.no")}
                </button>
              </div>
            )}
            {step.q.optional && (
              <button type="button" className="vy-talk-quiet" disabled={busy} onClick={engine.skip}>
                {t("voice:talk.skip")}
              </button>
            )}
          </section>
        )}

        {step.type === "confirm" && (
          <section className="vy-talk-turn">
            <p className="vy-talk-context">{step.q.question}</p>
            <h2 ref={headingRef} tabIndex={-1} className="vy-talk-readback">
              {step.readback}
            </h2>
            {s.note && <p className="vy-talk-note">{s.note}</p>}
            <Heard s={s} />
            <div className="vy-talk-confirm">
              <button type="button" className="vy-btn vy-btn-primary vy-talk-yes" disabled={busy} onClick={engine.yes}>
                <Check size={20} aria-hidden="true" /> {t("voice:talk.yes")}
              </button>
              <button type="button" className="vy-btn vy-btn-secondary vy-talk-change" disabled={busy} onClick={engine.change}>
                <Pencil size={18} aria-hidden="true" /> {t("voice:talk.change")}
              </button>
            </div>
          </section>
        )}

        {inTurn && s.typing && step.type === "ask" && (
          <form className="vy-talk-type" onSubmit={submitTyped}>
            <label className="vy-visually-hidden" htmlFor={`${titleId}-typed`}>
              {step.q.question}
            </label>
            <input
              ref={inputRef}
              id={`${titleId}-typed`}
              className="vy-input"
              value={typed}
              inputMode={step.q.kind === "number" ? "numeric" : undefined}
              onChange={(e) => setTyped(e.target.value)}
              placeholder={t("voice:talk.typePlaceholder")}
              autoComplete="off"
            />
            <button type="submit" className="vy-btn vy-btn-primary" disabled={!typed.trim() || busy}>
              {busy ? t("voice:talk.thinking") : t("voice:talk.send")}
            </button>
          </form>
        )}

        {inTurn && s.mode === "typing" && (
          <div className="vy-talk-typing-notes">
            {s.typingReason && s.typingReason !== "chosen" && <p className="vy-talk-hint">{t(`voice:typingReason.${s.typingReason}`)}</p>}
            <div className="vy-talk-row">
              {!s.voiceMissing && (
                <button type="button" className="vy-talk-quiet" onClick={engine.hearAgain} disabled={busy}>
                  <Volume2 size={18} aria-hidden="true" /> {t("voice:talk.hearIt")}
                </button>
              )}
              {canListen && s.typingReason === "chosen" && (
                <button type="button" className="vy-talk-quiet" onClick={engine.switchToVoice}>
                  <Mic size={18} aria-hidden="true" /> {t("voice:talk.answerByVoice")}
                </button>
              )}
            </div>
          </div>
        )}

        {inTurn && s.mode === "voice" && s.voiceMissing && s.history.length === 0 && <p className="vy-talk-fine vy-talk-novoice">{t("voice:talk.noVoice", { language: langName })}</p>}

        {step.type === "summary" && (
          <section className="vy-talk-summary">
            <h2 ref={headingRef} tabIndex={-1} className="vy-talk-question">
              {t("voice:summary.title")}
            </h2>
            <ul className="vy-talk-list">
              {step.done.summary.map((row) => {
                const editable = row.field in s.answers;
                return (
                  <li key={row.field}>
                    {editable ? (
                      <button type="button" className="vy-talk-line" onClick={() => engine.edit(row.field)} aria-label={t("voice:summary.change", { label: row.label, value: row.value_label })}>
                        <span className="vy-talk-line-label">{row.label}</span>
                        <span className="vy-talk-line-value">{row.value_label}</span>
                        <Pencil size={16} aria-hidden="true" />
                      </button>
                    ) : (
                      <div className="vy-talk-line">
                        <span className="vy-talk-line-label">{row.label}</span>
                        <span className="vy-talk-line-value">{row.value_label}</span>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="vy-talk-hint">{s.flow === "profile" ? t("voice:summary.nothingSaved") : t("voice:summary.nothingPosted")}</p>
            <button
              type="button"
              className="vy-btn vy-btn-primary vy-talk-done"
              onClick={() => {
                engine.stopAll();
                p.onDone({ flow: s.flow!, draft: step.done.draft, answers: s.answers });
              }}
            >
              {p.doneLabel}
            </button>
          </section>
        )}

        {step.type === "error" && (
          <section className="vy-talk-turn">
            <h2 ref={headingRef} tabIndex={-1} className="vy-talk-question">
              {t("voice:talk.errorTitle")}
            </h2>
            <p className="vy-talk-hint">{t("voice:talk.errorBody")}</p>
            <button type="button" className="vy-btn vy-btn-primary" onClick={engine.retry}>
              {t("voice:talk.tryAgain")}
            </button>
          </section>
        )}
      </div>

      {inTurn && s.mode === "voice" && (
        <footer className="vy-talk-dock">
          {!s.typing && (
            <>
              <button
                type="button"
                className="vy-talk-mic"
                data-state={s.waitingTap ? "waiting" : s.activity}
                onClick={engine.tapMic}
                disabled={busy}
                aria-label={micLabel(s, t)}
              >
                <MicFace activity={s.activity} />
              </button>
              <span className="vy-talk-mic-label" aria-hidden="true">
                {micLabel(s, t)}
              </span>
            </>
          )}
          <button type="button" className="vy-talk-quiet" onClick={s.typing ? engine.closeTyping : engine.openTyping}>
            {s.typing ? <Mic size={18} aria-hidden="true" /> : <Keyboard size={18} aria-hidden="true" />}
            {s.typing ? t("voice:talk.speakInstead") : t("voice:talk.typeInstead")}
          </button>
        </footer>
      )}
    </div>
  );
}

function micLabel(s: InterviewState, t: (k: string) => string): string {
  if (s.waitingTap) return t("voice:mic.waiting");
  switch (s.activity) {
    case "speaking":
      return t("voice:mic.speaking");
    case "listening":
      return t("voice:mic.listening");
    case "thinking":
    case "loading":
      return t("voice:mic.thinking");
    default:
      return t("voice:mic.idle");
  }
}

function Heard({ s }: { s: InterviewState }) {
  const { t } = useTranslation("voice");
  if (s.activity === "listening") {
    return (
      <p className="vy-talk-live" aria-hidden="true">
        {s.interim || <span className="vy-talk-live-wait">{s.step.type === "confirm" ? t("voice:talk.listeningConfirm") : t("voice:talk.listeningHint")}</span>}
      </p>
    );
  }
  if (s.activity === "thinking" && s.heard) return <p className="vy-talk-live">“{s.heard}”</p>;
  return null;
}

function MicFace({ activity }: { activity: InterviewState["activity"] }) {
  if (activity === "speaking") {
    return (
      <span className="vy-talk-wave" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </span>
    );
  }
  if (activity === "thinking" || activity === "loading") {
    return (
      <span className="vy-talk-dots" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
    );
  }
  return <Mic size={34} aria-hidden="true" />;
}

function Intro({ s, canListen, langName, onStart }: { s: InterviewState; canListen: boolean; langName: string; onStart: (typing?: boolean) => void }) {
  const { t } = useTranslation("voice");
  const starting = s.activity === "loading";
  return (
    <section className="vy-talk-intro">
      <span className="vy-talk-intro-icon" aria-hidden="true">
        <Mic size={34} />
      </span>
      <h2 className="vy-talk-question">{t("voice:intro.title")}</h2>
      <p className="vy-talk-lead">{t("voice:intro.body", { language: langName })}</p>
      {starting && canListen && s.mode === "voice" ? (
        <p className="vy-talk-note" role="status">{t("voice:intro.waitingForMic")}</p>
      ) : canListen ? <p className="vy-talk-hint">{t("voice:intro.micNote")}</p> : <p className="vy-talk-hint">{t("voice:typingReason.unsupported")}</p>}
      <div className="vy-talk-intro-actions">
        <button type="button" className="vy-btn vy-btn-primary vy-talk-start" disabled={starting} onClick={() => onStart(false)}>
          {canListen ? <Mic size={20} aria-hidden="true" /> : null}
          {starting ? t("voice:mic.thinking") : canListen ? t("voice:intro.start") : t("voice:intro.startTyping")}
        </button>
        {canListen && (
          <button type="button" className="vy-talk-quiet" onClick={() => onStart(true)}>
            <Keyboard size={18} aria-hidden="true" /> {t("voice:intro.rather")}
          </button>
        )}
      </div>
      <p className="vy-talk-fine">{t("voice:intro.nothingPosted")}</p>
    </section>
  );
}
