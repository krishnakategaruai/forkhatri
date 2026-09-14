---
module: MOD02
step: design-direction
status: Ready for Review
approver: Product Owner
updated: 2026-09-14
---

# Milavn — Design Direction 2030

*Why this exists.* The first implementation pass was functionally complete but visually read as "well-made 2019 Material". The owner's goal is sharper: be better than Partiful, Luma and Meetup on screen today, and still feel modern in 2030. This document is the researched answer to "what would that take", and the brief every later UI change is held to.

## 1. What the source documents already demand

| Source | Demand | Design consequence |
|---|---|---|
| Thesis §67 | "Open app → immediately understand what's around → tap → understand → join → show up → meet → come back" | The first screen answers the question in one glance; everything else is one tap away. |
| Thesis §68–§69 | Not a portal / Facebook / WhatsApp / dating / directory. Feel **local + useful + trusted + alive + simple**; personality **modern, warm, trustworthy, local, energetic, minimal, progressive** | Photography and place names carry warmth and locality; no likes, streams or counters that manufacture urgency. |
| Thesis §30–§32, §40 | Creation is four questions; **natural-language creation** and **voice** are the intended direction; prefer cards, visual discovery, one-tap actions, natural language, progressive disclosure | Ask-first surfaces (search and create) with the interpretation shown back; voice as a first-class input. |
| Thesis §33, §84 #9, Brand §14 | AI "removes friction" but is never a shortcut around permissions; **Understand → Recommend → Authorize → Execute → Record → Confirm** | The assistant proposes, the person confirms; nothing is created or joined silently. |
| Thesis §19–§21, §84 #7, Brand §9 | Trust visible, reputation earned, privacy by default | Badges always paired with text; attendance private; locality never an address. |
| Thesis §43, §42 | Share via WhatsApp, Instagram, SMS, email, QR, link; public pages without install | Share must produce something *worth forwarding*: a poster image, not just a URL. |
| Brand §12–§13 | Deep navy, warm off-white, saffron, controlled green; **multiple Indian languages, text and voice** | Palette stays; scripts and voice are first-class, not fallbacks. |

## 2. What the best comparable products do on screen (verified)

