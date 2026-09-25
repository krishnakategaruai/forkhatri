"use client";

// [IMP38 — Refactor C] The one data-loading primitive every data hook uses.
//
// Why a shared primitive: each page used to hand-roll the same
// useState + useEffect + setError dance, and they drifted — some re-fetched
// on a live language switch, some forgot to, leaving server-translated
// labels (skill names, category labels, state reasons) in the old language
// until a reload. Here the current i18n language is ALWAYS part of the
// dependency list (hard product rule since IMP32: a language switch must
// update every server-translated label), unless a hook explicitly opts out
// for data with no translated text in it.
//
// Behaviour kept from the pages it replaces:
//  - data is NOT cleared while a re-fetch runs (no skeleton flash on a
//    language switch or after an action; the old value stays until the new
//    one lands);
//  - an error is kept until the next successful load;
//  - a late response for stale inputs never overwrites a newer one.
import { useCallback, useEffect, useRef, useState, type DependencyList } from "react";
import { useTranslation } from "react-i18next";

export interface Resource<T> {
  data: T | null;
  error: unknown;
  loading: boolean;
  /** Re-run the loader now; resolves with the new value (or undefined on failure). */
  refresh: () => Promise<T | undefined>;
  /** Optimistic local update. */
  setData: React.Dispatch<React.SetStateAction<T | null>>;
}

export interface ResourceOptions<T> {
  /** false: skip loading (for example until a prerequisite is known). Default true. */
  enabled?: boolean;
  /** false: do not re-fetch on a language switch (data has no translated text). Default true. */
  language?: boolean;
  /** Value to use when the loader fails, instead of recording an error (for "render nothing" blocks). */
  fallback?: T;
}

export function useResource<T>(loader: () => Promise<T>, deps: DependencyList, options: ResourceOptions<T> = {}): Resource<T> {
  const { enabled = true, language = true } = options;
  const { i18n } = useTranslation();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const loaderRef = useRef(loader);
  const optionsRef = useRef(options);
  const seq = useRef(0);
  // Always call the latest loader (it closes over the latest ids / SDK).
  // Declared before the fetch effect below, so it runs first in the commit.
  useEffect(() => {
    loaderRef.current = loader;
    optionsRef.current = options;
  });

  const refresh = useCallback(async () => {
    const mine = ++seq.current;
    setLoading(true);
    try {
      const value = await loaderRef.current();
      if (mine === seq.current) {
        setData(value);
        setError(null);
      }
      return value;
    } catch (e) {
      if (mine === seq.current) {
        if ("fallback" in optionsRef.current) setData(optionsRef.current.fallback as T);
        else setError(e);
      }
      return undefined;
    } finally {
      if (mine === seq.current) setLoading(false);
    }
  }, []);

  const lang = language ? i18n.language : null;
  useEffect(() => {
    if (!enabled) return;
    // Start on the next microtask, and only if this effect is still the
    // live one: React's development double-invoke (mount, unmount, mount)
    // then issues ONE request instead of two, and no state is set
    // synchronously inside the effect body.
    let live = true;
    queueMicrotask(() => {
      if (live) void refresh();
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, lang, refresh, ...deps]);

  return { data, error, loading, refresh, setData };
}
