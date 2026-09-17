/* Connection calls against MangalyService — FR042/FR043/FR044/FR045. */

import { API_BASE, apiFetch } from './api';
import { getI18n } from './i18n/config';

function currentLanguageHeader(): Record<string, string> {
  try {
    return { 'X-Mangaly-Language': getI18n().language };
  } catch {
    return {};
  }
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await apiFetch(`${API_BASE}${path}`, {
      credentials: 'include',
      cache: 'no-store',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text ? (JSON.parse(text) as T) : null;
  } catch {
    return null;
  }
}

type Outcome<T> = { ok: true; data: T } | { ok: false; status: number; message?: string };

function postJson<T>(path: string, body?: unknown): Promise<Outcome<T>> {
  return sendJson<T>('POST', path, body);
}

async function sendJson<T>(method: 'POST' | 'PATCH' | 'DELETE', path: string, body?: unknown): Promise<Outcome<T>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}${path}`, {
      method,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...currentLanguageHeader() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    return { ok: false, status: 0 };
  }
  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;
  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      message: typeof parsed?.detail === 'string' ? parsed.detail : undefined,
    };
  }
  return { ok: true, data: parsed as T };
}

export type ConnectionStatus = 'pending' | 'accepted' | 'declined';

export type Connection = {
  id: string;
  acting_account_id: string;
  /* Whose request it is: the candidate. Equals acting_account_id unless a Home
     Circle member sent it for them (FR042). */
  subject_account_id: string;
  sent_by_family: boolean;
  on_behalf_of_profile_id: string | null;
  target_account_id: string;
  status: ConnectionStatus;
  requested_at: string;
  decided_at: string | null;
};

export async function sendRequest(
  targetAccountId: string,
  onBehalfOfAccountId?: string
): Promise<Outcome<Connection>> {
  return postJson('/connections', {
    target_account_id: targetAccountId,
    ...(onBehalfOfAccountId ? { on_behalf_of_account_id: onBehalfOfAccountId } : {}),
  });
}

export async function listIncoming(): Promise<Connection[]> {
  return (await getJson<Connection[]>('/connections/incoming')) ?? [];
}

export async function listSent(): Promise<Connection[]> {
  return (await getJson<Connection[]>('/connections/sent')) ?? [];
}

export async function getConnection(connectionId: string): Promise<Connection | null> {
  return await getJson<Connection>(`/connections/${connectionId}`);
}

export async function accept(connectionId: string): Promise<Outcome<null>> {
  return postJson(`/connections/${connectionId}/accept`);
}

export async function decline(connectionId: string): Promise<Outcome<null>> {
  return postJson(`/connections/${connectionId}/decline`);
}

/* FR046/FR047 — per-category sharing inside one accepted connection. */

export type ShareCategory = 'additional_photos' | 'phone' | 'email' | 'family_contact';

export type ShareState = {
  category: ShareCategory;
  shared_at: string | null;
  value: string | null;
  available: boolean;
  pending?: string | null;
};

export type SharingOverview = {
  connection_id: string;
  other_account_id: string;
  mine: ShareState[];
  theirs: ShareState[];
};

export async function getSharing(connectionId: string): Promise<SharingOverview | null> {
  return await getJson<SharingOverview>(`/connections/${connectionId}/sharing`);
}

export async function setShare(
  connectionId: string,
  category: ShareCategory,
  shared: boolean
): Promise<Outcome<ShareState>> {
  return sendJson('PATCH', `/connections/${connectionId}/share/${category}`, { shared });
}

/* FR048 — a family member's phone, shared only after that member approves. */

export async function requestFamilyContact(
  connectionId: string,
  membershipId: string
): Promise<Outcome<ShareState>> {
  return sendJson('POST', `/connections/${connectionId}/share/family-contact`, { membership_id: membershipId });
}

export async function withdrawFamilyContact(connectionId: string): Promise<Outcome<ShareState>> {
  return sendJson('DELETE', `/connections/${connectionId}/share/family-contact`);
}
