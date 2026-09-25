/**
 * ForKhatri's own devotional emblem of Bhagwan Kartavirya Sahasrarjun, shown beside the
 * greeting on the signed-in hub.
 *
 * Where the deity may appear (owner decision, 2026-09-24, replacing the older
 * "hub greeting only" rule): this emblem beside the hub greeting, the SSK portrait on
 * the first-load splash (components/Splash.tsx), and the app icon / favicon
 * (app/icon.png, app/apple-icon.png). Still never on module rows, notifications or
 * the sign-in form, and never with glow or motion gimmicks outside the splash.
 *
 * It is decorative-devotional: not interactive, role="img" with the localized name,
 * and out of the tab order. The SVG file is drawn with `currentColor`; it is applied as
 * a CSS mask read from its path at runtime, so the single warm-gold accent comes from
 * `background-color` and in-place refinements of the file show up without code changes.
 * There is no glow, gradient, filter, animation, parallax or extra frame.
 */
import type { CSSProperties } from "react";
import { DEVOTIONAL_EMBLEM } from "@/lib/hero-art";
import type { Translate } from "@/lib/i18n";

export default function DevotionalPortrait({ t }: { t: Translate }) {
  const style = {
    "--emblem": `url("${DEVOTIONAL_EMBLEM.src}")`,
    aspectRatio: `${DEVOTIONAL_EMBLEM.width} / ${DEVOTIONAL_EMBLEM.height}`,
  } as CSSProperties;
  return <span className="deity-emblem" role="img" aria-label={t("deityName")} style={style} />;
}
