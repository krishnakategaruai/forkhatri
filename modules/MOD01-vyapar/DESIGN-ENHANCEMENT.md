# Design Enhancement Spec — MOD01 Vyapar

## Palette 2026-09-29 (supersedes every colour rule below)

On 2026-09-29 the owner said: "colors need to be changed in vyapar, i really hate the colors you used, and theme based designs, else all other is good." The saffron-on-near-black, dark-first palette is retired. Everything else in this document still applies (structure, type, spacing, motion, the surface ladder, one primary action per screen). Where a later section names saffron, amber, `#e8871e`, `#D97A12`, "dark-first" or "accent-tinted chips", read it through this section. The research and every contrast ratio are in `references/palette-2026-09-29.md`.

**Rules**

1. **Light first.** The default page is a warm off-white "chalk" canvas (`--surface #f6f5f1`) with white cards (`--surface-raised #ffffff`). Dark mode is an option: it follows the phone or computer setting (`prefers-color-scheme`), and `<html data-theme="light|dark">` forces either theme. Dark is a blue-slate night (`#121419`), not near-black.
2. **One brand colour: "Neel" indigo.** `--brand #2b4acb` (dark `#8b9dff`). Use it only for the primary button, links (`--brand-text`), the focus ring (`--focus-ring`) and the current-page marker in the rail. Never use it on card titles, on selected chips, or on large areas.
3. **Card titles and headings use `--text-primary`.** globals.css enforces this for `.vy-card h2/h3`, `.vy-card-title`, `.vy-dcard-title` and `.vy-hub-tile-title`, with zero specificity so a component can still override it.
4. **Selected is neutral, not brand.** Chips, tabs, options and picked rows use `--selected-bg` / `--selected-fg` / `--selected-border` (an ink outline on a light fill). Segmented toggles without their own border use `--selected-solid-bg` / `--selected-solid-fg` (an ink fill).
5. **Secondary: peacock teal** (`--secondary`, `--secondary-soft`, `--secondary-text`). Use it only for small highlights such as icon tiles and the profile monogram.
6. **Semantic colours** (`--success`, `--warning`, `--danger`, `--info`, `--verified`) each come as a solid value, a `-soft` tint for backgrounds and a `-text` value for text. Always pair them with an icon or a word, never colour alone.
7. **The Search action** next to a search field (`.vy-search-action`) is a normal-sized button from 600px up. It is full width only on phones.
8. **No gradients, glass (backdrop blur) or glow.** The action bar and the top scrim are now solid.
9. **Every pair passes WCAG 2.2 AA in both themes** (4.5:1 text, 3:1 large text and UI). `node scripts/check-contrast.mjs` in `vyapar-web` reads the tokens from globals.css and fails if any pair drops below. Run it after any colour change.
10. **Tokens only.** Components never use hex, rgb or named colours. The legacy names `--accent*`, `--trust-*` and `--ink-*` remain as aliases so older code keeps working. New code uses `--brand*`, `--selected-*`, the semantic tokens and `--scrim`.

**Token names for other agents:** `--surface`, `--surface-raised`, `--surface-overlay`, `--surface-nested`, `--surface-sunken`, `--surface-floating`, `--border-hairline`, `--border-default`, `--border-strong`, `--text-primary`, `--text-quaternary`, `--text-secondary`, `--text-tertiary`, `--brand`, `--brand-hover`, `--brand-pressed`, `--brand-soft`, `--brand-text`, `--on-brand`, `--focus-ring`, `--secondary`, `--secondary-soft`, `--secondary-text`, `--success(-soft|-text)`, `--warning(-soft|-text)`, `--danger(-soft|-text)`, `--info(-soft|-text)`, `--verified(-soft|-text)`, `--selected-bg`, `--selected-fg`, `--selected-border`, `--selected-solid-bg`, `--selected-solid-fg`, `--scrim`, `--shadow-card`, `--shadow-float`.

---

**Created:** 2026-09-17. **Author:** UX critique agent, same persona as
`UX-CRITIQUE.md`. **Scope of this request:** the product owner asked to
"enhance colors, themes" — visual richness/polish within the **existing**
design direction, not a new direction. The existing rules stay fixed and are
restated here so the build agent does not drift from them:

- Near-monochrome base, exactly **one** accent colour (saffron/amber).
- **No** gradients, **no** glassmorphism, **no** neon glow, **no** ambient
  mesh, **no** decorative visual effects of any kind.
- Calm, quiet treatment of secondary content.
- Floating command hub, never a boxed tab bar.
- Dark mode is default; elevation is a **lightness step**, never a shadow
  (already Vyapar's own stated rule — see `globals.css`'s own header comment
  and 04-ui.md F4: "Dark — no shadows; raised surface + `--fk-border-subtle`").

