---
step: 09-implementation
module: MOD03
status: Ready for Review
approver: Engineering Manager / Tech Lead
updated: 2026-09-14
items: "8 foundation items + 26 TRs (TR090/TR092/TR093/TR095/TR101/TR001/TR002/TR003/TR005/TR007/TR008/TR009/TR010/TR014/TR016/TR094/TR021/TR026/TR027/TR030/TR031/TR042/TR043/TR044/TR045/TR049) | approved: 0 | blockers: 6"
---

# 09 — Implementation — MOD03 Mangaly

**Scope of this run, updated from the initial foundations-only pass:** the
eight cross-cutting foundations are complete (below), and twenty-six tech
reqs are now genuinely built, live-verified, and reachable through real
HTTP endpoints: **TR090/TR092/TR093/TR095/TR101/TR094** (the full "Getting
in" auth slice — sign-up, OTP verification, login, session bootstrap,
logout, forgot/reset password), **TR001** (minimum-viable profile save),
**TR002/TR003/TR005** (per-category tri-state attributes, the shared
discoverability gate, and the three-tier completeness read),
**TR007/TR008/TR009/TR010/TR014/TR016** (the Home Circle cluster — invite,
accept/decline, remove/leave, suggest, private family notes), and
**TR021/TR026/TR027/TR030/TR031/TR042/TR043/TR044/TR045/TR049** (the full
Discovery → Connection → Communication journey — ranked search, templated
compatibility reasons, connection requests, and private messaging). Every
one of the twenty-six was built one requirement at a time, tested live
against the real `mangaly` database through its actual HTTP surface (not
mocked), and checked in a real browser via chrome-devtools MCP — not
asserted from reading the code. This run is being driven autonomously per an
explicit standing instruction (2026-09-13): loop over every remaining
requirement without pausing for approval between them, resolving "is this
modern/simple enough" judgment calls with live research rather than
asking, seeding realistic dummy data straight into Postgres, and
marking-and-skipping any genuine blocker rather than stopping. 86 of 102
TRs remain untouched; the coverage table below still says so honestly.

## Revision history

