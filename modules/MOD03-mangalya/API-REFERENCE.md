# MOD03 Mangalya - API reference (as built 2026-11-22)

**Document status:** generated 2026-11-22 from the running service's `/openapi.json` (mangaly-service, port 8000) and the route files in `mangaly-service/app/api/routes/`. Scope: as built. Regenerate by fetching `http://localhost:8000/openapi.json`.

Conventions: all endpoints return JSON errors shaped `{"error":{"code","message","fields"}}`. Auth is the ForKhatri session cookie (identity service); `/health` is open; `/mangaly/admin/*`, `/operations/*` need an operator role; `/agents/admin/*` need an admin operator; `/rm/*` need a relationship-manager role. Mutating calls accept an `Idempotency-Key` header (table `mangaly_platform.idempotency_key`). `X-Mangaly-Manage` lets a parent/guardian act for a candidate (`for_candidate`) where allowed. Per-endpoint request/response schemas: see the live OpenAPI document (unverified per-field auth: confirm in the route file named in the tag).

The horoscope service (port 8013) is internal only: see section at the end.

## Index

agents (33), auth (9), billing (8), connections (22), messages (20), discovery (6), guides (2), ops (1), home_circle (24), horoscope (2), admin (5), media (1), notifications (2), operations (9), profile (35), assisted-matching (10), safety (4), shortlist (3), verification (3), wedding (3)

Total: 202 operations (API-001 to API-202).

## agents

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-001 | GET | `/agents/admin/applications` | Admin Applications | authorization  |
| API-002 | POST | `/agents/admin/applications/{account}/review` | Admin Review | account, authorization body: application/json |
| API-003 | GET | `/agents/admin/limits` | Admin Limits | authorization  |
| API-004 | PATCH | `/agents/admin/limits` | Admin Set Limit | authorization body: application/json |
| API-005 | GET | `/agents/admin/prices` | Admin Prices | authorization  |
| API-006 | PATCH | `/agents/admin/prices` | Admin Set Price | authorization body: application/json |
| API-007 | POST | `/agents/choose` | Choose | authorization, x-mangalya-language, accept-language body: application/json |
| API-008 | GET | `/agents/clients` | Clients | authorization, x-mangalya-language, accept-language  |
| API-009 | POST | `/agents/clients` | Add Client | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-010 | POST | `/agents/clients/import` | Import Clients | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-011 | GET | `/agents/clients/template` | Template | authorization, x-mangalya-language, accept-language  |
| API-012 | GET | `/agents/clients/{assignment_id}/shared` | Shared With Client | assignment_id, authorization, x-mangalya-language, accept-language  |
| API-013 | PATCH | `/agents/clients/{assignment_id}/stage` | Set Stage | assignment_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-014 | POST | `/agents/contact-open` | Contact Open | authorization, x-mangalya-language, accept-language body: application/json |
| API-015 | GET | `/agents/contact/{member_account_id}` | Contact | member_account_id, authorization, x-mangalya-language, accept-language  |
| API-016 | GET | `/agents/dashboard` | Dashboard | for_candidate, authorization  |
| API-017 | GET | `/agents/directory` | Directory | city, authorization  |
| API-018 | POST | `/agents/export/biodata` | Export Biodata | authorization, x-mangalya-language, accept-language body: application/json |
| API-019 | POST | `/agents/export/excel` | Export Excel | authorization, x-mangalya-language, accept-language body: application/json |
| API-020 | GET | `/agents/me` | Me | authorization  |
| API-021 | POST | `/agents/me` | Apply | authorization, x-mangalya-language, accept-language body: application/json |
| API-022 | GET | `/agents/offline` | Offline List | authorization, x-mangalya-language, accept-language  |
| API-023 | POST | `/agents/offline` | Offline Add | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-024 | GET | `/agents/offline-media/{offline_id}/{filename}` | Offline Media | offline_id, filename, authorization, x-mangalya-language, accept-language  |
| API-025 | POST | `/agents/offline/{offline_id}/archive` | Offline Archive | offline_id, authorization, x-mangalya-language, accept-language  |
| API-026 | PATCH | `/agents/privacy` | Privacy | authorization, x-mangalya-language, accept-language body: application/json |
| API-027 | GET | `/agents/quota` | Quota | authorization, x-mangalya-language, accept-language  |
| API-028 | POST | `/agents/release` | Release | authorization, x-mangalya-language, accept-language body: application/json |
| API-029 | POST | `/agents/reports` | Report | authorization, x-mangalya-language, accept-language body: application/json |
| API-030 | GET | `/agents/reports` | Reports | for_candidate, authorization  |
| API-031 | GET | `/agents/reports/suspects` | Report Suspects | day, for_candidate, authorization  |
| API-032 | POST | `/agents/share` | Share | authorization, x-mangalya-language, accept-language body: application/json |
| API-033 | POST | `/agents/shared/{suggestion_id}/answer` | Answer | suggestion_id, authorization, x-mangalya-language, accept-language body: application/json |

