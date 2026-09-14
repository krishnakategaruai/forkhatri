// Anonymous public page (FR046) · post-event feedback prompt (FR066) · edit &
// save (FR012) · co-organizer delegation (FR059) · QR-URL check-in (FR018).
export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  const API = 'http://localhost:8001';
  const errs = [];
  const step = async (name, fn) => { try { await fn(); console.log('OK  ', name); } catch (e) { console.log('FAIL', name, '-', e.message); errs.push(name); await page.shot(`${out}/fail-${name}.png`); } };
  const as = async (id, url, expect) => { await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', id); await page.goto(url); await page.waitFor(expect, 12000); };
  const apiCall = (id, path, opts = {}) => page.eval(`(async () => { const r = await fetch(${JSON.stringify(API + path)}, { method: ${JSON.stringify(opts.method ?? (opts.body ? 'POST' : 'GET'))}, headers: { 'X-Milavn-Member-Id': ${JSON.stringify(id)}, 'Content-Type': 'application/json' }, body: ${opts.body ? JSON.stringify(JSON.stringify(opts.body)) : 'undefined'} }); return r.json(); })()`);

  await step('anonymous-public-page', async () => {
    await page.goto('http://localhost:3001/welcome'); await page.eval(() => localStorage.clear());
    await page.goto('http://localhost:3001/a/occ-seed-yoga-1'); await page.waitFor('Open Milavn to RSVP', 12000); await page.sleep(500);
    await page.shot(`${out}/50-public-anon.png`);
  });

  await step('feedback-prompt', async () => {
    // Meera is checked in on Sunday Badminton (seed + organizer mark) -> prompt eligible.
    await as('33333333-3333-3333-3333-333333333333', 'http://localhost:3001/a/occ-bbbbbbbb0001', 'What this badge means');
    // Feedback is one-per-occurrence (FR066), so a re-run finds it already given: that is the correct product behaviour, not a failure.
    const pr = await apiCall('33333333-3333-3333-3333-333333333333', '/feedback/prompt/bbbbbbbb-0000-0000-0000-000000000001');
    if (pr.already_submitted) { const txt = await page.text(); if (txt.includes('How was it?')) throw new Error('prompt shown after feedback was already submitted'); console.log('     (feedback already submitted earlier -> prompt correctly hidden)'); return; }
    await page.waitFor('How was it?', 8000); await page.clickText('4', 'button'); await page.type('textarea', 'Great courts, friendly crowd.');
    await page.shot(`${out}/51-feedback.png`); await page.clickText('Send', 'button'); await page.waitFor('Thanks', 6000);
  });

  await step('edit-and-save', async () => {
    await as('11111111-1111-1111-1111-111111111111', 'http://localhost:3001/', 'Good');
    const id = await page.eval(`(async () => { const r = await fetch('${API}/occurrences/mine', { headers: { 'X-Milavn-Member-Id': localStorage.getItem('milavn.member') } }); const d = await r.json(); return d.hosting.find((h) => h.title.includes('Board games')).id; })()`);
    await page.goto(`http://localhost:3001/create?edit=${id}`); await page.waitFor('Save', 12000); await page.sleep(800);
    await page.type('input[placeholder^="e.g."]', 'Board games at Prism Café — round 2'); await page.clickText('Save', 'button');
    await page.waitFor('round 2', 12000); await page.shot(`${out}/52-edited.png`);
  });

  await step('delegate-co-organizer', async () => {
    const id = await page.eval(`(async () => { const r = await fetch('${API}/occurrences/mine', { headers: { 'X-Milavn-Member-Id': localStorage.getItem('milavn.member') } }); const d = await r.json(); return d.hosting.find((h) => h.title.includes('Board games')).id; })()`);
    await page.goto(`http://localhost:3001/organizer/${id}`); await page.waitFor('Delegate', 12000);
    await page.clickText('Delegate', 'button'); await page.waitFor('Vikram Rao', 6000); await page.clickText('Vikram Rao', 'button'); await page.sleep(800);
    await page.waitFor('Revoke', 6000); await page.shot(`${out}/53-delegated.png`);
  });

  await step('qr-url-checkin', async () => {
    const asha = '11111111-1111-1111-1111-111111111111';
    const tok = await apiCall(asha, '/occurrences/66a7a8db-99c2-4969-8f14-611cd5f4a532/checkin/token', { body: {} });
    if (!tok.qr_payload || !tok.qr_payload.startsWith('http')) throw new Error('qr payload is not a URL: ' + JSON.stringify(tok));
    await apiCall('22222222-2222-2222-2222-222222222222', '/occurrences/66a7a8db-99c2-4969-8f14-611cd5f4a532/participation', { body: { status: 'going' } });
    await as('22222222-2222-2222-2222-222222222222', tok.qr_payload, 'What this badge means');
    await page.waitFor('Checked in', 10000); await page.sleep(500); await page.shot(`${out}/54-qr-checked-in.png`);
  });

  console.log('CONSOLE ERRORS:', page.consoleErrors());
  console.log('FAILED STEPS:', errs);
}
