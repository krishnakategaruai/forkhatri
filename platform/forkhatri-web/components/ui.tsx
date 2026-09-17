/** Shared visual primitives: icons, wordmark, avatar, module glyphs. Monochrome by design (DESIGN-NOTES.md). */
import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Icon({ size = 22, children, ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

export const BellIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z" />
    <path d="M10 20.5a2.2 2.2 0 0 0 4 0" />
  </Icon>
);
export const ArrowIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);
export const ChevronIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 9l6 6 6-6" />
  </Icon>
);
export const SearchIcon = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="M20 20l-4.2-4.2" />
  </Icon>
);
export const MicIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" />
  </Icon>
);
export const LockIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="5" y="10.5" width="14" height="10" rx="3" />
    <path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" />
  </Icon>
);
export const CloseIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);
export const CheckIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </Icon>
);
export const EyeIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
);
export const EyeOffIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 4l16 16M10.6 6a9.8 9.8 0 0 1 1.4-.1C18 5.9 21.5 12 21.5 12a17 17 0 0 1-3 3.7M6.2 7.4A16.4 16.4 0 0 0 2.5 12S6 18.5 12 18.5a9.3 9.3 0 0 0 4-.9" />
    <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
  </Icon>
);
export const LogOutIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M14 4.5h3.5a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H14M10 16l-4-4 4-4M6 12h10" />
  </Icon>
);
export const CloudOffIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 3l18 18M8.5 7.2A5.5 5.5 0 0 1 17 11a4 4 0 0 1 3 6.2M17 19H7.5a4.5 4.5 0 0 1-1.6-8.7" />
  </Icon>
);

/** `luminous` is the signed-out arrival mark (gradient jaali star); the hub uses the flat accent mark. */
export function Wordmark({ luminous = false }: { luminous?: boolean }) {
  if (luminous) {
    return (
      <span className="wordmark" style={{ viewTransitionName: "fk-wordmark" }}>
        <svg className="wordmark-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
          <defs>
            <linearGradient id="fk-mark" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#ffd08a" />
              <stop offset="0.55" stopColor="#ff9a3c" />
              <stop offset="1" stopColor="#e0689b" />
            </linearGradient>
          </defs>
          <rect x="7" y="7" width="18" height="18" rx="3" fill="none" stroke="url(#fk-mark)" strokeWidth="2.2" />
          <rect x="7" y="7" width="18" height="18" rx="3" fill="none" stroke="url(#fk-mark)" strokeWidth="2.2" transform="rotate(45 16 16)" />
          <circle cx="16" cy="16" r="3" fill="url(#fk-mark)" />
        </svg>
        <span className="wordmark-text">
          For<b>Khatri</b>
        </span>
      </span>
    );
  }
  return (
    <span className="wordmark">
      {/* An eight-point jaali star in the single ForKhatri accent. */}
      <svg className="wordmark-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
        <g fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round">
          <rect x="8" y="8" width="16" height="16" rx="2.5" />
          <rect x="8" y="8" width="16" height="16" rx="2.5" transform="rotate(45 16 16)" />
        </g>
        <circle cx="16" cy="16" r="2.6" fill="currentColor" />
      </svg>
      <span className="wordmark-text">
        For<b>Khatri</b>
      </span>
    </span>
  );
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "•";
  const letters = parts.length === 1 ? [...parts[0]].slice(0, 1) : [[...parts[0]][0], [...parts[parts.length - 1]][0]];
  return letters.join("").toUpperCase();
}

export function Avatar({ name, size = 36 }: { name: string; size?: number }) {
  return (
    <span className="avatar" style={{ width: size, height: size, fontSize: size * 0.36 }} aria-hidden="true">
      {initials(name)}
    </span>
  );
}

/** Ambient aurora behind the signed-out arrival screens (arrival.css). */
export function Aurora() {
  return (
    <div className="aurora" aria-hidden="true">
      <span className="aurora-blob a1" />
      <span className="aurora-blob a2" />
      <span className="aurora-blob a3" />
      <span className="aurora-blob a4" />
      <span className="aurora-jaali" />
      <span className="aurora-grain" />
    </div>
  );
}

/** The arrival presence orb (arrival.css). */
export function OrbCore({ className = "" }: { className?: string }) {
  return (
    <span className={`orb-core ${className}`} aria-hidden="true">
      <span className="orb-ring" />
      <span className="orb-ring orb-ring-2" />
    </span>
  );
}

/** Monochrome line glyph per module; inherits `currentColor`. Unknown keys get a neutral mark. */
export function Sigil({ moduleKey, size = 24 }: { moduleKey: string; size?: number }) {
  const line = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    vectorEffect: "non-scaling-stroke" as const,
  };
  let art: ReactNode;
  switch (moduleKey) {
    case "mangaly":
      art = (
        <>
          <circle cx="24" cy="35" r="13" {...line} />
          <circle cx="40" cy="35" r="13" {...line} />
          <path d="M32 9l3.5 5.5L32 20l-3.5-5.5z" {...line} />
        </>
      );
      break;
    case "milavn":
      // A circle of people meeting: three members on one ring.
      art = (
        <>
          <circle cx="32" cy="34" r="17" {...line} />
          <circle cx="32" cy="14" r="5.5" fill="currentColor" />
          <circle cx="15" cy="44" r="5.5" fill="currentColor" />
          <circle cx="49" cy="44" r="5.5" fill="currentColor" />
        </>
      );
      break;
    case "vyapar":
      art = (
        <>
          <path d="M32 8l21 12v24L32 56 11 44V20z" {...line} />
          <path d="M22 40l7-7 5 5 9-10" {...line} />
        </>
      );
      break;
    case "counsel":
      art = (
        <>
          <path d="M32 9l19 7v13c0 12-8 21-19 26-11-5-19-14-19-26V16z" {...line} />
          <path d="M24 32l6 6 11-12" {...line} />
        </>
      );
      break;
    case "payments":
      art = (
        <>
          <circle cx="32" cy="32" r="22" {...line} />
          <path d="M25 23h14M25 30h14M30 23c7 0 7 10 0 10h-4l11 10" {...line} />
        </>
      );
      break;
    case "finance":
      art = (
        <>
          <path d="M10 52h44" {...line} />
          <path d="M14 43c8 0 10-10 17-10s8-12 19-17" {...line} />
          <path d="M43 14l7 2-2 7" {...line} />
        </>
      );
      break;
    default:
      art = <rect x="14" y="14" width="36" height="36" rx="8" {...line} />;
  }
  return (
    <svg className="sigil" width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      {art}
    </svg>
  );
}
