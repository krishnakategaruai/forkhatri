'use client';

import { useCallback, useEffect, useState } from 'react';

import { getContexts, type CircleContext, type Contexts } from '@/lib/homeCircle';

/* FR097 — whose search the member is acting in: their own, or a candidate
 * whose Home Circle they belong to. The choice is remembered per device, and
 * always re-validated against the signed-in member's own contexts. */

export type ActiveContext = { kind: 'self' } | { kind: 'family'; circle: CircleContext };

const STORAGE_KEY = 'mangaly.activeContext';

function readStored(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStored(value: string) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    // Remembering the choice is a convenience; the page still works without it.
  }
}

export function pickContext(contexts: Contexts, stored: string | null): ActiveContext | null {
  const circle = contexts.circles.find((c) => c.candidate_account_id === stored);
  if (circle) return { kind: 'family', circle };
  if (contexts.own_profile) return { kind: 'self' };
  return contexts.circles[0] ? { kind: 'family', circle: contexts.circles[0] } : null;
}

export function useActiveContext() {
  const [contexts, setContexts] = useState<Contexts | null>(null);
  const [active, setActive] = useState<ActiveContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      const result = await getContexts();
      if (!alive) return;
      setContexts(result);
      setActive(result ? pickContext(result, readStored()) : null);
      setLoaded(true);
    })();
    return () => {
      alive = false;
    };
  }, []);

  const choose = useCallback((next: ActiveContext) => {
    writeStored(next.kind === 'self' ? 'self' : next.circle.candidate_account_id);
    setActive(next);
  }, []);

  return { contexts, active, choose, loaded };
}
