// Explore view: exterior orbit, storey cutaway with capped section, hero-room walk. Data in explore.json.
// URL: ?view=exterior|cutaway|room:<id>  &level=<storey name or id>  &fps=1 (meter + continuous render)
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const $ = (id) => document.getElementById(id);
const q = new URLSearchParams(location.search);
const cfg = await (await fetch('explore.json')).json();
const mobile = matchMedia('(pointer: coarse)').matches || innerWidth < 700;
const fpsMode = q.has('fps');
document.title = (cfg.name ? cfg.name + ': ' : '') + 'Explore';
$('title').textContent = cfg.name || 'Explore';

// ---------- renderer, scene, lights
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, mobile ? 1.5 : 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.NeutralToneMapping; // keeps scheduled colours close to their swatches
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false; // the sun doesn't move: re-render shadows only when the scene changes
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe8ebed);
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.1, 5000);
const hemi = new THREE.HemisphereLight(0xf4f6fa, 0xd2cec6, 1.6); // light ground colour: ceilings face down and read too dark otherwise
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff6e8, 2.4);
sun.castShadow = true;
sun.shadow.mapSize.setScalar(mobile ? 1024 : 2048);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
// interiors sit in the envelope's shadow: an unshadowed fill from one side gives walls facing different ways different tones
const fill = new THREE.DirectionalLight(0xfff3e0, 0);
fill.position.set(0.6, -0.25, 0.4); // slightly from below so ceilings get some too
scene.add(fill);

const root = new THREE.Group();
scene.add(root);
const groups = {}; // storey id -> Group
const clip = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
const capUniforms = { uCapOn: { value: 0 }, uCapY: { value: 0 }, uCapColor: { value: new THREE.Color(0x3a3d40) } };

