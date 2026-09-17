"use client";

/**
 * Signed-out arrival (TR21): one calm question at a time.
 * identifier -> code -> (new member) name + language -> signed in.
 * "Use a password instead" is the secondary path. Each answered question
 * collapses into a chip above the current one.
 */
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ApiError, identity, NetworkError, type CodeChallenge, type Lang, type Member } from "@/lib/api";
import { errorText, LANGUAGES, type Translate } from "@/lib/i18n";
import { ArrowIcon, CheckIcon, EyeIcon, EyeOffIcon, LockIcon, OrbCore } from "./ui";

type Step = "identifier" | "code" | "name" | "password";

type ArrivalProps = {
  t: Translate;
  lang: Lang;
  onLang: (lang: Lang) => void;
  returnModuleName: string | null;
  notice: string | null;
  onSignedIn: (member: Member) => void | Promise<void>;
};

/** Accepts a 10-digit Indian mobile, +E.164, or an email; returns what we send. */
export function normaliseIdentifier(raw: string): string | null {
  const value = raw.trim();
  if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) return value.toLowerCase();
  const compact = value.replace(/[\s()-]/g, "");
  if (/^[6-9]\d{9}$/.test(compact)) return compact;
  if (/^0[6-9]\d{9}$/.test(compact)) return compact.slice(1);
  if (/^91[6-9]\d{9}$/.test(compact)) return `+${compact}`;
  if (/^\+[1-9]\d{7,14}$/.test(compact)) return compact;
  return null;
}

const spring = { type: "spring" as const, stiffness: 380, damping: 34 };

