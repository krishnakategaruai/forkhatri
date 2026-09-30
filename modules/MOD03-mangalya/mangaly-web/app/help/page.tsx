"use client";

import { useTranslation } from "react-i18next";
import Vignette from "@/components/Vignette";
import { useStoryCards } from "@/components/MangalyaStory";

const ART = ["family", "basics", "community", "partner", "lifestyle", "photos", "future"];

type Faq = { q: string; a: string };

export default function HelpPage() {
  const { t } = useTranslation("help");
  const cards = useStoryCards();
  const faq = t("help:faq", { returnObjects: true }) as Faq[];
  return (
    <>
      <header className="topbar topbar--wrap">
        <h1>{t("help:title")}</h1>
      </header>
      <main className="screen help">
        <p className="caption help__intro">{t("help:intro")}</p>
        <h2 className="h3">{t("help:storyTitle")}</h2>
        <ol className="help__story">
          {cards.map((c, i) => (
            <li key={c.title} className="help__card">
              <Vignette id={ART[i] ?? "family"} className="help__art" />
              <div>
                <h3 className="help__cardTitle">{c.title}</h3>
                <p className="help__cardBody">{c.body}</p>
              </div>
            </li>
          ))}
        </ol>
        <h2 className="h3">{t("help:faqTitle")}</h2>
        <div className="help__faq">
          {faq.map((f) => (
            <details key={f.q} className="help__q">
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </main>
    </>
  );
}
