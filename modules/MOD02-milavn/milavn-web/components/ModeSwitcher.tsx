'use client';

/* Feed / Calendar / Map / Search segmented control (FR005 · UX04/UX05) with a
 * spring-morphing pill; locality/interest context lives server-side per
 * profile so switching modes never resets it. */

import { useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

export type Mode = 'feed' | 'calendar' | 'map' | 'search';
const MODES: Mode[] = ['feed', 'calendar', 'map', 'search'];

export default function ModeSwitcher({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const [pill, setPill] = useState<{ left: number; width: number } | null>(null);
  const idx = MODES.indexOf(mode);
  useLayoutEffect(() => {
    const el = ref.current?.querySelectorAll<HTMLElement>('.seg__btn')[idx];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth });
  }, [idx]);
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') onChange(MODES[(idx + 1) % MODES.length]);
    if (e.key === 'ArrowLeft') onChange(MODES[(idx + MODES.length - 1) % MODES.length]);
  };
  return (
    <div className="seg" role="tablist" ref={ref} onKeyDown={onKey}>
      {pill && <span className="seg__pill" style={{ left: pill.left, width: pill.width }} aria-hidden="true" />}
      {MODES.map((m) => (
        <button key={m} role="tab" aria-selected={mode === m} className="seg__btn" onClick={() => onChange(m)}>{t(`home.modes.${m}`)}</button>
      ))}
    </div>
  );
}
