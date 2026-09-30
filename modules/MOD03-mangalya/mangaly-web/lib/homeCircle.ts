/* Home Circle calls against MangalyService — FR007/FR008/FR009/FR010/FR014/FR016.
 *
 * [2026-09-17 rework, contract §3/§6] Invite is available to every signed-in
 * account, in every context: a candidate invites family, a family member
 * invites a relative (or a candidate, by phone), and an account with no
 * context at all can start a circle by inviting someone. People are found
 * through `GET /home-circle/people?q=` (ForKhatri members by name or phone).
 * Relationship vocabulary now includes `guardian`. */

import { deleteJson, getJson, postJson, query, sendJson, type Outcome } from './api';
import type { LookingFor, Relationship } from './auth';

export type { Outcome };
export type RelationshipType = Relationship;

export const RELATIONSHIPS: RelationshipType[] = ['parent', 'guardian', 'sibling', 'relative'];

/* [Migration 040] Two levels, as the owner described them: the ROLE
 * (parent / guardian / sibling / relative — it groups the circle into Home and
 * Relatives and is what permissions read) and, inside it, the EXACT relation of
 * the member to the candidate — what the family actually calls each other. */
export type Relation =
  | 'mother' | 'father' | 'brother' | 'sister' | 'guardian'
  | 'grandmother' | 'grandfather'
  | 'paternal_uncle' | 'maternal_uncle' | 'paternal_aunt' | 'maternal_aunt'
  | 'cousin' | 'brother_in_law' | 'sister_in_law' | 'family_friend';

export const HOME_RELATIONS: Relation[] = ['mother', 'father', 'brother', 'sister', 'guardian'];
export const RELATIVE_RELATIONS: Relation[] = [
  'grandmother', 'grandfather',
  'paternal_uncle', 'maternal_uncle', 'paternal_aunt', 'maternal_aunt',
  'cousin', 'brother_in_law', 'sister_in_law', 'family_friend',
];

export const RELATION_ROLE: Record<Relation, RelationshipType> = {
  mother: 'parent', father: 'parent', guardian: 'guardian',
  brother: 'sibling', sister: 'sibling',
  grandmother: 'relative', grandfather: 'relative',
  paternal_uncle: 'relative', maternal_uncle: 'relative',
  paternal_aunt: 'relative', maternal_aunt: 'relative',
  cousin: 'relative', brother_in_law: 'relative', sister_in_law: 'relative',
  family_friend: 'relative',
};

/** The words for someone's place in a circle: the exact relation when stated,
 *  else the role (rows from before migration 040 recorded only a role). */
export function relationKey(relation: string | null | undefined, role: string): string {
  return relation ? `circle:relation.${relation}` : `circle:invite.relationshipOption.${role}`;
}

/** Who asked what, in words — one wording for Circle and Home. `to_candidate`:
 *  someone asks to join YOUR circle. `to_member`: you are asked into a
 *  candidate's circle, by the candidate or by someone already helping them. */
export function invitationText(
  t: (key: string, options?: Record<string, unknown>) => string,
  inv: PendingInvitation,
): string {
  const relationship = t(relationKey(inv.relation, inv.relationship_type)).toLowerCase();
  const name = inv.inviter_name ?? t('circle:pendingInvitations.someone');
  if (inv.direction === 'to_candidate') {
    return t('circle:pendingInvitations.asksToJoin', { name, relationship });
  }
  if (inv.candidate_name && inv.inviter_account_id !== inv.candidate_account_id) {
    return t('circle:pendingInvitations.addsYouTo', {
      name,
      candidate: inv.candidate_name,
      first: inv.candidate_name.split(' ')[0],
      relationship,
    });
  }
  return t('circle:pendingInvitations.invitesYou', { name, relationship });
}

export type PendingInvitation = {
  id: string;
  candidate_account_id: string;
  candidate_profile_id?: string;
  candidate_name?: string | null;
  inviter_account_id: string;
  inviter_name?: string | null;
  relationship_type: RelationshipType;
  relation?: Relation | null;
  created_at: string;
  expires_at: string | null;
  /** `to_member`: you are invited into the candidate's circle.
   *  `to_candidate`: the inviter asks to join YOUR circle (you are the candidate). */
  direction?: 'to_member' | 'to_candidate';
};

export type Member = {
  membership_id: string;
  member_account_id: string;
  relationship_type: RelationshipType;
  relation?: Relation | null;
  status: string;
  joined_at: string;
  member_name?: string | null;
  member_photo_url?: string | null;
};

