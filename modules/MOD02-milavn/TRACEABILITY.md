# Traceability matrix - MOD02 Milavn (2026-11-22)

BR (business requirement, `01-business-requirements.md` plus addendum) to FR (`02`, `02a`) to screens (`03-ux.md` addendum, SCR-xx) to endpoints (`API-REFERENCE.md`, by method and path) to tables (`07a-er-model.md` appendix A) to tests (`05-test-scenarios.md`). Test column: A automated (file), M manual (QA-RUN or scenario), none = no test. FR001-FR088 detail rows exist inside `02`; this matrix is at feature-group level so that it stays accurate.

| BR | Title | FR | Screens | Main endpoints | Main tables | Tests |
|---|---|---|---|---|---|---|
| BR01 | Profile, locality, interest, language | FR001-003, FR127, FR146-147 | SCR-02, SCR-17 | POST /profile, PATCH /profile/place, PUT /profile/interests, GET /profile/places | member_profile, member_interest | A test_first_run; M QA-fun 19 |
| BR02 | Contextual discovery, explainable ranking | FR004-009, FR089, FR090, FR098, FR110-111, FR148 | SCR-03, SCR-04 | GET /discovery/* | occurrence, hidden_occurrence, ranking_weight_config | A test_discovery_fit, test_first_run |
| BR03 | Effortless creation, recurrence | FR010-014, FR090, FR131 | SCR-06 | POST /occurrences, PATCH /occurrences/{id}, POST .../series | activity, occurrence | M QA-prof 3, QA-fun 15 |
| BR04 | Participation and attendance | FR015-019, FR103-105, FR112, FR114, FR129 | SCR-05, SCR-07 | POST .../participation, .../checkin*, .../confirm, .../plan, .../regular, .../join-online | participation, participation_status_history, qr_checkin_token | A test_showing_up; M QA-prof 2 |
| BR05 | Circles | FR020-029, FR093, FR095, FR115-124, FR125, FR126, FR139-145, FR152-153, FR157 | SCR-08, SCR-09, SCR-10 | /circles/* | circle, circle_membership, join_request, circle_post*, circle_album*, poll*, fundraiser*, circle_group*, trip_stop, circle_invite* | A test_circle_posts_and_activity_chat, test_circle_suggestion_groups; M QA-community, QA-safety 20 |
| BR06 | Calendar | FR030-033, FR122 | SCR-11 | GET /calendar/*, GET /public/hosts/{id}/calendar.ics | calendar_follow | M golden-path |
| BR07 | Trust taxonomy | FR034-037 | SCR-05, SCR-15 | GET /people/reputation/{id} | trust_status, trust levels | M |
| BR08 | Earned reputation | FR034-037, FR117 | SCR-15 | GET /people/reputation/{id} | reputation_signal | M |
| BR09 | Privacy-first location | FR038-041, FR100, FR127, FR128 | SCR-02, SCR-17, SCR-05 | GET/PUT /privacy/location, GET /profile/places/nearest | location_precision_setting, consent_grant, occurrence_venue | M QA-safety 21 |
| BR10 | People discovery, not dating | FR042-045, FR094, FR106, FR116, FR119 | SCR-14, SCR-15 | GET /people/* , POST /people/meet-again | meet_again, free_now | A test_discovery_fit (partly) |
| BR11 | Public shareable pages | FR046-050, FR099, FR150 | SCR-05 | GET /public/occurrences/{slug} | occurrence | M (re-verify) |
| BR12 | Non-spam notifications | FR051-057, FR101, FR144, FR156, FR159 | SCR-16 | /notifications/* | notification_inbox_entry, notification_preference, reminder_sent | M QA-safety 20 |
| BR13 | Organizer tooling | FR058-060, FR132-137 | SCR-07 | /occurrences/{id}/attendees, announcements, ticket-admin, money, co-organizers | occurrence_update, occurrence_co_organizer | M |
| BR14 | Report, block, safety | FR061-065, FR155, FR160 | SCR-19 | /safety/*, /milavn/admin/* | report, block, moderation_action | A test_admin_queue_grouping |
| BR15 | Post-event feedback | FR066-069, FR107, FR108 | SCR-05 | /feedback/* | feedback, thanks | M |
| BR16 | External event ecosystem | none | none | none | none | planned, not built |
| BR17 | AI natural-language planning | FR089, FR090 | SCR-03, SCR-06 | /discovery/understand, /smart-fill | none (deterministic grammar, not a model) | A test_first_run |
| BR18 | Local commerce layer | none | none | none | none | planned, not built |
| BR19 | Anywhere in India | FR127 | SCR-02, SCR-06 | GET /profile/places | member_profile.locality_*, occurrence.locality_* | M QA-fun 19 |
| BR20 | Professional and large events | FR129-138 | SCR-05, SCR-06, SCR-07 | ticket-types, discount-codes, ticket, program, teams, followup | ticket_type, discount_code, ticket, event_* | A test_paid_spots (partly); M QA-professional |
| BR21 | Venue and link only after a confirmed spot | FR128, FR129 | SCR-05 | GET /occurrences/{id} | occurrence_venue | M QA-safety 21 |
| BR22 | Trusted women-only groups | FR140, FR141 | SCR-08, SCR-09 | /circles/gender/me, POST /circles | circle, member_gender, trip_stop | M QA-safety 23 |
| BR23 | Circles as communities | FR142-145, FR152-154, FR157 | SCR-09 | /circles/{id}/albums, /posts, /notify, /cohosts | circle_post_media, circle_album*, circle_notify_setting, occurrence_cohost | M QA-fun 15-16, QA-safety 20 |
| BR24 | One-step first run | FR146-148 | SCR-02, SCR-03 | PATCH /profile/place | member_profile | A test_first_run |
| (platform) | Messaging, payments | FR096-097, FR102, FR136 | SCR-12, SCR-13, SCR-18 | /chats/*, /payments/* | conversation, chat_message, ticket, payment_event | A test_chat_presence_hub, test_paid_spots |

Rows for BR07/BR08 and FR034-FR037 are taken from the sealed titles (trust and reputation); where the sealed FR numbering is not visible in this pass the grouping is *unverified*; check against `02-functional-requirements.md` headings. FR numbers 125-160 are defined in `02a`.

| BR25 | Account deletion (kinds A and B) | FR161-FR166 | Me (settings gear modal) | POST /privacy/delete-account-data, POST /internal/v1/members/{id}/erase | milavn_platform.erasure_receipt, erase_member(), 70 member-referencing tables | M proof run on member #32 (TC-216..227); browser check NOT done; no automated erase test |
