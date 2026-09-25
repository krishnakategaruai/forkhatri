"use client";

// [Design direction] Reusable listing/opportunity card with subtle depth
// (single-direction shadow + 1px border shift on hover, never a gradient)
// and the three trust axes kept visually distinct per 04-ui.md's own
// separation rule, re-skinned into the one-accent minimal palette:
// verification = filled tinted label (calm green, ONLY for that label),
// Sponsored = dashed neutral outline tag, reputation = plain text + icon.
// Traces to: FR16 (listing detail context), FR54/SP030 (SponsoredBadge-CC —
// one shared render path for every paid-placement surface)
import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import SponsoredBadge from "@/app/components/SponsoredBadge";
import { Morph } from "@/app/components/Screen";

interface LivingCardProps {
  href: string;
  title: string;
  subtitle?: string;
  verified?: boolean;
  verificationLabel?: string;
  sponsored?: boolean;
  memberProvided?: boolean;
  meta?: string;
  // [Real gap found live by the product owner, fixed here] the submitter's
  // name used to be folded into the generic `meta` line, rendered in the
  // exact same lowest-emphasis style as a throwaway freshness stamp —
  // confirmed in this file's own CSS classes. Research on this audience
  // found they trust their own social network more than institutional
  // signals, so it gets its own line with a touch more visual weight
  // (secondary text colour + medium weight) than the plain meta line.
  submitterName?: string;
  children?: React.ReactNode;
  // [Real gap found via third critique pass, fixed here] UX08 names an
  // overflow menu (Not interested/Share/Report) as a per-card affordance
  // on the home feed itself — these actions already existed on the detail
  // screens but never here. Optional so LivingCard stays the one shared
  // card for every surface (Businesses cards have no "not interested"
  // concept, per FR20 — only opportunity cards do).
  onNotInterested?: () => void;
  reportHref?: string;
  shareText?: string;
  // [IMP33 — motion] Position in its list. Drives the entrance stagger
  // (see Motion.tsx for the timing rationale). Optional so no existing
  // call site breaks; a card without an index simply arrives at delay 0.
  index?: number;
  // [IMP33 — shared-element transition] When set, this card morphs into
  // the heading of the screen it opens instead of the two crossfading.
  // Must match the `Morph` name used on that detail screen.
  morphName?: string;
}

export default function LivingCard({
  href,
  title,
  subtitle,
  verified,
  verificationLabel,
  sponsored,
  memberProvided,
  meta,
  submitterName,
  children,
  onNotInterested,
  reportHref,
  shareText,
  index = 0,
  morphName,
}: LivingCardProps) {
  const { t } = useTranslation("common");
  const reduceMotion = useReducedMotion();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const hasMenu = onNotInterested || reportHref || shareText;

  async function share(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setMenuOpen(false);
    const url = typeof window !== "undefined" ? `${window.location.origin}${href}` : href;
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ title, text: shareText, url });
      } catch {
        /* member cancelled — not an error */
      }
    } else if (typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(url);
    }
  }

  return (
    // [IMP33] `transitionTypes` tags this as a *forward* navigation so the
    // destination screen slides in from the right and the list slides
    // left — the film/animation convention the Next.js guide cites, where
    // horizontal direction encodes navigation depth. Without the tag the
    // route change has no direction and every navigation looks identical.
    <Link
      href={href}
      // [IMP33] block + full height so a card stretches to its grid row on
      // desktop; previously the inline anchor made cards in a 2/3-column
      // grid ragged at different heights.
      style={{ textDecoration: "none", display: "block", height: "100%" }}
      transitionTypes={["vy-forward"]}
    >
      <motion.div
        className="vy-card"
        // [Design-enhancement pass, DESIGN-ENHANCEMENT.md] uses the named
        // --border-default step instead of a raw ink-5 value.
        // [IMP33] Entrance: the card rises into place with its list
        // position as a delay, so a grid of results reads as arriving in
        // order rather than appearing all at once. `initial`/`animate`
        // are skipped entirely under prefers-reduced-motion — a `false`
        // initial is the documented way to opt a motion element out.
        initial={reduceMotion ? false : { opacity: 0, y: 10 }}
        animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        whileHover={{ y: -2, borderColor: "var(--border-default)" }}
        whileTap={{ scale: 0.99 }}
        transition={{
          type: "spring",
          stiffness: 320,
          damping: 30,
          delay: reduceMotion ? 0 : Math.min(index * 0.035, 0.28),
        }}
        style={{ cursor: "pointer", position: "relative", height: "100%" }}
      >
        <div className="vy-row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
          {morphName ? (
            <Morph name={morphName}>
              <h3 style={{ fontSize: 17 }}>{title}</h3>
            </Morph>
          ) : (
            <h3 style={{ fontSize: 17 }}>{title}</h3>
          )}
          <div className="vy-row" style={{ gap: 4 }}>
            {sponsored && <SponsoredBadge />}
            {hasMenu && (
              <button
                type="button"
                className="vy-btn vy-btn-ghost"
                style={{ padding: "4px 8px", fontSize: 16, lineHeight: 1 }}
                aria-label={t("action.moreOptions")}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setMenuOpen((v) => !v);
                }}
              >
                ⋯
              </button>
            )}
          </div>
        </div>
        <AnimatePresence>
          {menuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="vy-card"
              style={{ position: "absolute", top: 40, right: 8, zIndex: 5, padding: 6, width: 180 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="vy-stack" style={{ gap: 2 }}>
                {onNotInterested && (
                  <button
                    type="button"
                    className="vy-btn vy-btn-ghost"
                    style={{ justifyContent: "flex-start", fontSize: 13 }}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setMenuOpen(false);
                      onNotInterested();
                    }}
                  >
                    {t("action.notInterested")}
                  </button>
                )}
                {shareText && (
                  <button type="button" className="vy-btn vy-btn-ghost" style={{ justifyContent: "flex-start", fontSize: 13 }} onClick={share}>
                    {t("action.share")}
                  </button>
                )}
                {reportHref && (
                  <button
                    type="button"
                    className="vy-btn vy-btn-ghost"
                    style={{ justifyContent: "flex-start", fontSize: 13 }}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setMenuOpen(false);
                      router.push(reportHref);
                    }}
                  >
                    {t("action.report")}
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {subtitle && <p style={{ marginBottom: 8 }}>{subtitle}</p>}
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
          {verified && (
            <span className="vy-badge vy-badge-verified">✓ {verificationLabel ?? t("badge.verified")}</span>
          )}
          {memberProvided && <span className="vy-badge vy-badge-member-provided">{t("badge.memberProvided")}</span>}
        </div>
        {/* [Design-enhancement pass, DESIGN-ENHANCEMENT.md] uses the new
            --text-quaternary token — the same fix this spec names for the
            still-open UX-CRITIQUE finding on social-trust framing
            prominence, now expressed through the design system's own
            lightness-step ladder rather than a one-off inline colour. */}
        {submitterName && <p style={{ marginTop: 6, fontSize: 13, fontWeight: 500, color: "var(--text-quaternary)" }}>{submitterName}</p>}
        {meta && <p className="vy-muted" style={{ marginTop: 4 }}>{meta}</p>}
        {children}
      </motion.div>
    </Link>
  );
}
