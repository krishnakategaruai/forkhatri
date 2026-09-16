"use client";

// [Design direction] Reusable listing/opportunity card with subtle depth
// (single-direction shadow + 1px border shift on hover, never a gradient)
// and the three trust axes kept visually distinct per 04-ui.md's own
// separation rule, re-skinned into the one-accent minimal palette:
// verification = filled tinted label (calm green, ONLY for that label),
// Sponsored = dashed neutral outline tag, reputation = plain text + icon.
// Traces to: FR16 (listing detail context), FR54/SP030 (SponsoredBadge-CC —
// one shared render path for every paid-placement surface)
import { motion } from "motion/react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import SponsoredBadge from "@/app/components/SponsoredBadge";

interface LivingCardProps {
  href: string;
  title: string;
  subtitle?: string;
  verified?: boolean;
  verificationLabel?: string;
  sponsored?: boolean;
  memberProvided?: boolean;
  meta?: string;
  children?: React.ReactNode;
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
  children,
}: LivingCardProps) {
  const { t } = useTranslation("common");
  return (
    <Link href={href} style={{ textDecoration: "none" }}>
      <motion.div
        className="vy-card"
        whileHover={{ y: -2, borderColor: "var(--ink-5)" }}
        whileTap={{ scale: 0.99 }}
        transition={{ type: "spring", stiffness: 400, damping: 28 }}
        style={{ cursor: "pointer" }}
      >
        <div className="vy-row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
          <h3 style={{ fontSize: 17 }}>{title}</h3>
          {sponsored && <SponsoredBadge />}
        </div>
        {subtitle && <p style={{ marginBottom: 8 }}>{subtitle}</p>}
        <div className="vy-row" style={{ flexWrap: "wrap", gap: 6 }}>
          {verified && (
            <span className="vy-badge vy-badge-verified">✓ {verificationLabel ?? t("badge.verified")}</span>
          )}
          {memberProvided && <span className="vy-badge vy-badge-member-provided">{t("badge.memberProvided")}</span>}
        </div>
        {meta && <p className="vy-muted" style={{ marginTop: 8 }}>{meta}</p>}
        {children}
      </motion.div>
    </Link>
  );
}
