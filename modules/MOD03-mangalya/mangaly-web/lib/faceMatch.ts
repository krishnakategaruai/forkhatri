/* The in-browser half of the live face match — DEC-V1-016.
 *
 * Everything biometric happens here, on the member's own device, and is
 * thrown away when the check ends: camera frames are read straight from the
 * <video> element and never drawn to a kept canvas, uploaded or stored; face
 * descriptors (128 numbers per face) live only in local variables. What leaves
 * this file is one number — the worst photo's best-face distance — plus
 * whether the liveness challenge passed. The server applies the threshold.
 *
 * Honest limits (recorded in DEC-V1-016/025): an active challenge (turn left,
 * turn right) is defeatable by a good video replay, and a client-side
 * comparison can be tampered with by anyone who edits this code. The strict
 * server-side threshold, rate limiting and human review are the v1 answer; no
 * vendor, no stored faces.
 *
 * Models (`public/models/face-api/`, copied from @vladmandic/face-api's
 * `model/` folder): Tiny Face Detector for the fast liveness loop, SSD
 * MobileNet v1 for the more careful detection behind each descriptor, the
 * 68-point landmark model, and the ResNet-34-style recognition model. */

type FaceApi = typeof import('@vladmandic/face-api');

const MODEL_URL = '/models/face-api';

let loading: Promise<FaceApi> | null = null;

/** Load the library and the four models once per page. */
export function loadFaceApi(): Promise<FaceApi> {
  if (!loading) {
    loading = (async () => {
      const faceapi = await import('@vladmandic/face-api');
      // The bundled tfjs is typed without its engine functions; these two
      // exist at runtime (the package's own demo calls them).
      const tf = faceapi.tf as unknown as {
        setBackend(name: string): Promise<boolean>;
        ready(): Promise<void>;
      };
      try {
        await tf.setBackend('webgl');
      } catch {
        /* falls back to whatever backend tfjs picks (cpu/wasm) */
      }
      await tf.ready();
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
      ]);
      return faceapi;
    })().catch((err) => {
      loading = null;
      throw err;
    });
  }
  return loading;
}

export type LiveReading =
  | { faces: 0 }
  | { faces: number; yaw: number };

/**
 * One quick reading of the live video: how many faces, and for a single face a
 * yaw ratio — where the nose tip sits between the two ends of the jaw line.
 * About 0.5 when facing the camera. Frames come from the camera un-mirrored,
 * so the person's own left is the image's right: turning to THEIR left moves
 * the nose toward the image's right and the ratio rises above 0.5.
 */
export async function readLive(faceapi: FaceApi, video: HTMLVideoElement): Promise<LiveReading> {
  const found = await faceapi
    .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 }))
    .withFaceLandmarks();
  if (found.length === 0) return { faces: 0 };
  if (found.length > 1) return { faces: found.length, yaw: 0.5 };
  const pts = found[0].landmarks.positions;
  const jawStart = pts[0];
  const jawEnd = pts[16];
  const nose = pts[30];
  const width = jawEnd.x - jawStart.x;
  if (width <= 0) return { faces: 1, yaw: 0.5 };
  return { faces: 1, yaw: (nose.x - jawStart.x) / width };
}

/** Thresholds for the challenge. Generous: this is a gesture, not a test. */
export const YAW = { facing: [0.4, 0.6] as const, left: 0.64, right: 0.36 };

/**
 * A descriptor for the live face, averaged over a few frames so one blurred
 * frame does not decide the result. Null if a single clear face was not seen.
 */
export async function liveDescriptor(
  faceapi: FaceApi,
  video: HTMLVideoElement,
  frames = 3,
): Promise<Float32Array | null> {
  const samples: Float32Array[] = [];
  for (let i = 0; i < frames * 2 && samples.length < frames; i++) {
    const all = await faceapi
      .detectAllFaces(video, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.6 }))
      .withFaceLandmarks()
      .withFaceDescriptors();
    if (all.length === 1) samples.push(all[0].descriptor);
    await new Promise((r) => setTimeout(r, 120));
  }
  if (samples.length === 0) return null;
  const mean = new Float32Array(samples[0].length);
  for (const s of samples) for (let i = 0; i < s.length; i++) mean[i] += s[i] / samples.length;
  samples.length = 0;
  return mean;
}

/** Every face in one of the member's own photos, as descriptors. */
async function photoDescriptors(faceapi: FaceApi, url: string): Promise<Float32Array[]> {
  // The photo is served only to its owner, from the API's own origin, so it is
  // fetched with the session cookie and decoded from a short-lived object URL:
  // the model can then read its pixels without a cross-origin (tainted) image.
  const res = await fetch(url, { credentials: 'include', cache: 'no-store' });
  if (!res.ok) return [];
  const objectUrl = URL.createObjectURL(await res.blob());
  try {
    const img = new Image();
    img.src = objectUrl;
    await img.decode();
    const found = await faceapi
      .detectAllFaces(img, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.5 }))
      .withFaceLandmarks()
      .withFaceDescriptors();
    return found.map((f) => f.descriptor);
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export type Comparison =
  | { kind: 'compared'; distance: number; photosCompared: number }
  | { kind: 'noFaceInPhotos' };

/**
 * Compare the live face with the member's photos. For each photo the CLOSEST
 * face counts (a group photo is fine as long as the person is in it); the
 * result is the FARTHEST of those — every photo that shows a face must show
 * this person. The main photo must show a face. Photos with no face at all
 * (a landscape, a pet) make no claim about a person and are skipped.
 */
export async function compareWithPhotos(
  faceapi: FaceApi,
  live: Float32Array,
  photos: { url: string; is_primary: boolean }[],
): Promise<Comparison> {
  let worst = 0;
  let compared = 0;
  for (const photo of photos) {
    const faces = await photoDescriptors(faceapi, photo.url);
    if (faces.length === 0) {
      if (photo.is_primary) return { kind: 'noFaceInPhotos' };
      continue;
    }
    const best = Math.min(...faces.map((f) => faceapi.euclideanDistance(live, f)));
    worst = Math.max(worst, best);
    compared += 1;
  }
  if (compared === 0) return { kind: 'noFaceInPhotos' };
  return { kind: 'compared', distance: worst, photosCompared: compared };
}
