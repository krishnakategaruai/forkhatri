/* Phone photos are often 8 MB or more, and the server refuses anything over
 * 8 MB (or a type it does not know). Shrink and re-encode a chosen picture as a
 * JPEG on the member's own device before upload: a clear photo at 2048 px on
 * the long side is a few hundred KB, and re-encoding also drops the hidden
 * location and camera details a phone writes into every photo (EXIF). Anything
 * the browser cannot decode is returned unchanged, so the server decides. */

const MAX_SIDE = 2048;
const QUALITY = 0.86;
const SKIP_BELOW_BYTES = 300 * 1024;

export async function preparePhoto(file: File): Promise<File> {
  if (typeof window === 'undefined' || !file.type.startsWith('image/')) return file;
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
    // Small JPEGs already under the limit still go through, to lose EXIF.
    if (scale === 1 && file.type === 'image/jpeg' && file.size < SKIP_BELOW_BYTES) {
      bitmap.close();
      return file;
    }
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      bitmap.close();
      return file;
    }
    ctx.fillStyle = '#fff'; // a transparent PNG becomes white, not black
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITY));
    if (!blob || blob.size === 0) return file;
    const name = file.name.replace(/\.[^.]+$/, '') || 'photo';
    return new File([blob], `${name}.jpg`, { type: 'image/jpeg' });
  } catch {
    return file;
  }
}