export default function Arrival({ t, lang, onLang, returnModuleName, notice, onSignedIn }: ArrivalProps) {
  const [step, setStep] = useState<Step>("identifier");
  const [identifier, setIdentifier] = useState("");
  const [challenge, setChallenge] = useState<CodeChallenge | null>(null);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [resendAt, setResendAt] = useState(0);
  const [now, setNow] = useState(0);
  const [shake, setShake] = useState(0);

  const normalised = normaliseIdentifier(identifier);
  const questionRef = useRef<HTMLHeadingElement>(null);
  const firstStep = useRef(true);

  const question =
    step === "identifier"
      ? t("askIdentifier")
      : step === "code"
        ? t("askCode", { destination: challenge?.destination_hint ?? "" })
        : step === "name"
          ? t("askName")
          : t("askPassword");

  // Move focus to the new question's field so keyboard and screen-reader users follow the conversation.
  useEffect(() => {
    if (firstStep.current) {
      firstStep.current = false;
      return;
    }
    const frame = requestAnimationFrame(() => {
      document.querySelector<HTMLInputElement>("[data-step-field]")?.focus();
    });
    return () => cancelAnimationFrame(frame);
  }, [step]);

  // Resend countdown.
  useEffect(() => {
    if (step !== "code") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [step]);
  const resendSeconds = Math.max(0, Math.ceil((resendAt - now) / 1000));

  function fail(caught: unknown) {
    if (caught instanceof NetworkError) setError(t("err_network"));
    else if (caught instanceof ApiError) setError(errorText(t, caught.code, caught.retryAfter));
    else setError(t("err_unknown"));
    setShake((value) => value + 1);
  }

  async function requestCode(event?: FormEvent) {
    event?.preventDefault();
    if (!normalised || busy) {
      if (!normalised) setError(t("identifierInvalid"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await identity.requestCode(normalised);
      setChallenge(next);
      setCode("");
      const started = Date.now();
      setNow(started);
      setResendAt(started + next.resend_in * 1000);
      if (step === "code") setInfo(t("codeResent"));
      setStep("code");
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  async function verify(value: string) {
    if (!challenge || busy || value.length !== 6) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await identity.verifyCode(challenge.challenge_id, value);
      if (result.outcome === "signed_in") {
        await onSignedIn(result.member);
        return;
      }
      setStep("name");
    } catch (caught) {
      if (caught instanceof ApiError && (caught.code === "code_expired" || caught.code === "code_attempts_exhausted")) {
        setStep("identifier");
        setChallenge(null);
      }
      setCode("");
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  async function welcome(event: FormEvent) {
    event.preventDefault();
    const displayName = name.trim();
    if (!challenge || busy || !displayName) return;
    setBusy(true);
    setError(null);
    try {
      const result = await identity.welcome({
        challenge_id: challenge.challenge_id,
        code,
        display_name: displayName,
        preferred_language: lang,
      });
      await onSignedIn(result.member);
    } catch (caught) {
      if (caught instanceof ApiError && (caught.code === "code_expired" || caught.code === "code_attempts_exhausted" || caught.code === "code_invalid")) {
        setStep("identifier");
        setChallenge(null);
        setCode("");
      }
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  async function signInWithPassword(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!normalised) {
      setError(t("identifierInvalid"));
      return;
    }
    if (!password) return;
    setBusy(true);
    setError(null);
    try {
      const result = await identity.password(normalised, password);
      await onSignedIn(result.member);
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  function goTo(next: Step) {
    setError(null);
    setInfo(null);
    setStep(next);
  }

  const answered: { key: string; label: string; icon?: "check"; onChange?: () => void }[] = [];
  if (step === "code" || step === "name") {
    answered.push({ key: "id", label: challenge?.destination_hint ?? identifier, onChange: step === "code" ? () => goTo("identifier") : undefined });
  }
  if (step === "name") answered.push({ key: "code", label: "••••••", icon: "check" });

  return (
    <main id="main" className="arrival" tabIndex={-1}>
      <div className="arrival-stage">
        <div className="presence" style={{ viewTransitionName: "fk-orb" }}>
          <OrbCore className={busy ? "is-thinking" : ""} />
        </div>
        <p className="kicker">{returnModuleName ? t("continueTo", { module: returnModuleName }) : t("arrivalKicker")}</p>

        {notice && (
          <p className="notice" role="status">
            <CheckIcon size={18} /> {notice}
          </p>
        )}

        <ol className="thread" aria-label="">
          <AnimatePresence initial={false}>
            {answered.map((item) => (
              <motion.li
                key={item.key}
                layout
                className="thread-chip"
                initial={{ opacity: 0, y: 18, scale: 0.9, filter: "blur(6px)" }}
                animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={spring}
              >
                {item.icon === "check" ? <CheckIcon size={16} className="chip-check" /> : <LockIcon size={16} />}
                <span dir="ltr">{item.label}</span>
                {item.onChange && (
                  <button type="button" className="chip-action" onClick={item.onChange}>
                    {t("change")}
                  </button>
                )}
              </motion.li>
            ))}
          </AnimatePresence>
        </ol>

        <p className="sr-only" aria-live="polite">
          {t("stepAnnounce", { question })}
        </p>

        <AnimatePresence mode="wait" initial={false}>
          <motion.section
            key={step}
            className="ask"
            initial={{ opacity: 0, y: 24, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -16, filter: "blur(6px)" }}
            transition={{ duration: 0.36, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <h1 ref={questionRef} className="question">
              {question}
            </h1>

            {step === "identifier" && (
              <IdentifierForm
                t={t}
                value={identifier}
                onChange={(value) => {
                  setIdentifier(value);
                  setError(null);
                }}
                valid={!!normalised}
                busy={busy}
                onSubmit={requestCode}
              />
            )}

            {step === "code" && challenge && (
              <div className="code-step">
                <CodeField
                  t={t}
                  value={code}
                  shake={shake}
                  busy={busy}
                  onChange={(value) => {
                    setCode(value);
                    setError(null);
                    if (value.length === 6) void verify(value);
                  }}
                />
                {challenge.dev_code && (
                  <p className="dev-code">
                    <span className="dev-code-label">{t("devCode")}</span>
                    <code dir="ltr">{challenge.dev_code}</code>
                    <button
                      type="button"
                      className="chip-action"
                      onClick={() => {
                        setCode(challenge.dev_code!);
                        void verify(challenge.dev_code!);
                      }}
                    >
                      {t("devCodeFill")}
                    </button>
                  </p>
                )}
                <div className="code-meta">
                  {busy ? (
                    <span className="muted">{t("verifying")}</span>
                  ) : resendSeconds > 0 ? (
                    <span className="resend-wait">
                      <CountdownRing total={challenge.resend_in} remaining={resendSeconds} />
                      {t("resendIn", { seconds: resendSeconds })}
                    </span>
                  ) : (
                    <button type="button" className="link-btn" onClick={() => void requestCode()}>
                      {t("resendCode")}
                    </button>
                  )}
                </div>
              </div>
            )}

            {step === "name" && (
              <form className="stack" onSubmit={welcome}>
                <label className="field field-plain">
                  <span className="sr-only">{t("nameLabel")}</span>
                  <input
                    data-step-field
                    className="field-input"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder={t("namePlaceholder")}
                    autoComplete="name"
                    maxLength={80}
                    required
                  />
                </label>
                <fieldset className="lang-choice">
                  <legend className="field-legend">{t("languageLabel")}</legend>
                  <div className="segmented" role="radiogroup" aria-label={t("languageLabel")}>
                    {LANGUAGES.map((option) => (
                      <button
                        key={option.code}
                        type="button"
                        role="radio"
                        aria-checked={lang === option.code}
                        lang={option.code}
                        className="segment"
                        onClick={() => onLang(option.code)}
                      >
                        {option.native}
                      </button>
                    ))}
                  </div>
                </fieldset>
                <button type="submit" className="btn-primary" disabled={!name.trim() || busy}>
                  {busy ? t("verifying") : t("finish")}
                </button>
              </form>
            )}

            {step === "password" && (
              <form className="stack" onSubmit={signInWithPassword}>
                <label className="field field-plain">
                  <span className="sr-only">{t("identifierLabel")}</span>
                  <input
                    className="field-input"
                    value={identifier}
                    onChange={(event) => {
                      setIdentifier(event.target.value);
                      setError(null);
                    }}
                    placeholder={t("identifierPlaceholder")}
                    autoComplete="username"
                    inputMode="email"
                    dir="ltr"
                  />
                </label>
                <label className="field">
                  <span className="sr-only">{t("passwordLabel")}</span>
                  <input
                    data-step-field
                    className="field-input"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      setError(null);
                    }}
                    placeholder={t("passwordLabel")}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="field-aux"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                    aria-pressed={showPassword}
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </label>
                <button type="submit" className="btn-primary" disabled={!normalised || !password || busy}>
                  {busy ? t("verifying") : t("signIn")}
                </button>
              </form>
            )}
          </motion.section>
        </AnimatePresence>

        <div className="ask-feedback" aria-live="assertive">
          <AnimatePresence>
            {error && (
              <motion.p key={error} role="alert" className="error-text" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                {error}
              </motion.p>
            )}
          </AnimatePresence>
          {info && !error && (
            <p className="info-text" role="status">
              {info}
            </p>
          )}
        </div>

        <div className="arrival-secondary">
          {(step === "identifier" || step === "code") && (
            <button type="button" className="link-btn" onClick={() => goTo("password")}>
              {t("usePassword")}
            </button>
          )}
          {step === "password" && (
            <button type="button" className="link-btn" onClick={() => goTo("identifier")}>
              {t("useCode")}
            </button>
          )}
        </div>

        <p className="privacy-cue">
          <LockIcon size={15} /> {t("privacyNumber")}
        </p>
      </div>

      <p className="arrival-promise">{t("arrivalPromise")}</p>
    </main>
  );
}

function IdentifierForm({
  t,
  value,
  onChange,
  valid,
  busy,
  onSubmit,
}: {
  t: Translate;
  value: string;
  onChange: (value: string) => void;
  valid: boolean;
  busy: boolean;
  onSubmit: (event: FormEvent) => void;
}) {
  const hintId = useId();
  return (
    <form className="stack" onSubmit={onSubmit} noValidate>
      <label className="field">
        <span className="sr-only">{t("identifierLabel")}</span>
        <input
          data-step-field
          autoFocus
          className="field-input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={t("identifierPlaceholder")}
          autoComplete="username"
          inputMode="email"
          enterKeyHint="send"
          aria-describedby={hintId}
          dir="ltr"
        />
        <button type="submit" className="field-go" disabled={!valid || busy} aria-label={t("sendCode")}>
          {busy ? <span className="spinner" aria-hidden="true" /> : <ArrowIcon />}
        </button>
      </label>
      <p id={hintId} className="sr-only">
        {t("identifierInvalid")}
      </p>
    </form>
  );
}

function CodeField({
  t,
  value,
  onChange,
  shake,
  busy,
}: {
  t: Translate;
  value: string;
  onChange: (value: string) => void;
  shake: number;
  busy: boolean;
}) {
  const [focused, setFocused] = useState(true);
  return (
    <motion.div
      key={shake}
      className={`code-field ${busy ? "is-busy" : ""}`}
      animate={shake ? { x: [0, -10, 9, -6, 4, 0] } : undefined}
      transition={{ duration: 0.4 }}
    >
      <input
        data-step-field
        autoFocus
        className="code-input"
        value={value}
        onChange={(event) => onChange(event.target.value.replace(/\D/g, "").slice(0, 6))}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        inputMode="numeric"
        autoComplete="one-time-code"
        pattern="[0-9]*"
        maxLength={6}
        aria-label={t("codeLabel")}
        disabled={busy}
        dir="ltr"
      />
      <div className="code-cells" aria-hidden="true" dir="ltr">
        {Array.from({ length: 6 }, (_, index) => {
          const digit = value[index];
          const active = focused && !busy && index === Math.min(value.length, 5);
          return (
            <span key={index} className={`code-cell ${digit ? "is-filled" : ""} ${active ? "is-active" : ""}`}>
              {digit ? (
                <motion.span initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={spring}>
                  {digit}
                </motion.span>
              ) : null}
            </span>
          );
        })}
      </div>
    </motion.div>
  );
}

function CountdownRing({ total, remaining }: { total: number; remaining: number }) {
  const radius = 8;
  const circumference = 2 * Math.PI * radius;
  const progress = total > 0 ? remaining / total : 0;
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" className="countdown-ring">
      <circle cx="11" cy="11" r={radius} fill="none" stroke="var(--line-strong)" strokeWidth="2.2" />
      <circle
        cx="11"
        cy="11"
        r={radius}
        fill="none"
        stroke="var(--saffron)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - progress)}
        transform="rotate(-90 11 11)"
      />
    </svg>
  );
}
