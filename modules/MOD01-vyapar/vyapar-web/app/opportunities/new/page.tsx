"use client";

// [TR011] Opportunity Composer: create, share, or upload (FR11). Three
// entry modes with one mandatory segment tag (Community/Public). "Upload
// a screenshot" accepts a pasted image URL rather than a real file-upload
// widget in this session — no Object Storage integration exists yet
// (SP008/TR008's signed-URL flow is only wired for verification documents
// so far, not opportunity screenshots); an honest, working substitute
// instead of a fake file picker that goes nowhere.
// Traces to: FR11, FR14, TR011, TR014
//
// [Product-owner reference check, 2026-09-15] "Vyapar is inspired from
// Upwork + WorkIndia" — checked live via web search. Upwork's own posting
// flow has a distinct "Skills & Experience" step ("select required skills,
// experience level, and project budget" — upwork.com/resources/how-to-
// post-job-on-upwork) BEFORE publish, which this composer's create mode
// was missing entirely (`required_capabilities`/`value_amount` were only
// ever sent empty). Added a skills input below — this also feeds FR19's
// own `capability_fit` ranking signal, so it's not cosmetic, it's the exact
// data the feed already scores on. WorkIndia's own pattern (minimal typing,
// fast local jobs) is why this stays ONE optional field, not Upwork's full
// multi-field skill-and-budget wizard — Vyapar's local_service/community
// opportunities are the WorkIndia-shaped case and shouldn't be forced
// through an Upwork-weight form.
// [Product-owner i18n rule] Converted to useTranslation().
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "@/lib/api";

type EntryMode = "create" | "share" | "upload";

const V1_TYPE_IDS = ["employment", "freelance", "local_service"];
const OTHER_TYPE_IDS = ["partnership", "training", "community"];

