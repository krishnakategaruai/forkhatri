// [IMP38 — Refactor C] Wire types for the Vyapar API, as the web app reads
// them. Taken from the interfaces the screens already declared (so nothing
// the screens rely on changed shape); where the backend's OpenAPI document
// (vyapar-service/openapi.json, workstream A) names more fields, they are
// optional additions here, never required.
//
import type { StructuredFields } from "./hiring-types";

// Conventions: raw slugs sit next to their localized labels
// (`capabilities` + `capability_labels`); labels arrive already translated
// into the language the client sent in X-Vyapar-Language.

// ---- shared -------------------------------------------------------------------

// [FE2] Badges, seeker protection and packages are declared with their own
// domains; the wire types below reference them.
import type { Badge, SeekerProtection } from "./domains/trust";
import type { ServicePackage } from "./domains/packages";
import type { ApplicantsWaiting, CouncilBadge, PaidOnTime, ProfessionVerdict, Restriction } from "./domains/trustPack";

export interface Reputation {
  interactions: number;
  recommends: number;
  top_tags: string[];
  under_review: number;
  response_minutes: number | null;
  new_on_vyapar: boolean;
}

/** Cursor-paginated list envelope returned by the parallel `/page` routes. */
export interface Page<T> {
  items: T[];
  next_cursor?: string | null;
}

export interface PageParams {
  limit?: number;
  cursor?: string | null;
}

export interface OkResponse {
  ok?: boolean;
  [key: string]: unknown;
}

// ---- members --------------------------------------------------------------------

export interface ProfileBrief {
  id: string;
  kind: "business" | "professional";
  name: string;
  headline: string | null;
  locality: string;
  state: string;
  verification_state: string;
  capability_labels: string[];
}

/** The member's own two profile kinds; `complete` when at least one exists. */
export interface MemberProfiles {
  business: ProfileBrief | null;
  professional: ProfileBrief | null;
  complete: boolean;
}

export interface Me {
  id?: string;
  display_name: string;
  is_operator: boolean;
  operator_permissions: string[];
  language?: string;
  profiles?: MemberProfiles | null;
}

export interface DevMember {
  id: string;
  display_name: string;
  locality: string | null;
  is_operator: boolean;
}

export interface FirstRunState {
  step: number;
  done: boolean;
  display_name: string;
  language?: string;
  locality?: string | null;
  lat?: number | null;
  lng?: number | null;
  capabilities?: string[];
  help_with?: string[];
  /** [Start flow 2026-10] show the 3-question start (once; never to a member with a trade or a post). */
  needs_start?: boolean;
  goal?: "find_work" | "hire" | "get_customers" | null;
  has_trade?: boolean;
  has_post?: boolean;
  date_of_birth_known?: boolean;
  /** 18 and over (or not yet asked). */
  eligible?: boolean;
}

// ---- [Start flow 2026-10] the 3-question start ------------------------------------------
export type StartGoal = "find_work" | "hire" | "get_customers";

export interface TradeTile {
  slug: string;
  label: string;
  category: string | null;
}

export interface StartInput {
  goal: StartGoal;
  capabilities?: string[];
  capabilities_other?: string[];
  locality?: string | null;
  lat?: number | null;
  lng?: number | null;
  /** ISO date; asked only when the identity does not know it. */
  date_of_birth?: string | null;
  business_name?: string | null;
  experience_years?: number | null;
  own_assets?: string[] | null;
  headline?: string | null;
}

export interface StartOut {
  state: FirstRunState;
  eligible: boolean;
  profile_id: string | null;
  live: boolean;
  publish_blocked: string | null;
  next: "discover" | "post" | "visible" | "under_18";
}

export interface CompletionQuestion {
  key: "experience_years" | "own_assets" | "headline" | "service_radius_km";
  kind: "choice" | "multi" | "text";
  question: string;
  options: { value: string; label: string }[];
  placeholder: string | null;
}

export interface ProfileCompletion {
  percent: number;
  done: string[];
  next: CompletionQuestion | null;
}

