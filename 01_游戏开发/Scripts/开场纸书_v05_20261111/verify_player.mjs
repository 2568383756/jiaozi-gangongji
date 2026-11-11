/** Local player QA, using an owned disposable headless browser and Node 24 CDP.
 * Run: node verify_player.mjs --smoke   (launch/page only; no media pass claim)
 *      node verify_player.mjs           (after the final MP4 exists)
 * No user browser/profile is attached. This is not Unity validation.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../..');
const art = path.join(root, '01_游戏开发/Art/开场纸书_v05_20261111');
const work = path.join(here, 'work');
const html = path.join(art, '播放开场.html');
const media = path.join(art, '开场纸书_v05_20261111.mp4');
const smoke = process.argv.includes('--smoke');
const reportPath = smoke ? path.join(work, 'player_preparation.json') : path.join(art, '播放器核验_v05.json');
const shotPath = path.join(work, smoke ? 'player_preparation.png' : 'player_review.png');
const report = {
  version: 'v05_20261111', test: 'independent_local_headless_player',
  started_at: new Date().toISOString(), smoke_only: smoke,
  status: 'not_run', media_checks_run: false, checks: [],
  unity_integration_tested: false,
  audio_scope: 'Browser audio track/decode and unmuted playback state; not a human listening test.',
};
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function exists(p) { try { await fs.access(p); return true; } catch { return false; } }
async function until(fn, label, timeout = 15000) {
  const start = Date.now(); let last;
  while (Date.now() - start < timeout) {
    last = await fn(); if (last) return last;
    await delay(100);
  }
  throw new Error(`Timed out: ${label}; last=${JSON.stringify(last)}`);
}
function check(name, passed, evidence) {
  report.checks.push({ name, passed: Boolean(passed), evidence });
  if (!passed) throw new Error(`Check failed: ${name}`);
}
class CDP {
  constructor(ws) {
    this.ws = ws; this.next = 1; this.pending = new Map(); this.handlers = new Map();
    ws.addEventListener('message', e => {
      const m = JSON.parse(e.data);
      if (m.id) {
        const p = this.pending.get(m.id); if (!p) return;
        clearTimeout(p.timer); this.pending.delete(m.id);
        if (m.error) p.reject(new Error(JSON.stringify(m.error))); else p.resolve(m.result ?? {});
      } else for (const handler of this.handlers.get(m.method) ?? []) handler(m.params);
    });
    ws.addEventListener('close', () => {
      for (const p of this.pending.values()) { clearTimeout(p.timer); p.reject(new Error('CDP connection closed')); }
      this.pending.clear();
    });
  }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { ws.close(); reject(new Error('CDP connection timeout')); }, 10000);
      ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      ws.addEventListener('error', e => { clearTimeout(timer); reject(new Error(e.message || 'CDP websocket error')); }, { once: true });
    });
    return new CDP(ws);
  }
  on(name, fn) { const list = this.handlers.get(name) ?? []; list.push(fn); this.handlers.set(name, list); }
  send(method, params = {}) {
    const id = this.next++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
      this.pending.set(id, { resolve, reject, timer }); this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result?.value;
  }
  close() { this.ws.close(); }
}

let browser, browserCDP, pageCDP; let browserExited = false;
const runtimeErrors = [];
try {
  await fs.mkdir(work, { recursive: true });
  if (!(await exists(html))) { report.status = 'blocked_missing_player'; throw new Error(`Missing player: ${html}`); }
  if (!smoke && !(await exists(media))) { report.status = 'blocked_missing_media'; throw new Error(`Final MP4 is not present: ${media}`); }
  if (!smoke) {
    const stat = await fs.stat(media);
    if (stat.size < 1024) { report.status = 'blocked_incomplete_media'; throw new Error('MP4 is empty or incomplete'); }
    report.media_file = { path: media, bytes: stat.size, mtime: stat.mtime.toISOString() };
  }
  const candidates = [process.env.INTRO_QA_BROWSER,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].filter(Boolean);
  let executable;
  for (const candidate of candidates) if (await exists(candidate)) { executable = candidate; break; }
  if (!executable) { report.status = 'blocked_missing_browser'; throw new Error('No installed Chrome or Edge found'); }
  const profile = path.join(work, `browser-profile-${Date.now()}-${process.pid}`);
  await fs.mkdir(profile, { recursive: true });
  report.browser_executable = executable; report.owned_profile = profile;
  browser = spawn(executable, ['--headless=new', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`, `--disk-cache-dir=${path.join(profile, 'Cache')}`,
    `--crash-dumps-dir=${path.join(profile, 'CrashDumps')}`,
    '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
    '--disable-component-update', '--disable-sync', '--disable-extensions',
    '--metrics-recording-only', '--window-size=1600,1200', 'about:blank'],
    { cwd: here, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  const ownedPid = browser.pid; report.owned_browser_pid = ownedPid;
  let log = '';
  browser.stdout.on('data', b => { log = (log + b.toString()).slice(-30000); });
  browser.stderr.on('data', b => { log = (log + b.toString()).slice(-30000); });
  browser.once('exit', () => { browserExited = true; });
  browser.once('error', error => { report.spawn_error = error.message; browserExited = true; });
  const devtoolsFile = path.join(profile, 'DevToolsActivePort');
  const devtools = await until(async () => {
    if (browserExited) throw new Error(`Owned browser exited during startup: ${report.spawn_error || log}`);
    try { const lines = (await fs.readFile(devtoolsFile, 'utf8')).trim().split(/\r?\n/); return lines.length >= 2 ? lines : false; } catch { return false; }
  }, 'owned browser debugging endpoint');
  const port = Number(devtools[0]); report.debug_port = port;
  browserCDP = await CDP.connect(`ws://127.0.0.1:${port}${devtools[1]}`);
  report.browser_version = await browserCDP.send('Browser.getVersion');
  const { targetId } = await browserCDP.send('Target.createTarget', { url: 'about:blank' });
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target = targets.find(t => t.id === targetId);
  if (!target?.webSocketDebuggerUrl) throw new Error('Owned page endpoint unavailable');
  pageCDP = await CDP.connect(target.webSocketDebuggerUrl);
  await pageCDP.send('Page.enable'); await pageCDP.send('Runtime.enable');
  pageCDP.on('Runtime.exceptionThrown', e => runtimeErrors.push(e.exceptionDetails?.exception?.description || e.exceptionDetails?.text));
  await pageCDP.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1200, deviceScaleFactor: 1, mobile: false });
  await pageCDP.send('Page.addScriptToEvaluateOnNewDocument', { source: `
    window.__introQA = { finishedEvents: [], nativeEnded: 0 };
    window.addEventListener('intro-finished', e => window.__introQA.finishedEvents.push({reason:e.detail?.reason,time:document.querySelector('video')?.currentTime,at:performance.now()}));
    document.addEventListener('ended', e => { if(e.target.tagName==='VIDEO') window.__introQA.nativeEnded++; }, true);
  ` });
  await pageCDP.send('Page.navigate', { url: pathToFileURL(html).href });
  await until(() => pageCDP.evaluate(`document.readyState==='complete' && !!document.querySelector('#card-play')`), 'local player DOM');
  check('local_player_loaded', true, await pageCDP.evaluate(`({url:location.href,title:document.title,videoCount:document.querySelectorAll('video').length})`));
  check('one_media_element', await pageCDP.evaluate(`document.querySelectorAll('video').length===1`), 'Single video owns audio and picture');
  if (smoke) {
    report.observed_media = await pageCDP.evaluate(`(()=>{const v=document.querySelector('video');return {readyState:v.readyState,error:v.error?.code??null,duration:Number.isFinite(v.duration)?v.duration:null}})()`);
    const shot = await pageCDP.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await fs.writeFile(shotPath, Buffer.from(shot.data, 'base64'));
    report.screenshot = shotPath; report.status = 'prepared_browser_launch_only';
    report.note = 'Preparation only. No MP4 metadata, sound, playback or finish checks have been marked passed.';
  } else {
    report.media_checks_run = true;
    await until(async () => {
      const s = await pageCDP.evaluate(`(()=>{const v=document.querySelector('video');return {ready:v.readyState,duration:v.duration,error:v.error?.code??null}})()`);
      if (s.error) throw new Error(`Video load/decode error ${s.error}`);
      return s.ready >= 1 && s.duration > 0;
    }, 'MP4 metadata', 30000);
    const state = () => pageCDP.evaluate(`(()=>{const v=document.querySelector('#intro');return {time:v.currentTime,duration:v.duration,width:v.videoWidth,height:v.videoHeight,paused:v.paused,ended:v.ended,muted:v.muted,volume:v.volume,readyState:v.readyState,decodedAudioBytes:v.webkitAudioDecodedByteCount??null,decodedVideoFrames:v.getVideoPlaybackQuality?.().totalVideoFrames??null,cardVisible:!document.querySelector('#title-card').hidden,events:[...window.__introQA.finishedEvents],nativeEnded:window.__introQA.nativeEnded}})()`);
    async function click(selector) {
      const point = await pageCDP.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing control');e.scrollIntoView({block:'center',inline:'center'});const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
      await pageCDP.send('Input.dispatchMouseEvent', { type: 'mouseMoved', ...point });
      await pageCDP.send('Input.dispatchMouseEvent', { type: 'mousePressed', button: 'left', clickCount: 1, ...point });
      await pageCDP.send('Input.dispatchMouseEvent', { type: 'mouseReleased', button: 'left', clickCount: 1, ...point });
    }
    let s = await state();
    check('metadata_48_seconds_1080p', Math.abs(s.duration - 48) <= .08 && s.width === 1920 && s.height === 1080, s);
    await click('#card-play');
    await until(async () => { const a = await state(); return !a.paused && a.time > .5; }, 'clicked playback advances');
    s = await state();
    const audioCapture = await pageCDP.evaluate(`(()=>{const v=document.querySelector('video');try{const s=v.captureStream();const a=s.getAudioTracks().map(t=>({kind:t.kind,enabled:t.enabled,readyState:t.readyState}));s.getTracks().forEach(t=>t.stop());return {tracks:a}}catch(e){return {error:e.message}}})()`);
    check('clicked_unmuted_audio_playback', !s.muted && s.volume > 0 && ((s.decodedAudioBytes ?? 0) > 0 || audioCapture.tracks?.some(t => t.enabled && t.readyState === 'live')), { state: s, audioCapture, limitation: report.audio_scope });
    await click('#play-pause'); s = await state(); const pausedAt = s.time;
    await delay(500); s = await state();
    check('pause_freezes_media_time', s.paused && Math.abs(s.time - pausedAt) < .06, { pausedAt, after: s.time });
    await click('.chapter[data-time="32"]');
    await until(async () => { const a = await state(); return a.paused && Math.abs(a.time - 32) < .15 && a.readyState >= 2; }, 'paused chapter seek to 32 seconds');
    check('chapter_32_preserves_pause', true, await state());
    await click('#play-pause');
    await until(async () => { const a = await state(); return !a.paused && a.time >= 35.2; }, 'play selected chapter', 8000);
    await click('#play-pause');
    await pageCDP.evaluate(`window.scrollTo(0,0)`);
    const shot = await pageCDP.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await fs.writeFile(shotPath, Buffer.from(shot.data, 'base64')); report.screenshot = shotPath;
    await click('#replay');
    await until(async () => { const a = await state(); return !a.paused && a.time > .1 && a.time < 2; }, 'replay from beginning');
    check('replay_resets_and_plays', true, await state());
    await click('#skip'); await click('#skip'); s = await state();
    check('skip_emits_once', s.events.length === 1 && s.events[0].reason === 'skipped' && s.paused && s.cardVisible, s);
    await click('#replay');
    await until(async () => { const a = await state(); return !a.paused && a.time > .1 && a.time < 2; }, 'replay after skip');
    // Seek near the end, then let the real media element reach EOF. No fake ended event.
    await pageCDP.evaluate(`document.querySelector('video').currentTime=document.querySelector('video').duration-.7`);
    await until(async () => { const a = await state(); return a.nativeEnded === 1 && a.events.length >= 2; }, 'native media ended', 8000);
    await click('#skip'); s = await state();
    check('natural_ended_emits_once', s.nativeEnded === 1 && s.events.length === 2 && s.events[1].reason === 'completed' && s.paused && s.cardVisible, s);
    await click('#replay');
    await until(async () => { const a = await state(); return !a.paused && a.time > .1 && a.time < 2; }, 'second completion replay');
    await pageCDP.evaluate(`document.querySelector('video').currentTime=document.querySelector('video').duration-.5`);
    await until(async () => { const a = await state(); return a.nativeEnded === 2 && a.events.length >= 3; }, 'second native media ended', 8000);
    s = await state();
    check('finish_guard_resets_each_replay', s.nativeEnded === 2 && s.events.length === 3 && s.events[2].reason === 'completed', s.events);
    check('no_uncaught_page_errors', runtimeErrors.length === 0, runtimeErrors);
    report.status = 'passed';
  }
  await fs.writeFile(path.join(work, smoke ? 'player_preparation_browser.log' : 'player_review_browser.log'), log, 'utf8');
} catch (error) {
  if (report.status === 'not_run') report.status = 'failed';
  report.error = error.stack || error.message; report.runtime_errors = runtimeErrors;
  process.exitCode = 1;
  if (pageCDP) {
    try {
      const shot = await pageCDP.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      const failureShot = path.join(work, smoke ? 'player_preparation_failed.png' : 'player_review_failed.png');
      await fs.writeFile(failureShot, Buffer.from(shot.data, 'base64')); report.failure_screenshot = failureShot;
    } catch { /* Preserve the actual primary failure. */ }
  }
} finally {
  if (browserCDP) { try { await browserCDP.send('Browser.close'); } catch {} }
  for (let i = 0; browser && !browserExited && i < 30; i++) await delay(100);
  if (browser && !browserExited) { browser.kill(); report.browser_cleanup = 'Terminated only the process spawned by this script'; }
  else report.browser_cleanup = browser ? 'Owned browser exited; user browsers untouched' : 'No browser was launched';
  pageCDP?.close(); browserCDP?.close();
  report.finished_at = new Date().toISOString();
  await fs.mkdir(path.dirname(reportPath), { recursive: true });
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), 'utf8');
  console.log(JSON.stringify({ status: report.status, smoke_only: smoke, report: reportPath, screenshot: report.screenshot ?? null, error: report.error?.split('\n')[0] ?? null }));
}
