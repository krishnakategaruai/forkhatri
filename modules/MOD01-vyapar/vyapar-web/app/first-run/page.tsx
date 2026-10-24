"use client";

// [Start flow 2026-10 — ONBOARDING-REDESIGN-2026-10.md, decisions 1–12,
// owner-accepted 2026-10-06] The 3-question start that replaced the five
// first-run steps: goal → trade(s) or need → area, then results. None of it
// is a sign-up/login/OTP screen (FR50: the member arrives authenticated).
//
//   [1] "Namaste Venkatesh, what do you want to do today?" Find work / Hire
//       someone / Get customers, the consent line and ONE "Agree and
//       continue" (FR53 asked once, at entry; decision 9). The date of birth
//       is asked here only when the identity does not know it (18+).
//   [2a] Find work: "What work do you do?" picture tiles + Other + search/mic.
//   [2b] Hire someone: straight to the AI composer (no profile wall).
//   [2c] Get customers: "What do you sell or offer?" tiles; business name
//        optional and suggested.
//   [3] "Where?" one field, any town accepted, nearby chips only when they
//       really are nearby. Radius and work mode are defaulted from the trade.
//   → POST /v1/first-run/start saves everything in one call and goes live
//     where the server rules allow; the member lands on results.
// Name, language and phone are never asked (identity). Voice completes the
// whole start (decision 7): the profile interview's answers are saved by the
// same call and the person lands on results, never back in a form.
// Traces to: FR44, FR53, FR04, FR01, TR044
import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
import { Briefcase, Check, Search, Store, type LucideIcon } from "lucide-react";
import type { FirstRunState, StartGoal, StartInput, StartOut } from "@/lib/sdk";
import { ApiError } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import DisabledReason from "@/app/components/DisabledReason";
import Steps from "@/app/components/account/Steps";
import LocalityField from "@/app/components/account/LocalityField";
import TradeTiles from "@/app/components/start/TradeTiles";
import VoiceEntry from "@/app/components/voice/VoiceEntry";
import VoiceInterview from "@/app/components/voice/VoiceInterview";
import { toProfile } from "@/app/components/voice/drafts";
import { useHost } from "@/app/host/HostProvider";
import "@/app/styles/account-2026.css";
import "@/app/styles/start-2026.css";

type Stage = "goal" | "trades" | "where" | "under18";
type LegalKind = "privacy" | "terms";

const GOALS: { id: StartGoal; icon: LucideIcon }[] = [
  { id: "find_work", icon: Search },
  { id: "hire", icon: Briefcase },
  { id: "get_customers", icon: Store },
];
const LEGAL: LegalKind[] = ["privacy", "terms"];

interface LegalDoc {
  kind: LegalKind;
  title: string;
  body: string;
  accepted: boolean;
}

