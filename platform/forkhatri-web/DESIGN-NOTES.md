# ForKhatri entrance — design notes

Owner direction (2026-09-14, live on the signed-in hub at 390×844): "improvise this
screen very much better, minimalist and modern." Earlier standing feedback: decorative
multi-hue gradients and glassmorphism read as generic AI-generated UI; prefer one
accent colour with semantic roles. The previous hub (six tinted glass cards, per-module
accent glows, gradient orb, ambient mesh) is replaced.

## Research findings (verified 2026-09-14)

1. **Google app launcher (Material 3 Expressive, 2026)** separates what you use from
   everything else: a "Your favorites" group sits in one rounded container with a single
   lighter/darker surface, and the remaining apps live in an outer scrolling container.
   Hierarchy comes from grouping and surface tone, not colour.
   https://9to5google.com/2026/01/26/google-app-launcher-m3e-redesign/
   → *Applied:* open modules form one grouped list. Modules that aren't open yet sit in
   a separate, quieter group underneath.

2. **Apple App Library** is automatic: apps are "automatically sorted into categories",
   the most-used reorder by usage, and search is the fast path. The member never
   maintains the structure. https://support.apple.com/en-us/108324
   → *Applied:* the order stays automatic (recently entered first, then registry
   order), and the ask field sits at the top as the search-like fast path.

3. **Grab superapp** treats service tiles as the first thing on launch that must be
   interactive immediately. Tiles change by city because "available services vary in
   each city". Availability is honest and contextual.
   https://engineering.grab.com/journey-to-a-faster-everyday-super-app
   → *Applied:* only available modules are prominent and tappable. Everything else is
   labelled "Being built" or "Planned" inside the collapsed "Coming to ForKhatri" row.

4. **Tata Neu UX review**: "Each brand has a distinct identity … different logo styles,
   colors, fonts and even navigation styles", which produced "a very broken experience
   when navigating across use cases." https://uxhack.co/blog/tata-neu-ux-first-impression/
   → *Applied:* registry `accent` colours are no longer painted on the hub. Every
   module row uses the same monochrome line glyph and the same type, so ForKhatri reads
   as one product.

5. **PhonePe home case studies** found the home "cluttered with information", with
   rarely used features on the home screen and features "spaced very close together",
   causing wrong taps and cognitive overload.
   https://medium.com/@sudhak45/analyzing-phonepe-a-ux-design-case-study-e3482692a37e ·
   https://medium.com/design-bootcamp/suddenly-everything-changed-a-case-study-on-phonepes-overwhelming-redesign-8d027ba5e983
   → *Applied:* four not-yet-open modules collapse into one row instead of four cards.
   Rows are at least 64px tall with generous gaps.

6. **Monzo's new Home screen** pursued simplicity that "brings order to complexity":
   the main jobs come first, and deeper detail and new products are secondary.
   https://monzo.com/blog/the-new-and-improved-home-screen ·
   https://monzo.com/blog/how-we-built-the-new-home-screen
   → *Applied:* the hierarchy is greeting → ask → open modules → coming soon. There is
   no promotional or invented content.

7. **Linear interface refresh (March 2026)** "reduces icon usage, scales their sizes
   down, and removes unnecessary visual treatments like colored team icon backgrounds".
   It moved from a saturated blue-ish palette to "a warmer gray … less saturated", and
   dimmed chrome so "the main content area … take[s] precedence".
   https://linear.app/now/behind-the-latest-design-refresh
   → *Applied:* warm near-neutral greys, small monochrome glyphs without coloured
   tiles, and a header in the same tone as the page.

8. **Vercel Geist colour system** is built on a gray scale plus two background values,
   with each step mapped to a role: backgrounds 100–300, borders 400–600, text
   900–1000. Hue is reserved for function rather than decoration.
   https://vercel.com/geist/colors
   → *Applied:* role tokens (`--bg`, `--surface`, `--line`, `--ink`, `--ink-2`,
   `--ink-3`) plus one accent.

## Scope (owner correction, 2026-09-14)

- The minimalist system applies **only to the signed-in hub** and its header, composer,
  account sheet and notifications sheet (`app/hub.css`, scoped to `.app[data-look="hub"]`).
- Signed-out screens keep the owner-approved first-pass look: arrival/sign-in, code,
  name, password, language switcher, orb and aurora background, plus offline and
  redirecting (`app/arrival.css`, scoped to `.app[data-look="arrival"]`). The only kept
  change there is the shorter identifier placeholder.
- Every module (open and not yet open) fits on the first phone screen with the greeting
  and the ask field, at 390×844 and 360×740 in en/hi/te. Not-yet-open modules are
  compact, muted, non-interactive tiles.
- **Devotional emblem:** ForKhatri's own emblem of Bhagwan Kartavirya Sahasrarjun
  (`public/assets/devotional/sahasrarjun-emblem.svg`) sits beside the greeting.
  - It is rendered as a CSS mask in a warm gold with a localized name line.
  - It is decorative-devotional: `role="img"`, not interactive, no effects.
  - It appears on the signed-in hub and nowhere else.
  - The Commons photo in that folder is a reference only and is never rendered.

## The system

- **Palette:** warm near-black (dark, default) and warm off-white (light, via
  `prefers-color-scheme`). There is no mesh background, blur/glass, or multi-hue
  gradient.
- **One accent: ForKhatri saffron**, used only for these roles:
  - brand mark
  - focus ring
  - active/current state (selected code cell, "visited" dot, module chip dot in the
    understood intent)
  - links
  - progress while entering a module

  Primary buttons use the ink colour (inverse), not the accent.
- **Type:** Sora for headings (tight tracking for Latin only), Geist for UI, and Noto
  Devanagari/Telugu. Hierarchy comes from size and weight, not colour.
- **Hub:**
  - date eyebrow → greeting → one-line subtitle → ask field (a plain input-shaped
    button; `/` on desktop)
  - "Open now" list, then a collapsed "Coming to ForKhatri" row that expands to show
    honest statuses
  - desktop adds starter suggestions under the ask field in a sticky left column
- **Ask:** the floating orb is removed. The ask field opens a composer: a bottom sheet
  on phones, a centred dialog on desktop (the command-palette pattern). It keeps the
  rule-based parser, understanding chips and voice input where supported.
- **Header:** opaque page-tone surface at all times; a hairline border appears once
  content scrolls under it. Bell sits immediately left of the avatar, the avatar is
  right-most, and there is no tab bar.
- **Motion:** short fades and a gentle stagger, press feedback, and sheet springs, all
  honouring `prefers-reduced-motion`. Tilt, parallax and glows are removed.
