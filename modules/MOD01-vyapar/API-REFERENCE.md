# Vyapar API reference (as built, 2026-11-22)

**Document status:** as built, 2026-11-22. Generated from the running service (`GET http://localhost:8011/openapi.json`, 268 operations) and from the route files in `vyapar-service/app/routers/`. Re-generate when routes change.

Conventions: every error uses the envelope `{"detail": ..., "error": {"code","message","details"}}` (see architecture.md section Error model). Language comes from `Accept-Language` or the member language (en, hi, te, mr, kn). `*` after a parameter = required; `(path)` = path parameter. Auth column: **member session** = resolved through the identity adapters (session cookie, bearer personal token, or dev header in dev mode); **member + admin scope** = also needs an admin scope from the platform; **service key** = platform-to-Vyapar bridge (`/internal/v1`, X-ForKhatri-Service key); **dev only** = only when DEV_MODE; **public / special** = no member context required in code (for example taxonomy reads, payment webhook) ; **see source** = the heuristic could not decide (operation id built dynamically); verify in the router file. Per-endpoint finer permission (owner-only, workspace role, entitlement) is enforced in the service layer and is not visible in OpenAPI.

## Contents

- [uploads](#uploads) (1)
- [first-run](#first-run) (7)
- [taxonomy](#taxonomy) (1)
- [profile](#profile) (4)
- [member-settings](#member-settings) (2)
- [discovery](#discovery) (2)
- [contact](#contact) (9)
- [listings](#listings) (17)
- [listing-packages](#listing-packages) (4)
- [feed](#feed) (7)
- [saved-searches](#saved-searches) (3)
- [opportunities](#opportunities) (24)
- [reputation](#reputation) (1)
- [notifications](#notifications) (5)
- [enquiries](#enquiries) (12)
- [verification](#verification) (2)
- [admin-verification](#admin-verification) (5)
- [trust-safety](#trust-safety) (5)
- [admin-moderation](#admin-moderation) (4)
- [reviews](#reviews) (5)
- [partnerships](#partnerships) (5)
- [commercial](#commercial) (9)
- [admin-commercial](#admin-commercial) (6)
- [payments](#payments) (3)
- [workspace](#workspace) (10)
- [campaigns](#campaigns) (6)
- [admin-ops](#admin-ops) (10)
- [internal-bridges](#internal-bridges) (1)
- [privacy](#privacy) (10)
- [events](#events) (1)
- [admin-audit](#admin-audit) (1)
- [dev](#dev) (8)
- [integrations](#integrations) (11)
- [contracts](#contracts) (22)
- [ai](#ai) (5)
- [admin-console](#admin-console) (20)
- [trust](#trust) (13)
- [voice](#voice) (2)
- [recommendations](#recommendations) (4)
- [untagged](#untagged) (1)


## uploads

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-001 | POST | /v1/uploads | uploadFile | Upload an image file and get its public URL | X-Dev-Member-Id | Body_uploadFile | 201:UploadOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## first-run

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-002 | GET | /v1/first-run/state | getFirstRunState | Get the member's first-run onboarding state | X-Dev-Member-Id | - | 200:FirstRunState 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-003 | GET | /v1/first-run/capability-options | listCapabilityOptions | List capability (skill) options for onboarding | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[TaxonomyOptionOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-004 | GET | /v1/first-run/category-options | listCategoryOptions | List business category options for onboarding | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[CategoryOptionOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-005 | GET | /v1/first-run/scoped-capability-options | listScopedCapabilityOptions | List capability options scoped to chosen categories | categories, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[TaxonomyOptionOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-006 | POST | /v1/first-run/step | saveFirstRunStep | Save one onboarding step | X-Dev-Member-Id | FirstRunStepInput | 200:FirstRunState 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-007 | GET | /v1/first-run/trade-tiles | listTradeTiles | Picture-tile trades for the start, by goal (find_work / get_customers) | goal, X-Vyapar-Language | - | 200:list[TradeTileOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-008 | POST | /v1/first-run/start | completeStart | Save the 3-question start (goal, trades, area) in one call and go live where the rules allow | X-Vyapar-Language, X-Dev-Member-Id | StartInput | 200:StartOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## taxonomy

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-009 | GET | /v1/taxonomy/tree | getTaxonomyTree | Categories with their skills and roles, localized | X-Vyapar-Language | - | 200:TaxonomyTreeOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |

## profile

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-010 | GET | /v1/me/profile | getMyProfile | The member's one profile, created from the ForKhatri identity on first read | X-Vyapar-Language, X-Dev-Member-Id | - | 200:MyProfileOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-011 | PATCH | /v1/me/profile | updateMyProfile | Update the member's profile, including its business section | X-Vyapar-Language, X-Dev-Member-Id | ProfilePatch | 200:MyProfileOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-012 | POST | /v1/me/profile/locate | locateMyProfile | Nearest known locality for the browser's current position, with nearby areas for one-tap chips | X-Vyapar-Language, X-Dev-Member-Id | LocateIn | 200:LocateOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-013 | GET | /v1/me/profile/completion | getMyProfileCompletion | How complete the profile is, and the one next question to ask (never blocking) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:CompletionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## member-settings

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-014 | GET | /v1/members/me | getMe | Get the signed-in member's basic settings | X-Vyapar-Language, X-Dev-Member-Id | - | 200:MemberMeOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-015 | PATCH | /v1/members/me/language | setMemberLanguage | Set the signed-in member's preferred language | X-Dev-Member-Id | LanguagePatch | 200:LanguageOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |

## discovery

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-016 | GET | /v1/listings/search | searchListings | Search business and professional listings | q, category, locality, radius_km, service_mode, availability, verified_only, include_unverified, sort_by, skills, broaden_attempt, limit, X-Vyapar-Language, X-Dev-Member-Id | - | 200:SearchResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-017 | GET | /v1/listings/search-suggestions | getSearchSuggestions | Get search suggestions for a partial query | X-Vyapar-Language, X-Dev-Member-Id | - | 200:SearchSuggestionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |

## contact

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-018 | GET | /v1/listings/contact-preferences | getContactPreferences | Get how the member allows others to call or message them | X-Dev-Member-Id | - | 200:ContactPreferencesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-019 | PATCH | /v1/listings/contact-preferences | updateContactPreferences | Update the member's call hours, days, daily cap and channels | X-Vyapar-Language, X-Dev-Member-Id | ContactPreferencesPatch | 200:ContactPreferencesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-020 | GET | /v1/listings/{listing_id}/contact-preferences | getListingContactPreferences | Get one listing's contact preferences (owner) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingContactPreferencesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-021 | PATCH | /v1/listings/{listing_id}/contact-preferences | updateListingContactPreferences | Override contact preferences for one listing (owner) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ContactPreferencesPatch | 200:ListingContactPreferencesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-022 | GET | /v1/enquiries/{enquiry_id}/contact-actions | getEnquiryContactActions | Call / WhatsApp actions for an accepted enquiry, per the other person's preferences | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContactActionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-023 | GET | /v1/enquiries/{enquiry_id}/contact-attempts | listContactAttempts | Who called or messaged whom on this enquiry, and when | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ContactAttemptOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-024 | POST | /v1/enquiries/{enquiry_id}/contact-attempts | recordContactAttempt | Record that the member is calling or messaging the other person now | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ContactAttemptIn | 201:ContactActionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-025 | GET | /v1/opportunities/{opportunity_id}/contact-actions | getOpportunityContactActions | Call / WhatsApp the poster before an application is accepted (when the post allows it) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PrecallActionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-026 | POST | /v1/opportunities/{opportunity_id}/contact-attempts | recordOpportunityContactAttempt | Record a pre-accept call or WhatsApp tap on an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ContactAttemptIn | 201:PrecallAttemptOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## listings

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-027 | POST | /v1/listings | createListing | Create a business or professional listing | X-Vyapar-Language, X-Dev-Member-Id | ListingCreate | 201:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-028 | GET | /v1/listings/mine | listMyListings | List the signed-in member's own listings | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ListingOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-029 | GET | /v1/listings/mine/page | listMyListingsPage | List the signed-in member's own listings, one page at a time | limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_ListingOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-030 | GET | /v1/listings/{listing_id} | getListing | Get one listing's profile | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-031 | PATCH | /v1/listings/{listing_id} | updateListing | Update a listing's details | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ListingPatch | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-032 | GET | /v1/listings/{listing_id}/similar | listSimilarProfiles | List profiles similar to a listing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ProfileCard] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-033 | POST | /v1/listings/{listing_id}/save | saveListing | Save a listing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-034 | DELETE | /v1/listings/{listing_id}/save | unsaveListing | Remove a listing from saved | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-035 | PATCH | /v1/listings/{listing_id}/contacts | updateListingContacts | Update a listing's contact channels | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ContactsPatch | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-036 | PATCH | /v1/listings/{listing_id}/visibility | updateListingVisibility | Update a listing's visibility | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | VisibilityPatch | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-037 | PATCH | /v1/listings/{listing_id}/intent | updateListingIntent | Update a listing's intent (what it is looking for) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | IntentPatch | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-038 | POST | /v1/listings/{listing_id}/submit | submitListing | Submit a draft listing for publishing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-039 | POST | /v1/listings/{listing_id}/archive | archiveListing | Archive a listing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-040 | POST | /v1/listings/{listing_id}/suspend | suspendListing | Suspend a listing | listing_id*(path), reason*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-041 | POST | /v1/listings/{listing_id}/otp/request | requestListingContactOtp | Request an OTP to verify a listing contact | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | OtpRequestIn | 200:OtpRequestOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-042 | POST | /v1/listings/{listing_id}/otp/verify | verifyListingContactOtp | Verify a listing contact with an OTP | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | OtpVerifyIn | 200:OtpVerifyOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-043 | POST | /v1/listings/{listing_id}/credential-ref/attach | attachListingCredentialRef | Attach a platform credential reference to a listing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ListingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## listing-packages

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-044 | GET | /v1/listings/{listing_id}/packages | listListingPackages | List a listing's service packages (basic / standard / premium) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[PackageOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-045 | PUT | /v1/listings/{listing_id}/packages | upsertListingPackages | Create or update up to three package tiers (owner) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | PackagesUpsertIn | 200:list[PackageOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-046 | DELETE | /v1/listings/{listing_id}/packages/{package_id} | deleteListingPackage | Delete one package tier (owner) | listing_id*(path), package_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[PackageOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-047 | POST | /v1/listings/{listing_id}/packages/{package_id}/request | requestListingPackage | Request a package: opens an enquiry tagged with it | listing_id*(path), package_id*(path), Idempotency-Key, X-Vyapar-Language, X-Dev-Member-Id | PackageRequestIn | 201:PackageRequestOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## feed

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-048 | GET | /v1/opportunities/feed/results | listOpportunityResults | One flat ranked list for a search or filters, with its total and facet counts | limit, skills, q, type, work_mode, radius_km, availability, sort, sort_by, types, pay_kind, pay_min_paise, pay_max_paise, posted_within, shift, experience, verified_only, segment, lat, lng, X-Vyapar-Language, X-Dev-Member-Id | - | 200:ResultsResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-049 | GET | /v1/opportunities/feed/rows | listOpportunityRows | The Discover home as themed rows (For you, Near you, categories, New today, ...) | lat, lng, X-Vyapar-Language, X-Dev-Member-Id | - | 200:RowsResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-050 | GET | /v1/opportunities/feed | listOpportunityFeed | Get the member's opportunity feed | skills, q, type, work_mode, radius_km, availability, sort, sort_by, types, pay_kind, pay_min_paise, pay_max_paise, posted_within, shift, experience, verified_only, segment, lat, lng, X-Vyapar-Language, X-Dev-Member-Id | - | 200:FeedResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-051 | GET | /v1/opportunities/feed/section/{section_key} | listOpportunityFeedSection | Get all items in one feed section | section_key*(path), skills, q, type, work_mode, radius_km, availability, sort, sort_by, types, pay_kind, pay_min_paise, pay_max_paise, posted_within, shift, experience, verified_only, segment, lat, lng, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[FeedCard] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-052 | GET | /v1/opportunities/feed/section/{section_key}/page | listOpportunityFeedSectionPage | Get one feed section, one page at a time | section_key*(path), limit, cursor, skills, q, type, work_mode, radius_km, availability, sort, sort_by, types, pay_kind, pay_min_paise, pay_max_paise, posted_within, shift, experience, verified_only, segment, lat, lng, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_FeedCard_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-053 | GET | /v1/opportunities/{opportunity_id}/why | getOpportunityWhy | Explain why an opportunity is shown to the member | opportunity_id*(path), X-Dev-Member-Id | - | 200:WhyResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-054 | GET | /v1/activity | getActivity | Get the member's activity (saved, applied, posted, received) | X-Dev-Member-Id | - | 200:ActivityResponse 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## saved-searches

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-055 | POST | /v1/opportunities/saved-searches | saveSearch | Save the current opportunity search, optionally with alerts | X-Vyapar-Language, X-Dev-Member-Id | SavedSearchIn | 201:SavedSearchOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-056 | GET | /v1/opportunities/saved-searches | listSavedSearches | List the member's saved searches | X-Dev-Member-Id | - | 200:list[SavedSearchOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-057 | DELETE | /v1/opportunities/saved-searches/{search_id} | deleteSavedSearch | Delete a saved search | search_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:DeletedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## opportunities

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-058 | POST | /v1/opportunities/jobs/expire | runOpportunityExpiry | Expire posts whose last date has passed, now (dev only; runs hourly anyway) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:ExpiryPassOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-059 | POST | /v1/opportunities | createOpportunity | Create an opportunity draft | X-Vyapar-Language, X-Dev-Member-Id | OpportunityCreate | 201:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-060 | GET | /v1/opportunities/mine | listMyOpportunities | List opportunities posted by the signed-in member | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[OpportunityOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-061 | GET | /v1/opportunities/mine/page | listMyOpportunitiesPage | List opportunities posted by the signed-in member, one page at a time | limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_OpportunityOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-062 | GET | /v1/opportunities/{opportunity_id} | getOpportunity | Get one opportunity with decision context | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-063 | PATCH | /v1/opportunities/{opportunity_id} | updateOpportunity | Update an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | OpportunityPatch | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-064 | GET | /v1/opportunities/{opportunity_id}/similar | listSimilarOpportunities | List opportunities similar to one opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[OpportunityOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-065 | GET | /v1/opportunities/{opportunity_id}/matching-profiles | listMatchingProfiles | List profiles matching an opportunity (poster only) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ProfileCard] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-066 | PATCH | /v1/opportunities/{opportunity_id}/confirm | confirmOpportunityFields | Confirm inferred opportunity fields | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ConfirmFieldsIn | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-067 | POST | /v1/opportunities/{opportunity_id}/publish | publishOpportunity | Publish a draft opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-068 | POST | /v1/opportunities/{opportunity_id}/pause | pauseOpportunity | Pause an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-069 | POST | /v1/opportunities/{opportunity_id}/resume | resumeOpportunity | Resume a paused opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-070 | POST | /v1/opportunities/{opportunity_id}/close | closeOpportunity | Close an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-071 | POST | /v1/opportunities/{opportunity_id}/renew | renewOpportunity | Renew a stale or expired opportunity (a passed last date is extended) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | RenewIn|null | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-072 | POST | /v1/opportunities/{opportunity_id}/save | saveOpportunity | Save an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-073 | DELETE | /v1/opportunities/{opportunity_id}/save | unsaveOpportunity | Remove an opportunity from saved | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:OpportunityOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-074 | POST | /v1/opportunities/{opportunity_id}/not-interested | markOpportunityNotInterested | Hide an opportunity as not interested | opportunity_id*(path), X-Dev-Member-Id | NotInterestedIn | 200:HiddenOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-075 | POST | /v1/opportunities/{opportunity_id}/share | shareOpportunity | Record that the member shared an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:SharedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-076 | POST | /v1/opportunities/{opportunity_id}/external-open | recordOpportunityExternalOpen | Record that the member opened an opportunity's external source | opportunity_id*(path), X-Dev-Member-Id | - | 200:OpenedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-077 | GET | /v1/opportunities/{opportunity_id}/suggestions | getOpportunitySuggestions | Tips to get more or better responses (poster only) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:SuggestionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-078 | GET | /v1/opportunities/{opportunity_id}/applicants | listOpportunityApplicants | List applicants and proposals on an opportunity (poster only) | opportunity_id*(path), stage, sort, limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:ApplicantPage 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-079 | GET | /v1/opportunities/{opportunity_id}/applicants/compare | compareApplicants | Compare 2 to 4 applicants side by side (poster only) | opportunity_id*(path), ids*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:CompareOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-080 | POST | /v1/opportunities/{opportunity_id}/applicants/{enquiry_id}/stage | setApplicantStage | Move an applicant to shortlisted, hired or declined (poster only) | opportunity_id*(path), enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | StageIn | 200:ApplicantOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-081 | POST | /v1/opportunities/{opportunity_id}/applicants/{enquiry_id}/contact-attempts | recordApplicantContactAttempt | Record that the poster called or messaged a shortlisted or hired applicant | opportunity_id*(path), enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ContactAttemptIn | 201:ApplicantOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## reputation

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-082 | GET | /v1/members/{member_id}/badges | getMemberBadges | A member's earned badges (counts-based, no score) | member_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:MemberBadgesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## notifications

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-083 | GET | /v1/notifications | listNotifications | List the member's notifications | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[NotificationOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-084 | GET | /v1/notifications/page | listNotificationsPage | List all of the member's notifications, one page at a time | limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_NotificationOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-085 | GET | /v1/notifications/unread-count | getUnreadNotificationCount | Get the number of unread notifications | X-Dev-Member-Id | - | 200:UnreadCountOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-086 | POST | /v1/notifications/{notification_id}/read | markNotificationRead | Mark one notification as read | notification_id*(path), X-Dev-Member-Id | - | 200:ReadOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-087 | POST | /v1/notifications/read-all | markAllNotificationsRead | Mark all notifications as read | X-Dev-Member-Id | - | 200:ReadOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## enquiries

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-088 | POST | /v1/enquiries | createEnquiry | Send an enquiry or application | Idempotency-Key, X-Vyapar-Language, X-Dev-Member-Id | EnquiryCreate | 201:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-089 | GET | /v1/enquiries/mine | listMyEnquiries | List the member's sent and received enquiries | role, X-Dev-Member-Id | - | 200:list[EnquiryOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-090 | GET | /v1/enquiries/mine/page | listMyEnquiriesPage | List the member's sent and received enquiries, one page at a time | role, limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_EnquiryOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-091 | GET | /v1/enquiries/{enquiry_id} | getEnquiry | Get one enquiry thread | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-092 | POST | /v1/enquiries/{enquiry_id}/messages | replyToEnquiry | Post a message in an enquiry thread | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | MessageIn | 201:EnquiryMessageOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-093 | POST | /v1/enquiries/{enquiry_id}/accept | acceptEnquiry | Accept an enquiry | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-094 | POST | /v1/enquiries/{enquiry_id}/resolve | resolveEnquiry | Mark an enquiry resolved | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-095 | POST | /v1/enquiries/{enquiry_id}/close | closeEnquiry | Close an enquiry | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-096 | POST | /v1/enquiries/{enquiry_id}/withdraw | withdrawEnquiry | Withdraw a sent enquiry | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-097 | POST | /v1/enquiries/{enquiry_id}/restrict | restrictEnquiry | Restrict an enquiry thread | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:EnquiryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-098 | POST | /v1/enquiries/block | blockMember | Block a member from contacting you | X-Dev-Member-Id | BlockIn | 200:BlockedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-099 | POST | /v1/enquiries/{enquiry_id}/refer-to-counsel | referEnquiryToCounsel | Refer an enquiry to Counsel | enquiry_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ReferToCounselIn | 200:ReferredOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## verification

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-100 | POST | /v1/listings/{listing_id}/verification | submitListingVerification | Submit a verification document for a listing | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | VerificationCreate | 201:VerificationOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-101 | GET | /v1/listings/{listing_id}/verification | listListingVerifications | List a listing's verification records | listing_id*(path), X-Dev-Member-Id | - | 200:list[VerificationOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## admin-verification

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-102 | GET | /v1/admin/verification-queue | listVerificationQueue | List the admin verification queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[VerificationOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-103 | POST | /v1/admin/verification-queue/{record_id}/verify | approveVerification | Approve a verification record (admin) | record_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DecisionIn | 200:VerificationOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-104 | POST | /v1/admin/verification-queue/{record_id}/reject | rejectVerification | Reject a verification record (admin) | record_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DecisionIn | 200:VerificationOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-105 | POST | /v1/admin/verification-queue/{record_id}/needs-clearer-copy | requestClearerVerificationCopy | Ask for a clearer verification copy (admin) | record_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DecisionIn | 200:VerificationOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-106 | POST | /v1/admin/verification-queue/listings/{listing_id}/revoke | revokeListingVerification | Revoke a listing's verification (admin) | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DecisionIn | 200:RevokedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |

## trust-safety

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-107 | POST | /v1/reports | createReport | Report content or a member | Idempotency-Key, X-Vyapar-Language, X-Dev-Member-Id | ReportIn | 201:ReportReceivedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-108 | GET | /v1/opportunities/{opportunity_id}/seeker-protection | getOpportunitySeekerProtection | The 'no fee may be asked from applicants' notice for an opportunity | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:SeekerProtectionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-109 | POST | /v1/opportunities/seeker-charge-check | checkSeekerCharge | Check opportunity text/fields for a charge on applicants before posting | X-Vyapar-Language, X-Dev-Member-Id | SeekerChargeCheckIn | 200:SeekerChargeCheckOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-110 | GET | /v1/moderation/outcomes | listMyModerationOutcomes | List moderation outcomes affecting the member | X-Dev-Member-Id | - | 200:list[ModerationOutcomeOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-111 | POST | /v1/appeals | createAppeal | Appeal a moderation outcome | X-Vyapar-Language, X-Dev-Member-Id | AppealIn | 201:AppealCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## admin-moderation

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-112 | GET | /v1/admin/moderation-queue | listModerationQueue | List the admin moderation queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ModerationCaseOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-113 | POST | /v1/admin/moderation-cases/{case_id}/decide | decideModerationCase | Decide a moderation case (admin) | case_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DecideIn | 200:CaseDecisionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-114 | GET | /v1/admin/appeals | listAppeals | List appeals (admin) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AppealQueueItemOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-115 | POST | /v1/admin/appeals/{appeal_id}/decide | decideAppeal | Decide an appeal (admin) | appeal_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AppealDecisionIn | 200:AppealDecisionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |

## reviews

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-116 | GET | /v1/reviews/invite/{interaction_kind}/{interaction_id} | getReviewInviteStatus | Get whether the member may review an interaction | interaction_kind*(path), interaction_id*(path), X-Dev-Member-Id | - | 200:ReviewInviteStatusOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-117 | POST | /v1/reviews | createReview | Submit a review for an interaction | Idempotency-Key, X-Vyapar-Language, X-Dev-Member-Id | ReviewIn | 201:ReviewCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-118 | GET | /v1/listings/{listing_id}/reviews | listListingReviews | List published reviews for a listing | listing_id*(path), X-Dev-Member-Id | - | 200:list[ListingReviewOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-119 | GET | /v1/listings/{listing_id}/reviews/page | listListingReviewsPage | List published reviews for a listing, one page at a time | listing_id*(path), limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_ListingReviewOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-120 | POST | /v1/reviews/{review_id}/dispute | disputeReview | Dispute a review (listing owner) | review_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__reviews__DisputeIn | 201:app__services__reviews__DisputeOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## partnerships

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-121 | POST | /v1/partnership-requests | createPartnershipRequest | Send a partnership request | Idempotency-Key, X-Vyapar-Language, X-Dev-Member-Id | PartnershipIn | 201:PartnershipCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-122 | GET | /v1/partnership-requests/mine | listMyPartnershipRequests | List the member's partnership requests | X-Dev-Member-Id | - | 200:list[PartnershipSummaryOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-123 | GET | /v1/partnership-requests/mine/page | listMyPartnershipRequestsPage | List the member's partnership requests, one page at a time | limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_PartnershipSummaryOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-124 | GET | /v1/partnership-requests/{request_id} | getPartnershipRequest | Get one partnership request | request_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PartnershipRequestOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-125 | POST | /v1/partnership-requests/{request_id}/{action} | transitionPartnershipRequest | Accept, decline or withdraw a partnership request | request_id*(path), action*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PartnershipTransitionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## commercial

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-126 | GET | /v1/promotions/options | listPromotionOptions | List promotion (boost) options | target_kind*, target_id*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:PromotionOptionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-127 | GET | /v1/promotions/quote | quoteCustomPromotion | Price a custom-length boost | days*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:PromotionQuoteOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-128 | POST | /v1/promotions | createPromotion | Create a promotion draft | X-Vyapar-Language, X-Dev-Member-Id | PromotionIn | 201:PromotionCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-129 | POST | /v1/promotions/{promotion_id}/confirm-purchase | confirmPromotionPurchase | Confirm a promotion purchase | promotion_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ConfirmIn | 200:PurchaseResultOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-130 | GET | /v1/promotions/mine | listMyPromotions | List the member's promotions | X-Dev-Member-Id | - | 200:list[PromotionSummaryOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-131 | GET | /v1/promotions/mine/page | listMyPromotionsPage | List the member's promotions, one page at a time | limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_PromotionSummaryOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-132 | GET | /v1/promotions/{promotion_id} | getPromotion | Get one promotion | promotion_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PromotionDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-133 | POST | /v1/promotions/{promotion_id}/cancel | cancelPromotion | Cancel a promotion | promotion_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PromotionCancelOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-134 | GET | /v1/performance/{target_kind}/{target_id} | getPerformanceReport | Get the performance report for a listing or opportunity | target_kind*(path), target_id*(path), promotion_id, days, X-Vyapar-Language, X-Dev-Member-Id | - | 200:PerformanceReportOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## admin-commercial

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-135 | POST | /v1/admin/promotions/{promotion_id}/reject | rejectPromotion | Reject a promotion (admin) | promotion_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__commercial__RejectIn | 200:PromotionRejectOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-155 | GET | /v1/admin/commercial/products | listCommercialProducts | List commercial products (admin) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminProductOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-156 | POST | /v1/admin/commercial/products | createCommercialProductVersion | Create a new commercial product version (admin) | X-Vyapar-Language, X-Dev-Member-Id | ProductVersionIn | 201:ProductVersionCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-157 | GET | /v1/admin/commercial/orders | listCommercialOrders | List commercial orders (admin) | kind, state, limit, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[CommercialOrderOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-158 | POST | /v1/admin/commercial/refunds | processRefund | Process a refund (admin) | X-Vyapar-Language, X-Dev-Member-Id | RefundIn | 200:RefundOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-159 | GET | /v1/admin/commercial/diagnostics/{target_kind}/{target_id} | getRankingDiagnostics | Get ranking diagnostics for an item (admin) | target_kind*(path), target_id*(path), q, X-Vyapar-Language, X-Dev-Member-Id | - | 200:RankingDiagnosticsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |

## payments

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-136 | POST | /v1/payments/webhook | receivePaymentWebhook | Receive a payment gateway webhook | - | - | 200:PaymentWebhookAck 400:PaymentWebhookAck 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | public / special |
| API-137 | GET | /v1/payments/orders/{order_id} | getPaymentOrder | Get one payment order | order_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PaymentOrderOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-138 | POST | /v1/payments/orders/{order_id}/simulate | simulatePaymentOrder | Simulate a sandbox payment for an order | order_id*(path), X-Vyapar-Language, X-Dev-Member-Id | SimulateIn | 200:SimulatedPaymentOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## workspace

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-139 | GET | /v1/workspace/mine | listMyWorkspaces | List workspaces the member belongs to | X-Dev-Member-Id | - | 200:list[WorkspaceSummaryOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-140 | GET | /v1/workspace/{listing_id} | getWorkspace | Get a listing's workspace | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:WorkspaceOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-141 | POST | /v1/entitlements | createEntitlement | Start a workspace plan purchase | X-Vyapar-Language, X-Dev-Member-Id | EntitlementIn | 201:EntitlementCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-142 | POST | /v1/entitlements/{entitlement_id}/confirm-purchase | confirmEntitlementPurchase | Confirm a workspace plan purchase | entitlement_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ConfirmIn | 200:EntitlementPurchaseOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-143 | POST | /v1/entitlements/{entitlement_id}/renewal | setEntitlementRenewal | Turn auto-renewal on or off for a plan | entitlement_id*(path), X-Vyapar-Language, X-Dev-Member-Id | RenewalIn | 200:RenewalOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-144 | GET | /v1/entitlements/mine | listMyEntitlements | List the member's workspace plans | X-Dev-Member-Id | - | 200:list[EntitlementOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-145 | POST | /v1/workspace/{listing_id}/invite | inviteWorkspaceMember | Invite a member to a workspace | listing_id*(path), X-Vyapar-Language, X-Dev-Member-Id | InviteIn | 201:InviteCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-146 | GET | /v1/workspace/invites/mine | listMyWorkspaceInvites | List workspace invitations for the member | X-Dev-Member-Id | - | 200:list[WorkspaceInviteOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-147 | POST | /v1/workspace/invites/{invite_id}/answer | answerWorkspaceInvite | Accept or decline a workspace invitation | invite_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__workspace__AnswerIn | 200:InviteAnswerOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-148 | POST | /v1/workspace/members/{member_row_id}/role | changeWorkspaceMemberRole | Change a workspace member's role | member_row_id*(path), X-Vyapar-Language, X-Dev-Member-Id | RoleChangeIn | 200:RoleChangeOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## campaigns

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-149 | GET | /v1/campaigns/options | listCampaignOptions | List campaign options | listing_id*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:CampaignOptionsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-150 | POST | /v1/campaigns | createCampaign | Create a campaign | X-Vyapar-Language, X-Dev-Member-Id | CampaignIn | 201:CampaignCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-151 | POST | /v1/campaigns/{campaign_id}/confirm-purchase | confirmCampaignPurchase | Confirm a campaign purchase | campaign_id*(path), X-Vyapar-Language, X-Dev-Member-Id | ConfirmIn | 200:CampaignPurchaseOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-152 | GET | /v1/campaigns/{campaign_id} | getCampaign | Get one campaign | campaign_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:CampaignOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-153 | POST | /v1/campaigns/{campaign_id}/items-state | setCampaignItemsState | Pause or resume a campaign's items | campaign_id*(path), X-Vyapar-Language, X-Dev-Member-Id | CampaignItemsStateIn | 200:CampaignItemsStateOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-154 | GET | /v1/campaigns/{campaign_id}/report | getCampaignReport | Get a campaign's performance report | campaign_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PerformanceReportOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## admin-ops

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-160 | GET | /v1/admin/marketplace-health | getMarketplaceHealth | Get marketplace health metrics (admin) | days, X-Vyapar-Language, X-Dev-Member-Id | - | 200:MarketplaceHealthOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-161 | GET | /v1/admin/opportunities-queue | listOpportunityReviewQueue | List opportunities awaiting review (admin) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[OpportunityQueueItemOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-162 | POST | /v1/admin/opportunities-queue/{opportunity_id}/decide | decideOpportunityReview | Decide an opportunity review (admin) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | QueueDecisionIn | 200:QueueDecisionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-163 | GET | /v1/admin/stale-queue | listStaleQueue | List stale items (admin) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[StaleItemOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-164 | POST | /v1/admin/stale-queue/bulk | bulkStaleAction | Apply an action to stale items in bulk (admin) | X-Vyapar-Language, X-Dev-Member-Id | BulkStaleIn | 200:BulkStaleOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-165 | GET | /v1/admin/taxonomy | listTaxonomyTerms | List taxonomy terms (admin) | kind, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[app__services__admin_ops__TaxonomyTermOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-166 | POST | /v1/admin/taxonomy | createTaxonomyTerm | Add a taxonomy term (admin) | X-Vyapar-Language, X-Dev-Member-Id | TaxonomyAddIn | 201:TaxonomyCreatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-167 | POST | /v1/admin/taxonomy/merge | mergeTaxonomyTerms | Merge taxonomy terms (admin) | X-Vyapar-Language, X-Dev-Member-Id | TaxonomyMergeIn | 200:TaxonomyMergedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-168 | POST | /v1/admin/taxonomy/{term_id}/rename | renameTaxonomyTerm | Rename a taxonomy term (admin) | term_id*(path), X-Vyapar-Language, X-Dev-Member-Id | TaxonomyRenameIn | 200:TaxonomyRenamedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |
| API-169 | GET | /v1/admin/dead-letters | listDeadLetters | List dead-lettered outbox events (admin) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[DeadLetterOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |

## internal-bridges

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-170 | GET | /internal/v1/dashboard-summary/{listing_id} | getDashboardSummary | Get a listing's summary for the platform dashboard (internal) | listing_id*(path), X-ForKhatri-Service-Key | - | 200:DashboardSummaryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | service key |

## privacy

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-171 | GET | /v1/privacy | getPrivacySettings | Get the member's privacy settings | X-Dev-Member-Id | - | 200:PrivacySettingsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-172 | PATCH | /v1/privacy | updatePrivacySettings | Update the member's privacy settings | X-Vyapar-Language, X-Dev-Member-Id | PrivacyPatch | 200:PrivacySettingsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-173 | POST | /v1/privacy/export | requestDataExport | Request an export of the member's data | X-Dev-Member-Id | - | 201:DataExportOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-174 | POST | /v1/privacy/withdraw-consent | withdrawConsent | Withdraw a consent | X-Dev-Member-Id | WithdrawConsentIn | 200:WithdrawConsentOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-175 | POST | /v1/privacy/delete | requestAccountDeletion | Request deletion of the member's Vyapar data | X-Vyapar-Language, X-Dev-Member-Id | - | 201:DeletionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-176 | GET | /v1/privacy/requests | listMyPrivacyRequests | List the member's privacy requests | X-Dev-Member-Id | - | 200:list[PrivacyRequestOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-177 | GET | /v1/preferences/mine | listMyPreferences | List the member's derived preferences | X-Dev-Member-Id | - | 200:list[DerivedPreferenceOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-178 | POST | /v1/preferences/{pref_id}/{action} | decidePreference | Accept or reject a derived preference | pref_id*(path), action*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PreferenceDecisionOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-179 | GET | /v1/legal/{kind} | getLegalDocument | Get the current legal document of a kind | kind*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:LegalDocumentOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-180 | POST | /v1/legal/{kind}/accept | acceptLegalDocument | Accept the current legal document of a kind | kind*(path), X-Dev-Member-Id | - | 200:LegalAcceptanceOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## events

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-181 | POST | /v1/events | submitEvents | Submit client interaction events | X-Dev-Member-Id | EventBatchIn | 200:EventsAcceptedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## admin-audit

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-182 | GET | /v1/admin/audit | searchAuditLog | Search the audit log (admin) | actor_id, object_kind, object_id, action, days, limit, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AuditEventOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member + admin scope |

## dev

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-183 | GET | /v1/dev/members | listDevMembers | List development members (dev only) | - | - | 200:list[DevMemberOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-184 | POST | /v1/dev/run-notification-matcher | runNotificationMatcher | Run the notification matcher now (dev only) | - | - | 200:SentOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-185 | POST | /v1/dev/run-notification-digest | runNotificationDigest | Run the notification digest now (dev only) | - | - | 200:SentOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-186 | POST | /v1/dev/run-credential-sync | runCredentialSync | Run the credential sync now (dev only) | - | - | 200:UpdatedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-187 | POST | /v1/dev/revoke-credential/{member_id} | devRevokeCredential | Revoke a member's platform credential (dev only) | member_id*(path) | - | 200:DevRevokedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-188 | POST | /v1/dev/run-verification-jobs | runVerificationJobs | Run verification jobs now (dev only) | - | - | 200:VerificationJobsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-189 | POST | /v1/dev/run-moderation-jobs | runModerationJobs | Run moderation jobs now (dev only) | - | - | 200:ModerationJobsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |
| API-190 | POST | /v1/dev/run-commercial-jobs | runCommercialJobs | Run commercial jobs now (dev only) | - | - | 200:object 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | dev only |

## integrations

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-191 | GET | /v1/integrations/me | getIntegrationIdentity | Who the caller is acting as, how it authenticated, and its scopes | X-Dev-Member-Id | - | 200:WhoAmI | public / special |
| API-192 | GET | /v1/integrations/scopes | listAccessTokenScopes | Scopes an access token can be granted | X-Dev-Member-Id, X-Vyapar-Language | - | 200:list[ScopeInfo] | public / special |
| API-193 | GET | /v1/integrations/tokens | listAccessTokens | Your personal access tokens (never the token values) | X-Dev-Member-Id | - | 200:list[AccessTokenOut] | public / special |
| API-194 | POST | /v1/integrations/tokens | createAccessToken | Create a personal access token; the value is returned only in this response | X-Dev-Member-Id, X-Vyapar-Language | AccessTokenCreate | 201:AccessTokenCreated | public / special |
| API-195 | DELETE | /v1/integrations/tokens/{token_id} | revokeAccessToken | Revoke a personal access token immediately | token_id*(path), X-Dev-Member-Id, X-Vyapar-Language | - | 200:AccessTokenOut | public / special |
| API-196 | GET | /v1/integrations/webhooks/events | listWebhookEventTypes | Event types a webhook can subscribe to | X-Dev-Member-Id, X-Vyapar-Language | - | 200:list[WebhookEventType] | public / special |
| API-197 | GET | /v1/integrations/webhooks | listWebhookSubscriptions | Your webhook subscriptions | X-Dev-Member-Id | - | 200:list[WebhookOut] | public / special |
| API-198 | POST | /v1/integrations/webhooks | createWebhookSubscription | Subscribe a URL to events; the signing secret is returned only in this response | X-Dev-Member-Id, X-Vyapar-Language | WebhookCreate | 201:WebhookCreated | public / special |
| API-199 | DELETE | /v1/integrations/webhooks/{subscription_id} | deleteWebhookSubscription | Delete a webhook subscription (its delivery log is kept) | subscription_id*(path), X-Dev-Member-Id, X-Vyapar-Language | - | 200:Ack | public / special |
| API-200 | POST | /v1/integrations/webhooks/{subscription_id}/test | testWebhookSubscription | Send a signed `ping` event now and return the delivery outcome | subscription_id*(path), X-Dev-Member-Id, X-Vyapar-Language | - | 200:WebhookDelivery | public / special |
| API-201 | GET | /v1/integrations/webhooks/{subscription_id}/deliveries | listWebhookDeliveries | Recent delivery attempts for a subscription | subscription_id*(path), limit, X-Dev-Member-Id, X-Vyapar-Language | - | 200:list[WebhookDelivery] | public / special |

## contracts

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-202 | POST | /v1/contracts/jobs/auto-release | runContractAutoRelease | Release overdue submitted milestones now (dev only) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:AutoReleaseOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-203 | GET | /v1/contracts/disputes | listContractDisputes | List contract disputes (moderation operators) | state, limit, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminDisputeOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-204 | GET | /v1/contracts/roles | getContractRoles | Who pays and who works if this enquiry becomes a contract, and whether I can start it | enquiry_id*, X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractRolesOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-205 | POST | /v1/contracts | createContract | Create a contract from an accepted enquiry (client) | X-Vyapar-Language, X-Dev-Member-Id | ContractCreateIn | 201:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-206 | GET | /v1/contracts | listMyContracts | List my contracts as client, provider or both | role, state, limit, cursor, X-Vyapar-Language, X-Dev-Member-Id | - | 200:Page_ContractSummaryOut_ 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-207 | GET | /v1/contracts/{contract_id} | getContract | Get one contract with milestones, ledger, timesheets, disputes and timeline | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-208 | POST | /v1/contracts/{contract_id}/propose | proposeContract | Send a draft contract to the provider (client) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-209 | POST | /v1/contracts/{contract_id}/accept | acceptContract | Accept a proposed contract (provider) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-210 | POST | /v1/contracts/{contract_id}/cancel | cancelContract | Cancel a contract; held milestones are refunded to the client | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | CancelIn|null | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-211 | POST | /v1/contracts/{contract_id}/complete | completeContract | Complete an active contract with nothing held (client; hourly contracts end this way) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-212 | POST | /v1/contracts/{contract_id}/milestones | addMilestone | Add a milestone to a draft fixed-price contract (client) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | MilestoneIn | 201:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-213 | PATCH | /v1/contracts/{contract_id}/milestones/{milestone_id} | updateMilestone | Edit a milestone of a draft contract (client) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | MilestoneUpdateIn | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-214 | DELETE | /v1/contracts/{contract_id}/milestones/{milestone_id} | deleteMilestone | Remove a milestone from a draft contract (client) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-215 | POST | /v1/contracts/{contract_id}/milestones/{milestone_id}/fund | fundMilestone | Open the checkout that funds a milestone (client) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:FundingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-216 | POST | /v1/contracts/{contract_id}/milestones/{milestone_id}/submit | submitMilestone | Submit a funded milestone for approval (provider) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | SubmitIn|null | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-217 | POST | /v1/contracts/{contract_id}/milestones/{milestone_id}/approve | approveMilestone | Approve a submitted milestone and release it (client) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-218 | POST | /v1/contracts/{contract_id}/milestones/{milestone_id}/reject | rejectMilestone | Send a submitted milestone back with a note (client) | contract_id*(path), milestone_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__contracts__RejectIn | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-219 | POST | /v1/contracts/{contract_id}/disputes | openDispute | Open a dispute on an active contract (either party) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__contracts__DisputeIn | 201:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-220 | POST | /v1/contracts/{contract_id}/disputes/{dispute_id}/resolve | resolveContractDispute | Record a dispute outcome (moderation operators) | contract_id*(path), dispute_id*(path), X-Vyapar-Language, X-Dev-Member-Id | DisputeResolveIn | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-221 | POST | /v1/contracts/{contract_id}/timesheets | submitTimesheet | Submit a week's hours on an hourly contract (provider) | contract_id*(path), X-Vyapar-Language, X-Dev-Member-Id | TimesheetIn | 201:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-222 | POST | /v1/contracts/{contract_id}/timesheets/{timesheet_id}/approve | approveTimesheet | Approve a timesheet and open the checkout that pays it (client) | contract_id*(path), timesheet_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:FundingOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-223 | POST | /v1/contracts/{contract_id}/timesheets/{timesheet_id}/reject | rejectTimesheet | Send a timesheet back with a note (client) | contract_id*(path), timesheet_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__contracts__RejectIn | 200:ContractOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## ai

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-224 | POST | /v1/ai/draft-opportunity | draftOpportunity | Draft an opportunity from free text (typed or dictated), in English, Hindi, Telugu or Hinglish | X-Vyapar-Language, X-Dev-Member-Id | DraftRequest | 200:DraftOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse 501:ErrorResponse 503:ErrorResponse | member session |
| API-225 | POST | /v1/ai/read-opportunity-image | readOpportunityImage | Draft an opportunity from a photo or PDF of a notice (needs the AI provider) | X-Vyapar-Language, X-Dev-Member-Id | ImageRequest | 200:DraftOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse 501:ErrorResponse 503:ErrorResponse | member session |
| API-226 | GET | /v1/opportunities/{opportunity_id}/ai-shortlist | getAiShortlist | Rank the applicants to one opportunity 1â€“10 with reasons and risks (poster only) | opportunity_id*(path), language, X-Vyapar-Language, X-Dev-Member-Id | - | 200:ShortlistOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse 501:ErrorResponse 503:ErrorResponse | member session |
| API-227 | POST | /v1/ai/posting-tips | getPostingTips | Tips that would get a draft or a posted opportunity more responses | X-Vyapar-Language, X-Dev-Member-Id | TipsRequest | 200:TipsOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse 501:ErrorResponse 503:ErrorResponse | member session |
| API-228 | POST | /v1/ai/improve-proposal | improveProposal | Suggest a better cover text and a bid range for applying to an opportunity | X-Vyapar-Language, X-Dev-Member-Id | ProposalRequest | 200:ProposalOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse 501:ErrorResponse 503:ErrorResponse | member session |

## admin-console

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-229 | GET | /vyapar/admin/manifest | getVyaparAdminManifest | Admin Console views this operator may open (TR-PLAT-01 manifest) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminManifestOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-230 | GET | /vyapar/admin/members/{member_id}/summary | getVyaparAdminMemberSummary | What this person has in Vyapar: plan, facts and flags (404 without a Vyapar account) | member_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:MemberSummaryOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-231 | GET | /vyapar/admin/moderation | listVyaparAdminModerationItems | List the 'moderation' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-232 | GET | /vyapar/admin/moderation/{item_id} | getVyaparAdminModerationItem | Get one 'moderation' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-233 | POST | /vyapar/admin/moderation/{item_id}/actions/{action_id} | actOnVyaparAdminModerationItem | Take an action on a 'moderation' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-234 | GET | /vyapar/admin/verification | listVyaparAdminVerificationItems | List the 'verification' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-235 | GET | /vyapar/admin/verification/{item_id} | getVyaparAdminVerificationItem | Get one 'verification' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-236 | POST | /vyapar/admin/verification/{item_id}/actions/{action_id} | actOnVyaparAdminVerificationItem | Take an action on a 'verification' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-237 | GET | /vyapar/admin/opportunities | listVyaparAdminOpportunitiesItems | List the 'opportunities' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-238 | GET | /vyapar/admin/opportunities/{item_id} | getVyaparAdminOpportunitiesItem | Get one 'opportunities' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-239 | POST | /vyapar/admin/opportunities/{item_id}/actions/{action_id} | actOnVyaparAdminOpportunitiesItem | Take an action on a 'opportunities' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-240 | GET | /vyapar/admin/appeals | listVyaparAdminAppealsItems | List the 'appeals' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-241 | GET | /vyapar/admin/appeals/{item_id} | getVyaparAdminAppealsItem | Get one 'appeals' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-242 | POST | /vyapar/admin/appeals/{item_id}/actions/{action_id} | actOnVyaparAdminAppealsItem | Take an action on a 'appeals' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-243 | GET | /vyapar/admin/disputes | listVyaparAdminDisputesItems | List the 'disputes' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-244 | GET | /vyapar/admin/disputes/{item_id} | getVyaparAdminDisputesItem | Get one 'disputes' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-245 | POST | /vyapar/admin/disputes/{item_id}/actions/{action_id} | actOnVyaparAdminDisputesItem | Take an action on a 'disputes' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-246 | GET | /vyapar/admin/commercial | listVyaparAdminCommercialItems | List the 'commercial' Admin Console queue | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[AdminQueueItem] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-247 | GET | /vyapar/admin/commercial/{item_id} | getVyaparAdminCommercialItem | Get one 'commercial' item with its history and available actions | item_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:AdminItemDetailOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |
| API-248 | POST | /vyapar/admin/commercial/{item_id}/actions/{action_id} | actOnVyaparAdminCommercialItem | Take an action on a 'commercial' item; returns the updated item | item_id*(path), action_id*(path), X-Vyapar-Language, X-Dev-Member-Id | AdminActionIn | 200:AdminQueueItem 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | see source |

## trust

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-249 | POST | /v1/trust/scam-check | checkScamShield | Check text a poster is about to send for a charge on applicants (never raises; nothing is stored) | X-Vyapar-Language, X-Dev-Member-Id | ScamCheckIn | 200:ScamCheckOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-250 | GET | /v1/profession-rules | listProfessionRules | What each regulated profession may show and buy on Vyapar (council rules, as configured) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[ProfessionRuleOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-251 | GET | /v1/credentials/types | listCredentialTypes | Council registers a professional can add, with number formats | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[CredentialTypeOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-252 | GET | /v1/me/profile/credentials | listMyCredentials | My council register entries, with their check status | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[CredentialOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-253 | POST | /v1/me/profile/credentials | addCredential | Add a council register entry (ICAI, medical council, NCAHP, Bar Council, CoA, DigiLocker) to my profile | X-Vyapar-Language, X-Dev-Member-Id | CredentialIn | 201:CredentialOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-254 | POST | /v1/me/profile/credentials/{credential_id}/recheck | recheckCredential | Ask for a register entry to be checked again | credential_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:CredentialOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-255 | DELETE | /v1/me/profile/credentials/{credential_id} | deleteCredential | Remove a register entry from my profile | credential_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:DeletedOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-256 | GET | /v1/paid-on-time/asks | listMyPaidOnTimeAsks | My "Were you paid on time?" questions (open ones by default) | state, X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[PaidOnTimeAskOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-257 | POST | /v1/paid-on-time/asks/{ask_id}/answer | answerPaidOnTime | Answer "Were you paid on time?" (Yes or No, once; only the person who was paid) | ask_id*(path), X-Vyapar-Language, X-Dev-Member-Id | app__services__paid_on_time__AnswerIn | 200:PaidOnTimeAskOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-258 | GET | /v1/members/{member_id}/paid-on-time | getMemberPaidOnTime | A payer's "Paid on time: 12 of 13" (shown only after 3 answers) | member_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:PaidOnTimeSummary 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-259 | GET | /v1/me/restrictions | listMyRestrictions | Everything of mine the platform restricts now, why, and how to appeal to a person | X-Vyapar-Language, X-Dev-Member-Id | - | 200:list[RestrictionOut] 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-260 | GET | /v1/opportunities/{opportunity_id}/close-check | getOpportunityCloseCheck | Before closing: how many applicants are still waiting, and what closing tells them (poster only) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:CloseCheckOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-261 | POST | /v1/trust/jobs/run | runTrustPass | Run the hourly trust pass now (dev only; runs hourly anyway) | X-Vyapar-Language, X-Dev-Member-Id | - | 200:TrustPassOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## voice

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-262 | POST | /v1/voice/interview/next | nextInterviewQuestion | The next spoken question for what is still missing, or the finished summary and draft | X-Vyapar-Language, X-Dev-Member-Id | InterviewNextRequest | 200:InterviewNextOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-263 | POST | /v1/voice/interview/interpret | interpretInterviewAnswer | Read one spoken answer: its typed value, a read-back to confirm, or what to ask again | X-Vyapar-Language, X-Dev-Member-Id | InterviewInterpretRequest | 200:InterviewInterpretOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## recommendations

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-264 | GET | /v1/me/taste | getMyTaste | What Vyapar has learned from your own actions, in your language | X-Vyapar-Language, X-Dev-Member-Id | - | 200:TasteOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-265 | DELETE | /v1/me/taste | resetMyTaste | Forget everything learned; earlier actions never count again | X-Vyapar-Language, X-Dev-Member-Id | - | 200:TasteOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-266 | PATCH | /v1/me/taste | removeMyTasteItem | Stop using one learned item (a skill, a kind of post, the distance limit, the pay floor ...) | X-Vyapar-Language, X-Dev-Member-Id | TastePatch | 200:TasteOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |
| API-267 | POST | /v1/opportunities/{opportunity_id}/more-like-this | moreLikeThis | Show me more posts like this one (a strong positive for your recommendations) | opportunity_id*(path), X-Vyapar-Language, X-Dev-Member-Id | - | 200:TasteOut 400:ErrorResponse 401:ErrorResponse 403:ErrorResponse 404:ErrorResponse 409:ErrorResponse 429:ErrorResponse | member session |

## untagged

| ID | Method | Path | operationId | Summary | Params | Request body | Responses | Auth |
|---|---|---|---|---|---|---|---|---|
| API-268 | GET | /health | health_health_get | Health | - | - | 200:object | see source |
