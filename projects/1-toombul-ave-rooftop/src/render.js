// Renders the HTML set to PDF + per-page PNG previews.
// usage: node render.js [--png]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const root = path.resolve(__dirname, '..');
  const html = path.join(root, '1-Toombul-Ave_Rooftop_Site-Report-Scope-Drawings_RevA.html');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1587, height: 1123 } });
  await page.goto('file://' + html, { waitUntil: 'networkidle' });
  await page.pdf({ path: html.replace('.html', '.pdf'), width: '420mm', height: '297mm', printBackground: true });
  if (process.argv.includes('--png')) {
    const n = await page.locator('section.sheet').count();
    for (let i = 0; i < n; i++) {
      await page.locator('section.sheet').nth(i).screenshot({ path: path.join(process.env.PREVIEW_DIR || root, `p${i}.png`) });
    }
  }
  await browser.close();
})();
