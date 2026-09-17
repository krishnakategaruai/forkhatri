import { flushSync } from "react-dom";

type ViewTransitionLike = {
  ready: Promise<void>;
  finished: Promise<void>;
  updateCallbackDone: Promise<void>;
};

type TransitionDocument = Document & {
  startViewTransition?: (update: () => void) => ViewTransitionLike;
};

const ignore = () => {};

/**
 * Runs a React state update inside a shared-element View Transition where the
 * browser supports it, the page is visible, and the member has not asked for
 * reduced motion. Elsewhere the update simply happens.
 *
 * A transition can be skipped by the browser (hidden tab, a newer transition,
 * duplicate names mid-update); its promises then reject with InvalidStateError.
 * The state update still applies, so those rejections are expected and handled.
 */
export function withViewTransition(update: () => void) {
  const doc = document as TransitionDocument;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!doc.startViewTransition || reduced || doc.visibilityState !== "visible") {
    update();
    return;
  }
  try {
    const transition = doc.startViewTransition(() => flushSync(update));
    transition.ready.catch(ignore);
    transition.finished.catch(ignore);
    transition.updateCallbackDone.catch(ignore);
  } catch {
    update();
  }
}
