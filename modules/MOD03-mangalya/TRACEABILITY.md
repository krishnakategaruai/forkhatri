# MOD03 Mangalya - Traceability matrix (as built 2026-11-22)

Covers the as-built FRs (FR103-FR134, see `02-functional-requirements.md`) and the links from the older BR01-BR20 / FR001-FR102 set by area. Endpoint groups refer to tags in `API-REFERENCE.md`; table ids to `07a-data-model-appendix.md`; tests to `05-test-scenarios.md`.

| BR | FR | Screens | Endpoints (tag) | Tables | Tests |
|---|---|---|---|---|---|
| BR26 | FR103-FR104 | SCR-01, SCR-03 | profile, discovery | profile | TC-103 (M) |
| BR26 | FR105-FR108 | SCR-03 | profile (`POST /profile`, places, photos, `PATCH /profile/{category}`) | profile, profile_media, profile_attribute | TC-105, TC-107, TC-107b (M) |
| BR26 | FR109 | SCR-03 | none | none (IndexedDB) | TC-109 (M) |
| BR26 | FR110 | SCR-03 | profile (biodata, documents) | profile_document | TC-110 (M) |
| BR26 | FR111-FR112 | SCR-03, SCR-01 | profile (managed, claim, disown) | account, account_alias, profile | TC-111, TC-112 (M) |
| BR26, BR02 | FR113-FR114 | SCR-05, SCR-07 | profile (completeness, member) | member_profile | M |
| BR28 | FR115 | all | none | none | TC-115 (M), locale parity script |
| BR02, BR03 | FR116-FR118 | SCR-12 | home_circle | membership, invitation, home_circle_note, suggestion | TC-116 (M); `check_home_circle.py`, `check_family_notes.py` |
| BR22 | FR119 | SCR-08 | profile (matchmaker) | profile_attribute | TC-119 (M); `test_matching_engine.py` (A) |
| BR22, BR06, BR07 | FR120-FR121, FR123 | SCR-11, SCR-04 | discovery, shortlist | discovery_profile_index, daily_pick, shortlist | TC-120 (M); `test_discovery_ranking.py` (A) |
| BR23 | FR122 | SCR-14, SCR-04 | horoscope | horoscope, chart, match | TC-122 (A) |
| BR11, BR12 | FR124 | SCR-04, SCR-13 | connections | connection_request, sharing_grant, family_contact_share | `check_family_sends_request.py` |
| BR11 | FR125-FR126 | SCR-13 | messages, conversations, notifications | conversation, message, conversation_participant, inbox_entry | TC-125, TC-125b (M) |
| BR27 | FR127 | SCR-09 | verification | member_face_match, biometric_consent | TC-127, TC-127b (M) |
| BR14, BR30 | FR128-FR129 | SCR-25, ops | safety, operations, admin | report, block, case, account_suspension, operator | TC-129 (M) |
| BR21 | FR130 | SCR-15 | billing | plan_subscription, order, plan_price, webhook_event | TC-130 (M) |
| BR24 | FR131 | SCR-19 to SCR-22 | agents | offline_profile, agent_contact_view, agent_export, agent_limit, contact_report | TC-131 (M); `check_agents.py`, `check_agent_limits.py` |
| BR29 | FR132 | SCR-23 | rm | relationship_manager, rm_assignment, rm_suggestion, rm_interaction | M |
| BR25 | FR133-FR134 | SCR-16, SCR-17 | wedding, guides | connection_stage, osm_place, partner, partner_offer, guide | TC-133 (M) |

Older set (kept): BR01-BR20 map to FR001-FR102 inside `02-functional-requirements.md` (each FR lists its BR). Their as-built status by area: auth FR089-FR101 built (legacy interim auth retired into the ForKhatri identity); Home Circle FR007-FR016 built; discovery FR025-FR032 built (ranking replaced by DEC-V1-031); verification FR033-FR044 changed (document verification dropped, face match instead - DEC-V1-016); chat FR049-FR056 built as three chat kinds; safety FR064-FR076 built, thin human review.
