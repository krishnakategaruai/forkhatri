/**
 * Typed client for the Admin & Governance Console API (identity service /v1/admin,
 * ARCHITECTURE.md ADR-012). Same transport rules as lib/api.ts: the session is an
 * HttpOnly cookie this code never sees, and failures surface as ApiError / NetworkError.
 */
import { ApiError, IDENTITY_API, NetworkError, type Lang } from "./api";

export type Person = { member_id: string; display_name: string | null };

export type RoleKey =
  | "owner"
  | "president"
  | "secretary"
  | "treasurer"
  | "grievance_officer"
  | "data_protection_officer"
  | "auditor"
  | "chapter_head"
  | "chapter_secretary"
  | "moderator"
  | "verifier";

export type ScopeKind = "platform" | "module" | "chapter";

export type RoleDef = {
  key: RoleKey;
  scope_kind: ScopeKind;
  sensitive: boolean;
  permissions: string[];
  module_actions: string[];
};

export type MyRole = {
  assignment_id: string;
  role: RoleKey;
  scope_kind: ScopeKind;
  scope_key: string | null;
  title: string | null;
  ends_at: string | null;
};

export type AdminMe = {
  is_admin: boolean;
  member: Person;
  roles: MyRole[];
  permissions: string[];
  module_scopes: string[];
  managed_chapters: string[];
  catalogue: { roles: RoleDef[]; reason_codes: string[]; suspension_days: number[] } | null;
};

export type AuditEvent = {
  id: number;
  at: string;
  action: string;
  actor: Person | null;
  target: Person | null;
  module_key: string | null;
  subject: string | null;
  reason_code: string | null;
  note: string | null;
  details: Record<string, unknown>;
};

export type Approval = {
  id: string;
  kind: "ban" | "grant_role";
  target: Person;
  payload: { role?: RoleKey; scope_kind?: ScopeKind; scope_key?: string | null; title?: string | null; ends_at?: string | null };
  reason_code: string;
  note: string;
  requested_by: Person;
  requested_at: string;
  status: "pending" | "approved" | "declined" | "withdrawn";
  decided_by: Person | null;
  decided_at: string | null;
  decision_note: string | null;
  can_decide?: boolean;
};

export type Overview = {
  members: { total: number; suspended: number; not_joined: number; new_7d: number; active_7d: number };
  approvals: Approval[];
  suspensions_ending: { member: Person; ends_at: string; reason_code: string }[];
  terms_ending: { assignment_id: string; member: Person; role: RoleKey; scope_kind: ScopeKind; scope_key: string | null; ends_at: string }[];
  recent: AuditEvent[];
};

export type MemberRow = {
  member_id: string;
  display_name: string;
  phone_hint: string | null;
  email_hint: string | null;
  status: "active" | "suspended" | "deleted";
  joined: boolean;
  created_at: string;
  last_seen_at: string | null;
  is_staff: boolean;
};

export type Assignment = {
  id: string;
  member: Person & { status: string };
  role: RoleKey;
  scope_kind: ScopeKind;
  scope_key: string | null;
  scope_name: string | null;
  title: string | null;
  starts_at: string;
  ends_at: string | null;
  granted_by: Person | null;
  grant_note: string;
  revoked_at: string | null;
};

export type Suspension = {
  id: string;
  kind: "suspension" | "ban";
  reason_code: string;
  note: string;
  starts_at: string;
  ends_at: string | null;
  by: Person | null;
  lifted_at: string | null;
  lifted_by: Person | null;
  lift_note: string | null;
};

export type MemberDetail = {
  member: {
    member_id: string;
    display_name: string;
    phone_hint: string | null;
    email_hint: string | null;
    preferred_language: Lang;
    identity_level: number;
    joined: boolean;
    status: "active" | "suspended" | "deleted";
    created_at: string;
  };
  sessions: { active: number; last_seen_at: string | null; first_sign_in_at: string | null };
  modules: { key: string; name: string; first_entered_at: string; last_entered_at: string; visits: number }[];
  roles: Assignment[];
  suspensions: Suspension[];
  pending_approvals: Approval[];
  history: AuditEvent[];
};

/** One module's own view of a person. Pricing tiers differ per module and are never merged. */
export type ModuleSummary = {
  module_id: string;
  error: string | null;
  plan?: { tier: string; name?: string; status?: string; renews_at?: string | null } | null;
  facts?: { label: string; value: string }[];
  flags?: string[];
};

export type Chapter = { key: string; name: string; kind: "state" | "city"; parent_key: string | null; office_bearers: Assignment[] };
export type Organisation = { national: Assignment[]; staff: Assignment[]; chapters: Chapter[]; modules: Assignment[] };

export type AdminModule = { key: string; name: string; availability: "available" | "in_development" | "planned"; members: number; updated_at: string };

/** TR-PLAT-01 AdminQueueItem, as each module sends it. */
export type QueueItem = {
  item_id: string;
  module_id: string;
  item_type: string;
  submitted_at: string;
  priority: "urgent" | "high" | "normal" | string;
  status: string;
  summary_text: string;
  subject_title?: string | null;
  reason?: string | null;
  due_at?: string | null;
};

