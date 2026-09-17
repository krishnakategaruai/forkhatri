/* Live expressions, Snapchat-style, done the privacy-by-design way: the front
 * camera is analysed ON THE DEVICE with MediaPipe's face landmarker
 * (blendshapes); only a word — "smile", "laugh", "surprised", "wink",
 * "thinking", "love", "neutral" — ever leaves the phone, as the person's
 * current expression next to their messages. No frame is stored or sent.
 * Opt-in per chat; the camera indicator is always visible while it runs. */

export type Expression = 'smile' | 'laugh' | 'surprised' | 'wink' | 'thinking' | 'love' | 'neutral';
export const EXPRESSION_EMOJI: Record<Expression, string> = { smile: '😊', laugh: '😂', surprised: '😮', wink: '😉', thinking: '🤔', love: '😍', neutral: '🙂' };
export const EXPRESSIONS: Expression[] = ['smile', 'laugh', 'surprised', 'wink', 'thinking', 'love', 'neutral'];

type Blend = Record<string, number>;

export function classify(b: Blend): Expression {
  const smile = ((b.mouthSmileLeft ?? 0) + (b.mouthSmileRight ?? 0)) / 2;
  const jaw = b.jawOpen ?? 0;
  const browUp = b.browInnerUp ?? 0;
  const browDown = ((b.browDownLeft ?? 0) + (b.browDownRight ?? 0)) / 2;
  const blinkL = b.eyeBlinkLeft ?? 0, blinkR = b.eyeBlinkRight ?? 0;
  const pucker = b.mouthPucker ?? 0;
  if (Math.abs(blinkL - blinkR) > 0.45 && Math.max(blinkL, blinkR) > 0.55) return 'wink';
  if (jaw > 0.45 && smile > 0.35) return 'laugh';
  if (jaw > 0.5 && browUp > 0.35) return 'surprised';
  if (pucker > 0.5 && smile > 0.2) return 'love';
  if (smile > 0.35) return 'smile';
  if (browDown > 0.4) return 'thinking';
  return 'neutral';
}

export type ExpressionSession = { stop: () => void };

/** MediaPipe's WASM prints routine "INFO: …" lines through console.error, which the Next dev overlay counts as an Issue. Drop only those. */
function quietMediaPipeInfo(): () => void {
  const original = console.error;
  console.error = (...args: unknown[]) => { if (typeof args[0] === 'string' && args[0].startsWith('INFO:')) return; original(...args); };
  return () => { console.error = original; };
}

/** Starts the camera + landmarker and calls `onChange` as soon as a new expression holds for two readings in a row (~0.4 s): live, without frame-to-frame flicker. */
export async function startExpressions(video: HTMLVideoElement, onChange: (e: Expression) => void, onError: (msg: string) => void): Promise<ExpressionSession | null> {
  let stream: MediaStream | null = null;
  let raf = 0;
  let stopped = false;
  const restoreConsole = quietMediaPipeInfo();
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 320, height: 240 }, audio: false });
    video.srcObject = stream;
    await video.play();
    const vision = await import('@mediapipe/tasks-vision');
    const files = await vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm');
    const landmarker = await vision.FaceLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', delegate: 'GPU' },
      outputFaceBlendshapes: true, runningMode: 'VIDEO', numFaces: 1,
    });
    let last: Expression | null = null; let candidate: Expression | null = null; let streak = 0; let lastAt = 0;
    const tick = () => {
      if (stopped) return;
      const now = performance.now();
      if (video.readyState >= 2 && now - lastAt > 200) {
        lastAt = now;
        try {
          const r = landmarker.detectForVideo(video, now);
          const shapes = r.faceBlendshapes?.[0]?.categories;
          if (shapes) {
            const b: Blend = {}; for (const c of shapes) b[c.categoryName] = c.score;
            const e = classify(b);
            streak = e === candidate ? streak + 1 : 1; candidate = e;
            if (streak >= 2 && e !== last) { last = e; onChange(e); }
          }
        } catch { /* a dropped frame is fine */ }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return {
      stop: () => { stopped = true; cancelAnimationFrame(raf); landmarker.close(); stream?.getTracks().forEach((t) => t.stop()); video.srcObject = null; restoreConsole(); },
    };
  } catch (e) {
    restoreConsole();
    stream?.getTracks().forEach((t) => t.stop());
    onError(e instanceof Error ? e.message : 'camera');
    return null;
  }
}
