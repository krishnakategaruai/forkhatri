'use client';

/* Acting-member context.
 *
 * Authentication is owned by the ForKhatri platform (ADR-004; ParentApp
 * 07-tech-reqs TR12-TR16). The browser holds one HttpOnly ForKhatri session
 * cookie; Milavn's API resolves it and `/identity/me` tells this client who
 * is here. Nothing about the member is stored in the browser by Milavn, and
 * no member id is ever sent as a header. Signed out (401) → the shell sends
 * the person to the ForKhatri entrance with `return_to`; identity service
 * unreachable (503) → a retryable "unavailable" state, never a guess. */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api, ApiError, UNAUTHORIZED_EVENT, type Identity, type Profile } from '@/lib/api';
import { signOutOfForKhatri } from '@/lib/platform';

// Left behind by the pre-platform development chooser; removed once on load.
const LEGACY_STORAGE_KEY = 'milavn.member';

type State = {
  ready: boolean;
  identity: Identity | null;
  profile: Profile | null | undefined; // undefined = not loaded yet
  /** The identity service could not be reached; show a retry, do not redirect. */
  unavailable: boolean;
  reload: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<Profile | null>;
  setProfile: (p: Profile | null) => void;
};

const Ctx = createContext<State | null>(null);

export function IdentityProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [unavailable, setUnavailable] = useState(false);

  const load = useCallback(async () => {
    try {
      const me = await api<Identity>('/identity/me');
      setIdentity(me);
      setUnavailable(false);
      setProfile(await api<Profile | null>('/profile/me'));
    } catch (e) {
      setIdentity(null);
      setProfile(null);
      setUnavailable(!(e instanceof ApiError && e.status === 401));
    }
  }, []);

  useEffect(() => {
    try { localStorage.removeItem(LEGACY_STORAGE_KEY); } catch { /* ignore */ }
    void load().finally(() => setReady(true));
  }, [load]);

  // A 401 anywhere means the ForKhatri session ended (signed out elsewhere, expired).
  useEffect(() => {
    const onUnauthorized = () => { setIdentity(null); setProfile(null); };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const reload = useCallback(async () => {
    setReady(false);
    await load();
    setReady(true);
  }, [load]);

  const signOut = useCallback(async () => {
    await signOutOfForKhatri();
  }, []);

  const refreshProfile = useCallback(async () => {
    const p = await api<Profile | null>('/profile/me');
    setProfile(p);
    return p;
  }, []);

  const value = useMemo(
    () => ({ ready, identity, profile, unavailable, reload, signOut, refreshProfile, setProfile }),
    [ready, identity, profile, unavailable, reload, signOut, refreshProfile],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useIdentity(): State {
  const v = useContext(Ctx);
  if (!v) throw new Error('useIdentity outside IdentityProvider');
  return v;
}
