import { readFileSync } from 'node:fs';

/* For each porutham, finds which inputs ProKerala's result is a function of
 * (star count, sign count, class pairs, star pair…) and prints the mapping,
 * so Mangaly's rule can be written exactly. Reads the calibration fixture. */
const f = JSON.parse(readFileSync(new URL('../test/fixtures/prokerala-porutham.json', import.meta.url), 'utf8'));
const moon = (v: string) => {
  const [k, p] = v.split('-').map(Number);
  const lon = (k! * 360) / 27 + ((p ?? 0) + 0.5) * (360 / 108);
  return { n: k! + 1, r: Math.floor(lon / 30) + 1, opt: v };
};
const GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0];
const YONI = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1];
const LORD = ['Ma', 'Ve', 'Me', 'Mo', 'Su', 'Me', 'Ve', 'Ma', 'Ju', 'Sa', 'Sa', 'Ju'];
const keys: Record<string, (g: any, b: any, p: any) => string> = {
  starCount: (g, b) => String(((b.n - g.n + 27) % 27) + 1),
  starCountMod9: (g, b) => String((((b.n - g.n + 27) % 27) + 1) % 9),
  signCount: (g, b) => String(((b.r - g.r + 12) % 12) + 1),
  ganaPair: (g, b) => `${GANA[g.n - 1]}-${GANA[b.n - 1]}`,
  yoniPair: (g, b) => `${YONI[g.n - 1]}-${YONI[b.n - 1]}`,
  shownPair: (_g, _b, p) => `${p.girl}|${p.boy}`,
  lordPair: (g, b) => `${LORD[g.r - 1]}-${LORD[b.r - 1]}`,
  signPair: (g, b) => `${g.r}-${b.r}`,
  starPair: (g, b) => `${g.n}-${b.n}`,
  starCount_sameStar: (g, b) => `${((b.n - g.n + 27) % 27) + 1}${g.n === b.n ? '*' : ''}`,
  optionPair: (g, b) => `${g.opt}|${b.opt}`,
};
const NAMES = ['Dina Porutham', 'Gana Porutham', 'Mahendra Porutham', 'Stree Deergha Porutham', 'Yoni Porutham', 'Veda Porutham', 'Rajju Porutham', 'Rasi Porutham', 'Rasiyathipathi Porutham', 'Vasya Porutham'];
const only = process.argv[2];
for (const name of NAMES) {
  if (only && !name.startsWith(only)) continue;
  const values = new Set<number>();
  const found: string[] = [];
  for (const [kname, kf] of Object.entries(keys)) {
    const m = new Map<string, Set<number>>();
    for (const row of f.rows) {
      const g = moon(row.girl), b = moon(row.boy);
      const p = row.poruthams.find((x: any) => x.name === name);
      values.add(p.points);
      const k = kf(g, b, p);
      (m.get(k) ?? m.set(k, new Set()).get(k)!).add(p.points);
    }
    const conflicts = [...m.values()].filter((s) => s.size > 1).length;
    if (conflicts === 0) found.push(`${kname}(${m.size})`);
    if (conflicts === 0 && process.argv[3] === kname) {
      console.log(`  ${name} by ${kname}:`);
      for (const [k, s] of [...m].sort((a, b) => (Number.parseFloat(a[0]) - Number.parseFloat(b[0])) || a[0].localeCompare(b[0]))) console.log(`    ${k} -> ${[...s].join(',')}`);
    }
  }
  console.log(`${name.padEnd(24)} points ${[...values].sort().join('/')}  consistent keys: ${found.join(' ') || 'none'}`);
}
