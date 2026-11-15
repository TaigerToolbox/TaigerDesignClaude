const { chromium } = require('playwright'); const path = require('path');
(async () => { const root = path.resolve(__dirname, '..'); const f = path.join(root, '1-Toombul-Ave_Rooftop_Finishes-Options_RevA.html');
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1587, height: 1123 } });
  await p.goto('file://' + f, { waitUntil: 'networkidle' }); await p.pdf({ path: f.replace('.html', '.pdf'), width: '420mm', height: '297mm', printBackground: true });
  if (process.env.PREVIEW_DIR) { const n = await p.locator('section.sheet').count(); for (let i = 0; i < n; i++) await p.locator('section.sheet').nth(i).screenshot({ path: path.join(process.env.PREVIEW_DIR, `b${i}.png`) }); }
  await b.close(); })();
