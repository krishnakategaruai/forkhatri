'use client';

/* Acting-member context.
 *
 * Authentication is owned by the parent ForKhatri platform (ADR-004, FR076-
 * FR080 are platform flows). Until this module is mounted inside the
 * platform shell, the member is chosen once on /welcome from the service's
 * development identity registry and remembered locally — the same
 * `member_id` the platform session will eventually supply. No credential
 * ever touches this module. */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api, setApiMember, type Identity, type Profile } from '@/lib/api';

const STORAGE_KEY = 'milavn.member';

type State = {
  ready: boolean;
  identity: Identity | null;
  profile: Profile | null | undefined; // undefined = not loaded yet
  choose: (memberId: string) => Promise<void>;
  signOut: () => void;
  refreshProfile: () => Promise<Profile | null>;
  setProfile: (p: Profile | null) => void;
};

const Ctx = createContext<State | null>(null);

export function IdentityProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);

  const load = useCallback(async (memberId: string | null) => {
    setApiMember(memberId);
    if (!memberId) {
      setIdentity(null);
      setProfile(null);
      return;
    }
    try {
      const me = await api<Identity>('/identity/me');
      setIdentity(me);
      setProfile(await api<Profile | null>('/profile/me'));
    } catch {
      setApiMember(null);
      setIdentity(null);
      setProfile(null);
      try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    }
  }, []);

  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch { /* ignore */ }
    void load(saved).finally(() => setReady(true));
  }, [load]);

  const choose = useCallback(async (memberId: string) => {
    try { localStorage.setItem(STORAGE_KEY, memberId); } catch { /* ignore */ }
    await load(memberId);
  }, [load]);

  const signOut = useCallback(() => {
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    void load(null);
  }, [load]);

  const refreshProfile = useCallback(async () => {
    const p = await api<Profile | null>('/profile/me');
    setProfile(p);
    return p;
  }, []);

  const value = useMemo(() => ({ ready, identity, profile, choose, signOut, refreshProfile, setProfile }), [ready, identity, profile, choose, signOut, refreshProfile]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useIdentity(): State {
  const v = useContext(Ctx);
  if (!v) throw new Error('useIdentity outside IdentityProvider');
  return v;
}
