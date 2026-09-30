/* Marriage agents (DEC-V1-033).
 *
 * Agent seat: apply, the membership, clients (one at a time or from a sheet),
 * biodata of people not on Mangalya, sharing, numbers and exports.
 * Family seat: the directory, Agent Connect, the agent dashboard (everything
 * shared, both kinds), answers, and the switch that closes the family's
 * number to agents. Administrators: applications and prices. */

import {
  API_BASE,
  apiFetch,
  currentLanguageHeader,
  getJson,
  postJson,
  query,
  sendJson,
  type Outcome,
} from './api';
import type { SuggestedPerson } from './rm';

export type AgentRecord = {
  kind: 'staff' | 'agent';
  display_name: string;
  business_name: string | null;
  business_phone: string | null;
  city: string | null;
  languages: string[];
  communities: string[];
  years_active: number | null;
  about: string | null;
  verification_status: 'pending' | 'verified' | 'rejected' | 'suspended';
  applied_at: string | null;
  verified_at: string | null;
  membership_until: string | null;
  live: boolean;
};

export type AgentApplication = {
  display_name: string;
  business_name: string | null;
  business_phone: string | null;
  city: string;
  languages: string[];
  communities: string[];
  years_active: number | null;
  about: string | null;
};

export type DirectoryAgent = {
  account_id: string;
  display_name: string;
  business_name: string | null;
  business_phone: string | null;
  city: string | null;
  languages: string[];
  communities: string[];
  years_active: number | null;
  about: string | null;
  photo_url: string | null;
  verified_at: string | null;
  families: number;
  marriages: number;
};

export const STAGES = ['searching', 'proposal_sent', 'meeting', 'engaged', 'married', 'paused'] as const;
export type Stage = (typeof STAGES)[number];

export type Client = {
  assignment_id: string;
  account_id: string;
  name: string | null;
  age: number | null;
  gender: string | null;
  city: string | null;
  looking_for: 'bride' | 'groom' | null;
  photo_url: string | null;
  stage: Stage;
  stage_changed_at: string;
  origin: 'assigned' | 'added_by_agent' | 'family_chose';
  assigned_at: string;
  made_by_me: boolean;
  claimed: boolean;
  suggestions: number;
  liked: number;
};

export type ImportRow = {
  row: number;
  name: string | null;
  status: 'created' | 'failed';
  account_id: string | null;
  error: string | null;
  warnings: string[];
};

export type ContactPerson = {
  account_id: string;
  display_name: string | null;
  relation: string;
  phone: string | null;
  email: string | null;
};

/** The agent's fair-use limits (DEC-V1-034). Own clients never count. */
export type Quota = {
  contacts_today: number;
  contacts_per_day: number;
  contacts_month: number;
  contacts_per_month: number;
  exported_others_today: number;
  export_others_per_day: number;
  added_today: number;
  profiles_added_per_day: number;
  contact_suspended: boolean;
};

export type ContactState = { open: string[]; opened: string[] };

export type ReportChannel = 'call' | 'whatsapp' | 'sms' | 'email';

export type Suspect = {
  agent_account_id: string;
  display_name: string | null;
  business_name: string | null;
  city: string | null;
  last_at: string;
};

export type ContactReport = {
  id: string;
  channel: ReportChannel;
  happened_on: string;
  note: string | null;
  named_agent_id: string | null;
  status: 'open' | 'dismissed' | 'warned' | 'suspended';
  created_at: string;
};

export const LIMIT_NAMES = [
  'contacts_per_day',
  'contacts_per_month',
  'export_others_per_day',
  'profiles_added_per_day',
  'reports_to_suspend',
] as const;
export type AgentLimits = Record<(typeof LIMIT_NAMES)[number], number>;

export type OfflineProfile = {
  id: string;
  name: string;
  gender: 'male' | 'female';
  age: number | null;
  date_of_birth: string | null;
  city: string | null;
  details: Record<string, string | number>;
  photo_urls: string[];
  biodata_url: string | null;
  biodata_kind: 'pdf' | 'image' | null;
  contact_note: string | null;
  created_at: string;
};

export type Decision = 'liked' | 'passed' | 'ask';

export type Shared = {
  suggestion_id: string;
  assignment_id: string;
  agent_account_id: string;
  note: string | null;
  shared_at: string;
  decision: Decision | null;
  decided_at: string | null;
  question: string | null;
  member_account_id: string | null;
  person: SuggestedPerson | null;
  offline: OfflineProfile | null;
};