// ground: a soft disc at ground level so the building sits on something; hidden when looking at basements
const ground = new THREE.Mesh(new THREE.CircleGeometry(1, 64), new THREE.MeshStandardMaterial({ color: 0xd8d6cf, roughness: 1 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// ---------- controls
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.dampingFactor = 0.08;
orbit.screenSpacePanning = true;
let dirty = true;
orbit.addEventListener('change', () => (dirty = true));
let touched = false; // once the visitor moves the camera, loading never moves it again
orbit.addEventListener('start', () => (touched = true));

const walk = { on: false, yaw: 0, pitch: 0, target: new THREE.Vector3(), keys: new Set(), eye: 1.6, floor: 0 };
const ray = new THREE.Raycaster();
let drag = null, lastTap = 0, pinch = null;
const el = renderer.domElement;
el.addEventListener('pointerdown', (e) => {
  if (!walk.on) return;
  drag = { x: e.clientX, y: e.clientY, id: e.pointerId, moved: 0 };
  el.setPointerCapture(e.pointerId);
});
el.addEventListener('pointermove', (e) => {
  if (!walk.on || !drag || drag.id !== e.pointerId || pinch) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  drag.x = e.clientX; drag.y = e.clientY; drag.moved += Math.abs(dx) + Math.abs(dy);
  walk.yaw += dx * 0.004; walk.pitch = THREE.MathUtils.clamp(walk.pitch + dy * 0.004, -1.2, 1.2); // drag the view like a photo
  dirty = true;
});
el.addEventListener('pointerup', (e) => {
  if (!walk.on || !drag) return;
  const tap = drag.moved < 6, now = performance.now();
  if (tap && now - lastTap < 350) walkTo(e.clientX, e.clientY);
  lastTap = tap ? now : 0;
  drag = null;
});
el.addEventListener('dblclick', (e) => walk.on && walkTo(e.clientX, e.clientY));
el.addEventListener('wheel', (e) => { if (walk.on) { step(-Math.sign(e.deltaY) * 0.5); e.preventDefault(); } }, { passive: false });
el.addEventListener('touchstart', (e) => { if (walk.on && e.touches.length === 2) pinch = dist(e.touches); }, { passive: true });
el.addEventListener('touchmove', (e) => {
  if (!walk.on || !pinch || e.touches.length !== 2) return;
  const d = dist(e.touches); step((d - pinch) * 0.01); pinch = d;
}, { passive: true });
el.addEventListener('touchend', (e) => { if (e.touches.length < 2) pinch = null; });
const dist = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
addEventListener('keydown', (e) => walk.on && walk.keys.add(e.key.toLowerCase()));
addEventListener('keyup', (e) => walk.keys.delete(e.key.toLowerCase()));

function forward() { return new THREE.Vector3(-Math.sin(walk.yaw), 0, -Math.cos(walk.yaw)); }
function step(m) { walk.target.addScaledVector(forward(), m); dirty = true; }
function walkTo(x, y) {
  ray.setFromCamera(new THREE.Vector2((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1), camera);
  const hit = ray.intersectObjects(root.children, true).find((h) => h.object.visible && h.object.material && !h.object.material.transparent);
  if (!hit) return;
  const n = hit.face ? hit.face.normal.clone().transformDirection(hit.object.matrixWorld) : new THREE.Vector3();
  const p = hit.point.clone();
  if (Math.abs(n.y) < 0.7) p.addScaledVector(ray.ray.direction, -0.5); // a wall: stop half a metre short
  walk.floor = Math.abs(n.y) >= 0.7 && n.y > 0 ? p.y : walk.floor;
  walk.target.set(p.x, walk.floor + walk.eye, p.z);
  dirty = true;
}

// ---------- loading
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const total = cfg.storeys.reduce((a, s) => a + s.bytes, 0);
let loaded = 0, tris = 0;
const bar = $('load').firstElementChild;

function prepare(obj) {
  obj.traverse((o) => {
    if (!o.isMesh) return;
    const m = o.material;
    o.castShadow = o.receiveShadow = !m.transparent;
    m.side = THREE.DoubleSide; // IFC faces are not reliably wound; back faces also draw the section cap
    if (m.transparent) { m.depthWrite = false; m.roughness = 0.05; o.renderOrder = 2; }
    else {
      m.onBeforeCompile = (s) => {
        Object.assign(s.uniforms, capUniforms);
        s.vertexShader = 'varying float vCapY;\n' + s.vertexShader.replace('#include <project_vertex>',
          '#include <project_vertex>\nvCapY = (modelMatrix * vec4(transformed, 1.0)).y;');
        // only back faces just under the cut are section; elsewhere they are badly wound faces (trees, proxies)
        s.fragmentShader = 'uniform float uCapOn;\nuniform float uCapY;\nuniform vec3 uCapColor;\nvarying float vCapY;\n' + s.fragmentShader.replace('#include <dithering_fragment>',
          '#include <dithering_fragment>\nif (uCapOn > 0.5 && !gl_FrontFacing && vCapY > uCapY - 0.6) gl_FragColor = vec4(uCapColor, 1.0);');
      };
    }
    tris += o.geometry.index ? o.geometry.index.count / 3 : o.geometry.attributes.position.count / 3;
  });
}

// order: ground floor first, then up, then down (what a first look needs), site last
const order = [...cfg.storeys].sort((a, b) => rank(a) - rank(b));
function rank(s) { if (s.site) return 1e6; const d = s.z - cfg.ground_y; return d >= -0.3 ? d : 1e3 - d; }
const loadAll = (async () => {
  const queue = [...order];
  const worker = async () => {
    while (queue.length) {
      const s = queue.shift();
      const g = (await loader.loadAsync(s.file)).scene;
      prepare(g);
      g.name = s.id;
      groups[s.id] = g;
      root.add(g);
      loaded += s.bytes;
      bar.style.width = (100 * loaded / total).toFixed(1) + '%';
      applyVisibility();
      if (Object.keys(groups).length === 1) frameAll(true);
      renderer.shadowMap.needsUpdate = true;
      dirty = true;
    }
  };
  await Promise.all([worker(), worker()]);
  $('load').hidden = true;
  window.__explore.ready = true;
})();

// ---------- bounds, sun, ground from the storey data (cheap, before anything loads)
const levels = cfg.storeys.filter((s) => !s.site);
const box = new THREE.Box3();
function frameAll(first) {
  box.setFromObject(root);
  if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  const r = size.length() / 2;
  ground.scale.setScalar(r * 3);
  ground.position.set(c.x, cfg.ground_y - 0.02, c.z);
  const az = THREE.MathUtils.degToRad(cfg.sun.az), elv = THREE.MathUtils.degToRad(cfg.sun.el);
  sun.position.set(c.x + Math.sin(az) * Math.cos(elv) * r * 2, c.y + Math.sin(elv) * r * 2, c.z - Math.cos(az) * Math.cos(elv) * r * 2);
  sun.target.position.copy(c);
  const sc = sun.shadow.camera;
  sc.left = sc.bottom = -r * 1.1; sc.right = sc.top = r * 1.1; sc.near = 0.1; sc.far = r * 4.5;
  sc.updateProjectionMatrix();
  orbit.maxDistance = r * 5;
  if (first && view.kind !== 'room') setView(view.kind, view.level, true);
}

// ---------- views
const view = { kind: 'exterior', level: cfg.default_level, room: null };
const findLevel = (v) => v && levels.find((s) => s.id === v || s.name.toLowerCase() === String(v).toLowerCase() || s.id === slug(v));
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function applyVisibility() {
  const lvl = findLevel(view.level) || levels[0];
  const room = view.room && cfg.rooms.find((r) => r.id === view.room);
  for (const s of cfg.storeys) {
    const g = groups[s.id];
    if (!g) continue;
    if (view.kind === 'cutaway') g.visible = s.site || s.z <= lvl.z + 0.01;
    else if (view.kind === 'room') { const rz = (findLevel(room.storey) || lvl).z; g.visible = !s.site && s.z <= rz + 0.01 + 3.6 && s.z >= rz - 6; }
    else g.visible = true;
  }
  const cut = view.kind === 'cutaway';
  renderer.clippingPlanes = cut ? [clip] : [];
  clip.constant = capUniforms.uCapY.value = lvl.z + cfg.cut_height;
  capUniforms.uCapOn.value = cut ? 1 : 0;
  ground.visible = view.kind !== 'cutaway' || lvl.z >= cfg.ground_y - 0.5;
  hemi.intensity = view.kind === 'room' ? 1.5 : 1.6;
  fill.intensity = view.kind === 'room' ? 1.6 : 0; // interiors get no sun through the shadowed envelope
  renderer.shadowMap.needsUpdate = true;
  dirty = true;
}

let tweenEnd = null;
function tweenCamera(pos, target, instant) {
  tweenEnd = { pos: pos.clone(), target: target.clone() };
  const p0 = camera.position.clone(), t0 = orbit.target.clone(), start = performance.now(), dur = instant ? 0 : 700;
  const tick = () => {
    const k = dur ? Math.min(1, (performance.now() - start) / dur) : 1, e = k * k * (3 - 2 * k);
    camera.position.lerpVectors(p0, pos, e); orbit.target.lerpVectors(t0, target, e); orbit.update(); dirty = true;
    if (k < 1) requestAnimationFrame(tick);
  };
  tick();
}

function setView(kind, arg, instant) {
  view.kind = kind;
  walk.on = kind === 'room';
  orbit.enabled = !walk.on;
  if (kind === 'cutaway' && arg) view.level = (findLevel(arg) || findLevel(view.level) || levels[0]).id;
  if (kind === 'room') view.room = (cfg.rooms.find((r) => r.id === arg) || cfg.rooms[0] || {}).id;
  applyVisibility();
  if (kind !== 'room') camera.fov = 40;
  const c = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3()), r = Math.max(size.length() / 2, 5);
  // fit to the narrower of the two fields of view, so portrait phones frame the building as well as desktops
  const half = Math.min(THREE.MathUtils.degToRad(camera.fov / 2), Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect));
  const fit = r / Math.sin(half);
  if (kind === 'exterior') {
    camera.near = 0.5;
    orbit.minDistance = 3; orbit.maxPolarAngle = THREE.MathUtils.degToRad(88);
    tweenCamera(c.clone().add(new THREE.Vector3(-0.62, 0.38, 0.69).normalize().multiplyScalar(fit * 0.8)), c, instant);
  } else if (kind === 'cutaway') {
    const lvl = findLevel(view.level);
    const t = new THREE.Vector3(c.x, lvl.z + cfg.cut_height * 0.5, c.z);
    camera.near = 0.3;
    orbit.minDistance = 2; orbit.maxPolarAngle = THREE.MathUtils.degToRad(85);
    const d = fit * 0.7;
    tweenCamera(t.clone().add(new THREE.Vector3(-0.45, 0.8, 0.55).normalize().multiplyScalar(d)), t, instant);
  } else if (kind === 'room') {
    const room = cfg.rooms.find((x) => x.id === view.room);
    if (!room) return setView('exterior');
    camera.near = 0.05;
    // interiors: wider, but never over 90 deg horizontal (wide lenses oversell rooms)
    camera.fov = Math.min(camera.aspect < 1 ? 70 : 60, THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(Math.PI / 4) / camera.aspect)));
    const p = new THREE.Vector3(...room.camera.pos), l = new THREE.Vector3(...room.camera.look);
    walk.target.copy(p); walk.floor = p.y - walk.eye;
    if (instant || camera.position.distanceTo(p) > 40) camera.position.copy(p);
    const dir = l.clone().sub(p);
    walk.yaw = Math.atan2(-dir.x, -dir.z); walk.pitch = -Math.atan2(dir.y, Math.hypot(dir.x, dir.z));
  }
  camera.updateProjectionMatrix();
  syncUI();
}