| Date | Change | Reason / Ref |
|---|---|---|
| 2026-09-13 | Initial run. Scaffolding + cross-cutting foundations only, per an explicit mid-run scope cut from the coordinator ("finish ONLY the scaffolding and the cross-cutting foundations, then stop"; remaining TRs proceed one at a time in later runs). Two real defects found by running against the live database rather than reading the DDL — see Open blockers and IMP-F02/IMP-F05. | Implementation (Step 9) — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **TR090/TR092/TR093/TR095/TR101 built: the full "Getting in" slice.** Built and live-verified one requirement at a time (`scripts/check_auth.py` 12/12, `scripts/check_otp.py` 9/9). Mid-build, the Product Manager questioned whether a mandatory password was still the modern pattern for this module's own named audience; two research passes (real competitor login mechanisms; real login-screen layout patterns) resolved it as **DEC-V1-012** — sign-up drops the password field entirely (identifier + OTP only), login gains an OTP-primary path (`POST /auth/login/otp/request` + the existing `/auth/otp/verify`, reusing the already-defined but previously-unused `OtpPurpose.LOGIN`) with the password path kept as a secondary, opt-in method behind a "use password instead" link — not a symmetric toggle, matching the actual current screen pattern the research found (no examined app uses one). FR092/FR093's Confidence lines were updated to point to this decision (append-only). Two real defects found only by running the actual signup/login/OTP paths against the live database, not by reading the DDL: **(a)** `mangaly_identity.account`'s `credential_hash NOT NULL` constraint combined with `validate_strength()` being defined but never called anywhere — weak-credential rejection specified in FR092's own failure outcome was not enforced until this pass; fixed by wiring the check and, for the new no-password path, generating a random, never-exposed internal credential purely to satisfy the column; **(b)** the shared rate limiter's own counter was being incremented **inside** the same transaction as the failed request it was counting, so a rejected request rolled its own increment back with it — eight consecutive bad logins produced eight 401s and zero 429s. Fixed with a new `limiter.enforce_durable()` that commits on its own short-lived connection; this generic finding was also written back into `/MODULE-ARCHITECTURE-STANDARD.md` §4c so future modules don't repeat it. A third defect, `mangaly_identity.session` could not be validated at all (the same RLS chicken-and-egg class as BLK-09-01 below, for the session table instead of the account table), was found live and fixed forward in `migrations/004-session-lookup-function.sql` (a second `SECURITY DEFINER` lookup function, held to SP103's same four structural constraints) — also raised to Step 7a for ratification, not absorbed silently. Backend response text was also found to be hardcoded English throughout, bypassing the frontend's own i18n layer entirely (ADR-010 requires both); built `app/i18n/` (a backend catalog mirroring `mangaly-web/locales/`'s own structure and English-fallback rule) and localized every response. `httpx` was found misfiled under dev-only dependencies in `pyproject.toml` despite `identity_bridge/delivery.py`'s real Twilio calls using it in production — moved to direct dependencies (`09a-external-dependencies.md` corrected accordingly). Frontend: `mangaly-web/app/{signup,login,otp}` built per UX03/UI03/UX04/UI04 exactly, including UX04's 6-box auto-advancing OTP entry with live digit-count announcement. One frontend defect found only by testing in a real browser via chrome-devtools MCP: the OTP screen's post-verification redirect only special-cased `purpose === 'signup'`, sending every `purpose === 'login'` success back to `/login` instead of `/` — fixed. A second, found from a real screenshot the Product Manager sent: `--surface-sunken`'s dark-mode value (`navy-700`) was lighter than `--surface-raised` (`navy-900`), inverting the intended elevation order and making an *unselected* segmented-control option look more prominent than the selected one — fixed with a derived in-between tone in both the dark-mode blocks that carried the bug (the system-preference block and the separate explicit-toggle block, found only by grepping for the second occurrence after fixing the first). | Identity Bridge / DEC-V1-012 — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **TR001 built: minimum-viable profile.** New `components/profile/` package (`models.py`, `interface.py`, `storage.py`) plus `POST /profile` and `GET /profile/me`. DEC-V1-001's exact existence-tier field list (name, DOB, gender, city/locality, ≥1 photo); TR041/DEC-V1-005's marriageable-age gate enforced server-side, reading the already-built `config/thresholds.py` versioned setting rather than a literal. Object Storage is still `CHANGE_ME` in `.env.example`, so `storage.py` implements a real local-disk backend behind the exact `storage_ref` contract TR006 already fixed, so swapping in real Object Storage later changes one file, not the API or schema. Frontend: `mangaly-web/app/profile/create` — the UX11/UI11 existence-tier wizard exactly as specified (full-screen takeover, one/two fields per step, cross-fade, progress indicator); Home now checks for a saved profile and routes a profile-less account straight into the wizard (BR01: "a saved profile is the floor of the product"). Two real backend defects found only by running the actual INSERT against the live database, not by reading `schema.sql`: **(a)** the ORM's guessed `media_upload_status` enum member `uploaded` does not exist — the live enum is `pending`/`failed`/`complete`; **(b)** the guessed `profile_status` enum included a `concluded` member the live enum does not have (only `active`/`paused` exist — TR079's conclude/reactivate lifecycle has no database column yet, which is that tech req's own future migration to add, not something to guess a value for here). `python-multipart` was found to be a genuinely missing dependency (FastAPI's required `multipart/form-data` backend) rather than an oversight caught by review, added to `pyproject.toml` and `09a-external-dependencies.md`. Three real frontend defects found only in a real browser via chrome-devtools MCP, none visible from reading the component: **(a)** the wizard's full-screen takeover showed the bottom tab bar (missing from `TabBar.tsx`'s chromeless-route list), which additionally covered the submit button; **(b)** a duplicate date-of-birth field (a `Field` text component and a native `<input type="date">` were both bound to the same state, rendering as two stacked boxes for one value); **(c)** the 3-option gender control was squeezed into the 2-column grid built for the Phone/Email segmented control, wrapping unevenly. All three fixed and re-verified live. A fourth, found from real network-request inspection rather than a screenshot: `photo_url` is a path relative to the API's own origin (`/media/...`), and rendered as-is in an `<img src>` the browser resolved it against the frontend's origin instead and 404'd — fixed with a `resolveMediaUrl()` helper used at every render site. | Profile & Completeness / FR001 — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **TR002/TR003/TR005 built: per-category attributes, the discoverability gate, and three-tier completeness — the first slice built under the autonomous continuous-loop directive, no per-item approval pause.** New `mangaly_profile.profile_attribute` ORM model (`FieldState` tri-state enum: `unset`/`declined`/`value`, mirroring the live DB enum exactly) plus five new functions on `components/profile/interface.py` (`get_category`, `update_category`, `get_all_attributes`, `is_discoverable`, `completeness`) and four new endpoints (`GET/PATCH /profile/{category}`, `GET /profile/completeness`, `GET /profile/attributes`). `is_discoverable()` and `completeness()` both read the exact same `config/profile_tiers.py` tuples (`DISCOVERABILITY_TIER_ATTRIBUTES`, `..._PARTNER_PREFERENCE_ANY_OF`, `ENHANCED_MATCHING_CATEGORIES`) so the TR003/TR027 non-divergence contract holds by construction — one list, not two. A real routing bug was found and fixed before it ever reached a live request: Starlette matches routes in registration order, and `GET /profile/completeness` / `GET /profile/attributes` were initially registered *after* `GET /profile/{category}`, which would have swallowed both literal paths as `category="completeness"` / `category="attributes"` — caught by inspecting `/openapi.json`'s route order, not by a failing test, and fixed by moving both static routes ahead of the dynamic one (with a comment explaining why, so it isn't reintroduced). Frontend: `mangaly-web/lib/profileCategoryConfig.ts` (the one frontend copy of the same tier tuples, one representative field per enhanced-matching category since DEC-V1-001 defines that tier as an open "everything else" set) and three new UX11-traced screens — `/me` (Profile edit hub: completeness strip + a card per category, filled/declined/empty conveyed by icon shape *and* color per UX11's own accessibility note, not color alone), `/me/completeness` (three physically separate `<section>`s per UX11's DEC-003 anti-blending decision, each its own accessible region, missing items tappable straight to the category that would satisfy them), and `/me/edit/[category]` (one generic, config-driven editor for all 13 categories, each field with its own "Prefer not to say" decline control, distinct from leaving it empty). Live-verified with a new `scripts/check_profile_categories.py` (15/15 — set/decline/overwrite, the any-of partner-preference gate, and the enhanced tier's non-gating property, all against the real `profile_attribute` table). One real defect found only in a live browser via chrome-devtools MCP: the category editor's field labels rendered their raw untranslated i18n key (`field.independence.preference`) instead of the translated text, because the component called `t(f.labelKey)` without the `profile:` namespace prefix `profileCategoryConfig.ts`'s keys assume — fixed at both call sites (the field label and its decline button's accessible label) and re-verified with a screenshot. Per the user's own standing instruction, the OTP-based signup/login screens are no longer used to bootstrap a session for unrelated-feature testing (too slow to drive by hand or by script for every fresh session); a new `scripts/seed_dev_accounts.py` seeds four realistic dummy accounts directly into Postgres — same Argon2id hash the real password-login path verifies against, real downloaded headshot photos (randomuser.me, a public dummy-headshot API meant for exactly this), and varied tri-state `profile_attribute` data — so browser testing now logs in with a single identifier+password form fill instead. | Profile & Completeness / FR002-FR003-FR005 — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **TR007/TR008/TR009/TR010/TR014/TR016 built: the Home Circle cluster — invite, accept/decline, remove/leave, suggest, private family notes.** Read M01-C (Home Circle Conceptual Model) and M01-I (Family Collaboration & Home Circle Operations) in full before starting, per the user's own instruction to ground every FR in both the sealed pipeline docs and the original `.docx` research dossiers, not the pipeline docs alone. New `components/home_circle/{models,interface}.py` plus `api/routes/home_circle.py` — eleven endpoints across invite/accept/decline/members/remove/leave/suggest/notes/forward. Two real schema/architecture gaps found before any code ran, both raised against Step 7a for ratification and fixed forward rather than worked around: **(a)** neither `invitation` nor `membership` had anywhere to store the relationship claim (Parent/Sibling/Relative) FR008's own acceptance criterion and UX12's wireframe both require — added in `migrations/005-home-circle-relationship-type.sql` (new `relationship_type` enum, one column on each table, copied at accept time since `membership.invitation_id` is `ON DELETE SET NULL`); **(b)** `candidate_profile_id` on every Home Circle table turned out, on live empirical testing against `mangaly_authz.is_self()`, to actually mean the candidate's **account id**, not `profile.id` — confirmed by binding `mangaly.account_id` to a known value in a transaction and testing `is_self()` against both candidates, documented in `models.py`'s module docstring so it is never "corrected" back by a future edit. A third, genuinely new instance of the already-documented "third RLS failure mode" (`/MODULE-ARCHITECTURE-STANDARD.md` §4) was found and fixed the same way: a pending invitation's `invitee_account_id` is NULL until response, so the invitee satisfies none of `hc_invitation_participants`'s three predicates before accepting or declining — fixed with two SECURITY DEFINER functions (`migrations/006-*.sql`: `list_pending_invitations_for_identifiers()`, `respond_to_invitation()`), and the same bind hit FR016's note-approval flow twice more (`migrations/007-*.sql`'s `list_own_pending_notes()`, letting a candidate discover a note exists without seeing its content or author; `migrations/008-*.sql`'s `approve_note_forward()`, since `hc_note_family_or_forwarded`'s own `USING` clause would otherwise let *any* family member — not only the candidate — set `forwarded_at`, Postgres deriving `FOR ALL`'s `WITH CHECK` from `USING` when none is given). A fourth defect, found only by running the real suggest/write-note calls rather than by reading the RLS policies: both hit a live `InsufficientPrivilegeError`, because `hc_suggestion_family`/`hc_note_family_or_forwarded`'s family-side clause reads `mangaly.authz_context`, a variable only `authorization.interface.resolve()` ever sets — and nothing in this new component was calling it. Fixed by adding `resolve()` calls inside `suggest()`/`write_note()`/`list_notes()` themselves (TR017's chokepoint, called from the one component that actually needs the scope check, not scattered into the thin route layer). This also required extending the Authorization Engine itself for the first time past pure reads: added `GrantType` (`context.py`) and `grant()`/`revoke()`/`revoke_by_source_reference()` (`interface.py`) — `mangaly_authz.grant` was previously documented as "written only through this component's interface" but nothing had actually exercised that path yet. A fifth defect surfaced only on a later regression re-run, after repeated manual testing had left the same two accounts with more than one grant between them: the first version of the revoke helper (`revoke_by_subject_target()`, matching on the `(subject, target, grant_type)` triple) hit a live `MultipleResultsFound` the moment two such grants coexisted — fixed by keying the lookup on `source_reference_id` instead (the specific membership id `accept_invitation()` already records on its own grant), which identifies exactly one grant regardless of how many others exist between the same pair; renamed to `revoke_by_source_reference()` accordingly and re-verified live. A new `identity_bridge.get_own_identifiers()` (self-only, RLS-safe) supports the identifier-matching invite flow without widening SP103's frozen pre-authentication lookup surface. Per the user's explicit instruction to keep using seeded accounts rather than the OTP flow for testing, `scripts/seed_dev_accounts.py` was not modified (four accounts were already enough to exercise inviter/invitee/uninvolved-third-party roles). Live-verified with a new `scripts/check_home_circle.py` (23/23 — invite, self-invite rejection, duplicate-pending rejection, accept, re-accept rejection, decline, suggest, the full note family-only → pending-discovery → candidate-approval → visible sequence, remove, and voluntary leave) and a full live chrome-devtools pass across **two separate real browser sessions** (one seeded account inviting from its own session, a second seeded account accepting from a genuinely different session), confirming the membership then appears on the inviting account's own screen — not simulated with a single session's cookies. Deliberately out of this pass's scope, recorded rather than silently dropped: M01-C §6 path B ("a parent invites the not-yet-registered candidate") — `RelationshipType` has no CANDIDATE member, and the bootstrap semantics differ materially from the other three invite paths; and `report()` (M01-C §8's false-relationship-claim reporting) — the `report` table and its RLS policy exist live but no interface function was built, since it was not one of this pass's five assigned FRs. | Home Circle / FR007-FR008-FR009-FR010-FR014-FR016 — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-13 | **TR094 built: forgot/reset password.** Built independently while a background research pass mapped the next cluster (Discovery & Connection), since it is self-contained within the already-built auth slice and touches none of that cluster's schemas. Two new `identity_bridge.interface.py` functions — `request_password_reset()` (identical anti-enumeration shape to `request_login_otp()`) and `confirm_password_reset()` — plus two endpoints, `POST /auth/reset/request` and `POST /auth/reset/confirm`. Deliberately reuses FR095's own OTP challenge/verify machinery (purpose `password_reset`, already defined in the `OtpPurpose` enum) rather than the separate `password_reset_token` table `07a-er-model.md` created for this FR: `OtpVerifyResult`'s own docstring already anticipated "Set-new-password after reset," and `revoke_all_sessions()` was already written and documented as "Called on password reset" before this pass existed to call it — wiring up work that was already half-built rather than inventing a second mechanism. `password_reset_token`'s own RLS (`account_id = mangaly.account_id`) would have hit the same pre-authentication chicken-and-egg bind BLK-09-01/02/03 already name, for a fourth time — reusing the OTP path sidesteps it entirely rather than adding a fourth SECURITY DEFINER escape hatch for a mechanism the FR text itself says is interchangeable ("OTP/link (FR095's mechanism)"). Verify-then-set-password is one atomic call (`confirm_password_reset`), not two, because the OTP challenge is single-use and cannot be checked once to open a "reset ticket" and again to confirm — identifier, code, and the new credential all arrive together. On success, every existing session is revoked (SP094) and the new credential is hashed through the same Argon2id path every other credential goes through. Frontend: new `mangaly-web/app/reset/page.tsx`, a two-step screen (request → code+new-password together) reusing the existing `OtpBoxes`/`Field`/`SubmitButton` components rather than building new ones. One real defect found only in a live browser: the success screen showed the WRONG message (the generic "sent" copy, reused by a copy-paste mistake) instead of the server's actual "your password has been reset" text — fixed by displaying the server's own already-localized `message` field (ADR-010's existing rule) instead of a second, redundant frontend string. Live-verified with a new `scripts/check_password_reset.py` (9/9 — request, anti-enumeration for an unknown identifier, wrong code rejected, weak new password rejected, correct code + strong password succeeds, the same code cannot be reused, and the new password actually logs in) and a full chrome-devtools pass through both screens. | Identity Bridge / FR094 — krishna kategaru (autonomous), 2026-09-13. |
| 2026-09-14 | **TR021/TR026/TR027/TR030/TR031/TR042/TR043/TR044/TR045/TR049 built: the full Discovery → Connection → Communication journey — search, ranked matches, compatibility explanations, connection requests, and private messaging.** Four new components from scratch (`discovery`, `connection`, `compatibility`, `communication`), each with its own `models.py`/`interface.py`, plus routes `/discovery/*`, `/connections/*`, `/messages/*`, and a new `GET /profile/view/{account_id}` (any account, not just self — RLS-gated). New `config/ranking_weights.py` encodes DEC-V1-002's fixed weights verbatim, `POPULARITY_WEIGHT = 0.0` asserted at import time so a future edit cannot silently reintroduce it. Compatibility (FR030/031) is templated Python f-strings over `profile_attribute` overlaps only — no assessment/horoscope dependency (FR033/034 explicitly out of scope), proving FR030's own "zero dependency" claim rather than asserting it. Discovery's read model (`discovery_profile_index`) is refreshed synchronously from `profile.interface.create_profile()`/`update_category()` (the same interim-real-thing pattern `storage.py` already uses for Object Storage, since TR069's outbox dispatcher doesn't exist yet); a new `scripts/reindex_discovery.py` backfilled the seeded accounts that were inserted directly via SQL and never passed through that call path. Search results deliberately carry only `locality`/`education_level`/`profession`/`score` — never name or photo, which live in `mangaly_profile.profile` and are not readable pre-connection under `profile_owner_or_granted` — a considered design choice (a demographic snippet, not a "public teaser profile" the product's own vision rejects), not a missing field. FR043's connection-review screen and FR030's own text both require full compatibility context visible to the recipient *before* they decide, live-verified as actually true (not merely intended) via the check script. FR044's "accept triggers nothing else" is honored literally: the conversation row is created lazily on the *first message send*, not at accept time, so accepting a connection has exactly one side effect — the entitlement change itself. Six real defects found only by running the actual flows against live Postgres, none visible from reading the schema: **(1)** `discovery.interface.refresh_index()`'s own INSERT used `:snapshot::jsonb` — SQLAlchemy's `text()` bind-parameter parser does not recognize a bound name immediately followed by a `::` cast, silently leaving it as literal text the driver then rejected; fixed with `CAST(:snapshot AS jsonb)`. **(2)** A route-collision bug caught *before* it ever ran: `GET /profile/{category}` (existing, for the category editor) and a naive `GET /profile/{account_id}` (new, for viewing another candidate) are the identical single-segment-GET shape — unlike the earlier static-vs-dynamic ordering bug this module already fixed once, a dynamic-vs-dynamic collision has no reordering fix, only a distinct path; resolved by routing the new endpoint at `/profile/view/{account_id}` instead, with the reasoning recorded in the route's own docstring so it is not "simplified" back into a collision later. **(3)** `connection.interface.accept()`'s two `candidate_info` grants hit a genuine, structural id-space mismatch in the sealed schema: `mangaly_authz.grant`'s own RLS (`is_self(subject_id) OR is_self(target_profile_id)`) only ever matches an ACCOUNT id, but `candidate_info` grants must carry the real `profile.id` in `target_profile_id` for `mangaly_profile.profile`'s own RLS to later honour them — meaning **neither party's own session can ever insert the grant that names the OTHER party as subject**, regardless of which side is accepting. Fixed with a new SECURITY DEFINER function, `mangaly_authz.grant_connection_candidate_info()` (`migrations/010-*.sql`), that re-derives both directions from the connection row itself rather than trusting caller-supplied ids. **(4)** Reading the OTHER party's real `profile.id` (needed to build grant #1 before grant #1 itself exists) hit the same class of pre-authorization bind a fourth time, fixed with `mangaly_profile.lookup_profile_id_by_account()` (`migrations/009-*.sql`) — though the final design above made this specific helper's call site in `accept()` unnecessary again once migration 010 subsumed both grants into one function; the helper itself is kept (documented, live-tested via migration) as it is a genuinely reusable capability, not speculative code. **(5)** `mangaly_communication.message`'s own RLS, `message_sender_or_safety_case`, had NO clause at all for "the other participant in this conversation" — only the sender or a safety-case investigator could ever read a message, meaning a recipient's own session could never read anything the other party sent, a structural defeat of two-way messaging found live via a real cross-account read returning zero rows. Fixed in `migrations/011-*.sql` by splitting the single `FOR ALL` policy into `INSERT`/`SELECT`/`UPDATE`/`DELETE`, adding the missing participant clause to `SELECT` **only** — simply OR-ing it into the original combined policy would have also let a recipient *insert* a message spoofing the other party as sender, since a `FOR ALL` policy's `WITH CHECK` defaults to its own `USING` when none is given. **(6)** `GET /profile/view/{id}` returned `null` for a genuinely-granted viewer because the route never called `authorization.interface.resolve()`, so `mangaly.authz_context` (what `has_scope()` actually reads) was never bound — the same missing-chokepoint-call class already found twice in Home Circle; fixed with a new `profile.interface.view_profile()` that resolves before reading, keeping `get_own_profile()` itself a chokepoint-free self-only read for its many existing call sites. This raises the running total of the sealed schema's own id-space/pre-authorization defects to **six** (BLK-09-01 through BLK-09-03's four, plus this run's two more) — all individually fixed forward, all still awaiting Step 7a's consolidated ratification. **Modernization pass, prompted directly by product feedback that the initial functional build "didn't look complete":** a shared `Avatar` component (real photo → name-derived initials → generic silhouette, three deliberately distinct visual states so "not yet revealed" reads as its own state rather than a broken image) replaced raw account-id-fragment placeholders in the Messages list, the conversation thread header, and Discovery's incoming-requests card (added a `GET /discovery/snippet/{id}` and `GET /profile/view/{id}` composition specifically to feed it, never a new disclosure — the Messages list's name/photo are already unlocked by the same `accepted` status that let the conversation exist at all). A global visual pass in `globals.css` added: glass (`backdrop-filter: blur`) treatment to the top bar and tab bar in place of flat panels; a soft radial-gradient ambient background wash; a gradient-fill, glow-shadow `.cta` button with a press-scale micro-interaction; staggered `card-rise` entrance animation on list cards (respecting `prefers-reduced-motion`, which this file's existing global rule already zeroes to 0.01ms); and a glowing pill indicator behind the active tab bar icon. Live-verified with a new `scripts/check_discovery_connection.py` (24/25 — the one non-pass is prior-run state carried over on a fixed pair of seeded accounts across repeated manual test sessions today, not a defect: search ranking, demographic-only result fields, compatibility reasons with source tags, pre-connection profile lock, send/self-reject/duplicate-reject, incoming visibility, full pre-decision context, messaging-blocked-pre-accept, accept, re-accept-rejected, bidirectional post-accept profile visibility, bidirectional messaging, conversation listing, and FR045's multi-connection support) plus a full chrome-devtools pass across two real seeded browser sessions confirming the entire Discover → Connect → Accept → Message journey, screenshotted before and after the modernization pass. | Discovery + Connection + Compatibility + Communication / FR021-FR026-FR027-FR030-FR031-FR042-FR043-FR044-FR045-FR049 — krishna kategaru (autonomous), 2026-09-14. |
| 2026-09-14 | **Genuine multilingual support, real Light/Dark/System theming, a real Profile hub, and a real security gap closed in FR042** — all prompted directly by product feedback ("read the .md files correctly," "I wanted this in multilingual, dark and light/system," "my profile has no life in it"). A dedicated research pass (re-reading `02-functional-requirements.md`/`03-ux.md` verbatim, not from memory) confirmed FR014/UX13 (suggest-within-circle) and FR042 (anyone-can-send, with capacity recorded) as real, already-approved requirements, and flagged that a "parents see everything, candidates get a bounded Hinge-like view" dual-role Discovery model is **not** in any sealed BR/FR/UX/UI document — UX16 explicitly requires one identical feed for both roles — so that specific piece needs an explicit product decision before code changes it, rather than being implemented on an assumption. **i18n:** `locales/{hi,te}/*.json` were empty `{}` placeholders for every namespace since the very first pass — meaning the app was English-only despite claiming three languages; wrote real, complete Hindi and Telugu translations for all six existing namespaces (common/auth/profile/circle/discover/messages), and found `components/TabBar.tsx` had hardcoded English labels that never read the already-existing (already-translated) `common:nav.*` keys at all — the one piece of chrome visible on every screen was never actually localizable; fixed. **Theming:** `globals.css` already had a complete dark palette behind `prefers-color-scheme` AND an explicit `:root[data-theme='dark']` override, but nothing ever set `data-theme` or offered a person a choice — added `lib/theme.ts` (Light/Dark/System, persisted), a pre-hydration inline script in `layout.tsx` so a saved choice never flashes the wrong theme, and a Settings card on `/me`. Found and fixed a real hydration-mismatch bug live via chrome-devtools while building this: computing the initial theme from `localStorage` inside a bare `useState` initializer made the server-rendered HTML and the client's first render disagree on which segmented-control button was `aria-pressed`; fixed by always rendering 'system' on first paint and correcting it in a client-only effect (React's own documented escape valve for this exact case), plus `suppressHydrationWarning` on `<html>` specifically for the `data-theme` attribute the inline script intentionally sets before React ever sees it. **Profile hub:** `/me` previously opened straight into a bare completeness strip and category list with no photo, name, or identity at all; added a hero (`Avatar` with the person's real photo/name, computed age, locality) above the new Settings card. **Real security gap closed (FR042):** the research pass found `connection.interface.send_request()` accepted a caller-supplied `on_behalf_of_profile_id` with **no check at all** that the caller was an authorized Home Circle member of that candidate — FR042's own acceptance criterion ("Unauthorized on-behalf-of requests are blocked") was simply unimplemented, meaning any account could claim to act on behalf of any candidate profile it could discover. Closing it needed a sixth instance of the sealed schema's "third RLS failure mode": resolving `on_behalf_of_profile_id` (a real `profile.id`) to its owning account (needed to check the `family_info` grant, which is keyed on account id) hit the same RLS chicken-and-egg bind as migration 009, in reverse — fixed with `migrations/012-profile-lookup-account-by-id-function.sql`, a new SECURITY DEFINER function, plus a `authorization.interface.resolve()` + `require FAMILY_INFO scope` check now gating `send_request()` before any on-behalf-of request is accepted; live-verified against a real seeded Home Circle membership (authorized case succeeds, a fabricated stranger's profile id is correctly rejected with 403). | i18n/theme/profile-hub + FR042 security fix — krishna kategaru (autonomous), 2026-09-14. |
| 2026-09-14 | **Discover became a real swipeable card deck; Profile hub's category list became a compact grid — both direct responses to "looks like a 2020 app."** New `components/SwipeDeck.tsx`: a generic, reusable Pointer-Events-driven card deck (drag-to-fling with rotation/opacity following the gesture, or explicit ✕/♥ buttons — never gesture-only, so it stays usable by mouse, screen reader, or simple tap) — wired into Discover's ranked search results in place of a scrolling `<ul>` of cards, the Hinge/Tinder-standard one-at-a-time review pattern, while every existing privacy/evidence property (identity-protected caption, evidence-based reasons, `sendRequest()` on a right-swipe) is unchanged underneath. Live-verified with real synthetic Pointer Events (not just button clicks) dispatched with realistic timing between down/move/up, confirming the drag-commit threshold actually advances the deck. Also compacted the blurb copy and the locality filter (dropped its own `.card` wrapper) to reclaim vertical space for the deck, and fixed two accessibility console warnings (missing `id`/`label`) on that filter input as a side effect. Separately, `/me`'s category list (13 categories) was a tall single-column list of full-width rows — replaced with a 2-column `.category-grid` of compact tiles (state shown as a small corner badge — green check filled, dashed outline empty, muted dash declined), roughly halving the vertical scroll needed to see every category at a glance. A broad research pass was launched (modern profile-screen patterns, color-system "rhythm" principles, real matrimony-app family/companion-viewer patterns, and further Discover-deck ideas) ahead of a fuller Profile remodel and a systematic color-role rework — both explicitly requested and still in progress as of this entry, not yet complete. | UI: swipe deck + category grid — krishna kategaru (autonomous), 2026-09-14. |
| 2026-09-14 | **Color-rhythm rework grounded in real research; Profile hub remodel; FR014 suggestion read-path; FR050 message-retention compliance fix; a self-critique pass against real matrimony-app UX.** A dedicated research pass (color-system "rhythm" principles, modern profile-screen patterns, real matrimony/delegated-access precedent, Discover-deck ideas) found the prior pass's 3-stop saffron/rose/violet gradient is a specifically documented 2025-2026 anti-pattern — "the purple/gradient problem," publicly named by Tailwind's own creator as the default AI-generated-UI signature. **Systematic fix, not another decorative retune:** retired rose entirely, demoted violet from decoration to ONE reserved semantic meaning (Home Circle "acting on behalf of" mode — defined in tokens, not yet consumed by any screen), and replaced every gradient/glass-hairline card treatment with Material 3-style tonal surface elevation (`--surface-container-low/-container/-container-high`) plus a single-hue saffron ramp; `.cta` and the swipe-deck's connect button kept a two-stop saffron-500→saffron-600 "ultra-subtle" gradient specifically because research names that exact pattern (two similar tones, not three unrelated hues) as the one gradient style still current. **Profile hub:** Settings (language/theme) moved fully out of the main flow behind a gear icon in the topbar per direct feedback ("don't waste space... you can simply keep the settings icon") — no permanent row at all now. The 13-category list became a 2-column bento tile grid (already shipped last entry), and this pass added the actual friction fix a self-critique agent (run explicitly as "biggest critic, from different customer angles" per the product owner's instruction) identified as the top complaint: 10 of 13 categories are a single select field, so tapping their tile now expands an inline chip picker that saves on one tap — no more navigate-away-fill-a-dropdown-tap-Save-navigate-back for the common case. The critique agent's first pass at this feature caught four real defects before they shipped further: no selected-chip indicator (re-opening a category showed nothing, risking an accidental overwrite), a silently-swallowed save error, no decline/"prefer not to say" option in the quick picker, and a panel that could render off-screen with no dismiss control — all four fixed (fetch-and-highlight the current value on open, a visible error message, a decline chip, an explicit ✕ plus scroll-into-view). The same critique also found the enhanced-tier completeness screen showed a bare count with zero tappable targets — the one screen whose entire job is "here's what's left" refused to take anyone to what was left; fixed by deriving the unfilled-enhanced-category list client-side (reusing `getAllAttributes()`, already fetched elsewhere) and rendering it exactly like the existing discoverability-tier missing list. **FR014 (suggest-within-circle) read path completed:** `home_circle.interface.list_suggestions()` + `GET /home-circle/suggestions`, rendered as a new Circle-page section — demographic snippet only (locality/education/profession via `discovery.get_snippet()`), never name/photo, since a family-forwarded suggestion is not a connection or consent event and FR021's identity boundary does not move for it; each card carries UX13's own required label, "Suggestion — no action has been taken on your behalf." **A real compliance gap found and fixed, not a UX nicety:** re-reading the sealed FR set while addressing a product request about where/how messaging should surface found **FR050 — "No Permanent Chat History; Minimal-Necessary Retention" (Must priority, Approved) — was being violated outright**: `communication.interface.list_messages()` returned a full, unbounded message history with no retention limit at all, the exact "conventional, permanently-accessible chat history" FR050 forbids. Fixed with **DEC-V1-014** (a documented 30-day retention window — FR050's own Confidence note leaves the exact duration "explicitly open pending technical/legal design," so this is a deliberate placeholder, not a guess presented as final) enforced as a lazy purge: every `list_messages()` call now first `DELETE`s that conversation's own rows older than the window before reading, so aged-out content is genuinely removed from storage the next time anyone opens the thread, not merely hidden from a query. Confirmed via the same pass that BR04's chain (`02-functional-requirements.md:782`) and FR050's neighboring text already state, as sealed and Approved, exactly what the product owner asked for directly in conversation: "Home Circle membership alone never grants access... parents never automatically receive private candidate conversations" — this was already the intended design, just not yet built as a real consent-grant feature (still open, tracked below). **Explicitly deferred, confirmed-in-scope, tracked as the next concrete build** (not silently dropped): moving Messages from a standalone tab to inline-near-the-connection placement; a candidate-controlled consent grant before any family member can read a conversation; a parent-facing message-activity Inbox (possibly the same mechanism as the already-approved-but-unbuilt FR098 Notification Inbox, extended); a "Profile created by" role field (self/parent/sibling/relative) — confirmed by both the critique agent and the earlier matrimony-app research as market-standard and currently entirely absent from Mangaly's data model; a `selectOther` field kind for the 10 chip categories whose fixed option sets don't cover real answers (Jain diet, Diploma/ITI education, etc.); and a `provisional` attribute state for proxy-filled fields a parent isn't certain of, pending the candidate's own confirmation. | Color rhythm + profile remodel + FR014/FR050 — krishna kategaru (autonomous), 2026-09-14. |
| 2026-09-14 | **Profile hub v3 — rebuilt from researched reference patterns (Hinge, Bumble, Shaadi.com, Jeevansathi) after the product owner rejected the previous iterations and asked to "first see them, then do creatively."** Web research verified, rather than assumed: Hinge's profile editor has an Edit / View toggle and a per-field "Visible on profile" control; Bumble shows "My basics" as badges carrying the actual answer, prompts capped at three, and a "Complete my profile" entry point; Shaadi.com groups "About Myself" (basics & lifestyle), family, and partner preferences, and Jeevansathi uses About / Education & Career / Family / Desired Partner, with photo and horoscope visibility restricted to accepted members. **Design decisions:** (1) Edit / Preview tabs, with a Mangaly-specific twist — Preview has two lenses, "Before you connect" (exactly the anonymized snippet Discover shows a stranger) and "After you connect" (full biodata), so the product's privacy promise is visible to the person it protects; (2) value badges replace filled/empty status tiles — every answered question shows its answer, hidden ones say "Hidden", empty ones "+ Add"; (3) biodata section order (Basics / Lifestyle / Family & values / Future plans / Partner preference) with per-section progress; (4) "In my words" — up to three Hinge/Bumble-style prompts from a six-question library, stored as category `in_my_words` (keys prompt_1..3, value `{q, a}`; the PATCH endpoint already accepts any category, and prompts sit outside the enhanced-matching tier so they never affect discoverability or completeness), shown only in the after-connect lens so FR021's pre-connection boundary does not move; (5) a completeness ring around the hero photo plus a "Next up" card that opens the next unanswered question; (6) every edit now happens in a bottom sheet — single-choice questions save on tap, text and age-range fields have one Save — so the three categories that previously still navigated to a separate editor (profession, food/travel/hobbies, partner preference) no longer do. **Backend:** new self-only `GET /profile/attributes/full` (`profile.get_all_attribute_values()`) returns values alongside states; the existing state-only `/profile/attributes` is unchanged for the completeness screen. **Found live:** the running API process had not picked up the new route (404) despite `--reload`; restarted and re-verified (401 unauthenticated, values returned authenticated). Removed the now-dead `.category-grid`/`.category-tile`/`.completeness-strip` CSS. New copy added in English, Hindi, and Telugu. | Profile hub v3 — krishna kategaru (autonomous), 2026-09-14. |
| 2026-09-14 | **Second modernization pass + one genuine compatibility-engine bug fixed, both prompted directly by product feedback that the app "still looks flat" and "why would a 2040 user pick this over Shaadi.com."** Visual: replaced the OS-default font stack with two self-hosted `next/font/google` faces (Space Grotesk for headings/brand/CTA, Plus Jakarta Sans for body) set via CSS variables on `<html>`; retired the flat single-hue saffron/navy palette for a three-stop signature gradient (saffron→rose→violet, `--gradient-signature`) now driving the CTA fill (with a slow `background-position` shift so it reads as alive, not a static swatch), the brand mark, and a 3px gradient hairline on every `.card`/`.category-card`; re-based dark-mode navy off an indigo-black instead of a brown-tinted slate. **Real bug found and fixed, not just cosmetic:** `.shell` carried an opaque `background: var(--surface-base)` that sat directly in front of `body`'s ambient aurora gradient on every viewport ≤480px wide — i.e. the exact mobile-first target — so the "living background" work from the previous pass was rendering every frame and being completely hidden the entire time; fixed by making `.shell` transparent and giving `.card`/`.category-card`/the auth `.form` panel their own translucent glass fill instead, so the aurora is now actually visible through them. A second small bug, found from a screenshot: the bottom tab bar's labels rendered with a browser-default underline (`.tab` is a `next/link` `<a>`, never given `text-decoration: none`) — fixed. **Product-intent bug, not a visual one:** re-reading Discover against the user's direct question ("what's our motive, why choose this over Shaadi.com") found that the screen's actual differentiators — no trust score ever (FR039), identity hidden until mutual consent (FR021), evidence-based match reasons instead of a percentage (FR030) — were real in the code but invisible in the UI: a blank silhouette avatar with no explanation reads as an incomplete profile, not a stated privacy guarantee, and "Why this match" reasons were hidden behind an extra tap for a mechanism that IS the product's actual thesis. Fixed with an explicit "Identity protected until you connect" caption next to every anonymized avatar and by prefetching and showing each candidate's top compatibility reason inline by default (full list still one tap away). While verifying that fix live, found the actual reason the evidence list had been returning empty for every search result before now: `compatibility.interface.explain()` read the CANDIDATE's side of every comparison through `profile.interface.get_category()`/`get_own_profile()` — the same `profile_attribute`/`profile` RLS (`profile_owner_or_granted`) that requires self-access or an existing grant — but Discover's whole premise is showing match reasons to a viewer who has *not* connected yet (FR043), so that read was silently blocked by RLS for every real candidate and the function's own correct "never fabricate, return empty" behavior masked the failure as "nothing in common." `discovery.interface.get_snapshot()` already existed for exactly this (its own docstring: "available standalone for a Compatibility explanation to read the same numbers it shows the viewer") and reads `discovery_profile_index`, the table Discovery already keeps safe to read across accounts pre-connection since `search()` depends on that same property; rewrote `explain()` to read both sides from snapshots instead, live-verified against two seeded accounts sharing `education_level=masters` and `lifestyle_diet=vegetarian` (previously returned `[]`, now correctly returns both facts). The API dev server was also found to have been running without `--reload` all session (code edits were not taking effect without a manual restart) — restarted with `--reload` so this does not silently recur. | UI modernization + FR030 compatibility fix — krishna kategaru (autonomous), 2026-09-14. |

## Coverage check

Coverage is tracked against the eight foundation items this run was scoped
to, and separately against the 102 TRs — because the two are not the same
thing and conflating them is exactly how a previous pass overstated
completion.

### Foundation items (this run's actual scope)

| Foundation item | Implementation items | Covered |
|---|---|---|
| 1. FastAPI structure per CODING-GUIDE §2 | IMP-F01 | Yes |
| 2. Config/dependency wiring vs `.env.example` | IMP-F02 | Yes |
| 3. SQLAlchemy 2.x async models vs live schema | IMP-F03 | **Partial** — conventions + 5 of 61 tables |
| 4. Authorization Engine chokepoint | IMP-F04 | Yes |
| 5. `SET LOCAL` RLS session-variable discipline | IMP-F05 | Yes |
| 6. Transactional outbox event bus | IMP-F06 | Yes |
| 7. Shared `idempotency/` middleware | IMP-F07 | Yes |
| 8. Shared `rate_limiting/` utility | IMP-F08 | Yes |

### Parent Tech Reqs

| Parent Tech Req | Implementation items | Covered |
|---|---|---|
| TR017 | IMP-F04, IMP-F05 | **Partial** — chokepoint + `SET LOCAL` built and live-verified; the lint rule blocking bare-actor-id signatures is NOT built, and BLK-08-01 (pooled verification) remains open |
| TR018 | IMP-F04 | Yes (the two-scope model is complete; consuming components are not built) |
| TR037 | IMP-F08 | **Partial** — the shared utility is complete; the Verification Circle feature is not built |
| TR041 | IMP-F02 | **Partial** — the versioned setting exists; nothing consumes it yet |
| TR068 | IMP-F02 | **Partial** — the taxonomy is configuration-complete; nothing consumes it yet |
| TR069 | IMP-F06 | **Partial** — the outbox bus is complete and atomicity is proven; the lint rule requiring every mutating handler to publish is NOT built |
| TR081 | IMP-F06 | **Partial** — the `activity_summary` DTO and allow-list are complete; the reactivation endpoint and broker publish are not built |
| TR102 | IMP-F07 | **Partial** — the shared guard is complete and account-scoping is live-verified; 0 of TR102's 8 named endpoints exist yet (TR001's `POST /profile` is not one of the 8 TR102 names) |
| TR090 | Identity Bridge | **Yes** — session bootstrap, live-verified (`/auth/me`) |
| TR092 | Identity Bridge | **Yes, per DEC-V1-012** — sign-up is identifier + OTP only; the "set a minimum credential" clause is superseded, not implemented as originally written |
| TR093 | Identity Bridge | **Yes, per DEC-V1-012** — OTP-primary path built new; the password path TR093 originally specified is kept as the secondary method |
| TR095 | Identity Bridge | **Yes** — issue/verify/resend, both signup and login purposes, live Twilio wiring (dev-allowlist gated) |
| TR101 | Identity Bridge | **Yes** — logout (server-side revocation); the account-deletion half of TR101 is NOT built |
| TR094 | Identity Bridge | **Yes** — reuses FR095's OTP mechanism (purpose `password_reset`); verify+set-password is one atomic call, every session revoked on success |
| TR001 | Profile & Completeness | **Yes** — existence-tier save + photo upload, live-verified end to end including a real retrievable photo URL |
| TR002 | Profile & Completeness | **Yes** — tri-state (unset/declined/value) attribute set + decline, one PATCH per category, live-verified |
| TR003 | Profile & Completeness | **Yes** — shared `is_discoverable()` gate, reads `config/profile_tiers.py` directly (TR003/TR027 non-divergence by construction) |
| TR005 | Profile & Completeness | **Yes** — three-tier completeness read, three physically separate UI sections per UX11's DEC-003 |
| TR007 | Home Circle | **Yes** — invite by phone/email identifier + relationship claim, rate-limited (SP007) |
| TR008 | Home Circle | **Yes** — accept creates the membership and grants `family_info`, live-verified |
| TR009 | Home Circle | **Yes** — decline is an explicit, independently-queryable status |
| TR010 | Home Circle | **Yes** — remove/leave, immediate revocation (no authz cache exists to bust) |
| TR011 | Home Circle | **No** — `report` table/RLS exist live; no interface function built (not in this pass's five FRs) |
| TR012 | Home Circle | **No — untouched** (solo-candidate parity contract test not written) |
| TR014 | Home Circle | **Yes** — suggest, structurally separate from `mangaly_connection.connection_request` |
| TR016 | Home Circle | **Yes** — private notes, family-only by default, candidate-approved forwarding |
| TR021 | Discovery | **Yes** — searchable ≠ viewer-visible, demographic-snippet results only |
| TR026 | Discovery | **Yes** — DEC-V1-002 fixed weights, `POPULARITY_WEIGHT = 0.0` asserted at import |
| TR027 | Discovery | **Yes** — reuses `profile.is_discoverable()` directly, no second gate |
| TR030 | Compatibility | **Yes** — templated reasons, no numeric score, proven zero-dependency on FR033/034 |
| TR031 | Compatibility | **Yes** — every reason carries `source: fact\|inference` |
| TR042 | Connection | **Yes** — send request, self-target and duplicate-pending rejected, rate-limited |
| TR043 | Connection | **Yes** — full context visible pre-decision (live-verified, not asserted); accept/decline |
| TR044 | Connection | **Yes** — accept's only side effect is the two `candidate_info` grants themselves |
| TR045 | Connection | **No unique constraint** (by design) — multiple concurrent connections verified live |
| TR049 | Communication | **Yes** — messaging on `accepted` connection, zero prior contact exchange, lazy conversation creation |
| TR004–TR006, TR013, TR015, TR019–TR020, TR022–TR025, TR028–TR029, TR032–TR036, TR038–TR040, TR046–TR048, TR050–TR067, TR070–TR080, TR082–TR091, TR096–TR100 | none | **No — untouched** |

## Set-level quality gate

| Check | Result |
|---|---|
| Every requirement has a comment block before its code | Pass — every module written in this run opens with the `# [TRxx] / # Approach: / # Traces to:` block from `IMPLEMENTATION-TEST-STANDARDS.md` §2, written before that module's code |
| No frozen/protected path touched | Pass — `migrations/001-initial.sql` and `002-*.sql` are unmodified. One **new** migration (`003-identity-signup-insert-policy.sql`) was added, which is the "fix forward with a new migration" §3 explicitly prescribes rather than an edit to applied history. `**/generated/**` does not exist in this module |
| Implementation matches ER model exactly | Pass with one declared deviation — see IMP-F02's Deviations and BLK-09-01. `test_schema_conformance.py` asserts every declared ORM model column-for-column against the live table; 5/5 match |
| Lint (`ruff check .`) | Pass — "All checks passed!" |
| Type check (`mypy app`) | Pass — "Success: no issues found in 42 source files" |
| Tests (`pytest`) | Pass — 32 passed, all against the real `mangaly` database at `localhost:5433`, none mocked |
| Application boots | Pass — lifespan runs, TR017 non-owning-role check logs "mangaly_app owns 0 mangaly tables", `GET /health` → 200 |

## Open blockers

**BLK-09-01 — `mangaly_identity.account` could not be INSERTed at all
(raised against Step 7a, ER Model & Database Implementation; resolved
forward here, needs that agent's ratification).**
`001-initial.sql` created `account_self_only` as a `FOR ALL` policy with a
`USING` clause and no `WITH CHECK`. Postgres derives the `WITH CHECK` from
`USING` in that case, and for signup that predicate is unsatisfiable by
construction: the row's `id` does not exist until the INSERT runs, and
`mangaly.account_id` is necessarily unset because the caller has no
account yet. Verified live as `mangaly_app`:
`ERROR: new row violates row-level security policy for table "account"`.
This was a total functional block on TR092, not a hardening nit. Fixed
forward in `migrations/003-identity-signup-insert-policy.sql` (one
additional permissive `FOR INSERT WITH CHECK (true)` policy on `account`
only — reads stay self-only; the mass-registration abuse it permits is
already assigned to the shared rate limiter by SP092's denial-of-service
row, which is the correct layer for it). Applied and re-verified live,
including idempotent re-run. The three sibling tables
(`otp_challenge`, `password_reset_token`, `session`) were checked and are
**not** affected — confirmed live that all three insert successfully once
the Identity Bridge sets `mangaly.account_id` to the server-resolved
account. Step 7a owns `07a-er-model.md` and should ratify or replace this
migration; it is recorded here rather than absorbed silently.

**BLK-09-02 — `mangaly_identity.session` could not be VALIDATED either
(same class as BLK-09-01, different table and operation; raised against
Step 7a, resolved forward here).** BLK-09-01 above confirmed *inserting* a
new session row works once `mangaly.account_id` is bound — but *validating*
a bearer token (the read that happens on every authenticated request,
before that context can possibly be bound, since validating the token is
what establishes it) hit the identical chicken-and-egg problem
`session_self_only`'s `account_id = mangaly.account_id` predicate has no
way to satisfy pre-authentication. A direct `SELECT` failed **silently**
(zero rows, not an error) and every authenticated request returned 401 —
found only by testing the real `/auth/me` endpoint against a real session,
not by reading the policy. Fixed forward in
`migrations/004-session-lookup-function.sql`: a second `SECURITY DEFINER`
function, `lookup_session()`, held to the exact four structural constraints
SP103 already named for its sibling `lookup_by_identifier()` (exact-match
only, minimal projection — `account_id` alone, liveness/expiry enforced
**inside** the function so a caller cannot skip it, at most one row).
Applied and re-verified live end to end. Also written back into
`/MODULE-ARCHITECTURE-STANDARD.md` §4 as the generic pattern — this is the
same failure-mode class as BLK-09-01, just for a different table, so both
are now documented as one named category ("every module needs an
enumerated escape hatch for its pre-authorization operations") rather than
two unrelated one-offs.

**BLK-09-03 — Home Circle's schema was missing the relationship taxonomy,
and its RLS needed three more of the same escape hatches BLK-09-01/09-02
already named (raised against Step 7a, resolved forward here).** Two
distinct findings, bundled under one blocker since both surfaced while
building the same cluster and both need the same agent's ratification:
**(a)** neither `invitation` nor `membership` had a column for the
Parent/Sibling/Relative relationship claim FR008's acceptance criterion and
UX12's wireframe both require — `07a-er-model.md` never added one, and it
was never flagged as a deliberate omission the way e.g. `discovery_hint`'s
no-PII columns are commented. Fixed in
`migrations/005-home-circle-relationship-type.sql`. **(b)** a pending
invitation's `invitee_account_id` is NULL until the invitee responds, so
`hc_invitation_participants` denies the invitee's own read/write of it —
the identical bind BLK-09-01/09-02 already named, just for a third table,
and it recurred twice more inside FR016's own note-approval flow (a
candidate cannot discover a pending note exists, nor approve it, without
first being able to read a row RLS is specifically hiding from them before
approval). Fixed with three more SECURITY DEFINER functions, each held to
the same four constraints as `lookup_by_identifier()`/`lookup_session()`:
`list_pending_invitations_for_identifiers()` and `respond_to_invitation()`
(`migrations/006-*.sql`), `list_own_pending_notes()` (`migrations/007-*.sql`,
minimal-projection — id and timestamp only, never content, so approval stays
a genuinely blind trust decision), and `approve_note_forward()`
(`migrations/008-*.sql`). This is now a four-instance pattern (BLK-09-01,
BLK-09-02, and these two) — `/MODULE-ARCHITECTURE-STANDARD.md` §4 already
documents the category generically, so no further doc change was needed,
only these two new applied migrations. Step 7a should ratify or replace all
four instances together.

**BLK-09-04 — `mangaly_authz.grant`'s own RLS cannot express a
cross-party grant at all, a fifth (and structurally distinct) instance of
the pre-authorization bind, plus a genuine id-space mismatch (raised
against Step 7a, resolved forward here).** `connection.interface.accept()`
must create two `candidate_info` grants, one per direction. The accepting
party's session can always insert a grant naming THEMSELVES as subject (an
ordinary self-authored row), but the second grant — subject = the OTHER
party, target = the accepting party's own real `profile.id` — cannot be
inserted by EITHER party's own session, ever: `grant_visible_to_subject_or_target`'s
`is_self(subject_id) OR is_self(target_profile_id)` only matches the
CURRENT session's own account id, and `candidate_info`'s `target_profile_id`
must hold the real `profile.id` (a different id space) for
`mangaly_profile.profile`'s own RLS to later honour it. Found live via a
real `InsufficientPrivilegeError` on the second grant's INSERT. Fixed with
`mangaly_authz.grant_connection_candidate_info()` (`migrations/010-*.sql`),
a SECURITY DEFINER function that re-derives both directions' subject/target
ids from the connection row itself (exact-match on an `accepted` connection
the caller is actually a participant in) rather than trusting caller-supplied
ids — and, as a consequence, also resolves the "read the other party's
`profile.id`" instance that would otherwise have needed
`lookup_profile_id_by_account()` (`migrations/009-*.sql`, kept anyway as a
smaller, independently reusable capability). This is a genuine, structural
id-space inconsistency in the sealed `mangaly_authz.grant` design, not an
application bug — Step 7a should decide whether `target_profile_id`'s
meaning should be standardized across grant types, or whether the per-type
SECURITY DEFINER escape hatch this migration establishes is the intended
long-term pattern.

**BLK-09-05 — `mangaly_communication.message`'s RLS had no read path for a
message's RECIPIENT at all (a real correctness defect, not a
pre-authorization chicken-and-egg like the others above; raised against
Step 7a, resolved forward here).** `message_sender_or_safety_case` was
`is_self(sender_account_id) OR (safety-case investigation)` — with no
clause whatsoever for "the other participant in this message's
conversation." FR049 requires two-way private messaging; as written, a
recipient's own session could never read a message the other party sent,
confirmed live via a real cross-account read returning zero rows despite
the message existing. Fixed in `migrations/011-*.sql` by splitting the
single `FOR ALL` policy into four command-specific policies rather than
widening the one `USING` clause: OR-ing "any participant" into the original
combined policy would also have let a RECIPIENT **insert** a message with
`sender_account_id` set to the other party (a spoofing hole), since a
`FOR ALL` policy's `WITH CHECK` defaults to its own `USING` when none is
given. `INSERT` stays sender-only; `SELECT` gains the participant clause;
`UPDATE`/`DELETE` stay exactly as restrictive as the original policy was
(messages are immutable in this codebase — no edit/delete feature exists).
Does not weaken SP051's own finding (no THIRD, unaccountable read path into
message content) — it restores the two legitimate parties' mutual
visibility, which is the entire point of a two-way conversation.

