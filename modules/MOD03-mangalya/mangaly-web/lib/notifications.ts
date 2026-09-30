/* Notifications — contract §3. Context-scoped like everything else: a parent
 * sees Ananya's request activity in Ananya's context, their own invitations
 * in every context. `link` is a Mangalya path the row opens. */

import { getJson, postJson, query, type Outcome } from './api';

export type NotificationKind =
  | 'request_received'
  | 'request_accepted'
  | 'invitation_received'
  | 'invitation_accepted'
  | 'suggestion_received'
  | 'family_conversation_opened'
  | 'note_forwarded';

export type Notification = {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string | null;
  link: string | null;
  created_at: string;
  read_at: string | null;
};

export async function listNotifications(forCandidate?: string): Promise<Notification[]> {
  return (await getJson<Notification[]>(`/notifications${query({ for_candidate: forCandidate })}`)) ?? [];
}

/** Marks the given ids read; with no ids, everything. */
export async function markRead(ids?: string[]): Promise<Outcome<null>> {
  return postJson('/notifications/read', ids && ids.length ? { ids } : { all: true });
}
