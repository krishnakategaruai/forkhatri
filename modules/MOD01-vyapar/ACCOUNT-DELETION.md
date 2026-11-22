# Vyapar: account deletion (kind A and kind B)

Contract: `docs/ParentApp/ACCOUNT-DELETION.md`. Implemented by migration `07a-db-implementation/migrations/033-erase-member.sql` (function `vyapar_identity.erase_member(member, analytics_pseudonym)`, SECURITY DEFINER, owner `vyapar_owner`, guarded: only the member's own request context or the service/dispatcher context) and `vyapar-service/app/services/privacy.py`.

Entry points (all call the same function, one transaction, idempotent):
- Kind A (ForKhatri account): `POST /internal/v1/members/{member_id}/erase` (service key). Returns `{module, status: done|nothing_to_delete, deleted{}, retained[], files_removed}`. An operator mirror (`is_operator`) is refused with 409 until the role is removed.
- Kind B (Delete my data in Vyapar): `POST /v1/privacy/delete-account-data` body `{"confirm":"DELETE"}`, member session only (never an access token), 3 per hour. The old `POST /v1/privacy/delete` still works and now performs the full erase. UI: Profile > Privacy > "Delete my data in Vyapar" (list of deleted and kept, type DELETE, red button, then back to the entrance).
- After erase the Vyapar mirror row is gone; the next sign-in of the same ForKhatri member creates a fresh blank mirror (`ensure_member`).
- Other members' records that pointed at the member now point at a one-way tombstone member `del_<hash>` ("Deleted member").

## Inventory (63 tables, 13 schemas: all inspected)

| Store | Holds | Action |
|---|---|---|
| identity.members | mirror: name, phone, location, avatar, call rules, badges | hard delete; tombstone member row (hash only) added |
| listings.listings (+ listing_contacts, listing_packages, member_listing, otp_challenges) | work/business profile, photos, contacts, packages, saved/viewed, OTP | hard delete (own); saved/viewed by the member also deleted |
| listings.verification_records, council_credentials | ID document images and masked/encrypted ids, credentials | hard delete + files removed |
| listings.taxonomy_terms, profession_rules | shared reference | not member data |
| opportunities.opportunities, member_opportunity, saved_searches | posts, images, saved, hidden, saved searches | hard delete |
| enquiries.enquiries | proposals/quotes/enquiries received (provider, or on own listing/post) | hard delete |
| enquiries.enquiries (sent) | requests sent to others | other party keeps the thread, sender becomes tombstone, profile snapshot, answers, milestones cleared |
| enquiries.enquiry_messages, contact_attempts, blocks | messages, call log, blocks | hard delete (attachments removed) |
| enquiries.partnership_requests | requests either way | hard delete (also for the other party, the listing is gone) |
| contracts.contracts, milestones, ledger, timesheets, events, disputes | work contracts | kept for the other party: member replaced by tombstone, open contracts cancelled, event data and dispute notes cleared |
| reviews.reviews, review_invites, review_disputes, paid_on_time_asks | written, received, invites | hard delete |
| commercial.campaigns, promotions, entitlements, workspace_members, impressions, commercial_order_history | boosts, plans, team access, views | hard delete (workspace `invited_by` on others' rows becomes tombstone) |
| payments.payment_orders | money records | RETAIN: tombstone id, amount, date; gateway events cleared (legal retention) |
| privacy.* (settings, acceptances, data_requests, derived_preferences, member_taste) | settings, consent, requests, learned taste | hard delete; one receipt row (tombstone, counts) added |
| trust_safety.reports, moderation_cases, appeals | reports filed or about the member, appeals | RETAIN minimal: tombstone id, no text or evidence |
| integration.access_tokens, webhook_subscriptions/deliveries, notifications, ai_events, counsel_referrals, dead_letters | tokens, hooks, inbox, AI log, referrals | hard delete |
| integration.audit_events | security log | RETAIN: id replaced by tombstone, details cleared |
| analytics.analytics_events | events by pseudonym | hard delete by pseudonym |
| platform.idempotency_key, rate_limit_counter | request bookkeeping | hard delete |
| *.outbox_event (listings, opportunities, enquiries, reviews, commercial) | event payloads | delete rows mentioning the member |
| integration.config, webhook_cursors, commercial.products, privacy.legal_documents | shared | not member data |
| Uploaded files on disk | photos, ID images, attachments | removed: every file named in a deleted row plus anything named `<member>-*` |
| Voice interviews | no stored audio or transcript (AI log only, above) | n/a |

## Known limits
- Other people's notifications and retained safety rows may still mention ids of deleted listings or posts (ids only, no member data).
- Sandbox only: no real money exists, so no refund call is made; with a real gateway the retained payment orders must be refunded first.
- Kind B leaves the ForKhatri session valid by design; only kind A ends sessions (identity does that).
