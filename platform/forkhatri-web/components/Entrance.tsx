"use client";

/**
 * ForKhatri web entrance: the single front door (07-tech-reqs.md TR21).
 *
 *   boot ──► signedOut (Arrival) ──sign in──► return_to (TR17) or signedIn (Hub)
 *     └───► offline (identity service unreachable, TR05)
 *
 * The session is an HttpOnly cookie owned by the Identity & Trust Service; this
 * component only ever asks `GET /v1/session` whether one exists.
 */
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, identity, NetworkError, orderModules, type Lang, type Member, type ModuleEntry } from "@/lib/api";
import { errorText, langFromNavigator, LANGUAGES, translator, type Translate } from "@/lib/i18n";
import { clearReturnTo, isBounceLoop, markBounce, moduleForTarget, readReturnTo, safeReturnTo } from "@/lib/return-to";
import { loadCachedRegistry, loadStoredLang, saveCachedRegistry, saveStoredLang } from "@/lib/storage";
import { useThemeSync } from "@/lib/theme";
import { withViewTransition } from "@/lib/view-transition";
import AccountSheet from "./AccountSheet";
import Arrival from "./Arrival";
import Hub, { EnteringOverlay, HubSkeleton } from "./Hub";
import Offline from "./Offline";
import Sheet from "./Sheet";
import { Aurora, Avatar, BellIcon, CheckIcon, OrbCore, Wordmark } from "./ui";

/**
 * DEVELOPMENT ONLY: the "Act as" member switcher (07-tech-reqs.md "Development tools").
 * NODE_ENV is inlined by the compiler, so a production build folds this to `null`
 * and never bundles ./dev/DevActAs, even if NEXT_PUBLIC_DEV_TOOLS is set.
 */
const DevActAs =
  process.env.NODE_ENV !== "production" && process.env.NEXT_PUBLIC_DEV_TOOLS === "true"
    ? dynamic(() => import("./dev/DevActAs"), { ssr: false })
    : null;

type Phase =
  | { kind: "boot" }
  | { kind: "offline" }
  | { kind: "signedOut" }
  | { kind: "signedIn"; member: Member }
  | { kind: "redirecting" };

type SheetKind = "account" | "notifications";
type Toast = { id: number; text: string; tone: "info" | "error" };

async function fetchRegistry(lang: Lang): Promise<{ modules: ModuleEntry[]; stale: boolean }> {
  try {
    const modules = orderModules(await identity.modules(lang));
    saveCachedRegistry(modules);
    return { modules, stale: false };
  } catch {
    const cached = loadCachedRegistry();
    return { modules: cached ? orderModules(cached) : [], stale: true };
  }
}

function describeError(t: Translate, error: unknown): string {
  if (error instanceof NetworkError) return t("err_network");
  if (error instanceof ApiError) return errorText(t, error.code, error.retryAfter);
  return t("err_unknown");
}

