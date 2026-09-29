'use client';

import { useRef, useState } from 'react';

/* A real gesture-driven card deck — drag with a pointer (mouse, touch, or
 * pen; the Pointer Events API unifies all three, so no separate touch
 * handler path is needed) to fling a card left/right, with rotation and
 * fade following the drag distance, and a spring-back when a drag doesn't
 * cross the commit threshold. This is the Hinge/Tinder-standard candidate
 * review pattern — a deliberate departure from a plain scrolling list for
 * exactly the surface (Discover) where a person is making a one-at-a-time
 * decision, not scanning a directory. Explicit buttons are always present
 * alongside the gesture (never gesture-only) so the same action works for
 * a mouse click, a screen reader, or anyone who simply prefers tapping. */

const COMMIT_PX = 110;
const MAX_ROTATE_DEG = 14;

export function SwipeDeck<T>({
  items,
  getKey,
  renderCard,
  onSwipeRight,
  onSwipeLeft,
  rightLabel,
  leftLabel,
  rightText,
  emptyState,
}: {
  items: T[];
  getKey: (item: T) => string;
  renderCard: (item: T) => React.ReactNode;
  onSwipeRight: (item: T) => void;
  onSwipeLeft: (item: T) => void;
  rightLabel: string;
  leftLabel: string;
  /** Visible text instead of the heart, when the action is not "connect". */
  rightText?: string;
  emptyState: React.ReactNode;
}) {
  const [index, setIndex] = useState(0);
  const [drag, setDrag] = useState<{ x: number; dragging: boolean }>({ x: 0, dragging: false });
  const [exiting, setExiting] = useState<'left' | 'right' | null>(null);
  const startX = useRef(0);
  const pointerId = useRef<number | null>(null);

  const visible = items.slice(index, index + 3);

  function advance(direction: 'left' | 'right') {
    const current = items[index];
    if (!current) return;
    setExiting(direction);
    window.setTimeout(() => {
      if (direction === 'right') onSwipeRight(current);
      else onSwipeLeft(current);
      setIndex((i) => i + 1);
      setExiting(null);
      setDrag({ x: 0, dragging: false });
    }, 220);
  }

  function onPointerDown(e: React.PointerEvent) {
    if (exiting) return;
    pointerId.current = e.pointerId;
    startX.current = e.clientX;
    setDrag({ x: 0, dragging: true });
  }

  function onPointerMove(e: React.PointerEvent) {
    if (pointerId.current !== e.pointerId || !drag.dragging) return;
    setDrag({ x: e.clientX - startX.current, dragging: true });
  }

  function endDrag() {
    if (Math.abs(drag.x) > COMMIT_PX) {
      advance(drag.x > 0 ? 'right' : 'left');
    } else {
      setDrag({ x: 0, dragging: false });
    }
    pointerId.current = null;
  }

  if (visible.length === 0) return <>{emptyState}</>;

  return (
    <div className="swipe-deck">
      <div className="swipe-deck__stack">
        {visible.map((item, i) => {
          const isTop = i === 0;
          const stackStyle: React.CSSProperties = isTop
            ? {
                transform: exiting
                  ? `translateX(${exiting === 'right' ? 600 : -600}px) rotate(${exiting === 'right' ? 24 : -24}deg)`
                  : `translateX(${drag.x}px) rotate(${Math.max(-MAX_ROTATE_DEG, Math.min(MAX_ROTATE_DEG, drag.x / 12))}deg)`,
                transition: drag.dragging ? 'none' : 'transform 260ms cubic-bezier(0.22, 1, 0.36, 1)',
                opacity: exiting ? 0 : 1,
                zIndex: 3,
                touchAction: 'pan-y',
              }
            : {
                transform: `translateY(${i * 10}px) scale(${1 - i * 0.04})`,
                zIndex: 3 - i,
                opacity: 1 - i * 0.25,
              };
          return (
            <div
              key={getKey(item)}
              className="swipe-deck__card"
              style={stackStyle}
              onPointerDown={isTop ? onPointerDown : undefined}
              onPointerMove={isTop ? onPointerMove : undefined}
              onPointerUp={isTop ? endDrag : undefined}
              onPointerCancel={isTop ? endDrag : undefined}
            >
              {isTop && drag.x !== 0 && (
                <span
                  className={`swipe-deck__stamp swipe-deck__stamp--${drag.x > 0 ? 'right' : 'left'}`}
                  style={{ opacity: Math.min(1, Math.abs(drag.x) / COMMIT_PX) }}
                  aria-hidden="true"
                >
                  {drag.x > 0 ? rightLabel : leftLabel}
                </span>
              )}
              {renderCard(item)}
            </div>
          );
        })}
      </div>
      <div className="swipe-deck__actions">
        <button
          type="button"
          className="swipe-deck__action swipe-deck__action--skip"
          aria-label={leftLabel}
          onClick={() => advance('left')}
        >
          ✕
        </button>
        <button
          type="button"
          className={`swipe-deck__action swipe-deck__action--connect${rightText ? ' swipe-deck__action--text' : ''}`}
          aria-label={rightLabel}
          onClick={() => advance('right')}
        >
          {rightText ?? '♥'}
        </button>
      </div>
    </div>
  );
}
