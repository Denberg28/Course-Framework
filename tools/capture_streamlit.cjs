/* Browser smoke and visual capture; no API credential or online generation. */
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

async function main() {
  const target = path.resolve(process.argv[2] || 'streamlit-review');
  fs.mkdirSync(target, { recursive: true });
  const server = spawn(process.env.COURSE_UI_PYTHON || 'python', [
    '-m', 'streamlit', 'run', 'tools/streamlit_ui_fixture.py', '--server.headless', 'true',
    '--server.port', '8507', '--server.address', '127.0.0.1', '--browser.gatherUsageStats', 'false'
  ], { cwd: path.resolve(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe'] });
  let logs = '';
  server.stdout.on('data', x => { logs += x.toString(); });
  server.stderr.on('data', x => { logs += x.toString(); });
  let browser;
  try {
    const deadline = Date.now() + 30000;
    let ready = false;
    while (Date.now() < deadline && !ready) {
      if (server.exitCode !== null) throw Error('Streamlit exited: ' + logs);
      try { ready = (await fetch('http://127.0.0.1:8507/_stcore/health')).ok; } catch (_) {}
      if (!ready) await new Promise(r => setTimeout(r, 200));
    }
    assert.ok(ready, 'Streamlit startup deadline');
    browser = await chromium.launch({ headless: true, ignoreDefaultArgs: ['--hide-scrollbars'] });
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
    page.setDefaultTimeout(20000);
    await page.goto('http://127.0.0.1:8507');
    await page.getByRole('heading', { name: 'Course Framework', exact: true }).waitFor();
    const select = label => page.getByTestId('stSelectbox').filter({ has: page.getByText(label, { exact: true }) });
    async function settleScroll() {
      await page.evaluate(async () => {
        const main = document.querySelector('[data-testid="stMain"]');
        let previous = main.scrollTop, stable = 0;
        for (let i = 0; i < 120 && stable < 6; i++) {
          await new Promise(requestAnimationFrame);
          stable = Math.abs(main.scrollTop - previous) < .1 ? stable + 1 : 0;
          previous = main.scrollTop;
        }
      });
    }
    async function choose(label, value) {
      await select(label).getByRole('combobox').click();
      await page.getByRole('option', { name: value, exact: true }).click();
      await page.waitForFunction(({ label, value }) => [...document.querySelectorAll('[data-testid="stSelectbox"]')]
        .some(e => e.textContent.includes(label) && e.textContent.includes(value)), { label, value });
    }
    assert.ok((await select('Agent model').innerText()).includes('gemini-3.5-flash-lite'));
    await choose('Agent model', 'gemini-3.8-flash');
    await choose('Agent model', 'gemini-3.5-flash-lite');
    assert.equal(await page.getByRole('button', { name: 'Generate', exact: true }).isEnabled(), true);
    await page.getByText('Send syllabus to this agent (fees/quota may apply)', { exact: true }).click();
    await page.waitForFunction(() => document.querySelector('input[aria-label="Send syllabus to this agent (fees/quota may apply)"]')?.checked);
    await page.getByRole('textbox', { name: 'Syllabus', exact: true }).fill(
      fs.readFileSync(path.resolve(__dirname, '../examples/AE416-syllabus.txt'), 'utf8'));
    // First action after paste: no Tab, Ctrl+Enter or separate apply step.
    await page.getByRole('button', { name: 'Generate', exact: true }).click();
    await page.getByText('Draft ready · 5/5 complete', { exact: true }).waitFor();
    await page.getByText('36 lecture h · 54 lab h · 90 total h', { exact: true }).waitFor();
    async function checkLayout() {
      const shape = await page.evaluate(() => {
        const main = document.querySelector('[data-testid="stMain"]');
        const toolbar = document.querySelector('[data-testid="stHeader"]');
        return { overflow: getComputedStyle(main).overflowY, height: main.clientHeight,
          scrollHeight: main.scrollHeight, width: document.documentElement.scrollWidth, viewport: innerWidth,
          gutter: main.getBoundingClientRect().width - main.clientWidth,
          top: main.getBoundingClientRect().top, bottom: main.getBoundingClientRect().bottom,
          toolbarBottom: toolbar ? toolbar.getBoundingClientRect().bottom : 0,
          thumbMinimum: parseFloat(getComputedStyle(main, '::-webkit-scrollbar-thumb').minHeight) };
      });
      assert.equal(shape.overflow, 'scroll');
      assert.ok(shape.scrollHeight > shape.height);
      assert.ok(shape.gutter > 0, 'Scrollbar has a reserved visible gutter');
      assert.ok(shape.top >= shape.toolbarBottom, 'Scroll track starts below the toolbar');
      assert.ok(shape.bottom <= page.viewportSize().height + 1, 'Scroll track stays inside the viewport');
      assert.ok(shape.thumbMinimum >= 56, 'Long-course thumb remains grabbable');
      assert.ok(shape.width <= shape.viewport + 1, 'No horizontal page overflow');
    }
    await checkLayout();
    await page.screenshot({ path: path.join(target, 'streamlit-input-desktop.png') });
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await choose('Provider', 'Local template');
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await page.getByRole('button', { name: 'Generate', exact: true }).click();
    await page.getByRole('button', { name: 'Use draft', exact: true }).waitFor();
    await page.getByRole('link', { name: 'Course material ↓', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('[data-testid="stMain"]').scrollTop > 100);
    await settleScroll();
    await page.screenshot({ path: path.join(target, 'streamlit-course-desktop.png') });
    const assessment = page.getByTestId('stExpander').filter({ has: page.getByText('Assessment', { exact: true }) }).first();
    assert.equal(await assessment.evaluate(el => {
      const details = el.matches('details') ? el : el.querySelector('details');
      return details ? details.open : null;
    }), false);
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download Markdown', exact: true }).click();
    const download = await downloadEvent;
    await download.saveAs(path.join(target, 'offline-draft.md'));
    assert.ok(fs.readFileSync(path.join(target, 'offline-draft.md'), 'utf8').includes('Paler-Calmorin'));
    await page.getByRole('link', { name: 'Syllabus', exact: true }).click();
    await settleScroll();
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await choose('Provider', 'Google AI Studio (Gemini)');
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await page.getByText('Gemini key configured in Secrets', { exact: true }).waitFor();
    await page.getByText('Send syllabus to this agent (fees/quota may apply)', { exact: true }).click();
    await page.waitForFunction(() => document.querySelector('input[aria-label="Send syllabus to this agent (fees/quota may apply)"]')?.checked);
    assert.equal(await page.getByRole('checkbox', { name: 'Send syllabus to this agent (fees/quota may apply)', exact: true }).isChecked(), true);
    async function captureGeneration(name) {
      await page.getByRole('button', { name: 'Generate', exact: true }).click();
      const busy = page.getByRole('button', { name: 'Generating…', exact: true });
      await busy.waitFor();
      assert.equal(await busy.isEnabled(), false);
      const status = page.locator('.st-key-generation_status');
      await status.getByText(/Generating module/).waitFor();
      const position = await status.evaluate(el => {
        const b = document.querySelector('.st-key-generation_controls button');
        const m = document.querySelector('[data-testid="stMain"]');
        return { top: el.getBoundingClientRect().top, bottom: el.getBoundingClientRect().bottom,
          buttonTop: b.getBoundingClientRect().top, mainTop: m.getBoundingClientRect().top, viewport: innerHeight };
      });
      assert.ok(position.top >= position.mainTop, 'Generation progress is visible in the scroll viewport');
      assert.ok(position.bottom <= position.buttonTop + 1, 'Progress sits above Generate');
      assert.ok(position.bottom <= position.viewport, 'Progress is not below the screen');
      await page.screenshot({ path: path.join(target, name) });
      await status.getByText('Draft ready · 5/5 complete', { exact: true }).waitFor();
      await page.getByRole('button', { name: 'Generate', exact: true }).waitFor();
    }
    await choose('Agent model', 'gemini-3.8-flash');
    await captureGeneration('streamlit-generation-desktop.png');
    await choose('Agent model', 'gemini-3.5-flash-lite');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('link', { name: 'Syllabus', exact: true }).click();
    await settleScroll();
    await checkLayout();
    assert.equal(await page.locator('.cf-art').isVisible(), false);
    await page.getByTestId('stMain').evaluate(el => el.scrollTo({ top: 0, behavior: 'instant' }));
    assert.ok(await page.getByRole('heading', { name: 'Course Framework', exact: true }).evaluate(el => {
      const toolbar = document.querySelector('[data-testid="stHeader"]');
      return el.getBoundingClientRect().top >= (toolbar ? toolbar.getBoundingClientRect().bottom : 0);
    }), 'Mobile masthead clears the Streamlit toolbar');
    await page.screenshot({ path: path.join(target, 'streamlit-input-mobile.png') });
    await captureGeneration('streamlit-generation-mobile.png');
    await page.getByRole('link', { name: 'Course material ↓', exact: true }).click();
    await settleScroll();
    await page.screenshot({ path: path.join(target, 'streamlit-course-mobile.png') });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    assert.equal(await page.getByTestId('stMain').evaluate(el => getComputedStyle(el).scrollBehavior), 'auto');
    // Regression: real browser table pastes contain blank first columns and tabs.
    await page.setViewportSize({ width: 1366, height: 900 });
    await page.getByRole('link', { name: 'Syllabus', exact: true }).click();
    const ojt = fs.readFileSync(path.resolve(__dirname, '../examples/AE417-syllabus.md'), 'utf8')
      .trim().split('\n').filter(line => !line.startsWith('|---'))
      .map(line => line.slice(1, -1).split('|').map(cell => cell.trim()).join('\t')).join('\n');
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await choose('Provider', 'Local template');
    await page.getByTestId('stExpander').filter({ has: page.getByText('Settings & files', { exact: true }) }).locator('summary').click();
    await page.getByRole('textbox', { name: 'Syllabus', exact: true }).fill(ojt);
    await page.getByRole('button', { name: 'Generate', exact: true }).click();
    await page.getByText('Draft ready · 13/13 complete', { exact: true }).waitFor();
    await page.getByText(/AE 417.*13 modules · 7 outcomes/).waitFor();
    await page.getByText('54 lecture h · 0 lab h · 54 total h', { exact: true }).waitFor();
    const ojtDownloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download Markdown', exact: true }).click();
    const ojtDownload = await ojtDownloadEvent;
    await ojtDownload.saveAs(path.join(target, 'ae417-offline-draft.md'));
    const ojtDraft = fs.readFileSync(path.join(target, 'ae417-offline-draft.md'), 'utf8');
    assert.equal((ojtDraft.match(/^## Module /gm) || []).length, 13);
    assert.ok(ojtDraft.includes('## Module 13: Pre-Deployment Seminar and Internship Requirements'));
    assert.ok(ojtDraft.includes('| Selected total | | 54 | 0 |'));
    await page.getByRole('link', { name: 'Course material ↓', exact: true }).click();
    await settleScroll();
    await checkLayout();
    await page.screenshot({ path: path.join(target, 'streamlit-ae417-course-desktop.png') });
    assert.equal(await page.getByTestId('stException').count(), 0);
    console.log('Browser smoke passed: direct first-click paste/generation, model selection, offline download, simulated in-flight progress, scrollbar/toolbar geometry, desktop/mobile navigation, reduced motion, AE 417 clipboard table and all 13 modules.');
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
