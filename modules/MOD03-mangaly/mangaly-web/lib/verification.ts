/* Face-match verification calls — DEC-V1-016 / DEC-V1-025.
 *
 * Only the OUTCOME of the in-browser comparison is ever sent: one distance
 * number, whether the liveness challenge passed, and how many photos were
 * compared. The server applies the threshold; nothing it returns contains a
 * score, and nothing on screen shows one. */

import { getJson, postJson } from './api';

export type VerificationStatus = {
  verified: boolean;
  verified_at: string | null;
  expires_at: string | null;
  consent_given: boolean;
  has_profile: boolean;
  has_photos: boolean;
};

export function getVerification(): Promise<VerificationStatus | null> {
  return getJson<VerificationStatus>('/verification/me');
}

export type FaceMatchResult =
  | { ok: true; passed: boolean; verified_at: string | null }
  | { ok: false; kind: 'rateLimited' | 'noPhotos' | 'network'; message?: string };

export async function submitFaceMatch(input: {
  distance: number;
  livenessPassed: boolean;
  photosCompared: number;
}): Promise<FaceMatchResult> {
  const res = await postJson<{ passed: boolean; verified_at: string | null }>(
    '/verification/face-match',
    {
      consent: true,
      distance: input.distance,
      liveness_passed: input.livenessPassed,
      photos_compared: input.photosCompared,
    },
  );
  if (res.ok) return { ok: true, passed: res.data.passed, verified_at: res.data.verified_at };
  if (res.status === 429) return { ok: false, kind: 'rateLimited' };
  if (res.status === 409) return { ok: false, kind: 'noPhotos' };
  return { ok: false, kind: 'network' };
}

export async function withdrawFaceMatch(): Promise<boolean> {
  return (await postJson<null>('/verification/withdraw')).ok;
}

/** "Sep 2026" in the reader's language — the provenance DEC-V1-016 shows. */
export function monthYear(iso: string | null, lang: string): string {
  if (!iso) return '';
  const locale = lang === 'hi' ? 'hi-IN' : lang === 'te' ? 'te-IN' : 'en-IN';
  return new Intl.DateTimeFormat(locale, { month: 'short', year: 'numeric' }).format(new Date(iso));
}

/** Only same-site paths are accepted as a place to return to. */
export function safeNext(value: string | null): string | null {
  if (!value || !value.startsWith('/') || value.startsWith('//')) return null;
  return value;
}
