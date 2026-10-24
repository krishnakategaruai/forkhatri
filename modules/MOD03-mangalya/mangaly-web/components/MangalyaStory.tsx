"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import Vignette from "@/components/Vignette";

const ART = ["family", "basics", "community", "partner", "lifestyle", "photos", "future"];
// [D2, 2026-10-06] The first-launch story is three cards; the full seven stay on Help.
const SHORT_ART = ["family", "partner", "community"];

type Card = { title: string; body: string };

/* The story of Mangalya: seven short cards, one idea each, in the member's
   language. Shown once before "Who is this profile for?" and kept on Help. */
export function useStoryCards(): Card[] {
  const { t } = useTranslation("help");
  return t("help:story", { returnObjects: true }) as Card[];
}

export default function MangalyaStory({ onDone, short }: { onDone: () => void; short?: boolean }) {
  const { t } = useTranslation("help");
  const full = useStoryCards();
  const cards = short ? (t("help:storyShort", { returnObjects: true }) as Card[]) : full;
  const art = short ? SHORT_ART : ART;
  const [i, setI] = useState(0);
  const card = cards[i];
  const last = i === cards.length - 1;
  return (
    <main className="screen screen--form story">
      <div className="story__top">
        <span className="caption">{t("help:storyTitle")}</span>
        <button type="button" className="link link--button" onClick={onDone}>
          {t("help:skip")}
        </button>
      </div>
      <div className="story__dots" aria-hidden="true">
        {cards.map((_, k) => (
          <span key={k} className={`story__dot${k === i ? " is-active" : ""}`} />
        ))}
      </div>
      <div className="form wizard-step" key={i}>
        <Vignette id={art[i] ?? "family"} className="wizard-step__art" />
        <div className="wizard-step__head">
          <h1 className="h2">{card.title}</h1>
          <p className="story__body">{card.body}</p>
          {short && last && <p className="caption">{t("help:storyMore")}</p>}
        </div>
        <div className="form__actions story__actions">
          {i > 0 && (
            <button type="button" className="btn" onClick={() => setI(i - 1)}>
              {t("help:back")}
            </button>
          )}
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => (last ? onDone() : setI(i + 1))}
          >
            {last ? t("help:begin") : t("help:next")}
          </button>
        </div>
      </div>
    </main>
  );
}

export const STORY_SEEN_KEY = "mangalya.story.seen";

export function storySeen(): boolean {
  try {
    return window.localStorage.getItem(STORY_SEEN_KEY) === "1";
  } catch {
    return true;
  }
}

export function markStorySeen(): void {
  try {
    window.localStorage.setItem(STORY_SEEN_KEY, "1");
  } catch {
    /* private mode: the story simply shows again next time */
  }
}
