---
doc: product-guardrails-and-decision-register
status: Sealed
approver: Product Manager (krishna kategaru)
updated: 2026-09-13
scope: ForKhatri (all modules)
---

# Product Guardrails & Decision Register

This document sits **above** every module's `01-business-requirements.md` in the pipeline. It exists because passing tests and internally-consistent requirements prove a specification works — they do not prove it is still the *right* product. Detailed requirements work can silently drift from the original product thesis one reasonable-looking decision at a time, even while every individual pipeline artifact passes its own review.

**Every pipeline agent (Step 0 through Step 14, every module) must treat this document as required, non-negotiable context.** No BR, FR, UX, UI, test scenario, architecture decision, or implementation may contradict a row in this register without an explicit, recorded decision from the Product Manager that amends this document itself.

The chain is:

> **Product Thesis → Guardrails (this document) → BRD → FR → UX → UI → Tests → Tech Reqs → Implementation**

and it must never become "FR → accidentally redefine product." Each stage **preserves** the thesis; it does not reinterpret it.

## Revision history
| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial creation, following the Product Manager's Step 6 review of MOD02 Milavn, which found the detailed requirements work product-aligned but flagged the risk of specification effort outpacing product-thesis preservation. | First formal Product Guardrails pass for the project. |
| 2026-09-14 | Post-seal correction: added "Platform guardrails (all modules)" and checkpoint question 9. Not re-sealed; awaits the Product Manager's review. | Product owner's instruction of 2026-09-14: ForKhatri is one app with one sign-in and one member identity, and the member chooses which module to enter. See `docs/ParentApp/00c-identity-and-entrance-decisions.md`. |

## Platform guardrails (all modules)

| Decision | Rule |
|---|---|
| One ForKhatri identity | A member has one ForKhatri account and one `member_id`. No module creates its own accounts, logins, sign-up, OTP or password flows. |
| Entrance and hub are the front door | Members sign in at the ForKhatri entrance and enter modules from the ForKhatri hub; every module surface offers a way back to the hub. |
| Trust is contextual | The platform holds only Level 1/2 trust (verified phone/email, later identity document). Each module's Level-3 trust is its own and is never shared with or read by another module. |
| Tiers and roles are module-owned | Tiers (free, premium) and roles (organiser, moderator, Home Circle member) are module data in module databases, never platform session data. Every member may enter every available module. |
| Hub privacy | The hub never surfaces sensitive module data (for example Mangaly profile, match or family details) without an explicit, privacy-reviewed contract. |
| Credentials never readable by page JavaScript | The browser's only credential is an HttpOnly session cookie; no token in `localStorage`, `sessionStorage`, URLs or response bodies. |

## Core guardrails (Milavn, and the pattern to replicate per module)

| Decision | Rule |
|---|---|
| Product identity | Real-world participation network, not a social feed or dating app |
| Primary loop | Discover → Participate → Connect → Contribute |
| Home experience | "Around You" (what's happening near me), not "which group should I join" |
| Primary success metric | Meaningful participation (RSVP → attendance), not views/impressions |
| Ranking philosophy | Relevance + locality + trust > popularity — must never let a popularity-compounding loop dominate |
| Social philosophy | Contextual to real activity, not engagement-maximizing (no likes/streaks/vanity metrics for their own sake) |
| Messaging | Structured, activity-scoped coordination — not a WhatsApp replacement |
| Dating/romantic framing | Explicitly not Milavn's purpose — no swipe/match mechanics, no romantic/matrimonial copy |
| Explainability | Every ranked/recommended item carries a real, human-legible "why this?" reason — a standing requirement, not a nice-to-have, because it keeps any future AI/recommendation layer accountable |
| External events | Deferred (future) — architect so it can be added later, do not build an aggregation platform during V1 |
| Ticketing / commerce | Deferred (future) |
| AI | Friction reduction, not a product replacement — architecture should be AI-friendly, but no AI planner should be built before basic participation works |
| Revenue | Monetize real economic value created, not belonging/community itself |
| Privacy | Location and attendance privacy by default; user controls precision |
| Trust | Reputation is earned, never purchasable — never pay-to-win, never a public numeric score |
| Moderation | No automated punitive action from a single signal (e.g. feedback or no-shows) alone |
| Architecture | Generic, reusable primitives; product-specific behavior is configuration on top, not forked code |
| Shared platform capabilities | When a capability (e.g. admin/moderation tooling) will be needed by more than one module, build it once as a shared platform capability rather than letting the first module that needs it build a bespoke version |
| Launch sequencing | Local activity density before geographic expansion |
| Organizer supply | Organizer activation is a first-class success metric, not an afterthought — no organizers means no activities means no discovery means no participation |
| Circle formation | Circles emerge from repeated real participation ("participate → repeat → recognize pattern → suggest circle"), not from cold group-creation |
| ForIndia / broader scale-out | Correct direction conceptually, explicitly not being built now |

## Standing PM checkpoint (ask after every pipeline stage, every module)

1. Does this still solve the original user problem?
2. Does it strengthen Discover → Participate → Connect → Contribute (or the equivalent core loop for the module in question)?
3. Is this MVP, future, or unnecessary?
4. Does it preserve trust/privacy?
5. Does it create real-world value?
6. Does it help the broader ForKhatri ecosystem?
7. Can a solo founder realistically build and operate it?
8. Are we solving a real user problem, or merely building an impressive feature?
9. Does this keep one ForKhatri identity and entrance?

## Two tracks that must run in parallel, not sequentially

- **Product certainty** — BRD → UX → FR → UI → Tests (this pipeline).
- **Market certainty** — real users, real organizers, real activities, real participation, real feedback and metrics.

Neither track substitutes for the other. Perfecting the specification is not a stand-in for validating the actual behaviour with real humans, and the pipeline's thoroughness should never be read as evidence the product itself is validated.

## Standing biggest business risks (tracked here so they aren't lost inside requirements detail)

- **Local activity density**: a technically perfect app with "no activities nearby" on first open is dead for that user. Density must be part of the product plan, not left to marketing.
- **Organizer supply**: participants are demand, organizers are supply — without organizer activation there is no content to discover.
