"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import AgentPlanCheckout from "@/components/AgentPlanCheckout";
import { NumberPrivacy, ReportUnwanted } from "@/components/ContactSafety";
import { Avatar } from "@/components/Avatar";
import ForKhatriHubLink from "@/components/ForKhatriHubLink";
import OfflineBiodataCard from "@/components/OfflineBiodataCard";
import {
  answerShared,
  chooseAgent,
  formatDay,
  getDashboard,
  getDirectory,
  isToday,
  releaseAgent,
  setAgentsMaySeeContact,
  type Dashboard,
  type Decision,
  type DirectoryAgent,
  type Shared,
} from "@/lib/agents";
import { resolveMediaUrl } from "@/lib/api";
import { getSession, type Session } from "@/lib/auth";
import {
  listMessages,
  openDirect,
  sendMessage,
  threadHref,
  type Message,
} from "@/lib/messages";

import "../agent/agent.css";

/* [DEC-V1-033] The family's agent dashboard. The owner (2026-09-29): people
 * connect to an agent "to enhance their profiling", the agent shares profiles
 * on Mangaly and beyond, connecting is a premium tier an administrator
 * prices, and the family gets a dashboard — "communication on the right side,
 * middle part profiles of the day, and down all the old profiles."
 *
 * Research (matchmaker portals, Hinge/CMB daily batches, WhatsApp biodata
 * habits) refined it: a slim left rail for the agents, the answer filters,
 * the number switch and what agents did; the feed in the middle with Today on
 * top and earlier shares grouped by day below (kept, never expiring — a
 * family decides more slowly than a dating app); the chat with the agent on
 * the right, where the family's answers also appear as small lines, so the
 * agent's thread is the whole story. Every share is Interested / Not for us /
 * Ask the agent. Biodata of someone not on Mangaly is its own card, always
 * labelled. On a phone: Profiles and Chat as two tabs. */

type Filter = "all" | "new" | "liked" | "passed" | "ask";