// ---------- UI
const levelsEl = $('levels'), roomsEl = $('rooms');
for (const s of [...levels].reverse()) {
  const b = document.createElement('button');
  b.textContent = s.name; b.dataset.level = s.id;
  b.onclick = () => setView('cutaway', s.id);
  levelsEl.append(b);
}
for (const r of cfg.rooms) {
  const b = document.createElement('button');
  b.textContent = r.name; b.dataset.room = r.id;
  b.onclick = () => setView('room', r.id);
  roomsEl.append(b);
}
if (!cfg.rooms.length) document.querySelector('[data-view="room"]').hidden = true;
for (const b of document.querySelectorAll('#bar button')) b.onclick = () => setView(b.dataset.view, b.dataset.view === 'room' ? view.room : view.level);

const hints = {
  exterior: mobile ? 'Drag to orbit, pinch to zoom' : 'Drag to orbit, right-drag to pan, scroll to zoom',
  cutaway: 'Pick a level on the right',
  room: mobile ? 'Drag to look, double-tap the floor to walk, pinch to step' : 'Drag to look, double-click the floor to walk, WASD or scroll to move',
};
function syncUI() {
  for (const b of document.querySelectorAll('#bar button')) b.setAttribute('aria-pressed', String(b.dataset.view === view.kind));
  levelsEl.hidden = view.kind !== 'cutaway';
  roomsEl.hidden = view.kind !== 'room' || cfg.rooms.length < 2;
  for (const b of levelsEl.children) b.setAttribute('aria-pressed', String(b.dataset.level === view.level));
  levelsEl.querySelector('[aria-pressed="true"]')?.scrollIntoView({ inline: 'center', block: 'nearest' });
  for (const b of roomsEl.children) b.setAttribute('aria-pressed', String(b.dataset.room === view.room));
  const room = cfg.rooms.find((r) => r.id === view.room);
  $('title').textContent = (cfg.name || 'Explore') + (view.kind === 'cutaway' ? ' · ' + findLevel(view.level).name : view.kind === 'room' && room ? ' · ' + room.name : '');
  $('hint').textContent = hints[view.kind];
  const u = new URL(location.href);
  u.searchParams.set('view', view.kind === 'room' ? 'room:' + view.room : view.kind);
  if (view.kind === 'cutaway') u.searchParams.set('level', findLevel(view.level).name); else u.searchParams.delete('level');
  history.replaceState(null, '', u);
  parent !== window && parent.postMessage({ type: 'explore:view', view: u.searchParams.get('view'), level: u.searchParams.get('level') }, '*');
}

