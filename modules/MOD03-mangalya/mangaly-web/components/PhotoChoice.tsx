"use client";

import { useRef } from "react";
import { useTranslation } from "react-i18next";

/* Adding a photo is the member's choice: pick one already on the phone, or
 * take a new one. Two buttons, never a camera opened without being asked. The
 * live face check is a separate step that starts only when the member chooses
 * it. On a computer, "take a photo" opens the file dialog as well.
 *
 * [D11, 2026-10-06] `onFiles` lets several photos be picked at once (for
 * example the ones saved from WhatsApp); `quiet` keeps both buttons plain
 * where the screen already has its one primary action. */
export default function PhotoChoice({
  onFile,
  onFiles,
  disabled,
  busyLabel,
  quiet,
}: {
  onFile?: (file: File) => void | Promise<void>;
  onFiles?: (files: File[]) => void | Promise<void>;
  disabled?: boolean;
  busyLabel?: string;
  quiet?: boolean;
}) {
  const { t } = useTranslation("common");
  const pickRef = useRef<HTMLInputElement>(null);
  const takeRef = useRef<HTMLInputElement>(null);
  const many = !!onFiles;

  function handle(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = ""; // the same photo can be chosen again after a failure
    if (files.length === 0) return;
    if (onFiles) void onFiles(files);
    else if (onFile) void onFile(files[0]);
  }

  return (
    <div className="photo-choice">
      <button
        type="button"
        className={quiet ? "btn" : "btn btn--primary"}
        disabled={disabled}
        onClick={() => pickRef.current?.click()}
      >
        {disabled && busyLabel ? busyLabel : many ? t("photoChoice.chooseMany") : t("photoChoice.choose")}
      </button>
      <button type="button" className="btn" disabled={disabled} onClick={() => takeRef.current?.click()}>
        {t("photoChoice.take")}
      </button>
      <input ref={pickRef} type="file" accept="image/jpeg,image/png,image/webp" multiple={many} hidden onChange={handle} />
      <input ref={takeRef} type="file" accept="image/jpeg,image/png,image/webp" capture="user" hidden onChange={handle} />
    </div>
  );
}
