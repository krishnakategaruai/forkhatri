import { PrisriJyotishProvider } from '../src/provider/prisri/PrisriJyotishProvider.ts';
import { placementFromLongitude, distanceToBoundary } from '../src/domain/zodiac.ts';

/* Finds a Hyderabad birth (IST, whole minute) whose Moon sits at a target
 * sidereal longitude, far from any boundary, for checking koota tables
 * against a reference site. Synthetic births only. */
const p = new PrisriJyotishProvider();
const cfg = { zodiacSystem: 'SIDEREAL', ayanamsha: 'LAHIRI', houseSystem: 'WHOLE_SIGN' } as const;
const targets: Record<string, number> = { A: 6.67, B: 46.67, C: 220, D: 100, E: 73.33, F: 126.67, G: 166.67, H: 20, I: 261.67, K: 35 };
const out: Record<string, unknown> = {};
for (const [k, target] of Object.entries(targets)) {
  let best: { ms: number; lon: number } | null = null;
  for (let ms = Date.UTC(1995, 0, 1); ms < Date.UTC(1996, 0, 1); ms += 3_600_000) {
    const lon = p.calculateChart({ instantUtc: new Date(ms).toISOString(), latitude: 17.385, longitude: 78.4867, elevationMeters: 0 }, cfg).grahas.MOON.siderealLongitude;
    const d = Math.abs(lon - target);
    if (d < 0.4 && (!best || d < Math.abs(best.lon - target))) best = { ms, lon };
    if (best && d < 0.3) break;
  }
  if (!best) throw new Error(k);
  const ist = new Date(best.ms + 5.5 * 3_600_000).toISOString();
  out[k] = { istDate: ist.slice(0, 10), istTime: ist.slice(11, 16), moon: +best.lon.toFixed(2), place: placementFromLongitude(best.lon), margin: +distanceToBoundary(best.lon).toFixed(2) };
}
console.log(JSON.stringify(out, null, 1));