export interface LocateResult {
  matched: boolean;
  locality: string | null;
  lat: number;
  lng: number;
  distance_km?: number | null;
  /** Areas within about 25 km, nearest first; empty anywhere else. */
  nearby: string[];
  source?: "gazetteer" | "listings" | "places" | "none";
}

// ---- opportunities ----------------------------------------------------------------

export interface PosterSummary {
  name: string | null;
  member_since: string | null;
  active_opportunities: number;
  verified_listing_id: string | null;
  verified_listing_name: string | null;
  reply_rate: "most" | "some" | "few" | null;
  reply_speed: "hours" | "day" | "days" | null;
}

export interface Opportunity {
  sponsored: boolean;
  id: string;
  is_poster: boolean;
  poster_id: string;
  submitter_name: string | null;
  title: string;
  type: string;
  type_action_label: string;
  description: string | null;
  requirements: string | null;
  compensation: string | null;
  location: string | null;
  work_mode: string | null;
  timing: string | null;
  deadline: string | null;
  source_segment: string;
  source_name: string | null;
  source_url: string | null;
  response_method: string | null;
  unconfirmed_fields: string[];
  confirmed_fields: string[];
  state: string;
  saved: boolean;
  posted_days_ago: number | null;
  capability_labels: string[];
  required_capabilities?: string[];
  min_experience_years: number | null;
  days_left: number | null;
  response_bucket: string | null;
  poster: PosterSummary | null;
  capability_match: boolean[] | null;
  viewer_matched_labels?: string[];
  /** [FE1] typed fields for the opportunity's type (others null); see hiring-types.ts */
  structured?: StructuredFields | null;
  /** [FE1] the poster lets people call before accepting (jobs and local services only) */
  allow_precall?: boolean;
  /** [FE1] the money line in the caller's language; falls back to `compensation` (FE1 owns this field) */
  compensation_label?: string | null;
  // Present in OpenAPI OpportunityOut; not read by the web screens.
  value_amount?: number | null;
  source_unreachable?: boolean;
  entry_mode?: string;
  state_reason?: string | null;
  relevance_reason?: string | null;
  // [FE2 — imp-backend-a §5 / -b §2-3] detail-read enrichers
  seeker_protection?: SeekerProtection | null;
  poster_badges?: Badge[];
  distance_km?: number | null;
  // [Trust pack] "Paid on time: 2 of 3" (null until three people answered),
  // the poster's own waiting applicants and any restriction on the post.
  poster_paid_on_time?: PaidOnTime | null;
  applicants_waiting?: ApplicantsWaiting | null;
  restriction?: Restriction | null;
}

export interface WhyResponse {
  signals: string[];
  gap: string | null;
  gap_skills: string | null;
  sponsored_note: string | null;
}

export type NotInterestedReason =
  | "too_far"
  | "wrong_type"
  | "not_my_capability"
  | "value_too_low"
  | "wrong_timing"
  | "already_found"
  | "not_interested";

/** One card in the Discover feed. */
export interface OpportunityCard {
  id: string;
  title: string;
  type: string;
  type_action_label: string;
  location: string | null;
  compensation: string | null;
  source_segment: string;
  submitter_name: string | null;
  posted_days_ago: number | null;
  relevance_reason: string | null;
  // [FE2 — imp-backend-b §5] FeedCard additions (all optional, additive)
  distance_km?: number | null;
  /** Server-localized: "In your area" under 0.5 km, else "1.8 km away" (imp-backend-b §5). */
  distance_label?: string | null;
  /** Locality only, e.g. "Madhapur" (imp-backend-b §5). */
  location_label?: string | null;
  poster_badges?: Badge[];
  seeker_protection?: SeekerProtection | null;
  compensation_label?: string | null;
  work_mode?: string | null;
  sponsored?: boolean;
  /** [Design language 2026-09-29] skill slugs (already in the API's FeedCard); picks the card's trade icon. */
  required_capabilities?: string[];
}

