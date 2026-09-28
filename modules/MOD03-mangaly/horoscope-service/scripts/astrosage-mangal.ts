import { existsSync, readFileSync, writeFileSync } from 'node:fs';

import { createDefaultEngine } from '../src/index.ts';
import { mulberry32 } from '../test/differential/corpus.ts';
import { astrosage } from './astrosage-check.ts';

/* Mangal Dosha calibration against AstroSage: random synthetic Hyderabad
 * births (seeded), each paired as groom with one fixed bride, recording
 * AstroSage's per-person Mangal level beside Mangaly's placements. Gentle
 * pace, resumable. */

const OUT = new URL('../test/fixtures/astrosage-mangal.json', import.meta.url);
const COUNT = Number(process.argv[2] ?? 40);
const engine = createDefaultEngine({ chartCacheTtlMs: 0 });
const rnd = mulberry32(4242);
const pad = (n: number) => String(n).padStart(2, '0');
const people: { date: string; time: string }[] = [];
while (people.length < COUNT) {
  const d = new Date(Date.UTC(1985, 0, 1) + Math.floor(rnd() * 15 * 365) * 86_400_000);
  people.push({ date: d.toISOString().slice(0, 10), time: `${pad(Math.floor(rnd() * 24))}:${pad(Math.floor(rnd() * 60))}` });
}
const bride = { date: '1996-06-15', time: '12:00' };

type Row = { person: { date: string; time: string }; astro: string | null; mangaly: unknown };
const done: { bride: typeof bride; rows: Row[] } = existsSync(OUT) ? JSON.parse(readFileSync(OUT, 'utf8')) : { bride, rows: [] };
const have = new Set(done.rows.map((r) => `${r.person.date} ${r.person.time}`));

for (const person of people) {
  if (have.has(`${person.date} ${person.time}`)) continue;
  const chart = engine.calculateChart({ birthDate: person.date, birthTime: person.time, birthTimePrecision: 'EXACT', birthLocation: 'Hyderabad', latitude: 17.3842, longitude: 78.4564, timezone: 'Asia/Kolkata' });
  let res;
  for (let a = 0; a < 3 && !res?.mangal; a++) {
    try { res = await astrosage([person.date, person.time], [bride.date, bride.time]); } catch { /* retry */ }
    if (!res?.mangal) await new Promise((r) => setTimeout(r, 8000));
  }
  const groomPart = /Mr\. Groom has\s+'([^']+)'/.exec(res?.mangal ?? '')?.[1]?.replace(/\s+/g, ' ') ?? (/Mr\. Groom and Ms\. Bride has\s+'([^']+)'/.exec(res?.mangal ?? '')?.[1]?.replace(/\s+/g, ' ') ?? null);
  done.rows.push({ person, astro: groomPart, mangaly: { input: chart.mangalInput } });
  writeFileSync(OUT, `${JSON.stringify(done, null, 1)}\n`);
  console.log(`${done.rows.length}/${COUNT} ${person.date} ${person.time} astro=${groomPart}`);
  await new Promise((r) => setTimeout(r, 4000));
}
console.log('complete');