export default function Entrance({ initialSheet }: { initialSheet?: SheetKind }) {
  const [phase, setPhase] = useState<Phase>({ kind: "boot" });
  const [lang, setLang] = useState<Lang>("en");
  const [modules, setModules] = useState<ModuleEntry[]>([]);
  const [stale, setStale] = useState(false);
  const [sheet, setSheet] = useState<SheetKind | null>(null);
  const [entering, setEntering] = useState<ModuleEntry | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [returnModuleName, setReturnModuleName] = useState<string | null>(null);
  const toastTimer = useRef<number | undefined>(undefined);

  const t = useMemo(() => translator(lang), [lang]);
  const member = phase.kind === "signedIn" ? phase.member : null;
  const arrivalLook = phase.kind === "signedOut" || phase.kind === "offline" || phase.kind === "redirecting";
  // Device appearance preference applies everywhere (sign-in screens included) once chosen.
  useThemeSync();

  const showToast = useCallback((text: string, tone: Toast["tone"] = "info") => {
    window.clearTimeout(toastTimer.current);
    setToast({ id: Date.now(), text, tone });
    toastTimer.current = window.setTimeout(() => setToast(null), 5000);
  }, []);

  const boot = useCallback(async () => {
    const fallbackLang = loadStoredLang() ?? langFromNavigator();
    try {
      const session = await identity.session();
      const nextLang = session?.member.preferred_language ?? fallbackLang;
      const registry = await fetchRegistry(nextLang);
      const rawReturn = readReturnTo();
      const target = safeReturnTo(rawReturn, registry.modules);

      if (session && target && !isBounceLoop(target)) {
        markBounce(target);
        setPhase({ kind: "redirecting" });
        window.location.assign(target.href);
        return;
      }
      if (session || (rawReturn && !target)) clearReturnTo();

      withViewTransition(() => {
        setLang(nextLang);
        setModules(registry.modules);
        setStale(registry.stale);
        if (session) {
          setPhase({ kind: "signedIn", member: session.member });
          if (initialSheet) setSheet(initialSheet);
        } else {
          setReturnModuleName(target ? (moduleForTarget(target, registry.modules)?.name ?? null) : null);
          setPhase({ kind: "signedOut" });
        }
      });
    } catch {
      // Unreachable or unhealthy identity service: calm offline state, last good registry dimmed.
      const cached = loadCachedRegistry();
      withViewTransition(() => {
        setLang(fallbackLang);
        setModules(cached ? orderModules(cached) : []);
        setStale(true);
        setPhase({ kind: "offline" });
      });
    } finally {
      setRetrying(false);
    }
  }, [initialSheet]);

  // Boot resolves asynchronously against the identity service (an external system).
  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(() => {
      if (!cancelled) void boot();
    });
    return () => {
      cancelled = true;
    };
  }, [boot]);

  // Every screen change starts at the top (the hub used to open part-way down after sign-in).
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [phase.kind]);

  // The header is always opaque; a hairline appears once content scrolls beneath it.
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    if ("scrollRestoration" in window.history) window.history.scrollRestoration = "manual";
    const onScroll = () => setScrolled(window.scrollY > 4);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Keep <html lang> in step with the interface language (screen readers, hyphenation, fonts).
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Back from a module restores this page from the bfcache: drop the "Entering…" veil.
  useEffect(() => {
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) setEntering(null);
    };
    window.addEventListener("pageshow", onPageShow);
    return () => window.removeEventListener("pageshow", onPageShow);
  }, []);

  // Reconnect automatically when the device comes back online.
  useEffect(() => {
    if (phase.kind !== "offline") return;
    const onOnline = () => {
      setRetrying(true);
      void boot();
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [phase.kind, boot]);

  const sessionEnded = useCallback(
    (message: string | null) => {
      withViewTransition(() => {
        setSheet(null);
        setEntering(null);
        setNotice(message);
        setPhase({ kind: "signedOut" });
      });
      void fetchRegistry(lang).then((registry) => {
        setModules(registry.modules);
        setStale(registry.stale);
      });
    },
    [lang],
  );

  const onSignedIn = useCallback(
    async (signedIn: Member) => {
      const nextLang = signedIn.preferred_language;
      const registry = await fetchRegistry(nextLang);
      const target = safeReturnTo(readReturnTo(), registry.modules);
      if (target) {
        markBounce(target);
        setPhase({ kind: "redirecting" });
        window.location.assign(target.href);
        return;
      }
      clearReturnTo();
      saveStoredLang(nextLang);
      withViewTransition(() => {
        setLang(nextLang);
        setModules(registry.modules);
        setStale(registry.stale);
        setNotice(null);
        setPhase({ kind: "signedIn", member: signedIn });
        if (initialSheet) setSheet(initialSheet);
      });
    },
    [initialSheet],
  );

  const changeLang = useCallback(
    (next: Lang) => {
      if (next === lang) return;
      const previous = lang;
      setLang(next);
      saveStoredLang(next);
      if (!member) return;
      // Optimistic: the interface switches now, the member record follows.
      setPhase({ kind: "signedIn", member: { ...member, preferred_language: next } });
      identity
        .updateMe({ preferred_language: next })
        .then((updated) => {
          setPhase((current) => (current.kind === "signedIn" ? { kind: "signedIn", member: updated } : current));
          // Taglines follow the member's stored language, so refetch only once the PATCH has landed.
          return fetchRegistry(next).then((registry) => {
            setModules(registry.modules);
            setStale(registry.stale);
          });
        })
        .catch((error) => {
          if (error instanceof ApiError && error.code === "not_signed_in") {
            sessionEnded(translator(next)("err_not_signed_in"));
            return;
          }
          setLang(previous);
          saveStoredLang(previous);
          setPhase((current) => (current.kind === "signedIn" ? { kind: "signedIn", member: { ...current.member, preferred_language: previous } } : current));
          showToast(describeError(translator(previous), error), "error");
        });
    },
    [lang, member, sessionEnded, showToast],
  );

  const updateMember = useCallback(
    async (patch: Partial<Pick<Member, "display_name">>) => {
      try {
        const updated = await identity.updateMe(patch);
        setPhase((current) => (current.kind === "signedIn" ? { kind: "signedIn", member: updated } : current));
        return updated;
      } catch (error) {
        if (error instanceof ApiError && error.code === "not_signed_in") sessionEnded(t("err_not_signed_in"));
        throw error;
      }
    },
    [sessionEnded, t],
  );

  const signOut = useCallback(
    async (everywhere: boolean) => {
      try {
        await identity.signOut(everywhere);
      } catch (error) {
        // Already signed out on the server is still a successful sign-out here.
        if (!(error instanceof ApiError && error.status === 401)) {
          showToast(describeError(t, error), "error");
          return;
        }
      }
      sessionEnded(t("signedOut"));
    },
    [sessionEnded, showToast, t],
  );

  const enter = useCallback(
    async (module: ModuleEntry) => {
      if (entering || module.availability !== "available") return;
      withViewTransition(() => setEntering(module));
      try {
        const { entry_url } = await identity.enter(module.key);
        window.location.assign(entry_url);
      } catch (error) {
        setEntering(null);
        if (error instanceof ApiError && error.code === "not_signed_in") {
          sessionEnded(t("err_not_signed_in"));
          return;
        }
        showToast(
          error instanceof ApiError && error.code.startsWith("http_") ? t("enterFailed", { module: module.name }) : describeError(t, error),
          "error",
        );
      }
    },
    [entering, sessionEnded, showToast, t],
  );

  const closeSheet = useCallback(() => {
    setSheet(null);
    if (window.location.pathname === "/account") window.history.replaceState(null, "", "/");
  }, []);

  const openSheet = (kind: SheetKind) => setSheet(kind);

  return (
    <MotionConfig reducedMotion="user">
      {/* Signed-out screens keep the owner-approved luminous look; only the signed-in hub is minimalist. */}
      <div className="app" data-phase={phase.kind} data-look={arrivalLook ? "arrival" : "hub"} data-scrolled={scrolled}>
        {arrivalLook && <Aurora />}
        <a href="#main" className="skip-link">
          {t("skipToContent")}
        </a>
        <header className="topbar">
          <Link href="/" className="wordmark-link" aria-label="ForKhatri">
            <Wordmark luminous={arrivalLook} />
          </Link>
          <div className="topbar-actions">
            {member ? (
              <>
                <button
                  type="button"
                  className="icon-btn"
                  aria-label={t("notifications")}
                  aria-haspopup="dialog"
                  aria-expanded={sheet === "notifications"}
                  onClick={() => openSheet("notifications")}
                >
                  <BellIcon />
                </button>
                <button
                  type="button"
                  className="avatar-btn"
                  aria-label={t("openAccount", { name: member.display_name })}
                  aria-haspopup="dialog"
                  aria-expanded={sheet === "account"}
                  onClick={() => openSheet("account")}
                >
                  <Avatar name={member.display_name} />
                </button>
              </>
            ) : phase.kind === "boot" || phase.kind === "redirecting" ? (
              <span className="skeleton sk-actions" aria-hidden="true" />
            ) : (
              <div className="lang-switch" role="group" aria-label={t("languageLabel")}>
                {LANGUAGES.map((option) => (
                  <button
                    key={option.code}
                    type="button"
                    lang={option.code}
                    aria-pressed={lang === option.code}
                    aria-label={option.native}
                    onClick={() => changeLang(option.code)}
                  >
                    {option.code === "en" ? "EN" : option.native.slice(0, option.code === "hi" ? 2 : 2)}
                  </button>
                ))}
              </div>
            )}
          </div>
        </header>

        {phase.kind === "boot" && <HubSkeleton label={t("loadingLabel")} />}

        {phase.kind === "redirecting" && (
          <main id="main" className="redirecting" aria-busy="true">
            <span className="presence">
              <OrbCore className="is-thinking" />
            </span>
            <span className="sr-only">{t("loadingLabel")}</span>
          </main>
        )}

        {phase.kind === "offline" && (
          <Offline
            t={t}
            cached={modules.length ? modules : null}
            retrying={retrying}
            onRetry={() => {
              setRetrying(true);
              void boot();
            }}
          />
        )}

        {phase.kind === "signedOut" && (
          <Arrival t={t} lang={lang} onLang={changeLang} returnModuleName={returnModuleName} notice={notice} onSignedIn={onSignedIn} />
        )}
        {phase.kind === "signedOut" && DevActAs && <DevActAs lang={lang} currentMemberId={null} variant="arrival" />}

        {member && (
          <>
            <Hub
              t={t}
              lang={lang}
              member={member}
              modules={modules}
              stale={stale}
              onEnter={(module) => void enter(module)}
            />

            <Sheet open={sheet === "notifications"} onClose={closeSheet} title={t("notifications")} closeLabel={t("close")}>
              {/* No notification service exists yet: an honest empty state, nothing invented. */}
              <div className="empty-state">
                <span className="empty-orb" aria-hidden="true">
                  <CheckIcon size={26} />
                </span>
                <p className="empty-title">{t("notificationsEmptyTitle")}</p>
                <p className="empty-body">{t("notificationsEmptyBody")}</p>
              </div>
            </Sheet>

            <Sheet open={sheet === "account"} onClose={closeSheet} title={t("accountTitle")} closeLabel={t("close")}>
              <AccountSheet t={t} lang={lang} member={member} onLang={changeLang} onUpdate={updateMember} onSignOut={signOut} />
              {DevActAs && <DevActAs lang={lang} currentMemberId={member.member_id} variant="sheet" />}
            </Sheet>
          </>
        )}

        {entering && <EnteringOverlay t={t} module={entering} />}

        <div className="toast-region" aria-live="polite">
          <AnimatePresence>
            {toast && (
              <motion.p
                key={toast.id}
                className="toast"
                data-tone={toast.tone}
                role={toast.tone === "error" ? "alert" : "status"}
                initial={{ opacity: 0, y: -14, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ type: "spring", stiffness: 420, damping: 32 }}
              >
                {toast.text}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </MotionConfig>
  );
}
