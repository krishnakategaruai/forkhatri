# Critique: UX, design language and accessibility across ForKhatri

Lens: cross-cutting. Written 2026-10-06. Read-only review.

**Evidence base.** I read the parent UX/UI docs, the module design notes and the Milavn UI review. I then used the real screens, signed in as Asha through the hub's "act as" link. I saw the hub, Milavn, Mangalya, Vyapar and Counsel at 390 px and 1280 px, in light and dark, mostly in Telugu. I ran small scripts for tap-target size, font size, letter-spacing and contrast. I did not submit any form. Screenshots are in the session scratchpad (`...\scratchpad\ux-01...` to `ux-25...`), cited below as `ux-NN`.

**Source note.** Items marked "via Google News" were found through Google News RSS searches. I give publisher, title and date but could not obtain the publishers' direct URLs, so treat them as unverified until opened.

**Limits, stated plainly.**
- The services run in development mode, so payload sizes are inflated and are only indicative.
- Hindi was inspected only in Milavn settings. Telugu was inspected widely.
- Not reviewed: admin console, Insights, event pages, Mangalya profile, chat and wedding screens, and payments.
- My browser tool blocked typing a public tunnel URL, so I used localhost for modules.
- Search quotas ran out mid-research. Some legal items rest on news reports rather than the primary text and are marked.

## 1. Understanding of the vision (please correct me)

ForKhatri is one umbrella web app, with one sign-in and one shell, mobile-first and in English, Hindi and Telugu. The hub is a calm, minimal launcher. Each module should feel like part of the same product. Mangalya is "calm royal" in kumkum and turmeric. Vyapar is premium. Milavn and Counsel are modern and warm. The owner wants a "2040-modern" feel, voice as guided conversation, no hardcoded strings, accurate Telugu and Hindi, and elders and low-literacy members served. The bell sits left of the avatar, and every module offers a way back to the hub.

## 2. Critiques, ranked

### Critical

