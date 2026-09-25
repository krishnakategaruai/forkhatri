'use client';

import { usePathname } from 'next/navigation';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  contextKey,
  pickContext,
  readBrowseLookingFor,
  writeBrowseLookingFor,
  type ActiveContext,
  type FamilyContext,
  type SelfContext,
} from './activeContext';
import { getContexts, type Contexts } from './homeCircle';
import { getSession, type Counts, type LookingFor, type Session } from './auth';
import { reportOutage } from './outage';
import { redirectToEntrance } from './platform';

/* [2026-09-17 rework] One session fetch for the whole app.
 *
 * The shell mounts `SessionProvider`; every page reads `useSession()` and
 * `useActiveContext()` instead of calling `/auth/me`, `/profile/me` and
 * `/home-circle/contexts` on its own. A page that needs fresh counts (after
 * accepting a request, reading notifications) calls `refresh()`.
 *
 * Routes the platform owns (`/login`, `/signup`, `/otp`, `/reset`) and the
 * profile wizard render without the shell and without this fetch. */

export const CHROMELESS = ['/login', '/signup', '/reset', '/otp', '/profile/create'];

export function isChromeless(pathname: string | null): boolean {
  return !!pathname && CHROMELESS.includes(pathname);
}

type SessionValue = {
  /** `null` while loading. Signed-out never renders: the provider hands off to the entrance. */
  session: Session | null;
  loading: boolean;
  refresh: () => Promise<void>;
  /** Optimistic count updates so a badge disappears the moment the member acts. */
  adjustCounts: (delta: Partial<Counts>) => void;
  contexts: Contexts | null;
  active: ActiveContext | null;
  choose: (next: ActiveContext) => void;
  /** Browse mode (contract §6): what an account with no context is looking for. */
  browse: LookingFor | null;
  setBrowse: (value: LookingFor) => void;
};

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const chromeless = isChromeless(pathname);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [contexts, setContexts] = useState<Contexts | null>(null);
  const [stored, setStored] = useState<string | null>(null);
  const [browse, setBrowseState] = useState<LookingFor | null>(null);

  const load = useCallback(async () => {
    try {
      const next = await getSession();
      if (!next) {
        redirectToEntrance();
        return;
      }
      setSession(next);
      // Contexts are their own endpoint because only it knows both the
      // account's own profile and the circles it belongs to.
      setContexts(await getContexts());
    } catch {
      reportOutage();
    } finally {
      setLoading(false);
    }
  }, []);

  /* eslint-disable react-hooks/set-state-in-effect -- reading device storage after mount is the documented pattern */
  useEffect(() => {
    try {
      setStored(localStorage.getItem('mangaly.activeContext'));
    } catch {
      setStored(null);
    }
    setBrowseState(readBrowseLookingFor());
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    if (chromeless) return;
    void load();
  }, [chromeless, load]);

  const active = useMemo(() => (contexts ? pickContext(contexts, stored) : null), [contexts, stored]);

  const choose = useCallback((next: ActiveContext) => {
    try {
      localStorage.setItem('mangaly.activeContext', contextKey(next));
    } catch {
      // Remembering the choice is a convenience, not a requirement.
    }
    setStored(contextKey(next));
  }, []);

  const setBrowse = useCallback((value: LookingFor) => {
    writeBrowseLookingFor(value);
    setBrowseState(value);
  }, []);

  const adjustCounts = useCallback((delta: Partial<Counts>) => {
    setSession((prev) =>
      prev
        ? {
            ...prev,
            counts: {
              unread_messages: Math.max(0, prev.counts.unread_messages + (delta.unread_messages ?? 0)),
              pending_requests: Math.max(0, prev.counts.pending_requests + (delta.pending_requests ?? 0)),
              unread_notifications: Math.max(
                0,
                prev.counts.unread_notifications + (delta.unread_notifications ?? 0)
              ),
            },
          }
        : prev
    );
  }, []);

  const value = useMemo<SessionValue>(
    () => ({ session, loading, refresh: load, adjustCounts, contexts, active, choose, browse, setBrowse }),
    [session, loading, load, adjustCounts, contexts, active, choose, browse, setBrowse]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

function useSessionValue(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error('useSession() must be used inside SessionProvider');
  return value;
}

export function useSession() {
  const { session, loading, refresh, adjustCounts } = useSessionValue();
  return { session, loading, refresh, adjustCounts };
}

/** Everything a context-aware screen needs in one read. */
export function useActiveContext() {
  const { contexts, active, choose, browse, setBrowse, session } = useSessionValue();
  const family: FamilyContext | null = active?.kind === 'family' ? active : null;
  const self: SelfContext | null = active?.kind === 'self' ? active : null;
  return {
    contexts,
    active,
    choose,
    family,
    self,
    /** `?for_candidate=` value for context-scoped calls; omitted ⇒ self. */
    forCandidate: family?.circle.candidate_account_id,
    /** Whose side the search is on: the candidate's answer, or the browse-mode choice.
     *  It is read from whoever is being searched FOR, never from the helper. */
    lookingFor: family
      ? family.circle.looking_for
      : (contexts?.own_profile?.looking_for ?? browse),
    browse,
    setBrowse,
    /** True when the account is neither a candidate nor in any circle. */
    noContext: !!session && !!contexts && !contexts.own_profile && contexts.circles.length === 0,
    hasCircles: (session?.circles.length ?? 0) > 0,
    hasOwnProfile: !!session?.own_profile,
  };
}