## auth

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-034 | POST | `/auth/login` | Log In | x-mangalya-language, accept-language body: application/json |
| API-035 | POST | `/auth/login/otp/request` | Request Login Otp | x-mangalya-language, accept-language body: application/json |
| API-036 | POST | `/auth/logout` | Log Out | authorization  |
| API-037 | GET | `/auth/me` | Me | authorization  |
| API-038 | POST | `/auth/otp/resend` | Resend Otp | x-mangalya-language, accept-language body: application/json |
| API-039 | POST | `/auth/otp/verify` | Verify Otp |  body: application/json |
| API-040 | POST | `/auth/reset/confirm` | Confirm Password Reset | x-mangalya-language, accept-language body: application/json |
| API-041 | POST | `/auth/reset/request` | Request Password Reset | x-mangalya-language, accept-language body: application/json |
| API-042 | POST | `/auth/signup` | Sign Up | x-mangalya-language, accept-language body: application/json |

## billing

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-043 | POST | `/billing/cancel` | Cancel | authorization, x-mangalya-language, accept-language  |
| API-044 | POST | `/billing/dev/pay/{order_id}` | Sandbox Pay | order_id, authorization, x-mangalya-language, accept-language  |
| API-045 | GET | `/billing/interested` | Interested | for_candidate, authorization  |
| API-046 | GET | `/billing/me` | My Plan | for_candidate, authorization, x-mangalya-language, accept-language  |
| API-047 | POST | `/billing/orders` | Create Order | authorization, x-mangalya-language, accept-language body: application/json |
| API-048 | POST | `/billing/orders/{order_id}/confirm` | Confirm Order | order_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-049 | GET | `/billing/plans` | List Plans | codes, x-mangalya-language, accept-language  |
| API-050 | POST | `/billing/webhook` | Webhook |   |

## connections

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-051 | POST | `/connection` | Send Request | authorization, x-mangalya-language, accept-language body: application/json |
| API-052 | GET | `/connection/incoming` | List Incoming | for_candidate, authorization  |
| API-053 | GET | `/connection/sent` | List Sent | for_candidate, authorization  |
| API-054 | GET | `/connection/{connection_id}` | Get Connection | connection_id, for_candidate, authorization  |
| API-055 | POST | `/connection/{connection_id}/accept` | Accept | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-056 | POST | `/connection/{connection_id}/decline` | Decline | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-057 | POST | `/connection/{connection_id}/share/family-contact` | Request Family Contact | connection_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-058 | DELETE | `/connection/{connection_id}/share/family-contact` | Withdraw Family Contact | connection_id, authorization, x-mangalya-language, accept-language  |
| API-059 | PATCH | `/connection/{connection_id}/share/{category}` | Set Share | connection_id, category, authorization, x-mangalya-language, accept-language body: application/json |
| API-060 | GET | `/connection/{connection_id}/sharing` | Get Sharing | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-061 | POST | `/connection/{connection_id}/withdraw` | Withdraw | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-062 | POST | `/connections` | Send Request | authorization, x-mangalya-language, accept-language body: application/json |
| API-063 | GET | `/connections/incoming` | List Incoming | for_candidate, authorization  |
| API-064 | GET | `/connections/sent` | List Sent | for_candidate, authorization  |
| API-065 | GET | `/connections/{connection_id}` | Get Connection | connection_id, for_candidate, authorization  |
| API-066 | POST | `/connections/{connection_id}/accept` | Accept | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-067 | POST | `/connections/{connection_id}/decline` | Decline | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-068 | POST | `/connections/{connection_id}/share/family-contact` | Request Family Contact | connection_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-069 | DELETE | `/connections/{connection_id}/share/family-contact` | Withdraw Family Contact | connection_id, authorization, x-mangalya-language, accept-language  |
| API-070 | PATCH | `/connections/{connection_id}/share/{category}` | Set Share | connection_id, category, authorization, x-mangalya-language, accept-language body: application/json |
| API-071 | GET | `/connections/{connection_id}/sharing` | Get Sharing | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-072 | POST | `/connections/{connection_id}/withdraw` | Withdraw | connection_id, for_candidate, authorization, x-mangalya-language, accept-language  |

