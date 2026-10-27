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

const server = spawn('uv', ['run', 'flosub', 'serve', video, '--port', String(PORT), '--no-browser'],
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
  const region = (i) => page.locator(`[part~="c${i}"]`).first()
  await region(3).waitFor({ timeout: 15000 })
  assert.equal(await page.evaluate(() => crossOriginIsolated), true, 'page must be cross-origin isolated')

  // resize a block on the timeline
  const box = await region(3).boundingBox()
  await page.mouse.move(box.x + box.width - 2, box.y + box.height / 2)
  await page.mouse.down(); await page.mouse.move(box.x + box.width + 28, box.y + box.height / 2, { steps: 6 }); await page.mouse.up()
  await page.waitForTimeout(1000)
  assert.ok((await project()).cues[3].end > 4.1, 'dragging the edge should move the end')

  // mark 5–7 s and cut with the keyboard
  await page.evaluate(() => (document.querySelector('video').currentTime = 5))
  await page.waitForTimeout(300); await page.keyboard.press('i')
  await page.evaluate(() => (document.querySelector('video').currentTime = 7))
  await page.waitForTimeout(300); await page.keyboard.press('o'); await page.keyboard.press('x')
  await page.waitForTimeout(1000)
  assert.deepEqual((await project()).keep, [[0, 5], [7, 10]])

  // edit text, undo the edit and the cut
  await page.locator('textarea').first().fill('Olá mundo')
  await page.waitForTimeout(1000)
  assert.equal((await project()).cues[0].text, 'Olá mundo')
  await page.locator('body').click({ position: { x: 5, y: 5 } })
  await page.keyboard.press('Control+z'); await page.keyboard.press('Control+z'); await page.keyboard.press('Control+z')
  await page.waitForTimeout(1000)
  const undone = await project()
  assert.deepEqual(undone.keep, [[0, 10]]); assert.equal(undone.cues[0].text, 'palavra0')

  // glossary suggestion
  await page.getByRole('button', { name: 'Check' }).click()
  await page.getByRole('button', { name: 'Apply', exact: true }).click()
  await page.waitForTimeout(1000)
  assert.equal((await project()).cues[7].text, 'Sétima')

  // export SRT
  await page.getByRole('button', { name: 'SRT' }).click()
  await page.waitForSelector('text=clip.edited.srt', { timeout: 15000 })
  assert.match(readFileSync(join(dir, 'clip.edited.srt'), 'utf8'), /Sétima/)
  assert.deepEqual(errors, [], 'no console errors')
  console.log('e2e smoke: ok')
} finally {
  await browser?.close()
  server.kill()
}
