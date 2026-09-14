export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', '11111111-1111-1111-1111-111111111111');
  await page.goto('http://localhost:3001/'); await page.waitFor('Good', 12000); await page.sleep(1500);
  await page.shot(`${out}/30-home-dark.png`);
  await page.eval(() => { document.documentElement.dataset.theme = 'light'; localStorage.setItem('milavn.theme', 'light'); });
  await page.sleep(500); await page.shot(`${out}/31-home-light.png`);
  await page.goto('http://localhost:3001/circles'); await page.waitFor('Discover circles', 10000); await page.sleep(800); await page.shot(`${out}/32-circles-light.png`);
  await page.goto('http://localhost:3001/a/occ-seed-ride-1'); await page.waitFor('higher-risk activity', 10000); await page.sleep(800); await page.shot(`${out}/33-detail-highrisk-light.png`);
  await page.eval(() => { delete document.documentElement.dataset.theme; localStorage.removeItem('milavn.theme'); });
  console.log('ERRORS', page.consoleErrors());
}