// about panel: where the geometry and every finish came from
const info = $('info');
function esc(s) { const d = document.createElement('span'); d.textContent = s; return d.innerHTML; }
info.innerHTML = `<h2>About this model</h2><p>${esc(cfg.disclaimer)}</p>
  <p>Source: ${esc(cfg.source || '')}. Finishes: ${cfg.finishes.total - cfg.finishes.placeholders} of ${cfg.finishes.total} from ${esc(cfg.finishes.sources.join(', ') || 'none')}; the rest are a neutral placeholder.</p>
  <table>${cfg.finishes.list.map((f) => `<tr><td><span class="sw" style="background:${esc(f.color)}"></span></td><td>${esc(f.material)}${f.placeholder ? ' <span class="ph">placeholder</span>' : ''}</td></tr>`).join('')}</table>`;
$('infoBtn').onclick = () => { info.hidden = !info.hidden; $('infoBtn').setAttribute('aria-expanded', String(!info.hidden)); };

// ---------- loop
const fpsEl = $('fps');
let frames = 0, t0 = performance.now(), fps = 0, last = performance.now();
window.__explore = { get fps() { return fps; }, get tris() { return tris; }, get bytes() { return loaded; }, ready: false, setView, view, camera, scene, render: renderNow, bench };
// render one frame now, finishing any camera move (for screenshots when the page runs in the background)
function renderNow() {
  if (walk.on) { camera.position.copy(walk.target); camera.rotation.set(-walk.pitch, walk.yaw, 0, 'YXZ'); }
  else { if (tweenEnd) { camera.position.copy(tweenEnd.pos); orbit.target.copy(tweenEnd.target); } orbit.update(); }
  if (renderer.shadowMap.needsUpdate === false) renderer.shadowMap.needsUpdate = true;
  renderer.render(scene, camera);
}
// GPU time per frame over n frames (gl.finish after each), a rough fps ceiling for this device
function bench(n = 60) {
  const gl = renderer.getContext(); renderNow(); gl.finish();
  const t = performance.now(); for (let i = 0; i < n; i++) { renderer.render(scene, camera); gl.finish(); }
  const ms = (performance.now() - t) / n; return { msPerFrame: +ms.toFixed(2), fps: Math.round(1000 / ms), tris, bytes: loaded };
}
renderer.setAnimationLoop(() => {
  const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (walk.on) {
    const f = forward(), r = new THREE.Vector3(-f.z, 0, f.x), k = walk.keys, v = 2.0 * dt;
    if (k.has('w') || k.has('arrowup')) walk.target.addScaledVector(f, v);
    if (k.has('s') || k.has('arrowdown')) walk.target.addScaledVector(f, -v);
    if (k.has('d') || k.has('arrowright')) walk.target.addScaledVector(r, v);
    if (k.has('a') || k.has('arrowleft')) walk.target.addScaledVector(r, -v);
    if (camera.position.distanceToSquared(walk.target) > 1e-6 || k.size) { camera.position.lerp(walk.target, 1 - Math.pow(0.001, dt)); dirty = true; }
    camera.rotation.set(-walk.pitch, walk.yaw, 0, 'YXZ');
  } else if (orbit.update()) dirty = true;
  if (dirty || fpsMode) { renderer.render(scene, camera); dirty = false; frames++; }
  if (now - t0 > 1000) { fps = Math.round(frames * 1000 / (now - t0)); frames = 0; t0 = now; if (fpsMode) { fpsEl.hidden = false; fpsEl.textContent = `${fps} fps · ${(tris / 1e6).toFixed(2)}M tris · ${(loaded / 1e6).toFixed(1)} MB`; } }
});
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); dirty = true; });

// deep link
const qv = (q.get('view') || 'exterior').toLowerCase();
if (qv.startsWith('room')) { view.kind = 'room'; view.room = qv.split(':')[1] || (cfg.rooms[0] || {}).id; }
else if (qv === 'cutaway' || q.get('level')) { view.kind = 'cutaway'; view.level = (findLevel(q.get('level')) || findLevel(view.level) || levels[0]).id; }
camera.position.set(50, 40, 50);
syncUI();
if (view.kind === 'room') setView('room', view.room, true);
await loadAll;
frameAll(!touched);
