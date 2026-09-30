"use client";

// [Design language 2026-09-29] A chooser card: tinted icon tile, a title,
// one line of hint and a chevron — the Post screen and the "Add a profile"
// screen both ask one question with two of these. A link when it goes
// somewhere, a button when it changes the screen in place.
import Link from "next/link";
import { ChevronRight, type LucideIcon } from "lucide-react";
import type { Tint } from "./ShortcutList";

export default function ChoiceCard({
  icon,
  tint,
  title,
  hint,
  href,
  onClick,
}: {
  icon: LucideIcon;
  tint: Tint;
  title: string;
  hint: string;
  href?: string;
  onClick?: () => void;
}) {
  const Icon = icon;
  const body = (
    <>
      <span className="vy-acct-tile vy-acct-tile-lg" data-tint={tint} aria-hidden="true">
        <Icon size={24} strokeWidth={1.9} />
      </span>
      <span className="vy-acct-choice-text">
        <span className="vy-acct-choice-title">{title}</span>
        <span className="vy-acct-choice-hint">{hint}</span>
      </span>
      <ChevronRight className="vy-acct-choice-arrow" size={20} strokeWidth={2} aria-hidden="true" />
    </>
  );
  if (href) {
    return (
      <Link href={href} transitionTypes={["vy-forward"]} className="vy-card vy-acct-choice">
        {body}
      </Link>
    );
  }
  return (
    <button type="button" className="vy-card vy-card-interactive vy-acct-choice" onClick={onClick}>
      {body}
    </button>
  );
}
