// The tone of a promotion / campaign state chip (design language 2026-09-29).
export function promotionTone(state: string): "action" | "done" | "warn" | "wait" | "muted" | undefined {
  switch (state) {
    case "active":
      return "action";
    case "awaiting_payment":
    case "scheduled":
      return "wait";
    case "completed":
      return "done";
    case "rejected":
      return "warn";
    case "cancelled":
    case "refunded":
    case "paused":
      return "muted";
    default:
      return undefined;
  }
}
