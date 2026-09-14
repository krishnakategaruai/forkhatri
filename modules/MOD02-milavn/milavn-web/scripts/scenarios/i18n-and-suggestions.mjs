// FR002 language switch (Hindi, Devanagari via Anek) + FR022 organic circle suggestion card.
export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', '11111111-1111-1111-1111-111111111111');
  await page.goto('http://localhost:3001/circles'); await page.waitFor('Discover circles', 12000); await page.sleep(800);
  await page.shot(`${out}/40-circles-suggestion.png`);
  await page.goto('http://localhost:3001/me'); await page.waitFor('Edit profile', 12000);
  await page.click('button[aria-label="Settings"]'); await page.sleep(400); await page.clickText('हिंदी', 'button'); await page.sleep(800);
  await page.goto('http://localhost:3001/'); await page.waitFor('आपके सर्कल', 12000); await page.sleep(1200);
  await page.shot(`${out}/41-home-hindi.png`);
  await page.goto('http://localhost:3001/me'); await page.sleep(1200); await page.click('button[aria-label="सेटिंग्स"]'); await page.sleep(400); await page.clickText('English', 'button'); await page.sleep(500);
  console.log('ERRORS', page.consoleErrors());
}