export interface FeedSection {
  key: string;
  items: OpportunityCard[];
  total_available: number;
}

export interface FeedResponse {
  sections: FeedSection[];
  enrichment_prompt: string | null;
  /** At most one labelled paid card; organic sections are unaffected. */
  sponsored?: OpportunityCard[];
  /** [FE2] The filters as the server applied them. */
  filters?: FeedFilterValues;
  /** [FE2] false when the member has no coordinates (distance sort/radius fall back to locality text). */
  distance_available?: boolean;
}

export type FeedSort = "relevance" | "distance" | "freshness" | "verified_first" | "salary_high";
export type OpportunityTypeSlug = "employment" | "freelance" | "local_service" | "partnership" | "training" | "community";
export type WorkMode = "on_site" | "remote" | "both";
export type FeedAvailability = "now" | "this_week" | "later";

/** [FE2 — imp-backend-b §5] Discover filters, as sent and as echoed back (`FeedFilters`). */
export interface FeedFilterValues {
  skills?: string[];
  q?: string | null;
  type?: OpportunityTypeSlug | string | null;
  work_mode?: WorkMode | string | null;
  radius_km?: number | null;
  availability?: FeedAvailability | string | null;
  sort?: FeedSort | string;
  // [FE2 — Discover filters redesign] additive
  types?: string[];
  pay_kind?: "monthly" | "project" | null;
  pay_min_paise?: number | null;
  pay_max_paise?: number | null;
  posted_within?: "today" | "week" | "month" | null;
  shift?: "day" | "night" | "flexible" | null;
  experience?: "fresher" | "1" | "3" | null;
  verified_only?: boolean;
  segment?: "community" | "public" | null;
}

export interface FacetCount {
  value: string;
  count: number;
  label?: string | null;
}

export interface FeedFacets {
  type: FacetCount[];
  work_mode: FacetCount[];
  posted_within: FacetCount[];
  shift: FacetCount[];
  experience: FacetCount[];
  verified: number;
  skills: FacetCount[];
}

/** [FE2] listOpportunityResults — one flat ranked list with its total and facet counts. */
export interface ResultsResponse {
  items: OpportunityCard[];
  total: number;
  facets: FeedFacets;
  filters: FeedFilterValues;
  distance_available: boolean;
  near_label: string | null;
  radius_km: number | null;
}

/** [FE2] listOpportunityRows — the Discover home as themed rows. */
export interface FeedRow {
  key: string;
  /** [imp-backend-b L13] the row title, translated by the server; preferred over title_key. */
  title?: string | null;
  title_key: string;
  title_params: Record<string, string | number>;
  see_all: Record<string, string | number | boolean>;
  items: OpportunityCard[];
  total: number;
}

export interface RowsResponse {
  rows: FeedRow[];
  /** [imp-backend-a N2] true when a row is built from the viewer's own skills (For you, their categories). */
  has_personal_rows?: boolean;
  /** [imp-backend-a N2] the viewer's own work categories, strongest first. */
  viewer_categories?: string[];
  enrichment_prompt: string | null;
  distance_available: boolean;
}

export interface FeedParams {
  skills?: readonly string[];
  q?: string | null;
  type?: string | null;
  work_mode?: string | null;
  radius_km?: number | null;
  availability?: string | null;
  sort?: string | null;
  types?: readonly string[];
  pay_kind?: string | null;
  pay_min_paise?: number | null;
  pay_max_paise?: number | null;
  posted_within?: string | null;
  shift?: string | null;
  experience?: string | null;
  verified_only?: boolean;
  segment?: string | null;
}

// ---- profiles (business / professional listings) --------------------------------------

export interface ProfileCardData {
  id: string;
  kind: "business" | "professional";
  name: string;
  headline: string | null;
  locality: string;
  verified: boolean;
  availability: "now" | "this_week" | "later" | null;
  experience_years: number | null;
  matched_labels: string[];
  other_labels: string[];
  reputation: Reputation | null;
  badges?: Badge[];
  profession?: ProfessionVerdict | null;
  council_badges?: CouncilBadge[];
}

