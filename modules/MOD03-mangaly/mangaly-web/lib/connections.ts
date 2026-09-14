/* Connection calls against MangalyService — FR042/FR043/FR044/FR045. */

import { API_BASE } from './api';
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
    const res = await fetch(`${API_BASE}${path}`, {
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

async function postJson<T>(path: string, body?: unknown): Promise<Outcome<T>> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
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
  on_behalf_of_profile_id: string | null;
  target_account_id: string;
  status: ConnectionStatus;
  requested_at: string;
  decided_at: string | null;
};

export async function sendRequest(targetAccountId: string): Promise<Outcome<Connection>> {
  return postJson('/connections', { target_account_id: targetAccountId });
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
