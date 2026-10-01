/* Thin JSON client for the Counsel API. The member is the ForKhatri session
 * cookie (credentials: include) — never a header this client sets. */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8014";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE ?? API_BASE.replace(/^http/, "ws");

export class ApiError extends Error {
  status: number;
  code: string;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    const d = detail as { code?: string; message?: string } | null;
    super(d?.message ?? `HTTP ${status}`);
    this.status = status;
    this.code = d?.code ?? "error";
    this.detail = detail;
  }
}

let language = "en";
export function setApiLanguage(lang: string) {
  language = lang;
}

export const UNAUTHORIZED_EVENT = "counsel:unauthorized";

/** API-served media ("/media/...") resolves against the API; anything else is used as is. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return path.startsWith("/media/") ? `${API_BASE}${path}` : path;
}

type Opts = { method?: string; body?: unknown; form?: FormData; signal?: AbortSignal };

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = { "X-Counsel-Language": language };
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? (opts.body !== undefined || opts.form ? "POST" : "GET"),
    headers,
    body: opts.form ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
    signal: opts.signal,
    cache: "no-store",
    credentials: "include",
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: { detail?: unknown } | null = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (res.status === 401 && typeof window !== "undefined") window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  if (!res.ok) throw new ApiError(res.status, data?.detail ?? data);
  return data as unknown as T;
}

/* ---------- Types ---------- */
export type Me = {
  member_id: string; display_name: string; language: string; is_admin: boolean;
  provider_status: string | null; unread: number; upcoming: number; entrance_url: string;
};
export type Expertise = { id: string; name: string; regulated: boolean; providers: number; parent_id: string | null };
export type ExpertiseTag = { id: string; name: string; years: number; primary: boolean; regulated: boolean };
export type Card = {
  id: string; name: string; headline: string; photo_url: string | null; city: string | null; country: string; languages: string[];
  status: string; expertise: ExpertiseTag[]; verified: string[]; rating: number | null; review_count: number; completed: number;
  from_minor: number | null; service_count: number; currency: string; next_slot: string | null; saved: boolean; why?: string[];
  badges?: { id: string; level: number; threshold: number | null; since: string }[]; standing?: string; available_now?: boolean;
  city_id?: string | null; distance_km?: number | null; reply_hours?: number | null; approved_at?: string | null;
};
export type Service = {
  id: string; provider_id: string; area_id: string; area_name?: string; title: string; description: string; outcomes: string[];
  duration_min: number; price_minor: number; currency: string; formats: string[]; min_notice_hours: number; max_advance_days: number;
  buffer_min: number; recording_allowed: boolean; status: string; allow_custom_time?: boolean;
};
export type Reputation = {
  completed: number; clients: number; repeat_clients: number; reliability_percent: number | null; rating: number | null; review_count: number;
  dimensions: { expertise: number | null; communication: number | null; professionalism: number | null; punctuality: number | null };
};
export type Evidence = { id: string; kind: string; title: string; issuer: string | null; year_from: number | null; year_to: number | null; status: string; reference_no?: string | null; review_note?: string | null; has_document?: boolean; document_name?: string | null };
export type Review = { id: string; overall: number; body: string; created_at: string; reviewer: string | null };
export type Profile = Card & {
  intro: string; timezone: string; links: Record<string, string>; services: Service[]; evidence: Evidence[]; reviews: Review[];
  reputation: Reputation; weekly: { weekday: number; start_time: string; end_time: string; kind: string }[];
};
export type Quote = { gross_minor: number; platform_fee_minor: number; processing_fee_minor: number; tax_minor: number; provider_payable_minor: number; currency: string; platform_fee_percent: number };
export type Policy = { seeker: { min_hours_before: number; refund_percent: number }[]; provider_cancel_refund_percent: number; seeker_no_show_refund_percent: number; provider_no_show_refund_percent: number };
export type ServiceDetail = Service & { follow_up_eligible?: boolean; packages: { id: string; sessions: number; price_minor: number; valid_days: number }[]; available_now: boolean; question_price_minor: number | null; question_answer_days: number; instant_allowed: boolean; provider_name: string; provider_timezone: string; photo_url: string | null; regulated: boolean; disclaimer_key: string | null; quote: Quote; cancellation_policy: Policy };
export type Booking = {
  id: string; service_id: string; provider_id: string; seeker_id: string; starts_at: string; ends_at: string; status: string; brief: string;
  service_title: string; duration_min: number; currency: string; gross_minor: number; platform_fee_minor: number; provider_payable_minor: number;
  refund_minor: number; cancellation_policy: Policy; recording_allowed: boolean; formats: string[]; cancel_reason: string | null;
  provider_name: string; seeker_name: string; role: "seeker" | "provider"; reviewed?: boolean; provider_photo?: string | null;
  pay_by?: string | null; recap?: string | null; purchase_id?: string | null; service_price_minor?: number;
  follow_ups?: { id: string; sessions: number; price_minor: number; valid_days: number }[];
  review?: { overall: number; body: string } | null; dispute?: { id: string; status: string; reason: string; resolution: string | null; refund_minor: number } | null;
  checkout?: { external_ref: string; mode: string };
  has_recap?: boolean; payout_status?: "none" | "eligible" | "paid"; completed_at?: string | null; cancelled_at?: string | null; created_at?: string;
};
export type TimelineEvent = { kind: string; at: string; who: "you" | "other" | null; params: { amount_minor?: number; overall?: number; status?: string } };
export type Message = { id: number; sender_id: string | null; kind: "chat" | "system" | "file"; body: string; file_id: string | null; created_at: string };
export type Notification = { id: number; kind: string; params: Record<string, unknown>; booking_id: string | null; read_at: string | null; created_at: string };
export type ActionItem = { id: string; text: string; owner_id: string | null; done: boolean; created_by: string; created_at: string };
export type RoomFile = { id: string; owner_id: string; name: string; mime: string; size_bytes: number; created_at: string; is_recording?: boolean };
export type RoomState = {
  booking: { id: string; status: string; starts_at: string; ends_at: string; service_title: string; duration_min: number; recording_allowed: boolean; formats: string[]; brief: string; provider_id: string; seeker_id: string };
  role: "seeker" | "provider"; me: string; names: Record<string, string>; open: boolean; live: boolean; ice_servers: RTCIceServer[];
  shared_note: { body: string; version: number }; private_note: { body: string; version: number };
  actions: ActionItem[]; files: RoomFile[]; consents: string[]; recording: boolean; present: string[];
};
