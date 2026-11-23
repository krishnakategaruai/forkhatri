"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { postJson } from "@/lib/api";
import { clearAllDrafts } from "@/lib/draft";
import { entranceUrl } from "@/lib/platform";

/* Account deletion, kind B (docs/ParentApp/ACCOUNT-DELETION.md): "Delete my
 * data in Mangalya". Plain list of what goes and what stays, the word DELETE
 * typed, a red button. The ForKhatri account is untouched; the member can come
 * back later as a brand-new Mangalya member. Drafts kept on this device
 * (keys starting "mangaly.") are cleared on success. */
export default function DeleteMyData() {
  const { t } = useTranslation(["common"]);
  const [open, setOpen] = useState(false);
  const [word, setWord] = useState("");
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<"idle" | "error" | "limited" | "role" | "done">("idle");

  async function run() {
    setBusy(true);
    const res = await postJson("/privacy/delete-account-data", { confirm: "DELETE" });
    setBusy(false);
    if (res.ok) {
      await clearAllDrafts();
      try {
        Object.keys(window.localStorage)
          .filter((k) => k.startsWith("mangaly."))
          .forEach((k) => window.localStorage.removeItem(k));
        window.sessionStorage.clear();
      } catch {
        /* storage unavailable: nothing to clear */
      }
      setState("done");
      // Replace the deleted session's history entry so Back cannot restore
      // the post-deletion screen from the browser's back/forward cache.
      window.setTimeout(() => window.location.replace(entranceUrl()), 2500);
      return;
    }
    setState(res.status === 429 ? "limited" : res.status === 409 ? "role" : "error");
  }

  if (state === "done") {
    return (
      <p className="caption" role="status" data-testid="delete-data-done">
        {t("common:deleteData.done")}
      </p>
    );
  }
  return (
    <div className="sheet__stack" style={{ marginTop: 16 }} data-testid="delete-data">
      {!open ? (
        <button type="button" className="quick-pick__chip" onClick={() => setOpen(true)}>
          {t("common:deleteData.open")}
        </button>
      ) : (
        <>
          <p className="caption" style={{ margin: 0, fontWeight: 600 }}>
            {t("common:deleteData.title")}
          </p>
          <p className="caption" style={{ margin: 0 }}>{t("common:deleteData.deleted")}</p>
          <p className="caption" style={{ margin: 0 }}>{t("common:deleteData.retained")}</p>
          <p className="caption" style={{ margin: 0 }}>{t("common:deleteData.kept")}</p>
          <label className="caption" htmlFor="delete-data-word">{t("common:deleteData.type")}</label>
          <input
            id="delete-data-word"
            value={word}
            autoComplete="off"
            onChange={(e) => setWord(e.target.value)}
          />
          {state === "error" && <p className="caption" role="alert">{t("common:deleteData.error")}</p>}
          {state === "limited" && <p className="caption" role="alert">{t("common:deleteData.limited")}</p>}
          {state === "role" && <p className="caption" role="alert">{t("common:deleteData.role")}</p>}
          <button
            type="button"
            className="sheet__danger"
            disabled={word !== "DELETE" || busy}
            onClick={() => void run()}
          >
            {t("common:deleteData.button")}
          </button>
          <button type="button" className="quick-pick__chip" onClick={() => { setOpen(false); setWord(""); }}>
            {t("common:action.cancel")}
          </button>
        </>
      )}
    </div>
  );
}
