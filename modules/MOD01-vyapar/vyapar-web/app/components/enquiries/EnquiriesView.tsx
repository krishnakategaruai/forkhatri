"use client";

// [IMP38 — Refactor C] Requests inbox, presentational half. Data in, events
// out; the thread shown in the split pane comes from `renderThread`.
//
// [Design language 2026-09-29] Rebuilt as an inbox people recognise (mail,
// WhatsApp, Upwork's messages): one page title with its purpose, Sent /
// Received as a segmented switch with counts, quiet state chips as
// filters, and rows that read avatar · what it is about · who · when, with
// the state as a small chip. Desktop (≥1024): the list stays on the left
// and the chosen thread opens in a sticky pane beside it. Phone: a row
// navigates. Dates are Indian order (lib/format), never toLocaleString.
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Briefcase, FileText, HelpCircle, Inbox, MessageSquare, Sparkles } from "lucide-react";
import type { EnquiryRole, EnquirySummary } from "@/lib/sdk";
import { formatDayMonth, formatDate } from "@/lib/format";
import { Reveal } from "@/app/components/Motion";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { useRoutes } from "@/app/host/HostProvider";

/** A post that has ended, as the quiet chip beside the request's own state. */
export const ENDED_TARGET_STATES = ["closed", "expired", "removed"] as const;

/** "Closed" / "Expired" / "Removed" for the post a request is about, or null while it is live. */
export function endedTargetLabel(
  t: (key: string) => string,
  targetState: string | null | undefined,
  postClosedShown: boolean,
): string | null {
  if (!targetState || !(ENDED_TARGET_STATES as readonly string[]).includes(targetState)) return null;
  // "Post closed" on the request already says it.
  if (postClosedShown) return null;
  // "Post expired", not a bare "Expired" beside the request's own "Closed".
  return t(`enquiries:detail.targetEnded.${targetState}`);
}

export const ENQUIRY_STATE_KEY: Record<string, string> = {
  open: "stateOpen",
  awaiting_response: "stateAwaitingResponse",
  in_progress: "stateInProgress",
  resolved: "stateResolved",
  closed: "stateClosed",
  withdrawn: "stateWithdrawn",
  restricted: "stateRestricted",
};

/** Tone of a request's state chip: needs the reader (wait), live (action), finished (done), stopped (warn). */
export function enquiryTone(state: string, isSender: boolean): "wait" | "action" | "done" | "warn" | "muted" | undefined {
  switch (state) {
    case "open":
    case "awaiting_response":
      return isSender ? undefined : "wait";
    case "in_progress":
      return "action";
    case "resolved":
      return "done";
    case "restricted":
      return "warn";
    case "closed":
    case "withdrawn":
      return "muted";
    default:
      return undefined;
  }
}

const KIND_ICON: Record<string, typeof HelpCircle> = {
  enquire: HelpCircle,
  apply: Briefcase,
  propose: FileText,
  contact: MessageSquare,
  register: Sparkles,
};

// FR23's five real, active-attention states — withdrawn/restricted are
// terminal/exceptional and deliberately excluded from the quick-filter row
// (still visible under "All").
const QUICK_STATES = ["open", "awaiting_response", "in_progress", "resolved", "closed"] as const;

export interface EnquiriesViewProps {
  role: EnquiryRole;
  onRoleChange: (role: EnquiryRole) => void;
  items: EnquirySummary[] | null;
  /** Both lists' sizes, for the tab counts (null while loading). */
  counts: { sent: number | null; received: number | null };
  stateFilter: string | null;
  onStateFilterChange: (next: string | null | ((prev: string | null) => string | null)) => void;
  /** Thread selected into the desktop split pane. */
  selected: string | null;
  onSelect: (id: string) => void;
  renderThread: (id: string) => React.ReactNode;
}

function initial(name: string | null | undefined): string {
  const s = (name ?? "").trim();
  return s ? s.charAt(0).toUpperCase() : "?";
}

/** "Today 2:05 pm" is noise in a list; the day is enough: "28 Sep", or "28 Sep 2025" for another year. */
function whenLabel(iso: string, language: string): string {
  const d = new Date(iso);
  return d.getFullYear() === new Date().getFullYear() ? formatDayMonth(d, language) : formatDate(d, language);
}

