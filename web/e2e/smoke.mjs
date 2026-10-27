// Browser smoke test: serve a synthetic clip, then drive the editor like a user.
// Needs: ffmpeg, uv, a built web app (`npm run build`) and Chromium (`npx playwright install chromium`).
// Run: `npm run e2e`. The clip is WebM because Playwright's Chromium has no H.264.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const PORT = 8799
const base = `http://127.0.0.1:${PORT}`
const dir = mkdtempSync(join(tmpdir(), 'legendaria-e2e-'))
const video = join(dir, 'clip.webm')

const ffmpeg = spawnSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc=s=640x360:r=25:d=10',
  '-f', 'lavfi', '-i', 'sine=d=10', '-shortest', '-c:v', 'libvpx-vp9', '-b:v', '1M', '-deadline', 'realtime',
  '-c:a', 'libopus', video])
assert.equal(ffmpeg.status, 0, 'ffmpeg could not make the test clip')

writeFileSync(`${video}.legendaria.json`, JSON.stringify({
  format: 'legendaria-project', version: 1, source: 'clip.webm', duration: 10, style: 'pop', language: 'pt',
  keep: [[0, 10]],
  cues: Array.from({ length: 10 }, (_, i) => ({ start: i + 0.1, end: i + 0.9, text: `palavra${i}` })),
}))
writeFileSync(join(dir, 'legendaria-glossary.txt'), 'palavra7 -> Sétima\n')

// No video on the command line: the browser must ask for one.
const server = spawn('uv', ['run', 'flosub', 'serve', '--port', String(PORT), '--no-browser'],
  { cwd: fileURLToPath(new URL('../../engine', import.meta.url)), stdio: 'inherit',
    env: { ...process.env, LEGENDARIA_CONFIG_DIR: join(dir, 'config'), LEGENDARIA_DATA_DIR: join(dir, 'data') } })

const project = async () => (await (await fetch(`${base}/api/state`)).json()).project
let browser
try {
  for (let i = 0; ; i++) {
    try { await fetch(base); break } catch { if (i > 60) throw new Error('server did not start'); await new Promise((r) => setTimeout(r, 500)) }
  }
  browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, locale: 'en-US' })
  const errors = []
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()))
  page.on('pageerror', (e) => errors.push(String(e)))
  await page.goto(base)

  // 1. start screen: choose the file in the server-side browser (type the folder path)
  await page.getByRole('button', { name: 'Choose a file…' }).click()
  await page.getByLabel('Folder path').fill(dir)
  await page.getByLabel('Folder path').press('Enter')
  await page.getByRole('button', { name: /clip\.webm/ }).click()
  const region = (i) => page.locator(`[part~="c${i}"]`).first()
  await region(3).waitFor({ timeout: 15000 })
  assert.equal(await page.evaluate(() => crossOriginIsolated), true, 'page must be cross-origin isolated')
  assert.equal(await page.locator('aside').count(), 0, 'the side drawer is closed by default')

  // 2. dragging an edge near the next block's start: it sticks while the mouse is still down
  const box = await region(3).boundingBox()
  await page.mouse.move(box.x + box.width - 2, box.y + box.height / 2)
  await page.mouse.down(); await page.mouse.move(box.x + box.width + 18, box.y + box.height / 2, { steps: 8 })
  assert.equal(await page.locator('[part~="guide"]').count(), 1, 'a guide line shows while snapping')
  await page.mouse.up()
  await page.waitForTimeout(1000)
  assert.equal(await page.locator('[part~="guide"]').count(), 0, 'the guide goes away on release')
  assert.ok(Math.abs((await project()).cues[3].end - 4.1) < 0.002, 'the end sticks to the next block start (4.1)')

  // 3. the magnet button turns snapping off: the same drag no longer sticks
  const magnet = page.getByRole('button', { name: /Snap/ })
  await magnet.click()
  assert.equal(await magnet.getAttribute('aria-pressed'), 'false')
  const b5 = await region(5).boundingBox()
  await page.mouse.move(b5.x + b5.width - 2, b5.y + b5.height / 2)
  await page.mouse.down(); await page.mouse.move(b5.x + b5.width + 18, b5.y + b5.height / 2, { steps: 8 })
  assert.equal(await page.locator('[part~="guide"]').count(), 0, 'no guide with the magnet off')
  await page.mouse.up()
  await page.waitForTimeout(800)
  assert.ok(Math.abs((await project()).cues[5].end - 6.1) > 0.002, 'with snap off the end does not stick')
  await magnet.click()

  // 4. double-click a block: select it and focus its text box
  await region(2).dblclick()
  assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'TEXTAREA')
  assert.equal(await page.evaluate(() => document.activeElement?.value), 'palavra2')
  assert.equal((await project()).cues.length, 10, 'double-click edits, it does not split')

  await page.keyboard.press('Escape') // leave the text box so the shortcuts work again

  // mark 5–7 s and cut with the keyboard
  await page.evaluate(() => (document.querySelector('video').currentTime = 5))
  await page.waitForTimeout(300); await page.keyboard.press('i')
  await page.evaluate(() => (document.querySelector('video').currentTime = 7))
  await page.waitForTimeout(300); await page.keyboard.press('o'); await page.keyboard.press('x')
  await page.waitForTimeout(1000)
  assert.deepEqual((await project()).keep, [[0, 5], [7, 10]])

  // edit text, undo the edit and the cut
  await region(0).click(); await page.locator('textarea').first().fill('Olá mundo')
  await page.waitForTimeout(1000)
  assert.equal((await project()).cues[0].text, 'Olá mundo')
  await page.locator('body').click({ position: { x: 5, y: 5 } })
  await page.keyboard.press('Control+z'); await page.keyboard.press('Control+z'); await page.keyboard.press('Control+z')
  await page.waitForTimeout(1000)
  const undone = await project()
  assert.deepEqual(undone.keep, [[0, 10]]); assert.equal(undone.cues[0].text, 'palavra0')

  // glossary: add a correction in the panel, then check and apply all suggestions
  await page.getByRole('button', { name: 'Glossary' }).first().click()
  await page.getByLabel('Add word or correction').fill('palavra5 -> Quinta')
  await page.getByRole('button', { name: 'Add', exact: true }).click()
  await page.getByRole('button', { name: 'Check' }).click()
  await page.getByRole('button', { name: /Apply all/ }).click()
  await page.waitForTimeout(1000)
  const reviewed = await project()
  assert.equal(reviewed.cues[5].text, 'Quinta'); assert.equal(reviewed.cues[7].text, 'Sétima')

  // export SRT
  await page.getByRole('button', { name: 'Export' }).first().click()
  await page.getByRole('button', { name: 'SRT' }).click()
  await page.waitForSelector('text=clip.edited.srt', { timeout: 15000 })
  assert.match(readFileSync(join(dir, 'clip.edited.srt'), 'utf8'), /Sétima/)
  assert.deepEqual(errors, [], 'no console errors')
  console.log('e2e smoke: ok')
} finally {
  await browser?.close()
  server.kill()
}
