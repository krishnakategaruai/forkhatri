import { useSyncExternalStore } from "react";

/* True only in the browser, after hydration. A page whose first paint is
 * already in the member's language (read from their session in the
 * browser) renders nothing on the server, so the server's English never
 * meets the member's Telugu or Hindi in a hydration mismatch. */
const subscribe = () => () => undefined;

export function useMounted(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
