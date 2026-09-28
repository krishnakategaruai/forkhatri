import { readFileSync } from 'node:fs';
import { scorePorutham } from '../src/domain/poruthamRules.ts';
import { PORUTHAM_ORDER } from '../src/domain/types.ts';

/* Compares Mangaly's Porutham rules with the ProKerala calibration file and
 * prints every disagreement, grouped by porutham. */
const f = JSON.parse(readFileSync(new URL('../test/fixtures/prokerala-porutham.json', import.meta.url), 'utf8'));
// ProKerala option value: "k" (0-based star) or "k-p" (star, 0-based pada) → rashi from the pada's longitude.
const moon = (v: string) => {
  const [k, p] = v.split('-').map(Number);
  const pada = p ?? 0;
  const lon = (k! * 360) / 27 + (pada + 0.5) * (360 / 108);
  return { nakshatra: k! + 1, rashi: Math.floor(lon / 30) + 1 };
};
const NAME: Record<string, string> = { 'Dina Porutham': 'DINA', 'Gana Porutham': 'GANA', 'Mahendra Porutham': 'MAHENDRA', 'Stree Deergha Porutham': 'STREE_DEERGHA', 'Yoni Porutham': 'YONI', 'Veda Porutham': 'VEDHA', 'Rajju Porutham': 'RAJJU', 'Rasi Porutham': 'RASI', 'Rasiyathipathi Porutham': 'RASI_ADHIPATHI', 'Vasya Porutham': 'VASYA' };
const bad: Record<string, string[]> = {};
let total = 0, totalBad = 0;
for (const row of f.rows) {
  const g = moon(row.girl), b = moon(row.boy);
  const ours = Object.fromEntries(scorePorutham(g, b).map((i) => [i.porutham, i]));
  let sumP = 0, sumO = 0;
  for (const p of row.poruthams) {
    const key = NAME[p.name]!; const o = ours[key]!;
    sumP += p.points; sumO += o.agrees ? 1 : 0;
    if ((p.points > 0) !== o.agrees || (p.points !== 0 && p.points !== 1)) (bad[key] ??= []).push(`girl ${row.girl}(${g.nakshatra}/${g.rashi}) boy ${row.boy}(${b.nakshatra}/${b.rashi}) pk=${p.points}[${p.girl}|${p.boy}] ours=${o.agrees}`);
  }
  total++; if (sumP !== sumO) totalBad++;
}
console.log(`pairs ${total}, totals differing ${totalBad}`);
for (const k of PORUTHAM_ORDER) console.log(k.padEnd(16), (bad[k]?.length ?? 0), (bad[k] ?? []).slice(0, 4).join('\n                  '));
