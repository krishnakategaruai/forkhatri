"use client";

/**
 * Account sheet content. The platform keeps only basic member information:
 * name, masked phone/email and language (PATCH /v1/me), plus sign-out.
 * Module-specific details are managed inside each module. A sheet, never a
 * page that eats space.
 */
import { AnimatePresence, motion } from "motion/react";
import { useState, type FormEvent } from "react";
import { ApiError, NetworkError, type Lang, type Member } from "@/lib/api";
import { errorText, LANGUAGES, type MessageKey, type Translate } from "@/lib/i18n";
import { useThemeChoice } from "@/lib/theme";
import type { ThemeChoice } from "@/lib/theme-script";
import { Avatar, CheckIcon, LockIcon, LogOutIcon } from "./ui";

type AccountSheetProps = {
  t: Translate;
  lang: Lang;
  member: Member;
  onLang: (lang: Lang) => void;
  onUpdate: (patch: Partial<Pick<Member, "display_name">>) => Promise<Member>;
  onSignOut: (everywhere: boolean) => Promise<void>;
};

const THEME_OPTIONS: { value: ThemeChoice; label: MessageKey }[] = [
  { value: "system", label: "themeSystem" },
  { value: "light", label: "themeLight" },
  { value: "dark", label: "themeDark" },
];

export default function AccountSheet({ t, lang, member, onLang, onUpdate, onSignOut }: AccountSheetProps) {
  const [theme, setTheme] = useThemeChoice();
  const [editingName, setEditingName] = useState(false);
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<{ kind: "saving" | "saved" | "error"; text: string } | null>(null);
  const [confirmEverywhere, setConfirmEverywhere] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  function startEdit() {
    setEditingName(true);
    setDraft(member.display_name);
    setStatus(null);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    const value = draft.trim();
    if (!value) return;
    setStatus({ kind: "saving", text: t("saving") });
    try {
      await onUpdate({ display_name: value });
      setEditingName(false);
      setStatus({ kind: "saved", text: t("saved") });
    } catch (caught) {
      const text =
        caught instanceof ApiError ? errorText(t, caught.code, caught.retryAfter) : caught instanceof NetworkError ? t("err_network") : t("saveFailed");
      setStatus({ kind: "error", text });
    }
  }

  async function signOut(everywhere: boolean) {
    setSigningOut(true);
    try {
      await onSignOut(everywhere);
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="account">
      <div className="account-id">
        <Avatar name={member.display_name} size={64} />
        <div>
          <p className="account-name">{member.display_name}</p>
          <p className="account-hints" dir="ltr">
            {[member.phone_hint, member.email_hint].filter(Boolean).join(" · ")}
          </p>
        </div>
      </div>

      <ul className="account-rows">
        <li className="account-row">
          {editingName ? (
            <form className="inline-edit" onSubmit={save}>
              <label className="field field-compact">
                <span className="field-label">{t("nameField")}</span>
                <input
                  data-autofocus
                  autoFocus
                  className="field-input"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder={t("namePlaceholder")}
                  maxLength={80}
                  autoComplete="name"
                />
              </label>
              <div className="inline-actions">
                <button type="button" className="btn-ghost" onClick={() => setEditingName(false)}>
                  {t("cancel")}
                </button>
                <button type="submit" className="btn-primary btn-small" disabled={!draft.trim() || status?.kind === "saving"}>
                  {t("save")}
                </button>
              </div>
            </form>
          ) : (
            <button type="button" className="row-button" onClick={startEdit}>
              <span className="row-text">
                <span className="field-label">{t("nameField")}</span>
                <span className="row-value">{member.display_name}</span>
              </span>
              <span className="row-action">{t("edit")}</span>
            </button>
          )}
        </li>
        <li className="account-row account-hints-row">
          <span className="field-label">{t("phoneHint")}</span>
          <span className="row-value" dir="ltr">
            {member.phone_hint ?? t("notSet")}
          </span>
          <span className="field-label">{t("emailHint")}</span>
          <span className="row-value" dir="ltr">
            {member.email_hint ?? t("notSet")}
          </span>
        </li>
      </ul>

      <p className="account-status" aria-live="polite">
        {status && (
          <span className={`status-${status.kind}`}>
            {status.kind === "saved" && <CheckIcon size={16} />} {status.text}
          </span>
        )}
      </p>

      <fieldset className="lang-choice">
        <legend className="field-label">{t("languageLabel")}</legend>
        <div className="segmented" role="radiogroup" aria-label={t("languageLabel")}>
          {LANGUAGES.map((option) => (
            <button
              key={option.code}
              type="button"
              role="radio"
              aria-checked={lang === option.code}
              lang={option.code}
              className="segment"
              onClick={() => onLang(option.code)}
            >
              {option.native}
            </button>
          ))}
        </div>
      </fieldset>

      {/* Device-only preference: stored in this browser, never sent to the identity service. */}
      <fieldset className="lang-choice">
        <legend className="field-label">{t("appearanceLabel")}</legend>
        <div className="segmented" role="radiogroup" aria-label={t("appearanceLabel")}>
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={theme === option.value}
              className="segment"
              data-theme-option={option.value}
              onClick={() => setTheme(option.value)}
            >
              {t(option.label)}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="account-quiet">
        <p className="privacy-cue">
          <LockIcon size={15} /> {t("privacyQuiet")}
        </p>
        <p className="module-note">{t("moduleDetailsNote")}</p>
      </div>

      <div className="account-signout">
        <button type="button" className="btn-secondary" onClick={() => void signOut(false)} disabled={signingOut}>
          <LogOutIcon size={20} /> {t("signOut")}
        </button>
        <AnimatePresence initial={false} mode="wait">
          {confirmEverywhere ? (
            <motion.div
              key="confirm"
              className="confirm-box"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <p>{t("signOutEverywhereConfirm")}</p>
              <div className="inline-actions">
                <button type="button" className="btn-ghost" onClick={() => setConfirmEverywhere(false)}>
                  {t("cancel")}
                </button>
                <button type="button" className="btn-danger" onClick={() => void signOut(true)} disabled={signingOut}>
                  {t("signOutEverywhereYes")}
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.button key="ask" type="button" className="btn-ghost btn-wide" onClick={() => setConfirmEverywhere(true)} exit={{ opacity: 0 }}>
              {t("signOutEverywhere")}
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
