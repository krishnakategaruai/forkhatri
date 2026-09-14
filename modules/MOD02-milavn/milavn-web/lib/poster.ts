/* Share poster (thesis §43 — sharing through WhatsApp, Instagram, SMS…): a
 * 1080×1350 image drawn on the device from the activity's own cover, title,
 * date, place, host and a QR of the public link. It is what people forward
 * on WhatsApp status and Instagram stories — a link alone is not. Nothing is
 * uploaded; the canvas stays local. */

import QR from 'qrcode';

export type PosterInput = { title: string; when: string; place: string; host: string; url: string; coverUrl: string | null; category: string; trustLabel: string };

function wrap(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, maxWidth: number, lineHeight: number, maxLines: number): number {
  const words = text.split(/\s+/); let line = ''; let lines = 0;
  for (let i = 0; i < words.length; i++) {
    const test = line ? `${line} ${words[i]}` : words[i];
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(lines === maxLines - 1 ? `${line}…` : line, x, y); y += lineHeight; lines++; line = words[i];
      if (lines >= maxLines) return y;
    } else line = test;
  }
  if (line && lines < maxLines) { ctx.fillText(line, x, y); y += lineHeight; }
  return y;
}

function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => { const img = new Image(); img.crossOrigin = 'anonymous'; img.onload = () => resolve(img); img.onerror = () => resolve(null); img.src = src; });
}

export async function renderPoster(input: PosterInput): Promise<Blob | null> {
  const W = 1080, H = 1350;
  const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d'); if (!ctx) return null;
  // Backdrop: navy with the cover blown up and darkened.
  ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, W, H);
  const cover = input.coverUrl ? await loadImage(input.coverUrl) : null;
  if (cover) {
    const scale = Math.max(W / cover.width, H / cover.height); const cw = cover.width * scale, ch = cover.height * scale;
    ctx.drawImage(cover, (W - cw) / 2, (H - ch) / 2, cw, ch);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(11,18,32,0.25)'); g.addColorStop(0.45, 'rgba(11,18,32,0.35)'); g.addColorStop(1, 'rgba(11,18,32,0.96)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  // Eyebrow + trust.
  ctx.fillStyle = '#ffd08a'; ctx.font = '700 34px system-ui, sans-serif'; ctx.fillText(input.category.toUpperCase(), 72, 780);
  ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.font = '600 30px system-ui, sans-serif'; ctx.fillText(`✓ ${input.trustLabel}`, 72 + ctx.measureText(input.category.toUpperCase()).width + 40, 780);
  // Title.
  ctx.fillStyle = '#ffffff'; ctx.font = '800 76px system-ui, sans-serif';
  const y = wrap(ctx, input.title, 72, 870, W - 144, 84, 3);
  // Date pill.
  ctx.font = '700 36px system-ui, sans-serif'; const dw = ctx.measureText(input.when).width + 48;
  const pg = ctx.createLinearGradient(72, 0, 72 + dw, 0); pg.addColorStop(0, '#f0a94a'); pg.addColorStop(1, '#d97f22');
  ctx.fillStyle = pg; ctx.beginPath(); ctx.roundRect(72, y + 6, dw, 62, 31); ctx.fill();
  ctx.fillStyle = '#0b1220'; ctx.fillText(input.when, 96, y + 49);
  // Place + host.
  ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.font = '500 36px system-ui, sans-serif'; ctx.fillText(input.place, 72, y + 130);
  ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.font = '500 30px system-ui, sans-serif'; ctx.fillText(`Hosted by ${input.host} · Milavn`, 72, y + 182);
  // QR bottom-right.
  try {
    const qr = await QR.toDataURL(input.url, { width: 220, margin: 1, color: { dark: '#0b1220', light: '#ffffff' } });
    const qi = await loadImage(qr);
    if (qi) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.roundRect(W - 72 - 236, H - 72 - 236, 236, 236, 24); ctx.fill(); ctx.drawImage(qi, W - 72 - 228, H - 72 - 228, 220, 220); }
  } catch { /* poster without QR is still a poster */ }
  // Brand mark.
  ctx.fillStyle = '#f0a94a'; ctx.font = '800 34px system-ui, sans-serif'; ctx.fillText('M', 84, 96);
  ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.font = '600 30px system-ui, sans-serif'; ctx.fillText('milavn · what’s happening around you', 132, 96);
  return new Promise((resolve) => canvas.toBlob((b) => resolve(b), 'image/png'));
}
