/* Resolves an AuthOutcome failure to displayable text.
 *
 * [ADR-010] `message` is already localized server-side (see `lib/auth.ts`'s
 * header comment) for anything the server actually responded to. The one
 * exception is a genuine network failure — there is no server response to
 * localize, so that single case falls back to the client's own translation.
 * Centralized here so every screen resolves an error the same way instead of
 * three near-identical ternaries drifting apart.
 */

import type { TFunction } from 'i18next';

export function authErrorText(
  result: { kind: 'rejected' | 'rateLimited' | 'network'; message?: string },
  t: TFunction,
): string {
  if (result.kind === 'network') return t('auth:error.network');
  return result.message ?? t('auth:error.invalidCredentials');
}
