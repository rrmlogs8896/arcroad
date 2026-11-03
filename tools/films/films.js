/* arcroad home-page films: five scenes rendered offline, frame by frame, from a time value.
 * Render page only (tools/films/render.py); the published output is the encoded video.
 *
 * Every number on screen is measured or derived from a measurement:
 *   S18 a→b 1,579.5 m / 193 s, b→a 1,546.0 m / 692 s, straight 13.1 m  (data/field/2026-11-01-results.json)
 *   S12 a→b 1,951.2 m / 245 s, straight 17.4 m                         (data/field/2026-11-02-results.json)
 *   Yearly cost: same constants as web/ticker.js (petrol Rs 116.15/l, 50 km/l, 22 working days a month)
 *   Option lengths: computed here from the same route drawing as web/drive/ ("illustration, not a design")
 * Roads are drawn straight and scaled so the route length equals the driven length, as on /drive/.
 * Vehicles, buildings and lights are made up. No brands, no plates, no people.
 */
(function () {
  'use strict';
  var T3 = window.THREE, W = 1920, H = 1080, DPR = 2;
  var film = (location.search.match(/film=(\w+)/) || [])[1] || 'thread';
  var $ = function (id) { return document.getElementById(id); };

  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function col(hex) { return new T3.Color(hex).convertSRGBToLinear(); }
  function cl(t) { return Math.max(0, Math.min(1, t)); }
  function sm(t) { t = cl(t); return t * t * (3 - 2 * t); }
  function ease(t) { t = cl(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function band(t, a, b, f) { return sm((t - a) / f) * (1 - sm((t - b) / f)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function inr(n) { return Math.round(n).toLocaleString('en-IN'); }

  // ---------------- renderer ----------------
  var R = new T3.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  R.setPixelRatio(DPR); R.setSize(W, H); R.outputEncoding = T3.sRGBEncoding;
  $('c').appendChild(R.domElement);
  var cam = new T3.PerspectiveCamera(40, W / H, 0.5, 20000);

  // ---------------- shared textures ----------------
  var GLOW = (function () { var c = document.createElement('canvas'); c.width = c.height = 256; var g = c.getContext('2d');
    var gr = g.createRadialGradient(128, 128, 0, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,255,255,0.55)');
    gr.addColorStop(0.45, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
    return new T3.CanvasTexture(c); })();
  function glow(hex, size, op) { var s = new T3.Sprite(new T3.SpriteMaterial({ map: GLOW, color: col(hex), blending: T3.AdditiveBlending, transparent: true, depthWrite: false, opacity: op == null ? 1 : op }));
    s.scale.set(size, size, 1); return s; }
  function label(text, hex, h) {
    var c = document.createElement('canvas'), g = c.getContext('2d'); c.width = 1024; c.height = 160;
    g.font = '600 84px Inter, system-ui, sans-serif'; var w = Math.min(1010, g.measureText(text).width + 96), x = (1024 - w) / 2;
    g.fillStyle = 'rgba(8,10,14,0.82)'; g.beginPath(); if (g.roundRect) g.roundRect(x, 12, w, 136, 68); else g.rect(x, 12, w, 136); g.fill();
    g.strokeStyle = hex; g.lineWidth = 4; g.stroke(); g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 512, 82);
    var t = new T3.CanvasTexture(c); t.encoding = T3.sRGBEncoding; t.anisotropy = 8;
    var s = new T3.Sprite(new T3.SpriteMaterial({ map: t, depthTest: false, transparent: true })); s.scale.set(h * 6.4, h, 1); s.renderOrder = 20; return s;
  }

  // ---------------- road geometry (same drawing as web/drive/drive.js) ----------------
  var LANES = [3.0, 6.5, 10.0], MED = 1.25, EDGE = 11.75;
  function route(L, half) {
    var A = [-half, 0], B = [half, 0];
    var px = [], pz = [], step = 0.25, z, t, f, shx = Math.min(60, Math.max(3, L * 0.45));
    for (z = 0; z > -shx; z -= step) { px.push(A[0] + (-LANES[0] - A[0]) * sm(-z / shx)); pz.push(z); }
    for (z = -shx; z > -L; z -= step) { px.push(-LANES[0]); pz.push(z); }
    for (f = Math.PI; f > 0; f -= step / LANES[0]) { px.push(LANES[0] * Math.cos(f)); pz.push(-L - LANES[0] * Math.sin(f)); }
    for (z = -L; z < -shx; z += step) { px.push(LANES[0]); pz.push(z); }
    for (z = -shx; z <= 0.001; z += step) { t = (z + shx) / shx; px.push(LANES[0] + (B[0] - LANES[0]) * sm(t)); pz.push(z); }
    var ps = [0], i; for (i = 1; i < px.length; i++) ps.push(ps[i - 1] + Math.hypot(px[i] - px[i - 1], pz[i] - pz[i - 1]));
    return { x: px, z: pz, s: ps, len: ps[ps.length - 1], L: L, half: half };
  }
  function fit(target, half) { var lo = 3, hi = 3000, k; for (k = 0; k < 44; k++) { var mid = (lo + hi) / 2; if (route(mid, half).len > target) hi = mid; else lo = mid; } return route((lo + hi) / 2, half); }
  function at(r, s) {
    s = Math.max(0, Math.min(r.len, s));
    var lo = 0, hi = r.s.length - 1; while (hi - lo > 1) { var m = (lo + hi) >> 1; if (r.s[m] < s) lo = m; else hi = m; }
    var f = (s - r.s[lo]) / ((r.s[hi] - r.s[lo]) || 1), x = r.x[lo] + (r.x[hi] - r.x[lo]) * f, z = r.z[lo] + (r.z[hi] - r.z[lo]) * f;
    var dx = r.x[hi] - r.x[lo], dz = r.z[hi] - r.z[lo], d = Math.hypot(dx, dz) || 1; return { x: x, z: z, hx: dx / d, hz: dz / d };
  }
  var S18 = { half: 13.1 / 2, ab: 1579.5, s: 193 }, S12 = { half: 17.4 / 2, ab: 1951.2, s: 245 };

  // ---------------- glowing ribbon: a flat strip whose width and drawn length are uniforms ----------------
  var RIB_V = 'attribute float side; attribute float along; attribute vec3 nrm; uniform float uW; varying float vSide; varying float vAlong;' +
    'void main(){ vSide = side; vAlong = along; vec3 p = position + nrm * side * uW; gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.0); }';
  var RIB_F = 'uniform vec3 uCol; uniform float uHead; uniform float uTail; uniform float uOp; uniform float uSoft; uniform float uChev; uniform float uTime; uniform float uLen;' +
    'varying float vSide; varying float vAlong;' +
    'void main(){ if (vAlong > uHead || vAlong < uTail) discard; float e = 1.0 - abs(vSide); float a = uSoft > 0.5 ? e * e * e : smoothstep(0.0, 0.35, e);' +
    ' float hd = smoothstep(uHead - 40.0, uHead, vAlong) * step(uHead, uLen - 0.5); float c = 1.0;' +
    ' if (uChev > 0.0) { float k = fract((vAlong - abs(vSide) * uChev * 0.6) / uChev - uTime); c = 0.55 + 0.45 * smoothstep(0.0, 0.12, k) * (1.0 - smoothstep(0.42, 0.55, k)); }' +
    ' gl_FragColor = vec4(uCol * (c + hd * 0.9), a * uOp); }';
  function ribbon(r, hex, opt) {
    opt = opt || {};
    var step = opt.step || 1, pts = [], s, i;
    for (s = 0; s <= r.len; s += step) pts.push(s); if (pts[pts.length - 1] < r.len) pts.push(r.len);
    var n = pts.length, pos = new Float32Array(n * 6), nrm = new Float32Array(n * 6), side = new Float32Array(n * 2), along = new Float32Array(n * 2), idx = [];
    for (i = 0; i < n; i++) {
      var p = at(r, pts[i]), y = opt.dip ? opt.dip(pts[i]) : (opt.y || 0.2);
      for (var k = 0; k < 2; k++) { pos[(i * 2 + k) * 3] = p.x; pos[(i * 2 + k) * 3 + 1] = y; pos[(i * 2 + k) * 3 + 2] = p.z;
        nrm[(i * 2 + k) * 3] = -p.hz; nrm[(i * 2 + k) * 3 + 2] = p.hx; side[i * 2 + k] = k ? 1 : -1; along[i * 2 + k] = pts[i]; }
      if (i < n - 1) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
    }
    var g = new T3.BufferGeometry(); g.setAttribute('position', new T3.BufferAttribute(pos, 3)); g.setAttribute('nrm', new T3.BufferAttribute(nrm, 3));
    g.setAttribute('side', new T3.BufferAttribute(side, 1)); g.setAttribute('along', new T3.BufferAttribute(along, 1)); g.setIndex(idx);
    function mat(soft) { return new T3.ShaderMaterial({ vertexShader: RIB_V, fragmentShader: RIB_F, transparent: true, depthWrite: false, depthTest: opt.depthTest !== false, blending: T3.AdditiveBlending,
      uniforms: { uCol: { value: col(hex) }, uHead: { value: r.len }, uTail: { value: -1 }, uOp: { value: 1 }, uSoft: { value: soft ? 1 : 0 }, uW: { value: 1 }, uChev: { value: opt.chev || 0 }, uTime: { value: 0 }, uLen: { value: r.len } } }); }
    var core = new T3.Mesh(g, mat(false)), halo = new T3.Mesh(g, mat(true)); core.renderOrder = 6; halo.renderOrder = 5; core.frustumCulled = halo.frustumCulled = false;
    var grp = new T3.Group(); grp.add(halo); grp.add(core);
    grp.set = function (o) { [core, halo].forEach(function (m, j) { var u = m.material.uniforms;
      if (o.head != null) u.uHead.value = o.head; if (o.tail != null) u.uTail.value = o.tail; if (o.time != null) u.uTime.value = o.time;
      if (o.w != null) u.uW.value = j ? o.w * 3.2 : o.w; if (o.op != null) u.uOp.value = j ? o.op * 0.42 : o.op; }); };
    grp.r = r; return grp;
  }

  // hairline road plan for the dark diagram scenes
  function plan(scene, half, gaps, z0, z1, hex) {
    var m = new T3.LineBasicMaterial({ color: col(hex || '#4A5463'), transparent: true, opacity: 1 }), segs = [];
    function seg(x0, za, x1, zb) { segs.push(x0, 0, za, x1, 0, zb); }
    [-1, 1].forEach(function (sd) { seg(sd * EDGE, z0, sd * EDGE, z1); seg(sd * (EDGE + 3.5), z0, sd * (EDGE + 3.5), z1); });
    var cuts = gaps.slice().sort(function (a, b) { return a - b; }), za = z0;
    cuts.forEach(function (z) { [-1, 1].forEach(function (sd) { seg(sd * MED, za, sd * MED, z - 7); }); seg(-MED, z - 7, MED, z - 7); seg(-MED, z + 7, MED, z + 7); za = z + 7; });
    [-1, 1].forEach(function (sd) { seg(sd * MED, za, sd * MED, z1); });
    var g = new T3.BufferGeometry(); g.setAttribute('position', new T3.Float32BufferAttribute(segs, 3));
    var lines = new T3.LineSegments(g, m); scene.add(lines);
    var dm = new T3.LineBasicMaterial({ color: col('#333B46') }), ds = [];
    [-4.75, -8.25, 4.75, 8.25].forEach(function (x) { for (var z = z0; z < z1; z += 9) ds.push(x, 0, z, x, 0, z + 3); });
    var dg = new T3.BufferGeometry(); dg.setAttribute('position', new T3.Float32BufferAttribute(ds, 3)); scene.add(new T3.LineSegments(dg, dm));
    var fill = new T3.Mesh(new T3.PlaneGeometry(EDGE * 2, z1 - z0), new T3.MeshBasicMaterial({ color: col('#0D1117'), transparent: true, opacity: 0.92, depthWrite: false }));
    fill.rotation.x = -Math.PI / 2; fill.position.set(0, -0.05, (z0 + z1) / 2); fill.renderOrder = 1; scene.add(fill);
    var grid = new T3.GridHelper(6000, 120, col('#18202B'), col('#131922')); grid.position.y = -0.2; grid.position.z = (z0 + z1) / 2; scene.add(grid);
    return { lines: lines, fill: fill, grid: grid };
  }
  function pin(scene, x, z, hex, size) { var g = glow(hex, size, 1); g.position.set(x, 0.5, z); g.renderOrder = 8; scene.add(g);
    var ring = new T3.Mesh(new T3.RingGeometry(0.75, 1, 64), new T3.MeshBasicMaterial({ color: col(hex), transparent: true, depthWrite: false, blending: T3.AdditiveBlending }));
    ring.rotation.x = -Math.PI / 2; ring.position.set(x, 0.3, z); scene.add(ring); return { g: g, ring: ring }; }

  // ---------------- HTML overlay helpers ----------------
  function ov(id, html, op, dy) { var e = $(id); if (html != null && e.innerHTML !== html) e.innerHTML = html; e.style.opacity = op; e.style.transform = 'translateY(' + ((1 - op) * (dy == null ? 14 : dy)) + 'px)'; }
  function fade(t, D) { $('fade').style.opacity = Math.max(1 - sm(t / 0.7), sm((t - (D - 0.7)) / 0.7)); }

  // =====================================================================
  // FILM: thread — the detour traced as a single line of light, from above
  // =====================================================================
  function filmThread() {
    var scene = new T3.Scene(); scene.background = col('#05070B');
    var r = fit(S18.ab, S18.half), gapN = -r.L - LANES[0];
    plan(scene, S18.half, [gapN, r.L + LANES[0]], gapN - 500, 500);
    var rib = ribbon(r, '#E2743B'); scene.add(rib);
    var a = pin(scene, -S18.half, 0, '#9AA0A6', 6), b = pin(scene, S18.half, 0, '#E2743B', 6);
    var head = glow('#FFD2B0', 10, 1); head.renderOrder = 9; scene.add(head);
    var straight = { len: 13.1, x: [-S18.half, S18.half], z: [0, 0], s: [0, 13.1] }; var line = ribbon(straight, '#FFFFFF', { step: 0.2, y: 0.4 }); scene.add(line);
    var D = 13;
    cam.fov = 30; cam.up.set(1, 0, 0); cam.updateProjectionMatrix();
    return { D: D, set: function (t) {
      var u = ease((t - 1.4) / 8.2), sHead = u * r.len, p = at(r, sHead);
      var far = sHead <= r.len / 2 ? Math.max(0, -p.z) : r.L + 6, fr = sm(far / (r.L + 6));
      var hgt = lerp(60, 1080, Math.pow(fr, 0.8)) * lerp(1, 0.96, sm((t - 10.2) / 2.5));
      var zc = lerp(0, -(r.L + 6) / 2 + 20, fr);
      cam.position.set(0, hgt, zc); cam.lookAt(0, 0, zc);
      var w = Math.max(0.3, hgt * 0.0024);
      rib.set({ head: sHead, w: w, op: 1 }); head.position.set(p.x, 0.6, p.z); head.scale.setScalar(w * 16); head.material.opacity = t > 1.4 && u < 0.999 ? 1 : lerp(1, 0, sm((t - 9.6) / 0.6)) * (t > 1.4 ? 1 : 0);
      [a, b].forEach(function (q) { q.g.scale.setScalar(w * 14); q.ring.scale.setScalar(w * (5 + 1.2 * Math.sin(t * 3))); });
      var lt = sm((t - 10.0) / 0.8); line.set({ head: 13.1 * lt, w: w * 1.15, op: lt });
      ov('eb', 'S18 · Hyderabad · driven 1 Nov 2026', sm((t - 0.6) / 0.8));
      var m = Math.round(sHead);
      ov('big', (t < 10.2 ? inr(m) : '13') + '<small>m</small>', sm((t - 1.2) / 0.6));
      ov('sub', t < 10.2 ? 'to get across' : 'straight across · <b>1,580 m</b> to get there', sm((t - 1.6) / 0.6));
      fade(t, D);
      R.render(scene, cam);
    } };
  }

  // =====================================================================
  // FILM: night — the S12 detour after dark (our 2 Nov drive was at night)
  // =====================================================================
  function filmNight() {
    var scene = new T3.Scene(), R1 = rng(1102);
    var r = fit(S12.ab, S12.half), gapN = -r.L - LANES[0], z0 = gapN - 260, z1 = 220;
    (function () { var c = document.createElement('canvas'); c.width = 4; c.height = 512; var g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 512);
      gr.addColorStop(0, '#020308'); gr.addColorStop(0.55, '#0A0F1C'); gr.addColorStop(0.72, '#1E2233'); gr.addColorStop(1, '#2A2028'); g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
      var tx = new T3.CanvasTexture(c); tx.encoding = T3.sRGBEncoding; scene.background = tx; })();
    scene.fog = new T3.Fog(col('#0C0F18'), 30, 330);
    scene.add(new T3.HemisphereLight(col('#3A4A70'), col('#140F0A'), 0.32));
    function flat(w, d, hex, x, y, z) { var m = new T3.Mesh(new T3.PlaneGeometry(w, d), new T3.MeshLambertMaterial({ color: col(hex) })); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); scene.add(m); return m; }
    flat(4000, 4000, '#07080A', 0, -0.3, (z0 + z1) / 2);
    flat(EDGE - MED, z1 - z0, '#16181C', -(EDGE + MED) / 2, 0, (z0 + z1) / 2); flat(EDGE - MED, z1 - z0, '#16181C', (EDGE + MED) / 2, 0, (z0 + z1) / 2);
    [-1, 1].forEach(function (sd) { flat(3.5, z1 - z0, '#202227', sd * (EDGE + 1.75), 0.1, (z0 + z1) / 2); });
    var lm = new T3.MeshBasicMaterial({ color: col('#6B6F76') }), dg = new T3.PlaneGeometry(0.14, 3); dg.rotateX(-Math.PI / 2);
    var dn = Math.ceil((z1 - z0) / 9) * 4, dash = new T3.InstancedMesh(dg, lm, dn), o = new T3.Object3D(), n = 0;
    [-4.75, -8.25, 4.75, 8.25].forEach(function (x) { for (var z = z0; z < z1; z += 9) { o.position.set(x, 0.03, z); o.updateMatrix(); dash.setMatrixAt(n++, o.matrix); } }); dash.count = n; scene.add(dash);
    // median with a gap at the U-turn
    var km = new T3.MeshLambertMaterial({ color: col('#2C2A24') });
    [[z0, gapN - 7], [gapN + 7, z1]].forEach(function (s) { var k = new T3.Mesh(new T3.BoxGeometry(MED * 2, 0.3, s[1] - s[0]), km); k.position.set(0, 0.15, (s[0] + s[1]) / 2); scene.add(k); });
    // sodium lamps on the median: head glow plus a warm pool on each carriageway
    var pool = new T3.MeshBasicMaterial({ map: GLOW, color: col('#FF9E45'), transparent: true, opacity: 0.22, blending: T3.AdditiveBlending, depthWrite: false });
    var pg = new T3.PlaneGeometry(26, 26); pg.rotateX(-Math.PI / 2);
    for (var z = z0 + 10; z < z1; z += 34) { if (Math.abs(z - gapN) < 9) continue;
      var pole = new T3.Mesh(new T3.BoxGeometry(0.16, 9, 0.16), new T3.MeshLambertMaterial({ color: col('#2B2E33') })); pole.position.set(0, 4.8, z); scene.add(pole);
      [-1, 1].forEach(function (sd) { var hg = glow('#FFB060', 5.5, 0.95); hg.position.set(sd * 2.1, 8.7, z); scene.add(hg); var core = glow('#FFE2B8', 1.1, 1); core.position.copy(hg.position); scene.add(core);
        var pm = new T3.Mesh(pg, pool); pm.position.set(sd * 5.2, 0.05, z); scene.add(pm); }); }
    // buildings as dark masses with lit windows
    var box = new T3.BoxGeometry(1, 1, 1); box.translate(0, 0.5, 0);
    var Bs = [], Ws = [];
    [-1, 1].forEach(function (sd) { var zz = z0; while (zz < z1) { var w = 7 + R1() * 15, h = [7, 10, 13, 16, 19, 22, 25][Math.floor(R1() * 7)], d = 10 + R1() * 12, x0 = sd * (EDGE + 5 + R1() * 2.5);
      Bs.push([x0 + sd * d / 2, zz + w / 2, w, h, d]);
      for (var f = 1; f < h / 3.1 - 0.4; f++) for (var q = 0; q < Math.floor(w / 2.4); q++) if (R1() < 0.42) Ws.push([x0 - sd * 0.05, f * 3.1 + 0.6, zz + 1.2 + q * 2.4, R1()]);
      zz += w + 0.4 + R1() * 1.2; } });
    var bm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: col('#1A1D24') }), Bs.length);
    Bs.forEach(function (b, i) { o.position.set(b[0], 0, b[1]); o.scale.set(b[4], b[3], b[2]); o.rotation.set(0, 0, 0); o.updateMatrix(); bm.setMatrixAt(i, o.matrix); }); scene.add(bm);
    var wg = new T3.PlaneGeometry(1.3, 1.4); var wm = new T3.InstancedMesh(wg, new T3.MeshBasicMaterial({ color: 0xffffff }), Ws.length);
    var wc = ['#FFC98A', '#FFB86B', '#FFE4BD', '#BFD4FF', '#FFD9A0'];
    Ws.forEach(function (w, i) { o.position.set(w[0], w[1], w[2]); o.rotation.set(0, w[0] < 0 ? Math.PI / 2 : -Math.PI / 2, 0); o.scale.set(1, 1, 1); o.updateMatrix(); wm.setMatrixAt(i, o.matrix);
      wm.setColorAt(i, col(wc[Math.floor(w[3] * 5)]).multiplyScalar(0.35 + 0.65 * w[3])); }); scene.add(wm);
    // vehicles: dark bodies, lights only
    var body = new T3.MeshLambertMaterial({ color: col('#121418') });
    function veh(len) { var g = new T3.Group(); var m = new T3.Mesh(new T3.BoxGeometry(1.8, 1.3, len), body); m.position.y = 0.75; g.add(m); g.userData.len = len; scene.add(g); return g; }
    function lights(g, hex, front, size) { [-0.62, 0.62].forEach(function (x) { var s = glow(hex, size, 1); s.position.set(x, 0.8, (front ? -1 : 1) * (g.userData.len / 2 + 0.15)); g.add(s); }); }
    function streak(g, hex, len) { var p = new T3.Mesh(new T3.PlaneGeometry(1.6, len), new T3.MeshBasicMaterial({ map: GLOW, color: col(hex), transparent: true, opacity: 0.35, blending: T3.AdditiveBlending, depthWrite: false }));
      p.rotation.x = -Math.PI / 2; p.position.set(0, 0.1, g.userData.len / 2 + len / 2); g.add(p); }
    var player = veh(4.2); lights(player, '#FF2A1A', false, 1.2); lights(player, '#FFF4DE', true, 2.2);
    var beam = new T3.Mesh(new T3.PlaneGeometry(9, 34), new T3.MeshBasicMaterial({ map: GLOW, color: col('#FFF0D0'), transparent: true, opacity: 0.32, blending: T3.AdditiveBlending, depthWrite: false }));
    beam.rotation.x = -Math.PI / 2; beam.position.set(0, 0.06, -19); player.add(beam);
    player.children.forEach(function (c) { c.visible = c === beam; });
    var same = [], opp = [];
    for (var i = 0; i < 14; i++) { var v = veh(R1() < 0.2 ? 8 : 4.2); lights(v, '#FF2A1A', false, 1.1); streak(v, '#FF3020', 14); same.push({ g: v, l: 1 + (i % 2), z0: -40 - i * 38 - R1() * 20, v: 12 + R1() * 5 }); }
    for (i = 0; i < 18; i++) { v = veh(R1() < 0.2 ? 8 : 4.2); lights(v, '#EAF2FF', true, 2.6); streak(v, '#CFE0FF', 10); v.children[3].position.z = -v.userData.len / 2 - 5; lights(v, '#FF2A1A', false, 1.1);
      opp.push({ g: v, l: i % 3, z0: z0 + i * 30 + R1() * 20, v: 15 + R1() * 6 }); }
    // pace: fast on the straight, slow through the U-turn; the shot covers the turn itself
    var s0 = r.L - 300, s1 = r.L + Math.PI * LANES[0] + 70, D = 12, TT = [0], SS = [s0];
    for (var s = s0; s < s1; s += 0.5) { var arc = s > r.L - 40 && s < r.L + Math.PI * LANES[0] + 20; var vv = arc ? 7 : 24; if (s > r.L - 90 && s <= r.L - 40) vv = lerp(24, 7, (s - (r.L - 90)) / 50);
      if (s >= r.L + Math.PI * LANES[0] + 20) vv = lerp(7, 20, cl((s - (r.L + Math.PI * LANES[0] + 20)) / 50)); TT.push(TT[TT.length - 1] + 0.5 / vv); SS.push(s + 0.5); }
    var tot = TT[TT.length - 1];
    function sAt(t) { var q = cl(t / D) * tot, lo = 0, hi = TT.length - 1; while (hi - lo > 1) { var m = (lo + hi) >> 1; if (TT[m] < q) lo = m; else hi = m; } return SS[lo] + (SS[hi] - SS[lo]) * (q - TT[lo]) / ((TT[hi] - TT[lo]) || 1); }
    cam.fov = 58; cam.near = 0.1; cam.up.set(0, 1, 0); cam.updateProjectionMatrix();
    return { D: D, set: function (t) {
      var s = sAt(t), p = at(r, s), back = at(r, s - 10);
      player.position.set(p.x, 0, p.z); player.rotation.y = Math.atan2(-p.hx, -p.hz);
      same.forEach(function (q) { var z = q.z0 - q.v * t; q.g.position.set(-LANES[q.l], 0, z); q.g.rotation.y = 0; q.g.visible = z > z0 && z < z1; });
      opp.forEach(function (q) { var z = ((q.z0 + q.v * t - z0) % (z1 - z0)) + z0; q.g.position.set(LANES[q.l], 0, z); q.g.rotation.y = Math.PI; });
      var ah = at(r, s + 16); cam.position.set(p.x, 1.3, p.z); cam.lookAt(ah.x, 1.1, ah.z);
      ov('eb', 'S12 · Hyderabad · driven after dark, 2 Nov 2026', sm((t - 0.7) / 0.8));
      ov('big', '1.95<small>km</small>', sm((t - 1.1) / 0.7));
      ov('sub', 'to cross <b>17 m</b>', sm((t - 1.5) / 0.7));
      fade(t, D); R.render(scene, cam);
    } };
  }

  // =====================================================================
  // FILM: orbit — from the whole planet down to 13 metres
  // =====================================================================
  function ll(lat, lon, rad) { var a = lat * Math.PI / 180, b = lon * Math.PI / 180; return new T3.Vector3(rad * Math.cos(a) * Math.cos(b), rad * Math.sin(a), -rad * Math.cos(a) * Math.sin(b)); }
  function filmOrbit() {
    var g1 = new T3.Scene(); g1.background = col('#04060A');
    var L = window.LAND || [], n = L.length / 2, pos = new Float32Array(n * 3), cc = new Float32Array(n * 3), i;
    for (i = 0; i < n; i++) { var v = ll(L[i * 2], L[i * 2 + 1], 1.001), lat = L[i * 2], lon = L[i * 2 + 1]; pos.set([v.x, v.y, v.z], i * 3);
      var india = lon > 68 && lon < 97.5 && lat > 6 && lat < 36, c = india ? col('#E2B08A') : col('#7D8BA0'); cc.set([c.r, c.g, c.b], i * 3); }
    var pg = new T3.BufferGeometry(); pg.setAttribute('position', new T3.BufferAttribute(pos, 3)); pg.setAttribute('color', new T3.BufferAttribute(cc, 3));
    var dot = (function () { var c = document.createElement('canvas'); c.width = c.height = 64; var g = c.getContext('2d'); g.fillStyle = '#fff'; g.beginPath(); g.arc(32, 32, 26, 0, 7); g.fill(); return new T3.CanvasTexture(c); })();
    var pm = new T3.PointsMaterial({ size: 0.0085, map: dot, vertexColors: true, transparent: true, alphaTest: 0.3, sizeAttenuation: true });
    g1.add(new T3.Points(pg, pm));
    g1.add(new T3.Mesh(new T3.SphereGeometry(0.996, 96, 64), new T3.MeshBasicMaterial({ color: col('#080C13') })));
    var atm = new T3.Mesh(new T3.SphereGeometry(1.06, 96, 64), new T3.ShaderMaterial({ side: T3.BackSide, transparent: true, blending: T3.AdditiveBlending, depthWrite: false,
      vertexShader: 'varying vec3 vN; void main(){ vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
      fragmentShader: 'varying vec3 vN; void main(){ float f = pow(max(0.0, 0.62 - dot(vN, vec3(0.0,0.0,1.0))), 3.0); gl_FragColor = vec4(vec3(0.30,0.50,0.95) * f * 1.6, 1.0); }' }));
    g1.add(atm);
    // cities on the globe (places.json) and the S18 pin
    var CITIES = [[17.385, 78.4867], [12.975, 77.625], [13.025, 80.15], [19.15, 73.0], [28.625, 77.2], [18.55, 73.85], [22.575, 88.375], [23.025, 72.6], [16.5, 80.525], [26.15, 91.8], [25.585, 85.15], [21.225, 81.7], [15.5, 73.875], [23.225, 72.65], [30.725, 76.8], [23.35, 85.325], [8.525, 76.95], [23.25, 77.425], [24.8, 93.95]];
    var cs = CITIES.map(function (c, k) { var s = glow(k ? '#E2743B' : '#FFD2B0', k ? 0.035 : 0.06, k ? 0.8 : 1); s.position.copy(ll(c[0], c[1], 1.004)); g1.add(s); return s; });
    var HYD = [17.4769, 78.3900], hyd = ll(HYD[0], HYD[1], 1);
    var rings = [0, 1, 2].map(function () { var m = new T3.Mesh(new T3.RingGeometry(0.965, 1, 128), new T3.MeshBasicMaterial({ color: col('#E2743B'), transparent: true, depthWrite: false, blending: T3.AdditiveBlending, side: T3.DoubleSide }));
      m.position.copy(ll(HYD[0], HYD[1], 1.0015)); m.lookAt(ll(HYD[0], HYD[1], 2)); g1.add(m); return m; });
    var hl = label('Hyderabad', '#E2743B', 0.05); g1.add(hl);
    // road scene (diagram, from above)
    var g2 = new T3.Scene(); g2.background = col('#05070B');
    var r = fit(S18.ab, S18.half), gapN = -r.L - LANES[0];
    plan(g2, S18.half, [gapN, r.L + LANES[0]], gapN - 600, 600);
    var rib = ribbon(r, '#E2743B'); g2.add(rib);
    var line = ribbon({ len: 13.1, x: [-S18.half, S18.half], z: [0, 0], s: [0, 13.1] }, '#FFFFFF', { step: 0.2, y: 0.4 }); g2.add(line);
    var pa = pin(g2, -S18.half, 0, '#9AA0A6', 6), pb = pin(g2, S18.half, 0, '#E2743B', 6);
    var lb13 = label('13 m', '#F5F6F7', 3.4); g2.add(lb13);
    var D = 13, cut = 7.0;
    return { D: D, set: function (t) {
      var sc;
      if (t < cut) {
        var u = ease(t / (cut - 0.2)), lat = lerp(-8, HYD[0], u), lon = lerp(36, HYD[1], u), dist = lerp(3.6, 1.14, Math.pow(u, 1.4)); pm.size = 0.0085 * Math.max(0.45, Math.min(1, (dist - 1) / 1.4));
        var cp = ll(lat - lerp(18, 0.0, u), lon, dist); cam.fov = 34; cam.near = 0.0001; cam.far = 50; cam.up.set(0, 1, 0); cam.updateProjectionMatrix();
        cam.position.copy(cp); cam.lookAt(ll(lerp(0, HYD[0], u), lerp(60, HYD[1], u), lerp(0, 1, sm((t - 1) / 5))));
        var k = sm((t - 2.6) / 1.2);
        rings.forEach(function (m, j) { var ph = ((t * 0.6 + j / 3) % 1); m.scale.setScalar(Math.max(0.0001, dist * 0.09 * ph + 0.0005)); m.material.opacity = k * (1 - ph); });
        cs.forEach(function (s, j) { var sz = (j ? 0.022 : 0.04) * Math.min(1, (dist - 0.99) * 1.4 + 0.02); s.scale.set(sz, sz, 1); });
        hl.position.copy(ll(HYD[0] + 0.0, HYD[1], 1.0 + (dist - 1) * 0.1)); var lh = Math.max(0.0002, (dist - 1) * 0.07); hl.scale.set(lh * 6.4, lh, 1); hl.material.opacity = k * (1 - sm((t - 5.0) / 0.5));
        sc = g1;
        ov('eb', 'One planet · 29 cities · one road', sm((t - 0.5) / 0.8) * (1 - sm((t - 5.9) / 0.6)));
        ov('big', '', 0); ov('sub', '', 0);
      } else {
        var w2 = (t - cut) / (D - cut), hgt = lerp(2400, 70, ease(cl(w2 / 0.62)));
        cam.fov = 32; cam.near = 0.5; cam.far = 20000; cam.up.set(1, 0, 0); cam.updateProjectionMatrix();
        var zc = lerp(-(r.L) / 2, 0, ease(cl(w2 / 0.62)));
        cam.position.set(0, hgt, zc); cam.lookAt(0, 0, zc);
        var wd = Math.max(0.3, hgt * 0.0024); rib.set({ w: wd, op: 1, head: r.len }); line.set({ w: wd * 1.15, op: sm((w2 - 0.55) / 0.15), head: 13.1 * sm((w2 - 0.55) / 0.15) });
        [pa, pb].forEach(function (q) { q.g.scale.setScalar(wd * 14); q.ring.scale.setScalar(wd * (5 + 1.2 * Math.sin(t * 3))); });
        lb13.position.set(0, 1, hgt * 0.16); lb13.scale.set(hgt * 0.07 * 6.4, hgt * 0.07, 1); lb13.material.opacity = sm((w2 - 0.62) / 0.12);
        sc = g2;
        ov('eb', 'S18 · Hyderabad', sm((w2 - 0.3) / 0.2));
        ov('big', '13<small>m</small>', sm((w2 - 0.6) / 0.15));
        ov('sub', 'apart · <b>1,580 m</b> to get there', sm((w2 - 0.66) / 0.15));
      }
      var fd = Math.max(1 - sm(t / 0.7), sm((t - (D - 0.7)) / 0.7), band(t, cut - 0.35, cut + 0.05, 0.3));
      $('fade').style.opacity = fd;
      R.render(sc, cam);
    } };
  }

  // =====================================================================
  // FILM: blueprint — the three options from /drive/ in one camera move
  // =====================================================================
  function filmBlueprint() {
    var scene = new T3.Scene(); scene.background = col('#06080D'); scene.fog = new T3.Fog(col('#06080D'), 260, 1300);
    var today = fit(S18.ab, S18.half), gapN = -today.L - LANES[0];
    var p0 = plan(scene, S18.half, [gapN, today.L + LANES[0]], gapN - 300, 400, '#5A6676');
    var tRib = ribbon(today, '#9AA0A6'); scene.add(tRib);
    var OPTS = [
      { k: 'Nearer U-turn', r: route(200, S18.half), hex: '#8FA89A', gap: -200 - LANES[0] },
      { k: 'Signal here', r: route(7, S18.half), hex: '#E2743B', gap: -7 - LANES[0] },
      { k: 'Underpass', r: route(110, S18.half), hex: '#7FB0E0', dip: true }
    ];
    OPTS.forEach(function (o) {
      o.rib = ribbon(o.r, o.hex, { chev: 6, depthTest: !o.dip, dip: o.dip ? function (s) { var mid = o.r.len / 2, d = Math.abs(s - mid) / (o.r.len / 2); return d > 0.82 ? 0.2 : -6 * sm((0.82 - d) / 0.3); } : null });
      o.rib.set({ op: 0 }); scene.add(o.rib);
      if (o.gap != null) { var m = new T3.Mesh(new T3.PlaneGeometry(MED * 2 + 0.3, 14), new T3.MeshBasicMaterial({ color: col(o.hex), transparent: true, opacity: 0, blending: T3.AdditiveBlending, depthWrite: false }));
        m.rotation.x = -Math.PI / 2; m.position.set(0, 0.05, o.gap); scene.add(m); o.cut = m; }
    });
    // signal heads for option 2
    var sig = new T3.Group(), lamps = [];
    [-1, 1].forEach(function (sd) { var pole = new T3.Mesh(new T3.BoxGeometry(0.25, 6, 0.25), new T3.MeshBasicMaterial({ color: col('#3A4350') })); pole.position.set(sd * (EDGE + 1.2), 3, -6); sig.add(pole);
      ['#FF3B30', '#FFB020', '#34C759'].forEach(function (h, j) { var s = glow(h, 2.4, 0); s.position.set(sd * (EDGE + 1.2), 6.6 - j * 0.8, -6); sig.add(s); lamps.push({ s: s, j: j }); }); });
    scene.add(sig);
    // underpass chamber: hairline box beneath the road
    var ch = new T3.LineSegments(new T3.EdgesGeometry(new T3.BoxGeometry(14, 6, 46)), new T3.LineBasicMaterial({ color: col('#7FB0E0'), transparent: true, opacity: 0 }));
    ch.position.set(0, -3.2, -110 - 3); scene.add(ch);
    var D = 15, seg = [[0.6, 5.0], [5.0, 9.6], [9.6, 14.4]];
    cam.fov = 38; cam.up.set(0, 1, 0); cam.updateProjectionMatrix();
    return { D: D, set: function (t) {
      var ang = lerp(-0.5, 0.75, t / D), look = new T3.Vector3(0, 0, -70), dist = 190;
      var k = 0; for (var q = 0; q < 3; q++) if (t >= seg[q][0]) k = q;
      var focus = [-104, -10, -58][k], fk = sm((t - seg[k][0]) / 1.2);
      look.z = lerp(k ? [-104, -10, -58][k - 1] : -104, focus, fk);
      dist = lerp(k ? [190, 95, 140][k - 1] : 190, [190, 95, 140][k], fk);
      var el = k === 2 ? lerp(0.62, 0.38, fk) : 0.62;
      cam.position.set(look.x + Math.sin(ang) * dist * Math.cos(el), dist * Math.sin(el), look.z + Math.cos(ang) * dist * Math.cos(el)); cam.lookAt(look);
      var w = 1.35;
      tRib.set({ w: w * 0.8, op: 0.6, time: t });
      OPTS.forEach(function (o, j) { var b = band(t, seg[j][0], seg[j][1] - 0.2, 0.5), grow = sm((t - seg[j][0]) / 1.6);
        o.rib.set({ w: w * 1.25, op: b * 1.15, head: o.r.len * grow, time: t * 0.9 }); if (o.cut) o.cut.material.opacity = b * 0.6; });
      var ub = band(t, seg[2][0], seg[2][1] - 0.2, 0.5); p0.fill.material.opacity = lerp(0.92, 0.45, ub); ch.material.opacity = ub * 0.9;
      var sb = band(t, seg[1][0], seg[1][1] - 0.2, 0.5), cyc = Math.floor(((t - seg[1][0]) * 0.9) % 3);
      lamps.forEach(function (l) { l.s.material.opacity = sb * (l.j === [2, 1, 0][cyc] ? 1 : 0.12); });
      var o = OPTS[k], m = Math.round(o.r.len), ttl = sm((t - seg[k][0] - 0.3) / 0.6) * (1 - sm((t - seg[k][1] + 0.9) / 0.5));
      ov('eb', 'What could fix S18 · illustration, not a design', sm((t - 0.5) / 0.8));
      ov('big', o.k, ttl);
      ov('sub', '<b>' + inr(m) + ' m</b> instead of 1,580 m', ttl);
      fade(t, D); R.render(scene, cam);
    } };
  }

  // =====================================================================
  // FILM: timelapse — one day on the road, and what a year of crossing costs
  // =====================================================================
  function filmTimelapse() {
    var scene = new T3.Scene(), R1 = rng(4040);
    var r = fit(S18.ab, S18.half), gapN = -r.L - LANES[0], z0 = -620, z1 = 420;
    var sky = document.createElement('canvas'); sky.width = 4; sky.height = 512; var sg = sky.getContext('2d'), stx = new T3.CanvasTexture(sky); stx.encoding = T3.sRGBEncoding; scene.background = stx;
    scene.fog = new T3.Fog(col('#d0c4b0'), 140, 900);
    var hemi = new T3.HemisphereLight(col('#dce8ff'), col('#7d6d55'), 0.85), sun = new T3.DirectionalLight(col('#ffe0b5'), 0.95); scene.add(hemi); scene.add(sun);
    function flat(w, d, hex, x, y, z) { var m = new T3.Mesh(new T3.PlaneGeometry(w, d), new T3.MeshLambertMaterial({ color: col(hex) })); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); scene.add(m); return m; }
    flat(5000, 5000, '#77705f', 0, -0.3, 0);
    flat(EDGE - MED, z1 - z0, '#4a4b4e', -(EDGE + MED) / 2, 0, (z0 + z1) / 2); flat(EDGE - MED, z1 - z0, '#4a4b4e', (EDGE + MED) / 2, 0, (z0 + z1) / 2);
    [-1, 1].forEach(function (sd) { flat(3.5, z1 - z0, '#a49a8a', sd * (EDGE + 1.75), 0.12, (z0 + z1) / 2); });
    var o = new T3.Object3D(), dg = new T3.PlaneGeometry(0.14, 3); dg.rotateX(-Math.PI / 2);
    var dash = new T3.InstancedMesh(dg, new T3.MeshBasicMaterial({ color: col('#e9e6dc') }), 4 * Math.ceil((z1 - z0) / 9)), n = 0;
    [-4.75, -8.25, 4.75, 8.25].forEach(function (x) { for (var z = z0; z < z1; z += 9) { o.position.set(x, 0.03, z); o.updateMatrix(); dash.setMatrixAt(n++, o.matrix); } }); dash.count = n; scene.add(dash);
    var km = new T3.MeshLambertMaterial({ color: col('#5d6b45') });
    [[z0, gapN - 7], [gapN + 7, z1]].forEach(function (s) { var k = new T3.Mesh(new T3.BoxGeometry(MED * 2, 0.4, s[1] - s[0]), km); k.position.set(0, 0.2, (s[0] + s[1]) / 2); scene.add(k); });
    var heads = [];
    for (var z = z0 + 10; z < z1; z += 34) { if (Math.abs(z - gapN) < 9) continue; var pole = new T3.Mesh(new T3.BoxGeometry(0.16, 9, 0.16), new T3.MeshLambertMaterial({ color: col('#7c8085') })); pole.position.set(0, 4.8, z); scene.add(pole);
      [-1, 1].forEach(function (sd) { var hg = glow('#FFB060', 6, 0); hg.position.set(sd * 2.1, 8.7, z); scene.add(hg); heads.push(hg); }); }
    var box = new T3.BoxGeometry(1, 1, 1); box.translate(0, 0.5, 0);
    var walls = ['#e8dcc4', '#efe6d2', '#d9c7a7', '#e3c9b6', '#cfd6d8', '#f1ede4', '#c9c1b2', '#e7d3a6'];
    var Bs = [], Ws = [];
    [-1, 1].forEach(function (sd) { var zz = z0; while (zz < z1) { var w = 7 + R1() * 15, h = [7, 10, 13, 16, 19, 22, 25][Math.floor(R1() * 7)], d = 10 + R1() * 12, x0 = sd * (EDGE + 5 + R1() * 2.5);
      Bs.push([x0 + sd * d / 2, zz + w / 2, w, h, d, walls[Math.floor(R1() * walls.length)]]);
      for (var f = 1; f < h / 3.1 - 0.4; f++) for (var q = 0; q < Math.floor(w / 2.4); q++) Ws.push([x0 - sd * 0.06, f * 3.1 + 0.6, zz + 1.2 + q * 2.4, R1()]);
      zz += w + 0.4 + R1() * 1.2; } });
    var bm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: 0xffffff }), Bs.length);
    Bs.forEach(function (b, i) { o.position.set(b[0], 0, b[1]); o.scale.set(b[4], b[3], b[2]); o.rotation.set(0, 0, 0); o.updateMatrix(); bm.setMatrixAt(i, o.matrix); bm.setColorAt(i, col(b[5])); }); scene.add(bm);
    var wg = new T3.PlaneGeometry(1.3, 1.4), wDay = new T3.InstancedMesh(wg, new T3.MeshLambertMaterial({ color: col('#45515c') }), Ws.length), lit = Ws.filter(function (w) { return w[3] < 0.45; });
    var wNight = new T3.InstancedMesh(wg, new T3.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: T3.AdditiveBlending, depthWrite: false }), lit.length);
    function place(mesh, list, dx) { list.forEach(function (w, i) { o.position.set(w[0] + (w[0] < 0 ? dx : -dx), w[1], w[2]); o.rotation.set(0, w[0] < 0 ? Math.PI / 2 : -Math.PI / 2, 0); o.scale.set(1, 1, 1); o.updateMatrix(); mesh.setMatrixAt(i, o.matrix); }); scene.add(mesh); }
    place(wDay, Ws, 0); place(wNight, lit, 0.03); lit.forEach(function (w, i) { wNight.setColorAt(i, col(['#FFC98A', '#FFB86B', '#FFE4BD', '#BFD4FF'][Math.floor(w[3] * 8.9) % 4])); });
    // traffic: boxes with lights; density follows the hour (made up shape: morning and evening peaks)
    var cols = ['#e9e9e6', '#c4c7cb', '#9ea3a8', '#4a4e54', '#1f2124', '#7b1e22', '#2b4a6b', '#c25a2a', '#e7bd26', '#3d8a41'];
    var NC = 220, cars = [], cbox = new T3.BoxGeometry(1, 1, 1); cbox.translate(0, 0.5, 0);
    var carM = new T3.InstancedMesh(cbox, new T3.MeshLambertMaterial({ color: 0xffffff }), NC); carM.frustumCulled = false; scene.add(carM);
    function lightPts(hex, size) { var g = new T3.BufferGeometry(); g.setAttribute('position', new T3.BufferAttribute(new Float32Array(NC * 3), 3));
      var m = new T3.Points(g, new T3.PointsMaterial({ map: GLOW, color: col(hex), size: size, transparent: true, opacity: 0, blending: T3.AdditiveBlending, depthWrite: false, sizeAttenuation: true }));
      m.frustumCulled = false; scene.add(m); return m; }
    var tails = lightPts('#FF2A1A', 3.2), fronts = lightPts('#EAF2FF', 5);
    for (var i = 0; i < NC; i++) { var len = R1() < 0.12 ? 9 : (R1() < 0.45 ? 2 : 4.2);
      cars.push({ c: i % 2, l: Math.floor(R1() * 3), z: z0 + R1() * (z1 - z0), v: 26 + R1() * 16, th: R1(), len: len, w: len < 3 ? 0.7 : 1.8, h: len < 3 ? 1.4 : (len > 8 ? 2.8 : 1.4) });
      carM.setColorAt(i, col(cols[Math.floor(R1() * cols.length)])); }
    var KEYS = [ // hour, top, mid, low, fog, sun colour, sun intensity, hemi intensity, night 0..1
      [5.0, '#0A0F1E', '#1C2236', '#3A2E3A', '#252433', '#ff9a6a', 0.0, 0.18, 1],
      [6.4, '#2E4A72', '#C98E7A', '#F4B07A', '#C8A28A', '#ffb27a', 0.55, 0.5, 0.35],
      [9.0, '#6F92B8', '#C2CCD0', '#E6D6BD', '#ddd0bb', '#ffe0b5', 0.95, 0.85, 0],
      [16.0, '#6C8DB2', '#C8C9C0', '#E8D4B5', '#ddcfb6', '#ffe0b5', 0.95, 0.85, 0],
      [18.2, '#2C3B66', '#B9736A', '#F09A5C', '#B98670', '#ff9a5a', 0.5, 0.5, 0.45],
      [19.4, '#070B18', '#18203A', '#3B2C3C', '#1E2030', '#ff8a5a', 0.0, 0.2, 1],
      [23.0, '#03050C', '#0B1020', '#1E1A26', '#121520', '#ff8a5a', 0.0, 0.15, 1]];
    function keyAt(h) { for (var k = 0; k < KEYS.length - 1; k++) if (h <= KEYS[k + 1][0]) { var a = KEYS[k], b = KEYS[k + 1], f = sm((h - a[0]) / (b[0] - a[0])); return { a: a, b: b, f: f }; } var L = KEYS[KEYS.length - 1]; return { a: L, b: L, f: 0 }; }
    function cmix(x, y, f) { return new T3.Color(x).lerp(new T3.Color(y), f); }
    function density(h) { var m = Math.exp(-Math.pow((h - 9.3) / 1.6, 2)), e = Math.exp(-Math.pow((h - 18.6) / 1.9, 2)); return 0.12 + 0.42 * (h > 6 && h < 22.5 ? 1 : 0.3) + 0.5 * m + 0.55 * e; }
    // yearly figures: one person, a round trip every working day (same inputs as web/ticker.js)
    var extraKm = (S18.ab + 1546.0 - 2 * 13.1) / 1000, mins = (193 + 692) / 60, days = 22 * 12;
    var yrKm = Math.round(extraKm * days), yrH = Math.round(mins * days / 60), yrRs = Math.round(extraKm / 50 * 116.15 * days);
    var D = 15;
    cam.fov = 30; cam.up.set(0, 1, 0); cam.updateProjectionMatrix();
    return { D: D, set: function (t) {
      var hr = lerp(5.2, 23.0, cl((t - 0.3) / (D - 3.2))), K = keyAt(hr), A = K.a, B = K.b, f = K.f;
      var gr = sg.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#' + cmix(A[1], B[1], f).getHexString()); gr.addColorStop(0.55, '#' + cmix(A[2], B[2], f).getHexString()); gr.addColorStop(1, '#' + cmix(A[3], B[3], f).getHexString());
      sg.fillStyle = gr; sg.fillRect(0, 0, 4, 512); stx.needsUpdate = true;
      scene.fog.color.copy(cmix(A[4], B[4], f).convertSRGBToLinear());
      var night = lerp(A[8], B[8], f); sun.color.copy(cmix(A[5], B[5], f).convertSRGBToLinear()); sun.intensity = lerp(A[6], B[6], f); hemi.intensity = lerp(A[7], B[7], f);
      var sa = (hr - 6) / 13 * Math.PI; sun.position.set(Math.cos(sa) * -1, Math.max(0.05, Math.sin(sa)), 0.35);
      heads.forEach(function (h) { h.material.opacity = night; }); wNight.material.opacity = night * 0.95;
      var dens = density(hr);
      var tp = tails.geometry.attributes.position.array, fp = fronts.geometry.attributes.position.array;
      cars.forEach(function (q, k) { var span = z1 - z0, dir = q.c ? 1 : -1, z = ((q.z + dir * q.v * t * 3) - z0) % span; if (z < 0) z += span; z += z0;
        var x = (q.c ? 1 : -1) * LANES[q.l], on = q.th < dens / 1.25;
        o.position.set(x, on ? 0.3 : -50, z); o.rotation.set(0, 0, 0); o.scale.set(q.w, q.h, q.len); o.updateMatrix(); carM.setMatrixAt(k, o.matrix);
        tp.set([x, on ? 0.9 : -50, z - dir * (q.len / 2 + 0.2)], k * 3); fp.set([x, on ? 0.9 : -50, z + dir * (q.len / 2 + 0.2)], k * 3); });
      carM.instanceMatrix.needsUpdate = true; tails.geometry.attributes.position.needsUpdate = true; fronts.geometry.attributes.position.needsUpdate = true;
      tails.material.opacity = night * 0.95; fronts.material.opacity = night * 0.9;
      var look = new T3.Vector3(0, 3, lerp(-260, -220, t / D));
      cam.position.set(lerp(-7, 5, t / D), 21 - t * 0.25, look.z + 250); cam.lookAt(look);
      var hh = Math.floor(hr), mm = Math.floor((hr - hh) * 60 / 5) * 5;
      ov('eb', 'S18 · one day, one crossing', sm((t - 0.5) / 0.8));
      var endK = sm((t - (D - 3.2)) / 0.7);
      ov('big', ('0' + hh).slice(-2) + ':' + ('0' + mm).slice(-2), sm((t - 0.9) / 0.6) * (1 - endK));
      ov('sub', 'A year of crossing, both ways, every working day', endK);
      $('row').innerHTML = '<div>' + inr(yrKm) + '<span>extra km</span></div><div>' + yrH + '<span>hours</span></div><div>₹' + inr(yrRs) + '<span>two-wheeler fuel</span></div>';
      $('row').style.opacity = sm((t - (D - 2.7)) / 0.6);
      if (endK > 0) $('big').style.height = (1 - endK) * 132 + 'px'; else $('big').style.height = '';
      fade(t, D); R.render(scene, cam);
    } };
  }

  var F = film === 'night' ? filmNight() : film === 'orbit' ? filmOrbit() : film === 'blueprint' ? filmBlueprint() : film === 'timelapse' ? filmTimelapse() : filmThread();
  window.FILM = { D: F.D, fps: 30, set: function (t) { F.set(t); return true; } };
  F.set(0);
})();
