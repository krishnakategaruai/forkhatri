"use client";

// [Recommendations 2026-09-30] "What Vyapar learned about you" — Profile →
// Settings, and linked from Privacy. A calm settings screen, the way
// Google's "My Ad Center" and YouTube's "not interested" history read:
//   - one short line on what this is;
//   - the learned preferences as plain rows ("Electrician jobs", "Fewer
//     posts far from you"), each with a remove (×) that forgets it at once;
//   - "Reset everything", asked once in place (no extra screen);
//   - a quiet note: it only uses what you did on Vyapar, never who posted.
// Personalisation switched off in Privacy: says so, with the way to turn it
// back on. A new member: "Vyapar learns from what you save and apply to."
// Words: GLOSSARY.md (post, save, apply, Privacy).
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { EyeOff, RotateCcw, ShieldCheck, Sparkles, X } from "lucide-react";
import { ApiError, type TasteItem, type TasteResponse } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import Screen from "@/app/components/Screen";
import { SkeletonGrid } from "@/app/components/States";
import PageHeader from "@/app/components/account/PageHeader";
import { showToast } from "@/app/components/reco/feedbackStore";

export default function LearnedPage() {
  const { t, i18n } = useTranslation(["privacy", "common"]);
  const sdk = useSdk();
  const [data, setData] = useState<TasteResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  const load = useCallback(
    () =>
      sdk.taste
        .get()
        .then((d) => {
          setData(d);
          setFailed(false);
        })
        .catch(() => setFailed(true)),
    [sdk],
  );

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load, i18n.language]);

  const fail = (e: unknown) => showToast(e instanceof ApiError ? String(e.detail) : t("common:state.actionFailed"));

  async function remove(id: string, label: string) {
    setBusy(id);
    try {
      setData(await sdk.taste.remove(id));
      showToast(t("privacy:learned.removed", { label }));
    } catch (e) {
      fail(e);
    } finally {
      setBusy(null);
    }
  }

  async function reset() {
    setBusy("reset");
    try {
      setData(await sdk.taste.reset());
      setConfirmReset(false);
      showToast(t("privacy:learned.resetDone"));
    } catch (e) {
      fail(e);
    } finally {
      setBusy(null);
    }
  }

  const header = (
    <PageHeader title={t("privacy:learned.title")} purpose={t("privacy:learned.purpose")} backHref="/profile" backLabel={t("common:nav.profile")} />
  );

  if (!data)
    return (
      <Screen>
        {header}
        {failed ? (
          <div className="vy-empty">
            <p>{t("common:state.actionFailed")}</p>
            <button type="button" className="vy-btn vy-btn-secondary" onClick={() => void load()}>
              {t("common:action.retry")}
            </button>
          </div>
        ) : (
          <SkeletonGrid count={2} grid={false} />
        )}
      </Screen>
    );

  const groups = [
    { key: "likes", title: t("privacy:learned.likesTitle"), items: data.likes },
    { key: "avoids", title: t("privacy:learned.avoidsTitle"), items: data.avoids },
  ].filter((g) => g.items.length > 0);
  const empty = groups.length === 0;
  const detail = (it: TasteItem) =>
    it.direction === "avoid"
      ? t("privacy:learned.fromHidden")
      : it.source === "applied"
        ? t("privacy:learned.fromApplied")
        : it.source === "saved"
          ? t("privacy:learned.fromSaved")
          : null;

  return (
    <Screen>
      {header}

      {!data.enabled && (
        <div className="vy-learned-off" role="status">
          <span className="vy-acct-tile" data-tint="sky" aria-hidden="true">
            <EyeOff size={20} strokeWidth={1.9} />
          </span>
          <div className="vy-stack" style={{ gap: 4, minWidth: 0 }}>
            <strong>{t("privacy:learned.offTitle")}</strong>
            <span>{t("privacy:learned.offBody")}</span>
            <Link href="/privacy#privacy-analytics" className="vy-tap-link">
              {t("privacy:learned.turnOn")}
            </Link>
          </div>
        </div>
      )}

      {/* Switched off: the note above says it all; "nothing learned yet" would contradict it. */}
      {empty ? (
        data.enabled && <div className="vy-empty vy-learned-empty">
          <span className="vy-empty-mark" aria-hidden="true">
            <Sparkles size={26} strokeWidth={1.8} />
          </span>
          <h2 className="vy-card-title">{t("privacy:learned.emptyTitle")}</h2>
          <p>{t("privacy:learned.emptyBody")}</p>
        </div>
      ) : (
        <section className="vy-card vy-learned-card" aria-label={t("privacy:learned.title")}>
          {groups.map((g) => (
            <div key={g.key} className="vy-learned-group">
              <h2 id={`learned-${g.key}`} className="vy-learned-heading">
                {g.title}
              </h2>
              <ul className="vy-learned-list" role="list" aria-labelledby={`learned-${g.key}`}>
                {g.items.map((it) => {
                  const d = detail(it);
                  return (
                    <li key={it.id} className="vy-learned-row">
                      <span className="vy-learned-text">
                        <span className="vy-learned-label">{it.label}</span>
                        {d && <span className="vy-learned-detail">{d}</span>}
                      </span>
                      <button
                        type="button"
                        className="vy-learned-remove"
                        aria-label={t("privacy:learned.removeOne", { label: it.label })}
                        title={t("common:action.remove")}
                        disabled={busy !== null}
                        onClick={() => void remove(it.id, it.label)}
                      >
                        <X size={18} strokeWidth={2.25} aria-hidden="true" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}

          {confirmReset ? (
            <div className="vy-acct-note" role="alertdialog" aria-labelledby="learned-reset-q">
              <RotateCcw size={18} strokeWidth={2} aria-hidden="true" />
              <div className="vy-stack" style={{ gap: 10 }}>
                <span id="learned-reset-q" style={{ color: "var(--text-primary)" }}>
                  {t("privacy:learned.resetConfirm")}
                </span>
                <div className="vy-row" style={{ flexWrap: "wrap", gap: 8 }}>
                  <button type="button" className="vy-btn vy-btn-secondary" style={{ color: "var(--danger-text)" }} disabled={busy !== null} onClick={() => void reset()}>
                    {t("privacy:learned.resetYes")}
                  </button>
                  <button type="button" className="vy-btn vy-btn-ghost" disabled={busy !== null} onClick={() => setConfirmReset(false)}>
                    {t("common:action.cancel")}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <button type="button" className="vy-btn vy-btn-ghost vy-learned-reset" disabled={busy !== null} onClick={() => setConfirmReset(true)}>
                <RotateCcw size={18} strokeWidth={2} aria-hidden="true" />
                {t("privacy:learned.reset")}
              </button>
            </div>
          )}
        </section>
      )}

      <p className="vy-learned-note">
        <ShieldCheck size={18} strokeWidth={2} aria-hidden="true" />
        <span>{t("privacy:learned.note")}</span>
      </p>
    </Screen>
  );
}
