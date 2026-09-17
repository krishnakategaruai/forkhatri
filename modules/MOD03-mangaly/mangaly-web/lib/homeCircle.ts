/* Home Circle calls against MangalyService — FR007/FR008/FR009/FR010/FR014/FR016. */

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

export type Outcome<T> = { ok: true; data: T } | { ok: false; status: number; message?: string };

async function sendJson<T>(method: 'POST' | 'PATCH', path: string, body?: unknown): Promise<Outcome<T>> {
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

function postJson<T>(path: string, body?: unknown): Promise<Outcome<T>> {
  return sendJson<T>('POST', path, body);
}

async function del(path: string): Promise<Outcome<null>> {
  try {
    const res = await apiFetch(`${API_BASE}${path}`, {
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
  member_name?: string | null;
};

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

/* `candidateAccountId` reads the circle of a candidate the signed-in member
 * helps, rather than their own — what the parent-role Circle screen shows. */
export async function listMembers(candidateAccountId?: string): Promise<Member[]> {
  const query = candidateAccountId
    ? `?candidate_account_id=${encodeURIComponent(candidateAccountId)}`
    : '';
  return (await getJson<Member[]>(`/home-circle/members${query}`)) ?? [];
}

export async function removeMember(membershipId: string): Promise<Outcome<null>> {
  return del(`/home-circle/members/${membershipId}`);
}

export async function listSuggestions(candidateAccountId?: string): Promise<Suggestion[]> {
  const query = candidateAccountId
    ? `?candidate_account_id=${encodeURIComponent(candidateAccountId)}`
    : '';
  return (await getJson<Suggestion[]>(`/home-circle/suggestions${query}`)) ?? [];
}

/* FR016 — private notes about a match. The author keeps and edits their own
 * notes and may ask the candidate to read one; the candidate sees who asks and
 * which match, and reads the words only by choosing to. */

export type NoteStatus = 'private' | 'requested' | 'shared' | 'declined';

export type FamilyNote = {
  id: string;
  subject_account_id: string;
  content: string;
  status: NoteStatus;
  created_at: string;
  updated_at: string;
};

export type NoteReadRequest = {
  id: string;
  author_name: string | null;
  relationship_type: RelationshipType;
  subject_account_id: string;
  requested_at: string;
};

export type SharedNote = {
  id: string;
  content: string;
  author_name: string | null;
  relationship_type: RelationshipType;
  subject_account_id: string;
  forwarded_at: string;
};

export async function listMyNotes(membershipId: string, subjectAccountId: string): Promise<FamilyNote[]> {
  const query = new URLSearchParams({ membership_id: membershipId, subject_account_id: subjectAccountId });
  return (await getJson<FamilyNote[]>(`/home-circle/notes?${query.toString()}`)) ?? [];
}

export async function addNote(
  membershipId: string,
  subjectAccountId: string,
  content: string
): Promise<Outcome<FamilyNote>> {
  return postJson('/home-circle/notes', {
    membership_id: membershipId,
    subject_account_id: subjectAccountId,
    content,
  });
}

export async function editNote(noteId: string, content: string): Promise<Outcome<FamilyNote>> {
  return sendJson('PATCH', `/home-circle/notes/${noteId}`, { content });
}

export async function deleteNote(noteId: string): Promise<Outcome<null>> {
  return del(`/home-circle/notes/${noteId}`);
}

export async function askToReadNote(noteId: string): Promise<Outcome<FamilyNote>> {
  return postJson(`/home-circle/notes/${noteId}/request`);
}

export async function listNoteRequests(): Promise<NoteReadRequest[]> {
  return (await getJson<NoteReadRequest[]>('/home-circle/notes/requests')) ?? [];
}

export async function readNote(noteId: string): Promise<Outcome<{ content: string }>> {
  return postJson(`/home-circle/notes/${noteId}/read`);
}

export async function declineNote(noteId: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/notes/${noteId}/decline`);
}

export async function listSharedNotes(): Promise<SharedNote[]> {
  return (await getJson<SharedNote[]>('/home-circle/notes/shared')) ?? [];
}

/* FR048 — requests to share this member's own phone with a candidate's match. */

export type ContactRequest = {
  id: string;
  candidate_account_id: string;
  candidate_name: string | null;
  relationship_type: RelationshipType | null;
  requested_at: string;
};

export async function listContactRequests(): Promise<ContactRequest[]> {
  return (await getJson<ContactRequest[]>('/home-circle/contact-requests')) ?? [];
}

export async function approveContactRequest(id: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/contact-requests/${id}/approve`);
}

export async function declineContactRequest(id: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/contact-requests/${id}/decline`);
}

/* FR097 — every search the member can act in. */

export type LookingFor = 'bride' | 'groom';

export type CircleContext = {
  membership_id: string;
  candidate_account_id: string;
  candidate_name: string;
  relationship_type: RelationshipType;
  joined_at: string;
  /* Whose side of the match this context searches on — always the CANDIDATE's
   * answer, never the family member's. Null until they have answered, or while
   * their profile is paused. */
  looking_for: LookingFor | null;
};

export type Contexts = {
  own_profile: { account_id: string; name: string; looking_for: LookingFor | null } | null;
  circles: CircleContext[];
};

export async function getContexts(): Promise<Contexts | null> {
  return await getJson<Contexts>('/home-circle/contexts');
}

/* FR014 — a family member suggests a profile to the candidate they help. */

export async function suggestProfile(
  membershipId: string,
  profileAccountId: string,
  note?: string
): Promise<Outcome<{ suggestion_id: string }>> {
  return postJson('/home-circle/suggest', {
    membership_id: membershipId,
    suggested_profile_id: profileAccountId,
    note: note ?? null,
  });
}
