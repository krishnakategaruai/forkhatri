# MOD03 Mangalya: account deletion inventory (2026-11-22)

Contract: `docs/ParentApp/ACCOUNT-DELETION.md`. Worker: migration `067-erase-member-data.sql` (`mangaly_identity.erase_account_data`, SECURITY DEFINER, owner role, one transaction, idempotent). Entry points:
- Member (kind B): `POST /privacy/delete-account-data` body `{"confirm":"DELETE"}`, 3 per hour, from the "Delete my data in Mangalya" control on `/me` (candidate Me and family-member Me).
- Platform (kind A): `POST /internal/v1/members/{member_id}/erase`, service key, 404 through the public edge. Returns `{module,status,deleted,retained,files_removed}`.
Files named by the function are removed from `.local-media` after the commit (`profile/storage.remove_member_files`).

| Store | Holds | Action |
|---|---|---|
| identity.account, account_alias, session, otp_challenge, password_reset_token | phone, email, credential, sign-in rows | hard delete |
| identity.account.managed_by_account_id (taken-over child accounts) | link to the parent | set to tombstone id |
| profile.profile (+ profile_attribute, profile_media, profile_document) | profile, birth/horoscope fields, preferences, photos, voice, biodata | hard delete (cascade) |
| profile.member_profile, profile_view | family-member profile, who viewed whom | hard delete |
| Managed profile, child has NOT taken over (created_by = member, claimed_at null) | child's account and profile | hard delete with the member (recursive) |
| Managed profile the child took over | the child's own profile | stays; created_by set NULL |
| discovery.discovery_profile_index, shortlist, daily_pick | search row, saved profiles (by or of the member), picks | hard delete |
| compatibility.horoscope, assessment_response; horoscope.chart, match | birth details, charts, matches | hard delete |
| trust.* (layer status, face match, biometric consent, evidence refs, verifier invites, admin requests) | verification | hard delete (+ evidence files) |
| home_circle.membership, invitation, note, hint, suggestion, introduction, scope | Home Circle both ways | hard delete (a membership that carries a report is kept with tombstone) |
| connection.connection_request, sharing_grant, family_contact_share; communication.contact_exchange_request | requests, shared values | hard delete (other party's row goes too: it only exists with the member) |
| communication.message, conversation_participant, conversation | messages written; threads tied to a removed connection or left with under 2 people | messages hard delete; threads removed; group threads keep the others' words |
| authz.grant, safety.block, wedding.connection_stage, lifecycle.* (notes, status, success story invite) | grants, blocks, wedding stage, notes | hard delete |
| notification.inbox_entry | notifications to or about the member | hard delete |
| operations.relationship_manager, rm_assignment, rm_suggestion, offline_profile, agent_contact_view, agent_export, support_ticket | broker profile and client lists | hard delete; clients detached (assignment row only), clients' own accounts untouched; offline client files removed; member removed from other agents' exports |
| billing.order, plan_subscription | orders | sandbox/unpaid hard delete; real paid orders kept with tombstone (tax) |
| platform.idempotency_key, rate_limit_counter, every outbox_event | technical rows | hard delete (rate-limit keys incl. hashed phone/email; the delete limiter itself is kept) |
| Files under `mangaly-service/.local-media` (`<id>/`, `offline-<id>/`) | photos, voice, biodata, evidence | deleted from disk |
| horoscope-service (port 8013) | nothing per member: the routes Mangalya calls are stateless; the in-memory store of the legacy `/horoscope/chart` route is never used by Mangalya | no action |
| Browser drafts | client-side only | cleared by the UI on success |
| safety.report, operations.contact_report, account_suspension, case_appeal, home_circle.report | moderation | RETAINED: id replaced by tombstone, free text and evidence nulled |
| platform.deletion_receipt | tombstone, date, counts | RETAINED (proof of deletion) |
| operations.csam_report_packet, case, case_decision | legal/moderation records | RETAINED untouched (legal duty); no member contact data |

Refused (HTTP 409, `role_must_be_removed_first`) while the member holds an operator role.

Known limits: 1:1 chats with the deleted member are removed for both sides (no second person to show "Deleted member"); a suspension is kept under the tombstone, so a returning member is not re-blocked by it (lawyer to confirm).
