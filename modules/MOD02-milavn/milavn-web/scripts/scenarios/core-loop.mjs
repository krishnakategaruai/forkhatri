// Discover -> Participate -> Connect -> Contribute, as Priya (already onboarded).
export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  const errs = [];
  const step = async (name, fn) => { try { await fn(); console.log('OK  ', name); } catch (e) { console.log('FAIL', name, '-', e.message); errs.push(name); await page.shot(`${out}/fail-${name}.png`); } };

  await page.goto('http://localhost:3001/');
  await page.setStorage('milavn.member', '55555555-5555-5555-5555-555555555555');
  await page.goto('http://localhost:3001/');
  await page.waitFor('Good', 10000);

  await step('detail-open', async () => { await page.clickText('Evening badminton doubles'); await page.waitFor('What this badge means', 10000); await page.sleep(800); await page.shot(`${out}/10-detail.png`); });
  await step('rsvp-going', async () => {
    if ((await page.text()).includes('Withdraw')) { await page.clickText('Withdraw', 'button'); await page.waitFor('Interested', 6000); await page.sleep(500); }
    await page.clickText('Going', 'button'); await page.waitFor("You’re going", 6000); await page.sleep(600); await page.shot(`${out}/11-detail-going.png`);
  });
  await step('trust-expand', async () => { await page.click('[aria-controls="trust-panel"]'); await page.waitFor('#trust-panel'); });
  await step('share-sheet', async () => { await page.click('.footer-sticky .icon-btn'); await page.waitFor('WhatsApp'); await page.shot(`${out}/12-share.png`); await page.click('.scrim-layer'); });
  await step('report-sheet', async () => { await page.click('.hero__top .icon-btn:last-child'); await page.waitFor('Report'); await page.clickText('Report', 'button'); await page.waitFor('Submit report'); await page.clickText('Misleading details', 'button'); await page.type('textarea', 'Time seems wrong'); await page.clickText('Submit report', 'button'); await page.waitFor('A moderator', 6000); await page.shot(`${out}/13-report-done.png`); });

  await step('discover-calendar', async () => { await page.goto('http://localhost:3001/discover?mode=calendar'); await page.waitFor('.date-strip', 10000); await page.sleep(800); await page.shot(`${out}/14-calendar-mode.png`); });
  await step('discover-search', async () => { await page.goto('http://localhost:3001/discover?mode=search'); await page.waitFor('input[type=search]', 10000); await page.type('input[type=search]', 'trek'); await page.sleep(1200); await page.waitFor('Trek', 6000); await page.shot(`${out}/15-search.png`); });
  await step('discover-map', async () => { await page.goto('http://localhost:3001/discover?mode=map'); await page.waitFor('.leaflet-container', 12000); await page.sleep(2500); await page.shot(`${out}/16-map.png`); });

  await step('circles', async () => { await page.goto('http://localhost:3001/circles'); await page.waitFor('Discover circles', 10000); await page.sleep(600); await page.shot(`${out}/17-circles.png`); });
  await step('circle-join', async () => { if (!(await page.text()).includes('Join')) { console.log('   (nothing to join)'); return; } await page.clickText('Join', 'button'); await page.waitFor('Joined', 6000); });
  await step('circle-detail', async () => { await page.clickText('Jubilee Hills Badminton Circle'); await page.waitFor('members', 10000); await page.sleep(600); await page.shot(`${out}/18-circle-detail.png`); });

  await step('calendar', async () => { await page.goto('http://localhost:3001/calendar'); await page.waitFor('Calendar', 10000); await page.sleep(1200); await page.shot(`${out}/19-calendar.png`); });
  await step('notifications', async () => { await page.goto('http://localhost:3001/notifications'); await page.waitFor('Alerts', 10000); await page.sleep(800); await page.shot(`${out}/20-notifications.png`); });
  await step('people', async () => { await page.goto('http://localhost:3001/people'); await page.waitFor('People', 10000); await page.sleep(800); await page.shot(`${out}/21-people.png`); });
  await step('me', async () => { await page.goto('http://localhost:3001/me'); await page.waitFor('Profile', 10000); await page.sleep(800); await page.shot(`${out}/22-me.png`); });

  await step('create', async () => {
    await page.goto('http://localhost:3001/create'); await page.waitFor('Make something happen', 10000);
    await page.clickText('Eat', 'button'); await page.type('input[placeholder^="e.g."]', 'Street food crawl at Charminar');
    const when = new Date(Date.now() + 26 * 3600e3); when.setMinutes(0, 0, 0);
    const p = (n) => String(n).padStart(2, '0');
    await page.clickText('Tomorrow 7 pm', 'button');
    await page.click('.picker'); await page.sleep(400); await page.clickText('Charminar', 'button'); await page.sleep(300);
    await page.clickText('More options', 'button'); await page.sleep(300);
    await page.shot(`${out}/23-create.png`);
    await page.clickText('Create', 'button'); await page.waitFor("It’s live", 10000); await page.sleep(700); await page.shot(`${out}/24-created.png`);
  });

  console.log('CONSOLE ERRORS:', page.consoleErrors());
  console.log('FAILED STEPS:', errs);
}