## messages

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-073 | GET | `/conversations` | List Conversations | for_candidate, authorization  |
| API-074 | GET | `/conversations/direct/contacts` | Direct Contacts | authorization  |
| API-075 | POST | `/conversations/direct/open` | Direct Open | authorization, x-mangalya-language, accept-language body: application/json |
| API-076 | GET | `/conversations/{connection_id}` | List Messages | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-077 | POST | `/conversations/{connection_id}` | Send Message | connection_id, kind, authorization, x-mangalya-language, accept-language body: application/json |
| API-078 | POST | `/conversations/{connection_id}/close` | Close Conversation | connection_id, authorization, x-mangalya-language, accept-language  |
| API-079 | POST | `/conversations/{connection_id}/family/open` | Open Family | connection_id, authorization, x-mangalya-language, accept-language  |
| API-080 | GET | `/conversations/{connection_id}/people` | Thread People | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-081 | POST | `/conversations/{connection_id}/read` | Mark Read | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-082 | POST | `/conversations/{connection_id}/report` | Report In Thread | connection_id, kind, authorization, x-mangalya-language, accept-language body: application/json |
| API-083 | GET | `/messages` | List Conversations | for_candidate, authorization  |
| API-084 | GET | `/messages/direct/contacts` | Direct Contacts | authorization  |
| API-085 | POST | `/messages/direct/open` | Direct Open | authorization, x-mangalya-language, accept-language body: application/json |
| API-086 | GET | `/messages/{connection_id}` | List Messages | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-087 | POST | `/messages/{connection_id}` | Send Message | connection_id, kind, authorization, x-mangalya-language, accept-language body: application/json |
| API-088 | POST | `/messages/{connection_id}/close` | Close Conversation | connection_id, authorization, x-mangalya-language, accept-language  |
| API-089 | POST | `/messages/{connection_id}/family/open` | Open Family | connection_id, authorization, x-mangalya-language, accept-language  |
| API-090 | GET | `/messages/{connection_id}/people` | Thread People | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-091 | POST | `/messages/{connection_id}/read` | Mark Read | connection_id, kind, authorization, x-mangalya-language, accept-language  |
| API-092 | POST | `/messages/{connection_id}/report` | Report In Thread | connection_id, kind, authorization, x-mangalya-language, accept-language body: application/json |

## discovery

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-093 | GET | `/discovery/because` | List Because | for_candidate, authorization, x-mangalya-language, accept-language  |
| API-094 | GET | `/discovery/compatibility/{candidate_account_id}` | Why This Match | candidate_account_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-095 | GET | `/discovery/fit/{candidate_account_id}` | How You Fit | candidate_account_id, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-096 | GET | `/discovery/search` | Search | page, page_size, for_candidate, looking_for, sort, q, nearby, city, age_min, age_max, height_min, height_max, marital_status, education, diet, gotra, sub_community, profession, income_band, mother_tongue, manglik, open_to_relocate, min_guna, mangal, min_porutham, porutham_essentials, authorization, x-mangalya-language, accept-language  |
| API-097 | GET | `/discovery/shelves` | List Shelves | for_candidate, looking_for, authorization, x-mangalya-language, accept-language  |
| API-098 | GET | `/discovery/snippet/{candidate_account_id}` | Get Snippet | candidate_account_id, authorization  |

## guides

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-099 | GET | `/guides` | List Guides | authorization, x-mangalya-language, accept-language  |
| API-100 | GET | `/guides/{slug}` | Get Guide | slug, authorization, x-mangalya-language, accept-language  |

## ops

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-101 | GET | `/health` | Health |   |

