"use client";

import { usePathname, useSearchParams } from "next/navigation";

import ConversationList from "@/components/ConversationList";

/* Messages is two panes on a desktop, the way every messenger is: the inbox
 * on the left, the open conversation on the right. On a phone it is one pane
 * at a time: the inbox at /messages, the thread when one is open. */
export default function MessagesLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/messages";
  const openId = pathname.startsWith("/messages/") ? pathname.split("/")[2] ?? null : null;
  // A candidates' session and the families' chat share one connection id;
  // the kind tells them apart, so only the open one is marked.
  const openKind = useSearchParams()?.get("kind") ?? "candidate";
  return (
    <div className={`mpane${openId ? " mpane--thread" : " mpane--inbox"}`}>
      <aside className="mpane__list">
        <ConversationList activeId={openId} activeKind={openKind} />
      </aside>
      <section className="mpane__main">{children}</section>
    </div>
  );
}