- **Partiful** — event pages are colourful and animated (theme + effect pickers), display type at ~40px, gradient washes, emoji-led RSVP; explicitly playful. ([Product Hunt](https://www.producthunt.com/products/partiful), [Refero style sheet](https://styles.refero.design/style/6db1057d-3457-4173-9184-df160415f060), [Aither case study](https://aither.co/projects/partiful))
- **Luma** — square rounded cover images, 40+ themes as page backdrops, calendar-first, minimal chrome. ([Luma cover guidance](https://help.luma.com/p/event-cover-images), [themes](https://help.luma.com/p/event-themes-and-customization))
- **Meetup 2025** — real-people photography, brighter palette, colour-coded icons, bolder CTAs, subtle gradients suggesting movement; attendee counts and ratings as credibility cues. ([Meetup blog](https://www.meetup.com/blog/new-design-2025/), [BusinessWire](https://www.businesswire.com/news/home/20250930663024/en))
- **Airbnb 2025** — tactile 3D "Lava" icons; flat minimalism giving way to depth and character. ([Medium deep-dive](https://medium.com/@waldobear002/airbnbs-new-lava-icon-format-a-technical-deep-dive-b2604626c7e0), [Bloomberg](https://www.bloomberg.com/news/articles/2025-06-13/apple-airbnb-ditch-flat-app-icons-for-new-3d-ui-design))
- **Strava** — activity becomes identity; maps and heatmaps make the community's real movement visible. ([Strava heatmaps](https://support.strava.com/en-us/articles/16046277-a-guide-to-strava-heatmaps))
- **2026 → 2030 direction** — glass as a selective material (iOS 26 "Liquid Glass"), bento hierarchies, expressive type, and then agentic / ambient / multimodal interfaces where forms give way to conversational input with review-and-confirm for anything irreversible. ([Rajesh R Nair](https://rajeshrnair.com/blog/design/ui-ux/ui-design-trends-2026-bento-grids-glassmorphism.html), [Midrocket](https://midrocket.com/en/guides/ui-design-trends-2026/), [Medium: adaptive, agentic, ambient](https://medium.com/@springmusk/the-future-of-ui-design-past-2026-adaptive-agentic-and-ambient-c1b652d5e941))
- **India specifics** — ~70% of users prefer regional-language content; voice-first flows in regional languages are growing fast; ~40% of phones have ≤2 GB RAM; WhatsApp-based journeys are the norm. ([ProCreator](https://procreator.design/blog/indian-startups-get-right-about-product-ux/), [CreateBytes 2026 guide](https://createbytes.com/insights/ux-design-mobile-apps-india), [HNK Media](https://hnkmedia.com/blogs/ui-ux-design-trends-india-2026/))

## 3. Where Milavn can be *better*, not just equal

None of the comparables combine all of these. Each is a thing Milavn already has the data or the doctrine for:

1. **Ask-first, in three scripts, by voice.** "इस वीकेंड मेरे पास बैडमिंटन" spoken or typed becomes filters you can see and correct. Partiful and Luma are still browse-and-filter products.
2. **Trust you can see, calm by design.** Verified badges with words, reputation as earned labels, attendance private, "be the first" instead of "0 going", no infinite feed — groups end. Meetup shows star ratings; we deliberately don't.
3. **Living posters.** The photo is the card; the page is tinted by the cover; the *share* is a poster image sized for WhatsApp status, generated on the device.
4. **Progressive complexity.** A participant sees four things; organizers unlock tools in place. Nothing "admin" leaks into the participant's screen.
5. **Light on the device.** No third-party image services, on-device QR, lazy images, skeletons; works on a mid-range phone on 3G.

## 4. The visual system (the "poster system")

- **Surfaces**: warm paper (`#fbf8f3`) by default with slow-drifting ambient light; dark navy only when the person chooses it. Navy is the *primary action* colour (buttons, active pills), saffron the *accent* (dates, sparks, highlights), one hue per category as a thin accent line. Lesson from v1: navy-as-background with saffron on top reads muddy; glass (blur + hairline) for controls that float over content — nav, chips, action cards, pills; solid surfaces for reading.
- **Cards are posters**: 4:5 photograph, bottom scrim, host as a glass pill, trust badge with text, uppercase eyebrow (category), 1.5–2.4rem title, saffron date pill, place + distance, why-reason in warm amber, count pill. Compact 16:10 variant for rails inside pages.
- **Pages are tinted by their cover** (detail): the activity's own image, blurred, sits behind the page.
- **Type**: Fraunces (editorial, optical sizes) for greetings, headlines and poster titles in Latin; Anek for body and for Devanagari/Telugu; eyebrows in 0.12em uppercase.
- **Controls**: pill radius everywhere; primary = saffron gradient with glow; secondary = glass; disabled = quiet, never muddy.
- **Layout**: phone = floating glass tab bar + horizontal snap rails; desktop (≥ 900px) = rail navigation + bento grid (first card of the first group spans two columns) + two-column detail with sticky action card.
- **Motion**: spring for selection and confirmation, staggered rise for lists, hover lift on pointer devices, all disabled under reduced-motion.
- **Ask surfaces**: sparkle-marked pill with mic; interpretation echoed as chips; empty results widen themselves and say so.
- **Header order (owner's rule)**: People · Alerts bell (unread count) · Profile avatar, always last. No Alerts tab; four destinations with Profile last.
- **Profile**: about the person; all preferences behind one gear icon in a sheet.
- **Icons**: one consistent set (Lucide) for navigation and actions; emoji only as category glyphs on gem tiles.
- **Real time, on the device**: Live pulse while an activity is on, "in N min" up to 90 minutes before, a Happening-now rail, and "Use where I am" (one-shot position, request-scoped).

## 5. Social layer — decided with the owner (2026-09-14)

The owner asked why likes, ratings, stories, infinite scroll, exact locations and themes were excluded, and asked for a Snapchat-like messaging system. Resolution, item by item:

| Item | Decision | Why |
|---|---|---|
| Likes, follower counts | **Reactions instead** (emoji on messages, moments, announcements); no follower graph | Brand §15 rejects followers/likes/virality; reactions express warmth without a popularity score |
| Star ratings | **No public ratings**; private post-event feedback feeds earned labels | Thesis §20 |
| Story rings | **Circle moments ring** for 24 h, tied to a real activity; no personal broadcast channel | Thesis §3, Brand §15 |
| Infinite scroll | **Groups that end** on Home; "load more" only inside Search | Thesis §66 |
| Video | **Skipped for now** (owner); later: short clips as moments, tap to play, never autoplay | India device/data realities |
| Exact locations | **Locality only, for everyone** — never an exact private location or meeting-point pin (owner restated) | Thesis §21, FR038 |
| External AI models | **Later and asynchronous**, never in the request path | Thesis §102–§103, latency, privacy |
| Theme picker | **Curated**: 8–12 tested themes per activity that keep text legible | Partiful/Luma parity without illegible pages |

## 6. Messaging — "plan together", the Milavn way

- **Trust-scoped.** You can message people you already share an activity or a circle with, never strangers; blocks are honoured both ways. One definer helper (`can_message`) decides, and all conversation creation goes through it.
- **1:1 and groups**, real-time over WebSocket (messages, reactions, typing, presence), polling as fallback. Photos in chat. Unread counts on the Chats tab and the bell.
- **Reactions, not likes.** Six emoji, toggled by tapping a bubble.
- **Presence.** "Active now" from a 30-second heartbeat; "at the activity" from check-in.
- **Expressions, Snapchat-style, privacy-first.** The front camera is analysed *on the device* (MediaPipe face landmarker blendshapes → smile / laugh / surprised / wink / thinking / love / neutral); only that word is shared, shown as a mood badge on the person's avatar and next to their messages. Opt-in per chat with a visible camera indicator; a manual mood picker is always available.
- **Not a WhatsApp clone.** No broadcast lists, no forwarding chains, no read-receipt pressure, no "last seen at 03:12".

## 7. Still not doing

Follower counts, public star ratings, personal stories, infinite feeds, autoplay video, exact private locations, external model calls in the request path, free-form themes, and any read-receipt or "seen" mechanics designed to pressure a reply.

## 8. Revision history
| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-14 | Completed with the owner's social-layer decisions (§5–§7) and the messaging design (§6): trust-scoped chats, reactions instead of likes, on-device expressions, locality only. | Owner: "and yes, complete the design direction 2030… video you can skip for now… never expose exact private location, share locality" — krishna kategaru (autonomous). |
| 2026-09-14 | v2 after the first poster pass was still rejected: colour roles inverted (paper default, navy primary, saffron accent, per-category hues), Fraunces display type, designed pickers, voice input, digest, poster share. | Product-owner feedback ("colour combinations are the worst") — krishna kategaru (autonomous). |
| 2026-09-14 | Initial direction after the owner rejected the first visual pass ("very old styled screens… look at competitive apps… be better than them… 2030 people should still think our app is modernised"). Research: thesis §19–§21, §30–§33, §40–§43, §66–§71, §84; Brand §9, §12–§15; product and trend sources linked above. | Product-owner instruction — krishna kategaru (autonomous). |

## Approval
Product Owner — [ ] Approved — name, date
