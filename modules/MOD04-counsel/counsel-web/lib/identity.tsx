"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError, UNAUTHORIZED_EVENT, type Me } from "@/lib/api";
import { signOutOfForKhatri } from "@/lib/platform";

type State = {
  ready: boolean;
  me: Me | null;
  unavailable: boolean;
  reload: () => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<State | null>(null);

export function IdentityProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  const load = useCallback(async () => {
    try {
      setMe(await api<Me>("/me"));
      setUnavailable(false);
    } catch (e) {
      setMe(null);
      setUnavailable(!(e instanceof ApiError && e.status === 401));
    }
  }, []);

  useEffect(() => {
    void load().finally(() => setReady(true));
  }, [load]);

  useEffect(() => {
    const onUnauthorized = () => setMe(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const reload = useCallback(async () => { await load(); }, [load]);
  const signOut = useCallback(async () => { await signOutOfForKhatri(); }, []);
  const value = useMemo(() => ({ ready, me, unavailable, reload, signOut }), [ready, me, unavailable, reload, signOut]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useIdentity(): State {
  const v = useContext(Ctx);
  if (!v) throw new Error("useIdentity outside IdentityProvider");
  return v;
}
