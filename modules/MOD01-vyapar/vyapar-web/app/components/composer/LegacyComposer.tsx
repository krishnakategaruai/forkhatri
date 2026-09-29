"use client";

// [TR011 → FE1 2026-09-28] The "share" and "upload" entry modes of the
// opportunity composer (FR11), kept exactly as they worked: paste a
// forwarded message or a link, or upload a screenshot with a short note;
// the server extracts what it can and the poster confirms the extracted
// fields on the opportunity page before publishing (FR12). Moved out of the
// page when the page became the AI-first structured composer; the only
// change is that skills now come from the taxonomy picker instead of a
// comma-separated text box (typed words were never valid skill slugs).
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { ApiError, type TaxonomyTree } from "@/lib/sdk";
import { useSdk } from "@/lib/sdk/react";
import FileUpload from "@/app/components/FileUpload";
import SkillPicker from "@/app/components/taxonomy/SkillPicker";
import VoiceInput, { appendSpoken } from "@/app/components/VoiceInput";
import { MAIN_KINDS, OTHER_KINDS, type PostKind } from "./draft";

export default function LegacyComposer({
  mode,
  initialImageUrl = "",
  initialType = "employment",
  tree,
  notice,
  onBack,
}: {
  mode: "share" | "upload";
  initialImageUrl?: string;
  initialType?: PostKind;
  tree: TaxonomyTree | null;
  notice?: string | null;
  onBack: () => void;
}) {
  const { t } = useTranslation(["opportunities", "common", "hiring"]);
  const sdk = useSdk();
  const router = useRouter();
  const [segment, setSegment] = useState<"community" | "public">("public");
  const [sourceName, setSourceName] = useState("");
  const [type, setType] = useState<PostKind>(initialType);
  const [rawInput, setRawInput] = useState("");
  const [imageUrl, setImageUrl] = useState(initialImageUrl);
  const [skills, setSkills] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      const opp = await sdk.posting.create({
        entry_mode: mode,
        type,
        required_capabilities: skills,
        response_method: "in_app",
        source_segment: segment,
        source_name: segment === "public" ? sourceName : undefined,
        raw_input: rawInput,
        raw_image_url: mode === "upload" ? imageUrl : undefined,
      });
      router.push(`/opportunities/${opp.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? (e.code ? t(`hiring:errors.${e.code}`, { defaultValue: String(e.detail) }) : String(e.detail)) : t("common:state.somethingWentWrong"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="vy-stack" style={{ gap: 20, maxWidth: 640 }}>
      <button type="button" className="vy-btn vy-btn-ghost" style={{ alignSelf: "flex-start", paddingLeft: 0 }} onClick={onBack}>
        ← {t("hiring:composer.backToStart")}
      </button>
      <h1>{mode === "share" ? t("opportunities:new.titleShare") : t("opportunities:new.titleUpload")}</h1>
      {notice && <p className="vy-card vy-card-nested" style={{ padding: 14, fontSize: 14 }}>{notice}</p>}

      <div className="vy-options" role="group" aria-label={t("hiring:fields.segment")}>
        {(["community", "public"] as const).map((s) => (
          <button key={s} type="button" className="vy-chip" aria-pressed={segment === s} onClick={() => setSegment(s)}>
            {t(s === "community" ? "opportunities:new.segmentCommunity" : "opportunities:new.segmentPublic")}
          </button>
        ))}
      </div>

      {segment === "public" && (
        <div className="vy-field">
          <label className="vy-label" htmlFor="vy-src">{t("opportunities:new.sourceNameLabel")}</label>
          <input id="vy-src" className="vy-input" value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder={t("opportunities:new.sourceNamePlaceholder")} />
        </div>
      )}

      {mode === "share" ? (
        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.pasteLabel")}</label>
          <textarea className="vy-textarea" rows={6} value={rawInput} onChange={(e) => setRawInput(e.target.value)} placeholder={t("opportunities:new.pastePlaceholder")} />
        </div>
      ) : (
        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.screenshotLinkLabel")}</label>
          <FileUpload value={imageUrl} onChange={setImageUrl} accept="image/*" />
          <label className="vy-label" style={{ marginTop: 8 }}>{t("opportunities:new.screenshotNotesLabel")}</label>
          <VoiceInput fieldLabel={t("opportunities:new.screenshotNotesLabel")} onConfirm={(text) => setRawInput((v) => appendSpoken(v, text))}>
            <textarea className="vy-textarea" rows={3} value={rawInput} onChange={(e) => setRawInput(e.target.value)} placeholder={t("opportunities:new.screenshotNotesPlaceholder")} />
          </VoiceInput>
        </div>
      )}

      <div className="vy-field">
        <span className="vy-label">{t("hiring:fields.type")}</span>
        <div className="vy-options">
          {[...MAIN_KINDS, ...OTHER_KINDS].map((k) => (
            <button key={k} type="button" className="vy-chip" aria-pressed={type === k} onClick={() => setType(k)}>
              {t(`opportunities:type.${k}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="vy-field">
        <span className="vy-label">
          {t("hiring:fields.skills")} <span className="vy-optional">· {t("hiring:fields.optional")}</span>
        </span>
        <SkillPicker tree={tree} selected={skills} onChange={setSkills} />
      </div>

      {error && <p className="vy-error" role="alert">{error}</p>}
      <button
        type="button"
        className="vy-btn vy-btn-primary vy-submit"
        disabled={saving || !rawInput.trim() || (mode === "upload" && !imageUrl) || (segment === "public" && !sourceName.trim())}
        onClick={submit}
      >
        {saving ? t("common:state.saving") : t("common:action.continue")}
      </button>
    </div>
  );
}
