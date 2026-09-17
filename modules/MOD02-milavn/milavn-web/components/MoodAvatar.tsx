'use client';

/* Expressive avatar v2 (FR097) — researched against Snapchat's Bitmoji system
 * (big-head "toon" proportions, a reactive head that mirrors expression,
 * always a little alive even at rest) and adapted to Milavn's own brand,
 * never Snapchat's colours. A cartoon face per person, drawn as SVG from a
 * stable hash of their member id, that:
 *   - never goes static: a slow idle sway + an occasional blink run even at
 *     "neutral", so it reads as alive, not a stuck sticker;
 *   - snaps into a full expression (smile, laugh, surprised, wink, thinking,
 *     love) the moment a mood arrives, with a soft glow ring while the
 *     person is active;
 *   - stays a private, local drawing: nothing about a real photo is used or
 *     sent, only the expression word (thesis §21 / Brand §9).
 */

import { useEffect, useRef, useState } from 'react';

import type { Expression } from '@/lib/expressions';

const SKIN = ['#f1c9a5', '#e0ac7e', '#c68642', '#8d5524', '#6b3f22', '#f6d5b8'];
const HAIR = ['#1f1a17', '#3b2a20', '#5a3825', '#0b1220', '#6e4b3a', '#2b2b2b'];
const SHIRT = ['#e8912b', '#1f8a5b', '#7c9cff', '#ff5fa2', '#2dd4bf', '#ff7a59'];

function hash(s: string): number { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return Math.abs(h >>> 0); }

const MOUTH: Record<Expression, string> = {
  neutral: 'M36 67 Q50 71 64 67',
  smile: 'M34 63 Q50 81 66 63',
  laugh: 'M31 61 Q50 90 69 61 Z',
  surprised: 'M43 66 a7 9 0 1 0 14 0 a7 9 0 1 0 -14 0',
  wink: 'M36 64 Q52 78 64 62',
  thinking: 'M39 69 Q50 64 61 68',
  love: 'M34 63 Q50 83 66 63',
};

/** A face that is alive at rest: gentle sway + an occasional natural blink, layered under whatever expression is passed in. */
function useIdle(expression: Expression) {
  const [blink, setBlink] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (expression !== 'neutral' && expression !== 'thinking') return undefined;
    const loop = () => {
      timer.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 140);
        loop();
      }, 2600 + Math.random() * 2600);
    };
    loop();
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [expression]);
  return blink;
}

