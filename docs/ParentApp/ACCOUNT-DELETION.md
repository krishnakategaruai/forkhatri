# Account deletion: design and contract (decided 2026-11-22)

Owner requirement (2026-11-22): "A user should be deleted if he needs to delete his account, immediately. If he is doing it from ForKhatri, all the accounts in sub modules and traces should be deleted. If he is doing it in an independent module, that module's data related to him, all the stuff, should be deleted."

## Two kinds of deletion

| | Where the member does it | What is deleted | What stays |
|---|---|---|---|
| **A. Delete my ForKhatri account** | Hub, account sheet: "Delete my ForKhatri account" | The ForKhatri identity AND the member's data in EVERY module (Vyapar, Milavn, Mangalya, Counsel), all sessions, credentials, uploads, notifications | Only what the law or other people's safety forces (see "Retained"), with no name, phone, email, photo or free text |
| **B. Delete my data in one module** | That module's own settings: "Delete my data in <Module>" | Everything that module holds about the member | The ForKhatri identity and the other modules' data. The member can enter the module again later as a brand-new member |

Both are IMMEDIATE (no waiting period). The member must confirm with their sign-in (password or one-time code) and by typing the word DELETE, because the action cannot be undone.

## Flow for A (orchestrated by the identity service)
1. Member confirms (re-authentication + typed DELETE). The identity service revokes ALL the member's sessions at once (they are signed out everywhere immediately).
2. Identity calls every registered module's internal endpoint (below) with the service key, in parallel, and records each result.
3. When every module answers `done`, identity deletes: sessions, password credential, handoff codes, member row (phone, email, name, language), notification preferences, admin role assignments, and replaces the member's id in audit-log rows with a one-way tombstone hash.
4. If a module is unreachable or fails: the member is already signed out and the identity row is marked `deleting` (the member cannot sign in); identity retries the failed modules (backoff, up to 7 days, an admin sees a "stuck deletions" list) and removes the identity row only when all modules have confirmed. The member sees a plain message: "Your account is closed. Deletion of the rest is finishing."
5. The member sees a short confirmation page (and gets an email/SMS to the old contact only if one was on file and a sender exists) listing what was deleted and what is retained and why.

## Module contract
Every module exposes (internal, service-key authenticated, idempotent):

`POST /internal/v1/members/{member_id}/erase`  
Headers: `X-ForKhatri-Service: <module>`, `X-ForKhatri-Service-Key: <key>` (same mechanism as the existing internal endpoints).  
Response `200`: `{"module": "<name>", "status": "done" | "nothing_to_delete" | "partial", "deleted": {"<kind>": <count>, ...}, "retained": [{"kind": "...", "reason": "..."}], "files_removed": <n>}`  
Calling it again after `done` returns `nothing_to_delete`. `partial` means retry later.

The member-facing version (kind B), session-authenticated by the module's normal auth, re-confirmed in the request body:

