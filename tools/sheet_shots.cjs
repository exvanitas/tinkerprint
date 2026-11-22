// Screenshots of the demo sheets for the README: docs/tobi.png (light) and docs/wren.png (dark).
//   node tools/sheet_shots.cjs <demo folder> <docs folder>
// 1046 px wide, where the whole room fits at 4x. Reduced motion shows the still frame, so every run
// gives the same picture for the same sheet. Set PLAYWRIGHT_CORE to playwright-core's folder if
// require('playwright-core') can't find it. A maintainer tool: not part of the package.
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');

const [demo, docs] = process.argv.slice(2).map(p => path.resolve(p));
if (!demo || !docs) {
  console.error('usage: node tools/sheet_shots.cjs <demo folder> <docs folder>');
  process.exit(2);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const [who, scheme] of [['tobi', 'light'], ['wren', 'dark']]) {
    const ctx = await browser.newContext({ viewport: { width: 1046, height: 860 }, colorScheme: scheme, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    await page.goto('file://' + path.join(demo, who, 'sheet.html'), { waitUntil: 'load' });
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(docs, who + '.png') });
    await ctx.close();
    console.log('wrote ' + who + '.png');
  }
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
