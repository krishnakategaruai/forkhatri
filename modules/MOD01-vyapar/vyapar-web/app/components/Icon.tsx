// [Design tightening, 2026-09-22] One thin-line icon set (24-unit grid,
// 1.6 stroke, currentColor) replacing the Unicode glyphs (▤ ◎ ⇄ ◇ …) that
// stood in for icons across the rail, the profile hub, the choosers and the
// profile cards. Inline SVG, no dependency, so it renders identically in
// every language and font. Decorative by default (aria-hidden); pass
// `label` when the icon stands alone.
import type { CSSProperties } from "react";

const PATHS: Record<string, string> = {
  discover: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm3.5 5.5-2 5-5 2 2-5 5-2Z",
  businesses: "M4 10V7l2-3h12l2 3v3M4 10a2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0M5 10v10h14V10M10 20v-5h4v5",
  post: "M12 5v14M5 12h14",
  activity: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2",
  profile: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0",
  listings: "M4 6h16M4 12h16M4 18h10",
  enquiries: "M4 5h16v11H9l-5 4V5Z",
  moderation: "M12 3l8 3v6c0 4.5-3.5 7.5-8 9-4.5-1.5-8-4.5-8-9V6l8-3Zm-3 9 2 2 4-4",
  boost: "M4 17l5-6 4 3 7-8M15 6h5v5",
  privacy: "M6 11V8a6 6 0 0 1 12 0v3M5 11h14v10H5V11Zm7 4v3",
  workspace: "M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z",
  help: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-2.5 6.5a2.5 2.5 0 0 1 5 0c0 1.5-2.5 2-2.5 3.5M12 17h.01",
  back: "M19 12H5m6-6-6 6 6 6",
  business: "M4 21V5l8-2v18M12 9l8 2v10M8 8h.01M8 12h.01M8 16h.01M16 14h.01M16 18h.01M4 21h16",
  professional: "M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 10a7 7 0 0 1 10-6.3M17 15l1.5 1.5L21 14M16 21h5",
  listing: "M5 4h14v16H5V4Zm3 5h8M8 13h8M8 17h5",
  opportunity: "M4 8h16v11H4V8Zm5 0V5h6v3M4 13h16",
  settings: "M4 7h10m4 0h2M4 17h4m4 0h8M14 5v4m-6 6v4",
  check: "M5 12l4 4L19 7",
  arrow: "M5 12h14m-6-6 6 6-6 6",
  alert: "M6 16V11a6 6 0 0 1 12 0v5l2 2H4l2-2Zm4 4h4",
  save: "M6 4h12v17l-6-4-6 4V4Z",
  share: "M12 3v12m0-12-4 4m4-4 4 4M5 13v7h14v-7",
};

export type IconName = keyof typeof PATHS;

export default function Icon({
  name,
  size = 20,
  strokeWidth = 1.6,
  label,
  style,
  className,
}: {
  name: IconName | string;
  size?: number;
  strokeWidth?: number;
  label?: string;
  style?: CSSProperties;
  className?: string;
}) {
  const d = PATHS[name];
  if (!d) return null;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
      style={{ flexShrink: 0, ...style }}
      className={className}
    >
      <path d={d} />
    </svg>
  );
}