export default function NewOpportunityPage() {
  const { t } = useTranslation(["opportunities", "common"]);
  const router = useRouter();
  const [mode, setMode] = useState<EntryMode | null>(null);
  // [Coordinator's "fewer taps" refinement, applied here] Segment
  // (Community/Public) is still an explicit, mandatory, independently-
  // changeable choice per FR11 — but it no longer forces its own screen.
  // It's smart-defaulted from the entry mode (create -> usually "my own";
  // share/upload -> usually "found elsewhere") and shown as one inline
  // toggle on the same screen as the details form, cutting three required
  // taps down to two screens without removing the choice itself.
  const [segment, setSegment] = useState<"community" | "public">("community");
  const [sourceName, setSourceName] = useState("");
  const [title, setTitle] = useState("");
  const [type, setType] = useState("employment");
  const [location, setLocation] = useState("");
  const [compensation, setCompensation] = useState("");
  const [skills, setSkills] = useState("");
  const [rawInput, setRawInput] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!mode) return;
    setSaving(true);
    setError(null);
    try {
      const opp = await api.post<{ id: string }>("/v1/opportunities", {
        entry_mode: mode,
        title: mode === "create" ? title : undefined,
        type,
        location: mode === "create" ? location : undefined,
        compensation: compensation || undefined,
        required_capabilities: skills.split(",").map((s) => s.trim()).filter(Boolean),
        response_method: "in_app",
        source_segment: segment,
        source_name: segment === "public" ? sourceName : undefined,
        raw_input: mode !== "create" ? rawInput : undefined,
        raw_image_url: mode === "upload" ? imageUrl : undefined,
      });
      router.push(`/opportunities/${opp.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : t("common:state.somethingWentWrong"));
    } finally {
      setSaving(false);
    }
  }

  if (!mode) {
    return (
      <main className="vy-shell">
        <h1>{t("opportunities:new.chooseModeTitle")}</h1>
        <div className="vy-stack">
          <button
            className="vy-card"
            style={{ textAlign: "left", border: "none", cursor: "pointer" }}
            onClick={() => {
              setMode("create");
              setSegment("community");
            }}
          >
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeCreate")}</h2>
            <p>{t("opportunities:new.modeCreateDesc")}</p>
          </button>
          <button
            className="vy-card"
            style={{ textAlign: "left", border: "none", cursor: "pointer" }}
            onClick={() => {
              setMode("share");
              setSegment("public");
            }}
          >
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeShare")}</h2>
            <p>{t("opportunities:new.modeShareDesc")}</p>
          </button>
          <button
            className="vy-card"
            style={{ textAlign: "left", border: "none", cursor: "pointer" }}
            onClick={() => {
              setMode("upload");
              setSegment("public");
            }}
          >
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeUpload")}</h2>
            <p>{t("opportunities:new.modeUploadDesc")}</p>
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="vy-shell">
      <h1>{mode === "create" ? t("opportunities:new.titleCreate") : mode === "share" ? t("opportunities:new.titleShare") : t("opportunities:new.titleUpload")}</h1>
      <div className="vy-stack">
        <div className="vy-row">
          <button
            className="vy-btn"
            style={{ background: segment === "community" ? "var(--accent)" : "var(--surface-overlay)", color: segment === "community" ? "var(--accent-ink)" : "var(--text-primary)" }}
            onClick={() => setSegment("community")}
          >
            {t("opportunities:new.segmentCommunity")}
          </button>
          <button
            className="vy-btn"
            style={{ background: segment === "public" ? "var(--accent)" : "var(--surface-overlay)", color: segment === "public" ? "var(--accent-ink)" : "var(--text-primary)" }}
            onClick={() => setSegment("public")}
          >
            {t("opportunities:new.segmentPublic")}
          </button>
        </div>

        {segment === "public" && (
          <div className="vy-field">
            <label className="vy-label">{t("opportunities:new.sourceNameLabel")}</label>
            <input className="vy-input" value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder={t("opportunities:new.sourceNamePlaceholder")} />
          </div>
        )}

        {mode === "create" && (
          <>
            <div className="vy-field">
              <label className="vy-label">{t("opportunities:new.titleLabel")}</label>
              <input className="vy-input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t("opportunities:new.titlePlaceholder")} />
            </div>
            <div className="vy-field">
              <label className="vy-label">{t("opportunities:new.locationLabel")}</label>
              <input className="vy-input" value={location} onChange={(e) => setLocation(e.target.value)} placeholder={t("opportunities:new.locationPlaceholder")} />
            </div>
          </>
        )}

        {mode === "share" && (
          <div className="vy-field">
            <label className="vy-label">{t("opportunities:new.pasteLabel")}</label>
            <textarea className="vy-textarea" rows={5} value={rawInput} onChange={(e) => setRawInput(e.target.value)} placeholder={t("opportunities:new.pastePlaceholder")} />
          </div>
        )}

        {mode === "upload" && (
          <div className="vy-field">
            <label className="vy-label">{t("opportunities:new.screenshotLinkLabel")}</label>
            <input className="vy-input" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder={t("opportunities:new.screenshotLinkPlaceholder")} />
            <label className="vy-label" style={{ marginTop: 8 }}>{t("opportunities:new.screenshotNotesLabel")}</label>
            <textarea className="vy-textarea" rows={3} value={rawInput} onChange={(e) => setRawInput(e.target.value)} placeholder={t("opportunities:new.screenshotNotesPlaceholder")} />
          </div>
        )}

        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.typeLabel")}</label>
          <select className="vy-select" value={type} onChange={(e) => setType(e.target.value)}>
            <optgroup label={t("opportunities:new.typeGroupCommon")}>
              {V1_TYPE_IDS.map((id) => (
                <option key={id} value={id}>{t(`opportunities:new.type${id.charAt(0).toUpperCase()}${id.slice(1).replace(/_(.)/g, (_, c) => c.toUpperCase())}` as "new.typeEmployment")}</option>
              ))}
            </optgroup>
            <optgroup label={t("opportunities:new.typeGroupOther")}>
              {OTHER_TYPE_IDS.map((id) => (
                <option key={id} value={id}>{t(`opportunities:new.type${id.charAt(0).toUpperCase()}${id.slice(1)}` as "new.typePartnership")}</option>
              ))}
            </optgroup>
          </select>
        </div>

        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.compensationLabel")}</label>
          <input className="vy-input" value={compensation} onChange={(e) => setCompensation(e.target.value)} placeholder={t("opportunities:new.compensationPlaceholder")} />
        </div>

        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.skillsLabel")}</label>
          <input className="vy-input" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder={t("opportunities:new.skillsPlaceholder")} />
        </div>

        {error && <p className="vy-error">{error}</p>}

        <button
          className="vy-btn vy-btn-primary"
          disabled={saving || (mode === "create" && (!title || !location)) || (mode !== "create" && !rawInput) || (segment === "public" && !sourceName)}
          onClick={submit}
        >
          {saving ? t("common:state.saving") : t("common:action.continue")}
        </button>
      </div>
    </main>
  );
}
