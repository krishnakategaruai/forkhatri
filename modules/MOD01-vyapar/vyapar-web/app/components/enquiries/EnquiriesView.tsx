"use client";

// [IMP38 — Refactor C] My enquiries, presentational half — markup moved
// verbatim out of app/enquiries/mine/page.tsx (see that file for the FR23
// state chips and the IMP33 ≥1024px split pane). Data in, events out; the
// thread shown in the split pane comes from `renderThread`, so this view
// never loads anything itself.
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { EnquiryRole, EnquirySummary } from "@/lib/sdk";
import { Reveal } from "@/app/components/Motion";
import { SkeletonGrid, EmptyState } from "@/app/components/States";
import { useRoutes } from "@/app/host/HostProvider";

export const ENQUIRY_STATE_KEY: Record<string, string> = {
  open: "stateOpen",
  awaiting_response: "stateAwaitingResponse",
  in_progress: "stateInProgress",
  resolved: "stateResolved",
  closed: "stateClosed",
  withdrawn: "stateWithdrawn",
  restricted: "stateRestricted",
};

// FR23's five real, active-attention states — withdrawn/restricted are
// terminal/exceptional and deliberately excluded from the quick-filter row
// (still visible under "All").
const QUICK_STATES = ["open", "awaiting_response", "in_progress", "resolved", "closed"] as const;

export interface EnquiriesViewProps {
  role: EnquiryRole;
  onRoleChange: (role: EnquiryRole) => void;
  items: EnquirySummary[] | null;
  stateFilter: string | null;
  onStateFilterChange: (next: string | null | ((prev: string | null) => string | null)) => void;
  /** Thread selected into the desktop split pane. */
  selected: string | null;
  onSelect: (id: string) => void;
  renderThread: (id: string) => React.ReactNode;
}

export default function EnquiriesView({ role, onRoleChange, items, stateFilter, onStateFilterChange, selected, onSelect, renderThread }: EnquiriesViewProps) {
  const { t, i18n } = useTranslation(["enquiries", "common"]);
  const routes = useRoutes();

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const e of items ?? []) c[e.state] = (c[e.state] ?? 0) + 1;
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    if (!items) return items;
    return stateFilter ? items.filter((e) => e.state === stateFilter) : items;
  }, [items, stateFilter]);

  return (
    <>
      <h1>{t("enquiries:mine.title")}</h1>
      <div className="vy-row">
        <button className="vy-btn" style={{ background: role === "sent" ? "var(--selected-solid-bg)" : "var(--surface-overlay)", color: role === "sent" ? "var(--selected-solid-fg)" : "var(--text-primary)" }} onClick={() => onRoleChange("sent")}>
          {t("enquiries:mine.tabSent")}
        </button>
        <button className="vy-btn" style={{ background: role === "received" ? "var(--selected-solid-bg)" : "var(--surface-overlay)", color: role === "received" ? "var(--selected-solid-fg)" : "var(--text-primary)" }} onClick={() => onRoleChange("received")}>
          {t("enquiries:mine.tabReceived")}
        </button>
      </div>
      {items && items.length > 0 && (
        <div className="vy-row" role="group" aria-label={t("enquiries:mine.filterByState")} style={{ flexWrap: "wrap" }}>
          <button className="vy-chip" aria-pressed={stateFilter === null} style={{ cursor: "pointer" }} onClick={() => onStateFilterChange(null)}>
            {t("enquiries:mine.filterAll", { n: items.length })}
          </button>
          {QUICK_STATES.filter((s) => counts[s]).map((s) => (
            <button
              key={s}
              className="vy-chip"
              aria-pressed={stateFilter === s}
              style={{ cursor: "pointer" }}
              onClick={() => onStateFilterChange((v) => (v === s ? null : s))}
            >
              {t(`enquiries:detail.${ENQUIRY_STATE_KEY[s]}` as "detail.stateOpen")} ({counts[s]})
            </button>
          ))}
        </div>
      )}
      {items === null && <SkeletonGrid count={4} grid={false} />}
      {items?.length === 0 && <EmptyState mark="✉" title={t("enquiries:mine.empty")} />}
      {items && items.length > 0 && filtered?.length === 0 && <EmptyState mark="◌" title={t("enquiries:mine.noneInState")} />}

      {filtered && filtered.length > 0 && (
        <div className="vy-pane">
          <div className="vy-pane-list vy-stack">
            {filtered.map((e, i) => {
              const meta = [
                t(`enquiries:actionType.${e.action_type}` as "actionType.enquire", { defaultValue: e.action_type }),
                t(`enquiries:detail.${ENQUIRY_STATE_KEY[e.state] ?? "stateOpen"}` as "detail.stateOpen"),
                e.counterpart_name ? t("enquiries:mine.withCounterpart", { name: e.counterpart_name }) : null,
                new Date(e.last_activity_at).toLocaleString(i18n.language, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }),
              ]
                .filter(Boolean)
                .join(" · ");
              const body = (
                <>
                  <strong>{e.target_name ?? t("enquiries:mine.untitledTarget")}</strong>
                  <span className="vy-muted" style={{ fontSize: 13 }}>{meta}</span>
                </>
              );
              return (
                <Reveal key={e.id} index={i}>
                  {/* Phone/tablet: navigate, exactly as before. */}
                  <a className="vy-card vy-pane-row-mobile" style={{ textDecoration: "none", gap: 4 }} href={routes.enquiry(e.id)}>
                    {body}
                  </a>
                  {/* Desktop console: select into the pane beside the list.
                      `aria-current` marks the selected row for assistive
                      tech; `.vy-card-selected` is the visual counterpart. */}
                  <button
                    type="button"
                    className={`vy-card vy-pane-row-console vy-card-interactive ${selected === e.id ? "vy-card-selected" : ""}`}
                    aria-current={selected === e.id ? "true" : undefined}
                    style={{ gap: 4, width: "100%", textAlign: "left", cursor: "pointer", font: "inherit", color: "inherit" }}
                    onClick={() => onSelect(e.id)}
                  >
                    {body}
                  </button>
                </Reveal>
              );
            })}
          </div>

          <div className="vy-pane-detail vy-console-only">
            {selected ? renderThread(selected) : <EmptyState mark="←" title={t("enquiries:mine.selectPrompt")} />}
          </div>
        </div>
      )}
    </>
  );
}
