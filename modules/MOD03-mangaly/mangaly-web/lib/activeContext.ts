/* FR097 · contract §1/§6 — whose search the member is acting in.
 *
 * A context is either the member's own candidate profile (`self`) or a
 * candidate whose Home Circle they belong to (`family`). It comes from
 * `GET /home-circle/contexts`, which is the one endpoint that knows both
 * halves, and the choice is remembered per device and always re-validated
 * against the contexts the account actually still has — a membership that
 * ended must not leave a stale context selected.
 *
 * A `family` context wraps the whole circle row rather than copying fields
 * out of it, so a screen acting for someone else always has that person's
 * name, relationship and `looking_for` to hand. `looking_for` travels with
 * the context because it permanently constrains who the search returns:
 * it is a property of the candidate being searched for, never a filter the
 * helper can switch off.
 *
 * An account with neither (no own profile, no circles) has no context and
 * browses in "browse mode" (contract §6): Discover asks "bride or groom?"
 * once and remembers that per device too. */

"use client";

import { useCallback, useEffect, useState } from "react";

import type { LookingFor } from "./auth";
import { getContexts, type CircleContext, type Contexts } from "./homeCircle";

export type SelfContext = { kind: "self" };
export type FamilyContext = { kind: "family"; circle: CircleContext };
export type ActiveContext = SelfContext | FamilyContext;

const STORAGE_KEY = "mangaly.activeContext";
const BROWSE_KEY = "mangaly.browseLookingFor";

/** Stable identity for a context: the candidate's account id, or `self`. */
export function contextKey(context: ActiveContext): string {
  return context.kind === "self" ? "self" : context.circle.candidate_account_id;
}

export function sameContext(
  a: ActiveContext | null,
  b: ActiveContext | null,
): boolean {
  if (!a || !b) return a === b;
  return contextKey(a) === contextKey(b);
}

function readStored(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStored(context: ActiveContext): void {
  try {
    localStorage.setItem(STORAGE_KEY, contextKey(context));
  } catch {
    // Remembering the choice is a convenience; the screen works without it.
  }
}

/** The remembered choice if it is still one of this account's contexts;
 *  otherwise their own profile, otherwise their first circle, otherwise none. */
export function pickContext(
  contexts: Contexts,
  stored: string | null,
): ActiveContext | null {
  if (stored === "self" && contexts.own_profile) return { kind: "self" };
  if (stored) {
    const circle = contexts.circles.find(
      (c) => c.candidate_account_id === stored,
    );
    if (circle) return { kind: "family", circle };
  }
  if (contexts.own_profile) return { kind: "self" };
  const first = contexts.circles[0];
  return first ? { kind: "family", circle: first } : null;
}

export function readBrowseLookingFor(): LookingFor | null {
  try {
    const v = localStorage.getItem(BROWSE_KEY);
    return v === "bride" || v === "groom" ? v : null;
  } catch {
    return null;
  }
}

export function writeBrowseLookingFor(value: LookingFor): void {
  try {
    localStorage.setItem(BROWSE_KEY, value);
  } catch {
    // Non-fatal.
  }
}

/** First name, for "For Ananya · as her mother" style labels. */
export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] || name;
}

/* `loaded` is deliberately separate from `contexts !== null`: a screen must
 * be able to tell "still fetching" from "fetched, and this account genuinely
 * has no context", because those two states lead to completely different
 * screens (a skeleton versus browse mode). */
export type UseActiveContext = {
  contexts: Contexts | null;
  active: ActiveContext | null;
  choose: (next: ActiveContext) => void;
  loaded: boolean;
};

export function useActiveContext(): UseActiveContext {
  const [contexts, setContexts] = useState<Contexts | null>(null);
  const [active, setActive] = useState<ActiveContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      let fetched: Contexts | null = null;
      try {
        fetched = await getContexts();
      } catch {
        // Treated as "no contexts": the screen falls back to browse mode
        // rather than hanging on a skeleton it can never resolve.
      }
      if (!alive) return;
      setContexts(fetched);
      setActive(fetched ? pickContext(fetched, readStored()) : null);
      setLoaded(true);
    })();
    return () => {
      alive = false;
    };
  }, []);

  const choose = useCallback((next: ActiveContext) => {
    setActive(next);
    writeStored(next);
  }, []);

  return { contexts, active, choose, loaded };
}
