# Vyapar design language, 2026-09-29

**Why:** on 2026-09-29 the owner said, "Somewhere I feel this complete design is old fashioned." Discover at 1440px had these problems:

- a permanent 248px sidebar of checkboxes and radio buttons;
- plain text-only cards;
- generic chips;
- floating pills (language, alerts, name) instead of a real header.

In short, it read like a 2015 e-commerce filter page. The same day the owner added a second requirement: the product must adapt to *everyone*, judged with a 2030 mindset. That means:

- a less literate delivery worker on a budget Android;
- Hindi-only and Telugu-only readers;
- women looking for safe work;
- a fresher;
- a kirana owner posting jobs;
- a CA or developer at a desk who wants density and speed;
- older people who need large text and high contrast.

This document is the visual and interaction language that answers both requirements. It keeps the palette of 2026-09-29 (`palette-2026-09-29.md`): chalk canvas, white cards, one Neel indigo brand, neutral selection. What it changes is shape, type, density, structure and motion.

Where it lives:

- **Tokens:** `vyapar-web/app/globals.css`.
- **The language applied to shared classes:** `vyapar-web/app/styles/language-2026.css`, loaded last, so every screen picks it up without markup changes.
- **Shell:** `app/components/nav/AppTopBar.tsx`, `app/components/CommandHub.tsx`.
- **Discover:** `app/components/discover/*`.
- **Trade icons:** `app/components/discover/trades.tsx`.

---

## Typography 2026-09-29 (premium) — supersedes §3 Type

**Why.** Reviewing the live screens on 2026-09-29 the owner said "see the fonts also" and "i wanted this to be a premium website for vyapar, but this looks ugly." Noto Sans had been chosen for one reason only, script coverage, and it reads as the default Android face. This section replaces §3.

### What premium products actually do

