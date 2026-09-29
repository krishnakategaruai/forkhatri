// [FE2 — imp-backend-b §1] Contact actions with poster control: the
// member's own calling preferences (account-wide and per listing), and the
// Call / WhatsApp actions on an accepted enquiry. Nothing here ever carries
// a phone number before acceptance — the server sends `revealed: false`
// and no hrefs until both sides have accepted.
import { seg, type VyaparClient } from "../client";

export type Weekday = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";
export type CallsFrom = "anyone" | "matching_only";
export type ContactChannel = "call" | "whatsapp";

export interface ContactPreferences {
  /** "HH:MM" in the member's timezone (IST); null = any time. */
  call_hours_start: string | null;
  call_hours_end: string | null;
  /** Empty = every day. */
  call_days: Weekday[];
  /** null = no limit. */
  max_calls_per_day: number | null;
  calls_from: CallsFrom;
  whatsapp_ok: boolean;
  call_ok: boolean;
  timezone?: string;
}

export type ContactPreferenceField = Exclude<keyof ContactPreferences, "timezone">;

export interface ContactPreferencesPatch extends Partial<Omit<ContactPreferences, "timezone">> {
  /** Fields to put back to the default (account) or to inherit (listing). */
  reset?: ContactPreferenceField[];
}

export interface ListingContactPreferences {
  listing_id: string;
  effective: ContactPreferences;
  /** Fields this listing sets itself; the rest follow the account. */
  overrides: ContactPreferenceField[];
}

export type ContactUnavailableReason =
  | "outside_hours"
  | "day_off"
  | "daily_cap_reached"
  | "not_matching"
  | "precall_off"
  | "caller_limit_reached";

export interface ContactAction {
  channel: ContactChannel | string;
  label: string;
  href: string | null;
  available_now: boolean;
  next_window: string | null;
  reason: ContactUnavailableReason | string | null;
  /** Server-localized explanation of `reason`, including the next window. */
  reason_label: string | null;
  /** e.g. "mon-sat 09:00-18:00"; null when there is no restriction. */
  window: string | null;
}

export interface ContactAttempt {
  id: string;
  enquiry_id: string;
  caller_id: string;
  callee_id: string;
  channel: ContactChannel | string;
  at: string;
  mine: boolean;
  /** Server-localized: "You contacted Anita Khatri by Call on 28 Sep 2026, 14:05". */
  summary: string;
}

export interface ContactActions {
  enquiry_id: string;
  revealed: boolean;
  counterpart_id: string;
  counterpart_name: string | null;
  contact_actions: ContactAction[];
  attempts: ContactAttempt[];
  calls_today?: number;
  max_calls_per_day?: number | null;
  /**
   * [FE2, pending backend A "shortlist reveals the applicant's number"] true when
   * the OTHER side can reach the viewer although the viewer cannot see theirs yet
   * (a shortlisted applicant: the poster may call them). Optional until it ships.
   */
  counterpart_can_contact?: boolean;
}

/**
 * [FE2 — imp-backend-b "Pre-accept calling"] Call / WhatsApp straight from an
 * opportunity, before any application, when the poster switched on
 * `allow_precall` (employment and local-service posts only). The number is
 * only ever inside `href`, and only while `available_now` is true.
 */
export type PrecallTopReason = "precall_off" | "own_post" | "no_contact";

export interface PrecallActions {
  opportunity_id: string;
  allow_precall: boolean;
  available: boolean;
  /** Why nothing can be offered at all (anonymous callers get precall_off). */
  reason: PrecallTopReason | string | null;
  reason_label: string | null;
  poster_name: string | null;
  contact_actions: ContactAction[];
  calls_today?: number;
  max_calls_per_day?: number | null;
  /** This caller's taps on this post today, and the daily allowance (3). */
  my_taps_today?: number;
  my_taps_limit?: number;
  /** The caller's open application on this post, if any. */
  application_enquiry_id?: string | null;
  attempts?: ContactAttempt[];
}

/** After a tap: the updated actions, plus whether an application was opened for the caller. */
export interface PrecallAttemptResult extends PrecallActions {
  attempt_id: string;
  application_created: boolean;
  application_error_code: string | null;
}

export function contactApi(c: VyaparClient) {
  const enquiry = (id: string) => `/v1/enquiries/${seg(id)}`;
  const opportunity = (id: string) => `/v1/opportunities/${seg(id)}`;
  return {
    /** getOpportunityContactActions — pre-accept calling, when the poster allows it */
    precallActions: (opportunityId: string) => c.get<PrecallActions>(`${opportunity(opportunityId)}/contact-actions`),
    /** recordOpportunityContactAttempt — call BEFORE opening the link; returns the updated actions */
    recordPrecallAttempt: (opportunityId: string, channel: ContactChannel) =>
      c.post<PrecallAttemptResult>(`${opportunity(opportunityId)}/contact-attempts`, { channel }, { keepalive: true }),
    /** getContactPreferences — the caller's account-wide settings */
    preferences: () => c.get<ContactPreferences>("/v1/listings/contact-preferences"),
    /** updateContactPreferences */
    updatePreferences: (patch: ContactPreferencesPatch) => c.patch<ContactPreferences>("/v1/listings/contact-preferences", patch),
    /** getListingContactPreferences — owner only */
    listingPreferences: (listingId: string) =>
      c.get<ListingContactPreferences>(`/v1/listings/${seg(listingId)}/contact-preferences`),
    /** updateListingContactPreferences — `reset` makes a field inherit the account value again */
    updateListingPreferences: (listingId: string, patch: ContactPreferencesPatch) =>
      c.patch<ListingContactPreferences>(`/v1/listings/${seg(listingId)}/contact-preferences`, patch),
    /** getEnquiryContactActions — either party */
    actions: (enquiryId: string) => c.get<ContactActions>(`${enquiry(enquiryId)}/contact-actions`),
    /** listContactAttempts */
    attempts: (enquiryId: string) => c.get<ContactAttempt[]>(`${enquiry(enquiryId)}/contact-attempts`),
    /** recordContactAttempt — call BEFORE opening the tel:/wa.me link; returns the updated actions */
    // keepalive: the dialler / WhatsApp opens at once, so the page may be
    // leaving while this is in flight (critique L4)
    recordAttempt: (enquiryId: string, channel: ContactChannel) =>
      c.post<ContactActions>(`${enquiry(enquiryId)}/contact-attempts`, { channel }, { keepalive: true }),
  };
}

export type ContactApi = ReturnType<typeof contactApi>;