`POST /privacy/delete-account-data` (path may follow each module's existing privacy routes) body `{"confirm":"DELETE"}` → performs the same erase for the signed-in member only, then signs the member out of that module.

## What "delete" means for each kind of data
- The member's own profile, photos, documents, files, voice clips, notes, drafts, preferences, saved items, search history, notifications, device/push registrations, uploaded media files on disk: HARD DELETE (rows and files).
- Messages and posts the member wrote, comments, reactions, polls votes: HARD DELETE (other people's conversations show "Deleted member" in place of the name).
- Events/circles/listings/posts the member owns: future events are cancelled with attendees notified (and refunded where a payment exists); circles transfer to the longest-standing co-organizer, or are deleted if none; open jobs/listings are closed and removed; past events stay for the people who attended with the host shown as "Deleted member" and no contact details.
- Requests, connections, bookings, quotes, enquiries the member sent or received: deleted for the member; the other party's view shows "Deleted member".
- In Mangalya, a profile the member MANAGES for a son or daughter who has not taken it over is deleted with them; a profile the child has taken over stays with the child.
- Reports the member FILED about others, and reports filed ABOUT the member, are kept only in minimal pseudonymised form (see Retained).

## Retained (only what must stay), with no identifying details
- Payment and tax records, when real money has moved (legal retention; the sandbox holds none today). Stored with a tombstone id, amount, date.
- A moderation/safety record that someone was reported or banned, so a deleted member cannot simply return and harm others: tombstone hash only, no name/contact/text.
- Server and security logs for the minimum legal period (DPDP Rules, 1 year for logs): the member's id replaced by the tombstone hash, no contact or free text.
- A one-line deletion receipt (tombstone hash, date, modules, counts) so the owner can prove deletion was done.
Each of these is shown to the member in plain words on the confirmation page. They are documented in docs/Critique as needing a lawyer's confirmation.

## Safety rails
- Re-authentication + typed DELETE required. Admin/owner accounts with role assignments need the role removed first (an admin cannot be deleted while they hold the only copy of a two-person approval).
- Rate limit: 3 attempts per hour per member.
- Never delete other members' data. Never touch another module from a module's endpoint.
- Test with throwaway members only (never the built-in personas, never krishna).
- Idempotent and resumable: safe to run twice.

## As built (identity and hub, 2026-11-22)

**Identity inventory** (every identity store holding the member, and its fate):

| Store | Fate |
|---|---|
| `identity.member` (name, phone, email, language, level) | Closed (status `deleted`) at once; hard-deleted when every module confirmed |
| `identity.session` | All revoked at the start; rows deleted at the end |
| `identity.password_credential` | Hard delete |
| `identity.otp_challenge` (by phone/email) and `platform.rate_limit_counter` keys for them | Hard delete |
| `registry.member_module_entry` (module visits) | Hard delete |
| `governance.role_assignment`, `approval_request` (about or by the member), `suspension` | Hard delete; deletion is refused while the member holds a live admin role (409 `admin_role_held`). A ban is kept only as a flag in the receipt |
| `governance.audit_event` | Member id replaced by a one-way tombstone (`actor_tombstone` / `target_tombstone`, HMAC-SHA256 of the id with `DELETION_TOMBSTONE_PEPPER`); notes, subject, details and ip about the member cleared |
| Sign-in hand-off codes | In memory, 60 s life, hold no member data |
| Notification preferences / inbox | None exist in identity (the hub bell is an empty state) |

**Endpoints** (identity, migration `db/migrations/008-account-deletion.sql`, applied as `identity_owner`):
`GET /v1/account/delete/preview`, `POST /v1/account/delete/code` (one-time code to the member's own phone/email), `POST /v1/account/delete` with `{confirm:"DELETE", password | challenge_id+code}`, `GET /v1/account/deletion/{job_id}` (public progress and receipt; the job id is the capability because the member is already signed out), admin `GET /v1/admin/deletions/stuck` and `POST /v1/admin/deletions/{job_id}/retry`.
Re-authentication is a new step-up (none existed): password, or a fresh code sent only to the member's own identifier. Every attempt counts toward 3 per hour.

**Flow.** Start closes the member and revokes all sessions, writes `identity.deletion_job` plus one `deletion_job_module` row per module in `SERVICE_KEYS`, clears the cookie, then runs in the background. Identity calls `POST {base}/internal/v1/members/{id}/erase` on all modules in parallel with headers `X-ForKhatri-Service: identity` (Counsel requires exactly this name) and the module's own service key. Base URLs: `ERASE_MODULE_API_URLS`, falling back to `ADMIN_MODULE_API_URLS` and `MODULE_API_URLS`; a registered module with no URL stays `failed: not_configured` (never skipped). A 404, other non-200, timeout or `partial` is retried with backoff 30 s doubling to 6 h by a loop every 30 s, for 7 days; after that, or after 3 failed attempts, the job is on the admin "stuck deletions" list (Modules page) with a Retry button. Identity rows are removed only when all modules are `done` or `nothing_to_delete`, by the SECURITY DEFINER function `identity.finalize_member_deletion` (the runtime role still has no DELETE grant). The job then keeps only the receipt (tombstone, per-module counts, retained list with reasons) and its `member_id` is nulled.

**Hub.** Account sheet, "Delete my ForKhatri account" opens a sheet: what is deleted, what is kept and why, password or code, type DELETE, red button, per-module progress, final receipt page, then "Return to ForKhatri" shows the entrance. The sheet cannot be dismissed once deletion has started. English strings were added to all five locale dictionaries.

**Proof (throwaway member #30).** Data in all four modules, then deletion via the API: all four modules `done` on attempt 1; zero identity rows left (member, sessions, password, entries, codes); old session 401; second erase on Vyapar and Mangalya answers `nothing_to_delete`; the Mangalya photo is gone. Orchestrator tests with a stub module server (`tests/integration/test_account_deletion.py`) cover a failing then recovering module, backoff, partial answers, audit tombstone rewrite, idempotence and the admin-role block.

**Left / notes.** Retained across the system: security log (tombstone only) and deletion receipts; a banned member is recorded only as a flag in the receipt (no sign-up block is enforced yet). Browser rendering of the hub sheet was type-checked but not screenshot-verified.
