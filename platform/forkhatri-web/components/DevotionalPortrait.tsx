/**
 * ForKhatri's own devotional emblem of Bhagwan Kartavirya Sahasrarjun, shown beside the
 * greeting on the signed-in hub ONLY. Never on module rows, loaders, logo/favicon,
 * notifications or sign-in screens.
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
