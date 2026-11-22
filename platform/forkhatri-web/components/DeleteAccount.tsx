"use client";

/**
 * "Delete my ForKhatri account" (docs/ParentApp/ACCOUNT-DELETION.md, kind A).
 * One flow in one sheet: what goes and what stays, re-authentication (password or a
 * fresh one-time code), typed DELETE, then live progress per module and a final receipt.
 * The server signs the member out the moment deletion starts, so progress and the
 * receipt are read from a public status address keyed by the job id.
 */
import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ApiError,
  identity,
  NetworkError,
  type CodeChallenge,
  type DeletePreview,
  type DeletionModule,
  type DeletionStatus,
} from "@/lib/api";
import { errorText, type MessageKey, type Translate } from "@/lib/i18n";
import { CheckIcon } from "./ui";

type Props = { t: Translate; onStarted: () => void; onFinished: () => void };

const STATUS_LABEL: Record<DeletionModule["status"], MessageKey> = {
  pending: "deleteStatusPending",
  running: "deleteStatusRunning",
  done: "deleteStatusDone",
  nothing_to_delete: "deleteStatusNothing",
  partial: "deleteStatusRetry",
  failed: "deleteStatusRetry",
};

function describe(t: Translate, error: unknown): string {
  if (error instanceof NetworkError) return t("err_network");
  if (error instanceof ApiError) return errorText(t, error.code, error.retryAfter);
  return t("err_unknown");
}

