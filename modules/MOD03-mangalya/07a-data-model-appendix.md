# MOD03 Mangalya - Data model appendix (as built 2026-11-22)

**Document status:** generated 2026-11-22 from `07a-db-implementation/migrations/001..066`. Migrations are authoritative; `schema.sql` lags. Linked from `07a-er-model.md`.

## Migration history

| No. | File | Purpose (from file header) |
|---|---|---|
| 001 | `001-initial.sql` | Migration 001 — Initial schema (all 14 Mangaly schemas, first production migration). No prior migration to depend on — this is migration zero. Idempotent: every CREATE SCHEMA/TABLE uses IF NOT EXISTS, every CREATE TYPE is wrapped in a DO bl |
| 002 | `002-idempotency-account-scope.sql` | 002 — Scope the idempotency key uniqueness to the owning account. WHY (Step 8 Security & Performance finding, SP102, 2026-09-13): 001-initial.sql created mangaly_platform.idempotency_key with UNIQUE (idempotency_key, endpoint) while the tab |
| 003 | `003-identity-signup-insert-policy.sql` | 003 — Allow the pre-authentication signup INSERT into mangaly_identity.account. WHY (Step 9 Implementation finding, 2026-09-13, found by running the real signup path against the live database rather than by reading the DDL): 001-initial.sql |
| 004 | `004-session-lookup-function.sql` | 004 — Pre-authorization session lookup function. WHY (Step 9 finding, 2026-09-13, found by running /auth/me against the live database rather than by reading the policy): `session_self_only` restricts mangaly_identity.session to account_id = |
| 005 | `005-home-circle-relationship-type.sql` | 005 — Home Circle relationship taxonomy (fixes forward against Step 7a) [Gap found live, 2026-09-13] FR008's own acceptance criterion requires "acceptance creates a membership record with the relationship claim," and UX12's wireframe requir |
| 006 | `006-home-circle-invitation-response-functions.sql` | 006 — Home Circle invitation-response escape hatches [Third RLS failure mode, found live 2026-09-13 — same class as BLK-09-01/ BLK-09-02, documented generically in /MODULE-ARCHITECTURE-STANDARD.md ss4] `hc_invitation_participants` grants ac |
| 007 | `007-home-circle-pending-notes-function.sql` | 007 — Home Circle: let a candidate discover their own unforwarded notes FR016 requires the candidate's explicit approval BEFORE a note's content becomes visible to them — `hc_note_family_or_forwarded`'s RLS already enforces that half correc |
| 008 | `008-home-circle-approve-note-forward-function.sql` | 008 — Home Circle: let the candidate actually perform the forward-approval Migration 007 let the candidate discover their own pending note ids without exposing content. But approving one hits the same RLS bind: a plain UPDATE on a not-yet-f |
| 009 | `009-profile-lookup-id-by-account-function.sql` | 009 — Connection accept needs the OTHER party's real profile.id [Fourth instance of the third RLS failure mode, found live 2026-09-14 — same class as BLK-09-01/02/03] `connection.interface.accept()` must create a `candidate_info` grant for  |
| 010 | `010-authz-grant-connection-candidate-info-function.sql` | 010 — Connection accept needs a cross-party grant escape hatch [Fifth instance of the third RLS failure mode, found live 2026-09-14 — and a genuinely new sub-case of it] `connection.interface.accept()` must create TWO `candidate_info` grant |
| 011 | `011-communication-message-recipient-read-fix.sql` | 011 — A message's recipient could never read it (real RLS defect, not a pre-authorization chicken-and-egg like the others in this file) [Found live, 2026-09-14] `message_sender_or_safety_case` was a single `FOR ALL` policy: `is_self(sender_ |
| 012 | `012-profile-lookup-account-by-id-function.sql` | 012 — Connection send_request needs the OWNING account of an on-behalf-of profile.id, to check Home Circle authorization [Fifth instance of the third RLS failure mode, found live 2026-09-14 — same class as BLK-09-01/02/03 and migration 009] |
| 013 | `013-profile-media-sort-order.sql` | 013 — Photo ordering for the profile photo grid The profile hub's photo grid (Hinge/Bumble pattern: up to six photos, long-press and drag to reorder) needs a stable, person-chosen order. profile_media previously had only `is_primary`, so ev |
| 014 | `014-platform-identity-link.sql` | 014 — mangaly_identity.account becomes Mangaly's member-link table for the ForKhatri platform identity. WHY (2026-09-14, product-owner decision; binding contract docs/ParentApp/07-tech-reqs.md TR10/TR11/TR15/TR23): ForKhatri is one app with |
| 015 | `015-selective-sharing-per-sharer.sql` | 015 — Selective sharing (FR046/FR047/FR048): one row per sharer, and the value each sharer chose to reveal. WHY (found while implementing TR046, 2026-09-15): * `sharing_grant` had UNIQUE (connection_id, category), so only ONE side of a conn |
| 016 | `016-family-contact-share-consent.sql` | 016 — Family contact sharing needs the family member's own decision (FR048 / TR048). WHY (2026-09-15): * A candidate may ask to share a Home Circle member's phone with a connection, but only that member may say yes. The candidate's session  |
| 017 | `017-home-circle-member-contexts.sql` | 017 — The candidates a family member helps (FR097 context switcher). WHY (2026-09-15): a parent who joins a candidate's Home Circle must be able to switch to "Viewing Ananya's search" and see whose search it is by name. The member can read  |
| 018 | `018-suggestion-candidate-read.sql` | 018 — A candidate can read the suggestions made to them (FR014 / TR014). WHY (found live 2026-09-15, testing with a real parent): Lakshmi Reddy, a Home Circle parent, suggested a profile to her daughter Ananya from Discover. Lakshmi could l |
| 019 | `019-member-display-name.sql` | 019 — A candidate sees who is in their Home Circle by name. WHY (2026-09-15, real test with a parent): Ananya's Members list showed only "Parent" and a date, so she could not tell who had joined. A family member such as her mother Lakshmi h |
| 020 | `020-discover-main-photo.sql` | 020 — Discover shows each candidate's main photo and age (DEC-V1-016). WHY (product-owner decision 2026-09-15): a text-only Discover card gives a member nothing to decide on. The main photo and age of a SEARCHABLE candidate are now visible  |
| 021 | `021-family-contact-ends-with-membership.sql` | 021 — A family contact share ends when its reason ends (FR048 / TR048, FR010), and `is_self` never answers NULL. WHY (2026-09-15): * Found live: a Home Circle member's phone stayed recorded on a connection after the member had left the circ |
| 022 | `022-family-notes-about-a-match.sql` | 022 — Private family notes are about one match, private to their author, and reach the candidate only when the author asks and the candidate agrees (FR016 / TR016, UX13, TS035–TS037). WHY (2026-09-15): * M01-B §12 / M01-I: parents keep priv |
| 023 | `023-on-behalf-request-belongs-to-the-candidate.sql` | 023 — A request a family member sends belongs to the candidate, not to them. WHY (2026-09-17, product owner, acting as a parent): "parents can send a request direct to a profile — understand how shaadi.com works: even if the account is cont |
| 024 | `024-subject-owns-conversation-and-sharing.sql` | 024 — The candidate, not whoever pressed send, is the party to the conversation. WHY (2026-09-17): migration 023 let an authorized family member send a connection request for a candidate. Three policies still decided "are you a party to thi |
| 025 | `025-family-sees-the-whole-circle.sql` | 025 — A family member sees the whole Home Circle, not just themselves. WHY (2026-09-17, product owner, reviewing the parent role): "focus on circle and improve … that contains home circle people always". Acting as a parent, the Circle scree |
| 026 | `026-conversation-opens-on-acceptance.sql` | 026 — An accepted connection opens the private conversation itself, with a system line both people can see (FR043/FR044/FR049). WHY (2026-09-17): * Product owner: "candidate should get private message once any request is successful". Until  |
| 027 | `027-public-biodata-of-a-discoverable-profile.sql` | 027 — A discoverable candidate's biodata is readable by any signed-in member, without their name or contact details (FR021, DEC-V1-016, DEC-V1-020). WHY (2026-09-17): * Product owner: "parents should see details like shaadi.com about other  |
| 028 | `028-either-participant-can-clear-a-thread.sql` | 028 — Either participant can clear their own conversation (FR050, DEC-V1-021). WHY (2026-09-17, found live): `message_delete_sender_or_safety_case` let a member delete only the rows they had sent themselves. Two consequences, both silent: * |
| 029 | `029-voice-introduction.sql` | 029 — A profile can carry a voice introduction (product owner, 2026-09-17). WHY: * The owner asked for "voice input, introduction". `profile_media` already models photos and a (never-built) video introduction; a spoken introduction is the s |
| 030 | `030-roles-per-membership-and-invite-paths.sql` | 030 — Roles are relations to a candidate, held per membership; every account is a full user; a family member may invite a candidate (DEC-V1-022). WHY (2026-09-17, product owner, rework contract §1/§6): * "Roles are relations to a particular |
| 031 | `031-discovery-biodata-columns.sql` | 031 — Discovery index carries the biodata facts the rework filters on. WHY (2026-09-17, rework contract §3): Discover gains height, gotra, sub-community, profession, income band, mother tongue and manglik filters, free-text `q` and three so |
| 032 | `032-shortlist.sql` | 032 — Shortlist, scoped to a context (rework contract §3). WHY (2026-09-17): "Save" on a Discover card keeps a candidate for later. A shortlist belongs to the context it was made in — the candidate's own search, or a circle acting for that  |
| 033 | `033-safety-blocks.sql` | 033 — Blocking (rework contract §3). WHY (2026-09-17): a member may block another; a blocked person vanishes from both sides' Discover, lists and request sending. A block row is private to the blocker (RLS), but the EFFECT has to be visible |
| 034 | `034-notifications.sql` | 034 — In-app notifications, one row per reader, scoped to a context. WHY (2026-09-17, rework contract §3): `GET /notifications?for_candidate=` lists what happened in a context; `POST /notifications/read` marks rows read. `mangaly_notificati |
| 035 | `035-family-conversations.sql` | 035 — Two conversation kinds on a connection: candidate and family (DEC-V1-024, rework contract §2). WHY (2026-09-17): "Messaging is one of only two things that vary by role." * `candidate` — the two candidates only, opened on acceptance (u |
| 036 | `036-connection-on-behalf-and-withdraw.sql` | 036 — A circle sees its candidate's requests; a request can be withdrawn; the recipient learns who pressed send (DEC-V1-022, contract §2). WHY (2026-09-17): * "Family members MAY send a connection request on behalf of their candidate ... th |
| 037 | `037-family-acts-for-candidate.sql` | 037 — A circle member acts for their candidate on acceptance; late-joining members are synced into family conversations (DEC-V1-022/024). WHY (2026-09-17): the contract makes every context-scoped action generic ("everything else works ident |
| 038 | `038-verification-evidence-readable.sql` | 038 — Make verification evidence readable (baseline §13). WHY (2026-09-21): `mangaly_trust.verification_layer_status` has existed since migration 001 and nothing has ever read it, so two problems went unnoticed. 1. Its RLS predicate is `is_ |
| 039 | `039-prompts-are-connected-candidates-only.sql` | 039 — The Hinge-style content is for connected candidates, unless its owner publishes it (product owner, 2026-09-21). WHY: Migration 027 opened a searchable candidate's whole attribute set to any signed-in member, which was right for BIODAT |
| 040 | `040-exact-family-relation.sql` | 040 — Two levels of family relation: the ROLE and the EXACT relation (product owner, 2026-09-21). WHY: The owner, looking at the Home Circle invite: "I am looking for profile relation (mother, father, etc.), while relative is a role and ins |
| 041 | `041-profile-created-for-a-child.sql` | 041 — A parent creates a candidate profile for their son or daughter (product owner, 2026-09-21; DEC-V1-019). WHY: Indian matrimony profiles are very often made by a parent. Shaadi.com's registration asks who the profile is for — Self, Son, |
| 042 | `042-erase-a-profile-made-for-someone.sql` | 042 — Erasing a profile that someone else made for a person (product owner, 2026-09-21; DEC-V1-019). WHY: A parent can create a profile for their son or daughter with the child's mobile number (041). Two cases need it gone: 1. "This isn't m |
| 043 | `043-shown-openly.sql` | 043 — "Shown openly": what a candidate chooses to show before any connection (product owner, 2026-09-22). WHY: The owner: "Few people like to share few things openly! Let them have that." Until now the pre-connection card was fixed for ever |
| 044 | `044-family-chat-and-chat-reports.sql` | 044 — Family chat opened by parents, named people in it, and chat reports that keep their evidence (DEC-V1-024, owner scenario DEC-V1-018). 1. A parent or guardian may open the family conversation for a connection of the candidate they help |
| 045 | `045-face-match-verification.sql` | 045 — Live face match: the outcome, its biometric consent, and withdrawal (DEC-V1-016; the maker gate of DEC-V1-020 / DEC-V1-025). WHAT A FACE MATCH IS HERE: The member's browser captures a live face, runs an active liveness challenge, and  |
| 046 | `046-direct-chat.sql` | 046 — One-to-one chat between people (DEC-V1-026) Owner, 2026-09-22: "we only offer incognito mode chat to candidate, and general chat for individual account like how chat present in Instagram / FB; now that we have option of family chat ke |
| 047 | `047-member-profile.sql` | 047 — Every account has its own Mangaly "My profile" (DEC-V1-027) Owner, 2026-09-22: "basic authentication of login happens in ForKhatri and each module has its own way of my profile." A parent, sibling or relative who is not looking for a  |
| 048 | `048-trust-safety-operations.sql` | 048 — Trust & safety operations: operators, severity classification with a real SLA clock, bounded automated detection, the moderator queue, account suspension and the Tier 3/4 exits (DEC-V1-006, DEC-V1-007, DEC-V1-009, DEC-V1-011, SP063, S |
| 049 | `049-horoscope.sql` | 049 — Kundli matching: one cached chart per account, read in pairs (DEC-V1-029) A family compares the two kundlis before a match goes further. Mangaly computes each person's Moon chart (rashi, nakshatra, Lagna when time and place are known, |
| 050 | `050-daily-pick.sql` | 050 — "Most compatible today": one stable-matching pick per person per day (DEC-V1-030). WHY (2026-09-22): Discover's first row shows ONE person chosen because the two of them fit each other's stated preferences — the result of a daily defe |
| 051 | `051-plans-and-payments.sql` | 051 — Plans, entitlements and payments (DEC-V1-031). WHY (2026-09-22): Mangaly earns its keep the way Shaadi, BharatMatrimony and Jeevansathi do — a free tier that lets anyone browse and send a few requests a day, and paid plans (Gold; Assi |
| 052 | `052-relationship-manager.sql` | 052 — Assisted matching: a named relationship manager (DEC-V1-032) WHY (2026-09-22): BharatMatrimony's Assisted Service gives a family a dedicated relationship manager from their region who speaks their language, shortlists and contacts pro |
| 053 | `053-family-reads-candidate-discovery-row.sql` | 053 — A Home Circle member can read their candidate's own Discovery row. WHY (2026-09-24, functional sweep): Discovery reads the seeker's side — who the candidate is looking for, their gender, their ranking snapshot — from the candidate's o |
| 054 | `054-parents-read-match-sharing.sql` | 054 — A candidate's parents and guardians can READ what the match shared. WHY (owner decision, 2026-09-25): once both sides accept, the parents and guardians in each candidate's Home Circle may see the match's full name, and contact details |
| 055 | `055-horoscope-field-values.sql` | 055 — Horoscope answers as fixed keys (2026-09-27). The editor now offers nakshatra as a pick-list of the 27 (it was free text) and validates horoscope values on save (components/profile/horoscope_fields .py). Earlier free-text nakshatra an |
| 056 | `056-horoscope-charts-and-matches.sql` | 056 — Kundli charts and Guna Milan results from the horoscope service. WHY (2026-09-27): * Guna Milan and Mangal Dosha are calculated by modules/MOD03-mangaly/horoscope-service (a pinned astronomy library for planet positions, Mangaly's own |
| 057 | `057-platform-member-insights.sql` | 057 — Facts for the ForKhatri owner's Members dashboard (platform console, ARCHITECTURE.md ADR-012) WHY (owner, 2026-09-27): "I want to see total users, and locations hotspot ... counts (m, f, age, etc.)". Gender and date of birth exist onl |
| 058 | `058-admin-member-summary.sql` | 058 — One member's Mangaly summary for the shared ForKhatri admin console (ARCHITECTURE.md ADR-012; TR-PLAT-01 member summary) WHY (2026-09-29): the platform console's member page shows each module's own facts side by side (Mangaly's plan n |
| 059 | `059-marriage-agents.sql` | 059 — Marriage agents: brokers and bureaus on Mangaly (DEC-V1-033) WHY (product owner, 2026-09-29): "a person who will act as broker, without app also he exists, so I don't want to kill his job rather I want to enhance him giving best platf |
| 060 | `060-agent-contact-limits.sql` | 060 — Marriage agents: fair-use limits on numbers and exports, and reports of unwanted calls (DEC-V1-034). The product owner (2026-09-29): whatever an agent does on his own WhatsApp groups is his business, but on Mangaly a number or email s |
| 061 | `061-client-photos-for-their-helper.sql` | 061 — A relationship manager or agent sees their own clients' photos. WHY (owner walkthrough, 2026-09-30): an agent opening a client family's file got a broken photo. The media route serves a photo only to its owner, a searchable profile's  |
| 062 | `062-wedding-arrangements.sql` | 062 — Wedding arrangements: the stage two families have reached, real places near them, and (later) Mangalya partners with offers. WHY (owner, 2026-10-01): once a request is accepted, Mangalya should help the families with what comes next — |
| 063 | `063-guides.sql` | 063 — Guides: short articles (and later videos) that teach families how to use Mangalya well — making a better profile, taking good photos, style, reporting and blocking, and different family situations. WHY (owner, 2026-10-01): "one more t |
| 064 | `064-guides-content.sql` | 064 — The first guides (generated by scripts/build_guides_migration.py from mangaly-service/app/components/guides/content.json; edit that file, not this one). Idempotent. |
| 065 | `065-parent-made-profile-without-child-number.sql` | 065 — A parent may publish a son's or daughter's profile without the child's own mobile number; the child takes it over later with consent. Plus a place for a family's biodata and horoscope (jathakam) file. (Owner, 2026-10-06: "yes, right — |
| 066 | `066-guides-marathi-kannada.sql` | 066 — Marathi (mr) and Kannada (kn) versions of the guides. WHY (owner, 2026-10-06): ForKhatri adds Marathi and Kannada alongside English, Hindi and Telugu. Each guide's `content` gains "mr" and "kn" entries; `content // jsonb` adds those t |

## Tables (TBL-xx)

| ID | Table | Created in |
|---|---|---|
| TBL-01 | `mangaly_identity.account` | 001 |
| TBL-02 | `mangaly_identity.otp_challenge` | 001 |
| TBL-03 | `mangaly_identity.password_reset_token` | 001 |
| TBL-04 | `mangaly_identity.session` | 001 |
| TBL-05 | `mangaly_platform.idempotency_key` | 001 |
| TBL-06 | `mangaly_platform.rate_limit_counter` | 001 |
| TBL-07 | `mangaly_authz.grant` | 001 |
| TBL-08 | `mangaly_authz.safety_override_grant` | 001 |
| TBL-09 | `mangaly_authz.outbox_event` | 001 |
| TBL-10 | `mangaly_profile.profile` | 001 |
| TBL-11 | `mangaly_profile.profile_media` | 001 |
| TBL-12 | `mangaly_profile.profile_attribute` | 001 |
| TBL-13 | `mangaly_profile.outbox_event` | 001 |
| TBL-14 | `mangaly_home_circle.invitation` | 001 |
| TBL-15 | `mangaly_home_circle.membership` | 001 |
| TBL-16 | `mangaly_home_circle.home_circle_note` | 001 |
| TBL-17 | `mangaly_home_circle.suggestion` | 001 |
| TBL-18 | `mangaly_home_circle.discovery_hint` | 001 |
| TBL-19 | `mangaly_home_circle.report` | 001 |
| TBL-20 | `mangaly_home_circle.connection_home_circle_scope` | 001 |
| TBL-21 | `mangaly_home_circle.family_introduction` | 001 |
| TBL-22 | `mangaly_home_circle.outbox_event` | 001 |
| TBL-23 | `mangaly_discovery.discovery_profile_index` | 001 |
| TBL-24 | `mangaly_discovery.outbox_event` | 001 |
| TBL-25 | `mangaly_compatibility.assessment_response` | 001 |
| TBL-26 | `mangaly_compatibility.horoscope` | 001 |
| TBL-27 | `mangaly_compatibility.outbox_event` | 001 |
| TBL-28 | `mangaly_trust.verification_layer_status` | 001 |
| TBL-29 | `mangaly_trust.verification_circle_invite` | 001 |
| TBL-30 | `mangaly_trust.admin_verification_request` | 001 |
| TBL-31 | `mangaly_trust.evidence_document_ref` | 001 |
| TBL-32 | `mangaly_trust.outbox_event` | 001 |
| TBL-33 | `mangaly_connection.connection_request` | 001 |
| TBL-34 | `mangaly_connection.sharing_grant` | 001 |
| TBL-35 | `mangaly_connection.family_contact_share` | 001 |
| TBL-36 | `mangaly_connection.outbox_event` | 001 |
| TBL-37 | `mangaly_communication.conversation` | 001 |
| TBL-38 | `mangaly_communication.message` | 001 |
| TBL-39 | `mangaly_communication.retention_policy_exception` | 001 |
| TBL-40 | `mangaly_communication.legal_hold` | 001 |
| TBL-41 | `mangaly_communication.retention_job_run` | 001 |
| TBL-42 | `mangaly_communication.contact_exchange_request` | 001 |
| TBL-43 | `mangaly_communication.outbox_event` | 001 |
| TBL-44 | `mangaly_safety.report` | 001 |
| TBL-45 | `mangaly_safety.detection_signal` | 001 |
| TBL-46 | `mangaly_safety.severity_classification` | 001 |
| TBL-47 | `mangaly_safety.outbox_event` | 001 |
| TBL-48 | `mangaly_lifecycle.profile_lifecycle_status` | 001 |
| TBL-49 | `mangaly_lifecycle.meeting_note` | 001 |
| TBL-50 | `mangaly_lifecycle.success_story_invite` | 001 |
| TBL-51 | `mangaly_lifecycle.success_story` | 001 |
| TBL-52 | `mangaly_lifecycle.outbox_event` | 001 |
| TBL-53 | `mangaly_operations.case` | 001 |
| TBL-54 | `mangaly_operations.case_decision` | 001 |
| TBL-55 | `mangaly_operations.case_appeal` | 001 |
| TBL-56 | `mangaly_operations.operator_role_scope` | 001 |
| TBL-57 | `mangaly_operations.paging_event` | 001 |
| TBL-58 | `mangaly_operations.csam_report_packet` | 001 |
| TBL-59 | `mangaly_operations.support_ticket` | 001 |
| TBL-60 | `mangaly_operations.outbox_event` | 001 |
| TBL-61 | `mangaly_notification.inbox_entry` | 001 |
| TBL-62 | `mangaly_discovery.shortlist` | 032 |
| TBL-63 | `mangaly_safety.block` | 033 |
| TBL-64 | `mangaly_communication.conversation_participant` | 035 |
| TBL-65 | `mangaly_trust.biometric_consent` | 045 |
| TBL-66 | `mangaly_profile.member_profile` | 047 |
| TBL-67 | `mangaly_trust.member_face_match` | 047 |
| TBL-68 | `mangaly_operations.operator` | 048 |
| TBL-69 | `mangaly_operations.account_suspension` | 048 |
| TBL-70 | `mangaly_horoscope.chart` | 049 |
| TBL-71 | `mangaly_discovery.daily_pick` | 050 |
| TBL-72 | `mangaly_billing."order"` | 051 |
| TBL-73 | `mangaly_billing.plan_subscription` | 051 |
| TBL-74 | `mangaly_billing.webhook_event` | 051 |
| TBL-75 | `mangaly_profile.profile_view` | 051 |
| TBL-76 | `mangaly_operations.relationship_manager` | 052 |
| TBL-77 | `mangaly_operations.rm_assignment` | 052 |
| TBL-78 | `mangaly_operations.rm_suggestion` | 052 |
| TBL-79 | `mangaly_operations.rm_interaction` | 052 |
| TBL-80 | `mangaly_horoscope.match` | 056 |
| TBL-81 | `mangaly_operations.agent_contact_view` | 059 |
| TBL-82 | `mangaly_operations.agent_export` | 059 |
| TBL-83 | `mangaly_billing.plan_price` | 059 |
| TBL-84 | `mangaly_operations.offline_profile` | 059 |
| TBL-85 | `mangaly_operations.agent_limit` | 060 |
| TBL-86 | `mangaly_operations.contact_report` | 060 |
| TBL-87 | `mangaly_wedding.connection_stage` | 062 |
| TBL-88 | `mangaly_wedding.osm_place` | 062 |
| TBL-89 | `mangaly_wedding.partner` | 062 |
| TBL-90 | `mangaly_wedding.partner_offer` | 062 |
| TBL-91 | `mangaly_content.guide` | 063 |
| TBL-92 | `mangaly_identity.account_alias` | 065 |
| TBL-93 | `mangaly_profile.profile_document` | 065 |

## SQL functions (FN-xx)

SECURITY DEFINER functions are the only way the app role touches some tables (see 08).

| ID | Function | First defined in |
|---|---|---|
| FN-001 | `mangaly_identity.lookup_by_identifier` | 001 |
| FN-002 | `mangaly_authz.has_scope` | 001 |
| FN-003 | `mangaly_authz.is_self` | 001 |
| FN-004 | `mangaly_identity.lookup_session` | 004 |
| FN-005 | `mangaly_home_circle.list_pending_invitations_for_identifiers` | 006 |
| FN-006 | `mangaly_home_circle.respond_to_invitation` | 006 |
| FN-007 | `mangaly_home_circle.list_own_pending_notes` | 007 |
| FN-008 | `mangaly_home_circle.approve_note_forward` | 008 |
| FN-009 | `mangaly_profile.lookup_profile_id_by_account` | 009 |
| FN-010 | `mangaly_authz.grant_connection_candidate_info` | 010 |
| FN-011 | `mangaly_profile.lookup_account_by_profile_id` | 012 |
| FN-012 | `mangaly_identity.ensure_platform_account` | 014 |
| FN-013 | `mangaly_connection.list_family_contact_requests` | 016 |
| FN-014 | `mangaly_connection.decide_family_contact_share` | 016 |
| FN-015 | `mangaly_home_circle.list_member_contexts` | 017 |
| FN-016 | `mangaly_home_circle.list_circle_members` | 019 |
| FN-017 | `mangaly_discovery.discovery_cards` | 020 |
| FN-018 | `mangaly_profile.is_discoverable_primary_photo` | 020 |
| FN-019 | `mangaly_connection.end_family_contact_for_member` | 021 |
| FN-020 | `mangaly_home_circle.is_active_note_author` | 022 |
| FN-021 | `mangaly_home_circle.list_note_forward_requests` | 022 |
| FN-022 | `mangaly_home_circle.decide_note_forward` | 022 |
| FN-023 | `mangaly_home_circle.list_shared_notes` | 022 |
| FN-024 | `mangaly_communication.open_conversation` | 026 |
| FN-025 | `mangaly_profile.public_biodata` | 027 |
| FN-026 | `mangaly_home_circle.list_pending_invitations_for` | 030 |
| FN-027 | `mangaly_home_circle.is_candidate_primary_photo_for_member` | 030 |
| FN-028 | `mangaly_identity.search_people` | 030 |
| FN-029 | `mangaly_identity.primary_identifier_of` | 030 |
| FN-030 | `mangaly_identity.account_id_for_identifier` | 030 |
| FN-031 | `mangaly_safety.blocked_account_ids` | 033 |
| FN-032 | `mangaly_safety.is_blocked_between` | 033 |
| FN-033 | `mangaly_notification.notify` | 034 |
| FN-034 | `mangaly_notification.notify_circle` | 034 |
| FN-035 | `mangaly_communication.is_participant` | 035 |
| FN-036 | `mangaly_communication.ensure_participants` | 035 |
| FN-037 | `mangaly_communication.open_family_conversation` | 035 |
| FN-038 | `mangaly_communication.conversation_people` | 035 |
| FN-039 | `mangaly_communication.is_conversation_photo` | 035 |
| FN-040 | `mangaly_connection.request_sender_info` | 036 |
| FN-041 | `mangaly_communication.sync_family_participants_for` | 037 |
| FN-042 | `mangaly_trust.verified_layers_for` | 038 |
| FN-043 | `mangaly_identity.create_account_for_child` | 041 |
| FN-044 | `mangaly_profile.can_manage` | 041 |
| FN-045 | `mangaly_profile.managed_profiles_of` | 041 |
| FN-046 | `mangaly_profile.created_for_me` | 041 |
| FN-047 | `mangaly_profile.erase_made_for_profile` | 042 |
| FN-048 | `mangaly_profile.disown_profile_made_for_me` | 042 |
| FN-049 | `mangaly_profile.is_open` | 043 |
| FN-050 | `mangaly_profile.is_openly_shared_photo` | 043 |
| FN-051 | `mangaly_profile.open_cards` | 043 |
| FN-052 | `mangaly_safety.report_conversation` | 044 |
| FN-053 | `mangaly_trust.face_match_status` | 045 |
| FN-054 | `mangaly_trust.record_face_match` | 045 |
| FN-055 | `mangaly_trust.withdraw_face_match` | 045 |
| FN-056 | `mangaly_trust.face_match_void_on_new_photo` | 045 |
| FN-057 | `mangaly_communication.sides_of` | 046 |
| FN-058 | `mangaly_communication.can_direct` | 046 |
| FN-059 | `mangaly_communication.direct_contacts` | 046 |
| FN-060 | `mangaly_communication.open_direct` | 046 |
| FN-061 | `mangaly_communication.thread_connections` | 046 |
| FN-062 | `mangaly_profile.is_member_photo_visible` | 047 |
| FN-063 | `mangaly_profile.member_photos` | 047 |
| FN-064 | `mangaly_trust.member_face_match_void_on_new_photo` | 047 |
| FN-065 | `mangaly_operations.operator_roles` | 048 |
| FN-066 | `mangaly_operations.is_suspended` | 048 |
| FN-067 | `mangaly_safety.classify_report` | 048 |
| FN-068 | `mangaly_safety.open_automated_report` | 048 |
| FN-069 | `mangaly_safety.open_profile_signal_report` | 048 |
| FN-070 | `mangaly_safety.underage_profiles` | 048 |
| FN-071 | `mangaly_operations.record_paging_event` | 048 |
| FN-072 | `mangaly_operations.store_csam_packet` | 048 |
| FN-073 | `mangaly_operations.packet_context` | 048 |
| FN-074 | `mangaly_operations.case_signal_type` | 048 |
| FN-075 | `mangaly_operations.safety_queue` | 048 |
| FN-076 | `mangaly_operations.acknowledge_case` | 048 |
| FN-077 | `mangaly_operations.resolve_case` | 048 |
| FN-078 | `mangaly_operations.reopen_case` | 048 |
| FN-079 | `mangaly_operations.suspend_account` | 048 |
| FN-080 | `mangaly_operations.lift_suspension` | 048 |
| FN-081 | `mangaly_horoscope.can_read` | 049 |
| FN-082 | `mangaly_horoscope.birth_inputs` | 049 |
| FN-083 | `mangaly_horoscope.save_chart` | 049 |
| FN-084 | `mangaly_horoscope.pair_charts` | 049 |
| FN-085 | `mangaly_profile.record_profile_view` | 051 |
| FN-086 | `mangaly_billing.who_viewed` | 051 |
| FN-087 | `mangaly_billing.who_shortlisted` | 051 |
| FN-088 | `mangaly_billing.active_subscriptions` | 051 |
| FN-089 | `mangaly_billing.mark_order_paid` | 051 |
| FN-090 | `mangaly_billing.mark_order_failed` | 051 |
| FN-091 | `mangaly_billing.order_id_for_gateway` | 051 |
| FN-092 | `mangaly_billing.attach_gateway_order` | 051 |
| FN-093 | `mangaly_billing.requests_sent_today` | 051 |
| FN-094 | `mangaly_operations.is_rm` | 052 |
| FN-095 | `mangaly_operations.rm_of` | 052 |
| FN-096 | `mangaly_operations.rm_assignment_visible` | 052 |
| FN-097 | `mangaly_operations.rm_owns_assignment` | 052 |
| FN-098 | `mangaly_operations.rm_member_summary` | 052 |
| FN-099 | `mangaly_operations.rm_member_family` | 052 |
| FN-100 | `mangaly_operations.rm_people_names` | 052 |
| FN-101 | `mangaly_operations.rm_linked` | 052 |
| FN-102 | `mangaly_connection.parent_of_share_recipient` | 054 |
| FN-103 | `mangaly_horoscope.current_chart` | 056 |
| FN-104 | `mangaly_horoscope.save_match` | 056 |
| FN-105 | `mangaly_horoscope.placements` | 056 |
| FN-106 | `mangaly_operations.platform_member_facts` | 057 |
| FN-107 | `mangaly_operations.admin_member_summary` | 058 |
| FN-108 | `mangaly_operations.agent_membership_until` | 059 |
| FN-109 | `mangaly_operations.can_work_as_rm` | 059 |
| FN-110 | `mangaly_operations.is_agent` | 059 |
| FN-111 | `mangaly_operations.apply_as_agent` | 059 |
| FN-112 | `mangaly_operations.review_agent` | 059 |
| FN-113 | `mangaly_operations.rm_assignment_guard` | 059 |
| FN-114 | `mangaly_operations.set_client_stage` | 059 |
| FN-115 | `mangaly_operations.choose_agent` | 059 |
| FN-116 | `mangaly_operations.release_agent` | 059 |
| FN-117 | `mangaly_operations.agent_directory` | 059 |
| FN-118 | `mangaly_operations.agents_of` | 059 |
| FN-119 | `mangaly_operations.agent_contact` | 059 |
| FN-120 | `mangaly_operations.agent_contact_open` | 059 |
| FN-121 | `mangaly_operations.contact_views_of` | 059 |
| FN-122 | `mangaly_profile.set_agents_may_see_contact` | 059 |
| FN-123 | `mangaly_profile.agents_may_see_contact` | 059 |
| FN-124 | `mangaly_operations.exports_of` | 059 |
| FN-125 | `mangaly_operations.agent_applications` | 059 |
| FN-126 | `mangaly_operations.my_agent_record` | 059 |
| FN-127 | `mangaly_operations.agent_client_biodata` | 059 |
| FN-128 | `mangaly_operations.agent_client_cores` | 059 |
| FN-129 | `mangaly_billing.set_plan_price` | 059 |
| FN-130 | `mangaly_operations.agent_connect_until` | 059 |
| FN-131 | `mangaly_operations.offline_media_visible` | 059 |
| FN-132 | `mangaly_operations.agent_limit_value` | 060 |
| FN-133 | `mangaly_operations.set_agent_limit` | 060 |
| FN-134 | `mangaly_operations.india_today_start` | 060 |
| FN-135 | `mangaly_operations.agent_opened_recently` | 060 |
| FN-136 | `mangaly_operations.agent_quota` | 060 |
| FN-137 | `mangaly_operations.contact_suspects` | 060 |
| FN-138 | `mangaly_operations.report_contact_misuse` | 060 |
| FN-139 | `mangaly_operations.contact_reports_admin` | 060 |
| FN-140 | `mangaly_operations.review_contact_report` | 060 |
| FN-141 | `mangaly_operations.lift_contact_suspension` | 060 |
| FN-142 | `mangaly_operations.is_client_photo` | 061 |
| FN-143 | `mangaly_identity.create_managed_account` | 065 |
| FN-144 | `mangaly_profile.set_pending_phone` | 065 |
| FN-145 | `mangaly_profile.made_for_my_number` | 065 |
| FN-146 | `mangaly_profile.take_over_profile` | 065 |
| FN-147 | `mangaly_profile.not_my_profile` | 065 |
| FN-148 | `mangaly_identity.alias_of` | 065 |

RLS: enabled on tables per migration (policies named in each migration file). Column-level detail: read the migration named in 'Created in' plus later ALTERs; full column listing not regenerated here (unverified beyond migration text).