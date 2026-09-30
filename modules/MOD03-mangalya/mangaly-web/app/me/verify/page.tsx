"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { resolveMediaUrl, setManaging } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import {
  YAW,
  compareWithPhotos,
  liveDescriptor,
  loadFaceApi,
  readLive,
} from "@/lib/faceMatch";
import { getMemberProfile, listPhotos, uploadMemberPhoto, type Photo } from "@/lib/profile";
import {
  getVerification,
  monthYear,
  safeNext,
  submitFaceMatch,
  withdrawFaceMatch,
  type VerificationStatus,
} from "@/lib/verification";

import "./verify.css";

/* DEC-V1-016 / DEC-V1-025 · "Confirm your photos are you"
 *
 * One explanation and one unbundled consent, then the camera, a two-turn
 * liveness challenge, and a comparison with the member's own photos — all on
 * this device. Only the outcome is sent; the server applies the threshold. The
 * member sees pass or fail and a month, never a number.
 *
 * Layout: one column on a phone; from 900px the explanation and the camera
 * stage sit side by side with the steps, so a desktop is a real two-pane page
 * rather than a phone column in the middle of a monitor. */

type Move = "center" | "left" | "right" | "capture";
type FailReason = "noMatch" | "liveness" | "noFace" | "noFaceInPhotos";
type CameraProblem = "denied" | "unavailable" | "loadFailed";

type Phase =
  | { k: "loading" }
  | { k: "noProfile" }
  | { k: "noPhotos" }
  | { k: "intro" }
  | { k: "verified" }
  | { k: "preparing" }
  | { k: "challenge" }
  | { k: "comparing" }
  | { k: "passed"; at: string | null }
  | { k: "failed"; reason: FailReason }
  | { k: "camera"; problem: CameraProblem }
  | { k: "rateLimited" }
  | { k: "network" };

const CHALLENGE_TIMEOUT_MS = 30_000;

/** The two turns in a random order, so a recording made for one attempt does
 *  not simply play back into the next. */
function turnOrder(): Move[] {
  const bit = crypto.getRandomValues(new Uint8Array(1))[0] & 1;
  return bit ? ["left", "right"] : ["right", "left"];
}

export default function VerifyPage() {
  return (
    <Suspense fallback={null}>
      <VerifyFlow />
    </Suspense>
  );
}

