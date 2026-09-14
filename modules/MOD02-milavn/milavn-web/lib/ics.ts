/* "Show up" (thesis §67): one tap puts the activity into the phone's own
 * calendar. A minimal RFC 5545 VEVENT, opened as a data URL so it works with
 * no server round-trip; the in-app Calendar (FR024) stays the community view. */

const CRLF = String.fromCharCode(13, 10);

function stamp(d: Date): string {
  return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
}

function escapeText(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
}

export function buildIcs(opts: { uid: string; title: string; start: string; durationMinutes?: number; location?: string; description?: string; url?: string }): string {
  const start = new Date(opts.start);
  const end = new Date(start.getTime() + (opts.durationMinutes ?? 120) * 60 * 1000);
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//ForKhatri//Milavn//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${opts.uid}@milavn.forkhatri`,
    `DTSTAMP:${stamp(new Date())}`,
    `DTSTART:${stamp(start)}`,
    `DTEND:${stamp(end)}`,
    `SUMMARY:${escapeText(opts.title)}`,
    opts.location ? `LOCATION:${escapeText(opts.location)}` : '',
    opts.description ? `DESCRIPTION:${escapeText(opts.description)}` : '',
    opts.url ? `URL:${opts.url}` : '',
    'END:VEVENT',
    'END:VCALENDAR',
  ].filter(Boolean);
  return lines.join(CRLF) + CRLF;
}

export function icsDataUrl(ics: string): string {
  return `data:text/calendar;charset=utf-8,${encodeURIComponent(ics)}`;
}
