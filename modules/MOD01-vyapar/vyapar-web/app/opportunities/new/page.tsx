"use client";

// [TR011] Opportunity Composer: create, share, or upload (FR11). Three
// entry modes with one mandatory segment tag (Community/Public).
// [Critique agent finding, fixed] "Upload a screenshot" now uses a real
// file-picker (app/components/FileUpload.tsx → POST /v1/uploads →
// dev-environment local-disk storage, served back statically) instead of
// a pasted-URL field — FR11's own named scenario (forwarding a WhatsApp
// screenshot) has no URL to paste for a gallery photo, so the earlier
// substitute was honestly documented but genuinely unusable for that case.
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
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { api, ApiError, resolveAttachmentUrl } from "@/lib/api";
import FileUpload from "@/app/components/FileUpload";
import Screen from "@/app/components/Screen";
import ProfileSetup from "@/app/components/ProfileSetup";
import type { Me } from "@/lib/sdk";
import ComposerPreview, { PreviewCard } from "@/app/post/_components/ComposerPreview";

type EntryMode = "create" | "share" | "upload";

const V1_TYPE_IDS = ["employment", "freelance", "local_service"];
const OTHER_TYPE_IDS = ["partnership", "training", "community"];
// [IMP39] Mirrors TYPE_ACTION_LABEL in the API (services/opportunities.py),
// used ONLY to label the live preview the way the feed card will.
const TYPE_ACTION: Record<string, string> = {
  employment: "apply",
  freelance: "submitProposal",
  local_service: "enquireNow",
  partnership: "contact",
  training: "register",
  community: "register",
};

export default function NewOpportunityPage() {
  const { t, i18n } = useTranslation(["opportunities", "common", "discover"]);
  const router = useRouter();
  const [mode, setMode] = useState<EntryMode | null>(null);
  // [Owner, 2026-09-22] no profile of either kind → setup first.
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    api.get<Me>("/v1/members/me").then(setMe).catch(() => setMe(null));
  }, [i18n.language]);
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
  // [IMP39] the poster's own name, shown on the live preview exactly where
  // the feed card shows the submitter line
  const [myName, setMyName] = useState("");

  useEffect(() => {
    api.get<{ display_name: string }>("/v1/members/me").then((m) => setMyName(m.display_name)).catch(() => undefined);
  }, []);

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

  if (me?.profiles && !me.profiles.complete) {
    return (
      <Screen width="wide">
        <h1>{t("opportunities:new.chooseModeTitle")}</h1>
        <ProfileSetup profiles={me.profiles} required />
      </Screen>
    );
  }

  if (!mode) {
    return (
      <Screen width="wide">
        <h1>{t("opportunities:new.chooseModeTitle")}</h1>
        <div className="vy-stack vy-choice-grid vy-choice-grid-3">
          <button
            className="vy-card vy-choice"
            onClick={() => {
              setMode("create");
              setSegment("community");
            }}
          >
            <span className="vy-choice-mark" aria-hidden="true">¶</span>
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeCreate")}</h2>
            <p>{t("opportunities:new.modeCreateDesc")}</p>
            <span className="vy-choice-arrow" aria-hidden="true">→</span>
          </button>
          <button
            className="vy-card vy-choice"
            onClick={() => {
              setMode("share");
              setSegment("public");
            }}
          >
            <span className="vy-choice-mark" aria-hidden="true">⇪</span>
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeShare")}</h2>
            <p>{t("opportunities:new.modeShareDesc")}</p>
            <span className="vy-choice-arrow" aria-hidden="true">→</span>
          </button>
          <button
            className="vy-card vy-choice"
            onClick={() => {
              setMode("upload");
              setSegment("public");
            }}
          >
            <span className="vy-choice-mark" aria-hidden="true">▣</span>
            <h2 style={{ fontSize: 17 }}>{t("opportunities:new.modeUpload")}</h2>
            <p>{t("opportunities:new.modeUploadDesc")}</p>
            <span className="vy-choice-arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </Screen>
    );
  }

  // [IMP39] Live preview (desktop): the Discover card other members will
  // see, from the values typed so far. For share/upload the server derives
  // the title from the pasted text, so the preview shows the first line and
  // says so, rather than inventing what the parser will produce.
  const firstLine = rawInput.split(/\r?\n/).map((l) => l.trim()).find(Boolean) ?? "";
  const previewTitle = mode === "create" ? title.trim() : firstLine.slice(0, 90);
  const previewMeta = [
    t(`opportunities:actionLabel.${TYPE_ACTION[type] ?? "contact"}` as "actionLabel.apply"),
    segment === "community" ? t("discover:home.sectionCommunity") : t("discover:home.sectionPublic"),
    t("common:preview.postedToday"),
  ].join(" · ");

  return (
    <Screen width="wide">
      <h1>{mode === "create" ? t("opportunities:new.titleCreate") : mode === "share" ? t("opportunities:new.titleShare") : t("opportunities:new.titleUpload")}</h1>
      <div className="vy-compose">
      <div className="vy-compose-main">
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
            {/* [Critique agent finding, fixed here] FR11's own named scenario
                is forwarding a WhatsApp screenshot — a pasted-URL field is
                unusable for a photo sitting in a gallery with no URL. Real
                file upload via the one shared FileUpload component. */}
            <label className="vy-label">{t("opportunities:new.screenshotLinkLabel")}</label>
            <FileUpload value={imageUrl} onChange={setImageUrl} accept="image/*" />
            <label className="vy-label" style={{ marginTop: 8 }}>{t("opportunities:new.screenshotNotesLabel")}</label>
            <textarea className="vy-textarea" rows={3} value={rawInput} onChange={(e) => setRawInput(e.target.value)} placeholder={t("opportunities:new.screenshotNotesPlaceholder")} />
          </div>
        )}

        <div className="vy-field-pair">
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
        </div>

        <div className="vy-field">
          <label className="vy-label">{t("opportunities:new.skillsLabel")}</label>
          <input className="vy-input" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder={t("opportunities:new.skillsPlaceholder")} />
        </div>

        {error && <p className="vy-error">{error}</p>}

        <button
          className="vy-btn vy-btn-primary vy-submit"
          disabled={saving || (mode === "create" && (!title || !location)) || (mode !== "create" && !rawInput) || (segment === "public" && !sourceName)}
          onClick={submit}
        >
          {saving ? t("common:state.saving") : t("common:action.continue")}
        </button>
      </div>
      </div>
      <ComposerPreview guide={[t("opportunities:new.guide1"), t("opportunities:new.guide2"), t("opportunities:new.guide3")]}>
        <PreviewCard
          image={mode === "upload" && imageUrl ? resolveAttachmentUrl(imageUrl) : undefined}
          title={previewTitle}
          subtitle={[mode === "create" ? location.trim() : "", compensation.trim()].filter(Boolean).join(" · ") || undefined}
          chips={skills.split(",").map((x) => x.trim()).filter(Boolean)}
          submitter={segment === "public" && sourceName.trim() ? sourceName.trim() : myName || undefined}
          meta={previewMeta}
        />
        {mode !== "create" && <p className="vy-muted">{t("opportunities:new.previewFromText")}</p>}
      </ComposerPreview>
      </div>
    </Screen>
  );
}