## home_circle

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-102 | GET | `/home-circle/contact-requests` | List Contact Requests | authorization  |
| API-103 | POST | `/home-circle/contact-requests/{share_id}/approve` | Approve Contact Request | share_id, authorization, x-mangalya-language, accept-language  |
| API-104 | POST | `/home-circle/contact-requests/{share_id}/decline` | Decline Contact Request | share_id, authorization, x-mangalya-language, accept-language  |
| API-105 | GET | `/home-circle/contexts` | List Contexts | authorization  |
| API-106 | GET | `/home-circle/invitations/pending` | List Pending Invitations | authorization  |
| API-107 | POST | `/home-circle/invitations/{invitation_id}/accept` | Accept Invitation | invitation_id, authorization, x-mangalya-language, accept-language  |
| API-108 | POST | `/home-circle/invitations/{invitation_id}/decline` | Decline Invitation | invitation_id, authorization, x-mangalya-language, accept-language  |
| API-109 | POST | `/home-circle/invite` | Invite | authorization, x-mangalya-language, accept-language body: application/json |
| API-110 | GET | `/home-circle/members` | List Members | candidate_account_id, for_candidate, authorization  |
| API-111 | DELETE | `/home-circle/members/{membership_id}` | Remove Member | membership_id, authorization, x-mangalya-language, accept-language  |
| API-112 | POST | `/home-circle/members/{membership_id}/leave` | Leave | membership_id, authorization, x-mangalya-language, accept-language  |
| API-113 | PATCH | `/home-circle/members/{membership_id}/relation` | Set Member Relation | membership_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-114 | POST | `/home-circle/notes` | Add Note | authorization, x-mangalya-language, accept-language body: application/json |
| API-115 | GET | `/home-circle/notes` | List My Notes | membership_id, subject_account_id, authorization, x-mangalya-language, accept-language  |
| API-116 | GET | `/home-circle/notes/requests` | List Note Requests | authorization  |
| API-117 | GET | `/home-circle/notes/shared` | List Shared Notes | authorization  |
| API-118 | PATCH | `/home-circle/notes/{note_id}` | Edit Note | note_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-119 | DELETE | `/home-circle/notes/{note_id}` | Delete Note | note_id, authorization, x-mangalya-language, accept-language  |
| API-120 | POST | `/home-circle/notes/{note_id}/decline` | Decline Note | note_id, authorization, x-mangalya-language, accept-language  |
| API-121 | POST | `/home-circle/notes/{note_id}/read` | Read Note | note_id, authorization, x-mangalya-language, accept-language  |
| API-122 | POST | `/home-circle/notes/{note_id}/request` | Request Note Forward | note_id, authorization, x-mangalya-language, accept-language  |
| API-123 | GET | `/home-circle/people` | Search People | q, authorization  |
| API-124 | POST | `/home-circle/suggest` | Suggest | authorization, x-mangalya-language, accept-language body: application/json |
| API-125 | GET | `/home-circle/suggestions` | List Suggestions | candidate_account_id, for_candidate, authorization  |

## horoscope

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-126 | POST | `/horoscope/check` | Check | authorization body: application/json |
| API-127 | GET | `/horoscope/match/{other_account_id}` | Get Match | other_account_id, for_candidate, authorization  |

## admin

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-128 | GET | `/mangaly/admin/manifest` | Manifest | x-mangalya-language, accept-language  |
| API-129 | GET | `/mangaly/admin/members/{member_id}/summary` | Member Summary | member_id, authorization, x-mangalya-language, accept-language  |
| API-130 | GET | `/mangaly/admin/moderation` | Queue | authorization, x-mangalya-language, accept-language  |
| API-131 | GET | `/mangaly/admin/moderation/{item_id}` | Detail | item_id, authorization, x-mangalya-language, accept-language  |
| API-132 | POST | `/mangaly/admin/moderation/{item_id}/actions/{action_id}` | Act | item_id, action_id, authorization, x-mangalya-language, accept-language body: application/json |

## media

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-133 | GET | `/media/{profile_id}/{filename}` | Get Media | profile_id, filename, authorization  |

## notifications

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-134 | GET | `/notifications` | List Notifications | for_candidate, authorization, x-mangalya-language, accept-language  |
| API-135 | POST | `/notifications/read` | Mark Read | authorization body: application/json |

