# API reference (Counsel service, port 8014)

Document status: 2026-11-22, as built. Source: live `/openapi.json` (106 operations) plus 3 internal routes and 1 WebSocket that OpenAPI does not list = 110 endpoints.

Conventions: errors are `{"detail":{"code","message",...}}` (see 07-tech-reqs.md). Language header `X-Counsel-Language` (en/hi/te/mr/kn). Session = HttpOnly `fk_session` cookie resolved by the platform identity service. Auth column: member = signed-in; admin = member with `counsel.admin` scope or listed in ADMIN_MEMBER_IDS; service key = platform service credentials.

Table of contents is the table itself; IDs API-001..API-110 are stable references used by 02, 05 and TRACEABILITY.

| ID | Endpoint | Auth | Purpose |
|---|---|---|---|
| API-001 | `GET /me` | member | Who am I: name, language, admin flag, provider status, unread count, upcoming count, entrance URL. |
| API-002 | `POST /me/ws-ticket` | member | Mint a single-use 60 s ticket for the room WebSocket. |
| API-003 | `GET /me/export` | member | Download my Counsel data as JSON (counsel-my-data.json). |
| API-004 | `GET /me/deletion-check` | member | List what blocks deleting my Counsel data (upcoming_bookings, open_packages_or_questions, open_disputes, unpaid_earnings). |
| API-005 | `POST /me/delete` | member | Erase my Counsel data; body {confirm:'DELETE'}. Updated 2026-11-22: no longer 409 deletion_blocked; same as API-110. |
| API-006 | `GET /me/saved` | member | My saved consultants as cards. |
| API-007 | `PUT /me/saved/{provider_id}` | member | Save a consultant (idempotent). |
| API-008 | `DELETE /me/saved/{provider_id}` | member | Unsave a consultant. |
| API-009 | `GET /me/notifications` | member | Last 50 in-app notifications. |
| API-010 | `POST /me/notifications/read` | member | Mark all my notifications read. |
| API-011 | `POST /me/blocks/{member_id}` | member | Block a member (each side is then refused as booking/question counterpart). |
| API-012 | `DELETE /me/blocks/{member_id}` | member | Unblock. |
| API-013 | `GET /expertise` | public | Active expertise areas with approved-consultant counts, names in X-Counsel-Language. |
| API-014 | `GET /places` | public | Listed cities (45) for near-me and the city picker, plus nearby_km (150). |
| API-015 | `GET /search` | public (session optional) | Deterministic search + ranking; filters q, area, min/max price, language, verified, duration_max, sort, now, min_rating, near, nearby, within_hours. Counts a search impression per result. |
| API-016 | `POST /understand` | public (session optional) | Describe it in your own words: text (600 chars) -> structured filters (rules parser, or Claude when configured) -> search results. |
| API-017 | `GET /home` | public (session optional) | Home data: featured (8), recent consultants I completed with, areas that have consultants (max 12). |
| API-018 | `GET /providers/{provider_id}` | public (session optional) | Public profile (approved only; owner/admin may see others). Records one unique profile view per viewer per day (hashed). |
| API-019 | `GET /services/{service_id}` | public (session optional) | Service detail with quote (fee split), cancellation policy, disclaimer key, follow-up eligibility, available_now. |
| API-020 | `GET /services/{service_id}/slots` | public | Bookable start times (UTC ISO) for from/days (max 45). |
| API-021 | `GET /provide/profile` | member | My consultant profile with expertise, verified dimensions, evidence list, required_dimensions; null if none. |
| API-022 | `PUT /provide/profile` | member | Create/update my profile and up to 8 expertise areas (replaces the list). |
| API-023 | `POST /provide/photo` | member | Upload profile photo (jpeg/png/webp, 5 MB); public file. |
| API-024 | `POST /provide/evidence` | member | Add an evidence item (experience, qualification, certification, registration, business, portfolio). |
| API-025 | `POST /provide/evidence/{evidence_id}/document` | member | Attach private proof (image/pdf, 10 MB), encrypted and scanned; audited. |
| API-026 | `GET /provide/evidence/{evidence_id}/document` | member | Owner downloads own proof. |
| API-027 | `DELETE /provide/evidence/{evidence_id}` | member | Delete own evidence item. |
| API-028 | `POST /provide/submit` | member | Submit profile for review (needs headline and at least 1 expertise); draft/changes_requested -> pending_review. |
| API-029 | `GET /provide/expertise-requests` | member | My proposed new expertise areas. |
| API-030 | `POST /provide/expertise-requests` | member | Propose a new expertise area. |
| API-031 | `GET /provide/services` | member | My non-archived services. |
| API-032 | `POST /provide/services` | member | Create a service; active status needs the area's compliance rule satisfied; price audited. |
| API-033 | `PUT /provide/services/{service_id}` | member | Update a service (price change audited; paused/archived allowed). |
| API-034 | `GET /provide/availability` | member | My weekly rules, future exceptions, time zone. |
| API-035 | `PUT /provide/availability/rules` | member | Replace all weekly rules (window or fixed slot). |
| API-036 | `POST /provide/availability/exceptions` | member | Add a date exception (day off, partial block, extra hours). |
| API-037 | `DELETE /provide/availability/exceptions/{exception_id}` | member | Remove an exception. |
| API-038 | `GET /provide/dashboard` | member | Consultant dashboard: status, reputation, upcoming, earnings, badges, how you are found, open questions, online-until. |
| API-039 | `GET /provide/earnings` | member | Last 100 bookings with money split plus payouts list. |
| API-040 | `GET /provide/payout-method` | member | Masked payout method (kind, holder, ifsc, last4) or null. |
| API-041 | `PUT /provide/payout-method` | member | Set UPI id or bank account + IFSC; stored encrypted (Fernet). |
| API-042 | `POST /provide/payouts` | member | Request payout of everything eligible past the hold; needs a payout method. |
| API-043 | `POST /bookings` | member | Create a booking (pending_payment) for a service and start time; returns checkout reference. |
| API-044 | `GET /bookings` | member | My bookings; scope upcoming|past|all, role any|seeker|provider (max 100). |
| API-045 | `POST /bookings/{booking_id}/pay` | member | Confirm payment (verified with the provider) -> confirmed; ledger rows written. |
| API-046 | `GET /bookings/{booking_id}/timeline` | member | Chronological events built from real rows (nothing inferred). |
| API-047 | `GET /bookings/{booking_id}` | member | One booking (participants only) with review, dispute, follow-up offers. |
| API-048 | `POST /bookings/{booking_id}/cancel` | member | Cancel; refund per snapshotted policy; provider cancel uses provider_cancel_refund_percent. |
| API-049 | `POST /bookings/{booking_id}/complete` | member | Either participant marks complete; payout becomes eligible; recap built; badges refreshed. |
| API-050 | `POST /bookings/{booking_id}/no-show` | member | Present party reports the other absent (10 minutes or more after start). |
| API-051 | `GET /bookings/{booking_id}/messages` | member | Conversation thread (after=id, max 200). |
| API-052 | `POST /bookings/{booking_id}/messages` | member | Send chat message (4000 chars); notifies the other if not in the room. |
| API-053 | `POST /bookings/{booking_id}/review` | member | Seeker reviews a completed booking (5 scores + text); once. |
| API-054 | `POST /bookings/{booking_id}/dispute` | member | Open a dispute (one open at a time). |
| API-055 | `POST /reports` | member | Report provider/service/booking/message/member. |
| API-056 | `POST /services/{service_id}/time-requests` | member | Propose a custom time (service must allow it; max 3 pending per consultant). |
| API-057 | `GET /time-requests` | member | My time requests (both roles); marks past ones expired. |
| API-058 | `POST /time-requests/{request_id}/accept` | member | Consultant accepts: creates a booking held up to 24 h for payment. |
| API-059 | `POST /time-requests/{request_id}/decline` | member | Consultant declines with a note. |
| API-060 | `POST /time-requests/{request_id}/withdraw` | member | Seeker withdraws. |
| API-061 | `GET /services/{service_id}/packages` | public | Active follow-up offers of a service. |
| API-062 | `POST /provide/services/{service_id}/packages` | member | Add follow-up offer (1-3 sessions, 30-90 days, must cost less than singles). |
| API-063 | `DELETE /provide/packages/{package_id}` | member | Deactivate an offer. |
| API-064 | `PUT /provide/services/{service_id}/offers` | member | Set written-question price/answer days and instant-consult flag. |
| API-065 | `POST /packages/{package_id}/buy` | member | Buy a follow-up (only after a completed consultation with that consultant). |
| API-066 | `POST /purchases/{purchase_id}/pay` | member | Confirm payment of a follow-up or question. |
| API-067 | `GET /purchases` | member | My purchases (both roles) with question text/answer. |
| API-068 | `POST /purchases/{purchase_id}/cancel` | member | Buyer cancels an active follow-up; unused sessions refunded. |
| API-069 | `POST /purchases/{purchase_id}/book` | member | Book one follow-up session (confirmed immediately, no second payment). |
| API-070 | `POST /services/{service_id}/questions` | member | Ask a paid written question (10-3000 chars; max 2 open per consultant). |
| API-071 | `POST /purchases/{purchase_id}/answer` | member | Consultant answers (10-6000 chars); payout becomes eligible. |
| API-072 | `POST /provide/available-now` | member | Go online for 0 (off) to 240 minutes; approved consultants only. |
| API-073 | `POST /bookings/{booking_id}/recap` | member | Build/return the recap from shared notes, actions, files. |
| API-074 | `GET /bookings/{booking_id}/calendar.ics` | member | Calendar invite with join link and 15-minute alarm. |
| API-075 | `POST /payments/events` | signature | Signed payment event from the gateway or MOD06; payment.succeeded confirms a booking or purchase. |
| API-076 | `GET /bookings/{booking_id}/room` | member | Room state: booking, role, names, open/live, ICE servers, notes, actions, files, consents, presence. |
| API-077 | `PUT /bookings/{booking_id}/note` | member | Save shared or private note (50 000 chars); shared note is broadcast. |
| API-078 | `POST /bookings/{booking_id}/actions` | member | Add action item. |
| API-079 | `PATCH /bookings/{booking_id}/actions/{action_id}` | member | Tick/untick action item. |
| API-080 | `DELETE /bookings/{booking_id}/actions/{action_id}` | member | Delete action item. |
| API-081 | `POST /bookings/{booking_id}/files` | member | Upload consultation file (allow-listed MIME, MAX_UPLOAD_MB), scanned and encrypted. |
| API-082 | `GET /bookings/{booking_id}/files/{file_id}` | member | Download a file (participants); audited. |
| API-083 | `DELETE /bookings/{booking_id}/files/{file_id}` | member | Soft-delete own file. |
| API-084 | `POST /bookings/{booking_id}/recordings` | member | Upload a recording (webm/mp4, 500 MB) only if both consented and the service allows. |
| API-085 | `POST /bookings/{booking_id}/call-feedback` | member | Thumbs plus issue chips after a call. |
| API-086 | `POST /bookings/{booking_id}/recording-consent` | member | Give recording consent. |
| API-087 | `GET /admin/overview` | admin | Counts and economics (GTV, fee, refunds, cancellations, no-shows). |
| API-088 | `GET /admin/providers` | admin | Providers by status (default pending_review). |
| API-089 | `GET /admin/providers/{provider_id}` | admin | Full provider review view incl. evidence, services, badge history, audit. |
| API-090 | `POST /admin/providers/{provider_id}/decide` | admin | approve | changes_requested | suspend | reinstate (suspend pauses services). |
| API-091 | `POST /admin/providers/{provider_id}/verify` | admin | Grant/revoke one verification dimension. |
| API-092 | `POST /admin/evidence/{evidence_id}/decide` | admin | Verify/reject/reset one evidence item. |
| API-093 | `GET /admin/evidence/{evidence_id}/document` | admin | View private proof (audited). |
| API-094 | `GET /admin/expertise-requests` | admin | Pending expertise proposals. |
| API-095 | `POST /admin/expertise-requests/{request_id}/decide` | admin | Approve (creates area with five-language names) or reject. |
| API-096 | `PUT /admin/expertise/{area_id}` | admin | Create/update/disable an expertise area. |
| API-097 | `GET /admin/reports` | admin | Reports by status. |
| API-098 | `POST /admin/reports/{report_id}/decide` | admin | actioned | dismissed. |
| API-099 | `GET /admin/disputes` | admin | Disputes by status. |
| API-100 | `POST /admin/disputes/{dispute_id}/decide` | admin | Refund percent (capped at what is still refundable) plus resolution. |
| API-101 | `GET /admin/transactions` | admin | Latest bookings with money fields. |
| API-102 | `GET /admin/settings` | admin | All platform settings. |
| API-103 | `PUT /admin/settings/{key}` | admin | Change one of 6 allowed settings (audited). |
| API-104 | `GET /admin/audit` | admin | Latest audit log rows. |
| API-105 | `GET /media/photos/{member_id}/{name}` | public | Public profile photo (cache 1 day). |
| API-106 | `GET /` | public | Service banner {service:counsel, ok:true}. |
| API-107 | `GET /internal/v1/members/{member_id}/deletion-check` | service key | Platform asks what blocks erasing a member. |
| API-108 | `POST /internal/v1/members/{member_id}/erase` | service key | Platform erases a member's Counsel data (reason forkhatri_account_deleted). |
| API-109 | `GET /internal/v1/members/{member_id}/export` | service key | Platform exports a member's Counsel data. |
| API-110 | `WS /ws/bookings/{booking_id}?ticket=` | ticket or session cookie | Room socket: presence, chat, notes, actions, files, consents, recording state, WebRTC signalling relay (offer, answer, ice, ready, media), sharing, typing, ping. |

## Account deletion (added 2026-11-22)
| ID | Endpoint | Auth | Purpose |
|---|---|---|---|
| API-110 | `POST /me/delete-account-data` | member | Erase my Counsel data; body `{"confirm":"DELETE"}`; 3 per hour per member, 429 beyond; idempotent. Web then sends the member to the ForKhatri entrance. |
Changed behaviour: API-005 `POST /me/delete` is kept and does the same erase (no longer 409 `deletion_blocked`). `GET /me/deletion-check` and API-107 no longer refuse; they return `blockers` as warnings. API-108 `POST /internal/v1/members/{member_id}/erase` requires `X-ForKhatri-Service: identity`, is called by the identity service and returns `{module, status: done | nothing_to_delete, deleted{}, retained[], files_removed}`. API-109 and `GET /me/export` return the full inventory. Hub endpoints (`/v1/account/delete/*`, admin stuck deletions) are in `docs/ParentApp/ACCOUNT-DELETION.md`.
