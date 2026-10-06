/* [054] Event formats (separate from the category) and online meeting providers. Labels live in the locale files
 * under evt.format.* and evt.provider.*; the API is the authority on which values are allowed. */

export const EVENT_FORMATS = [
  'workshop', 'webinar', 'talk', 'panel', 'masterclass', 'book_club', 'skill_share', 'office_hours', 'bootcamp', 'conference',
  'expo', 'cultural_night', 'tournament', 'festival', 'satsang', 'darshan_stream', 'town_hall', 'volunteering', 'trip', 'meetup',
] as const;
export type EventFormat = (typeof EVENT_FORMATS)[number];

// Formats that often run over several days: the create form offers "how many days" for these straight away.
export const MULTI_DAY_FORMATS: readonly string[] = ['bootcamp', 'conference', 'expo', 'festival', 'tournament', 'trip'];
// Formats that usually happen online: the create form suggests the online mode for these.
export const ONLINE_FORMATS: readonly string[] = ['webinar', 'darshan_stream', 'office_hours'];

export type Provider = 'google_meet' | 'zoom' | 'teams' | 'youtube' | 'other';

/* Whole calendar days an event spans in India time (1 for a same-day event). */
export function daySpan(startIso: string, endIso: string | null | undefined): number {
  if (!endIso) return 1;
  const day = (iso: string) => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(iso));
  const a = Date.parse(`${day(startIso)}T00:00:00Z`);
  const b = Date.parse(`${day(endIso)}T00:00:00Z`);
  return Math.max(1, Math.round((b - a) / 86_400_000) + 1);
}

/* Which day of the event (1-based) a moment falls on, India time. */
export function dayNumber(startIso: string, atIso: string): number {
  return daySpan(startIso, atIso);
}
