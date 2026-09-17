---
project: ForKhatri
artifact: Parent Application Business Requirements
step: 1
status: Ready for Review
updated: 2026-09-14
---

# Parent Application Business Requirements

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-09-13 | Initial BR01–BR06 and product invariants. | First reviewable parent slice. |
| 2026-09-14 | BR02 and BR04 clarified for the real platform identity; BR07 (existing members keep access) and BR08 (contextual trust and module-owned tiers) added; invariants extended. | Product-owner instruction, 2026-09-14. See `00c-identity-and-entrance-decisions.md`. |

## BR01 — Unified application entry

ForKhatri shall provide one recognizable application entry point for members, regardless of which module they intend to use.

## BR02 — One member identity

The parent application shall use one canonical ForKhatri member identity and shall not require separate module accounts or logins. Sign-up, sign-in, one-time codes, passwords and sessions are owned by the ForKhatri Identity & Trust Service; modules never own them.

## BR03 — Module discovery inside the parent

The parent application shall help a member understand and enter available ForKhatri modules without presenting them as unrelated products.

## BR04 — Shared member context

The parent application shall provide a consistent place for member context, notifications, account access, help, and settings entry points. A member signed in to ForKhatri shall be recognised by every module without signing in again, and shall be able to return to the ForKhatri hub from any module.

## BR05 — Progressive module integration

The parent application shall remain useful while some modules are unavailable, planned, or not yet integrated. Unavailable modules must be clearly labeled without breaking the parent experience.

## BR06 — Trustworthy and inclusive access

The parent application shall preserve ForKhatri's trust, privacy, accessibility, multilingual, and low-friction principles while modules are added progressively.

## BR07 — Existing members keep access

Members who already hold a verified account in a module built before the platform identity (Mangaly) shall keep their identity and password when moved to the ForKhatri identity, without re-registering.

## BR08 — Contextual trust and module-owned tiers

The platform shall hold only foundational trust (a verified phone or email, later a verified identity document). Trust earned in one module shall not carry into another. Tiers and roles belong to each module.

## Product invariants

- One ForKhatri app experience.
- One canonical member identity.
- One shared session unless a higher-risk action requires explicit re-authorization.
- Module boundaries are domain boundaries, not user-facing app boundaries.
- A module card or route must not imply that a second account is required.
- No credential is readable by page scripts.
- The hub never shows sensitive module data without an explicit contract.
