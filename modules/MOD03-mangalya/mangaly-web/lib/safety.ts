/* Trust & safety — contract §3. Block hides a profile from both sides'
 * discovery and lists; report sends a reason to moderation. Both sit behind a
 * quiet "…" menu on every profile, never a loud button. */

import { deleteJson, postJson, type Outcome } from './api';

export const REPORT_REASONS = [
  'harassment',
  'fake_profile',
  'inappropriate_content',
  'scam_or_money',
  'already_married',
  'underage',
  'other',
] as const;
export type ReportReason = (typeof REPORT_REASONS)[number];

export async function block(profileId: string): Promise<Outcome<null>> {
  return postJson(`/safety/block/${profileId}`);
}

export async function unblock(profileId: string): Promise<Outcome<null>> {
  return deleteJson(`/safety/block/${profileId}`);
}

export async function report(profileId: string, reason: ReportReason, details: string): Promise<Outcome<null>> {
  return postJson('/safety/report', { profile_id: profileId, reason, details });
}
