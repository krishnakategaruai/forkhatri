// Contribute side: create (Priya) -> organizer tools (Asha) -> moderation (Moderator).
export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  const errs = [];
  const step = async (name, fn) => { try { await fn(); console.log('OK  ', name); } catch (e) { console.log('FAIL', name, '-', e.message); errs.push(name); await page.shot(`${out}/fail-${name}.png`); } };
  const as = async (id, url = 'http://localhost:3001/', expect = 'Good') => { await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', id); await page.goto(url); await page.waitFor(expect, 12000); };

  await as('55555555-5555-5555-5555-555555555555');
  await step('create', async () => {
    await page.goto('http://localhost:3001/create'); await page.waitFor('Make something happen', 10000);
    await page.clickText('Eat', 'button'); await page.type('input[placeholder^="e.g."]', 'Street food crawl at Charminar');
    const when = new Date(Date.now() + 26 * 3600e3); when.setMinutes(0, 0, 0);
    const p = (n) => String(n).padStart(2, '0');
    await page.clickText('Tomorrow 7 pm', 'button');
    await page.click('.picker'); await page.sleep(400); await page.clickText('Charminar', 'button'); await page.sleep(300);
    await page.clickText('More options', 'button'); await page.sleep(300);
    await page.type('textarea', 'Old city street food, meet at the clock tower. Veg options too.');
    await page.shot(`${out}/23-create.png`);
    await page.clickText('Create', 'button'); await page.waitFor("It’s live", 12000); await page.sleep(700); await page.shot(`${out}/24-created.png`);
  });

  await as('11111111-1111-1111-1111-111111111111');
  await step('organizer-tools', async () => {
    await page.goto('http://localhost:3001/me'); await page.waitFor('Hosting', 10000);
    const id = await page.eval(async () => { const r = await fetch('http://localhost:8001/occurrences/mine', { headers: { 'X-Milavn-Member-Id': localStorage.getItem('milavn.member') } }); const d = await r.json(); return d.hosting.find((h) => h.title.includes('doubles')).id; });
    await page.goto(`http://localhost:3001/organizer/${id}`); await page.waitFor('Send to everyone going', 12000); await page.sleep(800);
    await page.shot(`${out}/25-organizer.png`);
    await page.type('textarea', `Courts 3 and 4 booked. Bring water! (${new Date().toLocaleTimeString()})`); // unique: identical text within an hour is refused by design await page.clickText('Send to everyone going', 'button'); await page.sleep(800);
    await page.clickText('QR check-in', 'button'); await page.waitFor('Expires', 8000); await page.sleep(500); await page.shot(`${out}/26-organizer-qr.png`);
    if ((await page.text()).includes('✓ In')) { await page.clickText('In', 'button'); await page.sleep(600); } else console.log('   (everyone already checked in)');
  });

  await as('55555555-5555-5555-5555-555555555555');
  await step('priya-inbox', async () => { await page.goto('http://localhost:3001/notifications'); await page.waitFor('Update from the organizer', 10000); await page.sleep(500); await page.shot(`${out}/27-inbox.png`); });

  await as('99999999-9999-9999-9999-999999999999', 'http://localhost:3001/admin/moderation', 'Moderation queue');
  await step('moderation', async () => {
    await page.sleep(800); await page.shot(`${out}/28-moderation.png`);
    await page.click('main .lrow'); await page.waitFor('Notes', 8000); await page.shot(`${out}/29-case.png`);
    await page.clickText('Dismiss', 'button'); await page.waitFor('Confirm', 4000); await page.clickText('OK', 'button'); await page.sleep(800);
  });

  console.log('CONSOLE ERRORS:', page.consoleErrors());
  console.log('FAILED STEPS:', errs);
}
