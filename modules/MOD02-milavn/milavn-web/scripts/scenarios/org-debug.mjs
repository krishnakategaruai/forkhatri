export default async function (page) {
  await page.goto('http://localhost:3001/welcome'); await page.setStorage('milavn.member', '11111111-1111-1111-1111-111111111111');
  await page.goto('http://localhost:3001/organizer/66a7a8db-99c2-4969-8f14-611cd5f4a532'); await page.waitFor('Send to everyone going', 12000); await page.sleep(1500);
  console.log(JSON.stringify(await page.eval(() => [...document.querySelectorAll('button')].map(b => [b.textContent.trim(), b.offsetParent !== null]))));

  console.log(await page.eval(() => document.querySelector('.list')?.innerText));
}
