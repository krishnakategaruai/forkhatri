// [FE2 — imp-backend-d] Pure contract rules the screens need: who acts next
// on a milestone, its dot tone, the running totals. Kept free of React so
// the list, the detail and the sticky phone footer all agree.
import type { Contract, ContractSummary, Milestone, Timesheet } from "@/lib/sdk";

export type MilestoneAction = "fund" | "submit" | "review" | null;
export type Tone = "open" | "held" | "action" | "done" | "warn";

const isClient = (c: { my_role: string }) => c.my_role === "client";

/** The one thing the viewer can do on this milestone right now, if any. */
export function milestoneAction(c: Contract, m: Milestone): MilestoneAction {
  if (c.state !== "active") return null;
  if (isClient(c)) {
    if (m.state === "pending") return "fund";
    if (m.state === "submitted") return "review";
    return null;
  }
  if (m.state === "funded" || m.state === "rejected") return "submit";
  return null;
}

export function milestoneTone(c: Contract, m: Milestone): Tone {
  if (milestoneAction(c, m)) return "action";
  switch (m.state) {
    case "released":
    case "approved":
      return "done";
    case "funded":
    case "submitted":
      return "held";
    case "rejected":
      return "warn";
    default:
      return "open";
  }
}

export function timesheetNeedsMe(c: Contract, t: Timesheet): boolean {
  return c.state === "active" && isClient(c) && t.state === "submitted";
}

/** Does the viewer have something to do on this contract? */
export function contractNeedsMe(c: Contract): boolean {
  if (c.state === "proposed") return !isClient(c);
  if (c.state === "draft") return isClient(c);
  if (c.state !== "active") return false;
  return c.milestones.some((m) => milestoneAction(c, m) !== null) || c.timesheets.some((t) => timesheetNeedsMe(c, t));
}

/** A list row only knows the state: proposals waiting on the provider and drafts on the client. */
export function summaryNeedsMe(c: ContractSummary): boolean {
  return (c.state === "proposed" && c.my_role === "provider") || (c.state === "draft" && c.my_role === "client");
}

export function stateTone(state: string): Tone {
  if (state === "completed") return "done";
  if (state === "disputed" || state === "cancelled") return "warn";
  if (state === "active") return "held";
  return "open";
}

export function counterpartOf(c: Contract): string {
  return (c.my_role === "client" ? c.provider_name : c.client_name) ?? c.counterpart_name ?? "";
}

/** Total not yet paid into the ledger (fixed contracts). */
export function notFundedPaise(c: Contract): number {
  const l = c.ledger;
  return Math.max(0, c.total_paise - l.held_paise - l.released_paise - l.refunded_paise - l.fee_paise);
}

/** The last seven Mondays up to this week, newest first, as YYYY-MM-DD in local time. */
export function recentMondays(count = 6, now = new Date()): string[] {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const back = (d.getDay() + 6) % 7; // days since Monday
  d.setDate(d.getDate() - back);
  const out: string[] = [];
  for (let i = 0; i < count; i++) {
    const x = new Date(d);
    x.setDate(d.getDate() - 7 * i);
    out.push(`${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`);
  }
  return out;
}

/** Where to go to pay: the Payment Bridge checkout, told to come back to this contract. */
export function checkoutHref(checkoutUrl: string, contractId: string): string {
  const sep = checkoutUrl.includes("?") ? "&" : "?";
  return `${checkoutUrl}${sep}return=${encodeURIComponent(`/contracts/${contractId}`)}`;
}