export interface ListingContact {
  channel: string;
  value: string;
  disclosure: "public" | "after_accept" | "hidden";
}

export interface Listing {
  id: string;
  kind: string;
  name: string;
  headline: string | null;
  description: string | null;
  locality: string;
  categories: string[];
  capabilities: string[];
  unmapped_labels: string[];
  category_labels: string[];
  capability_labels: string[];
  primary_phone: string | null;
  contact_verified: boolean;
  discoverable: boolean;
  enquiry_pref: string;
  state: string;
  state_reason: string | null;
  verification_state: string;
  intent_state: string | null;
  intent_visible: boolean;
  capability_visible: boolean;
  is_owner: boolean;
  owner_id: string;
  saved: boolean;
  contacts: ListingContact[];
  credential_ref: { id: string; claim: string; issuer: string; last_checked: string } | null;
  verification_document: string | null;
  verification_claim: string | null;
  verified_at: string | null;
  verification_expires_at: string | null;
  partnership_open: boolean;
  reputation: Reputation | null;
  sponsored: boolean;
  // [FE2 — imp-backend-b §3-4]
  badges?: Badge[];
  packages?: ServicePackage[];
  // [Trust pack] profession rules, council registrations, paid on time, restriction
  profession?: ProfessionVerdict | null;
  council_badges?: CouncilBadge[];
  paid_on_time?: PaidOnTime | null;
  restriction?: Restriction | null;
}

export interface SearchListing {
  id: string;
  name: string;
  locality: string;
  categories: string[];
  capabilities: string[];
  category_labels: string[];
  capability_labels: string[];
  verification_state: string;
  contact_verified: boolean;
  reputation?: Reputation | null;
  badges?: Badge[];
  /** Fields the search endpoint already returns (GET /v1/listings/search). */
  /** "business" or "professional". */
  kind?: string;
  /** True on the viewer's own profile. */
  is_owner?: boolean;
  headline?: string | null;
  /** "enabled" when the owner takes price enquiries. */
  enquiry_pref?: string | null;
  /** Only present when the owner shares it with this viewer. */
  primary_phone?: string | null;
  availability?: string | null;
  service_mode?: string | null;
  // [Trust pack] every listing read carries these
  profession?: ProfessionVerdict | null;
  council_badges?: CouncilBadge[];
  paid_on_time?: PaidOnTime | null;
}

export interface SearchResult {
  listing: SearchListing;
  relevance_reason: string;
  distance_km?: number | null;
  /** Server-localized: "In your area" under 0.5 km, else "1.8 km away" (imp-backend-b §5). */
  distance_label?: string | null;
}

export interface BroadeningOption {
  id: string;
  label: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total_considered: number;
  degraded?: boolean;
  notice?: string | null;
  broadening_options: BroadeningOption[];
  fallback?: { post_link: string; notify_link: string } | null;
  sponsored?: SearchResult[];
}

export interface ListingSearchParams {
  q?: string;
  category?: string;
  locality?: string;
  radius_km?: number | string;
  service_mode?: string;
  availability?: string;
  verified_only?: boolean | string;
  skills?: readonly string[];
  sort_by?: string;
  broaden_attempt?: number;
  [extra: string]: string | number | boolean | readonly string[] | undefined;
}

export interface SearchSuggestions {
  categories: { slug: string; label: string; [k: string]: unknown }[];
  localities: string[];
}

// ---- enquiries ------------------------------------------------------------------------

export interface EnquirySummary {
  id: string;
  action_type: string;
  state: string;
  /** [Trust pack] "post_closed" when the post closed, expired or filled before an answer. */
  state_reason?: string | null;
  /** The post's or profile's own state (closed / expired / removed when it has ended). */
  target_state?: string | null;
  is_sender: boolean;
  last_activity_at: string;
  target_name: string | null;
  counterpart_name: string | null;
}

export interface EnquiryMessage {
  id: string;
  sender_id: string;
  body: string;
  system_note: boolean;
  created_at: string;
  attachment_url: string | null;
}