export default function DeleteAccount({ t, onStarted, onFinished }: Props) {
  const [preview, setPreview] = useState<DeletePreview | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [useCode, setUseCode] = useState(false);
  const [challenge, setChallenge] = useState<CodeChallenge | null>(null);
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<DeletionStatus | null>(null);

  useEffect(() => {
    identity
      .deletePreview()
      .then((value) => {
        setPreview(value);
        setUseCode(!value.has_password);
      })
      .catch((caught) => setLoadError(describe(t, caught)));
  }, [t]);

  // Progress: poll the public status until the receipt exists.
  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    const tick = async () => {
      try {
        const value = await identity.deletionStatus(jobId);
        if (stop) return;
        setProgress(value);
        if (value.status === "done") return;
      } catch {
        /* a blip: keep polling */
      }
      if (!stop) window.setTimeout(tick, 1200);
    };
    void tick();
    return () => {
      stop = true;
    };
  }, [jobId]);

  const moduleNames = useMemo(() => preview?.modules.map((m) => m.name).join(", ") ?? "", [preview]);
  const reauthReady = useCode ? Boolean(challenge) && /^\d{6}$/.test(code) : password.length > 0;
  const canDelete = typed === "DELETE" && reauthReady && !busy && !preview?.blocked;

  async function sendCode() {
    setBusy(true);
    setError(null);
    try {
      setChallenge(await identity.deleteCode());
    } catch (caught) {
      setError(describe(t, caught));
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!canDelete) return;
    setBusy(true);
    setError(null);
    try {
      const started = await identity.deleteAccount({
        confirm: "DELETE",
        ...(useCode ? { challenge_id: challenge!.challenge_id, code } : { password }),
      });
      setJobId(started.job_id);
      onStarted();
    } catch (caught) {
      setError(describe(t, caught));
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------------ done / progress
  if (jobId) {
    const done = progress?.status === "done";
    return (
      <div className="del" data-state={done ? "done" : "working"}>
        <h3 className="del-title">{done ? t("deleteDoneTitle") : t("deleteProgressTitle")}</h3>
        <p className="del-note" aria-live="polite">
          {done ? t("deleteDoneBody") : progress && progress.modules.some((m) => m.attempts > 1) ? t("deleteStillFinishing") : t("deleteProgressNote")}
        </p>
        <ul className="del-modules">
          {(progress?.modules ?? []).map((m) => {
            const items = Object.values(m.deleted).reduce((a, b) => a + b, 0);
            const ok = m.status === "done" || m.status === "nothing_to_delete";
            return (
              <li key={m.module} data-status={m.status}>
                <span className="del-module-name">{m.name}</span>
                <span className="del-module-state">
                  {ok && <CheckIcon size={15} />} {t(STATUS_LABEL[m.status])}
                  {ok && items > 0 ? ` · ${t("deleteItems", { n: items })}` : ""}
                </span>
              </li>
            );
          })}
        </ul>
        {done && progress?.receipt && (
          <>
            <p className="del-kept">{t("deleteKeptHeading")}</p>
            <ul className="del-list">
              {progress.receipt.retained.map((r, index) => (
                <li key={index}>{r.reason}</li>
              ))}
            </ul>
            <p className="del-ref" dir="ltr">
              {t("deleteReceiptRef", { code: progress.receipt.tombstone.slice(0, 12) })}
            </p>
            <button type="button" className="btn-primary btn-wide" onClick={onFinished} data-autofocus>
              {t("deleteFinish")}
            </button>
          </>
        )}
      </div>
    );
  }

  // ------------------------------------------------------------------ confirmation
  if (loadError) return <p className="status-error">{loadError}</p>;
  if (!preview) return <p className="del-note">{t("loadingLabel")}</p>;

  return (
    <form className="del" onSubmit={submit}>
      <p className="del-note">{t("deleteIntro")}</p>

      <h3 className="del-heading">{t("deleteWhatTitle")}</h3>
      <ul className="del-list">
        <li>{t("deleteWhatId")}</li>
        <li>{t("deleteWhatModules", { modules: moduleNames })}</li>
        <li>{t("deleteWhatOthers")}</li>
        <li>{t("deleteWhatOwned")}</li>
      </ul>

      <h3 className="del-heading">{t("deleteRetainedTitle")}</h3>
      <ul className="del-list">
        <li>{t("deleteRetainedPay")}</li>
        <li>{t("deleteRetainedSafety")}</li>
        <li>{t("deleteRetainedLogs")}</li>
      </ul>

      {preview.blocked ? (
        <p className="status-error">{t("deleteBlockedAdmin")}</p>
      ) : (
        <>
          {useCode ? (
            <div className="del-reauth">
              {!challenge ? (
                <button type="button" className="btn-secondary" onClick={() => void sendCode()} disabled={busy}>
                  {t("deleteSendCode", { destination: preview.destination_hint ?? "" })}
                </button>
              ) : (
                <label className="field field-compact">
                  <span className="field-label">
                    {t("deleteCodeSent", { destination: challenge.destination_hint })}
                    {challenge.dev_code ? ` (${t("devCode")}: ${challenge.dev_code})` : ""}
                  </span>
                  <input
                    className="field-input"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    value={code}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))}
                    placeholder={t("deleteCodeLabel")}
                    dir="ltr"
                  />
                </label>
              )}
              {preview.has_password && (
                <button type="button" className="btn-ghost" onClick={() => setUseCode(false)}>
                  {t("deleteUsePassword")}
                </button>
              )}
            </div>
          ) : (
            <div className="del-reauth">
              <label className="field field-compact">
                <span className="field-label">{t("deletePassword")}</span>
                <input
                  className="field-input"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {preview.destination_hint && (
                <button type="button" className="btn-ghost" onClick={() => setUseCode(true)}>
                  {t("deleteUseCode")}
                </button>
              )}
            </div>
          )}

          <label className="field field-compact">
            <span className="field-label">{t("deleteTypeLabel")}</span>
            <input
              className="field-input"
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              autoComplete="off"
              autoCapitalize="characters"
              dir="ltr"
            />
          </label>

          {error && (
            <p className="status-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="btn-delete" disabled={!canDelete}>
            {busy ? t("deleteWorking") : t("deleteButton")}
          </button>
        </>
      )}
    </form>
  );
}
