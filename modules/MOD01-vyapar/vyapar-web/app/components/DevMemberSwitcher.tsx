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
import { api, getDevMemberId, setDevMemberId } from "@/lib/api";

interface DevMember {
  id: string;
  display_name: string;
  locality: string | null;
  is_operator: boolean;
}

export default function DevMemberSwitcher() {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const [members, setMembers] = useState<DevMember[]>([]);
  const [current, setCurrent] = useState("m_krishna");

  useEffect(() => {
    setCurrent(getDevMemberId());
    api.get<DevMember[]>("/v1/dev/members").then(setMembers).catch(() => setMembers([]));
  }, []);

  const currentMember = members.find((m) => m.id === current);

  return (
    <div style={{ position: "fixed", top: 14, right: 14, zIndex: 60 }}>
      <button
        className="vy-btn vy-btn-secondary"
        style={{ fontSize: 13, padding: "8px 14px" }}
        onClick={() => setOpen((v) => !v)}
        aria-label={t("devTools.switcherLabel")}
      >
        🧪 {currentMember?.display_name ?? current}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            className="vy-card"
            style={{
              position: "absolute",
              top: 44,
              right: 0,
              width: 260,
              maxHeight: 360,
              overflowY: "auto",
              padding: 10,
            }}
          >
            <p className="vy-muted" style={{ marginBottom: 8 }}>
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
                    background: m.id === current ? "var(--accent-soft)" : "transparent",
                    color: m.id === current ? "var(--accent-strong)" : "var(--text-primary)",
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