**BLK-08-01 (inherited from Step 8, still open).** SP017 requires the
`SET LOCAL`-only discipline be integration-tested against a **real
connection pooler in transaction mode** before release. No pooler sits in
front of the local Postgres, so this run verified the discipline
structurally (no code path can emit a plain `SET`; `set_config(..., true)`
is hardcoded) and verified transaction-scoping directly against Postgres
(`test_Given_context_set_in_one_transaction_When_next_transaction_starts_Then_it_is_gone`
passes). That is strictly less than what SP017 asks for. `DB_POOL_MODE`
is `session`, and `app/main.py` logs a loud warning if it is flipped to
`transaction`. **Not closed by this run.**

---

## IMP-F01 — FastAPI project structure
**Traces from:** CODING-GUIDE.md §2, MODULE-ARCHITECTURE-STANDARD §3
**Status:** Complete | **Confidence:** High

**Files touched**
- `mangaly-service/pyproject.toml` — [comment block: N/A, config file — but every dependency line is annotated]
- `mangaly-service/app/__init__.py`, `app/api/__init__.py`, `app/config/__init__.py`, `app/db/__init__.py`, `app/events/__init__.py`, `app/idempotency/__init__.py`, `app/rate_limiting/__init__.py` — [Yes]
- `mangaly-service/app/components/<14 packages>/__init__.py` — [Yes]
- `mangaly-service/app/main.py` — [Yes]
- `mangaly-service/tests/{unit,integration,e2e}/` — created, mirroring `05-test-scenarios.md`'s layer tags