export type QueueView = {
  module_id: string;
  view_id: string | null;
  title: string;
  nav_group?: string;
  required_permission_scope?: string;
  error: string | null;
  items: QueueItem[];
};

export type QueueDetail = { item_id: string; case_detail: Record<string, unknown>; available_actions: string[] };

type Method = "GET" | "POST" | "PATCH";

async function call<T>(path: string, { method = "GET", body, lang }: { method?: Method; body?: unknown; lang?: Lang } = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (lang) headers["Accept-Language"] = lang;
  let response: Response;
  try {
    response = await fetch(`${IDENTITY_API}/v1/admin${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "include",
      cache: "no-store",
    });
  } catch (error) {
    throw new NetworkError(error);
  }
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const detail = (payload as { detail?: { code?: unknown; message?: unknown } } | null)?.detail;
    throw new ApiError(
      response.status,
      typeof detail?.code === "string" ? detail.code : `http_${response.status}`,
      typeof detail?.message === "string" ? detail.message : response.statusText,
      null,
    );
  }
  return payload as T;
}

const q = (params: Record<string, string | number | null | undefined>) => {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value !== null && value !== undefined && value !== "") search.set(key, String(value));
  const text = search.toString();
  return text ? `?${text}` : "";
};

export type GrantResult = { status: "granted"; assignment_id: string } | { status: "approval_required"; approval_id: string };

export const admin = {
  me: () => call<AdminMe>("/me"),
  overview: () => call<Overview>("/overview"),

  members: (p: { q?: string; status?: string; offset?: number }) => call<{ total: number; members: MemberRow[] }>(`/members${q({ ...p, limit: 30 })}`),
  member: (id: string) => call<MemberDetail>(`/members/${id}`),
  memberModules: (id: string, lang: Lang) => call<ModuleSummary[]>(`/members/${id}/modules`, { lang }),
  contact: (id: string, note: string) => call<{ phone_e164: string | null; email: string | null }>(`/members/${id}/contact`, { method: "POST", body: { note } }),
  suspend: (id: string, body: { reason_code: string; days: number | null; note: string }) =>
    call<MemberDetail>(`/members/${id}/suspend`, { method: "POST", body }),
  lift: (id: string, note: string) => call<MemberDetail>(`/members/${id}/lift`, { method: "POST", body: { note } }),
  signOut: (id: string, note: string) => call<MemberDetail>(`/members/${id}/sign-out`, { method: "POST", body: { note } }),
  ban: (id: string, body: { reason_code: string; note: string }) => call<GrantResult>(`/members/${id}/ban`, { method: "POST", body }),

  approvals: (status: string | null) => call<Approval[]>(`/approvals${q({ status: status ?? "all" })}`),
  decide: (id: string, decision: "approved" | "declined" | "withdrawn", note: string) =>
    call<Approval>(`/approvals/${id}/decide`, { method: "POST", body: { decision, note: note || null } }),

  roles: () => call<Assignment[]>("/roles"),
  grant: (body: { member_id: string; role: RoleKey; scope_key: string | null; title: string | null; ends_at: string | null; note: string }) =>
    call<GrantResult>("/roles", { method: "POST", body }),
  revoke: (id: string, note: string) => call<{ status: string }>(`/roles/${id}/revoke`, { method: "POST", body: { note } }),

  org: () => call<Organisation>("/org"),
  addChapter: (body: { name: string; kind: "state" | "city"; parent_key: string | null }) => call<{ key: string }>("/org/chapters", { method: "POST", body }),
  closeChapter: (key: string, note: string) => call<{ status: string }>(`/org/chapters/${encodeURIComponent(key)}/close`, { method: "POST", body: { note } }),

  audit: (p: { action?: string; before?: number | null; target?: string }) => call<{ events: AuditEvent[]; next_before: number | null }>(`/audit${q({ ...p, limit: 40 })}`),

  modules: () => call<AdminModule[]>("/modules"),
  setModule: (key: string, availability: AdminModule["availability"], note: string) =>
    call<AdminModule[]>(`/modules/${encodeURIComponent(key)}`, { method: "PATCH", body: { availability, note } }),

  queues: (lang: Lang) => call<QueueView[]>("/queues", { lang }),
  queueItem: (module: string, view: string, item: string, lang: Lang) =>
    call<QueueDetail>(`/queues/${encodeURIComponent(module)}/${encodeURIComponent(view)}/${encodeURIComponent(item)}`, { lang }),
  queueAction: (module: string, view: string, item: string, action: string, body: { notes?: string; reason_code?: string }, lang: Lang) =>
    call<QueueItem>(
      `/queues/${encodeURIComponent(module)}/${encodeURIComponent(view)}/${encodeURIComponent(item)}/actions/${encodeURIComponent(action)}`,
      { method: "POST", body, lang },
    ),
};
