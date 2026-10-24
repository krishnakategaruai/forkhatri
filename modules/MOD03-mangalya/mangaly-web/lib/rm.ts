/* Assisted matching — the relationship manager (DEC-V1-032).
 *
 * Member seat: `/rm/me` (my RM, their suggestions, the calls they logged) and
 * a decision on a suggestion. RM seat: the console calls under
 * `/rm/assignments`, answered only for an account that is an RM. */

import { getJson, postJson, query, type Outcome } from './api';

export type Rm = {
  account_id: string;
  display_name: string;
  languages: string[];
  region: string | null;
  photo_url: string | null;
};

export type SuggestedPerson = {
  candidate_account_id: string;
  photo_url: string | null;
  age: number | null;
  locality: string | null;
  education_level: string | null;
  profession: string | null;
  open_name: string | null;
  open_photo_urls: string[];
};

export type RmSuggestion = {
  id: string;
  assignment_id: string;
  suggested_account_id: string;
  note: string | null;
  created_at: string;
  member_decision: 'liked' | 'passed' | null;
  decided_at: string | null;
  person: SuggestedPerson | null;
};

export type RmInteraction = {
  id: string;
  kind: 'call' | 'meeting' | 'note';
  scheduled_at: string | null;
  summary: string | null;
  created_at: string;
};

export type RmAssignment = {
  id: string;
  rm_account_id: string;
  member_account_id: string;
  member_name: string | null;
  member_photo_url: string | null;
  status: 'active' | 'ended';
  assigned_at: string;
  ended_at: string | null;
  note: string | null;
};

export type MyRm = {
  assignment: RmAssignment;
  rm: Rm;
  suggestions: RmSuggestion[];
  interactions: RmInteraction[];
};

export type FamilyMember = {
  account_id: string;
  display_name: string | null;
  relationship_type: string;
  relation: string | null;
};

export type MemberSummary = {
  name: string;
  age: number | null;
  city: string | null;
  gender: string | null;
  looking_for: 'bride' | 'groom' | null;
  mother_tongue: string | null;
  education_level: string | null;
  profession: string | null;
  partner_preference: Record<string, unknown>;
  family_involvement: Record<string, unknown>;
  language_preference: string;
  family: FamilyMember[];
};

export type AssignmentDetail = {
  assignment: RmAssignment;
  member: MemberSummary | null;
  suggestions: RmSuggestion[];
  interactions: RmInteraction[];
};

export type RmSearchResult = SuggestedPerson & {
  score: number;
  height_cm: number | null;
  marital_status: string | null;
  mother_tongue: string | null;
  already_suggested: boolean;
};

export type RmSearchPage = {
  results: RmSearchResult[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
};

export type RmSearchParams = {
  q?: string;
  age_min?: number;
  age_max?: number;
  city?: string;
  nearby?: 'city' | 'state';
  sort?: 'relevance' | 'newest' | 'recently_active';
  page?: number;
};

/* ---------- member seat ---------- */

export function getMyRm(forCandidate?: string): Promise<MyRm | null> {
  return getJson<MyRm>(`/rm/me${query({ for_candidate: forCandidate })}`);
}

export async function isRelationshipManager(): Promise<boolean> {
  const r = await getJson<{ is_rm: boolean }>('/rm/me/role');
  return !!r?.is_rm;
}

export function decideSuggestion(
  suggestionId: string,
  decision: 'liked' | 'passed',
  forCandidate?: string,
): Promise<Outcome<RmSuggestion>> {
  return postJson<RmSuggestion>(`/rm/suggestions/${suggestionId}/decision`, {
    decision,
    for_candidate: forCandidate,
  });
}

/* ---------- RM seat ---------- */

export function listAssignments(): Promise<RmAssignment[] | null> {
  return getJson<RmAssignment[]>('/rm/assignments');
}

export function getAssignment(assignmentId: string): Promise<AssignmentDetail | null> {
  return getJson<AssignmentDetail>(`/rm/assignments/${assignmentId}`);
}

export function searchForMember(assignmentId: string, params: RmSearchParams): Promise<RmSearchPage | null> {
  return getJson<RmSearchPage>(`/rm/assignments/${assignmentId}/search${query({ ...params, page_size: 24 })}`);
}

export function suggestToMember(
  assignmentId: string,
  suggestedAccountId: string,
  note: string,
): Promise<Outcome<RmSuggestion>> {
  return postJson<RmSuggestion>(`/rm/assignments/${assignmentId}/suggestions`, {
    suggested_account_id: suggestedAccountId,
    note: note || null,
  });
}

export function addInteraction(
  assignmentId: string,
  body: { kind: RmInteraction['kind']; scheduled_at?: string | null; summary?: string | null },
): Promise<Outcome<RmInteraction>> {
  return postJson<RmInteraction>(`/rm/assignments/${assignmentId}/interactions`, body);
}

export function endAssignment(assignmentId: string): Promise<Outcome<RmAssignment>> {
  return postJson<RmAssignment>(`/rm/assignments/${assignmentId}/end`);
}

export function assignMember(memberAccountId: string, note: string): Promise<Outcome<RmAssignment>> {
  return postJson<RmAssignment>('/rm/assign', { member_account_id: memberAccountId, note: note || null });
}

/* ---------- formatting ---------- */

const LOCALE: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', te: 'te-IN', mr: 'mr-IN', kn: 'kn-IN' };

/** "23 Sept, 6:30 pm" in the reader's language, Indian order. */
export function formatWhen(iso: string | null | undefined, language: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(LOCALE[language] ?? 'en-IN', {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function formatDay(iso: string | null | undefined, language: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString(LOCALE[language] ?? 'en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}