## operations

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-136 | GET | `/operations/cases` | List Cases | state, tier, authorization  |
| API-137 | GET | `/operations/cases/{case_id}` | Get Case | case_id, authorization  |
| API-138 | POST | `/operations/cases/{case_id}/acknowledge` | Acknowledge | case_id, authorization, x-mangalya-language, accept-language  |
| API-139 | POST | `/operations/cases/{case_id}/lift-suspension` | Lift Suspension | case_id, authorization, x-mangalya-language, accept-language  |
| API-140 | POST | `/operations/cases/{case_id}/reopen` | Reopen | case_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-141 | POST | `/operations/cases/{case_id}/resolve` | Resolve | case_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-142 | POST | `/operations/cases/{case_id}/suspend` | Suspend | case_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-143 | GET | `/operations/me` | Operator Me | authorization  |
| API-144 | POST | `/operations/sweeps/minor-profiles` | Sweep Minor Profiles | authorization  |

## profile

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-145 | POST | `/profile` | Create Profile | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-146 | GET | `/profile/attributes` | Get All Attributes | authorization, x-mangalya-language, accept-language  |
| API-147 | GET | `/profile/attributes/full` | Get All Attribute Values | authorization, x-mangalya-language, accept-language  |
| API-148 | POST | `/profile/biodata/read` | Biodata Read | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-149 | GET | `/profile/biodata/reader` | Biodata Reader | authorization  |
| API-150 | POST | `/profile/claim` | Claim | authorization  |
| API-151 | GET | `/profile/completeness` | Get Completeness | authorization, x-mangalya-language, accept-language  |
| API-152 | POST | `/profile/disown` | Disown | authorization  |
| API-153 | GET | `/profile/documents` | List Documents | authorization, x-mangalya-language, accept-language  |
| API-154 | POST | `/profile/documents` | Attach Document | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-155 | DELETE | `/profile/documents/{document_id}` | Delete Document | document_id, authorization  |
| API-156 | GET | `/profile/documents/{document_id}/file` | Get Document File | document_id, authorization  |
| API-157 | POST | `/profile/managed` | Create Profile For Child | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-158 | GET | `/profile/managed` | List Managed | authorization  |
| API-159 | GET | `/profile/matchmaker/brief` | Matchmaker Get | authorization, x-mangalya-language, accept-language  |
| API-160 | PATCH | `/profile/matchmaker/brief` | Matchmaker Save | authorization, x-mangalya-language, accept-language body: application/json |
| API-161 | POST | `/profile/matchmaker/understand` | Matchmaker Understand | authorization, x-mangalya-language, accept-language body: application/json |
| API-162 | GET | `/profile/me` | Get Own Profile | authorization  |
| API-163 | GET | `/profile/member/me` | Get Member | authorization  |
| API-164 | PATCH | `/profile/member/me` | Put Member | authorization body: application/json |
| API-165 | POST | `/profile/member/photo` | Put Member Photo | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-166 | GET | `/profile/photos` | List Photos | authorization, x-mangalya-language, accept-language  |
| API-167 | POST | `/profile/photos` | Add Photo | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-168 | PATCH | `/profile/photos/order` | Reorder Photos | authorization, x-mangalya-language, accept-language body: application/json |
| API-169 | DELETE | `/profile/photos/{media_id}` | Delete Photo | media_id, authorization, x-mangalya-language, accept-language  |
| API-170 | POST | `/profile/photos/{media_id}/primary` | Set Primary Photo | media_id, authorization, x-mangalya-language, accept-language  |
| API-171 | GET | `/profile/places/search` | Search Places | q, limit, authorization  |
| API-172 | GET | `/profile/view/{target_account_id}` | Get Profile | target_account_id, authorization  |
| API-173 | GET | `/profile/view/{target_account_id}/full` | Get Profile Full | target_account_id, authorization  |
| API-174 | GET | `/profile/view/{target_account_id}/public` | Get Public Profile | target_account_id, authorization  |
| API-175 | POST | `/profile/voice-intro` | Record Voice Intro | authorization, x-mangalya-language, accept-language body: multipart/form-data |
| API-176 | GET | `/profile/voice-intro` | Get Voice Intro | authorization  |
| API-177 | DELETE | `/profile/voice-intro` | Remove Voice Intro | authorization, x-mangalya-language, accept-language  |
| API-178 | GET | `/profile/{category}` | Get Category | category, authorization, x-mangalya-language, accept-language  |
| API-179 | PATCH | `/profile/{category}` | Update Category | category, authorization, x-mangalya-language, accept-language body: application/json |

