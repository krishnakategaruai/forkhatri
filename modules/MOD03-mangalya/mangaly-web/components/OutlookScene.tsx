/* Drawn scenes for the ten quick choices.
 *
 * Every pole of the outlook activity is a small line drawing rather than a
 * text button, so answering is picking the picture that looks like your
 * life. The owner's brief for all Mangalya art: specific to Mangalya and
 * rooted mostly in South Indian household life — never a generic stock
 * scene. So the vocabulary here is the one a Khatri family in Hyderabad,
 * Bengaluru or Chennai would recognise: the filter-coffee tumbler and
 * dabara, the verandah with its pillars, the oonjal (swing) in the hall,
 * the ammikallu (grinding stone), a banana-leaf meal, the temple pond
 * steps, a brass kalasam, the terrace at night, a scooter for two.
 *
 * Drawn in the app's own language: one ink, one accent, a warm tint, no
 * gradients. Everything is `currentColor` and CSS variables so the same
 * drawing works in dark mode and beside Devanagari or Telugu labels.
 *
 * Neither drawing in a pair is the nicer one. That is checked on purpose:
 * both sides of every pair get the same warmth, the same amount of detail
 * and the same accent. Olson's model is explicit that the extremes at BOTH
 * ends are the unhealthy ones, and a prettier picture would be a thumb on
 * the scale.
 */

import type { ReactNode } from "react";

type PersonProps = {
  x: number;
  y: number;
  /** Saree, bun and a kumkum dot. */
  f?: boolean;
  /** Seated: a shorter body. */
  sit?: boolean;
  /** A pair of spectacles, for the elders. */
  elder?: boolean;
  scale?: number;
};

function Person({ x, y, f, sit, elder, scale = 1 }: PersonProps) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <circle cx="0" cy="0" r="7" className="sc-paper" />
      {f ? (
        <>
          <path d="M-7 -1 Q-6 -8 0 -8 Q6 -8 7 -1" className="sc-ink" />
          <circle cx="7" cy="-3" r="3" className="sc-ink" />
          <circle cx="7" cy="-3" r="1.1" className="sc-paper" />
          <circle cx="0" cy="-2.5" r="1.1" className="sc-acc" />
        </>
      ) : (
        <path d="M-7 -2 Q-5 -8 0 -8 Q5 -8 7 -2" className="sc-ink" />
      )}
      {elder && <path d="M-5 1 h4 M1 1 h4 M-1 1 h2" />}
      {sit ? (
        <path d="M-9 22 Q-9 11 0 9 Q9 11 9 22 Z" className="sc-tint" />
      ) : (
        <path d="M-9 30 Q-9 12 0 9 Q9 12 9 30 Z" className="sc-tint" />
      )}
      {f && <path d={sit ? "M-3 12 L5 21" : "M-3 12 L6 28"} />}
    </g>
  );
}

/** A filter-coffee tumbler sitting in its dabara. */
function Tumbler({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <path d="M-4 -10 h8 l-1 10 h-6 z" className="sc-paper" />
      <path d="M-6 0 h12 l-1.5 3 h-9 z" className="sc-tint" />
      <path d="M-2 -13 q1 -2 0 -4 M2 -13 q1 -2 0 -4" strokeOpacity="0.5" />
    </g>
  );
}

/** A jasmine strand: the small white flowers on a thread. */
function Jasmine({ d, dots }: { d: string; dots: [number, number][] }) {
  return (
    <g>
      <path d={d} strokeOpacity="0.6" />
      {dots.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="2.2" className="sc-paper" />
      ))}
    </g>
  );
}