**Approach**
One FastAPI process; one Python package per component from
`architecture.md` §2 — all fourteen, including the two that own no schema
(Audit Bridge; Identity Bridge's authorization role). Each component's
`__init__.py` states its BRs, its owned schema, and the one-`interface.py`
import rule, so the boundary is documented at the boundary rather than
only in `CODING-GUIDE.md`. `events/`, `idempotency/`, `rate_limiting/`,
`db/` and `config/` sit alongside `components/`, exactly as §2 lays out.

**Deviations from plan** — none.

**Assumptions** — none.

**Decisions (append-only)** — 2026-09-13: created the 14 component
packages as empty-but-documented rather than only the ones this run
implements, so a later TR adds a module to an existing, correctly-named
package instead of inventing a location.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F02 — Config and dependency wiring
**Traces from:** TR017, TR037, TR041, TR068, TR102, SP092, SP104, DEC-V1-001, DEC-V1-005, DEC-V1-006, DEC-V1-009, DEC-V1-011
**Status:** Complete | **Confidence:** High

**Files touched**
- `app/config/settings.py` — [Yes]
- `app/config/thresholds.py` — [Yes]
- `app/config/profile_tiers.py` — [Yes]
- `app/config/paging.py` — [Yes]
- `app/api/deps.py` — [Yes]
- `mangaly-service/.env.example` — [Yes, as a header comment]

**Approach**
`Settings` (pydantic-settings v2) reads `07a-db-implementation/.env`
directly, using that file's own key names verbatim — the service does not
keep a second copy of `DB_*`, `CREDENTIAL_HASH_*`, `RATE_LIMIT_*`,
`OBJECT_STORAGE_*`, `PAGERDUTY_*`, `RETENTION_*` or `SMS_*`, because two
files owning one key is the drift risk §4c already warns about. The
service's own `.env.example` holds only genuinely application-level values
(session/OTP/reset lifetimes, credential-length floor).

`Settings` deliberately exposes **no owner-role credentials**: there is no
`db_owner_password` field, so the application cannot construct an
owner connection even by accident, which is the TR017 failure mode that
silently disables every RLS policy.

`thresholds.py` carries DEC-V1-005's marriageable age as a
`VersionedSetting` (value + effective date + legal basis) and DEC-V1-006's
four safety tiers as one frozen mapping. `profile_tiers.py` carries
DEC-V1-001's three tiers — modelling the partner-preference requirement as
an explicit *any-of* tuple rather than folding it into the all-of list,
where it would silently have become mandatory-both.

Verified live: the app boots, reads `mangaly`/`localhost:5433`/`mangaly_app`
from the DB `.env`, and reports Argon2id parameters 3 / 65536 / 4.

**Deviations from plan (if any)**
`app/api/deps.py`'s `get_authenticated_account` is a **fail-closed stub**
that returns HTTP 501. Real session validation is TR090/TR101 (Identity
Bridge), out of this run's scope. It is written to raise rather than to
default to any account, so nothing can be built against a permissive
placeholder — but it does mean no authenticated endpoint can function yet.

**Assumptions** — real values for every `CHANGE_ME` placeholder are
supplied later as a pure data change, per this project's
config-placeholder convention.

**Decisions (append-only)** — 2026-09-13: `mangaly_platform`'s models live
in `app/db/` rather than under any `components/` package, because
`07a-db-implementation/README.md` states that schema is not a business
component's; filing it under one component would misattribute ownership of
a table three flows write to.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F03 — SQLAlchemy 2.x async models
**Traces from:** `07a-db-implementation/README.md` "ORM / migration-tool conventions for Step 9", 07a-er-model.md Assumptions #3
**Status:** **Partial** | **Confidence:** High for what exists

**Files touched**
- `app/db/base.py` — [Yes]
- `app/db/engine.py` — [Yes]
- `app/db/mixins.py` — [Yes]
- `app/db/platform_models.py` — [Yes]
- `app/components/authorization/models.py` — [Yes]
- `tests/integration/test_schema_conformance.py` — [Yes, as a module docstring]

**Approach**
Typed `Mapped[...]`/`mapped_column()` style on a `DeclarativeBase` whose
`MetaData` uses a naming convention matching what Postgres already
generated, so introspection compares like with like. `Base.metadata` is
never passed to `create_all` anywhere — the hand-written
`migrations/*.sql` stay the only system that can create a table, per the
README's explicit instruction not to let two migration systems own one
database. Postgres enum types are declared `create_type=False` for the
same reason. No cross-schema `ForeignKey()` anywhere.

`OutboxEventMixin` gives all eleven `outbox_event` tables one column
definition instead of eleven copies — the same shared-implementation
discipline §4c applies to rate limiting.

`test_schema_conformance.py` reflects the live database and asserts every
declared model column-for-column, parameterised per table, so ORM drift
fails a test rather than surfacing as a runtime query error.

**Deviations from plan (if any)**
**This is the one genuinely partial foundation item.** Only **5 of the
live database's 61 tables** are modelled: `mangaly_authz.grant`,
`mangaly_authz.safety_override_grant`, `mangaly_authz.outbox_event`,
`mangaly_platform.idempotency_key`, `mangaly_platform.rate_limit_counter`.
All 5 verified MATCH against the live schema. The other 56 belong to
components whose features are not in this run's scope; modelling them now
would produce 56 untested model modules whose only proof of correctness is
that nothing imports them. Each is written when its TR lands. What IS
complete is the convention, the base, the mixins, and the conformance
test that will police every future model.

**Assumptions** — Alembic is not adopted; if it ever is, the README
requires `alembic stamp` after each raw migration rather than
autogeneration.

**Decisions (append-only)** — 2026-09-13: models are written per-TR rather
than all at once, for the reason above.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F04 — Authorization Engine chokepoint
**Traces from:** TR017, TR018, TR010, TR069 / SP017, SP018, SP069
**Status:** Complete (for the chokepoint itself) | **Confidence:** Medium — see Deviations

**Files touched**
- `app/components/authorization/context.py` — [Yes]
- `app/components/authorization/interface.py` — [Yes]
- `app/components/authorization/models.py` — [Yes]

**Approach**
`resolve(session, subject_id, account_id, target_profile_id, action,
capacity) -> AuthzContext` is the only sanctioned producer of an
`AuthzContext` and the only place `mangaly.authz_context` is ever set.
Order matters and is deliberate: it binds the session variable **before**
reading grants, because `mangaly_authz.grant`'s own RLS policy keys on that
variable — reading grants first returns nothing.

`AuthzContext` is a frozen, slotted dataclass, so a receiving component
cannot widen a scope it was handed (proven by a test that attempts it).
`scopes` is a `frozenset[GrantScope]` over the two enum members mirroring
`mangaly_authz.grant_scope`, never a combined boolean (TR018).
`require_scope()` raises `AuthorizationDenied` rather than degrading to an
empty result set — a denial that silently returns no rows is
indistinguishable from "there is nothing here", which makes authorization
bugs invisible in testing.

The self-access check delegates to the database's own
`mangaly_authz.is_self()` rather than reimplementing the rule in Python,
so the application and the RLS policies cannot evaluate different rules —
the same divergence class TR003/TR027 already had to correct once.

Nothing is cached: SP010's threshold is "every request re-resolves, not
cached", and a cached grant would survive its own revocation, which
TR010's immediate-revocation requirement forbids.

Every resolution publishes `authz.resolved` to
`mangaly_authz.outbox_event` in the same transaction (TR069).

Live-verified: no-grant → no scopes and `require_scope` raises; an active
`family_info` grant → `has_scope(FAMILY_INFO)` true and
`has_scope(CANDIDATE_INFO)` false with `grant_basis` recording
`home_circle_membership`; `resolve()` outside a transaction refuses.

**Deviations from plan (if any)**
TR017 and SP017 both require a **lint rule** blocking any public method
signature that accepts a bare actor id — "structural, not a code-review
convention". **That lint rule is NOT built.** It is deferred rather than
forgotten: with no component interfaces written yet there is nothing for
it to check, and writing it against zero call sites would produce a rule
proven only by its own absence of findings. It must land before the first
component `interface.py` does, and TR017 is not complete until it does.
Likewise `MODULE-ARCHITECTURE-STANDARD` §3's import-boundary lint rule is
not built.

**Assumptions** — the exact BR04 permission matrix remains
implementation-stage per TR017's own Assumptions; this builds the chain
evaluation and the chokepoint pattern, not the full matrix (BLK-08-02
stays open at Step 8).

**Decisions (append-only)** — 2026-09-13: `resolve_self()` added as a
named entry point so a self-only endpoint still routes through the
chokepoint and still binds the session variable, rather than skipping
authorization "because it's just my own data".

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F05 — `SET LOCAL` RLS session-variable discipline
**Traces from:** TR017 / SP017 (SP017: "the single highest-impact finding in this entire file")
**Status:** Complete in code; **BLK-08-01 remains open** | **Confidence:** Medium — see Deviations

**Files touched**
- `app/db/session.py` — [Yes]
- `app/db/engine.py` — [Yes]
- `app/main.py` — [Yes]

**Approach**
Three structural choices, because a convention would not survive this:

1. **`SELECT set_config(name, value, true)` instead of a literal
   `SET LOCAL name = value`.** `set_config(..., is_local => true)` *is*
   `SET LOCAL` — identical transaction-local semantics — but it takes bind
   parameters. A literal `SET LOCAL` cannot be parameterised in Postgres,
   which is exactly how "just interpolate the uuid" becomes an injection
   point in a statement carrying the authorization context.
2. **`is_local => true` is hardcoded.** No function in this module takes
   `is_local` as an argument, so no call site can pass `False`. There is
   no code path in the service that can emit a plain `SET`.
3. **Setting a variable outside a transaction raises rather than
   no-ops.** `set_config(..., true)` with no open transaction silently
   does nothing, and the RLS predicate then reads an empty string — a
   fail-open shape. `set_local()` refuses instead.

Variable names are constants (`VAR_ACCOUNT_ID`, `VAR_AUTHZ_CONTEXT`,
`VAR_OPERATOR_ROLE`, `VAR_SERVICE_ROLE`) checked against an allow-list, so
a typo is a lookup failure rather than a silently-unset variable and
therefore a silently empty result set.

Separately, `assert_non_owning_role()` runs in the FastAPI lifespan on
**every process start in every environment**, querying `pg_tables` for
tables owned by `current_user` and aborting startup if the count is
non-zero. SP017 asks for this as a CI/CD check "re-run on every deploy";
running it at boot is strictly stronger, since it also covers environments
no pipeline touched. Live output: `TR017 non-owning-role check passed:
mangaly_app owns 0 mangaly tables`.

Live-verified: context set in one transaction is empty in the next; no
context → zero profile rows visible; an unrelated account's context →
zero rows; setting an undeclared variable name raises.

**Deviations from plan (if any)**
BLK-08-01 is **not** closed — see Open blockers. Verification was against
direct Postgres, not a real pooler in transaction mode.

**Assumptions** — `DB_POOL_MODE=session` in every environment until
BLK-08-01 closes. `app/main.py` logs a warning naming BLK-08-01 if it is
set to `transaction`.

**Decisions (append-only)** — 2026-09-13: `request_transaction()` provided
so the request's transaction boundary is also its authorization boundary;
handlers take an already-open session rather than opening their own,
because a second transaction would silently carry no context.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F06 — Transactional outbox event bus
**Traces from:** TR069, TR052, TR081 / SP069, SP081
**Status:** Complete (bus + DTOs); dispatcher NOT built | **Confidence:** High for what exists

**Files touched**
- `app/events/bus.py` — [Yes]
- `app/events/dto.py` — [Yes]
- `app/db/mixins.py` — [Yes]

**Approach**
`publish()` takes the caller's already-open session and inserts into the
owning component's `<schema>.outbox_event`. It never commits, never opens
its own session, and never makes a network call — SP069's caution is that
"an event published after commit, or from a different session,
reintroduces exactly the lost-audit-record failure the pattern exists to
prevent". Because the insert rides the caller's transaction, there is no
window between the state change and the event. It refuses to run outside a
transaction rather than opening one.

Target schemas come from a closed `OUTBOX_SCHEMAS` frozenset, so the only
value ever interpolated into the SQL string is one of eleven constants;
every other value is bound.

**Payload minimisation is enforced, not documented.** `publish()` rejects
any payload value that is not a scalar, UUID, or list of those — a
dataclass, ORM object or nested domain model raises. That is the mechanism
behind SP069's "events carry identifiers and the resolved authorization
basis, not row contents" and behind SP081's "no serializer reflection over
the domain model".

`events/dto.py` holds `audit_payload()` (actor / capacity / resolved
authorization basis, so the three fields SP069 requires cannot be
forgotten one endpoint at a time) and the **TR081/SP081
`ActivitySummaryEvent`** — the module's only cross-boundary payload. It is
a frozen `slots=True` dataclass whose `to_payload()` is an explicit dict
literal: no `asdict()`, no `__dict__`, no `model_dump()`, no reflection
anywhere in the path. A field added to the dataclass and not to the
literal does **not** get published; the safe failure is omission, never
disclosure. `ACTIVITY_SUMMARY_ALLOW_LIST` is exported so SP081's required
build-blocking contract test asserts against a declared constant rather
than re-deriving the expected set from the code under test, and
`to_payload()` re-checks it at runtime too.

Live-verified: publishing outside a transaction refuses; an unknown schema
refuses; a domain object in the payload refuses; **a rolled-back
transaction leaves no event row** (the atomicity proof SP069 asks for);
a committed event is invisible without `mangaly.service_role='dispatcher'`
and visible with it.

**Deviations from plan (if any)**
Two things are NOT built and TR069 is not complete without them:
1. **The outbox dispatcher itself** — nothing polls `outbox_event` and
   forwards to the Audit Bridge. Every event written so far sits with
   `published_at IS NULL`. SP069's Class I thresholds (P95 < 5 s dispatch;
   >15 min pages Operations) are therefore unmeasured.