This document does not propose new colours, effects, or a different mental
model. It proposes **how to get more perceived craft out of the rules Vyapar
has already committed to**, the same way the reference products below do.

---

## Research grounding (read before implementing)

Real, current (2026) sources on how disciplined single-accent dark UIs create
richness without new hues or effects:

1. **Linear's dark design system** — a **four-step surface ladder**
   (`#0f1011` → `#141516` → `#18191a` → `#191a1b`) where "every card, hovered
   tile, and lifted dropdown" gets its hierarchy from **which step it sits
   on**, not from a shadow; the practice cited is stepping luminance up
   **5-8% per level**. The accent (Linear's lavender) is "deployed scarcely
   on the brand mark, focus rings, and one primary CTA per section" — no
   second chromatic colour, no atmospheric gradient, no spotlight card.
   (shadcn.io/design/linear; open-design.ai/plugins/design-system-linear-app)
2. **Vercel's dashboard system** — "near-black canvas surfaces where content
   floats on subtly elevated cards with hairline borders," a **200-step gray
   scale where every divider, border, and disabled state lives on its own
   deliberate step**, and a "shadow-as-border" technique
   (`box-shadow: 0 0 0 1px rgba(0,0,0,.08)`) that reads as a crisp edge
   rather than a drop shadow. No gradients on core UI — only marketing pages
   get a radial fade. (shadcn.io/design/vercel; design.withfudge.com)
3. **General 2026 dark-mode practice** — "good dark mode is a designed
   system, not inverted colors: it expresses elevation by lightening surfaces
   instead of casting shadows, keeps text contrast at or above WCAG's 4.5:1,
   and dials saturation down so accents don't vibrate against dark
   backgrounds." (uxmagic.ai/blog/dark-mode-ui-design-guide;
   muz.li/blog/dark-mode-design-systems-a-complete-guide-to-patterns-tokens-and-hierarchy)
4. **Fintech's disciplined-restraint pattern** (Mercury, Ramp, and the 2026
   fintech-design surveys) — "the important number is unmistakably the
   largest, secondary details are grouped and quieted, and colour is used
   with restraint to mean something specific rather than to decorate";
   products "raising the bar for trust through restraint" lead with one clear
   hierarchy signal rather than a wall of equally-weighted colour.
   (theskinsfactory.com/uiux-design-blog/fintech-ui-ux-design;
   wandr.studio/blog/fintech-mobile-app-design-trends)

**The common thread across all four sources, applied to Vyapar:** richness
comes from (a) more, finer **tonal steps** of the *same* neutral used with
intent (which surface sits on which step, and why), (b) **border weight/
opacity as a second hierarchy channel** independent of fill colour, (c)
**restraint in accent placement** — the accent should mark the one thing that
matters on a screen, not repeat as default styling on every chip/badge, and
(d) **interaction feedback** (press/hover) carrying real state change, not
just a scale transform.

---

## What `globals.css` currently does (read in full, matched against the
above)

Vyapar's actual token set (`vyapar-web/app/globals.css`) is a 10-step
`--ink-0` … `--ink-9` neutral ramp (dark-first, light override under
`prefers-color-scheme`), one accent (`--accent` / `--accent-strong` /
`--accent-soft` / `--accent-ink`), one trust-green pair, two shadow tokens,
and the `.vy-*` component classes. This is a good foundation — the ramp
exists — but the **implementation only ever draws from 3 of the 10 steps**
for actual surface hierarchy:

```
--surface:          var(--ink-1)   /* page background */
--surface-raised:    var(--ink-2)   /* ALL cards, everywhere, no matter nesting */
--surface-overlay:    var(--ink-3)   /* dropdowns, sheets, AND selected-chip fill */
```

Everything that should visually sit "above" or "below" something else —
a nested panel inside a card, a sheet inside a screen, a pressed vs. resting
button, a primary vs. secondary card — currently lands on one of these same
three steps, or falls back to the *identical* `--shadow-card` token
regardless of context. That is the concrete, checkable gap this document
targets: **Vyapar already has the ramp Linear/Vercel use, it just isn't using
enough of it to carry hierarchy.**

Specific places this shows up in the actual code (read this pass):

