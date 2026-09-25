/* Connection calls against MangalyService — FR042/FR043/FR044/FR045.
 *
 * [2026-09-17 rework, contract §2/§3] Incoming and sent lists are context
 * scoped (`?for_candidate=`), a family member may send on behalf of their
 * candidate (`on_behalf_of_profile_id`; reverses DEC-V1-019 by owner
 * instruction), and a pending request can be withdrawn. */

import { getJson, postJson, query, sendJson, type Outcome } from './api';

export type ConnectionStatus = 'pending' | 'accepted' | 'declined' | 'withdrawn';

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
  /** "Sent by Ananya's mother" — the server's own phrasing when a family member sent it. */
  sent_by_label?: string | null;
  /** Who sent it when it was not the candidate themself (contract §2). */
  sent_by?: { relationship: string; display_name: string | null; candidate_name: string | null } | null;
  subject_name?: string | null;
  /** Pre-connection-safe card of the requesting candidate (incoming only). */
  subject?: {
    locality?: string | null;
    education_level?: string | null;
    profession?: string | null;
    photo_url?: string | null;
    age?: number | null;
    /** Their first name, only when they chose to show it openly. */
    open_name?: string | null;
  } | null;
  /** Lightweight card of the other party, when the server includes it. */
  other?: {
    profile_id?: string;
    account_id?: string;
    name?: string | null;
    age?: number | null;
    locality?: string | null;
    photo_url?: string | null;
    education_level?: string | null;
    profession?: string | null;
  } | null;
};

export async function sendRequest(
  targetId: string,
  onBehalfOfProfileId?: string
): Promise<Outcome<Connection>> {
  return postJson('/connections', {
    target_account_id: targetId,
    ...(onBehalfOfProfileId ? { on_behalf_of_profile_id: onBehalfOfProfileId } : {}),
  });
}

export async function listIncoming(forCandidate?: string): Promise<Connection[]> {
  return (await getJson<Connection[]>(`/connections/incoming${query({ for_candidate: forCandidate })}`)) ?? [];
}

export async function listSent(forCandidate?: string): Promise<Connection[]> {
  return (await getJson<Connection[]>(`/connections/sent${query({ for_candidate: forCandidate })}`)) ?? [];
}

export async function getConnection(connectionId: string): Promise<Connection | null> {
  return await getJson<Connection>(`/connections/${connectionId}`);
}

/* The candidate, or their mother, father or guardian answering for them
 * (`forCandidate`). The server refuses anyone else in the circle. */
export async function accept(connectionId: string, forCandidate?: string): Promise<Outcome<null>> {
  return postJson(`/connections/${connectionId}/accept${query({ for_candidate: forCandidate })}`);
}

export async function decline(connectionId: string, forCandidate?: string): Promise<Outcome<null>> {
  return postJson(`/connections/${connectionId}/decline${query({ for_candidate: forCandidate })}`);
}

export async function withdraw(connectionId: string): Promise<Outcome<null>> {
  return postJson(`/connections/${connectionId}/withdraw`);
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
