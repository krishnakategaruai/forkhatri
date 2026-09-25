/* Messaging calls against MangalyService — FR049.
 *
 * [2026-09-17 rework, contract §2/§3] Two conversation kinds on a connection:
 * `candidate` (the two candidates only, exists on accept — a session, not a
 * history, DEC-V1-021) and `family` (both candidates plus both circles,
 * opened when either candidate taps "Involve my family"). One thread UI for
 * both. `GET /conversations?for_candidate=` lists both kinds. */

import { API_BASE, apiFetch, currentLanguageHeader, getJson, postJson, query, type Outcome } from './api';

/** `direct` (migration 046): an ordinary one-to-one chat, addressed by its
 * conversation id; the other two are addressed by their connection id. */
export type ConversationKind = 'candidate' | 'family' | 'direct';

export type Participant = {
  account_id: string;
  name: string | null;
  photo_url?: string | null;
  /** "Ananya's mother" style label, or null for a candidate. */
  role_label?: string | null;
  side?: 'mine' | 'theirs';
};

export type ConversationSummary = {
  connection_id: string;
  conversation_id?: string;
  kind: ConversationKind;
  other_account_id: string;
  other_name: string | null;
  other_photo_url: string | null;
  last_message_at: string | null;
  last_message?: { content: string; kind?: 'member' | 'system'; sender_account_id?: string | null; sender_name?: string | null; sent_at?: string } | string | null;
  unread_count?: number;
  participants?: ThreadPerson[];
  /** Family kind: whether the caller's side has joined yet. */
  joined?: boolean;
};

export type Message = {
  id: string;
  /* null for a system line: the platform is speaking, not either person. */
  sender_account_id: string | null;
  sender_name?: string | null;
  /* 'member' for something a person wrote, 'system' for a line the platform
     added — a system line's `content` is a key, rendered in the reader's own
     language rather than frozen in the sender's. */
  kind: 'member' | 'system';
  content: string;
  sent_at: string;
  sender_role?: string | null;
  /** [Migration 044] Exact relation ("mother") and whose side the sender is on. */
  sender_relation?: string | null;
  sender_side_account_id?: string | null;
};

/** One person in a thread, as the API names them (migration 044). */
export type ThreadPerson = {
  account_id: string;
  display_name: string | null;
  /** 'candidate', or the circle role: parent, sibling, relative, guardian. */
  role: string;
  photo_url: string | null;
  is_me: boolean;
  relation?: string | null;
  /** The candidate whose side this person is on (a candidate: themself). */
  side_account_id?: string | null;
  /** That candidate's name, for "father of Divya". */
  side_name?: string | null;
};

export async function listPeople(connectionId: string, kind: ConversationKind): Promise<ThreadPerson[]> {
  return (
    (await getJson<ThreadPerson[]>(
      `/messages/${connectionId}/people${query({ kind: kind === 'candidate' ? undefined : kind })}`,
    )) ?? []
  );
}

/** [DEC-V1-024] Report from inside a thread; the thread is kept with the report. */
export async function reportInThread(
  connectionId: string,
  kind: ConversationKind,
  reportedAccountId: string,
  reason: string,
  details: string,
): Promise<Outcome<{ report_id: string; message: string }>> {
  return postJson(`/messages/${connectionId}/report${query({ kind: kind === 'candidate' ? undefined : kind })}`, {
    reported_account_id: reportedAccountId,
    reason,
    details,
  });
}

export function lastMessageText(c: ConversationSummary): string | null {
  if (!c.last_message) return null;
  return typeof c.last_message === 'string' ? c.last_message : c.last_message.content;
}

export async function listConversations(forCandidate?: string): Promise<ConversationSummary[]> {
  const rows = await getJson<ConversationSummary[]>(`/conversations${query({ for_candidate: forCandidate })}`);
  if (rows) return rows.map((r) => ({ ...r, kind: r.kind ?? 'candidate' }));
  // Until the contract endpoint exists the older candidate-only list still answers.
  const legacy = await getJson<ConversationSummary[]>('/messages');
  return (legacy ?? []).map((r) => ({ ...r, kind: 'candidate' as const }));
}

export async function listMessages(connectionId: string, kind: ConversationKind = 'candidate'): Promise<Message[]> {
  return (
    (await getJson<Message[]>(`/messages/${connectionId}${query({ kind: kind === 'candidate' ? undefined : kind })}`)) ??
    []
  );
}

export async function sendMessage(
  connectionId: string,
  content: string,
  kind: ConversationKind = 'candidate'
): Promise<Outcome<Message>> {
  return postJson(`/messages/${connectionId}${query({ kind: kind === 'candidate' ? undefined : kind })}`, {
    content,
  });
}

/** Contract §2: either candidate opens the family conversation; the other side joins with one tap. */
export async function openFamilyConversation(connectionId: string): Promise<Outcome<{ conversation_id: string }>> {
  return postJson(`/conversations/${connectionId}/family/open`);
}

/** [DEC-V1-021] End the candidate session: everything the two wrote is deleted
 * for both. `keepalive` so the browser still sends it while the page is being
 * closed — leaving the thread is itself the end of the session. */
export async function closeConversation(connectionId: string): Promise<void> {
  try {
    await apiFetch(`${API_BASE}/messages/${connectionId}/close`, {
      method: 'POST',
      keepalive: true,
      headers: currentLanguageHeader(),
    });
  } catch {
    /* Leaving is not a moment to show an error; the next open purges anyway. */
  }
}


/** Someone the signed-in person may message one-to-one (DEC-V1-026). */
export type Contact = {
  account_id: string;
  display_name: string | null;
  photo_url: string | null;
  role: string;
  relation?: string | null;
  side_account_id?: string | null;
  side_name?: string | null;
  /** Their own family, or the other family of a connection. */
  mine: boolean;
};

export async function listContacts(): Promise<Contact[]> {
  return (await getJson<Contact[]>('/messages/direct/contacts')) ?? [];
}

export async function openDirect(accountId: string): Promise<Outcome<{ conversation_id: string }>> {
  return postJson('/messages/direct/open', { account_id: accountId });
}

/** Where a thread lives. */
export function threadHref(id: string, kind: ConversationKind): string {
  return `/messages/${id}${kind === 'candidate' ? '' : `?kind=${kind}`}`;
}
