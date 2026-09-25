/**
 * Devotional emblem of Bhagwan Kartavirya Sahasrarjun (ForKhatri original artwork,
 * `currentColor` SVG, viewBox 120×140). Shown beside the signed-in hub greeting.
 *
 * Since 2026-09-24 the owner has also placed the SSK portrait
 * (ssk-sahasrarjun.webp, from docs/images/sskicon.png) on the first-load splash and
 * in the app icon / favicon. Module rows and notifications still carry no deity art
 * and no glow gimmicks (see components/DevotionalPortrait.tsx).
 *
 * The Wikimedia Commons photo in the same folder is a reference only and is not
 * rendered anywhere (see public/assets/devotional/ATTRIBUTION.md). Do not delete it.
 */
export const DEVOTIONAL_EMBLEM = {
  src: "/assets/devotional/sahasrarjun-emblem.svg",
  width: 120,
  height: 140,
} as const;