const SCENES: Record<string, () => ReactNode> = {
  /* Gottman — how a disagreement begins. */
  talk_now: () => (
    <>
      <path d="M30 78 h100 M40 78 v20 M120 78 v20" />
      <Tumbler x={65} y={76} />
      <Tumbler x={95} y={76} />
      <Person x={48} y={44} f />
      <Person x={112} y={44} />
      <path d="M62 38 q6 -4 12 0 M98 38 q-6 -4 -12 0" />
      <path d="M78 30 h4 M78 36 h4" strokeOpacity="0.6" />
    </>
  ),
  need_time: () => (
    <>
      <path d="M18 26 v70 M142 26 v70 M10 26 h140 M10 96 h140" />
      <path d="M18 26 q0 -8 8 -8 h108 q8 0 8 8" />
      <circle cx="118" cy="44" r="7" className="sc-tint" />
      <path d="M116 38 a7 7 0 1 0 6 11" />
      <Person x={52} y={56} f sit />
      <Tumbler x={72} y={88} />
      <Person x={130} y={52} scale={0.7} />
    </>
  ),
  /* Gottman — repair attempts. */
  say_sorry_first: () => (
    <>
      <path d="M10 96 h140" />
      <Person x={48} y={48} />
      <Person x={112} y={48} f />
      <path d="M58 66 q10 -6 22 -2" />
      <Jasmine d="M64 62 q14 -10 32 2" dots={[[68, 60], [74, 57], [80, 56], [88, 57], [94, 61]]} />
      <path d="M104 70 q-6 -4 -12 -2" />
    </>
  ),
  heard_first: () => (
    <>
      <path d="M10 96 h140" />
      <Person x={48} y={48} f />
      <path d="M44 62 q4 3 8 0" className="sc-acc" />
      <rect x="62" y="22" width="30" height="18" rx="9" className="sc-paper" />
      <path d="M66 40 l-4 6 l10 -5" className="sc-paper" />
      <circle cx="71" cy="31" r="1.5" className="sc-ink" />
      <circle cx="77" cy="31" r="1.5" className="sc-ink" />
      <circle cx="83" cy="31" r="1.5" className="sc-ink" />
      <Person x={114} y={50} />
      <path d="M104 44 q-6 4 -4 10" />
    </>
  ),
  /* Circumplex — cohesion. */
  mostly_together: () => (
    <>
      <path d="M20 14 h120" />
      <path d="M50 14 v58 M110 14 v58" strokeDasharray="3 3" />
      <path d="M40 72 h80" strokeWidth="3" />
      <Person x={66} y={44} f sit />
      <Person x={94} y={44} sit />
      <path d="M10 98 h140" />
      <path d="M22 98 q4 -8 8 0 q4 -8 8 0" strokeOpacity="0.6" />
    </>
  ),
  own_space: () => (
    <>
      <path d="M80 10 v88 M10 98 h140" />
      <path d="M22 60 h24 v-30 h-24 z" className="sc-paper" />
      <path d="M34 30 v30" strokeOpacity="0.6" />
      <Person x={56} y={68} sit scale={0.9} />
      <rect x="100" y="52" width="30" height="20" rx="2" className="sc-paper" />
      <path d="M96 72 h38" />
      <Person x={104} y={40} f sit scale={0.9} />
      <path d="M28 20 l8 -8 l8 8 z" className="sc-tint" />
      <path d="M36 20 v8" />
      <path d="M124 20 l8 -8 l8 8 z" className="sc-tint" />
      <path d="M132 20 v8" />
    </>
  ),
  /* Circumplex — flexibility. */
  plan_it: () => (
    <>
      <rect x="44" y="18" width="72" height="72" rx="6" className="sc-paper" />
      <path d="M44 34 h72" />
      <rect x="44" y="18" width="72" height="16" rx="6" className="sc-tint" />
      <path d="M58 14 v8 M102 14 v8" />
      {[0, 1, 2, 3].map((r) =>
        [0, 1, 2, 3, 4].map((c) => (
          <circle
            key={`${r}${c}`}
            cx={56 + c * 12}
            cy={44 + r * 12}
            r="2.2"
            className={(r === 1 && c === 3) || (r === 2 && c === 1) ? "sc-acc" : "sc-ink"}
            opacity={(r === 1 && c === 3) || (r === 2 && c === 1) ? 1 : 0.35}
          />
        )),
      )}
      <path d="M22 96 l4 -4 l4 4 l-4 4 z M30 96 l4 -4 l4 4 l-4 4 z M26 88 l4 -4 l4 4 l-4 4 z" strokeOpacity="0.6" />
    </>
  ),
  as_we_go: () => (
    <>
      <circle cx="120" cy="24" r="8" className="sc-tint" />
      <path d="M10 92 h140" />
      <circle cx="46" cy="82" r="10" className="sc-paper" />
      <circle cx="114" cy="82" r="10" className="sc-paper" />
      <path d="M46 82 l14 -22 h30 l14 22 M60 60 v-8 h24 M40 66 h16" strokeLinejoin="round" />
      <path d="M62 60 q10 -6 30 0" className="sc-tint" />
      <Person x={74} y={38} scale={0.85} />
      <Person x={92} y={40} f scale={0.85} />
      <path d="M118 62 q10 -8 14 0" />
    </>
  ),
  /* §12 — family involvement. */
  family_in_the_room: () => (
    <>
      <path d="M10 96 h140" />
      <rect x="18" y="66" width="76" height="22" rx="8" className="sc-tint" />
      <path d="M18 76 v-16 q0 -6 6 -6 h64 q6 0 6 6 v16" />
      <Person x={40} y={50} f sit elder scale={0.9} />
      <Person x={72} y={50} sit elder scale={0.9} />
      <Person x={118} y={40} f scale={0.95} />
      <Person x={140} y={42} scale={0.95} />
      <path d="M104 26 l4 -8 l4 8 z" className="sc-acc" />
      <path d="M108 30 v4" />
    </>
  ),
  us_first: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M80 26 v40" />
      <path d="M62 26 h36 l-6 -12 h-24 z" className="sc-tint" />
      <ellipse cx="80" cy="70" rx="24" ry="5" className="sc-paper" />
      <path d="M80 75 v20" />
      <Person x={52} y={48} f sit />
      <Person x={108} y={48} sit />
      <Tumbler x={72} y={68} />
      <Tumbler x={90} y={68} />
    </>
  ),
  /* §12 — decision-making. */
  decide_and_move: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M96 20 h34 v76" />
      <path d="M96 20 v76" strokeOpacity="0.5" />
      <path d="M96 20 l-14 8 v70" className="sc-tint" />
      <Person x={68} y={44} />
      <path d="M60 74 l-6 20 M76 74 l10 18" />
      {[0, 1, 2].map((i) => (
        <ellipse key={i} cx={100 + i * 14} cy={90 - (i % 2) * 3} rx="3.2" ry="1.8" className="sc-acc" opacity={0.5 + i * 0.25} />
      ))}
    </>
  ),
  sit_with_it: () => (
    <>
      <path d="M116 60 l8 -34 l8 34 z M120 42 h8 M118 50 h12" className="sc-tint" />
      <path d="M10 60 h60 M10 72 h72 M10 84 h84 M10 96 h140" />
      <path d="M94 96 q10 -6 20 0 q10 -6 20 0" strokeOpacity="0.6" />
      <path d="M100 88 q8 -5 16 0" strokeOpacity="0.4" />
      <Person x={44} y={40} f sit />
      <path d="M52 52 q6 -8 -2 -10" strokeOpacity="0.7" />
      <circle cx="30" cy="20" r="5" className="sc-tint" />
    </>
  ),
  /* §12 — money. */
  save_first: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M56 50 q-16 14 -10 32 q4 12 34 12 q30 0 34 -12 q6 -18 -10 -32 z" className="sc-tint" />
      <path d="M56 50 h48 q4 -8 -4 -12 h-40 q-8 4 -4 12 z" className="sc-paper" />
      <path d="M62 44 h36" strokeOpacity="0.5" />
      <path d="M74 32 q6 -12 12 0 q6 -12 12 0" className="sc-acc" />
      {[0, 1, 2].map((i) => (
        <circle key={i} cx={64 + i * 16} cy={24 - (i % 2) * 6} r="4.5" className="sc-paper" />
      ))}
      <path d="M70 62 q10 12 20 0" strokeOpacity="0.5" />
    </>
  ),
  spend_on_now: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M40 46 h56 l6 48 h-68 z" className="sc-tint" />
      <path d="M52 46 q0 -14 16 -14 q16 0 16 14" />
      <path d="M44 62 q24 -8 48 0 M46 74 q22 -6 44 0" strokeOpacity="0.6" />
      <path d="M50 54 l40 30" className="sc-acc" strokeWidth="1.2" />
      <rect x="106" y="70" width="30" height="20" rx="3" className="sc-paper" />
      <path d="M106 78 h30 M121 70 v20" strokeOpacity="0.5" />
      <path d="M116 70 q5 -8 10 0" className="sc-acc" />
      <Jasmine d="M28 40 q10 -12 24 -4" dots={[[31, 37], [36, 34], [41, 33], [46, 34], [51, 36]]} />
    </>
  ),
  /* SCOPE — Social. */
  full_house: () => (
    <>
      <path d="M8 78 h144 M16 78 v18 M144 78 v18" />
      {[28, 62, 96, 130].map((x) => (
        <ellipse key={x} cx={x} cy="76" rx="14" ry="5" className="sc-tint" />
      ))}
      {[28, 62, 96, 130].map((x) => (
        <path key={`s${x}`} d={`M${x - 8} 76 h16`} strokeOpacity="0.4" />
      ))}
      <Person x={28} y={40} f scale={0.8} />
      <Person x={62} y={38} elder scale={0.8} />
      <Person x={96} y={40} f elder scale={0.8} />
      <Person x={130} y={38} scale={0.8} />
      <Person x={80} y={26} scale={0.6} />
      <path d="M60 16 q4 -8 8 0 q4 -8 8 0 q4 -8 8 0" strokeOpacity="0.5" />
    </>
  ),
  few_close: () => (
    <>
      <path d="M10 74 h140 M10 74 v22 M150 74 v22" />
      <path d="M10 96 h140" />
      <path d="M20 74 h130" strokeDasharray="8 6" strokeOpacity="0.4" />
      <Person x={56} y={46} f sit scale={0.9} />
      <Person x={80} y={44} sit scale={0.9} />
      <Person x={104} y={46} f sit scale={0.9} />
      <circle cx="132" cy="22" r="7" className="sc-tint" />
      <path d="M130 16 a7 7 0 1 0 6 11" />
      <path d="M28 18 l1 3 l3 1 l-3 1 l-1 3 l-1 -3 l-3 -1 l3 -1 z M48 30 l1 2 l2 1 l-2 1 l-1 2 l-1 -2 l-2 -1 l2 -1 z" className="sc-acc" />
    </>
  ),
  /* SCOPE — Change. */
  try_the_new: () => (
    <>
      <path d="M10 96 h140" />
      <rect x="34" y="70" width="56" height="10" rx="3" className="sc-paper" />
      <circle cx="62" cy="75" r="14" strokeOpacity="0.5" />
      <path d="M46 62 h32 v-8 h-32 z" className="sc-tint" />
      <path d="M78 58 h14" />
      <path d="M54 48 q2 -6 0 -10 M62 48 q2 -6 0 -10 M70 48 q2 -6 0 -10" strokeOpacity="0.5" />
      <rect x="104" y="40" width="24" height="42" rx="4" className="sc-paper" />
      <path d="M110 50 h12 M110 58 h12 M110 66 h8" strokeOpacity="0.6" />
      <circle cx="116" cy="76" r="1.6" className="sc-ink" />
      <path d="M96 30 l3 -3 M100 26 l3 -3" className="sc-acc" />
    </>
  ),
  keep_what_works: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M36 82 q0 -12 12 -12 h64 q12 0 12 12 v6 h-88 z" className="sc-tint" />
      <path d="M46 70 q34 -10 68 0" strokeOpacity="0.5" />
      <rect x="66" y="50" width="30" height="14" rx="7" className="sc-paper" transform="rotate(-8 81 57)" />
      <path d="M104 62 q6 -10 12 -4 M112 66 q6 -10 12 -4" className="sc-acc" />
      <path d="M46 64 q-4 -6 2 -8" className="sc-acc" />
      <path d="M124 40 q4 -8 8 0" strokeOpacity="0.5" />
    </>
  ),
  /* §12 — career orientation. */
  work_is_me: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M100 96 v-40 h14 v-16 h14 v56 M110 60 h8 M110 68 h8" strokeOpacity="0.4" />
      <path d="M128 40 v56" strokeOpacity="0.4" />
      <path d="M20 70 h70 M26 70 v26 M84 70 v26" />
      <rect x="40" y="46" width="34" height="22" rx="2" className="sc-paper" />
      <path d="M57 68 v4" />
      <Person x={30} y={44} f sit scale={0.9} />
      <path d="M78 70 q-2 -10 6 -14 q4 4 0 12 q6 -6 8 -2 q-2 6 -8 6" className="sc-tint" />
      <path d="M48 56 h14 M48 60 h10" strokeOpacity="0.5" />
    </>
  ),
  work_funds_life: () => (
    <>
      <path d="M10 56 h140" strokeOpacity="0.5" />
      <path d="M10 62 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0 q10 -6 20 0" strokeOpacity="0.4" />
      <circle cx="124" cy="30" r="8" className="sc-tint" />
      <path d="M10 96 h140" />
      <circle cx="44" cy="84" r="10" className="sc-paper" />
      <circle cx="78" cy="84" r="10" className="sc-paper" />
      <path d="M44 84 l12 -18 h12 l10 18 M56 66 l-4 -6 h8 M66 66 l4 -8 h6" strokeLinejoin="round" />
      <Person x={112} y={64} f sit scale={0.9} />
      <Person x={136} y={66} sit scale={0.9} />
      <path d="M100 92 q24 -8 48 0" className="sc-tint" />
    </>
  ),
  /* The third answer on every question. */
  depends: () => (
    <>
      <path d="M10 96 h140" />
      <path d="M72 96 l8 -18 l8 18 z" className="sc-tint" />
      <path d="M22 70 l116 -14" strokeWidth="3" />
      <g transform="translate(34 56) rotate(-7)">
        <path d="M-8 -6 h16 l-3 12 h-10 z" className="sc-paper" />
        <path d="M-9 -8 h18" />
      </g>
      <g transform="translate(126 44) rotate(-7)">
        <path d="M-8 -6 h16 l-3 12 h-10 z" className="sc-paper" />
        <path d="M-9 -8 h18" />
      </g>
      <path d="M80 36 q0 -8 6 -8 q6 0 6 6 q0 6 -6 8 v4" />
      <circle cx="86" cy="52" r="1.6" className="sc-ink" />
    </>
  ),
};

type Props = {
  /** A pole key from lib/outlook.ts, or "depends". */
  id: string;
  className?: string;
};

export default function OutlookScene({ id, className }: Props) {
  const draw = SCENES[id];
  if (!draw) return null;
  return (
    <svg
      viewBox="0 0 160 120"
      className={`scene${className ? ` ${className}` : ""}`}
      aria-hidden="true"
      focusable="false"
    >
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {draw()}
      </g>
    </svg>
  );
}

export function hasScene(id: string): boolean {
  return id in SCENES;
}