| Reference | Evidence | What we take |
|---|---|---|
| **Airbnb (Cereal)** | One custom geometric sans, "from button to billboard", set small and confident with tight negative tracking and generous line-height; never a second typeface ([Creative Review](https://www.creativereview.co.uk/airbnb-introduces-custom-typeface-cereal/), [Refero](https://styles.refero.design/style/c2325884-4391-4688-85cd-e143f5107517)). | One family, roles by weight and tracking, not by mixing faces. |
| **Revolut (Aeonik + Inter)** | A humanist display face at 500 for everything 20px and up, Inter as the workhorse for body, buttons and metadata ([Fonts In Use](https://fontsinuse.com/uses/61484/revolut), [CoType](https://cotypefoundry.com/fonts-in-use/revolut)). | A display role with character, a quiet UI role. |
| **Notion (Inter + Lyon), Linear (Inter Display)** | Inter for UI, a serif only for editorial pull quotes; Linear uses Inter throughout ([Wikipedia: Inter](https://en.wikipedia.org/wiki/Inter_(typeface))). | Restraint: the premium feel is hierarchy and spacing, not decoration. |
| **2026 trend write-ups** | "Big x-heights, tight letterfit, swaggering proportions"; display type as the statement piece over simple body copy; personality replacing uniform hyper-minimal sans ([Creative Bloq](https://www.creativebloq.com/design/fonts-typography/breaking-rules-and-bringing-joy-top-typography-trends-for-2026), [Untitled UI](https://www.untitledui.com/blog/best-free-fonts), [Fontfabric](https://www.fontfabric.com/blog/10-design-trends-shaping-the-visual-typographic-landscape-in-2026/)). | Tight-tracked heavy display, calm body. |

### Indic-aware candidates on Google Fonts (verified against the font data shipped with `next/font/google`)

| Family | Scripts in one design | Weights | Verdict |
|---|---|---|---|
| **Anek** (Ek Type): Anek Latin, Anek Devanagari, Anek Telugu | Latin, Devanagari, Telugu (plus seven more Indian scripts), all drawn together by one collective ([Google Design, "Design for Many"](https://design.google/library/anek-multiscript), [GitHub EkType/Anek](https://github.com/EkType/Anek), [ektype.in](https://ektype.in/anek-latin.html)) | Variable 100–800 (+ width 75–125) | **Chosen.** "Sharp terminals and tapered joineries" give the Latin character; the scripts share circular forms and terminals, so Hindi and Telugu screens look designed, not fallen back. Tabular figures present (measured in Chrome: `1111` and `0000` equal width with `tnum`). |
| Tiro Devanagari Hindi / Tiro Telugu (Tiro Typeworks) | Serif text faces with a Latin subset (Castoro) ([Google Design](https://design.google/library/the-modern-tiro-indic-collection-font)) | 400 + italic only | A book face; no weight range for UI or display. Rejected. |
| Hind / Hind Guntur (ITF) | Devanagari + Latin; Telugu + Latin ([Google Fonts](https://fonts.google.com/specimen/Hind%2BGuntur)) | 300–700 static | Solid UI humanist, but two separate families and a plain Latin; read as utility next to Anek in the specimen. Rejected. |
| Poppins, Mukta, Yantramanav, Baloo 2, Martel, Khand, Teko | Devanagari + Latin only | various | No Telugu companion; Baloo, Teko and Khand are display-only. Rejected. |
| Noto Serif / Noto Serif Devanagari / Noto Serif Telugu | all three | variable 100–900 | Coherent, but heavy Devanagari serif reads as newsprint, the "old fashioned" the owner already rejected. Rejected. |
| Mallanna, Ramabhadra, Gotu | single script | 400 only | No range. Rejected. |
| Inter / Inter Tight, Manrope, DM Sans, Geist, Plus Jakarta Sans | Latin only | variable | Would need Hind or Anek for Indic: two designs side by side. Rejected for the reason Airbnb never adds a second face. |

Specimen: `screenshots/2026-09-29/type-specimen-candidates-1440-light.png` (Noto Sans vs Anek vs Inter Tight + Hind, in en, hi and te at card sizes).

### The system

- **Family:** Anek Latin, Anek Devanagari, Anek Telugu, loaded in `app/layout.tsx` via `next/font/google` (`display: "swap"`, weight axis only). Latin is preloaded; Devanagari and Telugu are declared with `unicode-range` and `preload: false`, so an English reader on a budget Android downloads one font.
- **Tokens** (`app/globals.css`): `--font-display`, `--font-body` (both the Anek stack today; kept separate so the roles can diverge later), `--font-sans` as the legacy alias. Roles: `--weight-display` 700, `--weight-title` 650, `--weight-heading` 600, `--weight-ui` 600, `--weight-body` 400; `--tracking-hero` −0.03em, `--tracking-display` −0.024em, `--tracking-title` −0.016em, `--tracking-heading` −0.008em, `--tracking-ui` 0, `--tracking-label` 0.01em; `--leading-display` 1.05, `--leading-title` 1.15, `--leading-heading` 1.3, `--leading-body` 1.55, `--leading-ui` 1.2.
- **Scripts:** `:lang(hi)` and `:lang(te)` reset every tracking token to 0 and raise the leading tokens (body 1.7, heading 1.4, title 1.3, display 1.25, UI 1.4) in `language-2026.css`; the family stack falls through per glyph, so digits and ₹ inside Hindi text stay in Anek Latin.
- **Numbers:** `font-variant-numeric: tabular-nums lining-nums` on `.vy-num`, `.vy-money`, `.vy-ocard-pay`, `.vy-qbar-count`, `.vy-iconbtn-badge`, `.vy-fopt-count`, `.vy-avatar`, `time`, `[data-numeric]`. Screen agents: put `.vy-num` (or `data-numeric`) on any pay line, count, date or ID column.

### Scale (Anek has a lower x-height than Noto, so every step is one notch larger; nothing renders below 13px)

| Token | Size (phone to desktop, at a 16px root) | Role |
|---|---|---|
| `--type-hero` | 34px to 56px (fluid) | Discover greeting, one per screen: 700, `--tracking-hero` |
| `--type-display` | 30px to 44px | Page `<h1>`: 700, `--tracking-display` |
| `--type-title` | 22px to 30px | Row and sheet titles, `<h2>`: 700, `--tracking-title` |
| `--type-heading` | 18px to 20px | Card titles, `<h3>`, `.vy-card-title`: 600, `--tracking-heading` |
| `--type-pay` | 22px to 24px | The pay line: 700, tabular figures |
| `--type-body` | 17px | Body: 400, leading 1.55 |
| `--type-sm` | 15px | Buttons, chips, tabs, labels, meta: 600 (UI) / 400 (text) |
| `--type-xs` | 13.5px | Badges, tile labels, fine print: 600 |

Text size (A / A+ / A++, `html[data-text]`) and High contrast keep working: every size is rem, every colour is a token.

### Shared components (tokens and `vy-*` classes only)

- Heights: buttons 44 (primary 48), chips 40 (44 on touch), tabs 44, segmented options 40 (44 on touch), inputs 48, icon buttons 44, See-all and card info buttons 44. Chip, tab and button labels are `--type-sm` at 600, tracking 0.
- Cards: `--card-pad` 16 / 20 / 24px (phone / 600px and up / 900px and up); hover lifts 1px with `--shadow-raise`.
- Motion: `--ease-out` cubic-bezier(0.2, 0.8, 0.2, 1); press `--dur-press` 180ms on a short spring; sheets and drawers `--dur-sheet` 240ms (up on phones, in from the right on desktop); hover `--dur-hover` 160ms. Reduced motion removes every transform and animation.
- Shell: the wordmark is a logotype in the display face (700, −0.035em). Phone pages pad their bottom by `--hub-clear` (hub height + float + breathing room) plus the safe-area inset, so the floating hub never covers the last card.
- Dark theme: surfaces lifted one step to a blue-slate night (`#151821` canvas, `#1d212b` cards, `#2c3240` floating) after the owner's device check read them as black; `scripts/check-contrast.mjs` re-proves 264 pairs.
- Phone Discover: the two tabs share the width and show the short "Businesses" label; the search placeholder is the short key on phones; the mic is a 44px quiet icon and the input reserves its width; trade names wrap to two lines and never ellipsize; the location chip drops "Near" (the pin says it).

---

## 1. Research: what makes a 2026 product feel current

| Reference | What we looked at | What we take | What we leave |
|---|---|---|---|
| **Airbnb, May 2025 redesign** ([CNBC](https://www.cnbc.com/2025/05/13/airbnb-app-redesign-services-business.html), [9to5Mac](https://9to5mac.com/2025/05/13/airbnb-app-redesign-services-experiences-originals/), [It's Nice That](https://www.itsnicethat.com/articles/airbnb-app-redesign-140525)) | Three top tabs (Homes, Experiences, Services), each with a rich icon. A floating search pill. Softer, more curved edges and "fluid animations". Big photographic cards. | The **two-way switch at the top** (Opportunities / Businesses), with an icon on each tab. The **floating search pill**. Generous radii. Motion that explains a change. | The clay-like 3D icons: they are costly, and Airbnb draws them in-house. Our icons are original line icons on tinted tiles. |
| **Airbnb retired its category icon rail** ([Skift, 2025-09-25](https://skift.com/2025/09/25/airbnbs-categories-were-meant-to-reinvent-the-search-box-now-theyre-gone/)) | Category search "lost its utility when it expanded beyond one product". It was inspiration browsing for homes, not a tool. | A category rail only works when **tapping a tile does real work**. In Vyapar a tile applies a skill filter in place, and the tile states what it is ("Electricians", not "Amazing pools"). | Mood categories. |
| **ixigo hotels** (the owner's reference; measured by FE2 in `palette-2026-09-29.md`) | Horizontal themed rows, each with a title, "View all" and side arrows on desktop. Light canvas, white cards, the brand colour only on the one search action. | **Themed rows with snap scroll**, desktop arrows and "See all". The brand colour stays on the search button and primary actions. | — |
| **Apple App Store "Today"** ([Apple newsroom](https://www.apple.com/newsroom/2017/06/apple-unveils-all-new-app-store/), [Farrugia teardown](https://medium.com/@phillfarrugia/re-building-the-new-app-store-app-today-view-38b816f7302e)) | Cards with "rounded corners, a soft shadow… and some labels". Bold editorial type. The big line is the one that matters. | **One hero line per card.** On an opportunity card that line is the pay. Bold, large section titles. | Full-bleed photos (we have none of real people, by rule). |
| **Swiggy / Instamart, Zepto** ([Instamart case study](https://medium.com/@ar.kalloldeb/swiggy-instamart-designing-for-one-of-the-worlds-largest-instant-grocery-platform-02ea8ff8fd00), [Zepto case study](https://medium.com/design-bootcamp/ux-case-study-improving-the-user-experience-of-zepto-app-c9a61acb3ce9)) | Category tiles "in a dense grid or scrollable lane". A visual tile with a word under it. Understood at a glance by every literacy level. | **Tinted category tiles with a label underneath**, as a scrollable lane on the home screen and as a full grid in "All categories". | Promotional banners and discount noise. |
| **Urban Company** ([their own blog on the logo](https://www.urbancompany.com/blog/when-looks-do-matter-the-story-behind-our-new-logo), [app redesign notes](https://medium.com/uc-design/the-all-new-urban-company-app-32b3953e990e)) | Black and white "because they communicate simplicity". Service tiles are the entry to everything. Trust (verified professionals, fixed prices) sits on the card. | **Neutral ink carries the UI.** Service (trade) tiles are the entry point. **One trust badge on the card**, not a badge wall. | — |
| **Linear UI redesign** ([Linear](https://linear.app/now/how-we-redesigned-the-linear-ui)) | "Reduce visual noise… increase the hierarchy and density of navigation". Themes come from three variables. Darker text in light mode. | A **quiet, dense desktop rail**. The brand colour marks only the current page. Density for the desk user. | — |
| **CRED** ([NeoPOP](https://github.com/CRED-CLUB/neopop-web)) | Dramatic, dark, "premium". | Nothing visual. The palette decision already rejected it. We take only its **springy, tactile press feedback**. | Neon on black. |
| **Revolut, Perplexity Discover** | Revolut: a big balance number as the hero, with small tinted icon tiles for categories. Perplexity: a left rail of product icons with editorial cards ([shadcn study of Perplexity's system](https://www.shadcn.io/design/perplexity)). | **Numbers as heroes** (pay). **Small tinted icon tiles.** A rail of icons with labels. | — |
| **Apna** ([Google Play](https://play.google.com/store/apps/details?id=com.apnatime&hl=en_IN), [application flow study](https://medium.com/@muskaan.mourya20/making-every-tap-count-ux-enhancements-in-apnas-job-application-journey-492e2099db49)) | Built "for India's blue- and grey-collar workforce… basic smartphones and different regional languages". The study found people "didn't know how many steps were left". | Cards that answer **pay, place, when** before anything else. Large tap targets. No hidden steps. | — |
| **Material 3 Expressive, 2025** ([Android Authority deep dive](https://www.androidauthority.com/google-material-3-expressive-features-changes-availability-supported-devices-3556392/), [M3 motion](https://m3.material.io/styles/motion/overview/how-it-works)) | "46 research studies… 18,000 participants"; expressive designs "were found to be more usable". Spring motion ("spatial springs mirror the physics of how objects move"), larger components and emphasised type. | **Spring motion for anything touched.** **Bigger buttons and chips.** **Emphasised type** for the one line that matters. | Shape morphing for its own sake. |
| **2026 trend write-ups** ([Muzli 2026 patterns](https://muz.li/blog/whats-changing-in-mobile-app-design-ui-patterns-that-matter-in-2026/), [Elinext 2026](https://www.elinext.com/services/ui-ux-design/trends/key-mobile-app-ui-ux-design-trends/)) | Bottom sheets are now "the expected pattern for anything that doesn't deserve a full-screen takeover: settings, filters…". Thumb-zone primary actions. Bento or modular cards. | **Filters in a bottom sheet** (a right drawer on desktop), never a permanent sidebar. **A floating bottom hub in the thumb zone.** | Glassmorphism, and dark-as-default (both rejected by the owner). |

**Research on reaching everyone**

- **Low literacy.** In studies, text-only interfaces failed for low-literacy users, graphical interfaces reached full task completion, and voice helped. Abstract icons alone are "semantically opaque" and need words next to them ([Medhi et al., Microsoft Research](https://www.microsoft.com/en-us/research/publication/designing-mobile-interfaces-for-novice-and-low-literacy-users/); [ACM, *Actionable UI guidelines… inclusive of low-literate users*](https://dl.acm.org/doi/10.1145/3449210); [Islam et al., systematic review, 2023](https://journals.sagepub.com/doi/full/10.1177/21582440231172741)). **Rule: an icon never appears without its word, and the word never appears without its icon on navigation and category tiles. Voice sits in every search.**
- **Target size.** WCAG 2.2 sets a floor of 24×24 CSS px ([W3C 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)). We aim far above it: 44px minimum for anything tappable and 48px for primary actions, because a budget phone with a cracked screen is our baseline, not an edge case.
- **Contrast.** WCAG 2.2 AA is proven by `scripts/check-contrast.mjs`. The high-contrast mode raises secondary text and every border (section 9).

---

## 2. Principles (the five rules every screen follows)

1. **The first screen answers "what can I do here" with pictures and one line of words.** Every trade has its icon on a tile, a word under it, and a way to speak it (mic).
2. **One hero per card, one primary action per screen.** On an opportunity card the hero is the pay, with its period. On a screen, only one button is filled with the brand colour (critique D4). **Post** in the rail and the hub is therefore an *ink* button, not brand: on Discover the one brand fill is Search.
3. **Filters come to you, not sit beside you.**
   - Quick chips cover the six filters people use most.
   - Everything else sits behind a **Filters** button: a bottom sheet on phones, a right drawer on desktop.
   - The page always gives its full width to results.
4. **Motion explains cause and effect.** A tapped tile springs and the list below reflows. A sheet rises from where the thumb is. A card lifts under the pointer. Nothing moves on its own, and everything respects *reduce motion*.
5. **The same screen, tuned for each reader.** Text sizes are in `rem`, so the OS font setting works. There are **Text size** (A, A+, A++) and **High contrast** controls in the top bar. Desktop density is tighter than phone density, set by breakpoint and not by a different design.

---

## 3. Type

Noto Sans stays. It is the one family that covers Latin, Devanagari and Telugu with matching metrics, and the owner's i18n rule needs all three. What changes is **weight contrast and size**, with every size in `rem` so it follows the OS font-size setting and Vyapar's own Text size control.

| Token | Size (phone to desktop) | Weight / tracking | Use |
|---|---|---|---|
| `--type-hero` | 2rem to 3.25rem (fluid) | 800 / −0.035em | Discover greeting, one per screen |
| `--type-display` | 1.75rem to 2.625rem | 750 / −0.028em | Page `<h1>` on other screens |
| `--type-title` | 1.3rem to 1.75rem | 750 / −0.02em | Row titles, sheet titles |
| `--type-heading` | 1.0625rem to 1.1875rem | 700 / −0.01em | Card titles |
| `--type-pay` | 1.25rem to 1.375rem | 800 / −0.015em, tabular numbers | The pay hero line on a card |
| `--type-body` | 1rem | 400 / 0 | Body |
| `--type-sm` | 0.875rem | 600 on UI, 400 on text | Chips, meta lines |
| `--type-xs` | 0.8125rem | 600 | Badges, tile labels |

Rules:

- No text in the app is smaller than **13px at default size**. The old 11px hub labels are gone.
- Line height is 1.5 for body text and 1.1–1.25 for headings.
- Indic scripts get line height 1.6 on body text and never negative tracking (`:lang(hi)`, `:lang(te)`): matras and conjuncts need the room.
- Titles clamp at 2 lines and meta lines at 1 line with an ellipsis. Hindi and Telugu words run about 30–60% longer than English, so **no fixed-width text boxes**. Tiles and chips grow and wrap to 2 lines.

## 4. Shape (radius)

| Token | Value | Use |
|---|---|---|
| `--radius-xs` | 8px | Tiny badges |
| `--radius-sm` | 12px | Inputs inside dense panels, menu items |
| `--radius-md` | 16px | Inputs, icon tiles (40–48px), segmented tabs |
| `--radius-tile` | 20px | Category tiles (64px) |
| `--radius-card` | 22px | Cards |
| `--radius-lg` | 28px | Sheets, drawers, the hero search surface, large panels |
| `--radius-pill` | 999px | Buttons, chips, the search pill, the hub |

Concentric rule: an inner radius equals the outer radius minus the padding. An icon tile inside a card with 16px padding and a 22px radius gets a 12–16px radius, so corners never look pinched.

## 5. Space and density

The 4px base scale is unchanged (`--space-1` 4px to `--space-8` 64px).

| | Phone (<600) | Tablet (600–899) | Desktop (≥900) | Wide desktop (≥1280) |
|---|---|---|---|---|
| Page gutter | 16px | 24px | 32px | 40px |
| Card padding | 16px | 18px | 18px | 20px |
| Gap between rows | 28px | 32px | 36px | 40px |
| Card width in a row | 80vw (max 300px), so the next card peeks | 300px | 300px | 312px |
| Results grid | 1 column | 2 columns | 3 columns | 4 columns |
| Tap target minimum | 44px (primary 48px) | 44px | 40px (pointer), chips 36px | same |

Desktop density is higher because the CA and the developer asked for speed. The phone keeps big targets because the delivery worker is on a budget Android.

## 6. Elevation (subtle, token-based)

| Level | Token | Where |
|---|---|---|
| 0, flat | hairline border only | Nested panels, chips at rest |
| 1, resting | `--shadow-card` | Cards on the canvas |
| 2, raised | `--shadow-raise` | A card under the pointer (with a 2px lift), a sticky bar once content scrolls under it |
| 3, floating | `--shadow-float` | Sheets, drawers, menus, the hub, the top-bar search pill |

- A shadow is never a colour or a glow.
- Dark mode uses deeper, tighter shadows, plus one surface step up (`--surface-floating`) for real layering.

## 7. Iconography

- **Library:** [lucide-react](https://lucide.dev) (ISC licence), one line family:
  - 24-unit grid, `stroke-width` 1.75 (2 for the 16px size);
  - `currentColor`, so icons take the text colour and pass the same contrast.
- **Sizes:** 16px inline with text, 20px in buttons, chips and rails, 24–28px in tiles.
- **Every navigation icon and category icon has its word.** Icon-only buttons (bell, close, arrows) always carry an `aria-label` and a tooltip on desktop.
- **Trade icons** (`trades.tsx`):
  - Each of the 22 taxonomy categories and each of its 62 specialties maps to its own icon. Examples: electrician → plug, plumber → wrench, driver → steering wheel, delivery → package, cook → chef hat, tailor → scissors, CA / accounting → calculator, GST → receipt, developer → code, designer → pen tool, tutor → graduation cap, beautician → sparkles, security guard → shield, nurse → stethoscope, carpenter → hammer, painter → paint roller, photographer → camera, welder → flame, telecaller → headset, and so on.
  - A specialty without its own icon falls back to its category's icon.
  - The UI never shows an empty tile.

## 8. Category visuals (original, no stock people)

**Trade tile:**

- a tinted square (64px on phones, 72px on desktop, radius `--radius-tile`);
- the trade icon at 28px in the tint's ink colour;
- the word underneath, up to 2 lines, centred.

**Tint families** carry *meaning* (the family of work), not decoration. There are six restrained tints, each with a solid ink colour that passes 4.5:1 on its tint:

| Family | Token | Trades |
|---|---|---|
| Hands-on and home | `--tile-amber-*` | home repair, manufacturing, automotive, handicraft, printing |
| On the move | `--tile-sky-*` | drivers, delivery, logistics |
| Food, home and care | `--tile-green-*` | cooks, catering, housekeeping, security, health |
| Office and money | `--tile-indigo-*` | CA & tax, legal, office admin, sales |
| Tech, design and media | `--tile-plum-*` | developers, designers, photo and video, marketing |
| Learning and wellbeing | `--tile-teal-*` | tutors, beauty, wellness, events, textiles |

- A **selected** tile shows the neutral selected ink ring (2px `--selected-border`) and a check badge, following the palette's rule that selection is neutral, not brand.
- No gradients, no 3D and no people. The same tile, shrunk to 40–44px, is the trade icon on every opportunity card, so a person who cannot read "Electrician" still recognises the plug on the card that the tile promised.

## 9. Colour additions (the palette is otherwise untouched)

- **`--tile-*-bg` / `--tile-*-fg`**, six pairs, light and dark. Checked by the contrast script at 4.5:1 (ink on tint) and 3:1 (ink on surfaces).
- **`--shadow-raise`**, light and dark.
- **High contrast** (`<html data-contrast="more">`):
  - applied automatically when the OS asks (`prefers-contrast: more`), or from the Text and display menu;
  - secondary and tertiary text become near-primary;
  - hairline and subtle borders become `--border-strong`;
  - selected fills get a 2px ring.
  - The checker verifies this block too.
- **Text size** (`<html data-text="l|xl">`) sets the root font size to 112.5% or 125%. Because all type and component heights are in `rem`, the whole UI grows, not only paragraphs. The OS or browser font setting stacks with it.

## 10. Card anatomy: the opportunity card

```
┌──────────────────────────────────────┐  radius 22, padding 16–18, --shadow-card
│ [▣ trade tile 44]           Apply ›  │  tile tinted by family · action chip (kind of response)
│                                      │
│ Frontend developer (React)           │  --type-heading 700, 2-line clamp, ink colour
│ ₹9–14 LPA                            │  --type-pay 800: the hero line, always ₹ with its period
│ ⌖ Kondapur · 12.6 km                 │  icon + place · distance, 1 line
│ ─────────────────────────────────    │  hairline
│ ✓ Verified business      16 days ago │  ONE trust badge (the strongest earned) · posted time
└──────────────────────────────────────┘
```

- **Order of reading:**
  1. what kind of work (the icon);
  2. what the job is;
  3. how much it pays;
  4. where it is;
  5. whether to trust it and how fresh it is.
- Every card answers "pay, place, when" before anything else, as Apna and WorkIndia do.
- The **action chip** ("Apply", "Send proposal", "Enquire") is a neutral outline pill with an arrow. The whole card is the link, so the chip is a label of *what happens*, not a second target.
- **Why this?** An information button in the footer shows the reason in place (FE2's feature, kept).
- **Sponsored** keeps its dashed outline tag, beside the action chip.
- **Hover** (pointer only): lift 2px, `--shadow-raise`, border one step stronger; spring 200ms.
- **Press:** scale 0.98, with a spring back.

## 11. Discover structure

**Phone:**

1. **Top bar (56px):** the wordmark; a search button that appears once the hero search scrolls away; language and display; the bell; the avatar (always right-most).
2. **Hero:**
   - `Namaste, Priya` at `--type-hero`;
   - one quiet line underneath ("Work near Madhapur, picked for your skills");
   - the Opportunities / Businesses switch, as icon tabs;
   - the **search pill**: search icon, a field, the mic, and a round brand search button.
3. **Trade rail:** icon tiles in a snap-scrolling lane, ending with an "All" tile that opens every category in a sheet. Tapping a tile filters in place, and the list below reflows.
4. **Quick chips (sticky under the top bar):**
   - `⚲ Filters (n)`;
   - `⌖ Madhapur · 25 km`, which opens the distance popover;
   - `Near me`, `Today`, `₹20k+/month`, `Verified`, `Remote`, `Night shift`.
   - Each chip is a one-tap toggle with its icon. A selected chip shows a check.
5. **Themed rows (curated mode):**
   - For you, Near you (N km), one row per category you work in, New today, Starting this week, Top paying, From verified businesses, From your community, Projects for professionals, Work from home.
   - Each row has an icon, a title, a count and "See all".
   - Cards snap, and the next card peeks.
6. **Filtered mode** (any filter or sort): a result count heading (`24 opportunities near Madhapur`), the Sort menu, removable applied chips, "Save this search", then one flat ranked grid.
7. **Floating command hub** (bottom, in the thumb zone):
   - a pill with Discover, Businesses, **Post** (a raised ink circle), Activity and Profile;
   - an icon and a word on each;
   - it condenses to icons only while scrolling down and expands again on scroll up.

**Desktop (≥900):**

- **Top bar (64px, full width):**
  - the wordmark over the rail;
  - the **floating search pill** in the centre, shown once the hero search scrolls away, and always on other screens;
  - the Hire / Find work menus;
  - language and display, the bell and the avatar.
- **Side rail (232px):**
  - an ink-filled **Post** button first (brand stays for the screen's own primary action);
  - then Discover, Businesses, Activity and Profile as 44px rows with icon and label;
  - the current page gets a selected fill and a brand icon;
  - the "Vyapar · ForKhatri" host qualifier sits quietly at the bottom.
- **Content:** full width up to 1320px. There is no sidebar. The hero search is the Airbnb-style wide pill: what (field and mic), where (distance), and a Search button. Rows show three to four cards with ‹ › arrows. **Filters** opens a 420px right drawer with the same sections as the phone sheet.
- **Condensed header:** after 8px of scroll the top bar gains its hairline and `--shadow-raise`. After the hero search leaves the viewport, the compact search pill fades and slides into the top bar (180ms), so search is never more than one click away.

## 12. Motion

| Moment | Spec | Meaning |
|---|---|---|
| Press (buttons, chips, tiles, cards) | `transform: scale(.96)` (cards .98). Release spring `cubic-bezier(.34,1.56,.64,1)` over 220ms | "I felt your tap" on a slow phone, before the network answers |
| Card hover | translateY(−2px), shadow 1 to 2, 200ms `--ease-out` | "This is clickable" |
| Tile select | tile scale 1 to .94 to 1 (spring, stiffness 500, damping 26); check badge pops in | The filter is applied |
| Results reflow | cards fade and rise 8px, 30ms stagger, capped at 8 (spring 420/34) | The list changed because of your tap |
| Row arrows | smooth scroll by 90% of the strip, with snap alignment | Paging, not free-sliding |
| Sheet / drawer | from the bottom (phone) or the right (desktop), spring 380/36. The scrim fades over 180ms | It comes from where your thumb or pointer is |
| Header condense | top-bar shadow and hairline 160ms; search pill opacity and translateY(−6px) to 0 over 180ms | Search moved up, it did not vanish |
| Hub condense | labels fade and collapse over 200ms; the pill width animates with `motion` layout | More room for content while reading |
| Route change | the existing `<ViewTransition>` forward/back slide, plus a card-title-to-detail-title morph (`Morph`) | You went *into* this card |
| Loading | skeletons of the real card anatomy (tile, two lines, pay bar) pulse in opacity, never a travelling gradient | Content is coming, and the layout will not jump |

`prefers-reduced-motion: reduce` removes all transforms, springs, staggers and slides. Colour and opacity changes stay, so state changes remain visible.

## 13. Shared components (applied everywhere through `language-2026.css`)

| Component | 2026 language |
|---|---|
| `.vy-btn` | Pill; min height 2.75rem (primary 3rem); weight 650; springy press. Primary: brand fill, `--on-brand`. Secondary: white surface, default border, `--shadow-card` on hover. Ghost: no border; on hover, the selected fill. |
| `.vy-chip` | Pill; min height 2.25rem (2.5rem on touch); an icon slot; selected shows the neutral ink ring and fill (the palette rule) |
| `.vy-card` | Radius 22; hairline; `--shadow-card`; interactive cards lift on hover |
| `.vy-sheet` | Radius 28 top; grab handle; `--shadow-float`; spring in. On desktop it becomes a right drawer. |
| `.vy-segmented` / tabs | Pill track on `--surface-sunken`. The selected segment is a raised white pill with `--shadow-card` (Airbnb and iOS segmented style). |
| `.vy-input` / `.vy-select` / `.vy-textarea` | White surface; default border; radius 16; min height 3rem; 1rem text (so iOS does not zoom); focus is a 2px brand ring with a 3px soft halo in `--brand-soft`, which is a flat colour, not a glow |
| `.vy-badge` | Radius 8, weight 650, with an icon slot. Verified is green on its tint, with a shield icon. |
| `.vy-empty` | Tinted icon tile, bold title, one line, one action |
| `.vy-skeleton` | Opacity pulse on `--surface-sunken` |

The composer, detail, contracts, applicants, packages and every other screen pick these up without markup changes.

## 14. Checklist for the critique pass

- Budget Android at 390px:
  - the trade rail, chips and cards are readable at arm's length;
  - no target is under 44px;
  - the mic is in the search;
  - icons carry words.
- Hindi and Telugu: tiles, chips, row titles and card lines wrap and do not clip. Verified in hi and te screenshots.
- Women seeking safe work: the one trust badge on every card; "Verified" is one tap away as a quick chip; the seeker-protection notice on the detail page is unchanged.
- Fresher: the "Fresher" experience filter is in the sheet; "For you" works from first-run skills.
- Kirana owner posting: **Post** is the one filled button in the hub and in the rail.
- CA or developer on desktop: 4-column results; the top-bar search pill is always one click away; Hire / Find work menus; keyboard focus rings everywhere.
- Older users: Text size A+ and A++, High contrast, the OS font size (everything in rem), and reduced motion.

## 15. Decisions added during the build (critique and owner, 2026-09-29)

- **First card above the fold (critique W1).** At 360×740 the first card's title and pay sit above the hub. The phone hero is compact: no subtitle, a 1.625rem greeting, short tab names ("Businesses"), and a short placeholder ("Search jobs or skills"). The trade rail is one lane of 52px tiles. Measured: pay bottom 620px (en) and 641px (hi), with the hub top at 650px.
- **Control edges at 3:1 (critique P1/D2).**
  - New token `--border-control` (an alias of `--border-strong`, at least 3.55:1 on every surface in both themes).
  - It is used on inputs, selects, secondary buttons, chips, switches, the search pills and row arrows.
  - `check-contrast.mjs` checks it as UI on all six surfaces.
- **Monthly pay (critique W3 and the glossary).** A yearly "₹X–Y LPA" is shown as "₹A–B a month", rounded to ₹1,000, with "₹X–Y lakh a year" as the quiet second line. "LPA" never reaches the screen on a card.
- **No sidebar (critique W4).** The desktop filter sidebar is gone. FE2's panel lives in the sheet or drawer.
- **Trade names are never cut.** Tile labels wrap to two lines with no ellipsis, and tile columns are in rem, so Text size A++ never collides them.
- **Server row titles.** Rows render the server-translated `title` when present (imp-backend-b L13) and fall back to `explore.rows.<title_key>`.
- **Sparse home.** With three rows or fewer, or when the profile has no skills, the rows end in a "Want to see more work here?" block. It offers **Add my skills** (only when the member has none) and **Post what you need**. The trade tiles above stay as the way to browse. The home never leaves a blank gap.
- **Error state.** If the feed, or the first-run check it waits on, fails to load, Discover shows "Couldn't load opportunities" with **Try again**, never endless skeletons.
- **Dialogs** take focus on the sheet itself (screen readers land inside), with no focus ring drawn on touch.