## assisted-matching

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-180 | POST | `/rm/assign` | Assign | authorization, x-mangalya-language, accept-language body: application/json |
| API-181 | GET | `/rm/assignments` | Assignments | authorization, x-mangalya-language, accept-language  |
| API-182 | GET | `/rm/assignments/{assignment_id}` | Assignment Detail | assignment_id, authorization, x-mangalya-language, accept-language  |
| API-183 | POST | `/rm/assignments/{assignment_id}/end` | End Assignment | assignment_id, authorization, x-mangalya-language, accept-language  |
| API-184 | POST | `/rm/assignments/{assignment_id}/interactions` | Add Interaction | assignment_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-185 | GET | `/rm/assignments/{assignment_id}/search` | Search For Member | assignment_id, page, page_size, sort, q, nearby, city, age_min, age_max, height_min, height_max, marital_status, education, diet, gotra, sub_community, profession, income_band, mother_tongue, manglik, open_to_relocate, authorization, x-mangalya-language, accept-language  |
| API-186 | POST | `/rm/assignments/{assignment_id}/suggestions` | Suggest | assignment_id, authorization, x-mangalya-language, accept-language body: application/json |
| API-187 | GET | `/rm/me` | My Rm | for_candidate, authorization  |
| API-188 | GET | `/rm/me/role` | My Role | authorization  |
| API-189 | POST | `/rm/suggestions/{suggestion_id}/decision` | Decide | suggestion_id, authorization, x-mangalya-language, accept-language body: application/json |

## safety

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-190 | POST | `/safety/block/{profile_id}` | Block | profile_id, authorization, x-mangalya-language, accept-language  |
| API-191 | DELETE | `/safety/block/{profile_id}` | Unblock | profile_id, authorization  |
| API-192 | GET | `/safety/blocks` | List Blocks | authorization  |
| API-193 | POST | `/safety/report` | Report | authorization, x-mangalya-language, accept-language body: application/json |

## shortlist

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-194 | GET | `/shortlist` | List Shortlist | for_candidate, authorization  |
| API-195 | POST | `/shortlist/{profile_id}` | Add To Shortlist | profile_id, for_candidate, authorization body: application/json |
| API-196 | DELETE | `/shortlist/{profile_id}` | Remove From Shortlist | profile_id, for_candidate, authorization  |

## verification

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-197 | POST | `/verification/face-match` | Face Match | authorization, x-mangalya-language, accept-language body: application/json |
| API-198 | GET | `/verification/me` | My Verification | authorization  |
| API-199 | POST | `/verification/withdraw` | Withdraw | authorization  |

## wedding

| ID | Method | Path | Summary | Body / params |
|---|---|---|---|---|
| API-200 | GET | `/wedding/stages` | List Stages | ids, for_candidate, authorization  |
| API-201 | GET | `/wedding/{connection_id}/places` | Places | connection_id, category, near, for_candidate, authorization, x-mangalya-language, accept-language  |
| API-202 | POST | `/wedding/{connection_id}/stage` | Update Stage | connection_id, for_candidate, authorization body: application/json |

## Horoscope service (internal, port 8013)

Requires header `Authorization` service token (env `HOROSCOPE_SERVICE_TOKEN`, 24+ chars) and `x-mangaly-viewer`. Not reachable from the browser; mangaly-service calls it.

| ID | Method | Path | Purpose |
|---|---|---|---|
| HAPI-01 | GET | `/health` | liveness, no token |
| HAPI-02 | POST | `/horoscope/chart` | store/compute a person's chart (opt-in, audited, append-only store) |
| HAPI-03 | POST | `/horoscope/match` | Guna Milan (36), Porutham (10) and Mangal dosha for two charts |
| HAPI-04 | POST | `/horoscope/calculate/chart` | stateless chart calculation (engine) |
| HAPI-05 | POST | `/horoscope/calculate/match` | stateless match calculation |
| HAPI-06 | POST | `/horoscope/calculate/scores` | stateless koota scores |

Mangalya-facing wrappers: `POST /horoscope/check` (API: horoscope tag, used by `/horoscope/check` screen) and `GET /horoscope/match/{other_account_id}`.
