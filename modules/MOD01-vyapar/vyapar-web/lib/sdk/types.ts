// [IMP38 — Refactor C] Wire types for the Vyapar API, as the web app reads
// them. Taken from the interfaces the screens already declared (so nothing
// the screens rely on changed shape); where the backend's OpenAPI document
// (vyapar-service/openapi.json, workstream A) names more fields, they are
// optional additions here, never required.
//
// Conventions: raw slugs sit next to their localized labels
// (`capabilities` + `capability_labels`); labels arrive already translated
// into the language the client sent in X-Vyapar-Language.

// ---- shared -------------------------------------------------------------------

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
  // Present in OpenAPI OpportunityOut; not read by the web screens.
  value_amount?: number | null;
  source_unreachable?: boolean;
  entry_mode?: string;
  state_reason?: string | null;
  relevance_reason?: string | null;
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
}

export interface FeedParams {
  skills?: readonly string[];
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
}

export interface SearchResult {
  listing: SearchListing;
  relevance_reason: string;
  distance_km?: number | null;
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
