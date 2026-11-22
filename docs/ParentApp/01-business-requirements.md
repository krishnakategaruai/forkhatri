---
project: ForKhatri
artifact: Parent Application (Platform) Business Requirements
step: 1
status: Document status 2026-11-22, as built (needs owner confirmation where marked)
updated: 2026-11-22
---

# Platform Business Requirements (BR-xx)

**Document status 2026-11-22, as built.** Scope: the ForKhatri platform only (entrance/hub, Identity & Trust Service, admin console, members dashboard, shared integrations library, deployment kit). Module business requirements live in each `modules/MOD0x-*/01-business-requirements.md`. The original BR01-BR08 text is kept in Appendix A, unchanged; each maps to a BR-xx below. Functional detail: `02-functional-requirements.md` (index). Anything not verifiable from code, screens or a recorded decision is marked *unverified*.

## Contents
1. Vision and problem; 2. Users, personas, journeys; 3. Business model; 4. Value proposition and competitors; 5. Success metrics; 6. Policies; 7. Legal notes; 8. Operating model; 9. Requirements BR-01 to BR-24; 10. Roadmap; 11. Risks; 12. Owner decisions; Appendix A original BR01-BR08.

## 1. Vision and problem
ForKhatri is one mobile-first web app for the Khatri (Somavanshiya) community: one sign-in and one door to every community service (matrimony, community and events, jobs and local services, advice, later payments and loans). Problem: community services are scattered across unrelated apps and WhatsApp groups, each with its own account, trust level and language. The platform provides the shared parts (identity, session, hub, governance, statistics, integrations) so each module can focus on its domain. It is a web app, not a native app (memory: mobile-first-web-app). It runs under the Samaj, not a trust or the founder (owner 2026-10-02).

## 2. Users, personas and journeys
| Persona | Who | Platform journey |
|---|---|---|
| Member | Any community member, often phone-only, many elders | Entrance, enter phone or email, 6-digit code, (new: name and language), hub, tap a module, arrive signed in. |
| Member arriving from a module link | Opens a module URL signed out | Bounced to the entrance with return_to, signs in, returned to the module. |
| Parent or family helper | Acts for a candidate | A module may pre-create a profile (provisioned, level 0); the person claims it by signing in. |
| Samaj office bearer or chapter head | President, secretary, treasurer, chapter head | Admin console: members, roles, suspensions, approvals, audit, queues. |
| Moderator or verifier | Module role | Admin console queues for their module only. |
| Owner and platform staff | Owner, grievance officer, DPO, auditor | All of the above plus module open/closed and appointments. |
| Module service | Mangalya, Milavn, Vyapar, Counsel | Resolves sessions and provisions members through the internal API. |

Test personas are listed in the repo `CLAUDE.md` (asha, new-member, mangalya-family, mangalya-parent, milavn-moderator, samaj-president, samaj-secretary; `krishna` is for people only).

## 3. Business model and revenue
- Built: the platform charges nothing. No platform subscription exists. **Tiers are module-owned and never merged** (BR-08).
- Planned, not built: module earnings route a Samaj share to a Samaj Welfare Trust inside MOD07 Loans & Finance (owner 2026-10-02). Payments run on a sandbox until a vendor is chosen (`shared/forkhatri-integrations/BACKLOG.md`, V1-V7, B1-B8).
- Running costs (deploy kit): one Oracle Always Free VM, Cloudflare Tunnel (free), Resend email, optional R2 backups. Real SMS needs DLT registration (not done).
- Tax and charity treatment of any platform earnings: needs a chartered accountant.

## 4. Value proposition and competitors
One identity and one door for the community in five languages, Samaj-run governance, and contextual privacy (the platform holds basic identity only). Comparables named in the 2026-10-06 critique: CommuTree (community app, weak reviews) and mass-market bundles (Tata Neu, Gojek) as cold-start cautions. Not re-verified in this pass.

## 5. Success metrics (proposed; no targets set)
| Metric | Source today |
|---|---|
| Members and growth by city, age band, gender | `API-GET-v1-insights` (live) |
| Module use (members who entered) | `TBL-registry.member_module_entry` (a tap, not real use) |
| Sign-in success rate, code delivery failures | Not instrumented (unverified) |
| Weekly returning members per module | Recommended in critique C10; not built |
| Time to resolve moderation items | Derivable from `TBL-governance.audit_event`; no dashboard |

