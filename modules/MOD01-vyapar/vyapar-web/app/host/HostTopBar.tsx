"use client";

// [IMP38 — Refactor C] The host-owned end of the top bar: the bell only
// when the host supplies a notification source, the account control only
// when the host has one.
// [Design language 2026-09-29] No longer its own fixed-position corner: it
// renders inline at the end of <AppTopBar>, one flex row with the rest of
// the header, so the bell sits left of the avatar and the avatar is always
// the right-most item (the platform header rule), whatever the name width.
import { useHost } from "./HostProvider";
import NotificationBell from "@/app/components/NotificationBell";

export default function HostTopBar() {
  const host = useHost();
  const Account = host.AccountControl;
  return (
    <>
      {host.notifications && <NotificationBell />}
      {Account && <Account />}
    </>
  );
}