export default function MoodAvatar({ seed, expression = 'neutral', size = 56, active = false, label, idle = true }: { seed: string; expression?: Expression | null; size?: number; active?: boolean; label?: string; idle?: boolean }) {
  const h = hash(seed);
  const skin = SKIN[h % SKIN.length]; const hair = HAIR[(h >> 3) % HAIR.length]; const shirt = SHIRT[(h >> 6) % SHIRT.length];
  const hairStyle = (h >> 9) % 3; // 0 cap, 1 side part, 2 bun
  const glasses = (h >> 12) % 5 === 0; // one in five wears glasses, for variety
  const e: Expression = expression ?? 'neutral';
  const [pop, setPop] = useState(0);
  useEffect(() => { setPop((p) => p + 1); }, [e]);
  const autoBlink = useIdle(idle ? e : 'love'); // 'love' disables the idle loop (hook still runs, just never fires)
  const skinId = `sk-${seed.replace(/[^a-z0-9]/gi, '')}-${size}`;

  const browLift = e === 'surprised' ? -6 : e === 'thinking' ? 3 : e === 'laugh' ? -3 : 0;
  const browTilt = e === 'thinking' ? 10 : 0;
  const leftEyeClosed = e === 'wink' || e === 'laugh' || autoBlink;
  const rightEyeClosed = e === 'laugh' || autoBlink;
  const eyeRy = e === 'surprised' ? 6 : e === 'love' ? 0 : (autoBlink ? 0.6 : 4.2);

  return (
    <span className={`mood-wrap${active ? ' mood-wrap--active' : ''}`} style={{ width: size, height: size }}>
      {active && <span className="mood-ring" aria-hidden="true" style={{ borderColor: shirt }} />}
      {/* Named only when the caller gives a (localised) label; otherwise decorative, so the raw expression token never reaches a screen reader. */}
      <svg key={pop} viewBox="0 0 100 100" width={size} height={size} className="mood-avatar" {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}>
        <defs>
          <radialGradient id={skinId} cx="38%" cy="32%" r="75%">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.55" />
            <stop offset="35%" stopColor={skin} stopOpacity="0" />
          </radialGradient>
        </defs>
        <g className="mood-sway">
          <path d="M14 100 C14 80 30 72 50 72 C70 72 86 80 86 100 Z" fill={shirt} />
          <rect x="42" y="60" width="16" height="16" rx="6" fill={skin} />
          <ellipse cx="50" cy="44" rx="26" ry="28" fill={skin} />
          <ellipse cx="50" cy="44" rx="26" ry="28" fill={`url(#${skinId})`} />
          {hairStyle === 0 && <path d="M24 42 C24 20 36 12 50 12 C64 12 76 20 76 42 C70 30 62 26 50 26 C38 26 30 30 24 42 Z" fill={hair} />}
          {hairStyle === 1 && <path d="M24 44 C22 22 34 12 52 12 C68 12 78 22 76 40 C66 34 56 32 44 32 C36 32 30 36 24 44 Z" fill={hair} />}
          {hairStyle === 2 && <><path d="M24 40 C24 20 36 13 50 13 C64 13 76 20 76 40 C68 30 60 27 50 27 C40 27 32 30 24 40 Z" fill={hair} /><circle cx="50" cy="12" r="8" fill={hair} /></>}
          <g style={{ transform: `translateY(${browLift}px)`, transition: 'transform 260ms ease-out' }}>
            <line x1="34" y1="34" x2="44" y2="33" stroke={hair} strokeWidth="3" strokeLinecap="round" style={{ transform: `rotate(${-browTilt}deg)`, transformOrigin: '39px 33px' }} />
            <line x1="56" y1="33" x2="66" y2="34" stroke={hair} strokeWidth="3" strokeLinecap="round" style={{ transform: `rotate(${browTilt}deg)`, transformOrigin: '61px 33px' }} />
          </g>
          {e === 'love' ? (
            <>
              <path d="M39 40 c-3 -5 -10 -2 -6 4 l6 5 l6 -5 c4 -6 -3 -9 -6 -4 z" fill="#e5484d" className="mood-heart" />
              <path d="M61 40 c-3 -5 -10 -2 -6 4 l6 5 l6 -5 c4 -6 -3 -9 -6 -4 z" fill="#e5484d" className="mood-heart" />
            </>
          ) : (
            <>
              {leftEyeClosed ? <path d="M34 44 Q39 48 44 44" stroke="#14213d" strokeWidth="3" fill="none" strokeLinecap="round" /> : <ellipse cx="39" cy="44" rx="4" ry={eyeRy} fill="#14213d" style={{ transition: 'ry 90ms ease-out' }} />}
              {rightEyeClosed ? <path d="M56 44 Q61 48 66 44" stroke="#14213d" strokeWidth="3" fill="none" strokeLinecap="round" /> : <ellipse cx="61" cy="44" rx="4" ry={eyeRy} fill="#14213d" style={{ transition: 'ry 90ms ease-out' }} />}
              {!leftEyeClosed && e !== 'surprised' && <circle cx="40.5" cy="42.5" r="1.3" fill="#fff" />}
              {!rightEyeClosed && e !== 'surprised' && <circle cx="62.5" cy="42.5" r="1.3" fill="#fff" />}
            </>
          )}
          {(e === 'smile' || e === 'love' || e === 'laugh' || e === 'neutral') && <><circle cx="31" cy="54" r="4" fill="#ff7a59" opacity={e === 'neutral' ? 0.12 : 0.35} /><circle cx="69" cy="54" r="4" fill="#ff7a59" opacity={e === 'neutral' ? 0.12 : 0.35} /></>}
          <path d={MOUTH[e]} fill={e === 'laugh' || e === 'surprised' ? '#8b2f2f' : 'none'} stroke="#8b2f2f" strokeWidth="3" strokeLinecap="round" />
          {e === 'laugh' && <path d="M40 66 Q50 72 60 66" fill="#fff" />}
          {e === 'thinking' && <><circle cx="80" cy="30" r="2.5" fill="#5f6b85" /><circle cx="86" cy="22" r="3.5" fill="#5f6b85" /><circle cx="94" cy="12" r="4.5" fill="#5f6b85" /></>}
          {e === 'laugh' && <path d="M69 46 q4 6 0 9 q-4 -3 0 -9" fill="#7c9cff" className="mood-tear" />}
          {e === 'surprised' && <path d="M74 32 q4 6 0 9 q-4 -3 0 -9" fill="#7c9cff" />}
          {glasses && <g stroke="#14213d" strokeWidth="2" fill="none" opacity="0.55"><rect x="32" y="39" width="15" height="11" rx="4" /><rect x="53" y="39" width="15" height="11" rx="4" /><line x1="47" y1="43" x2="53" y2="43" /></g>}
        </g>
      </svg>
    </span>
  );
}