function StartInner() {
  const { t, i18n } = useTranslation(["firstRun", "common", "listings", "voice", "hiring", "profile"]);
  const router = useRouter();
  const params = useSearchParams();
  const sdk = useSdk();
  const { platformLink } = useHost();

  const [state, setState] = useState<FirstRunState | null>(null);
  const [screen, setScreen] = useState<Stage>("goal");
  const [goal, setGoal] = useState<StartGoal | null>(null);
  const [dob, setDob] = useState("");
  const [legal, setLegal] = useState<LegalDoc[]>([]);
  const [readLegal, setReadLegal] = useState<LegalKind | null>(null);
  const [trades, setTrades] = useState<string[]>([]);
  const [others, setOthers] = useState<string[]>([]);
  const [businessName, setBusinessName] = useState("");
  const [locality, setLocality] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [talking, setTalking] = useState(false);

  // The hub's search ("ప్లంబర్ పని కావాలి") rides along to results.
  const q = params.get("q");

  useEffect(() => {
    sdk.firstRun
      .state()
      .then((s) => {
        setState(s);
        setLocality(s.locality ?? "");
        if (s.goal) setGoal(s.goal);
        // Decision 1: never shown to a member who already has a trade or a post.
        if (s.needs_start === false) router.replace(q ? `/?q=${encodeURIComponent(q)}` : "/");
      })
      .catch(() => setState(null));
    Promise.all(LEGAL.map((k) => sdk.client.get<LegalDoc>(`/v1/legal/${k}`).catch(() => null))).then((rows) =>
      setLegal(rows.filter((d): d is LegalDoc => !!d)),
    );
  }, [sdk, router, q, i18n.language]);

  const firstName = (state?.display_name ?? "").split(" ")[0] || "";
  const dobNeeded = state ? !state.date_of_birth_known : false;
  const dobOk = !dobNeeded || /^\d{4}-\d{2}-\d{2}$/.test(dob);
  const pendingLegal = legal.filter((d) => !d.accepted);
  const totalSteps = goal === "hire" ? 1 : 3;
  const stepIndex = screen === "goal" ? 1 : screen === "trades" ? 2 : 3;

  const stepTitle = useMemo(() => {
    if (screen === "goal") return t("firstRun:start.goal.step");
    if (screen === "trades") return goal === "get_customers" ? t("firstRun:start.trades.titleSell") : t("firstRun:start.trades.titleWork");
    return t("firstRun:start.where.step");
  }, [screen, goal, t]);

  async function acceptLegal() {
    for (const d of pendingLegal) await sdk.client.post(`/v1/legal/${d.kind}/accept`);
    if (pendingLegal.length) setLegal((rows) => rows.map((d) => ({ ...d, accepted: true })));
  }

  function land(out: StartOut) {
    if (!out.eligible || out.next === "under_18") {
      setScreen("under18");
      return;
    }
    if (out.next === "post") {
      router.replace("/opportunities/new?from=start");
      return;
    }
    const search = new URLSearchParams();
    search.set("welcome", out.next === "visible" ? "visible" : "work");
    if (!out.live) search.set("draft", out.publish_blocked ?? "review");
    if (q) search.set("q", q);
    router.replace(`/?${search.toString()}`);
  }

  async function submit(extra: Partial<StartInput> = {}) {
    if (!goal) return;
    setSaving(true);
    setError(null);
    try {
      await acceptLegal();
      const body: StartInput = {
        goal,
        capabilities: trades,
        capabilities_other: others,
        locality: locality.trim() || null,
        lat: coords?.lat ?? null,
        lng: coords?.lng ?? null,
        date_of_birth: dobNeeded ? dob : null,
        business_name: goal === "get_customers" ? businessName.trim() || null : null,
        ...extra,
      };
      land(await sdk.firstRun.start(body));
    } catch (e) {
      setError(e instanceof ApiError && typeof e.detail === "string" ? e.detail : t("common:state.somethingWentWrong"));
    } finally {
      setSaving(false);
    }
  }

  async function continueFromGoal() {
    if (!goal || !dobOk) return;
    if (goal === "hire") {
      await submit();
      return;
    }
    setError(null);
    try {
      setSaving(true);
      await acceptLegal();
    } catch {
      setError(t("common:state.somethingWentWrong"));
      return;
    } finally {
      setSaving(false);
    }
    setScreen("trades");
  }

  const goalReason = !goal ? t("firstRun:start.goal.reason") : !dobOk ? t("firstRun:start.goal.reasonDob") : null;
  const tradesReason = trades.length + others.length === 0 ? t("common:disabled.skills") : null;
  const whereReason = !locality.trim() ? t("common:disabled.area") : null;

  return (
    <Screen className="vy-shell-center vy-start-shell">
      {talking && (
        <VoiceInterview
          flow="profile"
          initialAnswers={{ ...(state?.display_name ? { name: state.display_name } : {}), ...(locality.trim() ? { locality: locality.trim() } : {}) }}
          title={t("voice:flowTitle.profile")}
          doneLabel={t("voice:doneLabel.start")}
          onClose={() => setTalking(false)}
          onDone={({ draft }) => {
            // Decision 7: everything the conversation learned is saved in the
            // one start call; the person lands on results, never on the form.
            setTalking(false);
            const v = toProfile(draft);
            if (!goal) setGoal("find_work");
            if (v.locality) setLocality(v.locality);
            void submit({
              goal: goal ?? "find_work",
              capabilities: Array.from(new Set([...trades, ...v.capabilities])),
              capabilities_other: Array.from(new Set([...others, ...(v.capabilitiesOther ? v.capabilitiesOther.split(",").map((s) => s.trim()).filter(Boolean) : [])])),
              locality: v.locality ?? (locality.trim() || null),
              experience_years: v.experienceYears,
              own_assets: v.ownAssets,
              headline: v.headline,
            });
          }}
        />
      )}

      {screen !== "under18" && <Steps step={stepIndex} total={totalSteps} label={stepTitle} stepLabel={t("firstRun:progress.label", { step: stepIndex, total: totalSteps })} />}

      <AnimatePresence mode="wait">
        {screen === "goal" && (
          <motion.div key="goal" {...fade} className="vy-start">
            <div className="vy-start-head">
              <h1>{firstName ? t("firstRun:start.goal.title", { name: firstName }) : t("firstRun:start.goal.titleNoName")}</h1>
              <p>{t("firstRun:start.goal.help")}</p>
            </div>
            <div className="vy-start-goals" role="radiogroup" aria-label={t("firstRun:start.goal.step")}>
              {GOALS.map((g) => {
                const on = goal === g.id;
                const Icon = g.icon;
                return (
                  <button key={g.id} type="button" role="radio" aria-checked={on} className="vy-card vy-acct-fr-option vy-start-goal" aria-pressed={on} onClick={() => setGoal(g.id)}>
                    <span className="vy-acct-tile" data-tint={on ? "brand" : undefined} aria-hidden="true">
                      <Icon size={20} strokeWidth={1.9} />
                    </span>
                    <strong>
                      {t(`firstRun:start.goal.options.${g.id}.title`)}
                      <small>{t(`firstRun:start.goal.options.${g.id}.hint`)}</small>
                    </strong>
                    <span className="vy-acct-fr-check" aria-hidden="true">
                      <Check size={14} strokeWidth={3} />
                    </span>
                  </button>
                );
              })}
            </div>

            {dobNeeded && (
              <div className="vy-acct-field">
                <label className="vy-label" htmlFor="start-dob">{t("firstRun:start.goal.dobLabel")}</label>
                <input id="start-dob" className="vy-input vy-num" type="date" value={dob} max={new Date().toISOString().slice(0, 10)} autoComplete="bday" onChange={(e) => setDob(e.target.value)} />
                <span className="vy-acct-hint">{t("firstRun:start.goal.dobHint")}</span>
              </div>
            )}

            <VoiceEntry variant="profile" onStart={() => setTalking(true)} compact />

            <p className="vy-start-consent">
              {t("firstRun:start.consent.line")}{" "}
              {legal.map((d, i) => (
                <span key={d.kind}>
                  {i > 0 && ` ${t("firstRun:start.consent.and")} `}
                  <button type="button" aria-expanded={readLegal === d.kind} onClick={() => setReadLegal((k) => (k === d.kind ? null : d.kind))}>
                    {d.title}
                  </button>
                </span>
              ))}
              {legal.length > 0 && "."}
            </p>
            {readLegal && <div className="vy-start-legal">{legal.find((d) => d.kind === readLegal)?.body}</div>}

            {error && <p className="vy-error" role="alert">{error}</p>}
            <div className="vy-start-actions">
              <button className="vy-btn vy-btn-primary" aria-describedby="start-reason-goal" disabled={!goal || !dobOk || saving} onClick={continueFromGoal}>
                {saving ? t("common:state.saving") : pendingLegal.length ? t("firstRun:start.consent.agreeContinue") : t("common:action.continue")}
              </button>
              <DisabledReason id="start-reason-goal" show={!!goalReason && !saving}>{goalReason ?? ""}</DisabledReason>
            </div>
          </motion.div>
        )}

        {screen === "trades" && goal && goal !== "hire" && (
          <motion.div key="trades" {...fade} className="vy-start">
            <div className="vy-start-head">
              <h1>{goal === "get_customers" ? t("firstRun:start.trades.titleSell") : t("firstRun:start.trades.titleWork")}</h1>
              <p>{t("firstRun:start.trades.help")}</p>
            </div>
            <TradeTiles goal={goal} selected={trades} onChange={setTrades} others={others} onOthers={setOthers} />
            {goal === "get_customers" && (
              <div className="vy-acct-field">
                <label className="vy-label" htmlFor="start-biz">
                  {t("listings:new.nameLabelBusiness")} <span className="vy-acct-field-optional">· {t("listings:new.optional")}</span>
                </label>
                <input id="start-biz" className="vy-input" value={businessName} maxLength={120} autoComplete="organization" onChange={(e) => setBusinessName(e.target.value)} placeholder={firstName ? t("firstRun:start.trades.businessPlaceholder", { name: firstName }) : t("listings:new.namePlaceholderBusiness")} />
                <span className="vy-acct-hint">{t("firstRun:start.trades.businessHint")}</span>
              </div>
            )}
            <div className="vy-start-actions">
              <button className="vy-btn vy-btn-primary" aria-describedby="start-reason-trades" disabled={!!tradesReason || saving} onClick={() => setScreen("where")}>
                {t("common:action.continue")}
              </button>
              <DisabledReason id="start-reason-trades" show={!!tradesReason}>{tradesReason ?? ""}</DisabledReason>
              <button type="button" className="vy-acct-quiet" style={{ alignSelf: "flex-start" }} onClick={() => setScreen("goal")}>
                ← {t("common:action.back")}
              </button>
            </div>
          </motion.div>
        )}

        {screen === "where" && (
          <motion.div key="where" {...fade} className="vy-start">
            <div className="vy-start-head">
              <h1>{goal === "get_customers" ? t("firstRun:start.where.titleSell") : t("firstRun:start.where.titleWork")}</h1>
              <p>{t("firstRun:start.where.help")}</p>
            </div>
            <LocalityField
              id="start-locality"
              value={locality}
              onChange={setLocality}
              onCoords={(lat, lng) => setCoords({ lat, lng })}
              label={t("firstRun:start.where.label")}
              placeholder={t("firstRun:start.where.placeholder")}
              useLocationLabel={t("firstRun:start.where.useLocation")}
            />
            {error && <p className="vy-error" role="alert">{error}</p>}
            <div className="vy-start-actions">
              <button className="vy-btn vy-btn-primary" aria-describedby="start-reason-where" disabled={!!whereReason || saving} onClick={() => void submit()}>
                {saving ? t("common:state.saving") : goal === "get_customers" ? t("firstRun:start.where.ctaSell") : t("firstRun:start.where.ctaWork")}
              </button>
              <DisabledReason id="start-reason-where" show={!!whereReason && !saving}>{whereReason ?? ""}</DisabledReason>
              <button type="button" className="vy-acct-quiet" style={{ alignSelf: "flex-start" }} disabled={saving} onClick={() => setScreen("trades")}>
                ← {t("common:action.back")}
              </button>
            </div>
          </motion.div>
        )}

        {screen === "under18" && (
          <motion.div key="under18" {...fade} className="vy-card vy-start-kind" role="status">
            <h1>{t("firstRun:start.under18.title", { name: firstName })}</h1>
            <p>{t("firstRun:start.under18.body")}</p>
            <p className="vy-acct-hint">{t("firstRun:start.under18.later")}</p>
            {platformLink && (
              <a className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", textDecoration: "none" }} href={platformLink.href}>
                {t(platformLink.labelKey as "profile:backToForKhatri")}
              </a>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Screen>
  );
}

export default function StartPage() {
  return (
    <Suspense fallback={null}>
      <StartInner />
    </Suspense>
  );
}

const fade = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -16 },
  transition: { type: "spring" as const, stiffness: 340, damping: 30 },
};
