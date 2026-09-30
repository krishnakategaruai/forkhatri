"use client";

// [Design language 2026-09-29] The page header every account screen opens
// with: an optional way back (one row, 44px tall), the title, one line that
// says what the screen is for, and at most one action on the right. Sizes
// come from the --type-* tokens (account-2026.css); nothing here decides a
// font or a colour.
import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PageHeader({
  title,
  purpose,
  backHref,
  backLabel,
  onBack,
  action,
  as: Heading = "h1",
}: {
  title: ReactNode;
  purpose?: ReactNode;
  /** A link back (uses the shell's "back" route transition). */
  backHref?: string;
  backLabel?: string;
  /** A back action inside a flow (steps), instead of a link. */
  onBack?: () => void;
  action?: ReactNode;
  as?: "h1" | "h2";
}) {
  const back =
    backHref && backLabel ? (
      <Link href={backHref} transitionTypes={["vy-back"]} className="vy-acct-back">
        <ArrowLeft size={18} strokeWidth={2} aria-hidden="true" />
        {backLabel}
      </Link>
    ) : onBack && backLabel ? (
      <button type="button" className="vy-acct-back" onClick={onBack}>
        <ArrowLeft size={18} strokeWidth={2} aria-hidden="true" />
        {backLabel}
      </button>
    ) : null;

  return (
    <header className="vy-acct-head">
      {back}
      <div className="vy-acct-head-row">
        <div className="vy-stack" style={{ gap: 6, minWidth: 0 }}>
          <Heading>{title}</Heading>
          {purpose && <p>{purpose}</p>}
        </div>
        {action}
      </div>
    </header>
  );
}
