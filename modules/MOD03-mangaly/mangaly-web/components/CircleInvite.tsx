"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar } from "@/components/Avatar";
import {
  HOME_RELATIONS,
  RELATIVE_RELATIONS,
  RELATION_ROLE,
  invite,
  searchPeople,
  type Person,
  type Relation,
} from "@/lib/homeCircle";

/* The three ways into a Home Circle (DEC-V1-018, rework contract §3/§6), one
 * card:
 *
 *   own         a candidate adds family to their own circle
 *   join        anyone — typically a parent with no profile of their own —
 *               asks a candidate to let them into the candidate's circle.
 *               This is how a parent starts their child's search.
 *   forCandidate a member of someone's circle adds another relative to it
 *
 * People are found by name or phone among ForKhatri members; a typed phone
 * number still works for someone who has not joined yet (except in `join`,
 * where the candidate must already exist to own the circle). Nothing is
 * shared until the other person accepts. */

export type InviteMode = "own" | "join" | "forCandidate";

type Props = {
  mode: InviteMode;
  /** forCandidate: whose circle; used in copy and sent as `for_candidate`. */
  candidateAccountId?: string;
  candidateName?: string;
  onSent: () => void;
};

export default function CircleInvite({
  mode,
  candidateAccountId,
  candidateName,
  onSent,
}: Props) {
  const { t } = useTranslation(["common", "circle"]);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Person[]>([]);
  const [searching, setSearching] = useState(false);
  const [picked, setPicked] = useState<Person | null>(null);
  // Nothing pre-chosen: the exact relation is something only the person
  // filling this in knows, and a default would be a guess about their family.
  const [relation, setRelation] = useState<Relation | null>(null);
  const [showRelatives, setShowRelatives] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState<string | null>(null);

  const typedNumber = /^\+?\d[\d\s-]{6,}$/.test(q.trim())
    ? q.replace(/[\s-]/g, "")
    : null;

  // Search as you type, lightly debounced. State is only set from the timer
  // callback; a too-short term simply renders no results (see `shown`).
  useEffect(() => {
    const term = q.trim();
    if (picked || term.length < 2) return;
    let alive = true;
    const timer = window.setTimeout(async () => {
      const found = await searchPeople(term);
      if (!alive) return;
      // In `join` the invitee must be a candidate: only people with a profile.
      setResults(mode === "join" ? found.filter((p) => p.has_profile) : found);
      setSearching(false);
    }, 250);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [q, picked, mode]);
  const shown = q.trim().length >= 2 ? results : [];

  async function send() {
    if (!relation || (!picked && !(typedNumber && mode !== "join"))) return;
    setSending(true);
    setError(null);
    const outcome = await invite({
      ...(picked
        ? { invitee_account_id: picked.account_id }
        : { invitee_identifier: typedNumber! }),
      relation,
      relationship_type: RELATION_ROLE[relation],
      ...(mode === "join" ? { direction: "to_candidate" as const } : {}),
      ...(mode === "forCandidate" && candidateAccountId
        ? { for_candidate: candidateAccountId }
        : {}),
    });
    setSending(false);
    if (!outcome.ok) {
      setError(
        outcome.message ??
          (outcome.status === 0
            ? t("circle:error.network")
            : t("circle:error.alreadyInvited")),
      );
      return;
    }
    setSentTo(picked?.display_name ?? typedNumber);
    setPicked(null);
    setQ("");
    setResults([]);
    onSent();
  }

  const first = candidateName?.split(" ")[0] ?? "";
  const title =
    mode === "join"
      ? t("circle:invite.joinTitle")
      : mode === "forCandidate"
        ? t("circle:invite.forTitle", { name: first })
        : t("circle:invite.title");
  const hint =
    mode === "join"
      ? t("circle:invite.joinHint")
      : mode === "forCandidate"
        ? t("circle:invite.forHint", { name: first })
        : t("circle:invite.ownHint");

  return (
    <div className="card invite">
      <h2 className="h2" style={{ margin: 0 }}>
        {title}
      </h2>
      <p className="caption" style={{ margin: 0 }}>
        {hint}
      </p>

      {picked ? (
        <div className="person person--picked">
          <Avatar name={picked.display_name ?? undefined} size={44} />
          <span className="person__text">
            <span className="person__name">{picked.display_name}</span>
            <span className="caption">{picked.phone_masked}</span>
          </span>
          <button
            type="button"
            className="icon-btn icon-btn--text"
            onClick={() => setPicked(null)}
          >
            {t("circle:invite.change")}
          </button>
        </div>
      ) : (
        <>
          <div className="field__box">
            <input
              className="field__input"
              placeholder=" "
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setSearching(e.target.value.trim().length >= 2);
                setSentTo(null);
              }}
              autoComplete="off"
            />
            <label className="field__label">
              {mode === "join"
                ? t("circle:invite.searchCandidate")
                : t("circle:invite.search")}
            </label>
          </div>
          {shown.length > 0 && (
            <ul className="people">
              {shown.map((p) => (
                <li key={p.account_id}>
                  <button
                    type="button"
                    className="person"
                    onClick={() => setPicked(p)}
                  >
                    <Avatar name={p.display_name ?? undefined} size={40} />
                    <span className="person__text">
                      <span className="person__name">{p.display_name}</span>
                      <span className="caption">
                        {[
                          p.phone_masked,
                          p.has_profile ? t("circle:invite.hasProfile") : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {!searching && q.trim().length >= 2 && shown.length === 0 && (
            <p className="caption" style={{ margin: 0 }}>
              {mode === "join" ? (
                <>
                  {t("circle:invite.noCandidate")}{" "}
                  <Link className="link" href="/profile/create?for=child">
                    {t("circle:invite.createForThem")}
                  </Link>
                </>
              ) : null}
              {mode === "join"
                ? null
                : typedNumber
                  ? t("circle:invite.inviteNumber", { number: typedNumber })
                  : t("circle:invite.noOne")}
            </p>
          )}
        </>
      )}

      {/* A question and a row of chips, not a tab bar: this is one answer
          about a person, and the four choices carry the same permissions. */}
      <fieldset className="relpick">
        <legend className="relpick__q">
          {mode === "join"
            ? t("circle:invite.askJoin")
            : mode === "forCandidate"
              ? t("circle:invite.askFor", { name: first })
              : t("circle:invite.askOwn")}
        </legend>
        {(
          [
            ["home", HOME_RELATIONS],
            ["relatives", RELATIVE_RELATIONS],
          ] as const
        ).map(([group, list]) =>
          /* Relatives fold behind one chip: the household is the usual
             answer, and eleven more chips were a wall on a phone. */
          group === "relatives" &&
          !showRelatives &&
          !(RELATIVE_RELATIONS as readonly string[]).includes(relation ?? "") ? (
            <div key={group} className="relpick__chips">
              <button
                type="button"
                className="relchip relchip--more"
                onClick={() => setShowRelatives(true)}
              >
                {t("circle:invite.moreRelatives")} ▾
              </button>
            </div>
          ) : (
          <div key={group} className="relpick__group">
            {group === "relatives" && (
              <span className="relpick__group-title">
                {t(`circle:members.group.${group}`)}
              </span>
            )}
            <div className="relpick__chips" role="radiogroup">
              {list.map((r) => (
                <button
                  key={r}
                  type="button"
                  role="radio"
                  aria-checked={relation === r}
                  className={`relchip${relation === r ? " is-on" : ""}`}
                  onClick={() => setRelation(r)}
                >
                  {t(`circle:relation.${r}`)}
                </button>
              ))}
            </div>
          </div>
          ),
        )}
      </fieldset>

      {error && (
        <p className="form__error" role="alert">
          {error}
        </p>
      )}
      {sentTo && (
        <p className="caption invite__sent" role="status">
          {mode === "join"
            ? t("circle:invite.joinSent", { name: sentTo })
            : t("circle:invite.sentTo", { name: sentTo })}
        </p>
      )}

      <div className="form__actions">
        <button
          className="cta"
          disabled={
            sending ||
            !relation ||
            !(picked || (typedNumber && mode !== "join"))
          }
          onClick={() => void send()}
        >
          <span className={sending ? "cta__label--hidden" : undefined}>
            {mode === "join"
              ? t("circle:invite.joinSubmit")
              : t("circle:invite.submit")}
          </span>
          {sending && <span className="cta__spinner" aria-hidden="true" />}
        </button>
      </div>
    </div>
  );
}
