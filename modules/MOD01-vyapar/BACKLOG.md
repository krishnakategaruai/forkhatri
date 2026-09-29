# Vyapar backlog

Last updated: 29 Sep 2026.

This file lists what is still open after the Upwork + WorkIndia competitive build of 28–29 Sep 2026. Everything else from that build is done and checked. Each item says why it is open and what would unblock it. The "Next builds" section is the recommended order from `VISION-2040.md`.

## Blocked outside the team

| # | Item | What's built on our side | What unblocks it |
|---|---|---|---|
| B1 | **Real payment payouts and money held until approval** | Contracts, milestones and funding through the dev sandbox. A ledger records held, released and refunded amounts. 14-day auto-release. The worker fee stays at 0. | Razorpay merchant account (BLOCKER-01). Then add a payout adapter behind the "released" ledger entry. |
| B2 | **AI with Claude** (drafting, reading photos, shortlist wording, proposal help) | Everything runs on the built-in rules today. The Claude code path is built and tested offline. Photo reading returns "not available" without it. | Set `ANTHROPIC_API_KEY` and `AI_PROVIDER=anthropic` in `vyapar-service/.env`, then re-run `scripts/check_ai.py` and try one real photo. |
| B3 | **Better Hindi/Telugu voice** | Voice input uses the browser's speech recognition in en-IN, hi-IN and te-IN, and every field is confirmed before it is saved. Published accuracy is weak for Telugu. | A Bhashini API key (free government service; apply now). |
| B4 | **Masked phone numbers** for calls before acceptance | Calling hours, daily cap, matching-only callers, "WhatsApp only" as the default, and honest disclosure text. | An Exotel- or Knowlarity-type virtual number vendor (logged in `09a-external-dependencies.md`). |
| B5 | **Push, SMS and WhatsApp notifications** | The in-app inbox, and outbound webhooks for host platforms. | The host platform's delivery channels, and a VAPID/SMS/WhatsApp Business setup. |
| B6 | **Real credential checks for professionals** | Credential references are checked against a development stand-in. | The platform Identity & Trust service's credential check (council registers such as ICAI, NMC, Bar Council, Council of Architecture, and DigiLocker). |
| B7 | **Cross-border client payments, advances on approved work, ONDC business matching** | Not started (from the Vision). | A licensed cross-border payment partner, a lending partner through MOD07, and ONDC network registration. |

## Needs a decision or review

| # | Item | Notes |
|---|---|---|
| D1 | Legal review before Vyapar ever takes a fee from workers | A fee on workers' earnings may make Vyapar an "aggregator" under the Code on Social Security (1–2% welfare levy). `CONTRACT_PLATFORM_FEE_BPS` stays at 0 until a lawyer checks it. |
| D2 | Wording of two privacy messages | `privacy:delete.blocked` and `privacy:delete.done` were written during the build. They need checking against the real deletion rules. |
| D4 | Purge leftover critique test rows | The Pass-5 critique closed or withdrew its test data through the product, but a direct database purge was not permitted. Closed posts, withdrawn requests, their notifications and some privacy acceptances remain in the dev DB. The old test posts "CHAT CHEF" and "Chat Bandar Cheft" are also still live. The purge needs owner approval. |
| D5 | Translate link on notes | `TranslateLink` is built and stays hidden until `NEXT_PUBLIC_TRANSLATE_URL_TEMPLATE` is set (placeholder in `.env.example`). Choose a translation service, for example Bhashini. |
| D3 | Where "Startup operations" sits in the skills list | It sits under Software & IT. Moving it also changes the onboarding skill suggestions. |

## Next builds (recommended order, from `VISION-2040.md`)

1. **Trust pack.** Needs no outside vendor.
   - A scam shield across every text a poster writes.
   - Honest terms, and a "paid on time" count confirmed by the person paid.
   - Close the loop: every applicant gets a status and a polite closure.
   - Human appeal for any restriction.
   - Council-verified professional badges.
   - **Profession-aware profiles:** lawyers (Bar Council Rule 36) and architects (Council of Architecture) get no promotion, no reviews and no ranking. This is a compliance risk today: advocates are listed with reviews and can be promoted.
2. **Voice first with Bhashini** (needs B3), plus voice answers to a poster's questions.
3. **A personal work agent** for workers, professionals and posters: plain-language standing instructions, with limits, a log and undo (needs B2).

## Housekeeping

- Repo-wide `npm run lint` still reports older `set-state-in-effect` errors in files outside this build. Every file touched in this build lints clean.
- The development data has about 20 active posts. Under the stricter Discover rules (each post in one row only, rows of fewer than 3 hidden), some people's home looks sparse until more real posts arrive. The sparse-home state is designed for this.
- Check scripts to re-run after any backend change (all on a private port):
  - `check_structured_hiring.py`
  - `check_backend_b.py`
  - `check_ai.py`
  - `check_contracts.py`
  - `check_admin_console.py`
  - web `scripts/check-i18n-keys.py`
  - web `scripts/check-contrast.mjs`