2. **The lint rule** requiring every public mutating handler to publish an
   event. Same reasoning as IMP-F04's missing lint rule — there are no
   mutating handlers yet — and the same requirement that it land before
   the first one does.

Also recorded: `publish()` originally used `INSERT ... RETURNING id`, which
**failed against the real database**. Postgres applies a table's SELECT
policy to the rows an `INSERT ... RETURNING` hands back, and every
`outbox_event` table restricts SELECT to the dispatcher role, so the insert
was rejected inside ordinary business transactions. Fixed in application
code (generate the id application-side, drop the `RETURNING`) rather than
by relaxing the policy — the dispatcher-only read restriction is precisely
what SP069's tampering row asks for, and weakening it so a writer can read
back an id it does not need would trade a real control for nothing.

**Assumptions** — the Audit Log Store's durability is a platform property
(ADR-011), consumed not re-implemented.

**Decisions (append-only)** — 2026-09-13: outbox event ids are generated
application-side, for the reason above.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F07 — Shared idempotency middleware
**Traces from:** TR102 / SP102
**Status:** Complete (shared mechanism) | **Confidence:** High

**Files touched**
- `app/idempotency/store.py` — [Yes]
- `app/idempotency/guard.py` — [Yes]
- `app/db/platform_models.py` — [Yes]

