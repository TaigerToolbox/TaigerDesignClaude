(() => {
  const P = window.PROJECT;
  const $ = (s, r = document) => r.querySelector(s);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isMobile = () => innerWidth < 768;
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = (t) => t * t * (3 - 2 * t);
  const lerp = (a, b, t) => a + (b - a) * t;

  // ---- Text from the data file
  document.title = P.name;
  document.querySelectorAll("[data-bind]").forEach((el) => (el.textContent = P[el.dataset.bind] ?? ""));
  document.querySelectorAll("[data-href]").forEach((el) => (el.href = P[el.dataset.href] ?? "#"));

  // ---- Canvas helpers
  function fit(canvas) {
    const r = canvas.getBoundingClientRect();
    const d = Math.min(devicePixelRatio || 1, 2);
    const w = Math.round(r.width * d), h = Math.round(r.height * d);
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return ctx;
  }

  function cover(ctx, img) {
    const { width: W, height: H } = ctx.canvas;
    const s = Math.max(W / img.naturalWidth, H / img.naturalHeight);
    const w = img.naturalWidth * s, h = img.naturalHeight * s;
    ctx.drawImage(img, (W - w) / 2, (H - h) / 2, w, h);
  }

  // Rendered image sequence. Picks the portrait set on phones.
  // shortcut: loads every frame up front; switch to chunked loading once sequences pass ~150 frames each.
  function sequence(frames) {
    if (!frames) return null;
    const f = (isMobile() && frames.mobile) || frames.desktop;
    if (!f) return null;
    return Array.from({ length: f.count }, (_, i) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = requestRender;
      img.src = f.path.replace("{i}", String(i + 1).padStart(f.pad || 4, "0"));
      return img;
    });
  }

  // Draws the nearest loaded frame at or before t. Returns false if nothing is ready yet.
  function drawSequence(ctx, imgs, t) {
    if (!imgs) return false;
    for (let i = Math.round(t * (imgs.length - 1)); i >= 0; i--) {
      if (imgs[i].complete && imgs[i].naturalWidth) { cover(ctx, imgs[i]); return true; }
    }
    return false;
  }

  function stampPlaceholder(ctx, text) {
    const { height: H } = ctx.canvas, d = Math.min(devicePixelRatio || 1, 2);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.font = `500 ${11 * d}px Figtree, sans-serif`;
    ctx.fillStyle = "rgba(236,231,223,0.45)";
    ctx.fillText(`PLACEHOLDER  ${text}`, 16 * d, H - 16 * d);
  }

  // ---- Placeholder: tower at dusk, pushing in on a floor. Same proportions as the picker box (3:4).
  const hash = (a, b) => { const x = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return x - Math.floor(x); };

  function towerGeom(W, H, floors) {
    const tw = H * 0.24, top = H * 0.1, bottom = H * 0.9;
    return { left: W / 2 - tw / 2, tw, top, bottom, fh: (bottom - top) / floors };
  }

  function drawTower(ctx, t, floors, focusLevel, label) {
    const { width: W, height: H } = ctx.canvas;
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, "#151b29"); sky.addColorStop(0.55, "#4b4150"); sky.addColorStop(0.85, "#b8835c"); sky.addColorStop(1, "#d9a26f");
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H);

    const g = towerGeom(W, H, floors);
    const fy = focusLevel ? g.bottom - (focusLevel - 0.5) * g.fh : H / 2;
    const e = ease(t), s = 1 + e * 3;
    ctx.translate(W / 2, lerp(fy, H / 2, e)); ctx.scale(s, s); ctx.translate(-W / 2, -fy);

    // neighbours for depth
    for (let i = 0; i < 14; i++) {
      const bw = H * (0.06 + hash(i, 1) * 0.1), bh = H * (0.08 + hash(i, 2) * 0.28);
      const bx = (i / 14) * W * 1.2 - W * 0.1;
      if (Math.abs(bx + bw / 2 - W / 2) < g.tw) continue;
      ctx.fillStyle = "#1c1f27"; ctx.fillRect(bx, g.bottom - bh, bw, bh);
    }
    ctx.fillStyle = "#0b0d11"; ctx.fillRect(-W, g.bottom, W * 3, H);

    // tower body, floor slabs, windows
    ctx.fillStyle = "#1f232b"; ctx.fillRect(g.left, g.top, g.tw, g.bottom - g.top);
    const cols = 6, cw = g.tw / cols;
    for (let f = 0; f < floors; f++) {
      const y = g.bottom - (f + 1) * g.fh;
      for (let c = 0; c < cols; c++) {
        const lit = hash(f, c) > 0.5;
        ctx.fillStyle = lit ? `rgba(242,194,123,${0.55 + hash(c, f) * 0.4})` : "#2b313c";
        ctx.fillRect(g.left + c * cw + cw * 0.08, y + g.fh * 0.14, cw * 0.84, g.fh * 0.72);
      }
      ctx.fillStyle = "#3a3f49"; ctx.fillRect(g.left - g.tw * 0.02, y, g.tw * 1.04, g.fh * 0.08);
    }
    ctx.fillStyle = "#3a3f49"; ctx.fillRect(g.left - g.tw * 0.04, g.top - g.fh * 0.3, g.tw * 1.08, g.fh * 0.3);
    stampPlaceholder(ctx, label);
  }

  // ---- Placeholder: apartment plan from the type's room rects, camera moving room to room.
  function cameraFor(rect, W, H, pad) {
    const s = Math.min(W / (rect[2] + pad * 2), H / (rect[3] + pad * 2));
    return { s, x: rect[0] + rect[2] / 2, y: rect[1] + rect[3] / 2 };
  }

  function activeRoom(type, t) {
    let k = -1;
    type.rooms.forEach((r, i) => { if (r.at && t >= r.at[0]) k = i; });
    return k;
  }

  function drawPlan(ctx, t, type, label) {
    const { width: W, height: H } = ctx.canvas;
    ctx.fillStyle = "#11151b"; ctx.fillRect(0, 0, W, H);
    const timed = type.rooms.filter((r) => r.at);
    const whole = cameraFor([0, 0, type.plan.w, type.plan.h], W, H, 2);
    const k = activeRoom(type, t);
    let cam = whole;
    if (k >= 0) {
      const room = type.rooms[k], idx = timed.indexOf(room);
      const prev = idx > 0 ? cameraFor(timed[idx - 1].rect, W, H, 3) : whole;
      const cur = cameraFor(room.rect, W, H, 3);
      const u = ease(clamp((t - room.at[0]) / 0.08));
      cam = { s: lerp(prev.s, cur.s, u), x: lerp(prev.x, cur.x, u), y: lerp(prev.y, cur.y, u) };
    }
    const toScreen = (x, y) => [W / 2 + (x - cam.x) * cam.s, H / 2 + (y - cam.y) * cam.s];

    // 1 m grid
    ctx.strokeStyle = "rgba(201,163,106,0.08)"; ctx.lineWidth = 1;
    for (let x = -10; x <= type.plan.w + 10; x++) { const [sx] = toScreen(x, 0); ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, H); ctx.stroke(); }
    for (let y = -10; y <= type.plan.h + 10; y++) { const [, sy] = toScreen(0, y); ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(W, sy); ctx.stroke(); }

    const d = Math.min(devicePixelRatio || 1, 2);
    type.rooms.forEach((r, i) => {
      const [x, y] = toScreen(r.rect[0], r.rect[1]);
      const w = r.rect[2] * cam.s, h = r.rect[3] * cam.s;
      ctx.fillStyle = i === k ? "#e7dccb" : "#2a2e36"; ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = "#ece7df"; ctx.lineWidth = Math.max(2, cam.s * 0.2); ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = i === k ? "#0e1014" : "rgba(236,231,223,0.7)";
      ctx.font = `500 ${12 * d}px Figtree, sans-serif`;
      ctx.fillText(r.name.toUpperCase(), x + 10 * d, y + 22 * d);
      ctx.fillText(`${r.rect[2]} x ${r.rect[3]} m`, x + 10 * d, y + 40 * d);
    });
    stampPlaceholder(ctx, label);
  }

  // ---- Scroll-scrub engine: native sticky + scroll progress. No library needed.
  const scrubs = [];
  function progress(section, still) {
    if (reduced) return still;
    const r = section.getBoundingClientRect(), span = r.height - innerHeight;
    return span > 0 ? clamp(-r.top / span) : still;
  }
  let queued = false;
  function requestRender() { if (!queued) { queued = true; requestAnimationFrame(render); } }
  function render() {
    queued = false;
    for (const s of scrubs) {
      const r = s.section.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) continue;
      const t = progress(s.section, s.still);
      s.section.style.setProperty("--t", t.toFixed(4));
      s.draw(fit(s.canvas), t);
    }
  }
  addEventListener("scroll", requestRender, { passive: true });
  addEventListener("resize", () => { requestRender(); drawPicker(); });

  // ---- Hero
  const hero = $("#hero");
  const heroSeq = sequence(P.scenes.hero.frames);
  scrubs.push({
    section: hero, canvas: $("canvas", hero), still: 0,
    draw: (ctx, t) => drawSequence(ctx, heroSeq, t) || drawTower(ctx, t, P.levels, P.scenes.hero.focusLevel, "hero scene, set scenes.hero.frames")
  });

  // ---- Inside: one cutaway per type
  const inside = $("#inside");
  const typeKeys = Object.keys(P.types);
  let typeKey = typeKeys[0], typeSeq = sequence(P.types[typeKey].frames);
  const tabs = $(".type-tabs", inside);
  function setType(key) {
    typeKey = key; typeSeq = sequence(P.types[key].frames);
    tabs.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", b.dataset.key === key));
    requestRender();
  }
  typeKeys.forEach((key) => {
    const b = document.createElement("button");
    b.role = "tab"; b.dataset.key = key; b.textContent = P.types[key].name;
    b.onclick = () => setType(key);
    tabs.append(b);
  });
  const cap = $(".caption", inside);
  scrubs.push({
    section: inside, canvas: $("canvas", inside), still: 0.3,
    draw: (ctx, t) => {
      const type = P.types[typeKey];
      drawSequence(ctx, typeSeq, t) || drawPlan(ctx, t, type, `${type.name} cutaway, set types.${typeKey}.frames`);
      const room = type.rooms.find((r) => r.at && t >= r.at[0] && t <= r.at[1] && r.caption);
      cap.classList.toggle("off", !room);
      if (room) { $(".cap-type", cap).textContent = type.name; $(".cap-room", cap).textContent = room.name; $(".cap-text", cap).textContent = room.caption; }
    }
  });
  setType(typeKey);

  // ---- Unit picker
  const picker = $(".picker"), pickerCanvas = $("canvas", picker), pickerImg = $(".picker-img", picker);
  if (P.scenes.picker.image) { pickerImg.src = P.scenes.picker.image; pickerImg.hidden = false; pickerCanvas.hidden = true; }
  function drawPicker() { if (!pickerCanvas.hidden) drawTower(fit(pickerCanvas), 0, P.levels, null, "picker still"); }
  drawPicker();

  const panel = $(".unit-panel");
  const spots = $(".hotspots", picker);
  const area = (m) => (m ? `${m} m²` : "TBC");
  P.units.forEach((u) => {
    const b = document.createElement("button");
    b.className = "hotspot" + (u.status === "Available" ? "" : " reserved");
    b.style.left = u.x + "%"; b.style.top = u.y + "%";
    b.textContent = u.id;
    b.setAttribute("aria-pressed", "false");
    b.setAttribute("aria-label", `Residence ${u.id}, ${P.types[u.type]?.name ?? u.type}, level ${u.level}, ${u.status}`);
    b.onclick = () => {
      spots.querySelectorAll(".hotspot").forEach((x) => x.setAttribute("aria-pressed", x === b));
      panel.innerHTML = `
        <p class="eyebrow">${u.status}</p>
        <h3>Residence ${u.id}</h3>
        <dl>
          <dt>Type</dt><dd>${P.types[u.type]?.name ?? u.type}</dd>
          <dt>Level</dt><dd>${u.level}</dd>
          <dt>Bedrooms</dt><dd>${u.beds}</dd>
          <dt>Bathrooms</dt><dd>${u.baths}</dd>
          <dt>Internal</dt><dd>${area(u.internal)}</dd>
          <dt>External</dt><dd>${area(u.external)}</dd>
          <dt>Aspect</dt><dd>${u.aspect}</dd>
        </dl>
        <button class="btn" type="button">See inside ${P.types[u.type]?.name ?? ""}</button>`;
      $(".btn", panel).onclick = () => { setType(u.type); inside.scrollIntoView({ behavior: reduced ? "auto" : "smooth" }); };
    };
    spots.append(b);
  });

  // ---- Finishes
  $(".finishes").innerHTML = P.finishes.map((f) =>
    `<li><div class="area">${f.area}</div><div class="item">${f.item}</div><div class="muted small">${f.supplier} · ${f.code}</div></li>`).join("");

  // ---- Before and after
  const compare = $(".compare"), before = $(".before", compare), after = $(".after", compare);
  const range = $("input", compare), ctabs = $(".compare-tabs");
  range.oninput = () => compare.style.setProperty("--pos", range.value + "%");
  function setPane(el, side) {
    el.classList.toggle("ph", !side.src);
    el.style.backgroundImage = side.src ? `url("${side.src}")` : "";
    $(".tag", el).textContent = side.label;
  }
  P.progress.forEach((p, i) => {
    const b = document.createElement("button");
    b.role = "tab"; b.textContent = p.room;
    b.onclick = () => {
      ctabs.querySelectorAll("button").forEach((x) => x.setAttribute("aria-selected", x === b));
      setPane(before, p.before); setPane(after, p.after);
    };
    ctabs.append(b);
    if (i === 0) b.click();
  });

  requestRender();
})();
