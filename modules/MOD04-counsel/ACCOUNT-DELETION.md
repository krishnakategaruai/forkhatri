# Counsel: account deletion

Contract: `docs/ParentApp/ACCOUNT-DELETION.md` (decided 2026-11-22). Immediate, transactional, idempotent.
Implementation: service code in `counsel-service/app/components/privacy.py` (`erase_member`), no database migration needed
(every change is a DELETE or an UPDATE inside one transaction as the normal `counsel_app` role; RLS is not used in Counsel and nothing was loosened).

## Entry points
| Path | Who | Notes |
|---|---|---|
| `POST /internal/v1/members/{member_id}/erase` | Identity service (kind A), service key `X-ForKhatri-Service: identity` | Returns `{module, status: done / nothing_to_delete, deleted{}, retained[], files_removed}`. A second call returns `nothing_to_delete`. |
| `POST /me/delete-account-data` (also the older `POST /me/delete`) | Signed-in member (kind B) | Body `{"confirm":"DELETE"}`, 3 attempts per hour per member, then the web app sends the member to the ForKhatri hub. The ForKhatri account is untouched; the member can enter Counsel later as a brand-new member. |
| `GET /me/deletion-check`, `GET /internal/v1/members/{id}/deletion-check` | Member / identity | No longer refuses. Returns `blockers`, now shown as warnings of what is closed on the member's behalf. |
| `GET /me/export` | Member | Extended to the full inventory (profile, services, packages, availability, files metadata, notifications, blocks, disputes, reports and more). |

UI: Counsel web, account page (`/me`), card "Your data": "Download my data" and "Delete my data in Counsel" (confirmation dialog listing what is deleted, what is kept and why, what is closed now; type DELETE; red button).

## What happens to other people
| Situation | Result |
|---|---|
| Future booking as consumer (pending payment or confirmed) | Cancelled by the normal cancel routine; expert gets notice `booking.cancelled_deleted`; refund row and ledger entry where a payment exists (cancellation-policy percentage). |
| Future booking as expert | Cancelled, consumer notified, full refund row. Under-way consultation: refunded in full (expert) or counted as held (consumer). |
| Open package or written question | Refunded and closed; other party notified (`purchase.closed_deleted`). Pending time requests: other party told, request deleted. |
| Completed consultations | Kept for the other person. Deleted member shows as "Deleted member" (stand-in member row). The deleted member's brief, messages, notes, action items, files and recording consent are removed. Recap text stays. |
| Reviews | Reviews about the deleted expert are deleted. Star ratings the deleted member gave stay (no name, no text). |
| Expert's services | Never-booked services and packages deleted. Services a booking or purchase still points to stay archived and blank under the stand-in expert. |

The stand-in id is `sha256("counsel-erased:" + member_id + service key)`, one way, per member. Rows that must stay point at it, never at the real id.

## Inventory (40 tables in schema `counsel`)
| Store | What it holds about a member | Action |
|---|---|---|
| member | name, language, time zone (the "mirror" of identity) | hard delete; stand-in row "Deleted member" inserted |
| provider | expert profile: headline, intro, photo, city, links | hard delete; if bookings, purchases or payouts point at it, a stripped stand-in row (suspended, no text) replaces it |
| provider_expertise, verification, badge_award, search_impression, profile_view | expert areas, verifications, badges, analytics | hard delete |
| provider_evidence | qualification details and encrypted proof documents | hard delete rows and files on disk |
| availability_rule, availability_exception | working hours | hard delete |
| payout_method | encrypted UPI or bank details | hard delete |
| service, package | offers | delete when never used; else archive, blank text, re-point to stand-in |
| booking | consultations | stay for the other party under the stand-in id; brief blanked; two deleted parties with no payment: deleted |
| message | chat and file messages | member's own deleted; system messages re-pointed to stand-in |
| file | consultation files and recordings the member uploaded (encrypted on disk) | hard delete rows and files |
| note | private notes (and shared note authorship) | private notes deleted; authorship to stand-in |
| action_item, call_feedback, recording_consent | follow-ups, call feedback, consent | hard delete the member's |
| session_event | join and leave log | re-point to stand-in (no personal data) |
| time_request | proposed custom times | hard delete both directions |
| purchase, question | packages and written questions | buyer re-pointed to stand-in; open ones refunded; question text and answer by the member blanked |
| payment, ledger_entry, payout | money | retained only where money moved (tombstoned through the booking, purchase or provider); payment attempts that never succeeded deleted |
| review | ratings and comments | about the member: deleted; by the member: stand-in, text blanked |
| dispute | opened by member | retained: stand-in, free text blanked |
| report | reports filed or about the member | retained for safety: stand-in id, detail blanked |
| expertise_request | proposed new expertise areas | pending deleted; decided ones: stand-in, note blanked |
| notification, delivery | in-app notices and queued messages | hard delete |
| block, saved_provider | blocks and saved people (both directions) | hard delete |
| audit_log | actions | retained for security: actor and target become the stand-in, detail naming the member cleared |
| erased_member | deletion receipt | one row per deletion (stand-in id, date, reason) plus an audit line with counts |
| expertise_area, compliance_rule, platform_setting | catalogue and settings, no member data | not applicable |

Files on disk (`STORAGE_ROOT`): evidence documents (`private/evidence/<member>/`), photo (`public/photos/<member>/`, whole folder swept, including replaced uploads), consultation files (`file.storage_key`). Removed after the transaction commits. Call tickets are signed and in memory; cached sessions, names and tickets of the member are dropped.

## Retained (shown to the member in plain words)
Consultations other people took part in (as "Deleted member"); payment and tax rows where money moved; star ratings without text; safety report records; audit trail with the stand-in id; one deletion receipt. All need a lawyer's confirmation (see `docs/Critique`).
Known gap for the owner: an expert's earnings that are eligible but not yet paid out (`payout_status = eligible`) cannot be paid after payout details are deleted; the member is warned before confirming.

## Check
Counsel has no pytest suite. `counsel-service/scripts/check_account_deletion.py` is a repeatable end-to-end check (throwaway member #34 as consumer and expert, QA members #1 and #2); it cleans up after itself. Last run: all 16 checks passed.
