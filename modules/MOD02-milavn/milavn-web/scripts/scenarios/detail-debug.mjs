export default async function (page) {
  const out = 'C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs';
  await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', '11111111-1111-1111-1111-111111111111');
  await page.goto('http://localhost:3001/a/occ-seed-ride-1'); await page.sleep(3000);
  await page.shot(`${out}/33-detail-highrisk.png`);
  console.log((await page.text()).slice(0, 600));
  console.log('ERRORS', page.consoleErrors());
}