## 6. Policies
- Trust: platform trust is foundational only (verified phone or email). `identity_level` 1 or 2 exists; level 2 has no code path.
- Safety and moderation: suspension (1, 3, 7, 30 days or until lifted) ends all sessions everywhere; bans need two people; nobody acts on themselves; reports and cases stay in modules.
- Privacy: basic identity only; masked contact in the UI; contact reveal is audited with a reason. The no-screenshots rule is Mangalya-only.
- Refunds: none at platform level (no platform payments). Module policies live in module docs. Owner to confirm.

## 7. Legal and regulatory notes (all need a lawyer or CA)
- DPDP Act 2023 and Rules 2025: access, correction, erasure, withdrawal, grievance. Phase dates 13 Nov 2025, 13 Nov 2026, about 13 May 2027 (from critique research; confirm against the MeitY text). Delete, export and consent are **not built** (BR-17).
- The data fiduciary (Samaj body, company or founder) is not named anywhere.
- Under-18 parental consent: not built.
- Indian SMS needs DLT registration; WhatsApp needs business verification and templates.
- Section 2(15) Income Tax Act 20% business-receipts limit may affect a Welfare Trust fed by platform earnings (kept out of pitches per owner).
- Caste-body governance gives office bearers local power (critique C12); legal view needed on role and record handling.

## 8. Operating model
Samaj heads run ForKhatri (2026-10-02) through roles by scope and term in the admin console (BR-12). First owner is a direct audited database insert. Hosting, support staff, grievance officer and who answers "Contact ForKhatri support": **owner to confirm** (no support screen exists).

## 9. Business requirements
| ID | Requirement | Rationale | Status | Old id |
|---|---|---|---|---|
| BR-01 | One recognisable entry point for all modules. | Modules must not look like separate apps. | Built | BR01 |
| BR-02 | One member identity; sign-up, sign-in, codes, passwords and sessions owned only by the Identity service. | Single auth source. | Built | BR02 |
| BR-03 | The hub lists modules with honest availability (available, in development, planned), recent first. | Discovery without a second login. | Built | BR03 |
| BR-04 | Shared member context: bell, account sheet, language, sign-out, way back to the hub from any module. | Consistent shell. | Partial (bell is an empty state; no notification service) | BR04 |
| BR-05 | The parent stays useful when modules are down or planned; offline shows the last cached public registry. | Progressive integration. | Built | BR05 |
| BR-06 | Trust, privacy, accessibility, multilingual and low-friction principles preserved. | Audience includes elders. | Partial | BR06 |
| BR-07 | Existing module members keep identity and password on import. | No re-registration. | Built (Mangaly, Milavn dev identities) | BR07 |
| BR-08 | Platform holds foundational trust only; tiers and roles are module-owned. | Contextual trust. | Built | BR08 |
| BR-09 | Sign in with a one-time code to phone or email; password is secondary. | Phone-first audience. | Built; **phone codes cannot be delivered in production until an SMS or WhatsApp vendor exists** | new |
| BR-10 | Sign-in never reveals whether an identifier is registered and resists guessing. | Anti-enumeration. | Built | new |
| BR-11 | Five interface languages (English, Hindi, Telugu, Marathi, Kannada), accurate and respectful, no hardcoded user-visible strings. | Owner rules 2026-09-30, 2026-10-06. | Built for entrance, console, insights; human review of Indic text pending | new |
| BR-12 | Governance: roles by scope and term, nobody admin by default, nobody acts on themselves, two people for bans and senior appointments. | Samaj runs ForKhatri. | Built | new |
| BR-13 | Suspend or restore a member platform-wide with reasons; effective within 30 seconds in every module. | Safety. | Built; no member-facing appeal | new |
| BR-14 | Append-only audit of every governance action and every contact reveal. | Accountability. | Built | new |
| BR-15 | One admin console for all modules; modules publish queues and keep their own rules. | ADR-012. | Built (Mangalya, Milavn live; Vyapar partial) | new |
| BR-16 | Every member can see community statistics, totals only. | Owner 2026-09-27. | Built; small-cell suppression absent (C9) | new |
| BR-17 | Members can export and delete data, read a privacy notice, give and withdraw consent, reach a grievance officer. | DPDP. | **Not built** | new |
| BR-18 | Members can change or add a phone or email and recover access. | Critique C2. | **Not built** | new |
| BR-19 | Modules can provision a profile for another person who later claims it. | Parent-for-child flow. | Partial (level never rises; no claim step) | new |
| BR-20 | Shared integrations library so modules never wire vendors directly. | Owner 2026-10-01. | Partial (interfaces and adapters, no real vendor) | new |
| BR-21 | One notification inbox and channel preferences. | Critique C7. | Planned | new |
| BR-22 | Production on one VM behind Cloudflare Tunnel with backups. | Low cost. | Partial (kit written; real VM not run per critique) | new |
| BR-23 | Development persona switching without passwords, impossible in production. | Fast testing. | Built | new |
| BR-24 | Higher-risk actions need step-up re-authentication. | Shared phones. | Planned | new |