export type FamilyAgent = {
  assignment_id: string;
  agent: DirectoryAgent | null;
  stage: Stage;
  origin: string;
  assigned_at: string;
};

export type Activity = {
  agent_account_id: string;
  display_name: string | null;
  business_name: string | null;
  kind: 'contact' | 'excel' | 'biodata';
  at: string;
};

export type Dashboard = {
  candidate_account_id: string;
  may_decide: boolean;
  agent_connect_until: string | null;
  agents_may_see_contact: boolean | null;
  agents: FamilyAgent[];
  shared: Shared[];
  activity: Activity[];
};

export type BiodataPerson = {
  account_id: string;
  is_client: boolean;
  name: string | null;
  age: number | null;
  gender: string | null;
  city: string | null;
  photo_url: string | null;
  biodata: Record<string, Record<string, unknown>>;
  contacts: ContactPerson[];
};

export type BiodataExport = { agent_name: string; agent_phone: string | null; made_on: string; people: BiodataPerson[] };

export type AdminApplication = AgentRecord & { account_id: string };
export type AdminPrice = {
  plan_code: string;
  term_months: number;
  amount_paise: number;
  catalogue_paise: number | null;
  active: boolean;
};

/* ---------- my agent record (cached per page: the account menu asks too) ---------- */

let mine: Promise<AgentRecord | null> | null = null;

export function getMyAgentRecord(refresh = false): Promise<AgentRecord | null> {
  if (!mine || refresh) mine = getJson<AgentRecord | null>('/agents/me');
  return mine;
}

export async function applyAsAgent(body: AgentApplication): Promise<Outcome<AgentRecord>> {
  const out = await postJson<AgentRecord>('/agents/me', body);
  if (out.ok) mine = Promise.resolve(out.data);
  return out;
}

/* ---------- agent seat ---------- */

export function listClients(): Promise<Client[] | null> {
  return getJson<Client[]>('/agents/clients');
}

async function sendForm<T>(path: string, form: FormData): Promise<Outcome<T>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}${path}`, { method: 'POST', body: form, headers: currentLanguageHeader() });
  } catch {
    return { ok: false, status: 0 };
  }
  const text = await res.text();
  let parsed: unknown = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = null;
  }
  if (!res.ok) {
    const detail = (parsed as { detail?: unknown } | null)?.detail;
    const nested = (detail as { message?: unknown } | null)?.message;
    return {
      ok: false,
      status: res.status,
      message: typeof detail === 'string' ? detail : typeof nested === 'string' ? nested : undefined,
    };
  }
  return { ok: true, data: parsed as T };
}

export function addClient(form: FormData): Promise<Outcome<{ account_id: string }>> {
  return sendForm('/agents/clients', form);
}

export function importClients(form: FormData): Promise<Outcome<ImportRow[]>> {
  return sendForm('/agents/clients/import', form);
}

export function setStage(assignmentId: string, stage: Stage): Promise<Outcome<null>> {
  return sendJson('PATCH', `/agents/clients/${assignmentId}/stage`, { stage });
}

export function sharedWithClient(assignmentId: string): Promise<Shared[] | null> {
  return getJson<Shared[]>(`/agents/clients/${assignmentId}/shared`);
}

/** The numbers the agent may see for one person. Each call is written down
 *  for that family, so it is made only when the agent taps "Show number". */
export async function contactFor(accountId: string): Promise<Outcome<ContactPerson[]>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}/agents/contact/${accountId}`, { headers: currentLanguageHeader(), cache: 'no-store' });
  } catch {
    return { ok: false, status: 0 };
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: { message?: string } } | null;
    return { ok: false, status: res.status, message: body?.detail?.message };
  }
  return { ok: true, data: (await res.json()) as ContactPerson[] };
}

/** Who may be opened (the eye is drawn) and who was opened in the last 30
 *  days (opening again is free). */
export function contactOpen(ids: string[]): Promise<Outcome<ContactState>> {
  return postJson('/agents/contact-open', { ids });
}

export function getQuota(): Promise<Quota | null> {
  return getJson<Quota>('/agents/quota');
}

/** Downloads a file answered by a POST (the Excel export). */
export async function downloadExcel(ids: string[], withContacts: boolean): Promise<Outcome<null>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}/agents/export/excel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
      body: JSON.stringify({ ids, with_contacts: withContacts }),
    });
  } catch {
    return { ok: false, status: 0 };
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: { message?: string } } | null;
    return { ok: false, status: res.status, message: body?.detail?.message };
  }
  const blob = await res.blob();
  const name = /filename="([^"]+)"/.exec(res.headers.get('Content-Disposition') ?? '')?.[1] ?? 'mangaly-biodata.xlsx';
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return { ok: true, data: null };
}

