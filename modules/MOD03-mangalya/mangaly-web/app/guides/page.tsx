"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import AccountButton from "@/components/AccountButton";
import Icon from "@/components/Icon";
import MotionTitle from "@/components/MotionTitle";
import SacredLoader from "@/components/SacredLoader";
import { requireSession } from "@/lib/auth";
import { listGuides, type GuideSummary } from "@/lib/guides";

import "./guides.css";

/* Guides (owner, 2026-10-01; migration 063): short articles, and later
 * videos, on using Mangalya well — grouped the way a family would look for
 * them. They come from the database, so new ones appear without a release,
 * and reload when the language changes. */

const ORDER = ["start", "profile", "photos", "safety", "family", "next"];

export default function GuidesPage() {
  const { t, i18n } = useTranslation(["guides", "common"]);
  const [guides, setGuides] = useState<GuideSummary[] | null | "error">(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!(await requireSession()) || !alive) return;
      const list = await listGuides();
      if (alive) setGuides(list ?? "error");
    })();
    return () => {
      alive = false;
    };
  }, [i18n.language]);

  const groups =
    guides && guides !== "error"
      ? [...new Set([...ORDER, ...guides.map((g) => g.category)])]
          .map((c) => ({ category: c, items: guides.filter((g) => g.category === c) }))
          .filter((g) => g.items.length > 0)
      : [];

  return (
    <>
      <header className="topbar">
        <MotionTitle as="h1" className="royal-title" text={t("guides:title")} />
        <div className="topbar__actions">
          <AccountButton />
        </div>
      </header>
      <main className="screen guides">
        <p className="caption guides__intro">{t("guides:intro")}</p>
        {guides === null ? (
          <SacredLoader />
        ) : guides === "error" ? (
          <p className="caption">{t("guides:error")}</p>
        ) : (
          groups.map((g) => (
            <section key={g.category} className="guides__group">
              <h2 className="guides__cat">{t(`guides:category.${g.category}`, { defaultValue: g.category })}</h2>
              <ul className="guides__list">
                {g.items.map((guide) => (
                  <li key={guide.slug}>
                    <Link href={`/guides/${guide.slug}`} className="gcard">
                      <span className="gcard__text">
                        <span className="gcard__title">{guide.title}</span>
                        <span className="gcard__summary">{guide.summary}</span>
                        <span className="gcard__meta">
                          {guide.has_video && (
                            <>
                              <Icon name="play" size={16} />
                              {t("guides:video")} ·{" "}
                            </>
                          )}
                          {t("guides:minutes", { n: guide.minutes })}
                        </span>
                      </span>
                      <Icon name="caretRight" />
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </main>
    </>
  );
}