## 10. Roadmap and backlog
Next: choose the SMS or WhatsApp vendor (V3, V4); set and reset password; delete, export, consent and notice; raise level 0 to 1 on first sign-in; small-cell suppression; notification inbox; device list; Welfare Trust in MOD07; MOD06 Payment Services. Vendor list: `shared/forkhatri-integrations/BACKLOG.md`.

## 11. Risks (docs/Critique/CRITIQUE-platform.md, kept honest)
C1 phone sign-in undeliverable; C2 no identifier change; C3 no deletion, export or consent; C4 pre-provisioned hijack and level bug; C5 one id across modules; C6 suspension without appeal; C7 empty bell; C8 shared-phone sessions; C9 small counts; C10 cold start across modules; C11 single-VM availability claims; C12 admin power; C13 language quality; C14 voice quality; C15 shared-IP rate limits.

## 12. Owner decisions recorded
2026-09-14 real identity, existing members keep access, basic identity only, bell left of avatar. 2026-09-27 insights open to all. 2026-09-30 Telugu and Hindi accurate and respectful. 2026-10-01 shared integrations utility, vendors later. 2026-10-02 Samaj runs ForKhatri, Welfare Trust inside Finance, AI for premium tiers in plain words. 2026-10-06 Marathi and Kannada added; protect the base.

## Owner must confirm
Data fiduciary; support and grievance contact and who staffs it; SMS vs WhatsApp channel and budget; platform revenue (none today); refund policy owner; languages beyond five; launch wedge module.

## Appendix A: original business requirements (history, unchanged)

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

## Account deletion (added 2026-11-22)

Owner requirement (2026-11-22, quoted in `ACCOUNT-DELETION.md`): "A user should be deleted if he needs to delete his account, immediately. If he is doing it from ForKhatri, all the accounts in sub modules and traces should be deleted. If he is doing it in an independent module, that module's data related to him, all the stuff, should be deleted." This supersedes the earlier "account deletion and data export: not built" entries in this set (deletion is now built; export is still not built at platform level).

| ID | Business requirement | Why | Status |
|---|---|---|---|
| BR-25 | A member can erase their own data at any time, immediately, with no waiting period. | DPDP right to erasure; owner decision. | Built (not browser-checked) |
| BR-26 | Two kinds of deletion. Kind A (hub, "Delete my ForKhatri account"): the identity and the member's data in every module, all sessions, credentials, uploads. Kind B (inside one module, "Delete my data in the module"): everything that module holds; the ForKhatri identity and other modules stay and the member may re-enter later as a new member. | Members must control scope. | Built |
| BR-27 | Deletion needs re-authentication (password or a fresh one-time code) and typing the word DELETE, because it cannot be undone. | Shared phones, accidents. | Built |
| BR-28 | Only what law or other people's safety forces may be kept, with no name, phone, email, photo or free text, and the member is told in plain words what stays and why. | Minimisation and transparency. | Built; legal basis needs a lawyer |
| BR-29 | Other members' views stay coherent: where a deleted member's name was shown, others see "Deleted member". | Do not break other people's records. | Built in Vyapar, Milavn, Counsel; Mangalya one-to-one chats removed for both sides (known deviation) |
| BR-30 | The owner can prove a deletion happened (one-line receipt with a one-way tombstone, date, modules, counts) and sees deletions that are stuck. | Accountability. | Built |

Retained, in short: payment and tax records where real money moved; safety and moderation records (tombstone only); security log (tombstone only); the deletion receipt. Per-module detail is in each module's `ACCOUNT-DELETION.md` and in `docs/DATA-RIGHTS.md`.

Open business questions (owner): what happens to an expert's unpaid Counsel earnings on deletion; whether a banned member may sign up again (not enforced); whether one-to-one chats in Mangalya should show "Deleted member" to the other side instead of vanishing; the retention period of the audit log and the legal basis for each retained record ("needs lawyer").
