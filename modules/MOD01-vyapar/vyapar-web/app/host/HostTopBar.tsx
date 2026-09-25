"use client";

// [IMP38 — Refactor C] The top-right corner of the shell, owned by the host.
// Same markup layout.tsx had inline (one shared fixed flex row — see the
// comment kept in layout.tsx for why the bell and the account pill must
// share one container), but WHICH controls appear now comes from the host:
// the bell only when the host supplies a notification source, the account
// control only when the host has one.
import { useHost } from "./HostProvider";
import NotificationBell from "@/app/components/NotificationBell";

export default function HostTopBar() {
  const host = useHost();
  const Account = host.AccountControl;
  return (
    <div style={{ position: "fixed", top: 14, right: 14, zIndex: 60, display: "flex", alignItems: "flex-start", gap: 8, maxWidth: "calc(100vw - 28px)" }}>
      {host.notifications && <NotificationBell />}
      {Account && <Account />}
    </div>
  );
}
