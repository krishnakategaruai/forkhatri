// [Design language 2026-09-29, §9] Per-viewer display preferences: text
// size and high contrast. Stored in this browser only (a convenience, like
// the language), applied as attributes on <html> that globals.css reads:
//   data-text="l" | "xl"   → root font size 112.5% / 125% (all type is rem)
//   data-contrast="more"   → secondary text near-primary, 3:1 edges
// "auto" contrast follows the OS (prefers-contrast: more).
export type TextSize = "m" | "l" | "xl";
export type ContrastPref = "auto" | "more";

const TEXT_KEY = "vyapar.textSize";
const CONTRAST_KEY = "vyapar.contrast";

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* private mode: the choice still applies for this visit */
  }
}

export function getTextSize(): TextSize {
  const v = read(TEXT_KEY);
  return v === "l" || v === "xl" ? v : "m";
}

export function getContrast(): ContrastPref {
  return read(CONTRAST_KEY) === "more" ? "more" : "auto";
}

export function applyDisplay() {
  const html = document.documentElement;
  const size = getTextSize();
  if (size === "m") delete html.dataset.text;
  else html.dataset.text = size;
  const osMore = typeof window.matchMedia === "function" && window.matchMedia("(prefers-contrast: more)").matches;
  if (getContrast() === "more" || osMore) html.dataset.contrast = "more";
  else delete html.dataset.contrast;
}

export function setTextSize(size: TextSize) {
  write(TEXT_KEY, size);
  applyDisplay();
}

export function setContrast(pref: ContrastPref) {
  write(CONTRAST_KEY, pref);
  applyDisplay();
}

/** Inline, before first paint (layout.tsx <head>), so a large-text reader never sees the page jump. */
export const DISPLAY_BOOT_SCRIPT = `(function(){try{var h=document.documentElement,s=localStorage.getItem("${TEXT_KEY}");if(s==="l"||s==="xl")h.dataset.text=s;if(localStorage.getItem("${CONTRAST_KEY}")==="more"||(window.matchMedia&&matchMedia("(prefers-contrast: more)").matches))h.dataset.contrast="more";}catch(e){}})();`;
