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
// [IMP38 — Refactor C] The bell no longer calls a fixed endpoint: it reads
// its items from the host's NotificationSource (Vyapar's own inbox on both
// shipped hosts), through the SDK instance in scope. A host with its own
// notification centre supplies a different source, or none at all.
import { useEffect, useMemo, useState } from "react";
import { usePopoverDismiss } from "@/lib/usePopoverDismiss";
import { motion, AnimatePresence } from "motion/react";
import { useTranslation } from "react-i18next";
import type { Notification } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import { useHost } from "@/app/host/HostProvider";
import { Bell } from "lucide-react";

export default function NotificationBell() {
  const { t } = useTranslation("notifications");
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const sdk = useSdk();
  const host = useHost();
  const source = useMemo(() => host.notifications?.(sdk) ?? null, [host, sdk]);
  const ref = usePopoverDismiss(open, () => setOpen(false));

  async function refreshCount() {
    if (!source) return;
    try {
      setUnread(await source.unreadCount());
    } catch {
      /* dev-only polling — a failed check just tries again next interval */
    }
  }

  useEffect(() => {
    queueMicrotask(refreshCount);
    const interval = setInterval(refreshCount, 30_000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  async function openPanel() {
    setOpen((v) => !v);
    if (!open && source) {
      const list = await source.list();
      setItems(list);
    }
  }

  async function markAllRead() {
    if (!source) return;
    await source.markAllRead();
    setItems((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnread(0);
  }

  // [Bug fix — see layout.tsx's comment] no longer self-positions with a
  // hardcoded `right` offset; the parent flex row in layout.tsx now owns
  // placement for both this and DevMemberSwitcher.
  return (
    <div ref={ref} className="vy-menu-anchor">
      {/* [Design language 2026-09-29] an icon button in the top bar (bell
          left of the avatar), with the unread count as a small badge. */}
      <button type="button" className="vy-iconbtn" onClick={openPanel} aria-label={t("bellLabel")} aria-expanded={open} title={t("bellLabel")}>
        <Bell size={20} strokeWidth={1.75} aria-hidden="true" />
        {unread > 0 && <span className="vy-iconbtn-badge">{unread > 99 ? "99+" : unread}</span>}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            // [Design-enhancement pass, DESIGN-ENHANCEMENT.md — named
            // example] a floating dropdown panel, one step above the
            // ordinary --surface-raised content sitting behind it.
            className="vy-popover vy-popover-end"
            style={{ width: 320, maxHeight: 420, overflowY: "auto" }}
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
