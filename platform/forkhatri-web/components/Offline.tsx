"use client";

/** Identity service unreachable (TR05): calm, honest, with Retry and the last good registry dimmed. */
import type { CSSProperties } from "react";
import type { ModuleEntry } from "@/lib/api";
import type { Translate } from "@/lib/i18n";
import { CloudOffIcon, Sigil } from "./ui";

type OfflineProps = {
  t: Translate;
  cached: ModuleEntry[] | null;
  retrying: boolean;
  onRetry: () => void;
};

export default function Offline({ t, cached, retrying, onRetry }: OfflineProps) {
  return (
    <main id="main" className="offline" tabIndex={-1}>
      <div className="offline-card" role="alert">
        <span className="offline-orb" aria-hidden="true">
          <CloudOffIcon size={30} />
        </span>
        <h1 className="offline-title">{t("offlineTitle")}</h1>
        <p className="offline-body">{t("offlineBody")}</p>
        <button type="button" className="btn-primary" onClick={onRetry} disabled={retrying}>
          {retrying ? (
            <>
              <span className="spinner" aria-hidden="true" /> {t("offlineRetrying")}
            </>
          ) : (
            t("retry")
          )}
        </button>
      </div>

      {cached && cached.length > 0 && (
        <section className="offline-cached" aria-label={t("offlineCached")}>
          <p className="eyebrow">{t("offlineCached")}</p>
          <ul className="offline-list">
            {cached.map((module) => (
              <li key={module.key} className="offline-item" style={{ "--accent": module.accent } as CSSProperties}>
                <Sigil moduleKey={module.key} size={32} />
                <span>
                  <span className="offline-item-name">{module.name}</span>
                  <span className="offline-item-tagline">{module.tagline}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