export type Suggestion = {
  id: string;
  suggested_profile_id: string;
  suggested_by_relationship_type: RelationshipType;
  suggested_by_name?: string | null;
  /** True when the reader made this suggestion themselves. */
  suggested_by_is_you?: boolean;
  suggested_by_relation?: string | null;
  note: string | null;
  created_at: string;
};

/** Contract §6: a ForKhatri member found by name or phone. */
export type Person = {
  account_id: string;
  display_name: string;
  phone_masked: string | null;
  has_profile: boolean;
};

export async function searchPeople(q: string): Promise<Person[]> {
  if (!q.trim()) return [];
  return (await getJson<Person[]>(`/home-circle/people${query({ q: q.trim() })}`)) ?? [];
}

export type InviteInput = {
  /** A found person's account id (preferred) … */
  invitee_account_id?: string;
  /** … or a raw phone/email when they are not on ForKhatri yet. */
  invitee_identifier?: string;
  relationship_type: RelationshipType;
  /** [Migration 040] The exact relation; the server derives the role from it. */
  relation?: Relation;
  /** Whose circle: omitted ⇒ the caller's own. */
  for_candidate?: string;
  /** `to_candidate`: ask the invitee (a candidate) to let the caller join their circle. */
  direction?: 'to_member' | 'to_candidate';
};

export async function invite(input: InviteInput): Promise<Outcome<{ invitation_id: string }>> {
  return postJson('/home-circle/invite', input);
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

/* The contexts this account can act in: their own candidate profile (if they
 * have one) and every circle they belong to. A parent or relative with no
 * profile of their own still has circles here, which is how the Home and
 * Profile screens tell "start the wizard" apart from "go to your circle".
 * Each context carries `looking_for` because that answer always constrains
 * discovery for the candidate being acted for. */

export type OwnProfileContext = {
  account_id: string;
  name: string;
  looking_for: LookingFor | null;
};

export type CircleContext = {
  membership_id: string;
  candidate_account_id: string;
  candidate_name: string;
  relationship_type: RelationshipType;
  relation?: Relation | null;
  joined_at: string;
  looking_for: LookingFor | null;
};

export type Contexts = {
  own_profile: OwnProfileContext | null;
  circles: CircleContext[];
};

export async function getContexts(): Promise<Contexts | null> {
  return await getJson<Contexts>('/home-circle/contexts');
}

/** Members of a candidate's circle; omitted ⇒ the caller's own. */
export async function listMembers(forCandidate?: string): Promise<Member[]> {
  return (await getJson<Member[]>(`/home-circle/members${query({ for_candidate: forCandidate })}`)) ?? [];
}

/** FR010 — the candidate removes a member. */
/** [Migration 040] The candidate, or the member themselves, states the exact relation. */
export async function setMemberRelation(membershipId: string, relation: Relation): Promise<Outcome<null>> {
  return sendJson('PATCH', `/home-circle/members/${membershipId}/relation`, { relation });
}

export async function removeMember(membershipId: string): Promise<Outcome<null>> {
  return deleteJson(`/home-circle/members/${membershipId}`);
}

/** FR010 — a member leaves a circle themselves. */
export async function leaveCircle(membershipId: string): Promise<Outcome<null>> {
  return postJson(`/home-circle/members/${membershipId}/leave`);
}

export async function listSuggestions(forCandidate?: string): Promise<Suggestion[]> {
  return (
    (await getJson<Suggestion[]>(`/home-circle/suggestions${query({ for_candidate: forCandidate })}`)) ?? []
  );
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

/* Notes and suggestions are addressed by the caller's MEMBERSHIP (which
 * circle they write in), the API's `membership_id`. Every caller already
 * passes `family.membership_id`; it used to go out as `for_candidate`, which
 * the API does not read, so both features failed for every family member. */
export async function listMyNotes(membershipId: string, subjectAccountId: string): Promise<FamilyNote[]> {
  return (
    (await getJson<FamilyNote[]>(
      `/home-circle/notes${query({ membership_id: membershipId, subject_account_id: subjectAccountId })}`
    )) ?? []
  );
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
  return deleteJson(`/home-circle/notes/${noteId}`);
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

/* FR014 — a family member suggests a profile to the candidate they help. */

export async function suggestProfile(
  membershipId: string,
  profileId: string,
  note?: string
): Promise<Outcome<{ suggestion_id: string }>> {
  return postJson('/home-circle/suggest', {
    membership_id: membershipId,
    suggested_profile_id: profileId,
    note: note ?? null,
  });
}
