/* Shared conversation layout logic for ForKhatri modules.
 *
 * Every module that has a chat needs the same three decisions, and they are
 * the fiddly ones: which consecutive messages merge into one shaped group,
 * where a day separator belongs, and when a block earns a visible timestamp.
 * Milavn worked these out first (MOD02, chat v3, reviewed by the owner);
 * Mangaly then needed the same behaviour for a conversation with completely
 * different rules. Rather than copy the arithmetic into a second screen, it
 * lives here once.
 *
 * Deliberately NOT shared: anything a module owns. There is no React, no CSS,
 * no i18n and no network here — the modules' chats look and behave
 * differently on purpose (Milavn's is a persistent chat with presence and mood
 * avatars, Mangaly's is an ephemeral session that deletes for both people when
 * either one leaves) and this utility must never make them converge. It
 * answers "how is this list of messages shaped", and the module answers
 * everything else.
 *
 * Times are grouped in a fixed zone rather than the viewer's: both modules are
 * for people in India, and a day separator that says "Yesterday" must mean the
 * same day to both people in a conversation, whichever device they read it on.
 */

/** The fixed zone day boundaries are computed in. */
export const CHAT_TIME_ZONE = "Asia/Kolkata";

/** One person's consecutive messages closer together than this read as a
 *  single utterance and are merged into one shaped group. */
export const GROUP_GAP_MS = 10 * 60_000;

/** A longer pause than this opens a new block with a visible timestamp.
 *  Between blocks, individual messages carry no time of their own. */
export const BLOCK_BREAK_MS = 45 * 60_000;

/** The minimum a module must be able to tell us about a message. Modules keep
 *  their own richer types and supply an accessor, so neither has to rename its
 *  fields to adopt this. */
export type ChatMessageLike = {
  /** Stable id, used only for keying. */
  id: string;
  /** Who sent it. Messages merge only within one sender. */
  senderId: string;
  /** When it was sent, as an ISO 8601 string or a Date. */
  sentAt: string | Date;
  /** Optional. A message whose kind is listed in `standaloneKinds` never
   *  merges with a neighbour — a system notice or a sticker is its own thing. */
  kind?: string;
};

export type ShapeOptions = {
  /** Kinds that never merge into a group. Defaults to `['system']`. */
  standaloneKinds?: readonly string[];
  groupGapMs?: number;
  blockBreakMs?: number;
  timeZone?: string;
  /** Overridable for tests; defaults to `Date.now()`. */
  now?: number;
};

/** What a module needs in order to render one message in its list. */
export type ShapedMessage<T> = {
  message: T;
  /** True when the message above is the same person's and close in time, so
   *  this bubble's top corners should be squared off against it. */
  joinsAbove: boolean;
  /** The same, downwards. */
  joinsBelow: boolean;
  /** True when this message opens a new timestamped block. */
  startsBlock: boolean;
  /** Set only on the first message of a day: the separator to show above it. */
  daySeparator: DaySeparator | null;
};

/** A day separator, resolved to a token the module translates itself rather
 *  than to English text — these strings are user-visible and every ForKhatri
 *  surface ships in English, Hindi and Telugu. */
export type DaySeparator =
  | { kind: "today" }
  | { kind: "yesterday" }
  /** `date` is a plain YYYY-MM-DD in `CHAT_TIME_ZONE`, for the module to
   *  format in the reader's language. */
  | { kind: "date"; date: string };

function toDate(value: string | Date): Date {
  return value instanceof Date ? value : new Date(value);
}

/** YYYY-MM-DD in the fixed zone. `en-CA` is used purely because it formats as
 *  ISO; it is not a language choice and nothing user-visible comes from it. */
export function dayKey(
  value: string | Date,
  timeZone: string = CHAT_TIME_ZONE,
): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone }).format(toDate(value));
}

function separatorFor(
  key: string,
  now: number,
  timeZone: string,
): DaySeparator {
  if (key === dayKey(new Date(now), timeZone)) return { kind: "today" };
  if (key === dayKey(new Date(now - 86_400_000), timeZone))
    return { kind: "yesterday" };
  return { kind: "date", date: key };
}

/**
 * Shape a chronological list of messages for rendering.
 *
 * The input must already be sorted oldest-first; that is the order both
 * services return, and sorting here would hide a real bug in the caller.
 */
