"use client";

// [TR026] Respond to and manage a business partnership request (FR26). Both
// sides see the same record: state first, the other business with its
// reputation line as trust context (FR25), the seven fields, contact
// details only once accepted (FR26, the same disclosure as requests), and
// exactly the actions this role and state allow. After Close, the review
// composer appears here (FR27); Report is always available (FR39).
// [Design language 2026-09-29] The record in the main column as a
// key/value grid; a sticky aside with the other business (a card that
// opens their profile) and the actions. The receiver's decision is a
// "your turn" banner with Accept as the one filled button.
// Traces to: FR25, FR26, FR27, FR39, TR026, UX17
import { useEffect, useState, use as useParamsPromise } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { AlertTriangle, ChevronRight, Handshake, Lock, MoreHorizontal, ShieldAlert, Undo2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { ReputationLine, type Reputation } from "@/app/components/Reputation";
import ReviewComposer from "@/app/components/ReviewComposer";
import ReportSheet from "@/app/components/ReportSheet";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import DealsEmpty from "@/app/components/deals/Empty";
import { formatDate } from "@/lib/format";
import "@/app/styles/deals-2026.css";

interface ListingSummary {
  id: string;
  name: string;
  kind: string;
  verification_state: string;
  reputation: Reputation | null;
}

interface Partnership {
  id: string;
  state: string;
  is_sender: boolean;
  need: string;
  offer: string;
  expectations: string;
  category: string;
  locality: string;
  timing: string;
  next_step: string;
  created_at: string;
  sender_listing: ListingSummary | null;
  recipient_listing: ListingSummary | null;
  disclosed_contacts: { channel: string; value: string }[];
}

const FIELDS: [keyof Partnership, string, boolean][] = [
  ["need", "compose.need", true],
  ["offer", "compose.offer", true],
  ["expectations", "compose.expectations", true],
  ["category", "compose.category", false],
  ["locality", "compose.locality", false],
  ["timing", "compose.timing", false],
  ["next_step", "compose.nextStep", false],
];

function stateTone(state: string): "wait" | "action" | "done" | "warn" | "muted" | undefined {
  switch (state) {
    case "pending":
      return "wait";
    case "accepted":
      return "action";
    case "closed":
      return "done";
    case "restricted":
      return "warn";
    case "declined":
    case "withdrawn":
      return "muted";
    default:
      return undefined;
  }
}

export default function PartnershipDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = useParamsPromise(params);
  const { t, i18n } = useTranslation(["partnerships", "common", "enquiries"]);
  const [request, setRequest] = useState<Partnership | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [more, setMore] = useState(false);
  // Older requests stored the category as a taxonomy slug; show its label.
  const [categoryLabels, setCategoryLabels] = useState<Record<string, string>>({});

  async function refresh() {
    try {
      setRequest(await api.get<Partnership>(`/v1/partnership-requests/${id}`));
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("partnerships:detail.notFound"));
    }
  }

  useEffect(() => {
    api
      .get<{ categories: { slug: string; label: string }[] }>("/v1/listings/search-suggestions")
      .then((d) => setCategoryLabels(Object.fromEntries(d.categories.map((c) => [c.slug, c.label]))))
      .catch(() => undefined);
    // The initial load runs once per id (the pattern this module's data hooks use).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function act(action: string) {
    setBusy(true);
    setNotice(null);
    setMore(false);
    try {
      await api.post(`/v1/partnership-requests/${id}/${action}`);
      await refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (error)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <DealsEmpty tone="neutral" icon={<AlertTriangle size={24} strokeWidth={1.75} aria-hidden="true" />} title={t("partnerships:detail.notFound")} body={error} />
        </div>
      </Screen>
    );
  if (!request)
    return (
      <Screen width="wide">
        <div className="vy-dl-page">
          <SkeletonGrid count={3} grid={false} />
        </div>
      </Screen>
    );

  const other = request.is_sender ? request.recipient_listing : request.sender_listing;
  const pending = request.state === "pending";
  const receiverDecides = !request.is_sender && pending;
  const quiet = (!request.is_sender && (pending || request.state === "accepted")) || (request.is_sender && pending);

  // Rarely used, cautious actions in one quiet menu (restrict, withdraw).
  const moreMenu = quiet ? (
    <div className="vy-dl-more">
      <button type="button" className="vy-iconbtn" aria-label={t("enquiries:detail.moreActions")} title={t("enquiries:detail.moreActions")} aria-haspopup="menu" aria-expanded={more} disabled={busy} onClick={() => setMore((v) => !v)}>
        <MoreHorizontal size={20} strokeWidth={2} aria-hidden="true" />
      </button>
      {more && (
        <div className="vy-dl-more-menu" role="menu">
          {request.is_sender && pending && (
            <button type="button" role="menuitem" onClick={() => act("withdraw")}>
              <Undo2 size={18} strokeWidth={1.75} aria-hidden="true" /> {t("partnerships:detail.withdraw")}
            </button>
          )}
          {!request.is_sender && (pending || request.state === "accepted") && (
            <button type="button" role="menuitem" data-danger onClick={() => act("restrict")}>
              <ShieldAlert size={18} strokeWidth={1.75} aria-hidden="true" /> {t("partnerships:detail.restrict")}
            </button>
          )}
        </div>
      )}
    </div>
  ) : null;

  const actionBlock = (
    <>
      {notice && (
        <p className="vy-dl-notice" data-tone="bad" role="alert">
          <AlertTriangle size={18} strokeWidth={1.75} aria-hidden="true" />
          <span>{notice}</span>
        </p>
      )}
      {request.is_sender && request.state === "declined" && <p className="vy-dl-hint">{t("partnerships:detail.declinedCooldown")}</p>}
      {request.state === "restricted" && <p className="vy-dl-hint">{t("partnerships:detail.restrictedNote")}</p>}
      {request.is_sender && pending && <p className="vy-dl-hint">{t("partnerships:detail.waitingLine", { name: other?.name ?? "" })}</p>}
      {request.state === "accepted" && (
        <div className="vy-dl-page" style={{ gap: 6 }}>
          <button className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start" }} disabled={busy} onClick={() => act("close")}>
            {t("partnerships:detail.close")}
          </button>
          <p className="vy-dl-fine">{t("partnerships:detail.closeHelp")}</p>
        </div>
      )}
    </>
  );

  return (
    <Screen width="wide">
      <div className="vy-dl-page">
        <Link href="/activity" transitionTypes={["vy-back"]} className="vy-dl-back">
          <ChevronRight size={18} strokeWidth={2} aria-hidden="true" style={{ transform: "rotate(180deg)" }} />
          {t("partnerships:detail.backToActivity")}
        </Link>
        <div className="vy-ctx">
          <div className="vy-ctx-grid">
            <div className="vy-ctx-main">
              <div className="vy-dl-sec-head vy-dl-sec-head-3">
                <div className="vy-dl-head" style={{ gridColumn: "1 / span 2" }}>
                  <div className="vy-dl-tags">
                    <span className="vy-dl-state" data-tone={stateTone(request.state)}>{t(`partnerships:state.${request.state}` as "state.pending")}</span>
                    <span className="vy-dl-state">{request.is_sender ? t("partnerships:detail.youSent") : t("partnerships:detail.youReceived")}</span>
                  </div>
                  <h1>{t("partnerships:detail.title")}</h1>
                  <p>{t("partnerships:detail.sentWith", { date: formatDate(request.created_at, i18n.language), name: other?.name ?? "" })}</p>
                </div>
                <div className="vy-dl-sec-head-end vy-ctx-narrow-only">{moreMenu}</div>
              </div>

              {receiverDecides && (
                <div className="vy-dl-turn" role="status">
                  <span className="vy-dl-tile vy-dl-tile-brand" aria-hidden="true"><Handshake size={20} strokeWidth={1.75} /></span>
                  <div className="vy-dl-row-body">
                    <strong>{t("partnerships:detail.turnTitle", { name: other?.name ?? "" })}</strong>
                    <span className="vy-dl-hint">{t("partnerships:detail.turnBody")}</span>
                  </div>
                  <div className="vy-dl-turn-actions">
                    <button className="vy-btn vy-btn-primary" disabled={busy} onClick={() => act("accept")}>{t("partnerships:detail.accept")}</button>
                    <button className="vy-btn vy-btn-secondary" disabled={busy} onClick={() => act("decline")}>{t("partnerships:detail.decline")}</button>
                  </div>
                </div>
              )}
            </div>

            <aside className="vy-ctx-aside">
              {other && (
                <Link className="vy-dl-sec" href={`/listings/${other.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                  <div className="vy-dl-sec-head vy-dl-sec-head-3">
                    <span className="vy-dl-avatar" aria-hidden="true">{(other.name.trim().charAt(0) || "?").toUpperCase()}</span>
                    <span className="vy-dl-row-body">
                      <span className="vy-dl-fine">{request.is_sender ? t("partnerships:detail.to") : t("partnerships:detail.from")}</span>
                      <strong className="vy-dl-row-title">{other.name}</strong>
                      <span className="vy-dl-row-meta"><ReputationLine rep={other.reputation} /></span>
                    </span>
                    <ChevronRight size={18} strokeWidth={2} aria-hidden="true" className="vy-dl-sec-head-end" style={{ color: "var(--text-tertiary)" }} />
                  </div>
                </Link>
              )}
              <div className="vy-ctx-wide-only vy-dl-actions" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                <div className="vy-dl-page" style={{ gap: "var(--space-2)", flex: 1 }}>{actionBlock}</div>
                {moreMenu}
              </div>
            </aside>

            <div className="vy-ctx-after">
              <section className="vy-dl-sec" aria-label={t("partnerships:detail.title")}>
                <dl className="vy-dl-kv">
                  {FIELDS.map(([field, key, wide]) => (
                    <div key={field} className={wide ? "vy-dl-kv-wide" : undefined}>
                      <dt>{t(`partnerships:${key}` as "compose.need")}</dt>
                      <dd>{field === "category" ? (categoryLabels[request.category] ?? request.category) : String(request[field] ?? "")}</dd>
                    </div>
                  ))}
                </dl>
              </section>

              {request.disclosed_contacts.length > 0 && (
                <section className="vy-dl-sec" aria-label={t("partnerships:detail.contactTitle")}>
                  <div className="vy-dl-sec-head">
                    <span className="vy-dl-tile vy-dl-tile-green" aria-hidden="true"><Handshake size={20} strokeWidth={1.75} /></span>
                    <h2 className="vy-card-title">{t("partnerships:detail.contactTitle")}</h2>
                    <span className="vy-dl-sec-hint">{t("partnerships:detail.contactHint")}</span>
                  </div>
                  <dl className="vy-dl-kv">
                    {request.disclosed_contacts.map((c) => (
                      <div key={c.channel}>
                        <dt>{t(`enquiries:channel.${c.channel}` as "channel.phone", { defaultValue: c.channel })}</dt>
                        <dd>{c.value}</dd>
                      </div>
                    ))}
                  </dl>
                  <p className="vy-dl-safety">
                    <Lock size={13} strokeWidth={2} aria-hidden="true" />
                    <span>{t("partnerships:detail.safety")}</span>
                  </p>
                </section>
              )}

              <div className="vy-ctx-contents vy-ctx-narrow-only">
                <div className="vy-dl-page" style={{ gap: "var(--space-2)" }}>{actionBlock}</div>
              </div>

              {request.state === "closed" && <ReviewComposer interactionKind="partnership" interactionId={id} />}
              <ReportSheet objectKind="partnership" objectId={id} />
            </div>
          </div>
        </div>
      </div>
    </Screen>
  );
}