- **Nested cards look identical to their parent.** `app/listings/[id]/page.tsx`
  places `VerificationPanel`'s own `.vy-card` (contact-visibility card,
  capability-visibility card) directly inside the same-level page flow as the
  top-level listing card — both render `--surface-raised` + `--shadow-card` +
  `--radius-lg`, so a "card inside the flow" and "the primary subject of the
  page" are visually indistinguishable. Same pattern in
  `app/workspace/[listingId]/page.tsx` (plan card, team card, campaign card
  all flat-identical) and `app/admin/commercial/page.tsx` (product cards,
  order cards, diagnostics card all flat-identical).
- **`.vy-chip` defaults to accent-tinted even when not selected/active.**
  `globals.css` line 291-301: the base `.vy-chip` class itself sets
  `background: var(--accent-soft); color: var(--accent-strong)` — i.e. every
  chip in the app is orange-tinted *by default*, and every screen that wants
  an "unselected" chip state has to override it inline with
  `background: var(--surface-overlay)` (seen repeatedly: `FilterSheet.tsx`,
  `admin/moderation/page.tsx`, `first-run/page.tsx`, `boost/.../page.tsx` —
  at least 8 separate inline overrides of the same base class). This is
  exactly the "accent used as decoration instead of meaning" pattern the
  fintech-restraint research warns against — informational/parsed chips like
  `IntentBar.tsx`'s `chipCategory`/`chipNear` (never overridden) render
  accent-tinted purely because that's the class default, not because they're
  selected or actionable.
- **Press/interaction feedback is thinner than the sealed F6 spec already
  called for.** 04-ui.md F6 (Button/primary) specifies: "Pressed: `transform:
  scale(0.98)` 100ms **+ fill darkens to `#D97A12`**." The actual
  `.vy-btn:active` rule in `globals.css` (lines 164-166) only has
  `transform: scale(0.97)` — no fill-darken step at all. The colour-shift
  half of the sealed press feedback was dropped somewhere between spec and
  build.
- **Borders carry no weight/opacity hierarchy.** `--border-subtle` (`ink-4`,
  `#262d38`) is the *only* border token used across every context — card
  edges, hover states (`LivingCard`'s hover uses `ink-5` inline, not a
  token), dashed Sponsored borders (`--trust-sponsored-border`, also
  `ink-6`, a third ad-hoc value). Three different border colours are already
  in use ad hoc (`ink-4`, `ink-5` inline, `ink-6` as a separate named token)
  with no documented relationship between them — Vercel's "200-step gray
  scale where every divider lives on its own deliberate step" is the
  discipline to apply here: name the steps, don't improvise them per file.
- **Only two elevation levels exist for the whole app** (`--shadow-card`,
  `--shadow-float`), and dark mode's own stated rule ("no shadows; raised
  surface + border") means `--shadow-card`'s actual visual contribution on
  dark surfaces is close to zero (a soft shadow barely reads against
  `--surface: #0b0e13`) — so in practice **most cards on dark mode have no
  real elevation cue at all** beyond the 1px border, which is correct per
  the lightness-step rule but means the lightness step itself is currently
  too coarse (only one raised step exists) to do the actual work.

---

## Recommended token additions (additive — nothing below removes or renames
an existing token; existing usages keep working)

```css
:root {
  /* --- Finer surface ladder (Linear's 4-step pattern, same ink family) ---
     Existing --surface/--surface-raised/--surface-overlay are UNCHANGED.
     These three are new, inserted between/around them for nesting depth. */
  --surface-sunken:   var(--ink-0);  /* below --surface: pressed states, input wells */
  --surface-nested:   var(--ink-3);  /* a card/panel INSIDE a --surface-raised card
                                          — currently both use --ink-2 and are
                                          visually indistinguishable */
  --surface-floating: var(--ink-4);  /* sheets, dropdowns, popovers — one step
                                          above --surface-overlay, reserved for
                                          content that visually floats over
                                          everything else (NotificationBell panel,
                                          TrustContextSheet, FilterSheet when open) */

  /* --- Named border steps (replaces three ad hoc uses of ink-4/5/6) --- */
  --border-hairline: var(--ink-4);  /* = current --border-subtle value, kept as
                                          an alias so existing CSS is untouched */
  --border-default:  var(--ink-5);  /* hover/focus-adjacent borders — currently
                                          hardcoded inline in LivingCard only */
  --border-strong:   var(--ink-6);  /* dashed Sponsored border, disabled-state
                                          borders — currently only
                                          --trust-sponsored-border used this value
                                          under a one-off name */

  /* --- Press feedback restored to the sealed F6 spec --- */
  --accent-pressed: #d97a12; /* exact value F6 already named ("#D97A12") and the
                                  current .vy-btn:active never applies */

  /* --- A second step for trust-green, matching the accent's soft/strong
     pattern, for VerificationBadge's OWN pressed/hover state when it's a
     button (TrustContextSheet trigger) --- */
  --trust-verified-strong: #4fc384;
}

@media (prefers-color-scheme: light) {
  :root {
    --surface-sunken:   #f0ece3;
    --surface-nested:   #f4f1ea;
    --surface-floating: #ffffff;
    --border-default:   #d0cbc0;
    --border-strong:    #b8b2a4;
  }
}
```

