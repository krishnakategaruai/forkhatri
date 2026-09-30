"use client";

// [Dev-only, not a business FR — explicitly allowed by the task brief since
// it selects an identity the platform would already have authenticated,
// never a login form] Small corner widget so the product owner / this
// session can switch between the 16 seeded members while testing every
// other FR's owner-scoped behaviour (a Draft only its owner can see, an
// enquiry only its two parties can see, etc.) without a real sign-in flow.
// Approach: fetches the seeded member list from GET /v1/dev/members once,
// stores the chosen id in localStorage (api.ts reads it on every request),
// and re-renders the whole app tree via a custom event on change rather
// than a page reload, keeping the switch instant.
// Traces to: task brief's "Choose dev member" instruction (not an FR)
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
// [IMP38 — Refactor C] Mounted only by the ForKhatri host (app/host/
// forkhatri.tsx) as its account control; the standalone host has none.
import { getDevMemberId, setDevMemberId, type DevMember } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { FlaskConical, House } from "lucide-react";
import { useHost } from "@/app/host/HostProvider";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";

function initials(name: string): string {
  const parts = name.replace(/^m_/, "").split(/[\s_]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

export default function DevMemberSwitcher() {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const [members, setMembers] = useState<DevMember[]>([]);
  const [current, setCurrent] = useState("m_krishna");
  const sdk = useSdk();
  const host = useHost();
  const ref = usePopoverDismiss(open, () => setOpen(false));

  useEffect(() => {
    queueMicrotask(() => setCurrent(getDevMemberId()));
    sdk.dev.members().then(setMembers).catch(() => setMembers([]));
  }, [sdk]);

  const currentMember = members.find((m) => m.id === current);

  // [Real bug found live by the product owner — "Alerts and name is being
  // missed up in UI"] this pill used to `position: fixed; right: 14`
  // independently of NotificationBell's own hand-guessed offset, so a
  // longer display name than the dev-seeded default pushed this pill
  // leftward and OVER the bell. Now sits inside layout.tsx's shared flex
  // row (no more of its own `position: fixed`); the name itself gets an
  // explicit max-width + ellipsis so even a very long real name can never
  // force the header wider than the viewport on a narrow phone.
  return (
    <div ref={ref} className="vy-menu-anchor" style={{ minWidth: 0 }}>
      {/* [Design language 2026-09-29] the avatar: initials in a circle,
          plus the first name on desktop; always the right-most item. The
          small flask marks it as the development member switcher. */}
      <button
        type="button"
        className="vy-avatar-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label={t("devTools.switcherLabel")}
        aria-expanded={open}
        title={currentMember?.display_name ?? current}
      >
        <span className="vy-avatar" aria-hidden="true">
          {initials(currentMember?.display_name ?? current)}
          <span className="vy-avatar-dev"><FlaskConical size={10} strokeWidth={2.25} /></span>
        </span>
        <span className="vy-avatar-name">{(currentMember?.display_name ?? current).split(" ")[0]}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            className="vy-popover vy-popover-end"
            style={{ width: 280, maxHeight: 420, overflowY: "auto" }}
          >
            {/* [2026-09-30, owner: "i can't go to ForKhatri homepage from
                mobile view of Vyapar"] the way back to the platform, first
                in the account menu, from the host adapter (no URL here). */}
            {host.platformLink && (
              <a className="vy-menu-item vy-menu-home" href={host.platformLink.href}>
                <span className="vy-row" style={{ gap: 10 }}>
                  <House size={18} strokeWidth={1.9} aria-hidden="true" />
                  {t("shell.platformHome", { name: host.brand.qualifier ?? "" })}
                </span>
              </a>
            )}
            <p className="vy-muted" style={{ margin: "8px 0" }}>
              {t("devTools.notSignIn")}
            </p>
            <div className="vy-stack" style={{ gap: 2 }}>
              {members.map((m) => (
                <button
                  key={m.id}
                  className="vy-btn vy-btn-ghost"
                  style={{
                    justifyContent: "flex-start",
                    textAlign: "left",
                    background: m.id === current ? "var(--selected-bg)" : "transparent",
                    color: m.id === current ? "var(--selected-fg)" : "var(--text-primary)",
                  }}
                  onClick={() => {
                    setDevMemberId(m.id);
                    setCurrent(m.id);
                    setOpen(false);
                  }}
                >
                  {m.display_name}
                  <span className="vy-muted" style={{ marginLeft: "auto" }}>
                    {m.is_operator ? t("devTools.operator") : m.locality ?? "—"}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