export async function downloadTemplate(): Promise<void> {
  const res = await apiFetch(`${API_BASE}/agents/clients/template`, { headers: currentLanguageHeader() });
  if (!res.ok) return;
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mangaly-clients.xlsx';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function exportBiodata(ids: string[], withContacts: boolean): Promise<Outcome<BiodataExport>> {
  return postJson('/agents/export/biodata', { ids, with_contacts: withContacts });
}

export function listOffline(): Promise<OfflineProfile[] | null> {
  return getJson<OfflineProfile[]>('/agents/offline');
}

export function addOffline(form: FormData): Promise<Outcome<OfflineProfile>> {
  return sendForm('/agents/offline', form);
}

export function archiveOffline(id: string): Promise<Outcome<null>> {
  return postJson(`/agents/offline/${id}/archive`);
}

export function share(body: {
  assignment_ids: string[];
  member_ids?: string[];
  offline_ids?: string[];
  note?: string | null;
}): Promise<Outcome<{ shared: number }>> {
  return postJson('/agents/share', body);
}

/* ---------- family seat ---------- */

export function getDirectory(city?: string): Promise<DirectoryAgent[] | null> {
  return getJson<DirectoryAgent[]>(`/agents/directory${query({ city })}`);
}

export function getDashboard(forCandidate?: string): Promise<Dashboard | null> {
  return getJson<Dashboard>(`/agents/dashboard${query({ for_candidate: forCandidate })}`);
}

export function chooseAgent(agentAccountId: string, forCandidate?: string): Promise<Outcome<{ assignment_id: string }>> {
  return postJson('/agents/choose', { agent_account_id: agentAccountId, for_candidate: forCandidate });
}

export function releaseAgent(agentAccountId: string, forCandidate?: string): Promise<Outcome<null>> {
  return postJson('/agents/release', { agent_account_id: agentAccountId, for_candidate: forCandidate });
}

export function setAgentsMaySeeContact(open: boolean, forCandidate?: string): Promise<Outcome<null>> {
  return sendJson('PATCH', '/agents/privacy', { open, for_candidate: forCandidate });
}

export function answerShared(
  suggestionId: string,
  decision: Decision,
  question?: string,
  forCandidate?: string,
): Promise<Outcome<Shared>> {
  return postJson(`/agents/shared/${suggestionId}/answer`, { decision, question, for_candidate: forCandidate });
}

/** Agents who opened or exported the family's number in the 30 days up to a day. */
export function getSuspects(day: string, forCandidate?: string): Promise<Suspect[] | null> {
  return getJson<Suspect[]>(`/agents/reports/suspects${query({ day, for_candidate: forCandidate })}`);
}

export function listReports(forCandidate?: string): Promise<ContactReport[] | null> {
  return getJson<ContactReport[]>(`/agents/reports${query({ for_candidate: forCandidate })}`);
}

export function reportUnwantedContact(body: {
  channel: ReportChannel;
  happened_on: string;
  note?: string | null;
  named_agent_id?: string | null;
  for_candidate?: string;
}): Promise<Outcome<{ report_id: string }>> {
  return postJson('/agents/reports', body);
}

/* ---------- administrators ---------- */

export function getLimits(): Promise<AgentLimits | null> {
  return getJson<AgentLimits>('/agents/admin/limits');
}

export function setLimit(name: keyof AgentLimits, value: number): Promise<Outcome<null>> {
  return sendJson('PATCH', '/agents/admin/limits', { name, value });
}

export function listApplications(): Promise<AdminApplication[] | null> {
  return getJson<AdminApplication[]>('/agents/admin/applications');
}

export function reviewApplication(accountId: string, status: 'verified' | 'rejected'): Promise<Outcome<null>> {
  return postJson(`/agents/admin/applications/${accountId}/review`, { status });
}

export function listPrices(): Promise<AdminPrice[] | null> {
  return getJson<AdminPrice[]>('/agents/admin/prices');
}

export function setPrice(body: {
  plan_code: string;
  term_months: number;
  amount_paise: number;
  active: boolean;
}): Promise<Outcome<null>> {
  return sendJson('PATCH', '/agents/admin/prices', body);
}

/* ---------- small shared helpers ---------- */

/** Indian day-month order in the reader's language: "29 Sept 2026". */
export function formatDay(iso: string | null | undefined, lang: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(lang === 'en' ? 'en-IN' : `${lang}-IN`, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
}
