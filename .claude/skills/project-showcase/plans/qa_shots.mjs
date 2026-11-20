// Screenshots of a served showcase for QA: desktop 1440x900 and a phone (390x844, touch, DPR 2).
//   node qa_shots.mjs http://127.0.0.1:8781/my-project/ out_dir --room level-1-r07 --pano level-1-r07
// Drives headless Edge or Chrome over the DevTools protocol (no npm packages), so the phone view is
// true device emulation, not a narrow window. Shots: page top (stacking view), plan with a room
// selected (&focus=1 deep link), a panorama. Prints console errors. Look at every image yourself.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

const [url, out, ...rest] = process.argv.slice(2);
const opt = (k) => { const i = rest.indexOf(k); return i >= 0 ? rest[i + 1] : null; };
const exe = [String.raw`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, String.raw`C:\Program Files\Google\Chrome\Application\chrome.exe`,
  "/usr/bin/chromium", "/usr/bin/google-chrome"].find(existsSync);
if (!url || !out || !exe) { console.error("usage: node qa_shots.mjs <url> <out_dir> [--room id] [--pano id]  (needs Edge or Chrome)"); process.exit(2); }
mkdirSync(out, { recursive: true });
const prof = mkdtempSync(join(tmpdir(), "qashots-"));
const port = 9300 + Math.floor(Math.random() * 500);
const br = spawn(exe, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, "--enable-unsafe-swiftshader",
  "--force-prefers-reduced-motion", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page"); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0; const waiting = new Map(); const errors = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m.result); waiting.delete(m.id); }
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push(m.params.args.map((a) => a.value ?? a.description).join(" "));
  if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.text + " " + (m.params.exceptionDetails.exception?.description || ""));
  if (m.method === "Log.entryAdded" && m.params.entry.level === "error") errors.push(m.params.entry.text + " " + (m.params.entry.url || ""));
});
const send = (method, params = {}) => new Promise((r) => { const i = ++id; waiting.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Runtime.enable"); await send("Log.enable"); await send("Page.enable");

const base = url.replace(/\/?$/, "/") + "index.html";
const views = [["stack", ""]];
if (opt("--room")) views.push(["plan", `#room=${opt("--room")}&focus=1`]);
if (opt("--pano")) views.push(["pano", `#pano=${opt("--pano")}&focus=1`]);
const sizes = [["desktop", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false }],
               ["mobile", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true }]];
for (const [size, metrics] of sizes) {
  await send("Emulation.setDeviceMetricsOverride", metrics);
  await send("Emulation.setTouchEmulationEnabled", { enabled: metrics.mobile });
  for (const [name, frag] of views) {
    errors.length = 0;
    await send("Page.navigate", { url: "about:blank" });
    await send("Page.navigate", { url: base + frag });
    await sleep(name === "pano" ? 6000 : 3500);  // manifest, SVG, and a 4096 px panorama texture
    const shot = await send("Page.captureScreenshot", { format: "png" });
    const path = resolve(out, `${name}_${size}.png`);
    writeFileSync(path, Buffer.from(shot.data, "base64"));
    console.log(path + (errors.length ? "\n  console errors: " + errors.join(" | ") : "\n  console: no errors"));
  }
}
ws.close(); br.kill(); await sleep(300);
try { rmSync(prof, { recursive: true, force: true }); } catch {}
