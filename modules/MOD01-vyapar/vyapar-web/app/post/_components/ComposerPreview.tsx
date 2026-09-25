"use client";

// ======================================================================
// [IMP39 — agent D] The composer's live preview panel (desktop only).
//
// REQUIREMENT (owner): "why do I see it as phone only?" — the create/edit
// forms were a 720px stack of fields on a 1440px screen. The desktop
// layout puts the form on the left and, on the right, a sticky panel that
// shows what the OTHER person will see, built from the values being typed.
// Neither reference app does this at posting time (Upwork reviews the post
// only on a final step; WorkIndia not at all), and it answers the one
// question a poster actually has: "how will this look to them?".
//
// Static markup that mirrors LivingCard's card (title, subtitle, badges,
// submitter line, meta line) rather than LivingCard itself: LivingCard is a
// navigating <Link> with a menu and motion, and a preview must not be
// clickable or animate on every keystroke. `aria-live="polite"` is left off
// deliberately — announcing every keystroke's re-render would be noise; the
// form fields themselves are the accessible source of truth.
//
// Lives in a private `_components` folder so the App Router never treats it
// as a route. Rendered inside `.vy-compose-aside`, which is display:none
// below 900px, so the phone flow is unchanged.
// ======================================================================

import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export interface PreviewCardProps {
  title: string;
  subtitle?: string;
  submitter?: string;
  meta?: string;
  badges?: ReactNode;
  chips?: string[];
  image?: string;
  body?: string;
  bodyEmpty?: string;
}

export function PreviewCard({ title, subtitle, submitter, meta, badges, chips, image, body, bodyEmpty }: PreviewCardProps) {
  const { t } = useTranslation("common");
  return (
    <div className="vy-card vy-preview-card">
      {image && (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="vy-preview-img" src={image} alt="" />
      )}
      <h3 className={title ? undefined : "vy-preview-empty"}>{title || t("preview.titlePlaceholder")}</h3>
      {subtitle && <p>{subtitle}</p>}
      {body !== undefined && (
        <p className={`vy-preview-body ${body ? "" : "vy-preview-empty"}`}>{body || bodyEmpty}</p>
      )}
      {badges && <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>{badges}</div>}
      {chips && chips.length > 0 && (
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
          {chips.map((c) => (
            <span key={c} className="vy-chip">{c}</span>
          ))}
        </div>
      )}
      {submitter && <p style={{ fontSize: 13, fontWeight: 500, color: "var(--text-quaternary)" }}>{submitter}</p>}
      {meta && <p className="vy-muted">{meta}</p>}
    </div>
  );
}

export default function ComposerPreview({
  caption,
  guide,
  children,
  before,
}: {
  /** One line under the "Live preview" label. Defaults to the post caption. */
  caption?: string;
  /** Short guidance bullets shown under the preview. */
  guide?: string[];
  /** Optional block above the preview (e.g. who you are writing to). */
  before?: ReactNode;
  children: ReactNode;
}) {
  const { t } = useTranslation("common");
  return (
    <aside className="vy-compose-aside" aria-label={t("preview.label")}>
      {before}
      <span className="vy-preview-label">{t("preview.label")}</span>
      <p className="vy-preview-caption">{caption ?? t("preview.caption")}</p>
      {children}
      {guide && guide.length > 0 && (
        <div className="vy-guide">
          <h3>{t("preview.guideTitle")}</h3>
          <ul>
            {guide.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
