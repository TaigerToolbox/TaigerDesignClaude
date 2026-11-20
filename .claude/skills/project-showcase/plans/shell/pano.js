/* Minimal equirectangular panorama viewer: WebGL, no dependencies, works offline.
   Drag or swipe to look, wheel or pinch to zoom, arrow keys too. Hotspots are DOM buttons placed by
   projecting their direction each frame. Yaw is degrees clockwise from the panorama's centre column. */
(function () {
  "use strict";
  var VS = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
  var FS = [
    "precision highp float;uniform sampler2D t;uniform vec2 r;uniform float yaw,pitch,f;",
    "void main(){vec2 q=(gl_FragCoord.xy/r)*2.-1.;q.x*=r.x/r.y;",
    "vec3 d=normalize(vec3(q.x,q.y,f));float cp=cos(pitch),sp=sin(pitch);",
    "d=vec3(d.x,d.y*cp+d.z*sp,-d.y*sp+d.z*cp);float cy=cos(yaw),sy=sin(yaw);",
    "d=vec3(d.x*cy+d.z*sy,d.y,-d.x*sy+d.z*cy);",
    "float lon=atan(d.x,d.z),lat=asin(clamp(d.y,-1.,1.));",
    "gl_FragColor=texture2D(t,vec2(.5+lon/6.2831853,.5-lat/3.1415927));}"
  ].join("");
  var R = Math.PI / 180;

  function Pano(box, onSpot) {
    this.box = box; this.onSpot = onSpot;
    this.canvas = box.querySelector("canvas"); this.spots = box.querySelector(".pano-spots");
    this.yaw = 0; this.pitch = 0; this.fov = 80; this.items = [];
    var gl = this.gl = this.canvas.getContext("webgl", { antialias: false });
    if (!gl) { this.fail("This browser can't show 360 panoramas (no WebGL)."); return; }
    var prog = gl.createProgram();
    [[gl.VERTEX_SHADER, VS], [gl.FRAGMENT_SHADER, FS]].forEach(function (s) {
      var sh = gl.createShader(s[0]); gl.shaderSource(sh, s[1]); gl.compileShader(sh); gl.attachShader(prog, sh);
    });
    gl.linkProgram(prog); gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    this.u = {}; var self = this;
    ["r", "yaw", "pitch", "f"].forEach(function (n) { self.u[n] = gl.getUniformLocation(prog, n); });
    this.tex = gl.createTexture();
    this.bind();
    new ResizeObserver(function () { self.draw(); }).observe(box);
  }

  Pano.prototype.fail = function (msg) {
    this.box.innerHTML = '<div class="placeholder"></div>';
    this.box.firstChild.textContent = msg;
  };

  Pano.prototype.bind = function () {
    var self = this, el = this.box, pts = new Map(), last = null, pinch = null;
    el.tabIndex = 0;
    el.addEventListener("pointerdown", function (e) {
      if (e.target.closest(".spot")) return;
      el.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]);
      if (pts.size === 2) { var a = Array.from(pts.values()); pinch = { d: Math.hypot(a[0][0] - a[1][0], a[0][1] - a[1][1]), fov: self.fov }; }
    });
    el.addEventListener("pointermove", function (e) {
      if (!pts.has(e.pointerId)) return;
      var prev = pts.get(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]);
      if (pts.size === 2 && pinch) {
        var a = Array.from(pts.values());
        self.zoom(pinch.fov * pinch.d / Math.max(20, Math.hypot(a[0][0] - a[1][0], a[0][1] - a[1][1])), true);
        return;
      }
      var k = self.fov / el.clientHeight;  // degrees per pixel at this zoom
      self.yaw -= (e.clientX - prev[0]) * k; self.pitch += (e.clientY - prev[1]) * k; self.draw();
    });
    var up = function (e) { pts.delete(e.pointerId); if (pts.size < 2) pinch = null; };
    el.addEventListener("pointerup", up); el.addEventListener("pointercancel", up);
    el.addEventListener("wheel", function (e) { e.preventDefault(); self.zoom(self.fov * Math.exp(e.deltaY * 0.001)); }, { passive: false });
    el.addEventListener("keydown", function (e) {
      var m = { ArrowLeft: [-5, 0], ArrowRight: [5, 0], ArrowUp: [0, 5], ArrowDown: [0, -5] }[e.key];
      if (m) { e.preventDefault(); self.yaw += m[0]; self.pitch += m[1]; self.draw(); }
    });
  };

  Pano.prototype.zoom = function (fov) { this.fov = Math.max(30, Math.min(100, fov)); this.draw(); };

  Pano.prototype.show = function (p) {
    var self = this, gl = this.gl;
    if (!gl) return;
    this.items = p.hotspots || []; this.yaw = p.yaw || 0; this.pitch = 0; this.fov = 80;
    this.spots.innerHTML = "";
    this.items.forEach(function (h) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "spot";
      b.textContent = h.label; var s = document.createElement("small"); s.textContent = h.dist ? h.dist + " m" : "";
      b.appendChild(s);
      b.addEventListener("click", function () { self.onSpot && self.onSpot(h.to); });
      h.el = b; self.spots.appendChild(b);
    });
    var img = new Image();
    img.onload = function () {
      gl.bindTexture(gl.TEXTURE_2D, self.tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
      var pot = (img.width & (img.width - 1)) === 0 && (img.height & (img.height - 1)) === 0;
      if (pot) { gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); }
      else gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, pot ? gl.REPEAT : gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      self.ready = true; self.draw();
    };
    img.onerror = function () { self.fail("Panorama image missing: " + p.src); };
    img.src = p.src;
  };

  Pano.prototype.draw = function () {
    var gl = this.gl, c = this.canvas, self = this;
    if (!gl || !this.ready) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = Math.round(c.clientWidth * dpr), h = Math.round(c.clientHeight * dpr);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    this.pitch = Math.max(-85, Math.min(85, this.pitch));
    var f = 1 / Math.tan(this.fov * R / 2);
    gl.viewport(0, 0, w, h);
    gl.uniform2f(this.u.r, w, h); gl.uniform1f(this.u.yaw, this.yaw * R); gl.uniform1f(this.u.pitch, this.pitch * R); gl.uniform1f(this.u.f, f);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    var cw = c.clientWidth, ch = c.clientHeight, asp = cw / ch;
    this.items.forEach(function (it) {
      // world direction -> camera space (inverse of the shader's yaw then pitch)
      var y = (it.yaw - self.yaw) * R, pt = it.pitch * R;
      var d = [Math.cos(pt) * Math.sin(y), Math.sin(pt), Math.cos(pt) * Math.cos(y)];
      var cp = Math.cos(-self.pitch * R), sp = Math.sin(-self.pitch * R);
      d = [d[0], d[1] * cp + d[2] * sp, -d[1] * sp + d[2] * cp];
      if (d[2] <= 0.05) { it.el.style.display = "none"; return; }
      var x = (d[0] / d[2]) * f / asp, yy = (d[1] / d[2]) * f;
      it.el.style.display = Math.abs(x) > 1.1 || Math.abs(yy) > 1.1 ? "none" : "";
      it.el.style.left = ((x + 1) / 2 * 100) + "%"; it.el.style.top = ((1 - yy) / 2 * 100) + "%";
    });
  };

  window.Pano = Pano;
})();
