// Palette 2026-09-29 — WCAG 2.2 contrast check for every text/background and
// UI pair in the Vyapar theme. Reads the token values straight out of
// app/globals.css (light block = the one marked @palette-light, dark = the one marked
// @palette-dark, which must equal the forced [data-theme="dark"] block) so this check can never drift from the CSS.
// Run: node scripts/check-contrast.mjs   (exit code 1 if any pair fails)
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

function block(startMarker, from = 0, openAfter = false) {
  const i = css.indexOf(startMarker, from);
  if (i < 0) throw new Error("marker not found: " + startMarker);
  const open = openAfter ? css.indexOf("{", i) : css.lastIndexOf("{", i);
  let depth = 0, j = open;
  for (; j < css.length; j++) {
    if (css[j] === "{") depth++;
    else if (css[j] === "}" && --depth === 0) break;
  }
  const vars = {};
  for (const m of css.slice(open + 1, j).matchAll(/--([\w-]+)\s*:\s*([^;]+);/g)) vars[m[1]] = m[2].trim();
  return vars;
}
const light = block("/* @palette-light */");
const darkOnly = block("/* @palette-dark */");
const dark = { ...light, ...darkOnly };
// The forced [data-theme="dark"] block must match the system-dark block.
const forced = block(":root[data-theme=\"dark\"] {", 0, true);
for (const k of new Set([...Object.keys(darkOnly), ...Object.keys(forced)])) {
  if (darkOnly[k] !== forced[k]) { console.error("dark blocks differ at --" + k + ": " + darkOnly[k] + " vs " + forced[k]); process.exit(1); }
}

function resolve(vars, name, seen = new Set()) {
  let v = vars[name];
  if (v === undefined) throw new Error("undefined token --" + name);
  const m = v.match(/^var\(--([\w-]+)\)$/);
  if (m) { if (seen.has(m[1])) throw new Error("cycle " + name); seen.add(m[1]); return resolve(vars, m[1], seen); }
  return v;
}
function rgb(hex) {
  const h = hex.replace("#", "");
  if (!/^[0-9a-fA-F]{6}$/.test(h)) throw new Error("not a solid hex: " + hex);
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}
const lum = (c) => { const [r, g, b] = rgb(c).map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

const BODY = 4.5, UI = 3;
const surfaces = ["surface", "surface-raised", "surface-overlay", "surface-nested", "surface-sunken", "surface-floating"];
const pairs = [];
for (const s of surfaces) {
  pairs.push(["text-primary", s, BODY], ["text-quaternary", s, BODY], ["text-secondary", s, BODY], ["text-tertiary", s, BODY]);
  pairs.push(["brand-text", s, BODY], ["secondary-text", s, BODY]);
  pairs.push(["success-text", s, BODY], ["warning-text", s, BODY], ["danger-text", s, BODY], ["info-text", s, BODY], ["verified-text", s, BODY]);
  pairs.push(["brand", s, UI], ["focus-ring", s, UI], ["border-strong", s, UI], ["border-control", s, UI], ["selected-border", s, UI]);
}
pairs.push(
  ["on-brand", "brand", BODY], ["on-brand", "brand-hover", BODY], ["on-brand", "brand-pressed", BODY],
  ["brand-text", "brand-soft", BODY], ["text-primary", "brand-soft", BODY],
  ["secondary-text", "secondary-soft", BODY],
  ["success-text", "success-soft", BODY], ["warning-text", "warning-soft", BODY],
  ["danger-text", "danger-soft", BODY], ["info-text", "info-soft", BODY], ["verified-text", "verified-soft", BODY],
  ["selected-fg", "selected-bg", BODY], ["selected-border", "selected-bg", UI], ["selected-solid-fg", "selected-solid-bg", BODY],
  ["selected-solid-bg", "surface-overlay", UI], ["selected-solid-bg", "surface", UI],
  ["text-secondary", "selected-bg", BODY], ["text-tertiary", "brand-soft", BODY],
);
// [Design language 2026-09-29] trade-family tiles: the ink is the tile's
// icon AND may label it, so 4.5:1 on its own tint; the tint must also stay
// distinguishable text on the card surfaces (ink as text on surfaces).
for (const fam of ["amber", "sky", "green", "indigo", "plum", "teal"]) {
  pairs.push([`tile-${fam}-fg`, `tile-${fam}-bg`, BODY], [`tile-${fam}-fg`, "surface-raised", BODY], [`tile-${fam}-fg`, "surface", BODY]);
}

// High contrast (@palette-contrast) may only alias tokens this script
// already proves, so it can never introduce an unchecked pair.
const contrast = block("/* @palette-contrast */");
const proven = new Set(pairs.flat().filter((x) => typeof x === "string"));
for (const [k, v] of Object.entries(contrast)) {
  const m = v.match(/^var\(--([\w-]+)\)$/);
  if (!m || !proven.has(m[1])) { console.error("high-contrast --" + k + " must alias a checked token, got " + v); process.exit(1); }
}

let fails = 0;
const out = [];
for (const [themeName, vars] of [["light", light], ["dark", dark]]) {
  for (const [fg, bg, min] of pairs) {
    const a = resolve(vars, fg), b = resolve(vars, bg);
    const r = ratio(a, b);
    const ok = r >= min;
    if (!ok) fails++;
    out.push(`${ok ? "pass" : "FAIL"}  ${themeName.padEnd(5)}  --${fg} ${a}  on  --${bg} ${b}  ${r.toFixed(2)}:1  (min ${min})`);
  }
}
console.log(out.join("\n"));
console.log(`\n${pairs.length * 2} pairs checked, ${fails} failing.`);
process.exit(fails ? 1 : 0);
