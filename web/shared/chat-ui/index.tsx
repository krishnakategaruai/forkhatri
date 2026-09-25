"use client";

/* Shared conversation structure and behaviour for ForKhatri module chats.
 *
 * The layer above `@forkhatri/chat-core`. Where that package answers "how is
 * this list of messages shaped", this one owns the two things every chat
 * screen then has to build the same way and repeatedly gets subtly wrong: the
 * scrolling message area (separator placement, grouping classes, staying
 * pinned to the latest message) and the composer's behaviour (trimming,
 * when send is allowed, Enter versus newline, not sending twice).
 *
 * The rule this package is built to: SHARE STRUCTURE AND BEHAVIOUR, NEVER
 * APPEARANCE OR VOCABULARY. Nothing here renders a bubble, picks a colour or
 * contains a user-visible string. Modules pass their own class names and
 * their own labels, and render each message themselves through a child
 * function, so Milavn's chat (persistent, with presence, mood avatars and
 * reactions) and Mangaly's (an ephemeral session that deletes for both people
 * when either one leaves) stay as different as they are meant to be.
 *
 * Scope, by an explicit owner decision on 2026-09-21: the modules where
 * people connect with people — MOD02 Milavn and MOD03 Mangaly. MOD01 Vyapar
 * is NOT in scope. Its enquiry thread looks similar in the database but is a
 * transaction about an opportunity, with its own lifecycle and a
 * provider/sender asymmetry, not two people getting to know each other.
 */

import {
  resolveDayLabel,
  shapeConversation,
  type ChatMessageLike,
  type DayLabels,
  type ShapedMessage,
  type ShapeOptions,
} from "@forkhatri/chat-core";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

/* ------------------------------------------------------------------ *
 * Grouping class names
 * ------------------------------------------------------------------ */

export type GroupClassNames = {
  /** Always applied. */
  base: string;
  /** Applied when the message is the reader's own. */
  mine?: string;
  /** Applied when this message merges with the one above. */
  joinedAbove?: string;
  /** Applied when this message merges with the one below. */
  joinedBelow?: string;
};

/**
 * Build the class list for one message.
 *
 * The module owns every class name; this only decides which of them apply,
 * so the "is this bubble squared off against its neighbour" logic is not
 * re-derived per screen.
 */
export function bubbleClassName(
  shaped: Pick<ShapedMessage<unknown>, "joinsAbove" | "joinsBelow">,
  options: GroupClassNames & { mine?: string; isMine?: boolean },
): string {
  return [
    options.base,
    options.isMine ? options.mine : undefined,
    shaped.joinsAbove ? options.joinedAbove : undefined,
    shaped.joinsBelow ? options.joinedBelow : undefined,
  ]
    .filter(Boolean)
    .join(" ");
}

/* ------------------------------------------------------------------ *
 * ThreadBody
 * ------------------------------------------------------------------ */

export type ThreadBodyProps<T> = {
  /** Oldest first — the order both services already return. */
  messages: readonly T[];
  /** Map the module's own message type onto the minimum shape. */
  read: (message: T) => ChatMessageLike;
  /** The module's words for "Today", "Yesterday" and an older date. */
  dayLabels: DayLabels;
  /** Renders one message. Receives the shaping flags for that message. */
  children: (shaped: ShapedMessage<T>) => ReactNode;
  className?: string;
  /** Class for the day separator element. */
  dayClassName?: string;
  shapeOptions?: ShapeOptions;
  /** Pin to the newest message as it arrives. Default true. A reader who has
   *  scrolled up is left alone — yanking them back down mid-read is the most
   *  common bug in a hand-rolled chat list. */
  followLatest?: boolean;
};

const NEAR_BOTTOM_PX = 120;