export function shapeConversation<T>(
  messages: readonly T[],
  read: (message: T) => ChatMessageLike,
  options: ShapeOptions = {},
): ShapedMessage<T>[] {
  const {
    standaloneKinds = ["system"],
    groupGapMs = GROUP_GAP_MS,
    blockBreakMs = BLOCK_BREAK_MS,
    timeZone = CHAT_TIME_ZONE,
    now = Date.now(),
  } = options;

  const rows = messages.map((message) => {
    const m = read(message);
    return {
      message,
      senderId: m.senderId,
      at: toDate(m.sentAt).getTime(),
      day: dayKey(m.sentAt, timeZone),
      standalone: m.kind !== undefined && standaloneKinds.includes(m.kind),
    };
  });

  type Row = (typeof rows)[number];
  const joins = (a: Row | undefined, b: Row | undefined) =>
    !!a &&
    !!b &&
    !a.standalone &&
    !b.standalone &&
    a.senderId === b.senderId &&
    a.day === b.day &&
    b.at - a.at < groupGapMs;

  return rows.map((row, i) => {
    const previous = rows[i - 1];
    const startsBlock =
      !previous ||
      previous.day !== row.day ||
      row.at - previous.at >= blockBreakMs;
    return {
      message: row.message,
      joinsAbove: joins(previous, row),
      joinsBelow: joins(row, rows[i + 1]),
      startsBlock,
      daySeparator:
        !previous || previous.day !== row.day
          ? separatorFor(row.day, now, timeZone)
          : null,
    };
  });
}

/** How a module says the three separator cases in the reader's language. */
export type DayLabels = {
  today: string;
  yesterday: string;
  /** Format a YYYY-MM-DD (in `CHAT_TIME_ZONE`) for an older day. */
  date: (isoDate: string) => string;
};

/**
 * Turn a separator token into text.
 *
 * Every module was about to write this same three-branch switch. The strings
 * themselves stay with the module — this only decides which one applies — so
 * nothing user-visible is frozen into shared code.
 */
export function resolveDayLabel(
  separator: DaySeparator,
  labels: DayLabels,
): string {
  if (separator.kind === "today") return labels.today;
  if (separator.kind === "yesterday") return labels.yesterday;
  return labels.date(separator.date);
}

/** A reasonable default for `DayLabels.date`: "14 Sep 2026" in the reader's
 *  language. A module with its own date conventions passes its own instead. */
export function formatDayDate(isoDate: string, language: string): string {
  return new Intl.DateTimeFormat(`${language}-IN`, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(`${isoDate}T00:00:00`));
}

/* A conversation list shows when each thread last moved. A full machine
 * timestamp ("9/14/2026, 12:29:18 AM") is precise and useless; people read
 * this column to tell "just now" from "a while ago". Only "yesterday" needs a
 * word from the module — the rest Intl can say in the reader's own language. */
export type ListTime =
  | { kind: 'time'; text: string }
  | { kind: 'yesterday' }
  | { kind: 'weekday'; text: string }
  | { kind: 'date'; text: string };

export function conversationTime(
  value: string | Date,
  language: string,
  options: { now?: number; timeZone?: string } = {}
): ListTime {
  const { now = Date.now(), timeZone = CHAT_TIME_ZONE } = options;
  const key = dayKey(value, timeZone);
  if (key === dayKey(new Date(now), timeZone)) {
    return { kind: 'time', text: clockTime(value, language, timeZone) };
  }
  if (key === dayKey(new Date(now - 86_400_000), timeZone)) return { kind: 'yesterday' };
  // Inside the last week a weekday reads faster than a date.
  if (now - toDate(value).getTime() < 7 * 86_400_000) {
    return {
      kind: 'weekday',
      text: new Intl.DateTimeFormat(`${language}-IN`, { timeZone, weekday: 'short' }).format(
        toDate(value)
      ),
    };
  }
  return {
    kind: 'date',
    text: new Intl.DateTimeFormat(`${language}-IN`, { timeZone, day: 'numeric', month: 'short' }).format(
      toDate(value)
    ),
  };
}

/** Clock time for a block heading, in the reader's language. */
export function clockTime(
  value: string | Date,
  language: string,
  timeZone: string = CHAT_TIME_ZONE,
): string {
  return new Intl.DateTimeFormat(`${language}-IN`, {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
  }).format(toDate(value));
}
