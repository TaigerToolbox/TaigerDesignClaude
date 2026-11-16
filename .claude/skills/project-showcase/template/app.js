(() => {
  "use strict";
  const P = window.PROJECT || {};
  const F = window.FRAMES || {};
  const $ = (s, r = document) => r.querySelector(s);
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = (t) => t * t * (3 - 2 * t);
  const lerp = (a, b, t) => a + (b - a) * t;
  const mq = matchMedia("(prefers-reduced-motion: reduce)");
  let reduced = mq.matches;
  const saveData = navigator.connection?.saveData === true;
  const dpr = () => Math.min(devicePixelRatio || 1, 2);
  const T = (v, fallback = "TBC") => (v === null || v === undefined || v === "" ? fallback : String(v));
  const safeHref = (h) => (/^(https?:|mailto:|tel:|#)/i.test(String(h || "")) ? h : "#");

  // DOM builder. Text always goes in as textContent, so schedule data can never inject markup.
  function el(tag, attrs = {}, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "style") Object.assign(n.style, v);
      else if (k.startsWith("on")) n[k] = v;
      else n.setAttribute(k, v === true ? "" : String(v));
    }
    for (const c of kids.flat(Infinity)) if (c !== null && c !== undefined && c !== false) n.append(c);
    return n;
  }

  // ---------- Page text
  document.title = T(P.name, "Project");
  $('meta[name="description"]')?.setAttribute("content", T(P.description, ""));
  document.querySelectorAll("[data-bind]").forEach((n) => (n.textContent = T(P[n.dataset.bind], "")));
  // The renderer records styling props in the manifest; the caption follows automatically.
  const styled = (window.FRAMES || {})._meta?.styling === "indicative";
  const disclaimer = [P.disclaimer, P.sourceRevision, styled && "Furniture and styling indicative, not included."].filter(Boolean).join(" ");

  // ---------- Frame sequences: fetched as small compressed blobs, decoded only near the current frame.
  // Two 180-frame 1080p sequences decoded up front are ~3 GB of bitmaps and get the tab killed on iPhone.
  function frameSet(spec) {
    if (!spec) return null;
    const key = typeof spec === "string" ? spec : null;
    const s = key ? F[key] : spec;
    if (!s) return null;
    const out = {};
    for (const v of ["desktop", "mobile"]) {
      if (s[v]?.count) out[v] = { pad: 4, ...s[v], path: s[v].path || `frames/${key}/${v}/{i}.webp` };
    }
    return Object.keys(out).length ? out : null;
  }

  function coarseToFine(n, minStep) {
    const seen = new Uint8Array(n), out = [];
    const add = (i) => { if (i >= 0 && i < n && !seen[i]) { seen[i] = 1; out.push(i); } };
    add(0); add(n - 1);
    for (let s = 16; s >= minStep; s >>= 1) for (let i = 0; i < n; i += s) add(i);
    return out;
  }

  class Seq {
    constructor(set, onChange) { this.set = set; this.onChange = onChange; this.variant = null; }
    pick() { return innerHeight > innerWidth && this.set.mobile ? "mobile" : this.set.desktop ? "desktop" : "mobile"; }
    url(i, v = this.pick()) { const f = this.set[v]; return f.path.replace("{i}", String(i + 1).padStart(f.pad, "0")); }
    get width() { return this.set[this.variant || this.pick()].w || 1920; }
    load(stillT = 0) {
      const v = this.pick();
      if (v === this.variant) return;
      this.dispose();
      this.variant = v;
      const f = this.set[v];
      this.n = f.count;
      this.blobs = new Array(f.count);
      this.bmp = new Map();
      this.pending = new Set();
      this.ctrl = new AbortController();
      const order = reduced ? [Math.round(stillT * (f.count - 1))] : coarseToFine(f.count, saveData ? 2 : 1);
      let next = 0, active = 0;
      const signal = this.ctrl.signal;
      const pump = () => {
        while (active < 6 && next < order.length) {
          const i = order[next++];
          active++;
          const get = (tries) => fetch(this.url(i, v), { signal })
            .then((r) => { if (!r.ok) throw new Error(r.status); return r.blob(); })
            .catch((e) => { if (e.name !== "AbortError" && tries > 0) return get(tries - 1); throw e; });
          get(1)
            .then((b) => { if (this.blobs) { this.blobs[i] = b; this.onChange(); } })
            .catch((e) => { if (e.name !== "AbortError") console.warn("frame failed", this.url(i, v), e.message); })
            .finally(() => { active--; if (!signal.aborted) pump(); });
        }
      };
      pump();
    }
    nearest(i, has) {
      for (let d = 0; d < this.n; d++) {
        if (i - d >= 0 && has(i - d)) return i - d;
        if (i + d < this.n && has(i + d)) return i + d;
      }
      return -1;
    }
    decode(k) {
      if (!this.blobs[k] || this.bmp.has(k) || this.pending.has(k)) return;
      this.pending.add(k);
      const bmp = this.bmp;
      createImageBitmap(this.blobs[k])
        .then((b) => { this.pending?.delete(k); if (this.bmp !== bmp) return b.close(); bmp.set(k, b); this.onChange(); })
        .catch(() => this.pending?.delete(k));
    }
    get(t) {
      if (!this.blobs) return null;
      const i = this.nearest(Math.round(t * (this.n - 1)), (k) => this.blobs[k]);
      if (i < 0) return null;
      for (let k = Math.max(0, i - 8); k <= Math.min(this.n - 1, i + 8); k++) this.decode(k);
      for (const [k, b] of this.bmp) if (Math.abs(k - i) > 20) { b.close(); this.bmp.delete(k); }
      const j = this.nearest(i, (k) => this.bmp.has(k));
      return j < 0 ? null : this.bmp.get(j);
    }
    dispose() {
      this.ctrl?.abort();
      this.bmp?.forEach((b) => b.close());
      this.blobs = this.bmp = this.pending = null;
      this.variant = null;
    }
  }

  // ---------- Placeholders, drawn only while a scene has no rendered frames at all
  const hash = (a, b) => { const x = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return x - Math.floor(x); };

  function stamp(ctx, text) {
    const { height: H } = ctx.canvas, d = dpr();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.font = `500 ${11 * d}px Figtree, sans-serif`;
    ctx.fillStyle = "rgba(236,231,223,0.45)";
    ctx.fillText(`PLACEHOLDER  ${text}`, 16 * d, H - 16 * d);
  }

  function drawTower(ctx, t, opt, label) {
    const { width: W, height: H } = ctx.canvas;
    const floors = opt.levels || 10;
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, "#151b29"); sky.addColorStop(0.55, "#4b4150"); sky.addColorStop(0.85, "#b8835c"); sky.addColorStop(1, "#d9a26f");
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H);
    const tw = H * 0.24, top = H * 0.1, bottom = H * 0.9, left = W / 2 - tw / 2, fh = (bottom - top) / floors;
    const fy = opt.focusLevel ? bottom - (opt.focusLevel - 0.5) * fh : H / 2;
    const e = ease(t), s = 1 + e * 3;
    ctx.translate(W / 2, lerp(fy, H / 2, e)); ctx.scale(s, s); ctx.translate(-W / 2, -fy);
    for (let i = 0; i < 14; i++) {
      const bw = H * (0.06 + hash(i, 1) * 0.1), bh = H * (0.08 + hash(i, 2) * 0.28), bx = (i / 14) * W * 1.2 - W * 0.1;
      if (Math.abs(bx + bw / 2 - W / 2) < tw) continue;
      ctx.fillStyle = "#1c1f27"; ctx.fillRect(bx, bottom - bh, bw, bh);
    }
    ctx.fillStyle = "#0b0d11"; ctx.fillRect(-W, bottom, W * 3, H);
    ctx.fillStyle = "#1f232b"; ctx.fillRect(left, top, tw, bottom - top);
    const cols = 6, cw = tw / cols;
    for (let f = 0; f < floors; f++) {
      const y = bottom - (f + 1) * fh;
      for (let c = 0; c < cols; c++) {
        ctx.fillStyle = hash(f, c) > 0.5 ? `rgba(242,194,123,${0.55 + hash(c, f) * 0.4})` : "#2b313c";
        ctx.fillRect(left + c * cw + cw * 0.08, y + fh * 0.14, cw * 0.84, fh * 0.72);
      }
      ctx.fillStyle = "#3a3f49"; ctx.fillRect(left - tw * 0.02, y, tw * 1.04, fh * 0.08);
    }
    stamp(ctx, label);
  }

  function camFor(r, W, H, pad) {
    const s = Math.min(W / (r[2] + pad * 2), H / (r[3] + pad * 2));
    return { s, x: r[0] + r[2] / 2, y: r[1] + r[3] / 2 };
  }

  function drawPlan(ctx, t, type, k, label) {
    const { width: W, height: H } = ctx.canvas, d = dpr();
    ctx.fillStyle = "#11151b"; ctx.fillRect(0, 0, W, H);
    const plan = type.plan || { w: 10, h: 8 };
    const rooms = type.rooms || [];
    const timed = rooms.filter((r) => r.at && r.rect);
    const whole = camFor([0, 0, plan.w, plan.h], W, H, 2);
    let cam = whole;
    const room = rooms[k];
    if (room?.rect && room.at) {
      const idx = timed.indexOf(room);
      const prev = idx > 0 ? camFor(timed[idx - 1].rect, W, H, 3) : whole;
      const cur = camFor(room.rect, W, H, 3);
      const u = ease(clamp((t - room.at[0]) / 0.08));
      cam = { s: lerp(prev.s, cur.s, u), x: lerp(prev.x, cur.x, u), y: lerp(prev.y, cur.y, u) };
    }
    const sx = (x) => W / 2 + (x - cam.x) * cam.s, sy = (y) => H / 2 + (y - cam.y) * cam.s;
    ctx.strokeStyle = "rgba(201,163,106,0.08)"; ctx.lineWidth = 1;
    for (let x = -10; x <= plan.w + 10; x++) { ctx.beginPath(); ctx.moveTo(sx(x), 0); ctx.lineTo(sx(x), H); ctx.stroke(); }
    for (let y = -10; y <= plan.h + 10; y++) { ctx.beginPath(); ctx.moveTo(0, sy(y)); ctx.lineTo(W, sy(y)); ctx.stroke(); }
    rooms.forEach((r, i) => {
      if (!r.rect) return;
      const x = sx(r.rect[0]), y = sy(r.rect[1]), w = r.rect[2] * cam.s, h = r.rect[3] * cam.s;
      ctx.fillStyle = i === k ? "#e7dccb" : "#2a2e36"; ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = "#ece7df"; ctx.lineWidth = Math.max(2, cam.s * 0.2); ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = i === k ? "#0e1014" : "rgba(236,231,223,0.7)";
      ctx.font = `500 ${12 * d}px Figtree, sans-serif`;
      ctx.fillText(String(r.name || "").toUpperCase(), x + 10 * d, y + 22 * d);
      ctx.fillText(`${r.rect[2]} x ${r.rect[3]} m`, x + 10 * d, y + 40 * d);
    });
    stamp(ctx, label);
  }

  function drawBlank(ctx, t, label) {
    const { width: W, height: H } = ctx.canvas;
    ctx.fillStyle = "#11151b"; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "rgba(201,163,106,0.25)";
    ctx.fillRect(0, H - 3 * dpr(), W * t, 3 * dpr());
    stamp(ctx, label);
  }

  // ---------- Scroll-scrub engine: native sticky, eased toward the scroll target, reads before writes.
  const scrubs = [];
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      const s = scrubs.find((x) => x.section === e.target);
      if (s && e.isIntersecting) s.seq?.load(s.still);
    }
  }, { rootMargin: "100% 0px" });

  let raf = 0, last = 0;
  const kick = () => { if (!raf) raf = requestAnimationFrame(tick); };

  function fit(s) {
    const cw = s.canvas.clientWidth, ch = s.canvas.clientHeight;
    const d = s.seq ? Math.max(1, Math.min(dpr(), s.seq.width / Math.max(cw, ch * 0.5625))) : dpr();
    const w = Math.round(cw * d), h = Math.round(ch * d);
    if (s.canvas.width !== w || s.canvas.height !== h) { s.canvas.width = w; s.canvas.height = h; s.drawn = false; }
    const ctx = s.canvas.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return ctx;
  }

  function cover(ctx, img) {
    const { width: W, height: H } = ctx.canvas;
    const s = Math.max(W / img.width, H / img.height);
    ctx.drawImage(img, (W - img.width * s) / 2, (H - img.height * s) / 2, img.width * s, img.height * s);
  }

  function tick(now) {
    raf = 0;
    const dt = last ? Math.min(0.1, (now - last) / 1000) : 1 / 60;
    last = now;
    for (const s of scrubs) {
      const r = s.section.getBoundingClientRect();
      s.visible = r.bottom > 0 && r.top < innerHeight;
      const span = s.section.offsetHeight - s.stage.offsetHeight; // stable while the iOS address bar moves
      s.span = span;
      s.target = reduced || span <= 0 ? s.still : clamp(-r.top / span);
    }
    let moving = false;
    for (const s of scrubs) {
      if (s.t === undefined || !s.visible || reduced) s.t = s.target;
      else s.t += (s.target - s.t) * (1 - Math.exp(-dt * 9));
      if (Math.abs(s.target - s.t) < 0.0004) s.t = s.target;
      else moving = true;
      if (!s.visible) continue;
      s.section.style.setProperty("--t", s.t.toFixed(4));
      const ctx = fit(s);
      if (s.seq) {
        const b = s.seq.get(s.t);
        if (b) { cover(ctx, b); s.drawn = true; s.canvas.classList.add("live"); }
      } else {
        s.placeholder(ctx, s.t);
      }
      s.after?.(s.t);
    }
    if (moving) kick(); else last = 0;
  }
  addEventListener("scroll", kick, { passive: true });
  let resizeTimer;
  addEventListener("resize", () => {
    kick();
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { for (const s of scrubs) if (s.seq?.variant) s.seq.load(s.still); kick(); }, 300);
  });
  mq.addEventListener?.("change", (e) => { reduced = e.matches; kick(); });
  document.fonts?.ready.then(kick);

  function registerScrub(s) {
    s.still = s.still ?? 0;
    scrubs.push(s);
    io.observe(s.section);
  }

  function stageMarkup(sec, frames) {
    const seq = frames ? new Seq(frames, kick) : null;
    const isFirst = !scrubs.length;
    const poster = sec.poster || (seq ? seq.url(Math.round((sec.still || 0) * ((frames[seq.pick()].count || 1) - 1))) : null);
    const stage = el("div", { class: "stage" },
      poster && el("img", { class: "poster", src: poster, alt: "", fetchpriority: isFirst ? "high" : null, loading: isFirst ? null : "lazy", decoding: "async" }),
      el("canvas", { role: "img", "aria-label": T(sec.alt, sec.copy?.title || "Scene") }));
    return { seq, stage };
  }

  // ---------- Section builders. Each returns a <section>; a missing field skips that section only.
  const builders = {};
  const registry = {};

  builders.scrub = (sec) => {
    const frames = frameSet(sec.frames);
    const node = el("section", { id: sec.id, class: "scrub", style: { "--len": `${(sec.length || 3) * 100}vh` } });
    const { seq, stage } = stageMarkup(sec, frames);
    const c = sec.copy || {};
    if (c.title || c.text) {
      stage.append(el("div", { class: sec.hero ? "hero-copy" : "scene-copy" },
        c.eyebrow && el("p", { class: "eyebrow", text: c.eyebrow }),
        el(sec.hero ? "h1" : "h2", { text: T(c.title, "") }),
        c.text && el("p", { class: "lede", text: c.text })));
    }
    if (sec.hero) stage.append(el("p", { class: "scroll-hint", "aria-hidden": "true", text: "Scroll" }));
    if (disclaimer) stage.append(el("p", { class: "stamp", text: disclaimer }));
    node.append(stage);
    const ph = sec.placeholder || {};
    registerScrub({
      section: node, stage, canvas: $("canvas", stage), seq, still: sec.still,
      placeholder: (ctx, t) => ph.kind === "tower"
        ? drawTower(ctx, t, ph, `${sec.id}, render frames into frames/${sec.frames || sec.id}/`)
        : drawBlank(ctx, t, `${sec.id}, render frames into frames/${sec.frames || sec.id}/`)
    });
    return node;
  };

  builders.cutaway = (sec) => {
    const types = sec.types || {};
    const keys = Object.keys(types);
    if (!keys.length) throw new Error("cutaway needs at least one entry in types");
    const node = el("section", { id: sec.id, class: "scrub", style: { "--len": `${(sec.length || 5) * 100}vh` } });
    const stage = el("div", { class: "stage" }, el("canvas", { role: "img", "aria-label": T(sec.alt, "Cutaway, moving room to room") }));
    const tabs = el("div", { class: "type-tabs", role: "group", "aria-label": T(sec.typeLabel, "Type") });
    const rail = el("nav", { class: "rail", "aria-label": "Rooms" });
    const cap = el("div", { class: "caption off", "aria-live": "polite", "aria-hidden": "true" },
      el("p", { class: "eyebrow" }), el("h3"), el("p"));
    stage.append(tabs, rail, cap);
    if (disclaimer) stage.append(el("p", { class: "stamp", text: disclaimer }));
    node.append(stage);
    const s = { section: node, stage, canvas: $("canvas", stage), still: sec.still ?? 0.3 };
    let key = null, lastRoom = -2;

    function setType(k) {
      if (!types[k] || k === key) return;
      key = k;
      s.seq?.dispose();
      const fs = frameSet(types[k].frames);
      s.seq = fs ? new Seq(fs, kick) : null;
      if (s.seq && s.span !== undefined) s.seq.load(s.still);
      s.canvas.classList.remove("live");
      tabs.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.key === k)));
      rail.replaceChildren(...(types[k].rooms || []).filter((r) => r.at).map((r) => el("button", {
        type: "button", text: r.name,
        onclick: () => scrollTo({ top: node.offsetTop + (r.at[0] + 0.1 * (r.at[1] - r.at[0])) * (s.span || 0), behavior: reduced ? "auto" : "smooth" })
      })));
      lastRoom = -2;
      kick();
    }
    if (keys.length > 1) keys.forEach((k) => tabs.append(el("button", { type: "button", "data-key": k, "aria-pressed": "false", text: T(types[k].name, k), onclick: () => setType(k) })));
    s.placeholder = (ctx, t) => {
      const type = types[key];
      const k = (type.rooms || []).reduce((acc, r, i) => (r.at && t >= r.at[0] ? i : acc), -1);
      drawPlan(ctx, t, type, k, `${T(type.name, key)} cutaway, render frames into frames/${type.frames || key}/`);
    };
    s.after = (t) => {
      const type = types[key];
      const rooms = type.rooms || [];
      const k = rooms.findIndex((r) => r.at && t >= r.at[0] && t <= r.at[1]);
      if (k === lastRoom) return; // update the live region only when the room changes
      lastRoom = k;
      const room = rooms[k];
      cap.classList.toggle("off", !room?.caption);
      cap.setAttribute("aria-hidden", String(!room?.caption));
      if (room?.caption) {
        cap.children[0].textContent = T(type.name, key);
        cap.children[1].textContent = T(room.name, "");
        cap.children[2].textContent = room.caption;
      }
      rail.querySelectorAll("button").forEach((b) => b.toggleAttribute("aria-current", b.textContent === room?.name));
    };
    registerScrub(s);
    setType(sec.default && types[sec.default] ? sec.default : keys[0]);
    registry[sec.id] = { setType, node, has: (k) => !!types[k] };
    return node;
  };

  builders.picker = (sec) => {
    const units = sec.units || [];
    if (!units.length) throw new Error("picker needs units");
    const still = typeof sec.image === "string" ? { image: sec.image } : F[sec.image?.frames || sec.frames]?.desktop || sec.image || null;
    const hotspots = still?.hotspots || {};
    const node = el("section", { id: sec.id, class: "band" }, head(sec));
    const box = el("div", { class: "picker" });
    const spots = el("div", { class: "hotspots" });
    const panel = el("aside", { class: "unit-panel", "aria-live": "polite" }, el("p", { class: "muted", text: T(sec.prompt, "Select one to see its details.") }));
    if (still?.image) {
      if (still.w && still.h) box.style.aspectRatio = `${still.w} / ${still.h}`;
      const img = el("img", { src: still.image, alt: T(sec.alt, ""), loading: "lazy", decoding: "async" });
      img.onload = () => { box.style.aspectRatio = `${img.naturalWidth} / ${img.naturalHeight}`; }; // hotspots are % of this exact image
      box.append(img);
    } else {
      const c = el("canvas", { role: "img", "aria-label": T(sec.alt, "Placeholder building") });
      box.append(c);
      const draw = () => { const r = c.getBoundingClientRect(), d = dpr(); c.width = r.width * d; c.height = r.height * d; drawTower(c.getContext("2d"), 0, sec.placeholder || {}, "picker still"); };
      requestAnimationFrame(draw);
      addEventListener("resize", draw);
    }
    box.append(spots);
    const labels = sec.labels || {};
    units.forEach((u) => {
      const pos = (u.anchor && hotspots[u.anchor]) || (u.x !== undefined ? [u.x, u.y] : null);
      if (!pos) { console.warn("no position for", u.id); return; }
      const free = !u.status || /avail/i.test(u.status);
      const b = el("button", {
        type: "button", class: "hotspot" + (free ? "" : " taken"), "aria-pressed": "false",
        style: { left: pos[0] + "%", top: pos[1] + "%" },
        "aria-label": [T(labels.unit, "Residence"), u.id, u.typeName, u.status].filter(Boolean).join(", ")
      }, el("span", { text: T(u.label || u.id, "") }), !free && el("small", { text: T(u.status, "") }));
      b.onclick = () => {
        spots.querySelectorAll(".hotspot").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        const fields = (sec.fields || []).filter((f) => u[f.key] !== undefined);
        const h = el("h3", { tabindex: "-1", text: `${T(labels.unit, "Residence")} ${T(u.label || u.id, "")}` });
        const target = sec.link && registry[sec.link];
        panel.replaceChildren(
          u.status && el("p", { class: "eyebrow", text: u.status }), h,
          fields.length && el("dl", {}, fields.map((f) => [el("dt", { text: f.label }), el("dd", { text: T(u[f.key]) + (u[f.key] != null && f.unit ? " " + f.unit : "") })])),
          target && u.type && target.has(u.type) && el("button", {
            type: "button", class: "btn", text: T(labels.cta, "See inside"),
            onclick: () => { target.setType(u.type); target.node.scrollIntoView({ behavior: reduced ? "auto" : "smooth" }); }
          }));
        h.focus({ preventScroll: true });
      };
      spots.append(b);
    });
    node.append(el("div", { class: "picker-wrap" }, box, panel));
    return node;
  };

  builders.stats = (sec) => {
    if (!sec.items?.length) throw new Error("stats needs items");
    return el("section", { id: sec.id, class: "band stats" }, head(sec),
      el("dl", { class: "stat-row" }, sec.items.map((i) => el("div", {}, el("dt", { text: T(i.label, "") }), el("dd", { text: T(i.value) })))));
  };

  builders.specs = (sec) => {
    if (!sec.items?.length) throw new Error("specs needs items");
    return el("section", { id: sec.id, class: "band" }, head(sec),
      el("ul", { class: "finishes" }, sec.items.map((f) => el("li", {},
        el("div", { class: "area", text: T(f.area, "") }),
        el("div", { class: "item", text: T(f.item, "") }),
        el("div", { class: "muted small", text: [T(f.supplier), T(f.code)].join(" · ") })))));
  };

  builders.compare = (sec) => {
    const pairs = sec.pairs || [];
    if (!pairs.length) throw new Error("compare needs pairs");
    const range = el("input", { type: "range", min: "0", max: "100", value: "50", "aria-label": T(sec.sliderLabel, "Drag to compare") });
    const before = el("div", { class: "pane before" }), after = el("div", { class: "pane after" });
    const box = el("div", { class: "compare" }, before, after, el("div", { class: "handle", "aria-hidden": "true" }), range);
    const tabs = el("div", { class: "compare-tabs", role: "group", "aria-label": T(sec.tabsLabel, "Choose") });
    let cur = pairs[0];
    const update = () => {
      box.style.setProperty("--pos", range.value + "%");
      range.setAttribute("aria-valuetext", `${100 - range.value}% ${T(cur.before?.label, "before")}, ${range.value}% ${T(cur.after?.label, "after")}`);
    };
    range.oninput = update;
    const fill = (pane, side) => {
      pane.replaceChildren(
        side?.src ? el("img", { src: side.src, alt: T(side.alt, side.label || ""), loading: "lazy", decoding: "async" }) : el("div", { class: "ph" }),
        el("span", { class: "tag", text: T(side?.label, "") }));
    };
    const show = (p) => {
      cur = p;
      fill(before, p.before); fill(after, p.after);
      tabs.querySelectorAll("button").forEach((b, i) => b.setAttribute("aria-pressed", String(pairs[i] === p)));
      update();
    };
    if (pairs.length > 1) pairs.forEach((p) => tabs.append(el("button", { type: "button", text: T(p.label, ""), onclick: () => show(p) })));
    const node = el("section", { id: sec.id, class: "band" }, head(sec), tabs, box);
    show(pairs[0]);
    return node;
  };

  function head(sec) {
    const c = sec.copy || {};
    return el("div", { class: "band-head" },
      c.eyebrow && el("p", { class: "eyebrow", text: c.eyebrow }),
      c.title && el("h2", { text: c.title }),
      c.text && el("p", { class: "muted", text: c.text }));
  }

  // ---------- Build the page from the section list
  const main = $("main"), nav = $(".top nav");
  for (const sec of P.sections || []) {
    if (sec.off) continue;
    const build = builders[sec.kind];
    try {
      if (!build) throw new Error(`unknown section kind "${sec.kind}"`);
      if (!sec.id) throw new Error("section needs an id");
      main.append(build(sec));
      if (sec.nav) nav.append(el("a", { href: "#" + sec.id, text: sec.nav }));
    } catch (e) {
      console.error(`Section "${sec.id || sec.kind}" skipped:`, e.message);
    }
  }
  if (P.enquire?.href) nav.append(el("a", { class: "enquire", href: safeHref(P.enquire.href), text: T(P.enquire.label, "Enquire") }));
  $(".footer-disclaimer").textContent = disclaimer;
  kick();
})();
