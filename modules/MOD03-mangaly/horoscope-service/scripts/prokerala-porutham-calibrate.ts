import { existsSync, readFileSync, writeFileSync } from 'node:fs';

/* Porutham calibration against ProKerala's public "Nakshatra Porutham" form
 * (robots.txt allows it). Every girl star × boy star option — 54 × 54, stars
 * that span two signs split by pada — one request every ~2.5 s, resumable.
 * Results: test/fixtures/prokerala-porutham.json. Nothing from ProKerala is
 * shipped; the results define and verify Mangaly's own Porutham rules. */

const OUT = new URL('../test/fixtures/prokerala-porutham.json', import.meta.url);
const URL_ = 'https://www.prokerala.com/astrology/nakshatra-porutham.php';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36';

if (process.argv[2] === '--parse') {
  console.log(JSON.stringify(parse(readFileSync(process.argv[3]!, 'utf8'))));
  process.exit(0);
}

const form = await (await fetch(URL_, { headers: { 'user-agent': UA } })).text();
const sel = form.slice(form.indexOf('name="girl_star"'));
const options = [...sel.slice(0, sel.indexOf('</select>')).matchAll(/<option[^>]*value="([^"]+)"[^>]*>([^<]*)/g)].map((m) => ({ value: m[1]!, label: m[2]!.trim() }));
if (options.length !== 54) throw new Error(`expected 54 star options, got ${options.length}`);

type Row = { girl: string; boy: string; poruthams: { name: string; girl: string; boy: string; points: number; result: string }[]; total: string };
const done: { options: typeof options; rows: Row[] } = existsSync(OUT) ? JSON.parse(readFileSync(OUT, 'utf8')) : { options, rows: [] };
const have = new Set(done.rows.map((r) => `${r.girl}|${r.boy}`));

function parse(html: string): Omit<Row, 'girl' | 'boy'> | null {
  const i = html.indexOf('Porutham Result');
  if (i < 0) return null;
  const table = html.slice(i, html.indexOf('Total Porutham Points', i) + 400);
  const poruthams: Row['poruthams'] = [];
  for (const tr of table.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)) {
    const cells = [...tr[1]!.matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/g)].map((c) => c[1]!.replace(/<[^>]+>/g, '').replace(/&#8203;|&nbsp;/g, '').replace(/\s+/g, ' ').trim());
    if (cells.length >= 6 && /^\d+$/.test(cells[0] ?? '') && /Porutham$/.test(cells[1] ?? '')) {
      poruthams.push({ name: cells[1]!, girl: cells[2]!, boy: cells[3]!, points: Number(cells[4]), result: cells[5]! });
    }
  }
  const total = /Total Porutham Points[\s\S]*?(\d+(?:\.\d+)?\s*\/\s*10)/.exec(table)?.[1]?.replace(/\s+/g, '') ?? '';
  return poruthams.length === 10 ? { poruthams, total } : null;
}

let n = done.rows.length;
for (const g of options) {
  for (const b of options) {
    if (have.has(`${g.value}|${b.value}`)) continue;
    let parsed: ReturnType<typeof parse> = null;
    for (let attempt = 0; attempt < 3 && !parsed; attempt++) {
      try {
        const res = await fetch(URL_, {
          method: 'POST',
          headers: { 'user-agent': UA, 'content-type': 'application/x-www-form-urlencoded', referer: URL_ },
          body: new URLSearchParams({ locale: 'en', girl_star: g.value, boy_star: b.value, p: '1' }),
        });
        parsed = parse(await res.text());
      } catch { /* retry */ }
      if (!parsed) await new Promise((r) => setTimeout(r, 10_000));
    }
    if (!parsed) { console.error(`skip ${g.label} × ${b.label}`); continue; }
    done.rows.push({ girl: g.value, boy: b.value, ...parsed });
    n++;
    if (n % 20 === 0 || n === options.length ** 2) writeFileSync(OUT, `${JSON.stringify(done)}\n`);
    if (n % 50 === 0) console.log(`${n}/${options.length ** 2} last: ${g.label} × ${b.label} ${parsed.total}`);
    await new Promise((r) => setTimeout(r, 2500));
  }
}
writeFileSync(OUT, `${JSON.stringify(done)}\n`);
console.log('complete', done.rows.length);
