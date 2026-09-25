"use client";

// [Critique agent finding, fixed here] "Upload a screenshot" (opportunity
// entry, FR11) and the enquiry composer's attachment (FR22) both only ever
// accepted a pasted image URL — unusable for FR11's own named scenario (a
// forwarded WhatsApp screenshot sitting in a gallery, not at a URL). This
// is the ONE real file-picker + upload component; every screen that needs
// "attach a file" renders this, never a second divergent input.
// Traces to: FR11, FR22
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { uploadFile, resolveAttachmentUrl, ApiError } from "@/lib/api";

export default function FileUpload({
  value,
  onChange,
  accept = "image/*,.pdf",
}: {
  value: string;
  onChange: (url: string) => void;
  accept?: string;
}) {
  const { t } = useTranslation("common");
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const { url } = await uploadFile(file);
      onChange(url);
    } catch (e) {
      setError(e instanceof ApiError ? t("upload.failed") : t("state.somethingWentWrong"));
    } finally {
      setBusy(false);
    }
  }

  if (value) {
    return (
      <div className="vy-row" style={{ gap: 8, alignItems: "center" }}>
        <span className="vy-chip">{value.split("/").pop()}</span>
        <button type="button" className="vy-btn vy-btn-ghost" style={{ fontSize: 13 }} onClick={() => onChange("")}>
          {t("action.remove")}
        </button>
      </div>
    );
  }

  return (
    <div className="vy-stack" style={{ gap: 4 }}>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="vy-input"
        disabled={busy}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {busy && <span className="vy-muted" style={{ fontSize: 12 }}>{t("upload.uploading")}</span>}
      {error && <span className="vy-error" style={{ fontSize: 12 }}>{error}</span>}
    </div>
  );
}
