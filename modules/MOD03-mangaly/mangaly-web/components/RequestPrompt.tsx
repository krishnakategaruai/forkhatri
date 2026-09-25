"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import { getSession, type Session } from "@/lib/auth";
import {
  accept,
  decline,
  listIncoming,
  type Connection,
} from "@/lib/connections";
import { listMembers, relationKey } from "@/lib/homeCircle";

/* [Owner, 2026-09-21] "A profile request always gets a popup for the parent
 * and the candidate — mother, father, candidate — and any one can accept."
 *
 * Shown on every screen to the candidate and to each mother, father or
 * guardian in their circle (siblings and relatives see requests on the Circle
 * screen but do not decide). Whoever answers first answers for the family:
 * the request is no longer pending, so it disappears from everyone else's
 * popup. "Not now" hides it for this sitting only — a request never lapses
 * silently (FR043).
 *
 * What the card shows is what that reader may see before a connection: the
 * pre-connection-safe snippet (age, city, education, work, main photo) and who
 * sent it. "View profile" opens the profile in the reader's own lens — the
 * biodata for a parent, the candidate view for the candidate. */

type Pending = { request: Connection; forCandidate?: string; forName?: string; asRelation?: string };

const DISMISSED_KEY = "mangaly.requestPrompt.dismissed";

function dismissedIds(): Set<string> {
  try {
    return new Set(JSON.parse(sessionStorage.getItem(DISMISSED_KEY) ?? "[]") as string[]);
  } catch {
    return new Set();
  }
}

function dismiss(id: string) {
  try {
    const next = dismissedIds();
    next.add(id);
    sessionStorage.setItem(DISMISSED_KEY, JSON.stringify([...next]));
  } catch {
    /* private mode: the prompt simply returns next time */
  }
}

async function collect(session: Session): Promise<Pending[]> {
  const jobs: Promise<Pending[]>[] = [];
  if (session.own_profile) {
    jobs.push(listIncoming().then((rows) => rows.map((request) => ({ request }))));
  }
  for (const c of session.circles) {
    if (c.relationship !== "parent" && c.relationship !== "guardian") continue;
    const id = c.candidate_account_id;
    jobs.push(
      listIncoming(id).then((rows) =>
        rows.map((request) => ({
          request,
          forCandidate: id,
          forName: c.candidate_name,
          asRelation: c.relation ?? undefined,
        })),
      ),
    );
  }
  const all = (await Promise.all(jobs)).flat();
  const hidden = dismissedIds();
  return all.filter((p) => p.request.status === "pending" && !hidden.has(p.request.id));
}

export default function RequestPrompt() {
  const { t } = useTranslation(["common", "circle", "profile"]);
  const pathname = usePathname();
  const [queue, setQueue] = useState<Pending[]>([]);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  // Whether the candidate's own circle has a parent or guardian: only then
  // does "your parents can also answer this" tell the truth.
  const [hasParents, setHasParents] = useState(false);

  useEffect(() => {
    let alive = true;
    getSession()
      .then(async (s) => {
        if (!s) return [];
        if (s.own_profile) {
          const members = await listMembers().catch(() => []);
          if (alive) {
            setHasParents(
              members.some(
                (m) =>
                  m.status === "active" &&
                  (m.relationship_type === "parent" || m.relationship_type === "guardian"),
              ),
            );
          }
        }
        return collect(s);
      })
      .then((q) => alive && setQueue(q))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [pathname]);

  const current = queue[0];
  if (!current && !done) return null;

  if (done) {
    return (
      <div className="reqpop reqpop--done" role="status">
        <p>{done}</p>
        <button type="button" className="btn btn--ghost" onClick={() => setDone(null)}>
          {t("common:action.close", { defaultValue: "Close" })}
        </button>
      </div>
    );
  }

  const r = current.request;
  const who =
    r.subject_name ?? r.subject?.open_name ?? t("common:requestPrompt.someone");
  const facts = [
    r.subject?.age ? t("profile:hub.ageYears", { age: r.subject.age }) : null,
    r.subject?.locality,
  ]
    .filter(Boolean)
    .join(" · ");
  const work = [
    r.subject?.education_level
      ? t(`profile:option.highest_education_level.${r.subject.education_level}`)
      : null,
    r.subject?.profession,
  ]
    .filter(Boolean)
    .join(" · ");
  const sentBy = r.sent_by
    ? t("common:requestPrompt.sentBy", {
        name: r.sent_by.display_name ?? "",
        relation: t(`circle:invite.relationshipOption.${r.sent_by.relationship}`).toLowerCase(),
      })
    : null;

  async function answer(yes: boolean) {
    setBusy(true);
    const outcome = yes
      ? await accept(r.id, current.forCandidate)
      : await decline(r.id, current.forCandidate);
    setBusy(false);
    if (!outcome.ok) return;
    setQueue((q) => q.slice(1));
    if (yes) {
      setDone(
        current.forName
          ? t("common:requestPrompt.acceptedFor", { name: current.forName.split(" ")[0] })
          : t("common:requestPrompt.accepted"),
      );
    }
  }

  return (
    <div className="reqpop" role="dialog" aria-modal="false" aria-labelledby="reqpop-title">
      <span className="reqpop__eyebrow">
        {current.forName
          ? t("common:requestPrompt.forCandidate", {
              name: current.forName.split(" ")[0],
              relation: current.asRelation
                ? t(relationKey(current.asRelation, "parent"))
                : t("circle:invite.relationshipOption.parent"),
            })
          : t("common:requestPrompt.forYou")}
      </span>
      <div className="reqpop__card">
        <Avatar photoUrl={r.subject?.photo_url} name={r.subject_name ?? undefined} size={64} />
        <div className="reqpop__text">
          <h2 id="reqpop-title" className="reqpop__title">
            {t("common:requestPrompt.title", { name: who })}
          </h2>
          {facts && <span className="reqpop__facts">{facts}</span>}
          {work && <span className="caption">{work}</span>}
          {sentBy && <span className="caption">{sentBy}</span>}
        </div>
      </div>
      <p className="caption reqpop__note">
        {current.forName
          ? t("common:requestPrompt.noteFamily", { name: current.forName.split(" ")[0] })
          : hasParents
            ? t("common:requestPrompt.noteSelf")
            : t("common:requestPrompt.noteSelfAlone")}
      </p>
      <div className="reqpop__actions">
        <Link
          className="btn btn--ghost"
          href={`/profile/${r.subject_account_id}`}
          onClick={() => {
            dismiss(r.id);
            setQueue((q) => q.slice(1));
          }}
        >
          {t("common:requestPrompt.view")}
        </Link>
        <button
          type="button"
          className="btn btn--ghost"
          disabled={busy}
          onClick={() => {
            dismiss(r.id);
            setQueue((q) => q.slice(1));
          }}
        >
          {t("common:requestPrompt.notNow")}
        </button>
        <button type="button" className="btn btn--ghost" disabled={busy} onClick={() => void answer(false)}>
          {t("common:requestPrompt.decline")}
        </button>
        <button type="button" className="btn btn--primary" disabled={busy} onClick={() => void answer(true)}>
          {t("common:requestPrompt.accept")}
        </button>
      </div>
      {queue.length > 1 && (
        <span className="caption reqpop__more">
          {t("common:requestPrompt.more", { count: queue.length - 1 })}
        </span>
      )}
    </div>
  );
}