export function ThreadBody<T>({
  messages,
  read,
  dayLabels,
  children,
  className,
  dayClassName,
  shapeOptions,
  followLatest = true,
}: ThreadBodyProps<T>) {
  const scroller = useRef<HTMLDivElement | null>(null);
  const pinned = useRef(true);

  const onScroll = useCallback(() => {
    const el = scroller.current;
    if (!el) return;
    pinned.current =
      el.scrollHeight - el.scrollTop - el.clientHeight <= NEAR_BOTTOM_PX;
  }, []);

  useEffect(() => {
    if (!followLatest) return;
    const el = scroller.current;
    // Only follow when the reader was already at the bottom; someone reading
    // back through the conversation keeps their place.
    if (el && pinned.current) el.scrollTop = el.scrollHeight;
  }, [messages, followLatest]);

  const rows = shapeConversation(messages, read, shapeOptions);

  return (
    <div className={className} ref={scroller} onScroll={onScroll}>
      {rows.map((shaped) => (
        <Row
          key={read(shaped.message).id}
          shaped={shaped}
          dayLabels={dayLabels}
          dayClassName={dayClassName}
        >
          {children}
        </Row>
      ))}
    </div>
  );
}

function Row<T>({
  shaped,
  dayLabels,
  dayClassName,
  children,
}: {
  shaped: ShapedMessage<T>;
  dayLabels: DayLabels;
  dayClassName?: string;
  children: (shaped: ShapedMessage<T>) => ReactNode;
}) {
  return (
    <>
      {shaped.daySeparator && (
        <span className={dayClassName}>
          {resolveDayLabel(shaped.daySeparator, dayLabels)}
        </span>
      )}
      {children(shaped)}
    </>
  );
}

/* ------------------------------------------------------------------ *
 * useComposer
 * ------------------------------------------------------------------ */

export type UseComposerOptions = {
  /** Send the message. Resolve to send; throw to keep the text for a retry. */
  onSend: (text: string) => Promise<void> | void;
  /** Blocks sending regardless of the text (a closed or restricted thread). */
  disabled?: boolean;
  /** Enter sends and Shift+Enter makes a newline. Default true. */
  sendOnEnter?: boolean;
  maxLength?: number;
};

export type Composer = {
  value: string;
  setValue: (next: string) => void;
  /** True when there is something to send and nothing in flight. */
  canSend: boolean;
  sending: boolean;
  /** Set when the last attempt threw; cleared on the next edit or attempt. */
  failed: boolean;
  /** For a <form onSubmit>. */
  submit: (event?: FormEvent) => void;
  /** For a textarea's onKeyDown. */
  onKeyDown: (event: KeyboardEvent) => void;
};

/**
 * The composer's behaviour, without its appearance.
 *
 * Holds the rules a hand-rolled composer tends to miss: whitespace-only text
 * is not a message, the text survives a failed send so nothing a person wrote
 * is lost, and a second send cannot start while the first is in flight (which
 * is how duplicate messages appear).
 */
export function useComposer({
  onSend,
  disabled = false,
  sendOnEnter = true,
  maxLength,
}: UseComposerOptions): Composer {
  const [value, setRawValue] = useState("");
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState(false);

  const setValue = useCallback((next: string) => {
    setRawValue(maxLength ? next.slice(0, maxLength) : next);
    setFailed(false);
    // `maxLength` is a prop that does not change in practice; reading it here
    // rather than in a dependency keeps the callback stable for the input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const trimmed = value.trim();
  const canSend = !disabled && !sending && trimmed.length > 0;

  const submit = useCallback(
    (event?: FormEvent) => {
      event?.preventDefault();
      if (!canSend) return;
      setSending(true);
      setFailed(false);
      void (async () => {
        try {
          await onSend(trimmed);
          setRawValue("");
        } catch {
          // Keep the text: the person can try again without retyping it.
          setFailed(true);
        } finally {
          setSending(false);
        }
      })();
    },
    [canSend, onSend, trimmed],
  );

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!sendOnEnter) return;
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submit();
      }
    },
    [sendOnEnter, submit],
  );

  return { value, setValue, canSend, sending, failed, submit, onKeyDown };
}
