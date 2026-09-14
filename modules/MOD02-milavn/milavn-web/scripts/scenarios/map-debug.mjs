export default async function (page) {
  await page.goto('http://localhost:3001/discover?mode=map');
  await page.sleep(5000);
  const info = await page.eval(() => { const m = document.querySelector('.map'); const cs = getComputedStyle(m); return { h: cs.height, display: cs.display, tiles: document.querySelectorAll('.leaflet-tile-loaded').length, pins: document.querySelectorAll('.pin').length }; });
  console.log(JSON.stringify(info));
  await page.shot('C:/Users/krish/Krishna2025/startup2026/ForKhatri/modules/MOD02-milavn/milavn-web/.logs/16-map.png');
  console.log('ERRORS', page.consoleErrors());
}
