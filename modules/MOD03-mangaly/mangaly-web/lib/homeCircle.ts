/* Home Circle calls against MangalyService — FR007/FR008/FR009/FR010/FR014/FR016. */

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

async function del(path: string): Promise<Outcome<null>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: currentLanguageHeader(),
    });
    if (!res.ok) return { ok: false, status: res.status };
    return { ok: true, data: null };
  } catch {
    return { ok: false, status: 0 };
  }
}

export type RelationshipType = 'parent' | 'sibling' | 'relative';

export type PendingInvitation = {
  id: string;
  candidate_account_id: string;
  inviter_account_id: string;
  relationship_type: RelationshipType;
  created_at: string;
  expires_at: string | null;
};

export type Member = {
  membership_id: string;
  member_account_id: string;
  relationship_type: RelationshipType;
  status: string;
  joined_at: string;
};

export type PendingNote = { id: string; created_at: string };

export type Note = { id: string; content: string; forwarded_at: string | null; created_at: string };

export type Suggestion = {
  id: string;
  suggested_profile_id: string;
  suggested_by_relationship_type: RelationshipType;
  note: string | null;
  created_at: string;
};

export async function invite(
  invitee_identifier: string,
  relationship_type: RelationshipType
): Promise<Outcome<{ invitation_id: string }>> {
  return postJson('/home-circle/invite', { invitee_identifier, relationship_type });
}

export async function listPendingInvitations(): Promise<PendingInvitation[]> {
  return (await getJson<PendingInvitation[]>('/home-circle/invitations/pending')) ?? [];
}

export async function acceptInvitation(id: string): Promise<Outcome<{ membership_id: string }>> {
  return postJson(`/home-circle/invitations/${id}/accept`);
}

export async function declineInvitation(id: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/invitations/${id}/decline`);
}

export async function listMembers(): Promise<Member[]> {
  return (await getJson<Member[]>('/home-circle/members')) ?? [];
}

export async function removeMember(membershipId: string): Promise<Outcome<null>> {
  return del(`/home-circle/members/${membershipId}`);
}

export async function listPendingNotes(): Promise<PendingNote[]> {
  return (await getJson<PendingNote[]>('/home-circle/notes/pending')) ?? [];
}

export async function listNotes(): Promise<Note[]> {
  return (await getJson<Note[]>('/home-circle/notes')) ?? [];
}

export async function forwardNote(noteId: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/notes/${noteId}/forward`);
}

export async function listSuggestions(): Promise<Suggestion[]> {
  return (await getJson<Suggestion[]>('/home-circle/suggestions')) ?? [];
}
