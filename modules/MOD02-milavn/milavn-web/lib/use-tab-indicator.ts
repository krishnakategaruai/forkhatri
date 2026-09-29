'use client';

/* The measured sliding indicator under `.cx-tabs` (same behaviour as the circle
 * page): it fits equal tabs on a phone and auto-width tabs on desktop, and
 * follows the selected tab on resize. */

import { useLayoutEffect, useRef, useState } from 'react';

export function useTabIndicator(selected: string) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null);
  useLayoutEffect(() => {
    const measure = () => {
      const el = refs.current[selected];
      if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [selected]);
  const refFor = (key: string) => (el: HTMLButtonElement | null) => { refs.current[key] = el; };
  const style = indicator ? { transform: `translateX(${indicator.left}px)`, width: indicator.width } : undefined;
  return { refFor, style };
}
