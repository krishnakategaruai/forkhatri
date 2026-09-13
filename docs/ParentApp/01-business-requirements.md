---
project: ForKhatri
artifact: Parent Application Business Requirements
step: 1
status: Ready for Review
---

# Parent Application Business Requirements

## BR01 — Unified application entry

ForKhatri shall provide one recognizable application entry point for members, regardless of which module they intend to use.

## BR02 — One member identity

The parent application shall use one canonical ForKhatri member identity and shall not require separate module accounts or logins.

## BR03 — Module discovery inside the parent

The parent application shall help a member understand and enter available ForKhatri modules without presenting them as unrelated products.

## BR04 — Shared member context

The parent application shall provide a consistent place for member context, notifications, account access, help, and settings entry points.

## BR05 — Progressive module integration

The parent application shall remain useful while some modules are unavailable, planned, or not yet integrated. Unavailable modules must be clearly labeled without breaking the parent experience.

## BR06 — Trustworthy and inclusive access

The parent application shall preserve ForKhatri's trust, privacy, accessibility, multilingual, and low-friction principles while modules are added progressively.

## Product invariants

- One ForKhatri app experience.
- One canonical member identity.
- One shared session unless a higher-risk action requires explicit re-authorization.
- Module boundaries are domain boundaries, not user-facing app boundaries.
- A module card or route must not imply that a second account is required.

