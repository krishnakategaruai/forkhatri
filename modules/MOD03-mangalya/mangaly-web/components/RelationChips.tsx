"use client";

import { useTranslation } from "react-i18next";

import {
  HOME_RELATIONS,
  RELATIVE_RELATIONS,
  RELATION_ROLE,
  type Relation,
  type RelationshipType,
} from "@/lib/homeCircle";

/* The exact relations, in the two groups the owner named — Home and
 * Relatives — as chips. Used in place on a Members row to state a relation
 * that was recorded only as a role. */
export default function RelationChips({
  value,
  busy,
  role,
  onPick,
}: {
  value: Relation | null;
  busy?: boolean;
  /** When the role is already known (a row in Home as "Parent"), offer only
   *  the relations inside it — Mother or Father — not the whole list. */
  role?: RelationshipType;
  onPick: (r: Relation) => void;
}) {
  const { t } = useTranslation(["circle"]);
  if (role) {
    const within = [...HOME_RELATIONS, ...RELATIVE_RELATIONS].filter(
      (r) => RELATION_ROLE[r] === role,
    );
    return (
      <div className="relpick__chips" role="radiogroup">
        {within.map((r) => (
          <button
            key={r}
            type="button"
            role="radio"
            aria-checked={value === r}
            disabled={busy}
            className={`relchip${value === r ? " is-on" : ""}`}
            onClick={() => onPick(r)}
          >
            {t(`circle:relation.${r}`)}
          </button>
        ))}
      </div>
    );
  }
  return (
    <div className="relpick">
      {(
        [
          ["home", HOME_RELATIONS],
          ["relatives", RELATIVE_RELATIONS],
        ] as const
      ).map(([group, list]) => (
        <div key={group} className="relpick__group">
          <span className="relpick__group-title">
            {t(`circle:members.group.${group}`)}
          </span>
          <div className="relpick__chips" role="radiogroup">
            {list.map((r) => (
              <button
                key={r}
                type="button"
                role="radio"
                aria-checked={value === r}
                disabled={busy}
                className={`relchip${value === r ? " is-on" : ""}`}
                onClick={() => onPick(r)}
              >
                {t(`circle:relation.${r}`)}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