function AgentsDashboard() {
  const { t, i18n } = useTranslation(["agents", "common", "profile"]);
  const params = useSearchParams();
  const forCandidate = params.get("for") ?? undefined;
  const [dash, setDash] = useState<Dashboard | null | undefined>(undefined);
  const [directory, setDirectory] = useState<DirectoryAgent[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [chatAgent, setChatAgent] = useState<string | null>(null);
  const [mobileTab, setMobileTab] = useState<"profiles" | "chat">("profiles");
  const [stopping, setStopping] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);

  const reload = useCallback(async () => {
    const d = await getDashboard(forCandidate);
    setDash(d);
    if (d && d.agents.length && !chatAgent)
      setChatAgent(d.agents[0].agent?.account_id ?? null);
  }, [forCandidate, chatAgent]);

  useEffect(() => {
    let alive = true;
    getDashboard(forCandidate).then((d) => {
      if (!alive) return;
      setDash(d);
      if (d && d.agents.length)
        setChatAgent((c) => c ?? d.agents[0].agent?.account_id ?? null);
    });
    getDirectory().then((x) => alive && setDirectory(x));
    // Whose search this is: a parent sees "For Kavya Rao".
    getSession()
      .then((x) => alive && setSession(x))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [forCandidate]);

  // The session names circles by the candidate's account; the URL may carry
  // their profile id — the dashboard answers with the account.
  const forName =
    session?.circles.find(
      (c) =>
        c.candidate_profile_id === forCandidate ||
        c.candidate_profile_id === dash?.candidate_account_id,
    )?.candidate_name ??
    (forCandidate ? null : (session?.own_profile?.name ?? null));

  const agentName = useMemo(() => {
    const names: Record<string, string> = {};
    for (const a of dash?.agents ?? [])
      if (a.agent) names[a.agent.account_id] = a.agent.display_name;
    return names;
  }, [dash]);

  if (dash === undefined) {
    return (
      <Frame>
        <p className="caption">{t("common:state.loading")}</p>
      </Frame>
    );
  }
  if (dash === null) {
    return (
      <Frame>
        <p className="ag-error">
          {t("common:state.error", { defaultValue: "Something went wrong." })}
        </p>
      </Frame>
    );
  }

  const connected = !!dash.agent_connect_until;
  const chosenIds = new Set(dash.agents.map((a) => a.agent?.account_id));

  const choose = async (agent: DirectoryAgent) => {
    setError(null);
    const out = await chooseAgent(agent.account_id, forCandidate);
    if (!out.ok) {
      setError(out.message ?? null);
      return;
    }
    setChatAgent(agent.account_id);
    await reload();
  };

  const stop = async (agentId: string) => {
    const out = await releaseAgent(agentId, forCandidate);
    setStopping(null);
    if (out.ok) {
      if (chatAgent === agentId) setChatAgent(null);
      await reload();
    }
  };

  const togglePrivacy = async (open: boolean) => {
    setDash({ ...dash, agents_may_see_contact: open });
    const out = await setAgentsMaySeeContact(open, forCandidate);
    if (!out.ok) setDash({ ...dash });
  };

  const onAnswered = (s: Shared) =>
    setDash((d) =>
      d
        ? {
            ...d,
            shared: d.shared.map((x) =>
              x.suggestion_id === s.suggestion_id ? s : x,
            ),
          }
        : d,
    );

  /* ---- not connected yet: what it is, the price, who the agents are ---- */
  if (!connected) {
    return (
      <Frame>
        <div className="ag-connect">
          <div className="ag-head" style={{ gap: "var(--space-4)" }}>
            {forName && (
              <p className="ag-eyebrow">
                {t("agents:family.for", { name: forName })}
              </p>
            )}
            <h2 className="ag-title">{t("agents:family.connect.title")}</h2>
            <p className="ag-lede">{t("agents:family.lede")}</p>
            <ul className="ag-benefits">
              {(["point1", "point2", "point3", "point4"] as const).map(
                (k, i) => (
                  <li key={k}>
                    <span className="ag-benefits__mark">{i + 1}</span>
                    <span>{t(`agents:family.connect.${k}`)}</span>
                  </li>
                ),
              )}
            </ul>
          </div>
          <div className="card ag-form">
            {dash.may_decide ? (
              <AgentPlanCheckout code="AGENT_CONNECT" onPaid={reload} />
            ) : (
              <p className="caption">
                {t("agents:family.connect.onlyParents")}
              </p>
            )}
            <Link
              href={`/me/contact-safety${forCandidate ? `?for=${forCandidate}` : ""}`}
              className="btn btn--ghost btn--sm"
              style={{ alignSelf: "flex-start" }}
              prefetch={false}
            >
              {t("agents:safety.link")}
            </Link>
          </div>
        </div>
        <Directory
          agents={directory}
          chosen={chosenIds}
          canChoose={false}
          onChoose={choose}
        />
      </Frame>
    );
  }

  /* ---- connected ---- */
  const shared = dash.shared.filter((s) =>
    filter === "all"
      ? true
      : filter === "new"
        ? !s.decision
        : s.decision === filter,
  );
  const today = shared.filter((s) => isToday(s.shared_at));
  const earlierByDay = new Map<string, Shared[]>();
  for (const s of shared.filter((x) => !isToday(x.shared_at))) {
    const day = s.shared_at.slice(0, 10);
    earlierByDay.set(day, [...(earlierByDay.get(day) ?? []), s]);
  }
  const counts: Record<Filter, number> = {
    all: dash.shared.length,
    new: dash.shared.filter((s) => !s.decision).length,
    liked: dash.shared.filter((s) => s.decision === "liked").length,
    passed: dash.shared.filter((s) => s.decision === "passed").length,
    ask: dash.shared.filter((s) => s.decision === "ask").length,
  };
  const activeChat =
    dash.agents.find((a) => a.agent?.account_id === chatAgent)?.agent ?? null;

  return (
    <Frame>
      <div className="ag-bar">
        <div className="ag-head">
          {forName && (
            <p className="ag-eyebrow">
              {t("agents:family.for", { name: forName })}
            </p>
          )}
          <span className="caption">
            {t("agents:family.connect.active", {
              date: formatDay(dash.agent_connect_until, i18n.language),
            })}
          </span>
        </div>
      </div>
      {error && <p className="ag-error">{error}</p>}

      {dash.agents.length === 0 ? (
        <Directory
          agents={directory}
          chosen={chosenIds}
          canChoose={dash.may_decide}
          onChoose={choose}
        />
      ) : (
        <>
          <div className="ag-dash__mobile-tabs" role="tablist">
            {(["profiles", "chat"] as const).map((x) => (
              <button
                key={x}
                type="button"
                role="tab"
                className="ag-tab"
                aria-selected={mobileTab === x}
                onClick={() => setMobileTab(x)}
              >
                {t(`agents:family.tabs.${x}`)}
              </button>
            ))}
          </div>
          <div className="ag-dash" data-tab={mobileTab}>
            {/* ---- left: our agents, filters, the number switch, activity ---- */}
            <aside className="ag-dash__side">
              <div className="ag-head">
                <span className="label">{t("agents:family.yours")}</span>
                {dash.agents.map((a) =>
                  a.agent ? (
                    <div
                      key={a.assignment_id}
                      className={`ag-agent${a.agent.account_id === chatAgent ? " is-active" : ""}`}
                    >
                      <div className="ag-agent__head">
                        <Avatar
                          name={a.agent.display_name}
                          photoUrl={resolveMediaUrl(a.agent.photo_url)}
                          size={36}
                        />
                        <div style={{ minWidth: 0 }}>
                          <div className="ag-agent__name">
                            {a.agent.display_name}
                          </div>
                          <div className="ag-agent__biz">
                            {[a.agent.business_name, a.agent.city]
                              .filter(Boolean)
                              .join(" · ")}
                          </div>
                        </div>
                      </div>
                      <span
                        className="ag-pill ag-pill--quiet"
                        style={{ alignSelf: "flex-start" }}
                      >
                        {t(`agents:stage.${a.stage}`)}
                      </span>
                      <div className="ag-row">
                        <button
                          type="button"
                          className="btn btn--secondary btn--sm"
                          onClick={() => {
                            setChatAgent(a.agent!.account_id);
                            setMobileTab("chat");
                          }}
                        >
                          {t("agents:family.message")}
                        </button>
                        {dash.may_decide &&
                          (stopping === a.agent.account_id ? (
                            <button
                              type="button"
                              className="btn btn--danger btn--sm"
                              onClick={() => stop(a.agent!.account_id)}
                            >
                              {t("agents:family.stopConfirm")}
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="btn btn--ghost btn--sm"
                              onClick={() => setStopping(a.agent!.account_id)}
                              title={t("agents:family.stop", {
                                name: a.agent.display_name,
                              })}
                            >
                              {t("agents:family.stopConfirm")}
                            </button>
                          ))}
                      </div>
                    </div>
                  ) : null,
                )}
              </div>
              {dash.shared.length > 0 && (
                <div
                  className="ag-chips"
                  style={{ flexWrap: "wrap" }}
                  role="group"
                >
                  {(["all", "new", "liked", "passed", "ask"] as Filter[]).map(
                    (f) => (
                      <button
                        key={f}
                        type="button"
                        className="ag-chip"
                        aria-pressed={filter === f}
                        onClick={() => setFilter(f)}
                      >
                        {t(`agents:family.filter.${f}`)}
                        <span className="ag-chip__n">{counts[f]}</span>
                      </button>
                    ),
                  )}
                </div>
              )}
              <NumberPrivacy dash={dash} onToggle={togglePrivacy} />
              <ReportUnwanted
                forCandidate={forCandidate}
                numberOpen={dash.agents_may_see_contact !== false}
                mayDecide={dash.may_decide}
                onCloseNumber={() => togglePrivacy(false)}
              />
            </aside>

            {/* ---- middle: today, then earlier by day ---- */}
            <section className="ag-dash__feed">
              <div className="ag-day ag-day--today">
                <h2 className="ag-day__title">
                  {t("agents:family.today")}
                  <span className="caption">
                    {formatDay(new Date().toISOString(), i18n.language)}
                  </span>
                </h2>
                {today.length === 0 ? (
                  <p className="caption" style={{ margin: 0 }}>
                    {dash.shared.length === 0
                      ? t("agents:family.empty")
                      : t("agents:family.todayEmpty")}
                  </p>
                ) : (
                  <ul className="ag-feed">
                    {today.map((s) => (
                      <li key={s.suggestion_id}>
                        <SharedCard
                          shared={s}
                          agentName={agentName[s.agent_account_id] ?? ""}
                          forCandidate={forCandidate}
                          onAnswered={onAnswered}
                        />
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {earlierByDay.size > 0 && (
                <h2 className="ag-day__title">{t("agents:family.earlier")}</h2>
              )}
              {[...earlierByDay.entries()].map(([day, items]) => (
                <div key={day} className="ag-day">
                  <span className="label">
                    {formatDay(`${day}T12:00:00`, i18n.language)}
                  </span>
                  <ul className="ag-feed">
                    {items.map((s) => (
                      <li key={s.suggestion_id}>
                        <SharedCard
                          shared={s}
                          agentName={agentName[s.agent_account_id] ?? ""}
                          forCandidate={forCandidate}
                          onAnswered={onAnswered}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              {dash.may_decide && (
                <details>
                  <summary className="caption" style={{ cursor: "pointer" }}>
                    {t("agents:family.directory.title")}
                  </summary>
                  <Directory
                    agents={directory}
                    chosen={chosenIds}
                    canChoose
                    onChoose={choose}
                    bare
                  />
                </details>
              )}
            </section>

            {/* ---- right: the conversation with the agent ---- */}
            <section className="ag-dash__chat">
              {activeChat ? (
                <AgentChat
                  key={activeChat.account_id}
                  agent={activeChat}
                  shared={dash.shared}
                />
              ) : (
                <p className="caption">{t("agents:family.chat.choose")}</p>
              )}
            </section>
          </div>
        </>
      )}
    </Frame>
  );
}

function Frame({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation(["agents"]);
  return (
    <>
      <header className="topbar">
        <h1 className="topbar__title">{t("agents:family.title")}</h1>
        <div className="topbar__actions">
          <ForKhatriHubLink />
          <AccountButton />
        </div>
      </header>
      <main className="screen ag-screen">{children}</main>
    </>
  );
}

/* ---------------------------------------------------------------------------
 * One shared profile, with the family's answer
 * ------------------------------------------------------------------------- */

function SharedCard({
  shared,
  agentName,
  forCandidate,
  onAnswered,
}: {
  shared: Shared;
  agentName: string;
  forCandidate?: string;
  onAnswered: (s: Shared) => void;
}) {
  const { t } = useTranslation(["agents", "profile"]);
  const [open, setOpen] = useState(false);
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);

  const answer = async (decision: Decision) => {
    setBusy(true);
    const out = await answerShared(
      shared.suggestion_id,
      decision,
      decision === "ask" ? question : undefined,
      forCandidate,
    );
    setBusy(false);
    if (out.ok) {
      setAsking(false);
      onAnswered(out.data);
    }
  };

  const p = shared.person;
  const decided = shared.decision;
  const actions = (
    <div className="ag-card__actions">
      {decided && decided !== "ask" && (
        <span className="ag-card__answer">
          {t("agents:family.answer.yours", {
            answer: t(`agents:family.answer.${decided}`),
          })}
        </span>
      )}
      {decided === "ask" && shared.question && (
        <span className="ag-card__answer">
          {t("agents:family.answer.asked", { question: shared.question })}
        </span>
      )}
      {decided !== "liked" && (
        <button
          type="button"
          className="btn btn--primary btn--sm"
          disabled={busy}
          onClick={() => answer("liked")}
        >
          {t("agents:family.answer.liked")}
        </button>
      )}
      {decided !== "passed" && (
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          disabled={busy}
          onClick={() => answer("passed")}
        >
          {t("agents:family.answer.passed")}
        </button>
      )}
      {!asking && (
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={() => setAsking(true)}
        >
          {t("agents:family.answer.ask", { name: agentName.split(" ")[0] })}
        </button>
      )}
    </div>
  );
  const ask = asking && (
    <div className="ag-form">
      <textarea
        className="textarea"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        maxLength={1000}
        autoFocus
        placeholder={t("agents:family.answer.askPlaceholder")}
      />
      <div className="ag-row">
        <button
          type="button"
          className="btn btn--primary btn--sm"
          disabled={busy || !question.trim()}
          onClick={() => answer("ask")}
        >
          {t("agents:family.answer.send")}
        </button>
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={() => setAsking(false)}
        >
          {t("common:action.cancel", { defaultValue: "Cancel" })}
        </button>
      </div>
    </div>
  );
  const note = shared.note && (
    <blockquote className="ag-card__note">
      <span
        className="rm-tile__by"
        style={{
          display: "block",
          fontSize: "0.75rem",
          fontWeight: 600,
          color: "var(--accent)",
        }}
      >
        {t("agents:family.sharedBy", { name: agentName })}
      </span>
      {shared.note}
    </blockquote>
  );

  if (shared.offline) {
    return (
      <div className={`ag-card-stack${decided ? ` ag-card--${decided}` : ""}`}>
        <OfflineBiodataCard profile={shared.offline} open={open} bare />
        <p className="ag-card__warn">{t("agents:family.notVerified")}</p>
        {note}
        <div className="ag-row">
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? t("agents:family.hide") : t("agents:family.viewBiodata")}
          </button>
        </div>
        {actions}
        {ask}
      </div>
    );
  }

  const title = p?.open_name
    ? [p.open_name, p.age].filter(Boolean).join(", ")
    : p?.age
      ? t("agents:family.age", { age: p.age })
      : "";
  return (
    <div className={`ag-card${decided ? ` ag-card--${decided}` : ""}`}>
      <Link
        href={`/profile/${shared.member_account_id}`}
        className="ag-card__photo"
        prefetch={false}
      >
        {p?.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={resolveMediaUrl(p.photo_url) ?? ""}
            alt=""
            loading="lazy"
            decoding="async"
          />
        ) : (
          <Avatar anonymized size={56} />
        )}
      </Link>
      <div className="ag-card__body">
        <span
          className="ag-pill ag-pill--ok"
          style={{ alignSelf: "flex-start" }}
        >
          {t("agents:family.onMangaly")}
        </span>
        <span className="ag-card__title">
          {[title, p?.locality?.split(",")[0]?.trim()]
            .filter(Boolean)
            .join(" · ")}
        </span>
        {(p?.profession || p?.education_level) && (
          <span className="ag-card__line">
            {[p?.profession, p?.education_level ? t(`profile:option.highest_education_level.${p?.education_level}`, { defaultValue: p?.education_level.replace(/_/g, " ") }) : null].filter(Boolean).join(" · ")}
          </span>
        )}
        {note}
        <Link
          href={`/profile/${shared.member_account_id}`}
          className="btn btn--ghost btn--sm"
          style={{ alignSelf: "flex-start" }}
          prefetch={false}
        >
          {t("agents:family.view")}
        </Link>
        {actions}
        {ask}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * The agent directory
 * ------------------------------------------------------------------------- */

function Directory({
  agents,
  chosen,
  canChoose,
  onChoose,
  bare = false,
}: {
  agents: DirectoryAgent[] | null;
  chosen: Set<string | undefined>;
  canChoose: boolean;
  onChoose: (a: DirectoryAgent) => void;
  bare?: boolean;
}) {
  const { t } = useTranslation(["agents"]);
  return (
    <section
      className="section"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3)",
      }}
    >
      {!bare && (
        <h2 className="h3" style={{ margin: 0 }}>
          {t("agents:family.directory.title")}
        </h2>
      )}
      {agents === null ? null : agents.length === 0 ? (
        <p className="caption">{t("agents:family.directory.empty")}</p>
      ) : (
        <ul className="ag-directory">
          {agents.map((a) => (
            <li key={a.account_id} className="ag-agent">
              <div className="ag-agent__head">
                <Avatar
                  name={a.display_name}
                  photoUrl={resolveMediaUrl(a.photo_url)}
                  size={48}
                />
                <div style={{ minWidth: 0 }}>
                  <div className="ag-agent__name">
                    {a.business_name ?? a.display_name}
                  </div>
                  <div className="ag-agent__biz">
                    {[a.business_name ? a.display_name : null, a.city]
                      .filter(Boolean)
                      .join(" · ")}
                  </div>
                </div>
              </div>
              <div className="ag-row">
                <span className="ag-pill ag-pill--ok">
                  {t("agents:status.verified")}
                </span>
                {a.years_active != null && (
                  <span className="ag-pill ag-pill--quiet">
                    {t("agents:family.directory.years", {
                      count: a.years_active,
                    })}
                  </span>
                )}
                {a.families > 0 && (
                  <span className="ag-pill ag-pill--quiet">
                    {t("agents:family.directory.families", {
                      count: a.families,
                    })}
                  </span>
                )}
                {a.marriages > 0 && (
                  <span className="ag-pill ag-pill--quiet">
                    {t("agents:family.directory.marriages", {
                      count: a.marriages,
                    })}
                  </span>
                )}
              </div>
              {a.communities.length > 0 && (
                <span className="caption">{a.communities.join(", ")}</span>
              )}
              {a.about && (
                <p className="caption" style={{ margin: 0 }}>
                  {a.about}
                </p>
              )}
              <div className="ag-row">
                {chosen.has(a.account_id) ? (
                  <span className="ag-ok">
                    {t("agents:family.directory.chosen")}
                  </span>
                ) : (
                  canChoose && (
                    <button
                      type="button"
                      className="btn btn--primary btn--sm"
                      onClick={() => onChoose(a)}
                    >
                      {t("agents:family.directory.choose")}
                    </button>
                  )
                )}
                {a.business_phone && (
                  <a
                    className="btn btn--ghost btn--sm"
                    href={`tel:${a.business_phone}`}
                  >
                    {t("agents:family.directory.call")}
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------------------
 * The chat with the agent (an ordinary one-to-one chat, DEC-V1-026), with the
 * family's answers woven in as small lines so the thread tells the whole story.
 * ------------------------------------------------------------------------- */

function AgentChat({
  agent,
  shared,
}: {
  agent: DirectoryAgent;
  shared: Shared[];
}) {
  const { t, i18n } = useTranslation(["agents"]);
  const [conversation, setConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [me, setMe] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const list = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    getSession().then((s) => alive && setMe(s?.account_id ?? null));
    openDirect(agent.account_id).then(
      (r) => alive && r.ok && setConversation(r.data.conversation_id),
    );
    return () => {
      alive = false;
    };
  }, [agent.account_id]);

  useEffect(() => {
    if (!conversation) return;
    let alive = true;
    const load = () =>
      listMessages(conversation, "direct").then((m) => alive && setMessages(m));
    void load();
    const timer = window.setInterval(load, 8000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [conversation]);

  const events = shared
    .filter(
      (s) =>
        s.agent_account_id === agent.account_id && s.decided_at && s.decision,
    )
    .map((s) => {
      const who =
        s.offline?.name ??
        s.person?.open_name ??
        t("agents:family.age", { age: s.person?.age ?? "" });
      const line =
        s.decision === "ask"
          ? t("agents:family.answer.asked", { question: s.question ?? "" })
          : t("agents:family.answer.yours", {
              answer: t(`agents:family.answer.${s.decision}`),
            });
      return {
        id: `e-${s.suggestion_id}`,
        at: s.decided_at as string,
        text: `${who}: ${line}`,
      };
    });

  const timeline = [
    ...messages.map((m) => ({ id: m.id, at: m.sent_at, message: m })),
    ...events.map((e) => ({ id: e.id, at: e.at, event: e.text })),
  ].sort((a, b) => a.at.localeCompare(b.at));

  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight });
  }, [timeline.length]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!conversation || !text.trim()) return;
    setSending(true);
    const out = await sendMessage(conversation, text.trim(), "direct");
    setSending(false);
    if (out.ok) {
      setText("");
      setMessages((m) => [...m, out.data]);
    }
  };

  const time = (iso: string) =>
    new Date(iso).toLocaleString(
      i18n.language === "en" ? "en-IN" : `${i18n.language}-IN`,
      {
        day: "numeric",
        month: "short",
        hour: "numeric",
        minute: "2-digit",
      },
    );

  return (
    <div className="ag-chat">
      <div className="ag-chat__head">
        <Avatar
          name={agent.display_name}
          photoUrl={resolveMediaUrl(agent.photo_url)}
          size={32}
        />
        <span className="ag-chat__who">
          {t("agents:family.chat.title", { name: agent.display_name })}
        </span>
        {conversation && (
          <Link
            className="btn btn--ghost btn--sm"
            href={threadHref(conversation, "direct")}
            prefetch={false}
          >
            {t("agents:family.chat.open")}
          </Link>
        )}
      </div>
      <div className="ag-chat__list" ref={list}>
        {timeline.length === 0 && (
          <p className="caption">{t("agents:family.chat.empty")}</p>
        )}
        {timeline.map((item) =>
          "event" in item ? (
            <span key={item.id} className="ag-bubble ag-bubble--event">
              {item.event}
            </span>
          ) : (
            <span
              key={item.id}
              className={`ag-bubble${item.message.sender_account_id === me ? " ag-bubble--me" : ""}`}
            >
              {item.message.content}
              <span className="ag-bubble__time">{time(item.at)}</span>
            </span>
          ),
        )}
      </div>
      <form className="ag-chat__form" onSubmit={send}>
        <input
          className="input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("agents:family.chat.placeholder", {
            name: agent.display_name.split(" ")[0],
          })}
          aria-label={t("agents:family.chat.placeholder", {
            name: agent.display_name.split(" ")[0],
          })}
        />
        <button
          type="submit"
          className="btn btn--primary btn--sm"
          disabled={sending || !text.trim() || !conversation}
        >
          {t("agents:family.chat.send")}
        </button>
      </form>
    </div>
  );
}

export default function AgentsPage() {
  return (
    <Suspense fallback={null}>
      <AgentsDashboard />
    </Suspense>
  );
}
