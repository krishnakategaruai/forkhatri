"use client";

// [Start flow 2026-10 — decision 12] The completion card: "40% done · Next:
// how many years have you done this work?" with one-tap answers. One
// question per visit, never a wall (LinkedIn's meter never blocks use).
// Answers go through the ordinary PATCH /v1/me/profile; after an answer the
// card says thanks and rests until the next visit.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check } from "lucide-react";
import type { ProfileCompletion } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";

export default function CompletionCard() {
  const { t, i18n } = useTranslation(["firstRun", "common"]);
  const sdk = useSdk();
  const [data, setData] = useState<ProfileCompletion | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let live = true;
    sdk.myProfile
      .completion()
      .then((d) => live && setData(d))
      .catch(() => live && setData(null));
    return () => {
      live = false;
    };
  }, [sdk, i18n.language]);

  if (!data || data.percent <= 0 || (!data.next && !saved)) return null;
  const q = data.next;

  async function answer(value: unknown) {
    if (!q) return;
    setBusy(true);
    try {
      const patch: Record<string, unknown> =
        q.key === "experience_years" ? { experience_years: Number(value) }
        : q.key === "service_radius_km" ? { service_radius_km: Number(value) }
        : q.key === "own_assets" ? { own_assets: (value as string[]).filter((v) => v !== "none") }
        : { headline: String(value).trim() };
      await sdk.myProfile.update(patch);
      setSaved(true);
      setData((d) => (d ? { ...d, percent: Math.min(100, d.percent + Math.round(100 / Math.max(1, d.done.length + 2))), next: null } : d));
    } catch {
      /* the card is a nudge; a failed save is not worth an error wall */
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="vy-card vy-completion" aria-label={t("firstRun:completion.label")}>
      <div className="vy-completion-head">
        <strong>{t("firstRun:completion.percent", { percent: data.percent })}</strong>
        <div className="vy-meter" aria-hidden="true">
          <i style={{ width: `${Math.max(4, Math.min(100, data.percent))}%` }} />
        </div>
      </div>
      {saved || !q ? (
        <p className="vy-completion-thanks">
          <Check size={16} aria-hidden="true" /> {t("firstRun:completion.saved")}
        </p>
      ) : (
        <>
          <p className="vy-completion-q">{t("firstRun:completion.next", { question: q.question })}</p>
          {q.kind === "choice" && (
            <div className="vy-options">
              {q.options.map((o) => (
                <button key={o.value} type="button" className="vy-chip" disabled={busy} onClick={() => answer(o.value)}>
                  {o.label}
                </button>
              ))}
            </div>
          )}
          {q.kind === "multi" && (
            <div className="vy-stack" style={{ gap: 8 }}>
              <div className="vy-options">
                {q.options.map((o) => {
                  const on = picked.includes(o.value);
                  return (
                    <button
                      key={o.value}
                      type="button"
                      className={`vy-chip${on ? " vy-chip-selected" : ""}`}
                      aria-pressed={on}
                      disabled={busy}
                      onClick={() => setPicked((p) => (o.value === "none" ? ["none"] : on ? p.filter((x) => x !== o.value) : [...p.filter((x) => x !== "none"), o.value]))}
                    >
                      {o.label}
                    </button>
                  );
                })}
              </div>
              <button type="button" className="vy-btn vy-btn-secondary" style={{ alignSelf: "flex-start", padding: "9px 16px", fontSize: 14 }} disabled={busy || picked.length === 0} onClick={() => answer(picked)}>
                {t("common:action.save")}
              </button>
            </div>
          )}
          {q.kind === "text" && (
            <form
              className="vy-row"
              style={{ gap: 8, flexWrap: "wrap" }}
              onSubmit={(e) => {
                e.preventDefault();
                if (text.trim().length >= 3) void answer(text);
              }}
            >
              <input className="vy-input" style={{ flex: "1 1 220px" }} value={text} maxLength={120} placeholder={q.placeholder ?? undefined} aria-label={q.question} onChange={(e) => setText(e.target.value)} />
              <button type="submit" className="vy-btn vy-btn-secondary" style={{ padding: "9px 16px", fontSize: 14 }} disabled={busy || text.trim().length < 3}>
                {t("common:action.save")}
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
