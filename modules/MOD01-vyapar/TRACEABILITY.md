# MOD01 Vyapar traceability matrix (2026-11-22)

**Document status:** as built, 2026-11-22. Feature-level mapping BR -> FR -> screens -> endpoints (by API-REFERENCE tag, which lists every API-nnn) -> tables (see 07a-er-model-as-built.md) -> tests. Per-endpoint rows are in API-REFERENCE.md; this matrix is deliberately at tag level so it stays accurate. Screens SCR-nn are defined in 03-ux.md addendum.

| BR | FR | Screens | Endpoints | Tables | Tests |
|---|---|---|---|---|---|
| BR01,BR02 | FR01-FR07 | SCR-17,SCR-09 | tag profile, listings, listing-packages, first-run | vyapar_listings.*, vyapar_identity.members | check_profile.py |
| BR03,BR16 | FR08-FR10,FR47 | SCR-17,SCR-25 | tag verification, admin-verification | vyapar_listings (verification), vyapar_platform | manual |
| BR04 | FR11-FR14,FR55,FR58 | SCR-05,SCR-06,SCR-16 | tag opportunities | vyapar_opportunities.* | check_structured_hiring.py |
| BR05,BR06 | FR15-FR20,FR64 | SCR-01,SCR-03,SCR-08 | tag discovery, feed, saved-searches, recommendations | vyapar_opportunities, vyapar_listings, taste tables | check_taste.py, eval_recommendations.py |
| BR06 | FR21,FR70 | SCR-16 (bell) | tag notifications | notification tables (vyapar_platform/identity) | manual |
| BR07 | FR22-FR24,FR61 | SCR-11,SCR-07,SCR-18 | tag enquiries, contact | vyapar_enquiries.* | check_backend_b.py |
| BR08 | FR25-FR26 | SCR-15 | tag partnerships | vyapar_reviews/partnership tables | manual |
| BR09 | FR27-FR29,FR62 | SCR-06,SCR-23 | tag reviews, reputation, trust | vyapar_reviews.* | check_trust_pack.py |
| BR10,BR11 | FR30-FR35,FR54 | SCR-14,SCR-10,SCR-13 | tag commercial, payments, workspace, campaigns, admin-commercial | vyapar_commercial.*, vyapar_payments.* | manual |
| BR23 | FR59 | SCR-12,SCR-13 | tag contracts | vyapar_contracts.* | check_contracts.py |
| BR12 | FR36-FR38,FR53 | SCR-21,SCR-19 | tag privacy | vyapar_privacy.* | manual |
| BR13 | FR39-FR41,FR62 | SCR-20,SCR-22,SCR-25 | tag trust-safety, admin-moderation | vyapar_trust_safety.* | check_trust_pack.py |
| BR14,BR19,BR20 | FR42-FR44,FR56,FR57,FR63,FR65 | SCR-02 | tag first-run, voice, taxonomy | vyapar_identity.members, vyapar_listings.taxonomy_terms | check_voice_interview.py, check-i18n-keys.py |
| BR15 | FR45,FR46 | SCR-25 (ops) | tag events, admin-ops | vyapar_analytics.analytics_events | manual |
| BR17,BR22 | FR50-FR52,FR66,FR67 | (none, API) | tag integrations, internal-bridges | vyapar_integration.* | manual |
| BR16 | FR48,FR49,FR69 | SCR-25 | tag admin-console, admin-audit | vyapar_platform.* | check_admin_console.py |
| BR21 | FR60 | SCR-05 | tag ai | AI counters | check_ai.py |

Table-to-feature detail: unverified at column level; verify by reading the router and service named after the tag (vyapar-service/app/routers/<tag>.py).


## Account deletion (added 2026-11-22)
| BR | FR | Screens | Endpoints | Tables | Tests |
|---|---|---|---|---|---|
| BR24 | FR71-FR73 | SCR-21 (Privacy) | API-269, API-270, API-175 | all 63 (see ACCOUNT-DELETION.md), function vyapar_identity.erase_member | manual proof on throwaway member #31 (TC-701 to TC-707); browser not checked |
