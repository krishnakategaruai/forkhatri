"use client";

// [FE1 — 2026-09-28] The composer's first screen: one box, "Describe what
// you need", with a mic and a "Read from a photo" option; nothing else
// above the fold (research §1). Typing stays optional — "Fill in myself"
// opens the empty form — and the earlier share/upload modes stay one tap
// away. Presentational: the page runs the AI calls.
import { useRef } from "react";
import { useTranslation } from "react-i18next";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import { MAIN_KINDS, type PostKind } from "./draft";

export interface StartPanelProps {
  text: string;
  onText: (text: string) => void;
  kind: PostKind | null;
  onKind: (kind: PostKind | null) => void;
  busy: "draft" | "photo" | null;
  error: string | null;
  onDraft: (entry: "text" | "voice") => void;
  onPhoto: (file: File) => void;
  onManual: () => void;
  onLegacy: (mode: "share" | "upload") => void;
  /** A photo attached on this screen (kept with the post when it can't be read automatically). */
  attachedImage: string | null;
  attachedImageSrc: string | null;
  onRemoveImage: () => void;
  /** Did the current text come (at least partly) from the microphone? */
  spoken: boolean;
  onSpoken: () => void;
}

export default function StartPanel(p: StartPanelProps) {
  const { t } = useTranslation("hiring");
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="vy-describe">
      <div className="vy-page-head">
        <h1>{t("composer.startTitle")}</h1>
        <p>{t("composer.startSubtitle")}</p>
      </div>

      <div className="vy-options" role="group" aria-label={t("fields.type")}>
        {MAIN_KINDS.map((k) => (
          <button key={k} type="button" className="vy-chip" aria-pressed={p.kind === k} onClick={() => p.onKind(p.kind === k ? null : k)}>
            {t(`kinds.${k}`)}
          </button>
        ))}
      </div>

      <div className="vy-field">
        <label className="vy-label" htmlFor="vy-describe">{t("composer.describeLabel")}</label>
        <VoiceInput
          fieldLabel={t("composer.describeLabel")}
          onConfirm={(spoken) => {
            p.onText(appendSpoken(p.text, spoken));
            p.onSpoken();
          }}
        >
          <textarea
            id="vy-describe"
            className="vy-textarea"
            rows={5}
            maxLength={6000}
            value={p.text}
            onChange={(e) => p.onText(e.target.value)}
            placeholder={t(`composer.describePlaceholder.${p.kind ?? "any"}`)}
          />
        </VoiceInput>
        <span className="vy-field-hint">{t("composer.describeHint")}</span>
      </div>

      {!p.text.trim() && (
        <div className="vy-stack" style={{ gap: 6 }}>
          <span className="vy-field-hint">{t("composer.tryExample")}</span>
          <div className="vy-options">
            {(p.kind ? [p.kind] : MAIN_KINDS).map((k) => (
              <button key={k} type="button" className="vy-chip vy-example" onClick={() => p.onText(t(`composer.examples.${k}`))}>
                {t(`composer.examples.${k}`)}
              </button>
            ))}
          </div>
        </div>
      )}

      {p.attachedImage && (
        <div className="vy-card vy-card-nested vy-row" style={{ gap: 12, padding: 12, alignItems: "flex-start" }}>
          {p.attachedImageSrc && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.attachedImageSrc} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 12, flex: "0 0 72px" }} />
          )}
          <div className="vy-stack" style={{ gap: 4, flex: 1 }}>
            <strong style={{ color: "var(--text-primary)", fontSize: 14 }}>{t("composer.photoAttached")}</strong>
            <span className="vy-field-hint">{t("composer.photoAttachedHint")}</span>
          </div>
          <button type="button" className="vy-btn vy-btn-ghost" onClick={p.onRemoveImage}>
            {t("composer.removePhoto")}
          </button>
        </div>
      )}

      {p.busy && (
        <div className="vy-stack" style={{ gap: 8 }} aria-busy="true" role="status">
          <span className="vy-voice-status">
            <span className="vy-voice-dot" aria-hidden="true" /> {p.busy === "photo" ? t("composer.readingPhoto") : t("composer.drafting")}
          </span>
          <div className="vy-skeleton" style={{ height: 14, width: "70%" }} />
          <div className="vy-skeleton" style={{ height: 14, width: "45%" }} />
        </div>
      )}
      {p.error && <p className="vy-error" role="alert">{p.error}</p>}

      <div className="vy-describe-actions">
        <button type="button" className="vy-btn vy-btn-primary" disabled={!p.text.trim() || p.busy !== null} onClick={() => p.onDraft(p.spoken ? "voice" : "text")}>
          {t("composer.draftIt")}
        </button>
        <button type="button" className="vy-btn vy-btn-secondary" disabled={p.busy !== null} onClick={() => fileRef.current?.click()}>
          {t("composer.usePhoto")}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*,.pdf"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            e.target.value = "";
            if (f) p.onPhoto(f);
          }}
        />
        <button type="button" className="vy-btn vy-btn-ghost" disabled={p.busy !== null} onClick={p.onManual}>
          {t("composer.fillMyself")}
        </button>
      </div>

      <div className="vy-stack" style={{ gap: 8, marginTop: 8 }}>
        <span className="vy-eyebrow">{t("composer.otherWays")}</span>
        <div className="vy-describe-alt">
          <button type="button" className="vy-alt-mode" onClick={() => p.onLegacy("share")}>
            <strong>{t("composer.altShare")}</strong>
            <span>{t("composer.altShareDesc")}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
