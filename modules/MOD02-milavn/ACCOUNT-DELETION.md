# Milavn: account deletion (migration 056)

Follows `docs/ParentApp/ACCOUNT-DELETION.md`. One routine serves both kinds:

- Kind A (ForKhatri account deleted): `POST /internal/v1/members/{member_id}/erase`, service key (`X-ForKhatri-Service-Key`), refused with 401 without it, 404 through the public edge.
- Kind B (member taps "Delete my data in Milavn" on Me, settings gear): `POST /privacy/delete-account-data` with `{"confirm":"DELETE"}`, 3 attempts per hour. Milavn has no sign-in of its own (the ForKhatri session is shared), so the page sends the member back to the ForKhatri hub; opening Milavn again starts a brand-new member (onboarding).
- Code: `milavn-service/app/components/erasure/interface.py`, `app/api/routes/erasure.py`, SQL `milavn_platform.erase_member(uuid, text[])` (SECURITY DEFINER, owner role, acts only for that member or the internal service; no RLS policy was loosened).
- Order: upcoming hosted events cancelled the normal way (attendees told, paid spots refunded); paid tickets on other people's upcoming events withdrawn (refund, next person offered); then one SQL transaction for everything else; then files removed from disk. If a refund cannot be requested the whole thing rolls back and answers `partial` (retry later).
- Idempotent: second call returns `nothing_to_delete`. Tombstone id = `dead0000-...` (sha256 of the member id); the UI shows it as "Deleted member".

## Inventory (all `milavn_*` tables with a uuid member reference: 70; plus files)

| Store | Holds | Action |
|---|---|---|
| profile.member_profile, member_profile_media, member_interest, member_gender | place, bio, photo, interests, woman/man answer | hard delete; photo files removed |
| locationprivacy.location_precision_setting, consent_grant | privacy choices | hard delete |
| activity.occurrence / activity (hosted) | events the member hosts | upcoming: cancelled with notices and refunds; all: host becomes tombstone ("Deleted member"); event stays |
| activity.occurrence_contact | host phone/email | hard delete |
| activity.participation (+status_history, qr_checkin_token link) | going/waitlist/attended | hard delete; free-event waitlist promoted; history actor tombstoned |
| activity.event_team_member / event_team | teams | member removed, captain handed on, empty team removed |
| activity.occurrence_co_organizer, occurrence_cohost, event_speaker | roles | hard delete (granted_by / invited_by tombstoned) |
| activity.occurrence_message, occurrence_update, occurrence_photo (+moments files) | thread posts, announcements, photos | hard delete; files removed |
| activity.calendar_follow, series_regular, photo_preference; discovery.hidden_occurrence | follows, hides, preferences | hard delete |
| ticketing.ticket | tickets | unpaid: delete. paid/refunded: retained as payment record under tombstone, QR and pay link removed |
| circle.circle (organiser) | circles | hand over to longest-standing other organiser/assistant; none: circle deleted with its posts, photos, covers, files |
| circle.circle_membership, notify_setting, join_request, circle_invite, invite_link, formation_suggestion_member | membership traffic | hard delete (decided_by / invited_by tombstoned) |
| circle.circle_post (+media, photo/doc files), comment, reaction, album_photo | posts and photos | hard delete; files removed |
| circle.circle_album, circle_group(+update), poll, fundraiser, organization_scope | things the member created | creator becomes tombstone; group updates written by member deleted |
| circle.poll_vote | votes | hard delete |
| circle.fundraiser_pledge | pledges | unpaid: delete. paid: retained under tombstone, note removed |
| connect.chat_message (+chat photo files), message_reaction | messages | hard delete; files removed |
| connect.conversation_member / conversation | chats | group/activity: membership removed. One-to-one: stays for the other person with tombstone in place. Chats with nobody left: deleted with files |
| connect.free_now, presence, meet_again, meet_again_told | status and picks | hard delete |
| trust.feedback, reputation_signal, thanks | feedback, reputation, thanks sent/received | hard delete |
| trust.trust_status (as organiser) | derived label | hard delete |
| safety.block (made by member) | block list | hard delete |
| safety.report, block against member, moderation_action | reports by/about member | retained, tombstone only, free text removed |
| notification.inbox_entry, outbox, preference, reminder_sent | alerts | hard delete; member's name inside other people's notices replaced by "A deleted member" |
| platform.idempotency_key | replay snapshots | hard delete |
| outbox_event (4 schemas), notification_outbox payloads | queued events | member id replaced by tombstone |
| platform.erasure_receipt (new) | tombstone, date, counts | retained (proof of deletion) |
| Disk `.local-media`: profiles, moments, circle-posts/-docs/-covers/-albums, chat | uploaded files | removed (listed by the SQL function, deleted after commit) |
| rate_limit_counter | hashed key only | not personal, left |

Not touched on purpose: `covers/` event cover files (belong to the event, which stays), other members' data.

## RLS finding ("13 tables have no RLS")
Checked: none of the 13 holds member data that a member endpoint reads directly. Those with member ids (`activity.activity`, `notification_outbox`, `participation_status_history`, `trust_status`, `organization_scope`, `idempotency_key`, the four `outbox_event`) are all covered above. Erase runs as the table owner, so it works regardless of RLS.

## Retained (no name, contact or text)
Payment records for paid tickets/pledges; reports and blocks about or by the member; deletion receipt.


## Update 2026-11-22 (documents)
Documented in 01 (BR25), 02a (FR161-FR166), 03, 04, 05 (TC-216..227), 06, 07, 07a, 08 (section 14), 09, API-REFERENCE, RUNBOOK, TRACEABILITY, COVERAGE-REPORT, GLOSSARY. No deviation from the contract recorded for Milavn.