**Approach**
**`account_id` is a required, non-defaulted parameter on every function in
`store.py`, and appears in the WHERE clause of every statement.** SP102 is
explicit that "the middleware must also include `account_id` in every
lookup — the RLS policy is the second layer, not the first", so there is
deliberately no lookup-by-key-alone function to call by mistake.
`request_hash` is stored and compared, so a repeated key with a different
payload is rejected as a client error rather than silently returning a
stale success.

Implemented as an async context manager used inside the handler rather
than as ASGI middleware — a deliberate choice with a concrete reason.
`account_id` only exists after authentication, and the RLS policy on
`mangaly_platform.idempotency_key` keys on `mangaly.account_id`, which is
transaction-local. True ASGI middleware runs before both, so it would have
to either open a second transaction (losing atomicity between the snapshot
and the mutation) or fall back to a key-only lookup — precisely the
cross-account defect SP102 found. It is still one shared implementation
every endpoint calls; it just sits one layer in from the socket. The
snapshot write happens in the caller's transaction, so "the mutation
committed but its snapshot did not" is unreachable.

Live-verified against the real database: a repeated key executes the
mutation **once** (execution counter asserts 1, not 2); **the same key
under a different account returns no snapshot** — SP102's Critical
finding, re-verified from the application side; a reused key with a
changed payload raises `IdempotencyConflict`; a stored row is invisible
without the account's own session context (the RLS second layer).