**1. Five products, not one: the Tata Neu failure the hub's own research warns about.**
- Evidence: five palettes (`ux-03` near-black with amber, `ux-04` navy with amber, `ux-10` maroon with gold, `ux-14` slate with periwinkle, `ux-13` charcoal with teal).
  - Five type systems: Geist+Sora, Anek+Fraunces (twice), Instrument+Noto, Anek.
  - Navigation: orb (hub), five-tab bar (Milavn), five-tab bar with a centre "+" (Vyapar), four-tab bar (Counsel), and a hamburger holding 8 destinations (Mangalya).
  - Token names differ (`--accent` vs `--accent-primary`, `--surface` vs `--surface-base`). Mangalya's CSS has 206 distinct hex values over about 13,000 lines of stacked skins.
  - `platform/forkhatri-web/DESIGN-NOTES.md` quotes the Tata Neu review, "different logo styles, colors, fonts and even navigation styles… a very broken experience". I checked it: [uxhack](https://uxhack.co/blog/tata-neu-ux-first-impression/), 4 Apr 2022, updated 31 Aug 2026.
- Why it matters: members move between modules daily. Each switch relearns the controls, which is hardest for elders.
- Do: define a thin shell contract: header (back, bell, avatar), settings, tokens, type scale, tap size, focus ring, 404 and error pages. Let modules re-skin only accent, surface and display face. Mangalya's kumkum and turmeric stay as a skin (owner decision). **L**

**2. The notification bell is not one system, and the hub's is a stub.**
- Evidence: the hub bell shows a hard-coded "You're all caught up" (`Entrance.tsx` lines 414-421; screenshot `ux-24`). Milavn shows 6 unread and Vyapar 1. Mangalya has no bell and no notifications route at all. Milavn calls it "Alerts" and the others call it "Notifications". UX05 promised shared notifications.
- Why it matters: a mother waiting on a match request never sees it from the hub.
- Do: one inbox contract (module, type, deep link, read state), one bell component, and counts per module. Follow [NN/g push guidance](https://www.nngroup.com/articles/push-notification/): bundle, explain what you will send, and put preferences in-app. **M**

**3. Accessibility is unmanaged, and Indian law now treats digital access as a right.**
- Law: the Supreme Court held in April 2025 that digital access is part of Article 21 and directed accessible digital KYC (Live Law, 29 Apr 2025; SCC Online, 1 May 2025; found via Google News, primary judgment text not read, so check). RPwD Act 2016 and GIGW also apply.
- Evidence in the product:
  - A skip link exists only on the hub.
  - Tap targets under 44 px: Counsel's bell and saved icons are 40 px, Mangalya's menu is 40 px, and Milavn's tabs are 40 px (from the Milavn review, not re-measured).
  - Milavn light theme puts amber text on cream at 2.3:1 to 3.2:1 (greeting name "Asha", the location line, "See all"), measured on the page at 390 px.
  - No text-size control on the hub, Milavn or Counsel.
- Standards: WCAG 2.2 AA minimum target is 24 px ([W3C 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)). Material and Apple use 44 to 48. Typing an SMS code is only compliant if paste or autofill works ([W3C 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html)). The hub and Mangalya set `one-time-code`, which is good.
- Do: make WCAG 2.2 AA a release gate, with axe or Lighthouse in CI and a TalkBack pass in Telugu and Hindi. Publish an accessibility statement. **M**

**4. Latin typography rules are applied to Telugu and Hindi.**
- Evidence:
  - Milavn adds 0.88 px letter-spacing and uppercase to Telugu eyebrows ("సమాజం · AMEERPET", `ux-08`).
  - Mangalya applies -0.56 px tracking at line-height 1.0 to the 56 px Telugu greeting, and -0.18 px to Telugu headings.
  - The hub's Telugu helper text is 12 to 13 px.
  - Counsel truncates Telugu dropdown values ("భారతదేశం అంత…", `ux-25`).
  - Mangalya loads six font families (nine font files) for three scripts.
- Why it matters: Indic conjuncts break or look spaced out. Tracking and uppercase are meaningless in these scripts. This breaks the owner's rule that Telugu and Hindi be accurate and respectful.
- Do: add script-aware tokens under `:lang(te)` and `:lang(hi)`: letter-spacing 0, no uppercase, body at least 16 px and small text at least 14 px, line-height at least 1.6. Have native readers sign off. **S**

### High

**5. Terminology and strings drift between modules.**
- Evidence:
  - Hindi is spelled both "हिंदी" and "हिन्दी" (the hub says one, Milavn the other).
  - Telugu "Discover" is అన్వేషించు in Mangalya, అన్వేషణ and వెతుకు in Vyapar, and వెతకండి in Counsel, where a "వెతుకు" button sits on the same page.
  - Milavn's Telugu home shows an English sentence ("It's a quiet week…", from the service key `digest.quiet`).
  - The hub writes Mangalya in Latin while Mangalya's own header writes మంగళ్య.
  - No app has a `not-found.tsx` or `error.tsx`. Vyapar's 404 is a black English default page inside its themed chrome (`ux-15`).
- Do: one shared glossary file with a lint, and one localised 404 and error screen. **S**

**6. Known context is re-asked in Vyapar's first run.**
- Evidence: step 1 of 5 asks "What should we call you?" and "Which language can you read well?" (`ux-14`). The account already has both. This breaks the owner's "never re-ask known context" rule. Language does carry across modules (I changed it in Milavn and every module followed), which is good.
- Do: prefill and skip. Show the remaining steps only after a first useful result. **S**

**7. Cold start: empty screens and dead ends.**
- Evidence: Milavn's feed shows two stacked "quiet" messages, and the floating "Make something happen" button covers the empty-state text (`ux-04`). The Milavn review (P0 #1, #3) says the same. [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/) (19 Sep 2021): an empty state should give status, teach, and offer a direct path to the key task.
- Why it matters: a community app with few members is empty most of the time.
- Do: seed hub-level content from Samaj heads (announcements, verified events). Give each empty state one action. **M**

**8. Mangalya's mobile navigation hides everything, and its feed is heavy.**
- Evidence: eight destinations sit inside a hamburger drawer (`ux-11`). The discover wall is about 1.7 screens per profile, a full-bleed close-up face (`ux-12`).
- Why it matters: [NN/g's study of 123 people aged 65+](https://www.nngroup.com/articles/usability-for-senior-citizens/) found small targets and inflexible interfaces were the main problems. Parents are Mangalya's key users.
- Do: a four-tab bottom bar (Home, Discover, Circle, Messages) plus "More". Cap profile card height. **M**

**9. Performance on cheap phones is unbudgeted, and nothing installs or works offline.**
- Evidence:
  - No web app manifest or service worker exists in any app.
  - Mangalya's home moved about 740 KB with about 1 MB of JavaScript over 74 requests (dev mode).
  - Mangalya ships 13 MB of face models and 5 MB of art in `public/`.
  - There is a hub splash, and a full-screen "LOADING…" illustration on each Mangalya cold load (`ux-09`).
  - Phone prices rose 16% in H1 2026 and demand for 4G phones is reviving (Economic Times, 29 Sep 2026; Business Standard, 29 Sep 2026, both via Google News). Android is mostly recent (16 is 38.8%, [StatCounter](https://gs.statcounter.com/os-version-market-share/android/mobile-tablet/india), Sep 2026), so the weakness is RAM and CPU, not the OS.
  - Good targets are LCP 2.5 s and INP 200 ms at the 75th percentile ([web.dev](https://web.dev/articles/vitals)).
- Do: a written budget per module (JS, fonts, LCP on a Moto G-class phone at Slow 4G). Run Lighthouse CI on production builds. Add a manifest and a shell-caching service worker. Lazy-load face-api. **M/L**

**10. Appearance and text size are per module, not per member.**
- Evidence: theme and text-size keys are stored separately per module and origin (`mangaly.theme`, `vyapar.textSize`, `counsel.theme`). Only Vyapar and Mangalya offer text size.
- Why it matters: an elder who sets "Largest" in Mangalya meets small text in Milavn.
- Do: store language, theme and text size on the identity record and apply them in the shell. **S/M**

**11. Voice is built four times, with no shared fallback.**
- Evidence: separate Web Speech wrappers in the hub (`lib/hooks.ts`), Vyapar (`voice/speech.ts`), Milavn (`AskBar.tsx`) and Mangalya (`VoiceInput.tsx`). The Web Speech API sends audio to the browser vendor's servers ([Wikipedia, Web Speech API](https://en.wikipedia.org/wiki/Web_Speech_API); support varies by browser). Telugu accuracy is unverified. I found no WebOTP use, which would remove OTP typing on Android Chrome (SMS must end in `@domain #code`, [Chrome docs](https://developer.chrome.com/docs/identity/web-apis/web-otp)).
- Do: one shared voice service with capability detection, a typed fallback and a privacy line. Test Telugu and Hindi accuracy before promising voice. **M**

### Medium

**12. Trust cues are inconsistent and sometimes excessive.**
- Evidence: one Counsel provider card carries five badge chips before the price (`ux-25`). The other modules use different words and icons: "Business verified", "Identity verified", "ForKhatri Verified" and "photos verified".
- Why it matters: government advisories on fake matrimonial profiles are rising (India Today, 8 Jul 2026; Indian Express, 17 Jul 2026, via Google News). Members need one clear ladder.
- Do: a single platform verification ladder of three levels, one icon, one "what this means" sheet, and one primary badge per card. **M**

**13. Dark-pattern and engagement exposure.**
- Evidence: India's 2023 guidelines name 13 patterns. The June 2025 advisory told platforms to self-audit, and 26 declared compliance by Nov 2025 (The Hindu, 7 Jun 2025; Telangana Today, 20 Nov 2025). I could not fetch the guideline text, so the 13-pattern list is unverified. Mangalya's home shows "0 of 3 requests used today" next to a Gold upsell. Count badges sit on the bell in Milavn and Vyapar.
- This is a risk, not a finding of breach.
- Do: a dark-pattern checklist in design review (no timers, a skip as prominent as accept, one-tap cancel). Add "you're done for today" states. Dating-app burnout is a mainstream story (Medill, 23 Dec 2025; Global Dating Insights, 29 Jan 2026), which favours Mangalya's calm, family-led model. **S**

**14. Devotional imagery assumes one audience.**
- Evidence: Mangalya's splash and icon use a Rama and Sita wedding illustration (`ux-09`). The hub splash is Sahasrarjun (`ux-22`). Khatris are mostly Hindu, with a significant Sikh minority and a Muslim one; all ten Sikh Gurus were Khatri ([Wikipedia, Khatri](https://en.wikipedia.org/wiki/Khatri)). Seed data includes Punjabi Khatris.
- I respect the owner decision on the Kartavirya Arjuna emblem. I could not verify who in the community venerates which deity, so the owner may know this better.
- Do: keep the emblem on the hub, but make Mangalya's illustration a one-time first-visit moment and offer a neutral skin. **S**

**15. Duplicate and cluttered controls.**
- Evidence:
  - Milavn lists Profile and Calendar twice, and People in both header and sidebar.
  - Vyapar's desktop view has two search bars (`ux-17`).
  - Vyapar's header has four icons.
  - The entrance shows a hub-shaped skeleton before the sign-in card (`ux-01`).
  - The language switcher shows "EN / हि / తె" in place of full words (`ux-02`).
- Do: one control per job, and full language names. **S**

**16. Mangalya's screenshot guard hurts honest users.**
- Evidence: `ScreenGuard.tsx` covers the page whenever the tab is hidden. Its own comment says a web page cannot stop OS capture.
- Why it matters: someone who switches to WhatsApp to ask a relative returns to a blank screen.
- Do: cover only photos, show a friendly message, and measure complaints. Treat the guard as a deterrent, not a guarantee. **S**

**17. No way back to the hub from Counsel's header.**
- Evidence: Counsel's header links go only to its own pages (`ux-13`). UX04 says every module surface offers a way back.
- Do: add "ForKhatri" to the shared shell header. **S**

## 3. New in the world

- [NN/g on Apple's Liquid Glass](https://www.nngroup.com/articles/liquid-glass/) (10 Oct 2025): translucency lowers contrast, tap targets shrank, and "motion for motion's sake" harms. Apply this before adding more glow or glass to the "2040" direction.
- India's dark-pattern self-audit regime (2025): published self-audits of 18 e-commerce and quick-commerce platforms (MediaNama, 21 Nov 2025).
- DPDP Rules 2025 were notified in Nov 2025, with most duties phased over about 18 months (India Briefing, 11 May 2026). Plan multilingual notices now.
- Matrimonial fraud advisories and AI deepfakes (2026, see item 12).
- Dating-app burnout and renewed matchmaker interest (see item 13).
- WhatsApp is shifting: Meta named Kunal Shah to lead it in Jun 2026 and moved Business pricing to tokens in Jul 2026 (Moneycontrol, 2 Jul 2026). India told WhatsApp to pause usernames (Reuters, 2 Jul 2026). Treat WhatsApp as a possible notification channel, with cost and policy risk.
- WebOTP (above) and WCAG 2.2's accessible-authentication rule.
- Rising handset prices keep low-end phones in use longer (item 9).

## 4. Rethink

1. **A monochrome hub over colourful modules.**
   - For: a calm launcher avoids PhonePe-style clutter.
   - Against: the modules then feel like separate apps (item 1). Consider a shared shell with per-module skins.
2. **Dark-first.**
   - For: modern look and battery savings on AMOLED.
   - Against: elders, outdoor use and print-like reading favour light. Milavn and Mangalya default to "System", so the hub's dark-first stance is not carried through. Pick one default and sync it.
3. **Web app, not installable.**
   - For: no store friction and one codebase.
   - Against: no manifest means no install, no offline shell and no reliable push on cheap phones. A PWA keeps "web" and fixes most of this.
4. **Voice as the answer for low literacy.**
   - For: [Microsoft Research's text-free UI work](https://en.wikipedia.org/wiki/Indrani_Medhi_Thies) is the standard reference. I could not fetch its figures, so they are unverified.
   - Against: browser voice is uneven in Telugu and sends audio to servers. Pictures, icons and plain labels may serve more people sooner.
5. **A bell per module versus WhatsApp-first.**
   - For: members already live in WhatsApp.
   - Against: cost, policy change, and consent under the DPDP rules. An in-app inbox is still needed as the record.

## 5. Do not change

- Conversational sign-in: one question at a time, `one-time-code` set, "Your number is never shown to other members" (`ux-02`).
- Language stored per member and carried across modules.
- The hub's grouped list, "Coming to ForKhatri" collapse, skip link and live regions (`ux-03`).
- Mangalya's kumkum and turmeric, serif display type and calm tone (`ux-10`, `ux-20`).
- Vyapar's Telugu screens are clean and well set (`ux-16`).
- Milavn's one-line create flow and its honest trust copy.
- Counsel's quiet-luxury look.
- Reduced-motion handling in all five apps, and the splash that is shown once per session.
- Anek as the multi-script family in three modules (the fix is consistency, not replacement).
- The development "act as" switcher that keeps testing off the OTP screens.
