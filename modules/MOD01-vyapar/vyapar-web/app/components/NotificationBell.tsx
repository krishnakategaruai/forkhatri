"use client";

// [TR021] Notification bell — "no separate Alerts tab; alerts bell sits to
// the left of the profile avatar" (the platform-wide header rule the
// coordinator invoked for this build). Vyapar's own top-right corner is
// currently occupied by <DevMemberSwitcher> (the dev-only stand-in for a
// real profile avatar) — this bell is positioned immediately to ITS left,
// so once a real avatar replaces the dev switcher, the bell is already in
// the correct relative position without a further layout change.
// Approach: polls unread-count on an interval (no WebSocket/push infra
// exists yet — honest polling, not a fake "real-time" claim) and opens a
// dropdown panel listing the inbox on click, matching the same
// dropdown-panel pattern DevMemberSwitcher/LanguageSwitcher already use.
// Traces to: FR21, TR021
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";

interface Notification {
  id: string;
  kind: string;
  title: string;
  body: string | null;
  link: string | null;
  read: boolean;
  created_at: string;
}

export default function NotificationBell() {
  const { t } = useTranslation("notifications");
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);

  async function refreshCount() {
    try {
      const r = await api.get<{ count: number }>("/v1/notifications/unread-count");
      setUnread(r.count);
    } catch {
      /* dev-only polling — a failed check just tries again next interval */
    }
  }

  useEffect(() => {
    refreshCount();
    const interval = setInterval(refreshCount, 30_000);
    return () => clearInterval(interval);
  }, []);

  async function openPanel() {
    setOpen((v) => !v);
    if (!open) {
      const list = await api.get<Notification[]>("/v1/notifications");
      setItems(list);
    }
  }

  async function markAllRead() {
    await api.post("/v1/notifications/read-all");
    setItems((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnread(0);
  }

  return (
    <div style={{ position: "fixed", top: 14, right: 168, zIndex: 60 }}>
      <button
        className="vy-btn vy-btn-secondary"
        style={{ fontSize: 13, padding: "8px 12px", position: "relative" }}
        onClick={openPanel}
        aria-label={t("bellLabel")}
      >
        🔔
        {unread > 0 && (
          <span
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              background: "var(--accent)",
              color: "var(--accent-ink)",
              borderRadius: "999px",
              fontSize: 10,
              fontWeight: 700,
              minWidth: 16,
              height: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "0 3px",
            }}
          >
            {unread}
          </span>
        )}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            className="vy-card"
            style={{ position: "absolute", top: 44, right: 0, width: 280, maxHeight: 360, overflowY: "auto", padding: 10 }}
          >
            <div className="vy-row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
              <strong style={{ fontSize: 14 }}>{t("panelTitle")}</strong>
              {items.length > 0 && (
                <button className="vy-btn vy-btn-ghost" style={{ fontSize: 12, padding: 0 }} onClick={markAllRead}>
                  {t("markAllRead")}
                </button>
              )}
            </div>
            {items.length === 0 && <p className="vy-muted">{t("empty")}</p>}
            <div className="vy-stack" style={{ gap: 6 }}>
              {items.map((n) => (
                <a
                  key={n.id}
                  href={n.link ?? "#"}
                  className="vy-card"
                  style={{ padding: 8, textDecoration: "none", background: n.read ? "transparent" : "var(--accent-soft)" }}
                >
                  <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{n.title}</p>
                  {n.body && <p className="vy-muted" style={{ fontSize: 12 }}>{n.body}</p>}
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