export default function EnquiriesView({ role, onRoleChange, items, counts, stateFilter, onStateFilterChange, selected, onSelect, renderThread }: EnquiriesViewProps) {
  const { t, i18n } = useTranslation(["enquiries", "common"]);
  const routes = useRoutes();

  const stateCounts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const e of items ?? []) c[e.state] = (c[e.state] ?? 0) + 1;
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    if (!items) return items;
    return stateFilter ? items.filter((e) => e.state === stateFilter) : items;
  }, [items, stateFilter]);

  const stateLabel = (s: string) => t(`enquiries:detail.${ENQUIRY_STATE_KEY[s] ?? "stateOpen"}` as "detail.stateOpen");

  return (
    <div className="vy-dl-page">
      <div className="vy-dl-head">
        <h1>{t("enquiries:mine.title")}</h1>
        <p>{t("enquiries:mine.subtitle")}</p>
      </div>

      <div className="vy-segmented vy-dl-tabs" role="tablist" aria-label={t("enquiries:mine.title")}>
        {(["received", "sent"] as EnquiryRole[]).map((r) => (
          <button key={r} type="button" role="tab" aria-selected={role === r} onClick={() => onRoleChange(r)}>
            {r === "sent" ? t("enquiries:mine.tabSent") : t("enquiries:mine.tabReceived")}
            {counts[r] != null && <span className="vy-dl-count">{counts[r]}</span>}
          </button>
        ))}
      </div>

      {items && items.length > 0 && (
        <div className="vy-dl-chips" role="group" aria-label={t("enquiries:mine.filterByState")}>
          <button type="button" className="vy-chip" aria-pressed={stateFilter === null} onClick={() => onStateFilterChange(null)}>
            {t("enquiries:mine.all")} <span className="vy-dl-count">{items.length}</span>
          </button>
          {QUICK_STATES.filter((s) => stateCounts[s]).map((s) => (
            <button key={s} type="button" className="vy-chip" aria-pressed={stateFilter === s} onClick={() => onStateFilterChange((v) => (v === s ? null : s))}>
              {stateLabel(s)} <span className="vy-dl-count">{stateCounts[s]}</span>
            </button>
          ))}
        </div>
      )}

      {items === null && <SkeletonGrid count={4} grid={false} />}
      {items?.length === 0 && (
        <DealsEmpty
          icon={<Inbox size={24} strokeWidth={1.75} aria-hidden="true" />}
          title={role === "sent" ? t("enquiries:mine.emptySent") : t("enquiries:mine.emptyReceived")}
          body={role === "sent" ? t("enquiries:mine.emptySentBody") : t("enquiries:mine.emptyReceivedBody")}
        />
      )}
      {items && items.length > 0 && filtered?.length === 0 && (
        <DealsEmpty tone="neutral" icon={<Inbox size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("enquiries:mine.noneInState")} />
      )}

      {filtered && filtered.length > 0 && (
        <div className="vy-pane">
          <div className="vy-pane-list vy-dl-list">
            {filtered.map((e, i) => {
              const Kind = KIND_ICON[e.action_type] ?? HelpCircle;
              const kind = t(`enquiries:actionType.${e.action_type}` as "actionType.enquire", { defaultValue: e.action_type });
              const who = e.counterpart_name ? t("enquiries:mine.withCounterpart", { name: e.counterpart_name }) : null;
              const tone = enquiryTone(e.state, e.is_sender);
              const postClosed = e.is_sender && e.state === "closed" && e.state_reason === "post_closed";
              const ended = endedTargetLabel(t as (k: string) => string, e.target_state, postClosed);
              const body = (
                <>
                  <span className="vy-dl-avatar" aria-hidden="true">{initial(e.counterpart_name)}</span>
                  <span className="vy-dl-row-body">
                    <span className="vy-dl-row-title">{e.target_name ?? t("enquiries:mine.untitledTarget")}</span>
                    <span className="vy-dl-row-meta">
                      <Kind size={14} strokeWidth={2} aria-hidden="true" />
                      <span>{[kind, who].filter(Boolean).join(" · ")}</span>
                    </span>
                    <span className="vy-dl-tags" style={{ marginTop: 4 }}>
                      <span className="vy-dl-state" data-tone={tone}>
                        {tone === "wait"
                          ? t("enquiries:mine.needsYou")
                          : postClosed
                            ? t("enquiries:detail.statePostClosed") /* [Trust pack §3] quietly, never "rejected" */
                            : stateLabel(e.state)}
                      </span>
                      {ended && (
                        <span className="vy-dl-state" data-tone="muted">
                          {ended}
                        </span>
                      )}
                    </span>
                  </span>
                  <span className="vy-dl-row-aside">
                    <time className="vy-dl-row-time" dateTime={e.last_activity_at}>{whenLabel(e.last_activity_at, i18n.language)}</time>
                  </span>
                </>
              );
              return (
                <Reveal key={e.id} index={i}>
                  {/* Phone/tablet: navigate. */}
                  <a className="vy-dl-row vy-pane-row-mobile" href={routes.enquiry(e.id)}>
                    {body}
                  </a>
                  {/* Desktop console: select into the pane beside the list. */}
                  <button type="button" className="vy-dl-row vy-pane-row-console" aria-current={selected === e.id ? "true" : undefined} onClick={() => onSelect(e.id)}>
                    {body}
                  </button>
                </Reveal>
              );
            })}
          </div>

          <div className="vy-pane-detail vy-console-only">
            {selected ? (
              <div className="vy-dl-pane-detail">{renderThread(selected)}</div>
            ) : (
              <div className="vy-dl-pane-empty">
                <span className="vy-dl-tile vy-dl-tile-lg" aria-hidden="true">
                  <MessageSquare size={24} strokeWidth={1.75} />
                </span>
                <p>{t("enquiries:mine.selectPrompt")}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
