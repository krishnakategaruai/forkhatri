// FR076 launch -> FR001/FR002/FR081 onboarding -> FR004 home, as a brand-new member.
// Fresh identity per run: pass FRESH_MEMBER=<name> (default Kiran Das). A member
// who already has a profile is sent straight to Around You (FR076), so the
// onboarding steps are skipped automatically in that case.
export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  const who = process.env.FRESH_MEMBER ?? 'Kiran Das';
  await page.goto('http://localhost:3001/welcome');
  await page.eval(() => localStorage.clear());
  await page.goto('http://localhost:3001/welcome');
  await page.waitFor('Continue as');
  await page.shot(`${out}/01-welcome.png`);
  await page.clickText(who, 'button');
  await page.sleep(2500);
  if ((await page.text()).includes('Good ')) { console.log('already onboarded → home'); await page.shot(`${out}/05-home.png`); return; }
  await page.waitFor('Where are you?', 10000);
  await page.shot(`${out}/02-onboarding-where.png`);
  // Designed place picker (identity v2): open, pick the city chip, pick the locality chip.
  await page.clickText('Choose a place', 'button'); await page.sleep(400); await page.clickText('Hyderabad', 'button'); await page.sleep(300); await page.clickText('Gachibowli', 'button'); await page.sleep(400);
  await page.clickText('Continue', 'button');
  await page.waitFor('What are you into?');
  await page.clickText('Badminton', 'button');
  await page.clickText('Coffee meetups', 'button');
  await page.shot(`${out}/03-onboarding-interests.png`);
  await page.clickText('Continue', 'button');
  await page.waitFor('Choose your language');
  await page.shot(`${out}/04-onboarding-language.png`);
  await page.clickText('Show me what', 'button');
  await page.waitFor('Good', 10000);
  await page.sleep(1500);
  await page.shot(`${out}/05-home.png`);
  console.log('HOME TEXT:\n' + (await page.text()).slice(0, 900));
  console.log('CONSOLE ERRORS:', page.consoleErrors());
}
