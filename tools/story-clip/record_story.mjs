// Records a 25 s portrait (1080x1920) gameplay plate, frame by frame, with scripted shots and key presses.
// Usage: npm i playwright-core && node record_story.mjs [scale]   scale=1 -> 540x960 preview, scale=2 -> 1080x1920 final
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
const here = path.dirname(fileURLToPath(import.meta.url));
const SCALE = Number(process.argv[2] || 2), FPS = 30, SECONDS = 25;
const out = path.join(here, SCALE === 2 ? 'frames' : 'frames_preview');
fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });

// 100 BPM -> one beat = 0.6 s = 18 frames. Sections: intro 8 beats, controls 12, showcase 16, closing ~5.7
const SHOTS = [
  { name: 'intro',    nomap: true, t0: 0,    t1: 4.8,  tod: [1.00, 1.10], tele: { x: 0,  z: 96,  h: Math.PI, v: 0 },  auto: true, wp: 1,
    cam: '(S,u)=>{const c=Math.cos(S.h),s=Math.sin(S.h),L=(lx,lz)=>[S.x+lx*c+lz*s,S.z-lx*s+lz*c];const p=L(1.4+0.6*u,-5.4-0.4*u),l=L(-.2,1.0+4*u);return{p:[p[0],2.3+0.8*u,p[1]],l:[l[0],.55,l[1]],fov:58}}' },
  { name: 'controls', nomap: true, t0: 4.8,  t1: 12.0, tod: [1.10, 1.20], tele: { x: 1,  z: 72,  h: Math.PI, v: 0 },  auto: false,
    keys: [ [4.8,'w',1], [6.0,'a',1], [6.5,'a',0], [6.9,'d',1], [7.8,'d',0], [8.1,'a',1], [8.5,'a',0], [9.0,' ',2], [10.2,' ',2], [10.8,'f',2], [11.4,'w',0] ] },
  { name: 'shops',    t0: 12.0, t1: 14.4, tod: [1.20, 1.25], tele: { x: -6, z: -62, h: Math.PI, v: 7 },  auto: true, wp: 1,
    cam: '(S,u)=>({p:[3.5,1.9,S.z+5.5],l:[-15.9,3.6,-78-2.5*u],fov:50})' },
  { name: 'sail',     t0: 14.4, t1: 16.2, tod: [1.25, 1.29], tele: { x: -14, z: 90, h: Math.PI / 2, v: 5 }, auto: false, sail: true,
    cam: '(S,u)=>({p:[S.x-7,3.4,S.z+7],l:[S.x+1.2,1.5,S.z-.5],fov:60})' },
  { name: 'islands',  t0: 16.2, t1: 18.0, tod: [1.29, 1.34], tele: { x: -340, z: -84, h: Math.PI, v: 8 }, auto: true, wp: 15 },
  { name: 'hills',    t0: 18.0, t1: 19.8, tod: [1.34, 1.38], tele: { x: -286, z: -50, h: -Math.PI / 2, v: 6 }, auto: true, wp: 13,
    cam: '(S,u)=>({p:[S.x+8,2.5+0.6*u,S.z-3.5],l:[S.x-60,9+2*u,S.z+42],fov:62})' },
  { name: 'turbo',    t0: 19.8, t1: 21.6, tod: [1.38, 1.44], tele: { x: 0,  z: 34,  h: Math.PI, v: 10 }, auto: true, wp: 1, turbo: true },
  { name: 'closing',  nomap: true, t0: 21.6, t1: 25.0, tod: [1.45, 1.62], tele: { x: 0,  z: 16,  h: 0,       v: 6 },  auto: false },
];

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--use-angle=metal', '--ignore-gpu-blocklist', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: SCALE });
page.on('pageerror', e => console.error('PAGEERROR', e.message));
await page.goto(pathToFileURL(path.join(here, '..', '..', 'index.html')).href + '?rec&story', { waitUntil: 'load' });
await page.waitForFunction(() => typeof window.__adv === 'function', null, { timeout: 60000 });
await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(1500);
for (let i = 0; i < 3; i++) await page.evaluate(() => window.__adv(0));

const keyOf = k => k === ' ' ? 'Space' : k;
const held = new Set(), log = { shots: [], keys: [], samples: [] };
const total = FPS * SECONDS, t0w = Date.now();
let cur = null, firedKeys = new Set();
for (let i = 0; i < total; i++) {
  const t = i / FPS, shot = SHOTS.find(s => t >= s.t0 && t < s.t1);
  if (shot !== cur) {
    for (const k of [...held]) { await page.keyboard.up(keyOf(k)); held.delete(k); }
    cur = shot;
    await page.evaluate(({ tele, auto, turbo, wp, cam, nomap, sail }) => {
      app.clearWake(); window.__camFn = cam ? eval(cam) : null; document.body.classList.toggle('nomap', !!nomap);
      const S = app.S; S.x = tele.x; S.z = tele.z; S.h = tele.h; S.camH = tele.h; S.v = tele.v; S.w = 0; S.steer = 0; S.bumps = 0; S.recT = 0; S.stuckT = 0;
      app.setSail(false); app.setTurbo(!!turbo); app.setAuto(false); S.auto = false; if (sail) app.setSail(true);
      if (auto) { app.setAuto(true); if (wp !== undefined) S.wp = wp; }
      app.snap();
    }, { tele: shot.tele, auto: shot.auto, turbo: shot.turbo, wp: shot.wp, cam: shot.cam, nomap: shot.nomap, sail: shot.sail });
    log.shots.push({ name: shot.name, t0: shot.t0, t1: shot.t1 });
  }
  for (const [kt, k, d] of (shot.keys || [])) {
    const id = kt + k + d; if (firedKeys.has(id) || kt > t + 1e-6) continue; firedKeys.add(id);
    if (d === 1) { await page.keyboard.down(k); held.add(k) } else if (d === 0) { await page.keyboard.up(k); held.delete(k) } else { await page.keyboard.press(keyOf(k)) }
    log.keys.push({ t: kt, key: k, state: d });
  }
  const f = (t - shot.t0) / (shot.t1 - shot.t0), tod = shot.tod[0] + (shot.tod[1] - shot.tod[0]) * f;
  await page.evaluate(([tod, dt, u]) => { window.__shotT = u; app.setTime(tod); window.__adv(dt); }, [tod, 1 / FPS, f]);
  if (i % 15 === 0) log.samples.push(await page.evaluate(t => ({ t, ...Object.fromEntries(['x','z','v','h','bumps'].map(k => [k, +app.S[k].toFixed(2)])), turbo: app.S.turbo, auto: app.S.auto }), t));
  await page.screenshot({ path: path.join(out, `f_${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 94 });
  if (i % 60 === 0) console.log(`frame ${i}/${total} ${shot.name} ${((Date.now() - t0w) / 1000).toFixed(0)}s`);
}
fs.writeFileSync(path.join(here, 'manifest.json'), JSON.stringify(log, null, 1));
await browser.close(); console.log('done', ((Date.now() - t0w) / 1000).toFixed(0) + 's');