export interface EnquiryDetail {
  id: string;
  sender_id: string;
  provider_id: string;
  is_sender: boolean;
  action_type: string;
  state: string;
  delivered: boolean;
  safety_notice_seen: boolean;
  messages: EnquiryMessage[];
  disclosed_contacts: { channel: string; value: string }[];
  // Present in OpenAPI EnquiryOut (read by FE2's contract and contact screens).
  listing_id?: string | null;
  opportunity_id?: string | null;
  /** [FE1, critique N5] backend A: language of the free-text message, when known. */
  message_language?: string | null;
  created_at?: string;
  last_activity_at?: string;
  target_name?: string | null;
  counterpart_name?: string | null;
  bid_amount_paise?: number | null;
  bid_type?: string | null;
  timeline_days?: number | null;
  milestones?: { title: string; amount_paise: number; due_days?: number | null }[] | null;
}

export type EnquiryRole = "sent" | "received";

// ---- activity -------------------------------------------------------------------------

export interface ActivityItem {
  kind: "listing" | "opportunity" | "enquiry" | "partnership";
  id: string;
  title: string;
  group: string;
  status: string | null;
}

export interface ActivityResponse {
  saved: ActivityItem[];
  posted: ActivityItem[];
  recently_viewed: ActivityItem[];
  shared: ActivityItem[];
  completed: ActivityItem[];
  responded: ActivityItem[];
  to_review: ActivityItem[];
  partnerships: ActivityItem[];
}

// ---- notifications ----------------------------------------------------------------------

export interface Notification {
  id: string;
  kind: string;
  title: string;
  body: string | null;
  link: string | null;
  read: boolean;
  created_at: string;
}

// ---- workspace ------------------------------------------------------------------------

export interface WorkspaceInvite {
  id: string;
  listing_id: string;
  listing_name: string | null;
  role: string;
  expires_at: string;
}

export interface WorkspaceRow {
  listing_id: string;
  listing_name: string;
  role: string;
}

// ---- integrations (personal access tokens, webhooks) -----------------------------------

export interface AccessToken {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  status: string;
  created_at: string;
  expires_at: string | null;
  last_used_at?: string | null;
  revoked_at?: string | null;
}

/** Returned once, at creation: `token` is the only time the secret is ever shown. */
export interface AccessTokenCreated extends AccessToken {
  token: string;
}

export interface Webhook {
  id: string;
  url: string;
  description?: string | null;
  event_types: string[];
  all_events: boolean;
  secret_prefix: string;
  active: boolean;
  failure_streak: number;
  created_at: string;
}

export interface WebhookCreated extends Webhook {
  secret: string;
}

export interface WebhookDelivery {
  id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempts: number;
  last_status_code?: number | null;
  last_error?: string | null;
  created_at: string;
  delivered_at?: string | null;
  next_attempt_at?: string | null;
}

export interface WebhookEventType {
  type: string;
  operator_only: boolean;
  description: string;
}

// [Recommendations 2026-09-30] references/imp-recommendations.md
/** One thing Vyapar learned from what the member saved, applied to or hid. */
export interface TasteItem {
  /** Stable id: "skill:electrical", "type:employment", "distance_limit", "pay_floor"… */
  id: string;
  kind: string;
  /** Server-localized, e.g. "Electrician" or "Posts within 8 km". */
  label: string;
  direction: "like" | "avoid";
  /** The kind of action it was mostly learned from (likes only). */
  source?: "applied" | "saved" | "other" | null;
  strength: number;
}

export interface TasteResponse {
  /** false when personalised posts (or usage analytics) are switched off in Privacy. */
  enabled: boolean;
  confidence: number;
  actions_counted: number;
  /** Server-localized lines ("Like jobs you applied to: Electrician"). */
  summary: string[];
  summary_text: string;
  likes: TasteItem[];
  avoids: TasteItem[];
  distance_limit_km?: number | null;
  pay_floor_paise?: number | null;
  updated_at?: string | null;
}