---

## Component-level recommendations, before/after, per screen type

### 1. Card (default list card — `.vy-card` used via `LivingCard` and directly)

**Before:** every card, at every nesting depth, is `--surface-raised` + 1px
`--border-hairline` + `--shadow-card` + `--radius-lg`. A card inside a card
(verification panel inside listing detail, plan card inside workspace) is
pixel-identical to the outer card.

**After (no new visual language, just using the ladder already proposed
above):**
- Keep top-level/primary cards (the subject of the screen — a listing, an
  opportunity, a queue item) exactly as-is: `--surface-raised`.
- Any card that sits *inside* another card's content flow (Verification
  panel, Contact visibility panel, Capability visibility panel inside
  Listing Detail; Plan/Team/Campaigns panels inside Workspace; Refund form
  inside an Order card in Admin Commercial) steps to `--surface-nested`
  (one step up in luminance from its parent, matching Linear's "step up 5-8%
  per level" practice) and drops the shadow entirely (nested content doesn't
  need its own elevation cue, the parent already established the layer).
- This is a config-only change: swap `className="vy-card"` for a new
  `className="vy-card vy-card-nested"` on the specific nested instances named
  above, where `.vy-card-nested { background: var(--surface-nested);
  box-shadow: none; }`.

### 2. Buttons (`.vy-btn-primary`)

**Before:** `:active` only scales (0.97). No colour change at all on press,
despite F6 explicitly naming a fill-darken step.

**After:**
```css
.vy-btn-primary:active {
  background: var(--accent-pressed);
}
```
Layer this alongside the existing `transform: scale(0.97)` (don't replace
it) — the combination of a colour shift *and* a scale-down on press is
exactly the "interaction feedback with intent" the research names as a
richness channel that doesn't require new colours, since `--accent-pressed`
is a darker step of the *same* accent hue, not a new one.

### 3. Chips (`.vy-chip`)

**Before:** the base class defaults to accent-tinted; every "unselected"
usage has to override it inline, and any chip that never gets that override
(informational/parsed chips in `IntentBar.tsx`) stays accent-tinted by
accident, not by intent — the exact "accent as decoration, not meaning"
anti-pattern the fintech research flags.

**After:** flip the base-class default to neutral, matching the majority of
selected/unselected usages already in the codebase, and make the *selected*
state the one that opts into accent:
```css
.vy-chip {
  background: var(--surface-overlay);
  color: var(--text-primary);
  border: 1px solid var(--border-hairline);
}
.vy-chip[aria-pressed="true"],
.vy-chip.vy-chip-selected {
  background: var(--accent-soft);
  color: var(--accent-strong);
  border-color: transparent;
}
```
This lets every screen currently doing manual `style={{ background: selected
? "var(--accent)" : "var(--surface-overlay)" }}` inline (FilterSheet,
first-run, admin/moderation, boost) drop the inline override entirely once
they add `aria-pressed` (several already do, for accessibility reasons
unrelated to this fix — e.g. `FilterSheet.tsx`'s radius chips), consolidating
one behaviour that's currently reimplemented per-file. The build agent should
confirm each call site before deleting its inline style, since a few (e.g.
`IntentBar`'s parsed chips) have no selection state at all and should simply
adopt the new neutral default with no `aria-pressed`.

### 4. Trust badge (`VerificationBadge`, when rendered as a button — i.e. has
`onOpenTrustSheet`)

**Before:** identical fill (`--trust-verified-soft` / `--trust-verified`)
whether resting or pressed — no feedback that it's interactive beyond the
cursor.

**After:**
```css
.vy-badge-verified:active {
  color: var(--trust-verified-strong);
}
```
One new token, reserved solely for this pressed state — not introduced as a
new "shade of meaning," just the same restrained two-step pattern
(soft/strong) the accent already uses, applied to the one other semantic
colour Vyapar has (trust green), so the badge confirms a tap the same way
the primary button does.

### 5. Sheets/overlays (`TrustContextSheet`, `NotificationBell`'s panel,
`FilterSheet` when expanded)

