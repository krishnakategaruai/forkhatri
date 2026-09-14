'use client';

/* Expressive avatar (Snapchat-style, FR097): a cartoon face per person, drawn
 * as SVG from a stable hash of their member id, whose eyes, brows, mouth and
 * cheeks animate with the live expression — smile, laugh, surprised, wink,
 * thinking, love, neutral. The expression is a word from on-device face
 * detection or the mood row; no photo of the person is ever used or sent. */

import { useEffect, useState } from 'react';

import type { Expression } from '@/lib/expressions';

const SKIN = ['#f1c9a5', '#e0ac7e', '#c68642', '#8d5524', '#6b3f22', '#f6d5b8'];
const HAIR = ['#1f1a17', '#3b2a20', '#5a3825', '#0b1220', '#6e4b3a', '#2b2b2b'];
const SHIRT = ['#e8912b', '#1f8a5b', '#7c9cff', '#ff5fa2', '#2dd4bf', '#ff7a59'];

function hash(s: string): number { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return Math.abs(h >>> 0); }

const MOUTH: Record<Expression, string> = {
  neutral: 'M38 66 Q50 70 62 66',
  smile: 'M36 63 Q50 78 64 63',
  laugh: 'M34 62 Q50 86 66 62 Z',
  surprised: 'M43 66 a7 9 0 1 0 14 0 a7 9 0 1 0 -14 0',
  wink: 'M38 64 Q52 76 64 62',
  thinking: 'M40 68 Q50 64 60 68',
  love: 'M36 63 Q50 80 64 63',
};

export default function MoodAvatar({ seed, expression = 'neutral', size = 56, label }: { seed: string; expression?: Expression | null; size?: number; label?: string }) {
  const h = hash(seed);
  const skin = SKIN[h % SKIN.length]; const hair = HAIR[(h >> 3) % HAIR.length]; const shirt = SHIRT[(h >> 6) % SHIRT.length];
  const hairStyle = (h >> 9) % 3; // 0 cap, 1 side part, 2 bun
  const e: Expression = expression ?? 'neutral';
  const [pop, setPop] = useState(0);
  useEffect(() => { setPop((p) => p + 1); }, [e]);
  const browLift = e === 'surprised' ? -6 : e === 'thinking' ? 3 : e === 'laugh' ? -3 : 0;
  const browTilt = e === 'thinking' ? 10 : 0;
  const leftEyeClosed = e === 'wink' || e === 'laugh';
  const rightEyeClosed = e === 'laugh';
  const eyeRy = e === 'surprised' ? 6 : e === 'love' ? 0 : 4.2;
  return (
    <svg key={pop} viewBox="0 0 100 100" width={size} height={size} className="mood-avatar" role="img" aria-label={label ? `${label} · ${e}` : e}>
      {/* shoulders */}
      <path d="M14 100 C14 80 30 72 50 72 C70 72 86 80 86 100 Z" fill={shirt} />
      {/* neck */}
      <rect x="42" y="60" width="16" height="16" rx="6" fill={skin} />
      {/* head */}
      <ellipse cx="50" cy="44" rx="26" ry="28" fill={skin} />
      {/* hair */}
      {hairStyle === 0 && <path d="M24 42 C24 20 36 12 50 12 C64 12 76 20 76 42 C70 30 62 26 50 26 C38 26 30 30 24 42 Z" fill={hair} />}
      {hairStyle === 1 && <path d="M24 44 C22 22 34 12 52 12 C68 12 78 22 76 40 C66 34 56 32 44 32 C36 32 30 36 24 44 Z" fill={hair} />}
      {hairStyle === 2 && <><path d="M24 40 C24 20 36 13 50 13 C64 13 76 20 76 40 C68 30 60 27 50 27 C40 27 32 30 24 40 Z" fill={hair} /><circle cx="50" cy="12" r="8" fill={hair} /></>}
      {/* brows */}
      <g className="mood-brows" style={{ transform: `translateY(${browLift}px)` }}>
        <line x1="34" y1="34" x2="44" y2="33" stroke={hair} strokeWidth="3" strokeLinecap="round" style={{ transform: `rotate(${-browTilt}deg)`, transformOrigin: '39px 33px' }} />
        <line x1="56" y1="33" x2="66" y2="34" stroke={hair} strokeWidth="3" strokeLinecap="round" style={{ transform: `rotate(${browTilt}deg)`, transformOrigin: '61px 33px' }} />
      </g>
      {/* eyes */}
      {e === 'love' ? (
        <>
          <path d="M39 40 c-3 -5 -10 -2 -6 4 l6 5 l6 -5 c4 -6 -3 -9 -6 -4 z" fill="#e5484d" className="mood-heart" />
          <path d="M61 40 c-3 -5 -10 -2 -6 4 l6 5 l6 -5 c4 -6 -3 -9 -6 -4 z" fill="#e5484d" className="mood-heart" />
        </>
      ) : (
        <>
          {leftEyeClosed ? <path d="M34 44 Q39 48 44 44" stroke="#14213d" strokeWidth="3" fill="none" strokeLinecap="round" /> : <ellipse cx="39" cy="44" rx="4" ry={eyeRy} fill="#14213d" />}
          {rightEyeClosed ? <path d="M56 44 Q61 48 66 44" stroke="#14213d" strokeWidth="3" fill="none" strokeLinecap="round" /> : <ellipse cx="61" cy="44" rx="4" ry={eyeRy} fill="#14213d" />}
          {!leftEyeClosed && e !== 'surprised' && <circle cx="40.5" cy="42.5" r="1.3" fill="#fff" />}
          {!rightEyeClosed && e !== 'surprised' && <circle cx="62.5" cy="42.5" r="1.3" fill="#fff" />}
        </>
      )}
      {/* cheeks */}
      {(e === 'smile' || e === 'love' || e === 'laugh') && <><circle cx="31" cy="54" r="4" fill="#ff7a59" opacity="0.35" /><circle cx="69" cy="54" r="4" fill="#ff7a59" opacity="0.35" /></>}
      {/* mouth */}
      <path d={MOUTH[e]} fill={e === 'laugh' || e === 'surprised' ? '#8b2f2f' : 'none'} stroke="#8b2f2f" strokeWidth="3" strokeLinecap="round" className="mood-mouth" />
      {e === 'laugh' && <path d="M40 66 Q50 72 60 66" fill="#fff" />}
      {/* thinking: thought dots */}
      {e === 'thinking' && <><circle cx="80" cy="30" r="2.5" fill="#5f6b85" /><circle cx="86" cy="22" r="3.5" fill="#5f6b85" /><circle cx="94" cy="12" r="4.5" fill="#5f6b85" /></>}
      {/* laugh: tear */}
      {e === 'laugh' && <path d="M69 46 q4 6 0 9 q-4 -3 0 -9" fill="#7c9cff" className="mood-tear" />}
      {/* surprised: sweat */}
      {e === 'surprised' && <path d="M74 32 q4 6 0 9 q-4 -3 0 -9" fill="#7c9cff" />}
    </svg>
  );
}
