/* Messaging calls against MangalyService — FR049. */

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

async function postJson<T>(path: string, body?: unknown): Promise<Outcome<T>> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}${path}`, {
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

export type ConversationSummary = {
  connection_id: string;
  other_account_id: string;
  other_name: string | null;
  other_photo_url: string | null;
  last_message_at: string | null;
};

export type Message = {
  id: string;
  /* null for a system line: the platform is speaking, not either person. */
  sender_account_id: string | null;
  /* 'member' for something a person wrote, 'system' for a line the platform
     added — a system line's `content` is a key, rendered in the reader's own
     language rather than frozen in the sender's. */
  kind: 'member' | 'system';
  content: string;
  sent_at: string;
};

export async function listConversations(): Promise<ConversationSummary[]> {
  return (await getJson<ConversationSummary[]>('/messages')) ?? [];
}

export async function listMessages(connectionId: string): Promise<Message[]> {
  return (await getJson<Message[]>(`/messages/${connectionId}`)) ?? [];
}

export async function sendMessage(connectionId: string, content: string): Promise<Outcome<Message>> {
  return postJson(`/messages/${connectionId}`, { content });
}

/** [DEC-V1-021] End the session: everything the two wrote is deleted for both.
 * `keepalive` so the browser still sends it while the page is being closed —
 * leaving the thread is itself the end of the session. */
export async function closeConversation(connectionId: string): Promise<void> {
  try {
    await apiFetch(`${API_BASE}/messages/${connectionId}/close`, {
      method: 'POST',
      credentials: 'include',
      keepalive: true,
      headers: currentLanguageHeader(),
    });
  } catch {
    /* Leaving is not a moment to show an error; the next open purges anyway. */
  }
}