function VerifyFlow() {
  const { t, i18n } = useTranslation(["verify", "common"]);
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));

  const [phase, setPhase] = useState<Phase>({ k: "loading" });
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [consent, setConsent] = useState(false);
  const [moves, setMoves] = useState<Move[]>([]);
  const [moveIndex, setMoveIndex] = useState(0);
  const [hint, setHint] = useState<"noFace" | "many" | null>(null);
  const [confirmWithdraw, setConfirmWithdraw] = useState(false);
  const [withdrawn, setWithdrawn] = useState(false);
  const [busy, setBusy] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const runningRef = useRef(false);
  const photosRef = useRef<Photo[]>([]);

  const stopCamera = useCallback(() => {
    runningRef.current = false;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  const [addingPhoto, setAddingPhoto] = useState(false);
  const load = useCallback(async () => {
    const s = await getVerification();
    if (!s) {
      setPhase({ k: "network" });
      return;
    }
    setStatus(s);
    if (!s.has_profile) setPhase({ k: "noProfile" });
    else if (!s.has_photos) setPhase({ k: "noPhotos" });
    else setPhase({ k: s.verified ? "verified" : "intro" });
  }, []);

  useEffect(() => {
    // A face check is always about the signed-in person, never about a
    // profile they are filling in for someone else.
    setManaging(null);
    let active = true;
    (async () => {
      const session = await requireSession();
      if (!active || !session) return;
      await load();
    })();
    return () => {
      active = false;
      stopCamera();
    };
  }, [load, stopCamera]);

  const leave = () => router.push(next ?? "/me");

  async function start() {
    setHint(null);
    setMoveIndex(0);
    const order = turnOrder();
    setMoves(["center", ...order, "capture"]);
    setPhase({ k: "preparing" });

    if (!navigator.mediaDevices?.getUserMedia) {
      setPhase({ k: "camera", problem: "unavailable" });
      return;
    }
    let faceapi: Awaited<ReturnType<typeof loadFaceApi>>;
    try {
      const [api, stream, photos] = await Promise.all([
        loadFaceApi(),
        navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        }),
        // [DEC-V1-027] A parent or relative is checked against their member photo.
        listPhotos().then(async (own) => {
          if (own.length > 0) return own;
          const m = await getMemberProfile();
          return m?.photo_url ? [{ id: "member", url: m.photo_url, is_primary: true } as Photo] : [];
        }),
      ]);
      faceapi = api;
      streamRef.current = stream;
      photosRef.current = photos.map((p) => ({
        ...p,
        url: resolveMediaUrl(p.url) ?? p.url,
      }));
      const video = videoRef.current;
      if (!video) throw new Error("video element missing");
      video.srcObject = stream;
      await video.play();
    } catch (err) {
      stopCamera();
      const name = err instanceof DOMException ? err.name : "";
      setPhase({
        k: "camera",
        problem:
          name === "NotAllowedError" || name === "SecurityError"
            ? "denied"
            : name === "NotFoundError" ||
                name === "OverconstrainedError" ||
                name === "NotReadableError"
              ? "unavailable"
              : "loadFailed",
      });
      return;
    }
    if (photosRef.current.length === 0) {
      stopCamera();
      setPhase({ k: "noPhotos" });
      return;
    }
    setPhase({ k: "challenge" });
    void runChallenge(faceapi, ["center", ...order, "capture"]);
  }

  async function runChallenge(
    faceapi: Awaited<ReturnType<typeof loadFaceApi>>,
    sequence: Move[],
  ) {
    const video = videoRef.current;
    if (!video) return;
    runningRef.current = true;
    const startedAt = performance.now();
    let index = 0;
    let streak = 0;
    const needed: Record<Move, number> = { center: 3, left: 2, right: 2, capture: 3 };

    while (runningRef.current && index < sequence.length) {
      if (performance.now() - startedAt > CHALLENGE_TIMEOUT_MS) {
        stopCamera();
        setPhase({ k: "failed", reason: "liveness" });
        return;
      }
      const reading = await readLive(faceapi, video);
      if (!runningRef.current) return;
      if (reading.faces === 0) {
        setHint("noFace");
        streak = 0;
      } else if (reading.faces > 1) {
        setHint("many");
        streak = 0;
      } else {
        setHint(null);
        const yaw = "yaw" in reading ? reading.yaw : 0.5;
        const move = sequence[index];
        const facing = yaw > YAW.facing[0] && yaw < YAW.facing[1];
        const ok =
          move === "left"
            ? yaw > YAW.left
            : move === "right"
              ? yaw < YAW.right
              : facing;
        streak = ok ? streak + 1 : 0;
        if (streak >= needed[move]) {
          if (move === "capture") break;
          index += 1;
          streak = 0;
          setMoveIndex(index);
        }
      }
      await new Promise((r) => setTimeout(r, 90));
    }
    if (!runningRef.current) return;

    const live = await liveDescriptor(faceapi, video);
    // The camera is done with the moment the live descriptor exists.
    stopCamera();
    if (!live) {
      setPhase({ k: "failed", reason: "noFace" });
      return;
    }
    setPhase({ k: "comparing" });
    const comparison = await compareWithPhotos(faceapi, live, photosRef.current);
    live.fill(0);
    if (comparison.kind === "noFaceInPhotos") {
      setPhase({ k: "failed", reason: "noFaceInPhotos" });
      return;
    }
    const result = await submitFaceMatch({
      distance: comparison.distance,
      livenessPassed: true,
      photosCompared: comparison.photosCompared,
    });
    if (!result.ok) {
      setPhase(
        result.kind === "rateLimited"
          ? { k: "rateLimited" }
          : result.kind === "noPhotos"
            ? { k: "noPhotos" }
            : { k: "network" },
      );
      return;
    }
    if (result.passed) {
      setStatus((s) => (s ? { ...s, verified: true, verified_at: result.verified_at } : s));
      setPhase({ k: "passed", at: result.verified_at });
    } else {
      setPhase({ k: "failed", reason: "noMatch" });
    }
  }

  function cancel() {
    stopCamera();
    setPhase({ k: status?.verified ? "verified" : "intro" });
  }

  async function withdraw() {
    setBusy(true);
    const ok = await withdrawFaceMatch();
    setBusy(false);
    setConfirmWithdraw(false);
    if (!ok) {
      setPhase({ k: "network" });
      return;
    }
    setWithdrawn(true);
    setConsent(false);
    await load();
  }

  const lang = i18n.language;
  const cameraOn =
    phase.k === "preparing" || phase.k === "challenge";
  const currentMove = moves[moveIndex] ?? "center";
  const progress = moves.length ? moveIndex / moves.length : 0;

  return (
    <>
      <header className="topbar">
        <button
          type="button"
          className="icon-btn"
          onClick={() => {
            stopCamera();
            leave();
          }}
          aria-label={t("common:action.back")}
        >
          ←
        </button>
        <h1>{t("verify:title")}</h1>
        <span style={{ width: 44 }} aria-hidden="true" />
      </header>

      <main className="screen verify">
        {phase.k === "loading" && (
          <p className="caption verify__loading">{t("common:state.loading")}</p>
        )}

        {(phase.k === "intro" || phase.k === "verified") && (
          <div className="verify__grid">
            <section className="verify__lead">
              <span className="verify__eyebrow">{t("verify:intro.eyebrow")}</span>
              <h2 className="verify__heading">{t("verify:intro.heading")}</h2>
              <p className="verify__body">{t("verify:intro.body")}</p>

              {withdrawn && (
                <p className="verify__note" role="status">
                  {t("verify:verified.withdrawn")}
                </p>
              )}

              {phase.k === "verified" && status?.verified ? (
                <div className="verify__fact card">
                  <span className="verify__seal" aria-hidden="true">
                    <SealIcon />
                  </span>
                  <div className="verify__fact-text">
                    <strong>
                      {t("verify:verified.fact", {
                        date: monthYear(status.verified_at, lang),
                      })}
                    </strong>
                    <span className="caption">
                      {t("verify:verified.until", {
                        date: monthYear(status.expires_at, lang),
                      })}
                    </span>
                  </div>
                  <div className="verify__fact-actions">
                    {next && (
                      <button
                        type="button"
                        className="btn btn--primary"
                        onClick={leave}
                      >
                        {t("verify:passed.continue")}
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={() => setPhase({ k: "intro" })}
                    >
                      {t("verify:verified.redo")}
                    </button>
                    {confirmWithdraw ? (
                      <span className="verify__confirm">
                        <span>{t("verify:verified.withdrawConfirm")}</span>
                        <button
                          type="button"
                          className="btn btn--ghost"
                          disabled={busy}
                          onClick={() => void withdraw()}
                        >
                          {t("verify:verified.withdrawYes")}
                        </button>
                        <button
                          type="button"
                          className="link link--button"
                          onClick={() => setConfirmWithdraw(false)}
                        >
                          {t("verify:verified.withdrawNo")}
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="link link--button"
                        onClick={() => setConfirmWithdraw(true)}
                      >
                        {t("verify:verified.withdraw")}
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <form
                  className="verify__consent"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (consent) void start();
                  }}
                >
                  <label className="verify__check">
                    <input
                      type="checkbox"
                      checked={consent}
                      onChange={(e) => setConsent(e.target.checked)}
                    />
                    <span>{t("verify:intro.consent")}</span>
                  </label>
                  <button
                    type="submit"
                    className="btn btn--primary verify__start"
                    disabled={!consent}
                  >
                    {t("verify:intro.start")}
                  </button>
                  <p className="caption">{t("verify:intro.tips")}</p>
                </form>
              )}
            </section>

            <ol className="verify__points">
              {(["1", "2", "3"] as const).map((n) => (
                <li key={n} className="verify__point">
                  <span className="verify__point-num" aria-hidden="true">
                    {n}
                  </span>
                  <span className="verify__point-text">
                    <strong>{t(`verify:intro.point${n}Title`)}</strong>
                    <span>{t(`verify:intro.point${n}`)}</span>
                  </span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* The stage stays mounted while the camera is on so the <video>
            exists before the stream is attached. */}
        {cameraOn && (
          <div className="verify__grid verify__grid--stage">
            <div className="verify__stage">
              <div
                className="verify__ring"
                style={{ ["--progress" as string]: `${Math.round(progress * 100)}%` }}
              >
                <video
                  ref={videoRef}
                  className="verify__video"
                  playsInline
                  muted
                  aria-label={t("verify:camera.videoLabel")}
                />
              </div>
            </div>
            <section className="verify__panel" aria-live="polite">
              {phase.k === "preparing" ? (
                <p className="verify__instruction">{t("verify:camera.preparing")}</p>
              ) : (
                <>
                  <span className="caption">
                    {t("verify:step.progress", {
                      current: Math.min(moveIndex + 1, moves.length),
                      total: moves.length,
                    })}
                  </span>
                  <p className="verify__instruction">
                    {currentMove === "left" && <span aria-hidden="true">← </span>}
                    {t(`verify:step.${currentMove}`)}
                    {currentMove === "right" && <span aria-hidden="true"> →</span>}
                  </p>
                  <p className="verify__hint">
                    {hint ? t(`verify:step.${hint}`) : " "}
                  </p>
                  <ol className="verify__moves">
                    {moves.map((m, i) => (
                      <li
                        key={`${m}-${i}`}
                        className={`verify__move${i < moveIndex ? " is-done" : ""}${i === moveIndex ? " is-current" : ""}`}
                      >
                        <span className="verify__tick" aria-hidden="true" />
                        {t(`verify:step.${m}`)}
                      </li>
                    ))}
                  </ol>
                </>
              )}
              <button type="button" className="link link--button" onClick={cancel}>
                {t("verify:step.cancel")}
              </button>
            </section>
          </div>
        )}

        {phase.k === "comparing" && (
          <div className="verify__result">
            <span className="verify__pulse" aria-hidden="true" />
            <p className="verify__instruction">{t("verify:comparing")}</p>
          </div>
        )}

        {phase.k === "passed" && (
          <div className="verify__result card">
            <span className="verify__seal verify__seal--lg" aria-hidden="true">
              <SealIcon />
            </span>
            <h2 className="verify__heading">{t("verify:passed.title")}</h2>
            <p className="verify__date">{monthYear(phase.at, lang)}</p>
            <p className="verify__body">{t("verify:passed.body")}</p>
            <button type="button" className="btn btn--primary" onClick={leave}>
              {next ? t("verify:passed.continue") : t("verify:passed.done")}
            </button>
          </div>
        )}

        {phase.k === "failed" && (
          <Outcome
            title={t(`verify:failed.${phase.reason}.title`)}
            body={t(`verify:failed.${phase.reason}.body`)}
          >
            {phase.reason === "noFaceInPhotos" ? (
              <Link href="/me" className="btn btn--primary">
                {t("verify:failed.noFaceInPhotos.cta")}
              </Link>
            ) : (
              <button type="button" className="btn btn--primary" onClick={() => void start()}>
                {t("verify:failed.retry")}
              </button>
            )}
            <p className="caption">{t("verify:failed.help")}</p>
          </Outcome>
        )}

        {phase.k === "camera" && (
          <Outcome
            title={t(`verify:camera.${phase.problem}.title`)}
            body={t(`verify:camera.${phase.problem}.body`)}
          >
            {phase.problem !== "unavailable" && (
              <button type="button" className="btn btn--primary" onClick={() => void start()}>
                {t("verify:failed.retry")}
              </button>
            )}
          </Outcome>
        )}

        {/* [Owner walkthrough, 2026-09-30] A father making his son's profile
            has no Mangalya profile and no photos of his own, and was sent to
            "My profile" — which would make him a matrimony profile of his
            own. The photo the check compares against is added right here
            instead, as his member photo (a selfie on a phone), and the check
            continues from this screen. */}
        {(phase.k === "noPhotos" || phase.k === "noProfile") && (
          <Outcome title={t("verify:addSelf.title")} body={t("verify:addSelf.body")}>
            <label className="btn btn--primary verify-addself">
              {addingPhoto ? t("verify:addSelf.saving") : t("verify:addSelf.cta")}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                capture="user"
                hidden
                disabled={addingPhoto}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setAddingPhoto(true);
                  const saved = await uploadMemberPhoto(file);
                  setAddingPhoto(false);
                  if (saved) await load();
                  else setPhase({ k: "network" });
                }}
              />
            </label>
          </Outcome>
        )}


        {phase.k === "rateLimited" && (
          <Outcome title={t("verify:rateLimited.title")} body={t("verify:rateLimited.body")} />
        )}

        {phase.k === "network" && (
          <Outcome title={t("verify:error.network")} body="">
            <button type="button" className="btn btn--primary" onClick={() => void load()}>
              {t("verify:failed.retry")}
            </button>
          </Outcome>
        )}
      </main>
    </>
  );
}

function Outcome({
  title,
  body,
  children,
}: {
  title: string;
  body: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="verify__result card" role="status">
      <h2 className="verify__heading verify__heading--sm">{title}</h2>
      {body && <p className="verify__body">{body}</p>}
      {children}
    </div>
  );
}

function SealIcon() {
  return (
    <svg viewBox="0 0 24 24" width="100%" height="100%">
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 3l2.1 1.5 2.6-.2.9 2.4 2.2 1.4-.7 2.5.7 2.5-2.2 1.4-.9 2.4-2.6-.2L12 18l-2.1-1.5-2.6.2-.9-2.4-2.2-1.4.7-2.5-.7-2.5 2.2-1.4.9-2.4 2.6.2L12 3z M8.8 10.9l2.2 2.2 4.2-4.2"
      />
    </svg>
  );
}
