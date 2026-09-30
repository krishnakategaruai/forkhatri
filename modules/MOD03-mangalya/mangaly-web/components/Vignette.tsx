/* Small drawn vignettes for section cards and the Home greeting.
 *
 * Same brief as the outlook scenes (components/OutlookScene): specific to
 * Mangalya and drawn from South Indian household life, in one ink and one
 * accent. Each one stands for what the section is actually about in this
 * community rather than a generic pictogram — a kolam at the doorstep for
 * "About you", the gopuram for "Community", the palm-leaf horoscope
 * (jataka) for "Horoscope", a tulasi plant in the courtyard for "Family",
 * two garlands for "Partner preference".
 */

import type { ReactNode } from "react";

const V: Record<string, () => ReactNode> = {
  /* A framed photograph with a jasmine strand laid over the corner. */
  photos: () => (
    <>
      <rect x="34" y="22" width="92" height="76" rx="4" className="sc-paper" />
      <rect x="44" y="32" width="72" height="56" rx="2" className="sc-tint" />
      <circle cx="80" cy="54" r="9" className="sc-paper" />
      <path d="M62 88 q18 -24 36 0" className="sc-paper" />
      <path d="M26 30 q20 -14 40 -4" strokeOpacity="0.6" />
      {[[30, 27], [37, 23], [45, 21], [53, 22], [61, 25]].map(([x, y]) => (
        <circle key={x} cx={x} cy={y} r="2.4" className="sc-paper" />
      ))}
    </>
  ),
  /* A pulli kolam at the doorstep: the dot grid first, then one line that
     loops around every dot without lifting. */
  basics: () => (
    <>
      <path d="M10 100 h140" />
      <path d="M36 100 v-72 h88 v72" strokeOpacity="0.4" />
      <path d="M36 28 q44 -10 88 0" strokeOpacity="0.4" />
      <g transform="translate(80 68)">
        {[-2, -1, 0, 1, 2].map((r) =>
          [-2, -1, 0, 1, 2].map((c) => (
            <circle key={`${r}${c}`} cx={c * 11} cy={r * 9} r="1.4" className="sc-ink" opacity="0.7" />
          )),
        )}
        <path
          d="M0 -27 C 12 -27 22 -18 22 -9 C 22 0 12 9 0 9 C -12 9 -22 0 -22 -9 C -22 -18 -12 -27 0 -27 Z"
          strokeOpacity="0.9"
        />
        <path
          d="M0 27 C 12 27 22 18 22 9 C 22 0 12 -9 0 -9 C -12 -9 -22 0 -22 9 C -22 18 -12 27 0 27 Z"
          strokeOpacity="0.9"
        />
        <path d="M-33 0 C -33 -12 -22 -18 -11 -18 C 0 -18 11 -12 11 0 C 11 12 0 18 -11 18 C -22 18 -33 12 -33 0 Z" strokeOpacity="0.9" />
        <path d="M33 0 C 33 -12 22 -18 11 -18 C 0 -18 -11 -12 -11 0 C -11 12 0 18 11 18 C 22 18 33 12 33 0 Z" strokeOpacity="0.9" />
        <circle r="2.6" className="sc-acc" />
        {[[-11, -9], [11, -9], [-11, 9], [11, 9]].map(([x, y]) => (
          <circle key={`${x}${y}`} cx={x} cy={y} r="2" className="sc-acc" />
        ))}
      </g>
    </>
  ),
  /* The gopuram over the street. */
  community: () => (
    <>
      <path d="M10 98 h140" />
      <path d="M44 98 v-34 l36 -46 l36 46 v34" className="sc-tint" />
      <path d="M56 98 v-28 h48 v28" className="sc-paper" />
      <path d="M50 74 h60 M56 60 h48 M64 46 h32 M72 34 h16" strokeOpacity="0.6" />
      <path d="M76 24 h8 l-4 -8 z" className="sc-acc" />
      <path d="M70 98 v-14 h20 v14" />
      <path d="M18 98 v-20 h14 v20 M128 98 v-20 h14 v20" strokeOpacity="0.5" />
    </>
  ),
  /* Books, a laptop and the tumbler beside it. */
  education_career: () => (
    <>
      <path d="M10 98 h140" />
      <rect x="54" y="48" width="52" height="34" rx="3" className="sc-paper" />
      <path d="M46 84 h68 l-4 6 h-60 z" className="sc-tint" />
      <path d="M64 58 h26 M64 66 h20 M64 74 h30" strokeOpacity="0.5" />
      <path d="M22 90 h22 v-6 h-22 z M24 84 h20 v-6 h-20 z M26 78 h18 v-6 h-18 z" className="sc-tint" />
      <path d="M124 78 h10 l-1 12 h-8 z" className="sc-paper" />
      <path d="M121 90 h16 l-2 4 h-12 z" className="sc-tint" />
      <path d="M127 72 q1 -3 0 -5 M131 72 q1 -3 0 -5" strokeOpacity="0.5" />
    </>
  ),
  /* The jataka on palm leaf, tied with a thread, under a star. */
  horoscope: () => (
    <>
      <path d="M30 44 h100 v12 h-100 z M30 60 h100 v12 h-100 z M30 76 h100 v12 h-100 z" className="sc-tint" />
      <path d="M40 50 h60 M40 66 h70 M40 82 h50" strokeOpacity="0.5" />
      <path d="M46 40 v52 M114 40 v52" strokeOpacity="0.7" />
      <path d="M46 36 q-6 4 0 8 M114 36 q6 4 0 8" strokeOpacity="0.7" />
      <path d="M124 14 l2 5 l5 1 l-4 3 l1 5 l-4 -3 l-4 3 l1 -5 l-4 -3 l5 -1 z" className="sc-acc" />
      <path d="M36 22 l1 2 l2 1 l-2 1 l-1 2 l-1 -2 l-2 -1 l2 -1 z" className="sc-acc" />
    </>
  ),
  /* A morning walk past the tank, tumbler waiting on the wall. */
  lifestyle: () => (
    <>
      <circle cx="30" cy="26" r="9" className="sc-tint" />
      <path d="M10 98 h140" />
      <path d="M10 70 h140" strokeOpacity="0.4" />
      <path d="M40 70 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0" strokeOpacity="0.5" />
      <g transform="translate(112 52)">
        <circle r="7" className="sc-paper" />
        <path d="M-7 -2 Q-5 -8 0 -8 Q5 -8 7 -2" className="sc-ink" />
        <path d="M-8 30 Q-8 12 0 9 Q8 12 8 30 Z" className="sc-tint" />
        <path d="M-6 30 l-6 16 M6 30 l8 14 M-8 14 l-8 10 M8 14 l10 6" />
      </g>
      <path d="M20 98 v-14 h30 v14" className="sc-paper" />
      <path d="M31 84 h8 l-1 -10 h-6 z" className="sc-paper" />
    </>
  ),
  /* The courtyard: tulasi in its brindavan, the house behind. */
  family: () => (
    <>
      <path d="M10 98 h140" />
      <path d="M24 98 v-46 l56 -30 l56 30 v46" className="sc-paper" />
      <path d="M24 52 l56 -30 l56 30" />
      <path d="M40 98 v-24 h22 v24 M98 74 h22 v16 h-22 z" strokeOpacity="0.5" />
      <path d="M70 98 v-20 h20 v20" className="sc-tint" />
      <path d="M78 78 q-10 -14 -2 -24 M80 78 q10 -14 2 -24 M80 76 v-30" className="sc-acc" strokeWidth="1.6" />
      {[[70, 60], [90, 58], [74, 50], [86, 48]].map(([x, y]) => (
        <ellipse key={x + y} cx={x} cy={y} rx="4" ry="2.4" className="sc-tint" transform={`rotate(-20 ${x} ${y})`} />
      ))}
    </>
  ),
  /* The road out of the lane: what comes next. */
  future: () => (
    <>
      <path d="M10 98 h140" />
      <path d="M10 44 h140" strokeOpacity="0.4" />
      <path d="M100 44 v-14 h10 v-10 h12 v24 M126 44 v-18 h10 v18" strokeOpacity="0.5" />
      <path d="M40 98 l30 -54 h20 l30 54 z" className="sc-tint" />
      <path d="M80 92 v-8 M80 76 v-8 M80 60 v-6" strokeOpacity="0.7" />
      <path d="M22 44 v-10 l8 -8 l8 8 v10" className="sc-paper" />
      <circle cx="134" cy="22" r="7" className="sc-tint" />
    </>
  ),
  /* Two garlands, laid across each other. */
  partner: () => (
    <>
      <path d="M36 30 q44 90 88 0" strokeOpacity="0.5" />
      <path d="M124 30 q-44 90 -88 0" strokeOpacity="0.5" />
      {[[40, 40], [48, 56], [58, 70], [70, 80], [80, 84], [90, 80], [102, 70], [112, 56], [120, 40]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="4" className={i % 2 ? "sc-acc" : "sc-paper"} />
      ))}
      {[[44, 48], [54, 64], [66, 76], [94, 76], [106, 64], [116, 48]].map(([x, y], i) => (
        <circle key={`b${i}`} cx={x} cy={y} r="2.4" className="sc-paper" />
      ))}
      <path d="M76 100 q4 -8 8 0" className="sc-acc" />
    </>
  ),
  /* The Home greeting: two tumblers on the windowsill at first light,
     a jasmine strand beside them. */
  morning: () => (
    <>
      <path d="M18 14 h124 v72 h-124 z" strokeOpacity="0.5" />
      <path d="M80 14 v72 M18 50 h124" strokeOpacity="0.3" />
      <circle cx="112" cy="40" r="10" className="sc-tint" />
      <path d="M18 50 q20 -6 30 0 q10 -6 20 0" strokeOpacity="0.3" />
      <path d="M10 92 h140 M10 86 h140" />
      <path d="M52 86 h10 l-1 -14 h-8 z M68 86 h10 l-1 -14 h-8 z" className="sc-paper" />
      <path d="M49 86 h16 l-2 4 h-12 z M65 86 h16 l-2 4 h-12 z" className="sc-tint" />
      <path d="M56 66 q1 -4 0 -7 M60 66 q1 -4 0 -7 M72 66 q1 -4 0 -7 M76 66 q1 -4 0 -7" strokeOpacity="0.45" />
      <path d="M92 84 q14 -14 34 -6" strokeOpacity="0.6" />
      {[[96, 81], [104, 76], [112, 74], [120, 75], [126, 78]].map(([x, y]) => (
        <circle key={x} cx={x} cy={y} r="2.4" className="sc-paper" />
      ))}
    </>
  ),
};

export default function Vignette({ id, className }: { id: string; className?: string }) {
  const draw = V[id];
  if (!draw) return null;
  return (
    <svg
      viewBox="0 0 160 120"
      className={`scene${className ? ` ${className}` : ""}`}
      aria-hidden="true"
      focusable="false"
    >
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {draw()}
      </g>
    </svg>
  );
}

export function hasVignette(id: string): boolean {
  return id in V;
}
