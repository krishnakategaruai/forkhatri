"use client";

// [Design direction — replaces 04-ui.md's five-destination bottom tab bar]
// A single small floating pill anchored bottom-center that expands into the
// five destinations on tap, spring-physics driven via `motion`. Rejected
// alternatives (per standing design memory): a re-skinned always-expanded
// tab bar, and a glow/glass treatment — both read as generic to the product
// owner. This stays collapsed by default so it never competes with a
// screen's own primary content, and expands only on deliberate tap.
// Traces to: task brief's Design direction section
import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";

const DESTINATIONS = [
  { href: "/", labelKey: "nav.discover", icon: "✦" },
  { href: "/businesses", labelKey: "nav.businesses", icon: "▤" },
  { href: "/post", labelKey: "nav.post", icon: "+" },
  { href: "/activity", labelKey: "nav.activity", icon: "◔" },
  { href: "/profile", labelKey: "nav.profile", icon: "◍" },
] as const;

export default function CommandHub() {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div
      style={{
        position: "fixed",
        bottom: 20,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 50,
        pointerEvents: "none",
      }}
    >
      <motion.div
        layout
        style={{ pointerEvents: "auto" }}
        transition={{ type: "spring", stiffness: 380, damping: 30 }}
      >
        <AnimatePresence mode="popLayout">
          {open ? (
            <motion.div
              key="expanded"
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="vy-row"
              style={{
                background: "var(--surface-overlay)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-pill)",
                padding: 6,
                boxShadow: "var(--shadow-float)",
                gap: 2,
              }}
            >
              {DESTINATIONS.map((d) => {
                const active = pathname === d.href;
                return (
                  <button
                    key={d.href}
                    onClick={() => {
                      router.push(d.href);
                      setOpen(false);
                    }}
                    className="vy-btn"
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: 2,
                      padding: "8px 14px",
                      background: active ? "var(--accent)" : "transparent",
                      color: active ? "var(--accent-ink)" : "var(--text-secondary)",
                      minWidth: 60,
                    }}
                  >
                    <span style={{ fontSize: 16 }}>{d.icon}</span>
                    <span style={{ fontSize: 11, fontWeight: 600 }}>{t(d.labelKey)}</span>
                  </button>
                );
              })}
              <button
                onClick={() => setOpen(false)}
                className="vy-btn vy-btn-ghost"
                aria-label={t("nav.collapse")}
                style={{ padding: "8px 12px" }}
              >
                ✕
              </button>
            </motion.div>
          ) : (
            <motion.button
              key="collapsed"
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              onClick={() => setOpen(true)}
              aria-label={t("nav.open")}
              style={{
                background: "var(--accent)",
                color: "var(--accent-ink)",
                border: "none",
                borderRadius: "var(--radius-pill)",
                width: 56,
                height: 56,
                fontSize: 22,
                boxShadow: "var(--shadow-float)",
                cursor: "pointer",
              }}
            >
              ✦
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
