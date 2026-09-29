"use client";

/**
 * Federated module queues (TR-PLAT-01). Every module view the person is appointed to,
 * in one place: list on the left, the chosen item on the right (a full-screen sheet on
 * phones). The console renders whatever the module sends; each decision is dispatched
 * back to the module, which enforces it, and is also written to the platform audit log.
 */
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useMediaQuery } from "@/lib/hooks";
import { admin, type QueueDetail, type QueueItem, type QueueView } from "@/lib/admin-api";
import { adminLabel, humanise, type AdminKey } from "@/lib/admin-i18n";
import { Badge, Chips, Dialog, Empty, errorMessage, ErrorLine, Field, formatDateTime, isPast, Loading, PageHead, relative, useConsole, useLoad } from "./kit";

const CLOSED = new Set(["resolved", "dismissed", "actioned", "closed", "verified", "rejected", "approved", "removed", "upheld", "overturned", "decided", "done"]);
export const isOpen = (status: string) => !CLOSED.has(status);

const viewKey = (v: { module_id: string; view_id: string | null }) => `${v.module_id}/${v.view_id ?? ""}`;
const PRIORITY_ORDER: Record<string, number> = { urgent: 0, high: 1, normal: 2 };

export default function Queues() {
  const { t, lang, changed } = useConsole();
  const params = useSearchParams();
  const list = useLoad(() => admin.queues(lang), [lang]);
  const views = list.data;
  const error = list.error ? errorMessage(t, list.error) : null;
  const [selectedView, setSelectedView] = useState<string>(params.get("view") ?? "");
  const [onlyOpen, setOnlyOpen] = useState<"open" | "all">("open");
  const [item, setItem] = useState<QueueItem | null>(null);
  const phone = useMediaQuery("(max-width: 899px)");

  const current = useMemo(() => {
    if (!views?.length) return null;
    return views.find((v) => viewKey(v) === selectedView) ?? views.find((v) => !v.error && v.items.some((i) => isOpen(i.status))) ?? views[0];
  }, [views, selectedView]);

  const items = useMemo(() => {
    if (!current) return [];
    return current.items
      .filter((i) => onlyOpen === "all" || isOpen(i.status))
      .sort(
        (a, b) =>
          Number(!isOpen(a.status)) - Number(!isOpen(b.status)) ||
          (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3) ||
          (a.due_at ?? "9").localeCompare(b.due_at ?? "9") ||
          a.submitted_at.localeCompare(b.submitted_at),
      );
  }, [current, onlyOpen]);

  function replaceItem(updated: QueueItem) {
    if (views)
      list.set(views.map((v) => (v.module_id === updated.module_id ? { ...v, items: v.items.map((i) => (i.item_id === updated.item_id ? { ...i, ...updated } : i)) } : v)));
    setItem((prev) => (prev && prev.item_id === updated.item_id ? { ...prev, ...updated } : prev));
    changed();
  }

  return (
    <div className="adm-page adm-page-wide">
      <PageHead title={t("queuesTitle")} sub={t("queuesSub")} />
      <ErrorLine error={error} />
      {!views ? (
        <Loading />
      ) : views.length === 0 ? (
        <Empty>{t("noQueues")}</Empty>
      ) : (
        <>
          <div className="adm-queue-tabs" role="tablist">
            {views.map((v) => {
              const open = v.items.filter((i) => isOpen(i.status)).length;
              const active = current && viewKey(v) === viewKey(current);
              return (
                <button
                  key={viewKey(v)}
                  type="button"
                  role="tab"
                  aria-selected={!!active}
                  className={`adm-queue-tab${active ? " is-on" : ""}`}
                  onClick={() => {
                    setSelectedView(viewKey(v));
                    setItem(null);
                  }}
                >
                  <span className="adm-queue-tab-module">{humanise(v.module_id)}</span>
                  <span className="adm-queue-tab-title">{v.view_id ? v.title : humanise(v.module_id)}</span>
                  {v.error ? <span className="adm-queue-tab-err" aria-hidden="true">!</span> : <span className="adm-chip-count">{open}</span>}
                </button>
              );
            })}
          </div>

          {current && (
            <div className="adm-split">
              <div className="adm-split-list">
                <div className="adm-split-toolbar">
                  {current.nav_group && <span className="adm-muted">{adminLabel(t, `group_${current.nav_group}`, humanise(current.nav_group))}</span>}
                  <Chips
                    label={t("queuesTitle")}
                    value={onlyOpen}
                    onChange={setOnlyOpen}
                    options={[
                      { value: "open", label: t("filterOpen") },
                      { value: "all", label: t("filterAll") },
                    ]}
                  />
                </div>
                {current.error ? (
                  <Empty>{t(queueErrorKey(current.error))}</Empty>
                ) : items.length === 0 ? (
                  <Empty>{onlyOpen === "open" ? t("queueEmptyOpen") : t("queueEmpty")}</Empty>
                ) : (
                  <ul className="adm-list">
                    {items.map((i) => (
                      <li key={i.item_id}>
                        <button type="button" className={`adm-row adm-queue-row${item?.item_id === i.item_id ? " is-selected" : ""}`} onClick={() => setItem(i)}>
                          <span className={`adm-dot ${i.priority === "urgent" ? "is-urgent" : i.priority === "high" ? "is-warn" : ""}`} aria-hidden="true" />
                          <span className="adm-row-main">
                            <span className="adm-row-title">{i.summary_text}</span>
                            <span className="adm-row-sub">
                              <Due item={i} /> · {t("submitted", { when: relative(i.submitted_at, lang, t) })}
                            </span>
                          </span>
                          <StatusBadge status={i.status} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="adm-split-detail">
                {phone ? null : item && current.view_id ? (
                  <ItemDetail key={item.item_id} view={current} item={item} onClose={() => setItem(null)} onChanged={replaceItem} />
                ) : (
                  <Empty>{t("selectItem")}</Empty>
                )}
              </div>
            </div>
          )}
        </>
      )}
      {/* Phones: the chosen item opens as a full-screen sheet over the list. */}
      {phone && (
        <Dialog open={!!item && !!current?.view_id} onClose={() => setItem(null)} title={item?.summary_text ?? ""}>
          {item && current?.view_id && <ItemDetail view={current} item={item} onClose={() => setItem(null)} onChanged={replaceItem} bare />}
        </Dialog>
      )}
    </div>
  );
}

function queueErrorKey(code: string): AdminKey {
  return (["no_access", "module_unreachable", "not_connected"].includes(code) ? `queueError_${code}` : "queueError_generic") as AdminKey;
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useConsole();
  const label = adminLabel(t, `queueStatus_${status}`, humanise(status));
  return <Badge tone={isOpen(status) ? "warn" : "ok"}>{label}</Badge>;
}

function Due({ item }: { item: QueueItem }) {
  const { t, lang } = useConsole();
  if (!item.due_at || !isOpen(item.status)) return <>{adminLabel(t, `priority_${item.priority}`, humanise(item.priority))}</>;
  const late = isPast(item.due_at);
  return <span className={late ? "adm-late" : undefined}>{late ? t("overdue", { when: relative(item.due_at, lang, t) }) : t("dueIn", { when: relative(item.due_at, lang, t) })}</span>;
}

type Detail = QueueDetail & { action_options?: Record<string, string[]> };

function ItemDetail({ view, item, onClose, onChanged, bare }: { view: QueueView; item: QueueItem; onClose: () => void; onChanged: (i: QueueItem) => void; bare?: boolean }) {
  const { t, lang } = useConsole();
  const loaded = useLoad(() => admin.queueItem(view.module_id, view.view_id ?? "", item.item_id, lang) as Promise<Detail>, [view.module_id, view.view_id, item.item_id, lang]);
  const detail = loaded.data;
  const [actionError, setError] = useState<string | null>(null);
  const error = actionError ?? (loaded.error ? errorMessage(t, loaded.error) : null);
  const [action, setAction] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  async function run() {
    if (!action) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await admin.queueAction(view.module_id, view.view_id ?? "", item.item_id, action, { notes: notes.trim() || undefined, reason_code: outcome || undefined }, lang);
      setDone(t("actionDone", { action: actionName(action) }));
      setAction(null);
      setNotes("");
      setOutcome("");
      onChanged({ ...item, ...updated });
      loaded.reload();
    } catch (e) {
      setError(errorMessage(t, e));
    } finally {
      setBusy(false);
    }
  }

  function actionName(id: string) {
    return adminLabel(t, `qa_${id}`, humanise(id));
  }

  const caseDetail = detail?.case_detail ?? {};
  const history = Array.isArray(caseDetail.history) ? (caseDetail.history as { action?: string; by?: string; notes?: string | null; at?: string }[]) : [];
  // A module may send its own labelled, localised fields ({label, value}); otherwise the raw detail is shown readably.
  const labelled = Array.isArray(caseDetail.fields) ? (caseDetail.fields as { label: string; value: string }[]) : null;
  const facts = Object.entries(caseDetail).filter(([key]) => !["history", "summary_text", "fields"].includes(key));
  const options = action ? detail?.action_options?.[action] : undefined;

  return (
    <article className={`adm-detail${bare ? " is-bare" : ""}`}>
      {!bare && (
        <header className="adm-detail-head">
          <div>
            <p className="adm-muted">{view.title.toLowerCase().startsWith(view.module_id) ? view.title : `${humanise(view.module_id)} · ${view.title}`}</p>
            <h2>{item.summary_text}</h2>
          </div>
          <button type="button" className="adm-icon-btn" onClick={onClose} aria-label={t("close")}>
            ×
          </button>
        </header>
      )}
      <ErrorLine error={error} />
      {done && <p className="adm-success" role="status">{done}</p>}
      {!detail ? (
        !error && <Loading />
      ) : (
        <>
          <section className="adm-detail-section">
            <h3>{t("caseActions")}</h3>
            {detail.available_actions.length === 0 ? (
              <p className="adm-muted">{t("noActions")}</p>
            ) : (
              <div className="adm-actions">
                {detail.available_actions.map((a) => (
                  <button key={a} type="button" className={`adm-btn${action === a ? " primary" : ""}${/suspend|ban|remove|reject/.test(a) ? " danger-outline" : ""}`} onClick={() => setAction(action === a ? null : a)}>
                    {actionName(a)}
                  </button>
                ))}
              </div>
            )}
            {action && (
              <div className="adm-action-form">
                {options && options.length > 0 && (
                  <Field label={t("outcomeLabel")}>
                    <select className="adm-input" value={outcome} onChange={(e) => setOutcome(e.target.value)}>
                      <option value="">—</option>
                      {options.map((o) => (
                        <option key={o} value={o}>
                          {adminLabel(t, `qo_${o}`, humanise(o))}
                        </option>
                      ))}
                    </select>
                  </Field>
                )}
                <Field label={t("notesLabel")}>
                  <textarea className="adm-input" rows={3} value={notes} placeholder={t("notesPlaceholder")} onChange={(e) => setNotes(e.target.value)} />
                </Field>
                <div className="adm-actions">
                  <button type="button" className="adm-btn" onClick={() => setAction(null)}>
                    {t("cancel")}
                  </button>
                  <button type="button" className="adm-btn primary" disabled={busy} onClick={() => void run()}>
                    {actionName(action)}
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="adm-detail-section">
            <h3>{t("caseDetails")}</h3>
            <dl className="adm-facts">
              {labelled
                ? labelled.map((f) => (
                    <div key={f.label} className="adm-fact">
                      <dt>{f.label}</dt>
                      <dd>{f.value}</dd>
                    </div>
                  ))
                : facts.map(([key, value]) => <Fact key={key} name={key} value={value} />)}
            </dl>
          </section>

          {history.length > 0 && (
            <section className="adm-detail-section">
              <h3>{t("caseHistory")}</h3>
              <ul className="adm-timeline">
                {history.map((h, index) => (
                  <li key={index} className="adm-tl-item">
                    <span className="adm-tl-dot" aria-hidden="true" />
                    <div className="adm-tl-body">
                      <p className="adm-tl-text">
                        {h.action ? actionName(h.action) : ""}
                        {h.by ? ` · ${h.by}` : ""}
                      </p>
                      {h.notes && <p className="adm-tl-note">{h.notes}</p>}
                      {h.at && <time className="adm-tl-time">{formatDateTime(h.at, lang)}</time>}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </article>
  );
}

const ISO = /^\d{4}-\d{2}-\d{2}T/;
// Machine fields a person does not need to decide: identifiers, slugs, links.
const HIDDEN = /(^|_)(id|ids|member_id|account_id|profile_id|slug|deep_link|url)$/;

/** Renders a module's opaque case detail readably: words for keys, dates in Indian order, no raw ids. */
function Fact({ name, value }: { name: string; value: unknown }) {
  const { lang } = useConsole();
  if (value === null || value === undefined || value === "" || HIDDEN.test(name)) return null;
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    if (value.every((v) => typeof v !== "object")) return <Fact name={name} value={value.join(", ")} />;
    return (
      <>
        {value.map((v, i) => (
          <Fact key={i} name={`${name} ${i + 1}`} value={v} />
        ))}
      </>
    );
  }
  if (typeof value === "object") {
    // A person object ({display_name, ...ids}) reads as just the name.
    const person = value as { display_name?: unknown };
    if (typeof person.display_name === "string") return <Fact name={name} value={person.display_name} />;
    const entries = Object.entries(value as Record<string, unknown>).filter(([k, v]) => v !== null && v !== "" && !HIDDEN.test(k));
    if (!entries.length) return null;
    return (
      <div className="adm-fact-group">
        <dt>{humanise(name)}</dt>
        <dd>
          <dl className="adm-facts nested">
            {entries.map(([k, v]) => (
              <Fact key={k} name={k} value={v} />
            ))}
          </dl>
        </dd>
      </div>
    );
  }
  const text = typeof value === "boolean" ? (value ? "✓" : "—") : typeof value === "string" && ISO.test(value) ? formatDateTime(value, lang) : String(value);
  return (
    <div className="adm-fact">
      <dt>{humanise(name)}</dt>
      <dd>{text}</dd>
    </div>
  );
}