**Before:** `TrustContextSheet` and the FilterSheet card both render at
`--surface-raised` (`.vy-card`) — the same step as the ordinary list card
sitting behind them. Depth is currently implied only by the scrim
(`rgba(0,0,0,0.5)`) behind `TrustContextSheet`, which `NotificationBell`'s
dropdown doesn't even have.

**After:** these three genuinely-floating surfaces (things that sit *above*
the page, not inside its flow) move to `--surface-floating` (one step above
`--surface-overlay`), so a person's eye gets a real luminance cue that this
content is layered above the page even before the scrim/position registers.
No new visual device — same lightness-step logic already governing
`--surface` → `--surface-raised`, extended one more step.

### 6. Text hierarchy inside a card (list card meta lines)

**Before:** confirmed in `UX-CRITIQUE.md`'s own addendum this pass —
`LivingCard`'s `meta` prop (which carries reputation, freshness, relevance
*and* the submitter's name/community framing) is a single `<p
className="vy-muted">` line, i.e. everything in it gets identical weight at
`--text-tertiary`, 13px.

**After (design-system-level fix that also serves the UX-CRITIQUE finding):**
add a fourth text-emphasis step between `--text-secondary` and
`--text-tertiary` for content that's socially/trust-meaningful but not the
card's primary subject:
```css
--text-quaternary: var(--ink-8); /* NEW — between secondary (ink-7) and
                                        primary (ink-9); for submitter/
                                        community framing specifically */
```
`LivingCard` gets an optional `emphasis?: string` prop rendered at
`--text-quaternary` ahead of the existing `vy-muted` meta line, so "posted by
Asha · from your community" can sit one visible step above a plain freshness
stamp without introducing a new colour — purely a lightness-step move within
the same neutral ramp, consistent with every other recommendation in this
document.

---

## What this document deliberately does NOT propose

- No new hues. Every addition above is either a finer step of the existing
  `--ink-*` ramp, a second step of the existing accent, or a second step of
  the existing trust-green — never a new colour family.
- No gradients, glass, blur, or glow on any surface.
- No shadow increase on dark mode — the lightness-step rule stays exactly as
  sealed; `--shadow-card`/`--shadow-float` are untouched, only used more
  selectively (nested content drops its shadow rather than gaining one).
- No structural/navigation change — the floating CommandHub, card anatomy,
  and screen layouts are unchanged; this is a token- and CSS-class-level
  pass only.

## Handoff notes for the build agent

- All additions are backward-compatible CSS custom properties and two new
  utility classes (`.vy-card-nested`, `.vy-chip-selected`/`[aria-pressed]`)
  plus one new optional `LivingCard` prop. No existing class is renamed or
  removed, so this can land incrementally, screen by screen, without a
  full-app regression risk.
- Suggested implementation order, highest-visible-impact first: (1) chip
  default-state flip (touches the most screens, most visible), (2) button
  press-state fill (one CSS rule, every primary button in the app), (3)
  nested-card step-down (Listing Detail, Workspace, Admin Commercial), (4)
  floating-surface step (TrustContextSheet, NotificationBell, FilterSheet),
  (5) submitter/community text-emphasis step (ties into the still-open
  UX-CRITIQUE addendum finding on social-trust framing).
- After implementing, re-verify contrast: `--text-quaternary` (`ink-8`,
  `#c3c9d2`) against `--surface-raised` (`ink-2`, `#11151b`) and
  `--accent-pressed` (`#d97a12`) against `--accent-ink` (`#1c0f00`) both need
  a quick WCAG contrast check before shipping (expected to pass comfortably
  given the existing ramp's spacing, but not computed here — this is a spec,
  not a verified implementation).

## Sources

- [Linear Design System for React — Lavender, 22 components](https://www.shadcn.io/design/linear)
- [Linear design system — palette, typography & tokens](https://open-design.ai/plugins/design-system-linear-app/)
- [Vercel Design System for React — Ink, Geist](https://www.shadcn.io/design/vercel)
- [vercel.com website design: fonts, colors and UI patterns](https://design.withfudge.com/share/vercel.com-design)
- [Dark Mode UI Design: A Definitive 2026 Guide](https://uxmagic.ai/blog/dark-mode-ui-design-guide)
- [Dark Mode Design Systems: A Complete Guide to Patterns, Tokens, and Hierarchy](https://muz.li/blog/dark-mode-design-systems-a-complete-guide-to-patterns-tokens-and-hierarchy/)
- [Fintech UI/UX Design: Best Practices for Financial Apps in 2026](https://www.theskinsfactory.com/uiux-design-blog/fintech-ui-ux-design)
- [Fintech Mobile App Design Trends for 2026 | WANDR](https://www.wandr.studio/blog/fintech-mobile-app-design-trends)
