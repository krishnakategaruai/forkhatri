/* Booking state rules shared by the booking cards, the bookings lists and the
   booking page, so every screen offers the same next step at the same moment. */

import type { Booking } from "@/lib/api";

const MIN = 60000;
/** The room opens 15 minutes before the start and stays open 2 hours after the end (as the room itself allows). */
export const ROOM_OPENS_MIN = 15;
const ROOM_CLOSES_MIN = 120;

export const isLive = (b: Booking) => ["confirmed", "in_progress"].includes(b.status);

export function canJoin(b: Booking, now: number): boolean {
  return isLive(b) && now >= new Date(b.starts_at).getTime() - ROOM_OPENS_MIN * MIN && now <= new Date(b.ends_at).getTime() + ROOM_CLOSES_MIN * MIN;
}

/** The refund percent the snapshotted policy gives if this person cancelled right now. */
export function refundPercentNow(b: Booking, now: number): number {
  if (b.role === "provider") return b.cancellation_policy?.provider_cancel_refund_percent ?? 100;
  const hoursLeft = (new Date(b.starts_at).getTime() - now) / 3600000;
  const tiers = [...(b.cancellation_policy?.seeker ?? [])].sort((a, c) => c.min_hours_before - a.min_hours_before);
  return tiers.find((tier) => hoursLeft >= tier.min_hours_before)?.refund_percent ?? 0;
}

/** When the full refund ends for the seeker (null when it has already ended or the policy has no full tier). */
export function fullRefundUntil(b: Booking, now: number): Date | null {
  const full = (b.cancellation_policy?.seeker ?? []).filter((t) => t.refund_percent >= 100).sort((a, c) => a.min_hours_before - c.min_hours_before)[0];
  if (!full) return null;
  const until = new Date(new Date(b.starts_at).getTime() - full.min_hours_before * 3600000);
  return until.getTime() > now ? until : null;
}

/** The one next step a booking card offers. */
export type NextStep =
  | { kind: "pay"; until: string }
  | { kind: "await_payment" }
  | { kind: "join"; startsIn: number }
  | { kind: "complete" }
  | { kind: "calendar"; startsIn: number }
  | { kind: "review" }
  | { kind: "recap" }
  | { kind: "book_again" }
  | { kind: "none" };

export function nextStep(b: Booking, now: number): NextStep {
  const start = new Date(b.starts_at).getTime();
  if (b.status === "pending_payment") {
    return b.role === "seeker" && b.pay_by ? { kind: "pay", until: b.pay_by } : { kind: "await_payment" };
  }
  if (isLive(b)) {
    // After the scheduled end the consultant closes it; the room stays open a while longer.
    if (b.role === "provider" && now > new Date(b.ends_at).getTime()) return { kind: "complete" };
    if (canJoin(b, now)) return { kind: "join", startsIn: start - now };
    return { kind: "calendar", startsIn: start - now };
  }
  if (b.status === "completed") {
    if (b.role === "seeker" && !b.reviewed) return { kind: "review" };
    if (b.has_recap || b.recap) return { kind: "recap" };
    return b.role === "seeker" ? { kind: "book_again" } : { kind: "none" };
  }
  return { kind: "none" };
}

/** Completed consultations the seeker has not reviewed yet, within this many days, are asked about. */
export const REVIEW_ASK_DAYS = 30;

export function needsAction(b: Booking, now: number): boolean {
  if (b.status === "pending_payment" && b.role === "seeker" && !!b.pay_by) return true;
  if (b.status === "completed" && b.role === "seeker" && !b.reviewed) {
    const done = new Date(b.completed_at ?? b.ends_at).getTime();
    return now - done < REVIEW_ASK_DAYS * 86400000;
  }
  if (isLive(b) && b.role === "provider" && now > new Date(b.ends_at).getTime()) return true;
  return false;
}

export const sameDay = (iso: string, now: number) => new Date(iso).toDateString() === new Date(now).toDateString();

/** What the consultant keeps from this booking after the fee and any refund. */
export const earningMinor = (b: Booking) => Math.max(0, b.provider_payable_minor - b.refund_minor);
