/* Reads AstroSage's public Guna Milan result for one pair of synthetic
 * births, submitting its form exactly as a browser does (astrosage.com's
 * robots.txt allows automated access). Used only to build and verify
 * Mangaly's koota tables; nothing from AstroSage is shipped.
 *
 * Usage: node scripts/astrosage-check.ts G_DATE G_TIME B_DATE B_TIME  (dates YYYY-MM-DD, times HH:MM, Hyderabad) */

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36';

class Jar {
  private c = new Map<string, string>();
  take(res: Response) {
    for (const h of res.headers.getSetCookie?.() ?? []) {
      const [kv] = h.split(';');
      const i = kv!.indexOf('=');
      this.c.set(kv!.slice(0, i).trim(), kv!.slice(i + 1));
    }
  }
  header() {
    return [...this.c].map(([k, v]) => `${k}=${v}`).join('; ');
  }
}

async function go(jar: Jar, url: string, body?: URLSearchParams, referer?: string): Promise<{ url: string; html: string }> {
  let current = url;
  let init: RequestInit = { method: body ? 'POST' : 'GET', body, headers: { 'user-agent': UA, cookie: jar.header(), ...(referer ? { referer } : {}), ...(body ? { 'content-type': 'application/x-www-form-urlencoded' } : {}) }, redirect: 'manual' };
  for (let hop = 0; hop < 8; hop++) {
    const res = await fetch(current, init);
    jar.take(res);
    const loc = res.headers.get('location');
    if (res.status >= 300 && res.status < 400 && loc) {
      current = new URL(loc, current).toString();
      init = { method: 'GET', headers: { 'user-agent': UA, cookie: jar.header() }, redirect: 'manual' };
      continue;
    }
    return { url: current, html: await res.text() };
  }
  throw new Error('too many redirects');
}

function formFields(html: string, formId: string): { action: string; fields: URLSearchParams } {
  const start = html.indexOf(`id="${formId}"`);
  const open = html.lastIndexOf('<form', start);
  const close = html.indexOf('</form>', start);
  const form = html.slice(open, close);
  const action = /action="([^"]+)"/.exec(form)?.[1] ?? '';
  const fields = new URLSearchParams();
  for (const m of form.matchAll(/<input[^>]*>/g)) {
    const tag = m[0];
    const name = /name=['"]([^'"]+)['"]/.exec(tag)?.[1];
    const type = /type=['"]([^'"]+)['"]/.exec(tag)?.[1] ?? 'text';
    if (!name || type === 'button' || type === 'radio') continue;
    fields.set(name, /value=['"]([^'"]*)['"]/.exec(tag)?.[1] ?? '');
  }
  for (const m of form.matchAll(/<select[^>]*name="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)) {
    const selected = /<option[^>]*selected[^>]*value=['"]([^'"]*)['"]/i.exec(m[2]!) ?? /<option[^>]*value=['"]([^'"]*)['"][^>]*selected/i.exec(m[2]!) ?? /<option[^>]*value=['"]([^'"]*)['"]/i.exec(m[2]!);
    if (selected) fields.set(m[1]!, selected[1]!);
  }
  return { action, fields };
}

export interface AstroResult {
  kootas: Record<string, { boy: string; girl: string; obt: number }>;
  total: number | null;
  mangal: string | null;
  place: string[];
}

export async function astrosage(g: [string, string], b: [string, string]): Promise<AstroResult> {
  const jar = new Jar();
  await go(jar, 'https://www.astrosage.com/freechart/matchmaking.asp');
  const p = (d: string, t: string, n: 1 | 2, name: string) => {
    const [y, mo, da] = d.split('-').map(Number);
    const [h, mi] = t.split(':').map(Number);
    return { [`name${n}`]: name, [`day${n}`]: String(da), [`month${n}`]: String(mo), [`year${n}`]: String(y), [`hrs${n}`]: String(h), [`min${n}`]: String(mi), [`sec${n}`]: '0', [`place${n}`]: 'Hyderabad' };
  };
  const first = new URLSearchParams({ ...p(g[0], g[1], 1, 'Groom'), ...p(b[0], b[1], 2, 'Bride'), submit: 'Submit' });
  const confirm = await go(jar, 'https://www.astrosage.com/freechart/confirmMatchMaking.asp', first, 'https://www.astrosage.com/freechart/matchmaking.asp');
  const { action, fields } = formFields(confirm.html, 'form2');
  // The page's own JavaScript picks these; the script picks the same: Hyderabad, India, IST.
  for (const [placeField, tzField] of [['PlaceOfBirth', 'timeZone'], ['PlaceOfBirthForGirl', 'timeZoneForGirl']] as const) {
    const india = /<option value\s*=\s*'(Hyderabad,[^']*India)'/.exec(confirm.html.slice(confirm.html.indexOf(`name="${placeField}"`)));
    if (!india) throw new Error('Hyderabad, India not offered');
    fields.set(placeField, india[1]!);
    fields.set(tzField, '5.5');
  }
  const place = [fields.get('PlaceOfBirth') ?? '', fields.get('timeZone') ?? '', fields.get('PlaceOfBirthForGirl') ?? '', fields.get('timeZoneForGirl') ?? ''];
  let out = await go(jar, new URL(action, confirm.url).toString(), fields, confirm.url);
  // The session page hands the details on through an auto-submitting form.
  if (out.html.includes("id='frmpost'")) {
    const post = new URLSearchParams();
    for (const m of out.html.matchAll(/<input type="hidden" value='([^']*)'\s+name="([^"]+)"\/?>/g)) post.set(m[2]!, m[1]!);
    const act = /id='frmpost' action="([^"]+)"/.exec(out.html)?.[1] ?? '/cloud/matchmakingoutput.asp';
    out = await go(jar, new URL(act, out.url).toString(), post, out.url);
  }
  if (process.env.ASTRO_DEBUG) (await import('node:fs')).writeFileSync(process.env.ASTRO_DEBUG, `<!-- ${out.url} -->
` + out.html);
  const text = out.html.replace(/<[^>]+>/g, '\t').replace(/&nbsp;/g, ' ').replace(/\t+/g, '\t').replace(/\s*\n\s*/g, '\n');
  const kootas: AstroResult['kootas'] = {};
  for (const row of out.html.matchAll(/<tr>\s*((?:<td[^>]*>[\s\S]*?<\/td>\s*){6})<\/tr>/g)) {
    const cells = [...row[1]!.matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map((c) => c[1]!.replace(/<[^>]+>/g, '').trim());
    const name = cells[0] ?? '';
    if (['Varna', 'Vasya', 'Tara', 'Yoni', 'Maitri', 'Gana', 'Bhakoot', 'Nadi'].includes(name) && !(name in kootas)) {
      kootas[name] = { boy: cells[1]!, girl: cells[2]!, obt: Number(cells[4]) };
    }
  }
  const total = /between boy and girl is\s*([\d.]+)\s*\/\s*36/.exec(text);
  const mangal = /(Mr\.[^\n]*?Mangal Dosha'[^\n]*?)(?:\n|Conclusion)/.exec(text.replace(/\t/g, ' '));
  return { kootas, total: total ? Number(total[1]) : null, mangal: mangal ? mangal[1]!.trim() : null, place };
}

if (process.argv[1]?.endsWith('astrosage-check.ts')) {
  const [gd, gt, bd, bt] = process.argv.slice(2);
  if (gd && gt && bd && bt) console.log(JSON.stringify(await astrosage([gd, gt], [bd, bt]), null, 1));
}