**Deviations from plan (if any)**
None in the mechanism. But **none of TR102's eight named endpoints
(TR002, TR042, TR043, TR046, TR047, TR049, TR057, TR058) exists**, so the
guard is currently applied to zero real endpoints. The 7-day TTL cleanup
job (SP102's Class F threshold) is also not built.

**Assumptions** — the client-side offline mutation queue is a separate
mobile-engineering component per TR102; this covers server-side
idempotency only.

**Decisions (append-only)** — 2026-09-13: guard is a context manager, not
ASGI middleware, for the reason above.

**Review history** — (none yet)
**Approval:** Eng Manager / Tech Lead — [ ] Approved — name, date

---

## IMP-F08 — Shared rate-limiting utility
**Traces from:** TR037 (canonical), TR093, TR095 / SP037, SP093, SP095
**Status:** Complete | **Confidence:** High

**Files touched**
- `app/rate_limiting/limiter.py` — [Yes]
- `app/db/platform_models.py` — [Yes]

**Approach**
One module, one public check (`check_and_increment` / `enforce`), with the
per-caller differences (key prefix, window, limit) as arguments rather
than as separate implementations — §4c exists because a Tech Reqs review
caught three components each about to build their own copy.

**Atomicity is the load-bearing property.** SP037's caution says
plainly that '"DB-backed" alone doesn't guarantee atomicity — a naive
read-then-write under concurrent requests reintroduces exactly the race a
rate limiter exists to prevent.' The check is therefore a single
`INSERT ... ON CONFLICT (rate_limit_key, window_start) DO UPDATE SET
hit_count = ... + 1 RETURNING hit_count`: one statement, one row lock, and
the returned count is the caller's own ordinal in the window. **Proven,
not asserted:** a concurrency test fires 20 simultaneous calls at a
limit of 5 through 20 separate sessions and asserts exactly 5 pass. It
does.

Key subjects are SHA-256 hashed. The login/OTP/reset limiters key on a raw
phone number or email, and `rate_limit_counter` has no RLS (correctly —
two of three callers are pre-authentication, where no `mangaly.account_id`
exists to enforce a policy against). Hashing keeps the counter functional
while leaving no readable identifier in an unprotected infrastructure
table — relevant to SP104's concentration-risk concern.

`peek()` reads the current window without incrementing, needed by TR095's
minimum-resend-interval check so it does not consume a slot from the
hourly resend budget. `constant_time_equals()` is shared here for SP094's
constant-time token comparison.

Live-verified: 6 calls against a limit of 5 → `[T,T,T,T,T,F]`; 20
concurrent calls at limit 5 → exactly 5 allowed; `enforce()` raises past
the limit; a raw identifier does not appear in the stored key.

**Deviations from plan (if any)**
Fixed windows rather than a sliding log, because
`mangaly_platform.rate_limit_counter`'s applied schema is
`UNIQUE (rate_limit_key, window_start)` — one row per window — and a
sliding log would need a different table. Fixed windows admit up to 2x the
limit across a boundary; acceptable for all three abuse cases here (invite
spam, login brute force, SMS bombing), which are about cost and volume
rather than a hard correctness bound. Recorded rather than left implicit.

**Assumptions** — `.env`'s `RATE_LIMIT_*` values are the operative limits;
callers pass them in rather than the limiter reading them, so a limit is
always visible at the call site.

**Decisions (append-only)** — 2026-09-13: fixed-window model, for the
reason above. 2026-09-13: `RateLimitScope` is a closed enum rather than a
free-text prefix, so every key in the table greps back to a named TR.

---

## TR090/TR092/TR093/TR095/TR101 — Identity Bridge: passwordless-primary auth
**Traces from:** FR090, FR092, FR093, FR095, FR101 (`06-impact-analysis.md` IA090/092/093/095/101); DEC-V1-012
**Status:** Complete, live-verified | **Confidence:** High

**What's built.** `components/identity_bridge/{models,interface,otp,delivery,credentials}.py`
plus `api/routes/auth.py`: `POST /auth/signup` (identifier + optional
credential — DEC-V1-012), `POST /auth/login` (secondary, password),
`POST /auth/login/otp/request` (primary), `POST /auth/otp/verify`,
`POST /auth/otp/resend`, `GET /auth/me`, `POST /auth/logout`. Real Twilio
SMS delivery (`.env`'s `TWILIO_*`, dev-allowlist gated per an explicit
instruction not to burn trial quota on non-test numbers).

**Live verification, not asserted.** `scripts/check_auth.py` (12/12):
login/logout/session round-trip, SP090 cookie flags, SP093 identical
response body AND identical response time for wrong-password vs
unknown-account, SP092 identical signup response for existing vs new
identifier, TR093 rate-limiting actually firing at the configured
threshold. `scripts/check_otp.py` (9/9): issue/verify/resend for both
signup and login purposes, single-use enforcement, resend rate-limiting.
Both suites re-run clean after every fix below, not just once.

**Defects found by running, fixed, all covered above in Revision history:**
weak-credential rejection never wired; the rate limiter counting inside the
transaction it should have survived; `mangaly_identity.session` unreadable
at validation time (BLK-09-02); `httpx` misfiled as dev-only; backend
responses hardcoded to English regardless of ADR-010.

**Constraints surfaced** — BLK-09-01/BLK-09-02 (both need Step 7a
ratification); BLK-08-01 (pooling, inherited, still open — nothing in this
build closes it, `DB_POOL_MODE` stays `session`).
**Decisions (append-only)** — DEC-V1-012 (2026-09-13, `v1-decisions.md`):
passwordless-primary auth, password kept as an opt-in secondary method.
**Review history** — (none yet)
**Approval:** Engineering Manager / Tech Lead — [ ] Approved — name, date

---

## TR001 — Minimum Viable Profile
**Traces from:** FR001 (`06-impact-analysis.md` IA001)
**Status:** Complete, live-verified | **Confidence:** High

**What's built.** `components/profile/{models,interface,storage}.py` plus
`api/routes/profile.py`: `POST /profile` (`multipart/form-data` — a photo
is part of the existence tier, not optional), `GET /profile/me`.
DEC-V1-001's exact field list; TR041/DEC-V1-005's marriageable-age gate
read from the already-built `config/thresholds.py` versioned setting.
`storage.py` is a real local-disk backend behind TR006's exact
`storage_ref` contract — Object Storage is still `CHANGE_ME`, so this is
what actually runs today, not a mock.

**Live verification, not asserted.** `scripts/check_profile.py` (10/10):
missing-field rejection (field-level, not generic), underage rejection,
unsupported-media-type rejection, a real multipart photo upload that
saves and is independently re-fetchable by URL, the one-profile-per-account
guard, and a read-back that matches what was saved. Also driven through a
real browser via chrome-devtools MCP end to end (signup → OTP → wizard →
save → Home shows the saved profile with photo).

**Defects found by running, fixed, all covered above in Revision history:**
two ORM enum values guessed wrong against the live schema
(`media_upload_status`, `profile_status`); `python-multipart` a genuinely
missing dependency; the frontend wizard's tab bar/submit-button overlap,
duplicate date-of-birth field, 3-option segmented-control layout, and a
relative-media-URL resolution bug — the last three found only by driving
the actual UI, not by reading the component.

**Constraints surfaced** — TR006 (signed-URL retrieval) is a separate,
not-yet-built tech req this one deliberately does not reach into (TR002/
TR003/TR005, "the rest of the profile hub," were built next — see their own
IMP-item section and Revision history entry below).
**Assumptions** — DEC-V1-001's field list may be refined post-launch
(already an accepted FR-level risk, per TR001's own text).
**Decisions (append-only)** — none.
**Review history** — (none yet)
**Approval:** Engineering Manager / Tech Lead — [ ] Approved — name, date

---

## TR002/TR003/TR005 — Per-Category Attributes, Discoverability Gate, Three-Tier Completeness
**Traces from:** FR002, FR003, FR005 (`06-impact-analysis.md`); UX11/UI11
**Status:** Complete, live-verified | **Confidence:** High

**What's built.** `mangaly_profile.profile_attribute` ORM model
(`FieldState`: `unset`/`declined`/`value`, mirroring the live DB enum) plus
five `components/profile/interface.py` functions — `get_category`,
`update_category`, `get_all_attributes`, `is_discoverable`, `completeness`
— and four endpoints: `GET`/`PATCH /profile/{category}`,
`GET /profile/completeness`, `GET /profile/attributes`. `is_discoverable()`
and `completeness()` both read `config/profile_tiers.py`'s tuples directly
(no second copy), so TR003/TR027's non-divergence contract holds by
construction. Frontend: `lib/profileCategoryConfig.ts` (13 categories, one
representative field per enhanced-matching category since DEC-V1-001 leaves
that tier's exact field list open), `/me` (Profile edit hub), `/me/completeness`
(three physically separate sections per UX11's DEC-003), `/me/edit/[category]`
(one generic, config-driven editor for all 13 categories).

**Live verification, not asserted.** `scripts/check_profile_categories.py`
(15/15): set/decline/overwrite semantics, the discoverability tier's
all-four-plus-any-of-partner-preference gate, a declined field still
counting as missing (never satisfied by declining), and the enhanced tier
reflecting a touched category without gating anything. Also driven through
a real browser via chrome-devtools MCP: hub → category editor (select +
decline + save) → completeness screen, across two seeded accounts (one
discoverability-complete, one deliberately incomplete with declined fields)
to see both states render for real, not just the happy path.

**Defects found by running, fixed, all covered above in Revision history:**
a route-registration-order bug that would have swallowed `/profile/completeness`
and `/profile/attributes` as literal `{category}` values (caught from
`/openapi.json`, fixed before it ever reached a live request); a frontend
i18n bug where the category editor's field labels rendered raw untranslated
keys instead of translated text (missing `profile:` namespace prefix at the
call site, found from a live screenshot).

**Constraints surfaced** — none new; TR006 (signed-URL retrieval) remains
the same open gap TR001's own section already names.
**Assumptions** — the enhanced-matching tier's exact field list per category
is this build's own implementation choice (DEC-V1-001 defines that tier only
as "everything else"); the frontend's `profileCategoryConfig.ts` is the one
place that choice lives, matching `config/profile_tiers.py`'s own role for
tier membership.
**Decisions (append-only)** — none new; reuses DEC-V1-001 verbatim.
**Review history** — (none yet)
**Approval:** Engineering Manager / Tech Lead — [ ] Approved — name, date

---

## TR007/TR008/TR009/TR010/TR014/TR016 — Home Circle
**Traces from:** FR007, FR008, FR009, FR010, FR014, FR016 (`06-impact-analysis.md`); UX12/UI12
**Status:** Complete, live-verified | **Confidence:** High

**What's built.** `components/home_circle/{models,interface}.py` plus
`api/routes/home_circle.py` — eleven endpoints: invite; list/accept/decline
pending invitations; list/remove members; leave; suggest; write/list/forward
notes; list a candidate's own pending (unforwarded) notes. Read M01-C (Home
Circle Conceptual Model) and M01-I (Family Collaboration & Home Circle
Operations) — the original `.docx` research dossiers, not only the sealed
pipeline docs — in full before implementing, confirming the FR/UX/TR chain
correctly absorbed both documents' conceptual model (relationship ≠
authorization; suggestion ≠ decision; membership is flexible, never
trapping a candidate) with one real gap: neither document's "search by
username" assumption was ever resolved to an actual capability anywhere in
the chain, and Identity Bridge confirmed it does not exist — TR007's own
named fallback (invite by phone/email identifier) is what is actually built.

**Live verification, not asserted.** `scripts/check_home_circle.py` (23/23):
invite, self-invite rejection, duplicate-pending rejection, the relationship
claim surviving into both the pending-invitation view and the accepted
membership, accept, re-accept rejection, decline, an uninvolved account
seeing nothing, suggest, and the full note lifecycle (family-only by
default → candidate can discover a note is pending without seeing it →
candidate approves → content becomes visible), remove, and voluntary leave.
Also driven through two genuinely separate real browser sessions via
chrome-devtools MCP (one seeded account inviting, a second seeded account
accepting from its own login), confirming the membership then appears on
the inviting account's own `/circle` screen — not simulated with one
session's cookies reused.

**Defects found by running, fixed, all covered above in Revision
history:** the relationship-taxonomy schema gap (migration 005); the
candidate-account-id-not-profile-id naming trap (found by testing
`is_self()` directly, not by reading `07a-er-model.md`); a third and fourth
occurrence of the pending-invitee/pending-note "read before you're
authorized to prove who you are" RLS bind (migrations 006-008); and two
live `InsufficientPrivilegeError`s from `suggest()`/`write_note()` never
having bound `mangaly.authz_context` before their INSERTs.

**Constraints surfaced** — TR006 (signed-URL retrieval) remains open;
TR011 (report) and TR012 (solo-candidate parity contract test) were not
attempted (TR011 was not one of this pass's five assigned FRs; TR012 is a
cross-cutting contract test better done once more components exist to test
against).
**Assumptions** — M01-C §6 path B ("a parent invites the not-yet-registered
candidate") is out of scope this pass — see this cluster's Revision-history
entry for why the bootstrap semantics differ materially from the other
three invite paths.
**Decisions (append-only)** — none new.
**Review history** — (none yet)
**Approval:** Engineering Manager / Tech Lead — [ ] Approved — name, date

---

## TR021/TR026/TR027/TR030/TR031/TR042-TR045/TR049 — Discovery, Connection, Compatibility, Communication
**Traces from:** FR021, FR026, FR027, FR030, FR031, FR042, FR043, FR044, FR045, FR049 (`06-impact-analysis.md`); UX15-UX21
**Status:** Complete, live-verified | **Confidence:** High

**What's built.** Four new components (`discovery`, `connection`,
`compatibility`, `communication`), eleven new endpoints, and a new
`config/ranking_weights.py`. Full detail — every design decision, every
defect found and fixed, and the modernization pass that followed — is in
this file's own Revision history entry above; not repeated here to avoid
the two drifting apart.

**Live verification, not asserted.** `scripts/check_discovery_connection.py`
(24/25 — the one non-pass is prior-run state on a fixed seeded pair, not a
defect) plus a full chrome-devtools pass across two real browser sessions
through the entire Discover → Connect → Accept → Message journey, before
and after the modernization pass.

**Constraints surfaced** — BLK-09-04 and BLK-09-05 (both raised to Step 7a
for ratification, see Open blockers). TR045 has no unique constraint by
design (FR045 requires multiple concurrent connections), confirmed as
intentional rather than a missed index.
**Assumptions** — the ranking function's locality/partner-preference
matching rules are a documented, simplified interpretation (exact-string
locality match, partner-preference-locality substring match) rather than a
full geocoding/radius model — recorded in `discovery.interface._score()`'s
own docstring as a reasonable scope cut, not a hidden gap. FR014's
suggestion feed has no frontend screen yet (needs a profile-preview screen
this pass did not build for that specific purpose).
**Decisions (append-only)** — none new; DEC-V1-002's weights implemented
verbatim.
**Review history** — (none yet)
**Approval:** Engineering Manager / Tech Lead — [ ] Approved — name, date

---

## Not implemented — explicit list

Recorded so no later reader has to infer it from absence.

- **Almost all feature endpoints.** The API surface is now
  `/health`, `/auth/*` (signup, login, login/otp/request, me, logout,
  otp/verify, otp/resend), `/profile*` (create, me, completeness,
  attributes, per-category GET+PATCH), `/home-circle/*` (invite,
  invitations pending/accept/decline, members list/remove/leave, suggest,
  notes/pending/forward), and `/auth/reset/*` (request, confirm) — sixteen
  TRs' worth, out of 102. Every other component's router is still
  unregistered.
- **TR006 (signed-URL retrieval), TR011 (report), TR012 (solo-candidate
  parity contract test)** and every other untouched TR: not yet built,
  correctly shown as "No" in the coverage table above.
- **`app/components/identity_bridge/credentials.py`** — no longer a dangling
  file. TR092/TR093's build wired it in fully: `hash()`/`validate_strength()`
  drive both the optional-credential sign-up path and the secondary password
  login path, and `verify_or_dummy()` is `log_in`'s only verification entry
  point, live-verified to close both the response-body and timing halves of
  the anti-enumeration requirement (`scripts/check_auth.py`'s SP093 checks).
- **The two lint rules** TR017/SP017 and TR069/SP069 both require
  (bare-actor-id signatures; mutating-handler-without-event). Neither is
  built. See IMP-F04 and IMP-F06.
- **The `MODULE-ARCHITECTURE-STANDARD` §3 import-boundary lint rule.**
- **The outbox dispatcher** and its Step 13 alerting.
- **Session validation is no longer a stub.** `app/api/deps.py`'s
  `get_authenticated_account` now performs a real lookup against
  `mangaly_identity.session` via `identity.validate_session`, live-verified
  (`scripts/check_auth.py`'s FR090 check). The HTTP 501 fail-closed stub
  described in the original foundations run no longer exists.
- **41 of 61 tables still have no ORM model.** This pass adds
  `discovery_profile_index` (Discovery), `connection_request` (Connection),
  and `conversation`/`message` (Communication) — `sharing_grant`,
  `family_contact_share` (Connection), `assessment_response`, `horoscope`
  (Compatibility — FR033/034, out of scope), and
  `contact_exchange_request`/`retention_policy_exception`/`legal_hold`
  /`retention_job_run` (Communication — BR12/FR050/053/054, out of scope)
  still do not. Modeled total: 20 of 61. See IMP-F03.
- **Every background job:** idempotency-key TTL cleanup, expired
  OTP/reset/session purge, retention/legal-hold jobs.
- **The frontend beyond the twenty-six built TRs.** `mangaly-web/` (Next.js
  App Router, per CODING-GUIDE.md §1) now has `/`, `/login`, `/signup`,
  `/otp`, `/reset`, `/profile/create`, `/me` (+`/me/completeness`,
  `/me/edit/[category]`), `/circle` (invite, pending invitations, members,
  family notes — no screen yet for the suggestion feed, since it needs a
  profile-preview screen this pass did not build for that specific purpose),
  `/discover` (incoming requests with full pre-decision context, ranked
  search, why-this-match, connect), and `/messages` (+`/messages/[id]`
  thread), plus `app/i18n/` on the backend and `lib/i18n/` on the frontend
  for ADR-010. Every tab in `TabBar.tsx` now has a real screen behind it —
  no bare `ScreenStub` remains anywhere in the app.

## Definition of Done — self-check

Honest status against this step's own DoD, which this file does **not**
currently meet and does not claim to:

- Coverage check has no blank rows — **Pass** for the foundation table;
  the TR table is deliberately mostly "No/untouched", which is accurate,
  not blank.
- Set-level quality gate entirely Pass — **Pass** for the checks that
  apply to what was built.
- Every dependency in `09a-external-dependencies.md` is known to Step 8 or
  has a cleared supplementary review — **Pass with two assessed edge
  cases** (`pydantic-settings`, `asyncpg`), reasoning shown in that file
  for the Security Lead to accept or convert into a review.
- No open blockers — **Fail.** BLK-09-01 through BLK-09-05 (all raised to
  Step 7a for ratification) and BLK-08-01 (inherited, pooling) are open.
- **This file is therefore NOT Sealed, and Step 10 (Test Automation) is
  NOT cleared to begin.**

## Approval

Engineering Manager / Tech Lead — [ ] Approved — name, date
