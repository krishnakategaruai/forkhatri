"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import Icon from "@/components/Icon";
import SacredLoader from "@/components/SacredLoader";
import { requireSession } from "@/lib/auth";
import { getGuide, type Guide } from "@/lib/guides";

import "../guides.css";

/* One guide: an optional video, then short sections of plain text and
 * points, then the screen it leads to. */

const ACTION_KEY: Record<string, string> = {
  "/help": "help",
  "/circle": "circle",
  "/me/edit": "edit",
  "/wedding": "wedding",
};

function VideoBlock({ url }: { url: string }) {
  // A YouTube link plays in place; any other https video in the browser's player.
  const yt = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/);
  if (yt) {
    return (
      <div className="guide__video">
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${yt[1]}`}
          title="video"
          allow="encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }
  return (
    <div className="guide__video">
      <video src={url} controls preload="metadata" playsInline />
    </div>
  );
}

export default function GuidePage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { t, i18n } = useTranslation(["guides", "common"]);
  const [guide, setGuide] = useState<Guide | null | "missing">(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!(await requireSession()) || !alive) return;
      const g = await getGuide(slug);
      if (alive) setGuide(g ?? "missing");
    })();
    return () => {
      alive = false;
    };
  }, [slug, i18n.language]);

  return (
    <>
      <header className="topbar topbar--wrap">
        <button type="button" className="icon-btn" onClick={() => router.back()} aria-label={t("common:action.back")}>
          <Icon name="back" />
        </button>
        <h1>{guide && guide !== "missing" ? t(`guides:category.${guide.category}`, { defaultValue: "" }) : t("guides:title")}</h1>
        <span style={{ width: 44 }} aria-hidden="true" />
      </header>
      <main className="screen guides">
        {guide === null ? (
          <SacredLoader />
        ) : guide === "missing" ? (
          <p className="caption">{t("guides:notFound")}</p>
        ) : (
          <article className="guide">
            <h2 className="guide__title">{guide.title}</h2>
            <p className="guide__summary">{guide.summary}</p>
            <p className="gcard__meta">{t("guides:minutes", { n: guide.minutes })}</p>
            {guide.language !== i18n.language && i18n.language !== "en" && (
              <p className="caption guide__lang">{t("guides:englishOnly")}</p>
            )}
            {guide.video_url && /^https:\/\//.test(guide.video_url) && <VideoBlock url={guide.video_url} />}
            {guide.sections.map((s, i) => (
              <section key={i} className="guide__section">
                {s.h && <h3 className="guide__h">{s.h}</h3>}
                {s.p && <p className="guide__p">{s.p}</p>}
                {s.points && (
                  <ul className="guide__points">
                    {s.points.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
            {guide.action_href && guide.action_href.startsWith("/") && (
              <Link href={guide.action_href} className="btn btn--primary guide__action">
                {t(`guides:action.${ACTION_KEY[guide.action_href] ?? "default"}`)}
              </Link>
            )}
            <Link href="/guides" className="guide__more">
              {t("guides:more")}
            </Link>
          </article>
        )}
      </main>
    </>
  );
}
