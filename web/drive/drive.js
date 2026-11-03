/* arcroad · 13 metres across: ride the detour we drove at S18.
 *
 * Every number shown comes from the 1 Nov 2026 field drive (data/field/2026-11-01-results.json):
 *   S18 a→b (west side to east side): 1,579.5 m in 193 s; b→a: 1,546.0 m in 692 s; straight 13.1 m.
 * The road is drawn straight and scaled so the route length equals the driven length. Where the car
 * slows and stops is illustrated; the total time equals the driven time. Vehicles, buildings and trees
 * are made up. Traffic density is set to match each pass's average speed (about 29 and 8 km/h).
 * Monthly figures reuse the cost calculator's constants (web/cost/index.html).
 * Three.js r147 (MIT), self-hosted. No network, no storage, no tracking.
 */
(function () {
  'use strict';
  var T3 = window.THREE;
  var host = document.getElementById('stage');
  if (!T3 || !host) return;
  var $ = function (id) { return document.getElementById(id); };
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------------- measured data ----------------
  var STRAIGHT = 13.1;
  var DRIVES = {
    ab: { m: 1579.5, s: 193, model: 1571.7, from: 'west side', to: 'east side', ev: 'Driven by arcroad · 1 Nov 2026 · matched the model (1.57 km) · single pass, candidate until repeated',
          cost: '../cost/?place=S18%20west%20to%20east&veh=tw&km=1.57&min=3' },
    ba: { m: 1546.0, s: 692, model: 1378.3, from: 'east side', to: 'west side', ev: 'Driven by arcroad · 1 Nov 2026 · matched the model (1.38 km) · backed by photos',
          cost: '../cost/?place=S18%20east%20to%20west&veh=tw&km=1.53&min=12' }
  };
  var COST = { petrol: 116.15, tw: 50, car: 16, days: 22 }; // same as web/cost/ (16 Oct 2026 price)

  // ---------------- small helpers ----------------
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  var R0 = rng(20261101);
  function rr(a, b) { return a + (b - a) * R0(); }
  function pick(arr) { return arr[Math.floor(R0() * arr.length)]; }
  function col(hex) { return new T3.Color(hex).convertSRGBToLinear(); }
  function smooth(t) { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); }
  function fmtM(m) { return Math.round(m).toLocaleString('en-IN') + ' m'; }
  function fmtClock(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function fmtDur(s) { s = Math.round(s); var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    return h ? h + ' h ' + m + ' min' : (m ? m + ' min ' + x + ' s' : x + ' s'); }

  // Merge non-indexed coloured parts into one geometry (one draw call per vehicle type).
  function Parts() { this.list = []; }
  Parts.prototype.box = function (cx, cy, cz, sx, sy, sz, hex, m4) {
    var g = new T3.BoxGeometry(sx, sy, sz).toNonIndexed();
    if (m4) g.applyMatrix4(m4);
    g.translate(cx, cy, cz); this.list.push([g, col(hex)]); return this;
  };
  Parts.prototype.geo = function (g, cx, cy, cz, hex) { g = g.toNonIndexed(); g.translate(cx, cy, cz); this.list.push([g, col(hex)]); return this; };
  Parts.prototype.build = function () {
    var n = 0, i, k; for (i = 0; i < this.list.length; i++) n += this.list[i][0].attributes.position.count;
    var pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), cl = new Float32Array(n * 3), o = 0;
    for (i = 0; i < this.list.length; i++) {
      var g = this.list[i][0], c = this.list[i][1], p = g.attributes.position.array, q = g.attributes.normal.array;
      pos.set(p, o * 3); nor.set(q, o * 3);
      for (k = 0; k < g.attributes.position.count; k++) { cl[(o + k) * 3] = c.r; cl[(o + k) * 3 + 1] = c.g; cl[(o + k) * 3 + 2] = c.b; }
      o += g.attributes.position.count; g.dispose();
    }
    var out = new T3.BufferGeometry();
    out.setAttribute('position', new T3.BufferAttribute(pos, 3));
    out.setAttribute('normal', new T3.BufferAttribute(nor, 3));
    out.setAttribute('color', new T3.BufferAttribute(cl, 3));
    return out;
  };
  var VC = new T3.MeshLambertMaterial({ vertexColors: true });

  // ---------------- road layout (metres; x east, -z north) ----------------
  var MED = 1.25;                       // half median width
  var LANES = [3.0, 6.5, 10.0];         // lane centres from the road axis
  var EDGE = 11.75, WALK = 15.25, FRONT = 17;
  var A = [-6.5, 0], B = [6.5, 0];      // 13 m apart, as measured

  // Route a→b: merge to the inner lane, run to the gap, U-turn round the median end, come back.
  function route(L) {
    var px = [], pz = [], step = 0.25, z, t, f;
    for (z = 0; z > -60; z -= step) { px.push(A[0] + (-LANES[0] - A[0]) * smooth(-z / 60)); pz.push(z); }
    for (z = -60; z > -L; z -= step) { px.push(-LANES[0]); pz.push(z); }
    for (f = Math.PI; f > 0; f -= step / LANES[0]) { px.push(LANES[0] * Math.cos(f)); pz.push(-L - LANES[0] * Math.sin(f)); }
    for (z = -L; z < -60; z += step) { px.push(LANES[0]); pz.push(z); }
    for (z = -60; z <= 0.001; z += step) { t = (z + 60) / 60; px.push(LANES[0] + (B[0] - LANES[0]) * smooth(t)); pz.push(z); }
    var ps = [0], i; for (i = 1; i < px.length; i++) ps.push(ps[i - 1] + Math.hypot(px[i] - px[i - 1], pz[i] - pz[i - 1]));
    return { x: px, z: pz, s: ps, len: ps[ps.length - 1], L: L };
  }
  function fit(target) { var lo = 70, hi = 2000, r, k; for (k = 0; k < 40; k++) { var mid = (lo + hi) / 2; r = route(mid); if (r.len > target) hi = mid; else lo = mid; } return route((lo + hi) / 2); }
  var RT = { ab: fit(DRIVES.ab.m), ba: null };
  (function () { var r = fit(DRIVES.ba.m); // b→a is the mirror (start at B heading south, gap to the south)
    r.x = r.x.map(function (v) { return -v; }); r.z = r.z.map(function (v) { return -v; }); RT.ba = r; })();
  var GAP_N = -RT.ab.L - LANES[0], GAP_S = RT.ba.L + LANES[0];     // centres of the two median gaps
  var ZMIN = GAP_N - 330, ZMAX = GAP_S + 330;

  function at(r, s) { // position and heading at distance s along route r
    s = Math.max(0, Math.min(r.len, s));
    var lo = 0, hi = r.s.length - 1; while (hi - lo > 1) { var m = (lo + hi) >> 1; if (r.s[m] < s) lo = m; else hi = m; }
    var f = (s - r.s[lo]) / ((r.s[hi] - r.s[lo]) || 1);
    var x = r.x[lo] + (r.x[hi] - r.x[lo]) * f, z = r.z[lo] + (r.z[hi] - r.z[lo]) * f;
    var dx = r.x[hi] - r.x[lo], dz = r.z[hi] - r.z[lo], d = Math.hypot(dx, dz) || 1;
    return { x: x, z: z, hx: dx / d, hz: dz / d };
  }

  // ---------------- pace: total time equals the driven time ----------------
  function pace(dir) {
    var r = RT[dir], S = Math.ceil(r.len), T = DRIVES[dir].s, heavy = dir === 'ba';
    var a0 = 60 + (r.L - 60), a1 = a0 + Math.PI * LANES[0];           // arc start and end along the route
    var w = new Float64Array(S + 1), i, stops = [];
    for (i = 0; i <= S; i++) {
      var v = 1;
      if (i < 40) v *= 1 + 2 * (1 - i / 40);
      if (S - i < 50) v *= 1 + 2.5 * (1 - (S - i) / 50);
      if (i > a0 - 60 && i <= a0) v *= 1 + 2.2 * (i - (a0 - 60)) / 60;
      if (i > a0 && i < a1) v *= 3.5;
      if (i >= a1 && i < a1 + 40) v *= 1 + 1.5 * (1 - (i - a1) / 40);
      if (heavy) { var sn = Math.sin(i / 47); v *= 1 + 1.4 * sn * sn; if (i > a0 - 260 && i <= a0) v *= 2.6; }
      w[i] = v;
    }
    if (heavy) stops = [[Math.round(S * 0.16), 18], [Math.round(S * 0.31), 26], [Math.round(a0 - 120), 30], [Math.round(a0), 45], [Math.round(S * 0.8), 22]];
    else stops = [[Math.round(a0), 7]];
    var sumW = 0, sumStop = 0; for (i = 0; i <= S; i++) sumW += w[i]; stops.forEach(function (x) { sumStop += x[1]; });
    var k = (T - sumStop) / sumW, TT = [0], SS = [0], t = 0, si = 0;
    stops.sort(function (p, q) { return p[0] - q[0]; });
    for (i = 0; i < S; i++) {
      while (si < stops.length && stops[si][0] === i) { t += stops[si][1]; TT.push(t); SS.push(i); si++; }
      t += w[i] * k * (Math.min(i + 1, r.len) - i); TT.push(t); SS.push(Math.min(i + 1, r.len));
    }
    var scale = T / t; for (i = 0; i < TT.length; i++) TT[i] *= scale;
    return { T: T, t: TT, s: SS };
  }
  var PACE = { ab: pace('ab'), ba: pace('ba') };
  function sAt(p, t) {
    if (t <= 0) return 0; if (t >= p.T) return p.s[p.s.length - 1];
    var lo = 0, hi = p.t.length - 1; while (hi - lo > 1) { var m = (lo + hi) >> 1; if (p.t[m] < t) lo = m; else hi = m; }
    var d = p.t[hi] - p.t[lo]; return d > 0 ? p.s[lo] + (p.s[hi] - p.s[lo]) * (t - p.t[lo]) / d : p.s[hi];
  }

  // ---------------- renderer, scene, cameras ----------------
  var SMALL = Math.min(screen.width, screen.height) < 700;
  var R = new T3.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  R.setPixelRatio(Math.min(window.devicePixelRatio || 1, SMALL ? 1.5 : 2));
  R.outputEncoding = T3.sRGBEncoding;
  host.insertBefore(R.domElement, host.firstChild);
  R.domElement.setAttribute('aria-hidden', 'true');
  var scene = new T3.Scene();
  (function () { var c = document.createElement('canvas'); c.width = 4; c.height = 256; var g = c.getContext('2d');
    var gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#7f9db8'); gr.addColorStop(0.55, '#c8c9c0'); gr.addColorStop(1, '#e6d6bd');
    g.fillStyle = gr; g.fillRect(0, 0, 4, 256); var tx = new T3.CanvasTexture(c); tx.encoding = T3.sRGBEncoding; scene.background = tx; })();
  scene.fog = new T3.Fog(col('#ddd0bb'), 60, 205);
  var cam = new T3.PerspectiveCamera(60, 16 / 9, 0.15, 1200);
  scene.add(cam);
  scene.add(new T3.HemisphereLight(col('#dce8ff'), col('#7d6d55'), 0.85));
  var sun = new T3.DirectionalLight(col('#ffe0b5'), 0.95); sun.position.set(-0.6, 1, 0.35); scene.add(sun);

  // ---------------- the world ----------------
  var LEN = ZMAX - ZMIN, ZMID = (ZMAX + ZMIN) / 2;
  function flat(w, d, hex, x, y, z, mat) { var m = new T3.Mesh(new T3.PlaneGeometry(w, d), mat || new T3.MeshLambertMaterial({ color: col(hex) })); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); scene.add(m); return m; }
  function noiseTex(base, spread, rep) {
    var c = document.createElement('canvas'); c.width = c.height = 128; var g = c.getContext('2d'), d = g.createImageData(128, 128), r = rng(7);
    for (var i = 0; i < d.data.length; i += 4) { var v = base + (r() - 0.5) * spread; d.data[i] = v; d.data[i + 1] = v; d.data[i + 2] = v + 3; d.data[i + 3] = 255; }
    g.putImageData(d, 0, 0); var t = new T3.CanvasTexture(c); t.wrapS = t.wrapT = T3.RepeatWrapping; t.repeat.set(rep[0], rep[1]); t.encoding = T3.sRGBEncoding; t.anisotropy = 4; return t;
  }
  flat(900, LEN + 600, '#9a8c74', 0, -0.3, ZMID);                                            // ground
  var asphalt = new T3.MeshLambertMaterial({ map: noiseTex(66, 26, [3, LEN / 10]) });
  flat(EDGE - MED, LEN, null, -(EDGE + MED) / 2, 0, ZMID, asphalt);
  flat(EDGE - MED, LEN, null, (EDGE + MED) / 2, 0, ZMID, asphalt);
  [GAP_N, GAP_S].forEach(function (z) { flat(MED * 2 + 0.2, 14, null, 0, 0.01, z, asphalt); });
  // footpaths and kerbs
  [-1, 1].forEach(function (sd) {
    var fp = new T3.Mesh(new T3.BoxGeometry(WALK - EDGE, 0.18, LEN), new T3.MeshLambertMaterial({ color: col('#a49a8a') }));
    fp.position.set(sd * (EDGE + WALK) / 2, 0.09, ZMID); scene.add(fp);
  });
  // lines: edge lines (white outside, yellow by the median) and lane dashes
  (function () {
    var lineM = new T3.MeshBasicMaterial({ color: col('#e9e6dc') }), yel = new T3.MeshBasicMaterial({ color: col('#d9b43c') });
    [-1, 1].forEach(function (sd) { flat(0.15, LEN, null, sd * (EDGE - 0.35), 0.03, ZMID, lineM); });
    var dashG = new T3.PlaneGeometry(0.14, 3); dashG.rotateX(-Math.PI / 2);
    var per = Math.floor(LEN / 9), dash = new T3.InstancedMesh(dashG, lineM, per * 4), o = new T3.Object3D(), n = 0;
    [-4.75, -8.25, 4.75, 8.25].forEach(function (x) { for (var i = 0; i < per; i++) { o.position.set(x, 0.03, ZMIN + i * 9); o.updateMatrix(); dash.setMatrixAt(n++, o.matrix); } });
    scene.add(dash);
    // median segments with striped kerb, soil, shrubs; gaps at the two U-turns
    var segs = [[ZMIN, GAP_N - 7], [GAP_N + 7, GAP_S - 7], [GAP_S + 7, ZMAX]];
    var shrubG = new T3.IcosahedronGeometry(0.75, 0), shrubM = new T3.MeshLambertMaterial({ color: 0xffffff, flatShading: true });
    var shrubN = 0; segs.forEach(function (s) { shrubN += Math.floor((s[1] - s[0]) / 2.6); });
    var shrubs = new T3.InstancedMesh(shrubG, shrubM, shrubN), sc = 0, greens = ['#4f7a3a', '#5d8a42', '#3f6a33', '#6b8f45'];
    segs.forEach(function (s) {
      var len = s[1] - s[0], mid = (s[0] + s[1]) / 2;
      var c = document.createElement('canvas'); c.width = 64; c.height = 8; var g = c.getContext('2d');
      g.fillStyle = '#f0c419'; g.fillRect(0, 0, 32, 8); g.fillStyle = '#1b1b1b'; g.fillRect(32, 0, 32, 8);
      var tx = new T3.CanvasTexture(c); tx.wrapS = T3.RepeatWrapping; tx.repeat.set(len / 2, 1); tx.encoding = T3.sRGBEncoding;
      var kerb = new T3.Mesh(new T3.BoxGeometry(MED * 2, 0.3, len), [new T3.MeshLambertMaterial({ map: tx }), new T3.MeshLambertMaterial({ map: tx }), new T3.MeshLambertMaterial({ color: col('#6b5a43') }), new T3.MeshLambertMaterial({ color: col('#6b5a43') }), new T3.MeshLambertMaterial({ color: col('#1b1b1b') }), new T3.MeshLambertMaterial({ color: col('#1b1b1b') })]);
      kerb.position.set(0, 0.15, mid); scene.add(kerb);
      for (var z = s[0] + 1.3; z < s[1] - 1; z += 2.6) {
        if (sc >= shrubN) break;
        var k = rr(0.7, 1.25); o.position.set(rr(-0.35, 0.35), 0.45 + 0.3 * k, z); o.scale.set(k, k * rr(0.8, 1.2), k); o.rotation.set(0, rr(0, 6), 0); o.updateMatrix();
        shrubs.setMatrixAt(sc, o.matrix); shrubs.setColorAt(sc, col(pick(greens))); sc++;
      }
    });
    shrubs.count = sc; o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0); scene.add(shrubs);
    // median street lights
    var P = new Parts(); P.box(0, 4.5, 0, 0.16, 9, 0.16, '#7c8085').box(0, 8.9, 0, 4.4, 0.12, 0.12, '#7c8085').box(2.1, 8.75, 0, 0.6, 0.18, 0.3, '#d9d6cc').box(-2.1, 8.75, 0, 0.6, 0.18, 0.3, '#d9d6cc');
    var lg = P.build(), lights = [], z;
    segs.forEach(function (s) { for (z = s[0] + 10; z < s[1] - 6; z += 34) lights.push(z); });
    var lamps = new T3.InstancedMesh(lg, VC, lights.length); lights.forEach(function (z, i) { o.position.set(0, 0.3, z); o.updateMatrix(); lamps.setMatrixAt(i, o.matrix); }); scene.add(lamps);
  })();
  // buildings, window bands, shop awnings, trees (all instanced, all made up)
  (function () {
    var o = new T3.Object3D(), box = new T3.BoxGeometry(1, 1, 1); box.translate(0, 0.5, 0);
    var walls = ['#e8dcc4', '#efe6d2', '#d9c7a7', '#e3c9b6', '#cfd6d8', '#f1ede4', '#c9c1b2', '#e7d3a6', '#d6b8a4', '#bfc8c2'];
    var awn = ['#b8452f', '#2f6f8f', '#c98a2b', '#5a7d3c', '#7a4b8c', '#a33b4a', '#2e7f73', '#d0a23c'];
    var B = [], W = [], S = [], Tr = [];
    [-1, 1].forEach(function (sd) {
      var z = ZMIN; while (z < ZMAX) {
        var w = rr(7, 22), h = pick([7, 10, 10, 13, 13, 16, 19, 22, 25]) + rr(-0.5, 0.5), d = rr(10, 22), gap = R0() < 0.18 ? rr(4, 12) : rr(0.4, 1.6);
        var x0 = sd * (FRONT + rr(0, 2.5));
        B.push([x0 + sd * d / 2, z + w / 2, w, h, d, pick(walls)]);
        for (var f = 1; f < h / 3.1 - 0.4; f++) W.push([x0 - sd * 0.06, f * 3.1 + 0.9, z + w / 2, w * 0.86, 1.15]);
        if (R0() < 0.75) S.push([x0 - sd * 1.0, 2.6, z + w / 2, w * 0.9, pick(awn)]);
        z += w + gap;
      }
      for (z = ZMIN + rr(0, 8); z < ZMAX; z += rr(11, 19)) Tr.push([sd * (WALK - 0.9), z, rr(0.8, 1.35)]);
    });
    var bm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: 0xffffff }), B.length);
    B.forEach(function (b, i) { o.position.set(b[0], 0, b[1]); o.scale.set(b[4], b[3], b[2]); o.updateMatrix(); bm.setMatrixAt(i, o.matrix); bm.setColorAt(i, col(b[5])); }); scene.add(bm);
    var wm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: col('#45515c') }), W.length);
    W.forEach(function (b, i) { o.position.set(b[0], b[1], b[2]); o.scale.set(0.12, b[4], b[3]); o.updateMatrix(); wm.setMatrixAt(i, o.matrix); }); scene.add(wm);
    var sm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: 0xffffff }), S.length);
    S.forEach(function (b, i) { o.position.set(b[0], b[1], b[2]); o.scale.set(2.0, 0.35, b[3]); o.updateMatrix(); sm.setMatrixAt(i, o.matrix); sm.setColorAt(i, col(b[4])); }); scene.add(sm);
    var P = new Parts(); P.box(0, 1.2, 0, 0.32, 2.4, 0.32, '#6a5039').geo(new T3.IcosahedronGeometry(2.3, 0), 0, 4.0, 0, '#557d3d').geo(new T3.IcosahedronGeometry(1.6, 0), 0.9, 5.2, 0.5, '#4a7035');
    var tg = P.build(), tm = new T3.InstancedMesh(tg, new T3.MeshLambertMaterial({ vertexColors: true, flatShading: true }), Tr.length);
    Tr.forEach(function (t, i) { o.position.set(t[0], 0.18, t[1]); o.scale.set(t[2], t[2] * rr(0.9, 1.15), t[2]); o.rotation.y = rr(0, 6); o.updateMatrix(); tm.setMatrixAt(i, o.matrix); }); scene.add(tm);
  })();

  // ---------------- vehicles (made up, no brands, no plates, faceless riders) ----------------
  function vCar(c, suv) { var L = suv ? 4.6 : 4.1, W = suv ? 1.85 : 1.72, H = suv ? 0.3 : 0;
    return new Parts().box(0, 0.05, 0, W + 0.35, 0.02, L + 0.4, '#202124').box(0, 0.28, 0, W * 0.96, 0.42, L * 0.8, '#141517')
      .box(0, 0.66 + H / 2, 0, W, 0.56 + H, L, c).box(0, 1.2 + H, L * 0.04, W * 0.86, 0.55, L * 0.52, '#232a31').box(0, 1.49 + H, L * 0.04, W * 0.82, 0.06, L * 0.48, c)
      .box(W * 0.34, 0.78 + H, L / 2 + 0.01, W * 0.22, 0.12, 0.04, '#d5332b').box(-W * 0.34, 0.78 + H, L / 2 + 0.01, W * 0.22, 0.12, 0.04, '#d5332b').build(); }
  function vAuto(lo, hi) { var L = 2.7, W = 1.35;
    return new Parts().box(0, 0.05, 0, W + 0.3, 0.02, L + 0.3, '#202124').box(0, 0.22, 0, W * 0.9, 0.3, L * 0.85, '#141517')
      .box(0, 0.6, 0.15, W, 0.5, L * 0.85, lo).box(0, 0.65, -L / 2 + 0.25, W * 0.55, 0.6, 0.5, lo).box(0, 1.25, 0.2, W * 0.94, 0.7, L * 0.62, '#2a2a2a')
      .box(0, 1.68, 0.1, W * 1.02, 0.16, L * 0.8, hi).box(0, 0.75, L / 2 - 0.12 + 0.15, W * 0.7, 0.1, 0.04, '#d5332b').build(); }
  function vTw(c, shirt) { var L = 1.9;
    return new Parts().box(0, 0.05, 0, 0.75, 0.02, L + 0.2, '#202124').box(0, 0.32, 0, 0.18, 0.6, L * 0.92, '#18191b').box(0, 0.68, 0.05, 0.42, 0.3, 1.15, c)
      .box(0, 1.12, 0.2, 0.44, 0.62, 0.34, shirt).box(0, 1.56, 0.16, 0.3, 0.3, 0.32, pick(['#1d1d1f', '#e8e4da', '#b3332c', '#24476b']))
      .box(0, 0.62, L / 2 - 0.15, 0.14, 0.08, 0.04, '#d5332b').build(); }
  function vBus(c, band) { var L = 11, W = 2.5;
    return new Parts().box(0, 0.05, 0, W + 0.4, 0.02, L + 0.4, '#202124').box(0, 0.3, 0, W * 0.94, 0.5, L * 0.9, '#141517').box(0, 1.75, 0, W, 2.7, L, c)
      .box(0, 2.15, 0.3, W + 0.02, 0.85, L * 0.86, '#26303a').box(0, 2.0, -L / 2 - 0.01, W * 0.9, 1.3, 0.04, '#26303a').box(0, 0.95, 0, W + 0.01, 0.35, L, band)
      .box(W * 0.38, 0.9, L / 2 + 0.01, 0.3, 0.2, 0.04, '#d5332b').box(-W * 0.38, 0.9, L / 2 + 0.01, 0.3, 0.2, 0.04, '#d5332b').build(); }
  function vTruck(cab, load) { var L = 8, W = 2.4;
    return new Parts().box(0, 0.05, 0, W + 0.4, 0.02, L + 0.4, '#202124').box(0, 0.45, 0, W * 0.9, 0.6, L * 0.95, '#18191b')
      .box(0, 1.6, -L / 2 + 1.1, W, 2.2, 2.2, cab).box(0, 2.2, -L / 2 - 0.01, W * 0.86, 0.75, 0.04, '#26303a')
      .box(0, 1.95, 1.15, W, 2.1, L - 2.5, load).box(W * 0.38, 0.85, L / 2 + 0.01, 0.3, 0.18, 0.04, '#d5332b').box(-W * 0.38, 0.85, L / 2 + 0.01, 0.3, 0.18, 0.04, '#d5332b').build(); }
  var carCols = ['#e9e9e6', '#e9e9e6', '#c4c7cb', '#9ea3a8', '#4a4e54', '#1f2124', '#7b1e22', '#2b4a6b', '#c25a2a', '#e9e9e6'];
  var TYPES = [
    { k: 'tw', w: 40, len: 1.9, f: [1.05, 1.3], make: function () { return vTw(pick(['#1d1d1f', '#8c1d22', '#2c4f7c', '#d6d2c8', '#3d3f42']), pick(['#3b6aa0', '#e2ddd0', '#8a2f3a', '#3f6b4e', '#d39a3a', '#5b4e7a'])); } },
    { k: 'car', w: 25, len: 4.1, f: [0.95, 1.12], make: function () { return vCar(pick(carCols)); } },
    { k: 'suv', w: 8, len: 4.6, f: [0.95, 1.1], make: function () { return vCar(pick(carCols), true); } },
    { k: 'auto', w: 15, len: 2.7, f: [0.86, 1.0], make: function () { return R0() < 0.5 ? vAuto('#e7bd26', '#1c1c1c') : vAuto('#3d8a41', '#e5c330'); } },
    { k: 'bus', w: 6, len: 11, f: [0.82, 0.93], make: function () { return pick([function () { return vBus('#e7e3d8', '#2e7f73'); }, function () { return vBus('#b9452f', '#e7e3d8'); }, function () { return vBus('#3e5f86', '#e7e3d8'); }])(); } },
    { k: 'truck', w: 6, len: 8, f: [0.8, 0.92], make: function () { return vTruck(pick(['#d4692b', '#2d5d9a', '#b8352c', '#e0b23a']), pick(['#4d6e3a', '#2f5c86', '#7a5a3a', '#8a8f55'])); } }
  ];
  var VARIANTS = []; TYPES.forEach(function (t) { var n = t.k === 'tw' ? 5 : (t.k === 'car' ? 6 : 3); for (var i = 0; i < n; i++) VARIANTS.push({ t: t, g: t.make(), list: [] }); });
  function pickType() { var tot = 0, i; TYPES.forEach(function (t) { tot += t.w; }); var r = R0() * tot; for (i = 0; i < TYPES.length; i++) { r -= TYPES[i].w; if (r <= 0) return TYPES[i]; } return TYPES[0]; }

  var WIN = 200, VEH = [], meshes = [];
  function laneX(c, l) { return (c ? 1 : -1) * LANES[l]; }
  function dirOf(c) { return c ? 1 : -1; }   // west carriageway runs north (-z), east runs south (+z)
  function makeTraffic(heavy) {
    VEH = []; VARIANTS.forEach(function (v) { v.list = []; v.mesh = null; });
    meshes.forEach(function (m) { scene.remove(m); m.dispose && m.dispose(); }); meshes = [];
    var start = heavy ? B : A, cs = start[0] < 0 ? 0 : 1;
    for (var c = 0; c < 2; c++) for (var l = 0; l < 3; l++) {
      var z = start[1] - WIN, dense = heavy ? (c === cs ? [1.8, 6] : [3, 11]) : [7, 24];
      while (z < start[1] + WIN) {
        var t = pickType(), gap = rr(dense[0], dense[1]) * (l === 0 ? 1.15 : 1);
        if (l === 2 && (t.k === 'bus' || t.k === 'truck') && R0() < 0.4) t = TYPES[0];
        var vs = VARIANTS.filter(function (v) { return v.t === t; }), v = pick(vs);
        var zc = z + t.len / 2;
        var clear = c === cs && l < 2 && Math.abs(zc - start[1]) < 14;
        if (!clear) { var veh = { c: c, l: l, x: laneX(c, l) + (t.k === 'tw' ? rr(-1.0, 1.0) : rr(-0.25, 0.25)), z: zc, len: t.len, f: rr(t.f[0], t.f[1]) * [1, 0.97, 0.92][l], ph: rr(0, 6), v: v };
          v.list.push(veh); VEH.push(veh); }
        z += t.len + gap;
      }
    }
    VARIANTS.forEach(function (v) { if (!v.list.length) return; var m = new T3.InstancedMesh(v.g, VC, v.list.length); m.instanceMatrix.setUsage(T3.DynamicDrawUsage); m.frustumCulled = false; v.mesh = m; scene.add(m); meshes.push(m); });
  }
  var player = new T3.Mesh(vCar('#d9dde2'), VC); scene.add(player);

  // driver's cockpit (follows the camera; hidden from above)
  var cockpit = new T3.Group();
  (function () {
    var dark = new T3.MeshLambertMaterial({ color: col('#101215') }), bon = new T3.MeshLambertMaterial({ color: col('#6c7279') });
    var dash = new T3.Mesh(new T3.BoxGeometry(2.6, 0.3, 0.7), dark); dash.position.set(0, -0.72, -0.9); cockpit.add(dash);
    var hood = new T3.Mesh(new T3.BoxGeometry(1.6, 0.05, 1.0), bon); hood.position.set(0, -1.06, -2.2); hood.rotation.x = 0.05; cockpit.add(hood);
    [-1, 1].forEach(function (s) { var p = new T3.Mesh(new T3.BoxGeometry(0.045, 1.5, 0.045), dark); p.position.set(s * 1.02, -0.05, -1.0); p.rotation.z = -s * 0.36; p.rotation.x = -0.4; cockpit.add(p); });
  })();
  cam.add(cockpit);

  // A and B pins with labels
  var pins = [];
  function label(text, accent) {
    var c = document.createElement('canvas'), g = c.getContext('2d'); c.width = 768; c.height = 128;
    g.font = '600 52px Inter, system-ui, sans-serif'; var w = Math.min(760, g.measureText(text).width + 64);
    g.fillStyle = 'rgba(8,10,14,0.86)'; var x = (768 - w) / 2; g.beginPath(); if (g.roundRect) g.roundRect(x, 20, w, 88, 44); else g.rect(x, 20, w, 88); g.fill();
    g.strokeStyle = accent; g.lineWidth = 3; g.stroke(); g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 384, 66);
    var t = new T3.CanvasTexture(c); t.encoding = T3.sRGBEncoding;
    var s = new T3.Sprite(new T3.SpriteMaterial({ map: t, depthTest: false, transparent: true })); s.scale.set(12, 2, 1); s.renderOrder = 10; return s;
  }
  function makePins(dir) {
    pins.forEach(function (p) { scene.remove(p); }); pins = [];
    var st = dir === 'ab' ? A : B, en = dir === 'ab' ? B : A;
    [[st, 'You are here', '#9AA0A6', 0x9aa0a6], [en, 'Where you need to be · 13 m', '#E8A87C', 0xe8a87c]].forEach(function (q) {
      var g = new T3.Group(), m = new T3.MeshBasicMaterial({ color: col('#' + q[3].toString(16)), transparent: true, opacity: 0.9 });
      var pole = new T3.Mesh(new T3.CylinderGeometry(0.09, 0.09, 11, 8), m); pole.position.y = 5.5; g.add(pole);
      var ring = new T3.Mesh(new T3.RingGeometry(1.0, 1.35, 40), m); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.06; g.add(ring);
      var top = new T3.Mesh(new T3.SphereGeometry(0.35, 16, 12), m); top.position.y = 11; g.add(top);
      var lb = label(q[1], q[2]); lb.position.y = 12.8; g.add(lb);
      g.position.set(q[0][0], 0, q[0][1]); scene.add(g); pins.push(g);
    });
  }

  // ---------------- strip map (the whole hairpin at a glance) ----------------
  var strip = $('strip'), sg = strip.getContext('2d');
  function drawStrip(dir, s) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = strip.clientWidth, h = strip.clientHeight;
    if (strip.width !== Math.round(w * dpr)) { strip.width = Math.round(w * dpr); strip.height = Math.round(h * dpr); }
    sg.setTransform(dpr, 0, 0, dpr, 0, 0); sg.clearRect(0, 0, w, h);
    var top = GAP_N - 40, bot = GAP_S + 40, pad = 12;
    function Y(z) { return pad + (z - top) / (bot - top) * (h - 2 * pad); }
    function X(x) { return w / 2 + x * (w * 0.032); }
    sg.lineCap = 'round';
    sg.strokeStyle = 'rgba(255,255,255,0.16)'; sg.lineWidth = 6;
    [-1, 1].forEach(function (sd) { sg.beginPath(); sg.moveTo(X(sd * 6.5), Y(top)); sg.lineTo(X(sd * 6.5), Y(bot)); sg.stroke(); });
    var r = RT[dir], i, n = r.x.length, stp = Math.max(1, Math.floor(n / 220));
    sg.strokeStyle = 'rgba(232,168,124,0.35)'; sg.lineWidth = 2; sg.beginPath();
    for (i = 0; i < n; i += stp) { if (i === 0) sg.moveTo(X(r.x[i]), Y(r.z[i])); else sg.lineTo(X(r.x[i]), Y(r.z[i])); } sg.stroke();
    sg.strokeStyle = '#E8A87C'; sg.lineWidth = 2.5; sg.beginPath();
    for (i = 0; i < n && r.s[i] <= s; i += stp) { if (i === 0) sg.moveTo(X(r.x[i]), Y(r.z[i])); else sg.lineTo(X(r.x[i]), Y(r.z[i])); }
    var p = at(r, s); sg.lineTo(X(p.x), Y(p.z)); sg.stroke();
    var st = dir === 'ab' ? A : B, en = dir === 'ab' ? B : A;
    sg.fillStyle = '#9AA0A6'; sg.beginPath(); sg.arc(X(st[0]), Y(st[1]), 3, 0, 7); sg.fill();
    sg.fillStyle = '#E8A87C'; sg.beginPath(); sg.arc(X(en[0]), Y(en[1]), 3.5, 0, 7); sg.fill();
    sg.fillStyle = '#fff'; sg.strokeStyle = '#E8A87C'; sg.lineWidth = 2; sg.beginPath(); sg.arc(X(p.x), Y(p.z), 4.5, 0, 7); sg.fill(); sg.stroke();
  }

  // ---------------- state ----------------
  var S = { dir: 'ab', rate: 8, mode: 'intro', t: 0, above: RM, orbit: 0.6 };
  var camPos = new T3.Vector3(30, 26, 30), camLook = new T3.Vector3(0, 0, 0), tmpP = new T3.Vector3(), tmpL = new T3.Vector3();
  var stage = host, playB = $('play'), skipB = $('skip'), viewB = $('view'), introC = $('intro'), result = $('result');
  function setPressed(groupId, v) { Array.prototype.forEach.call($(groupId).querySelectorAll('button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === String(v))); }); }
  function two(lg, sm) { return '<span class="lg">' + lg + '</span><span class="sm">' + sm + '</span>'; }
  function updateViewBtn() { viewB.innerHTML = S.above ? two("Driver's view", 'Driver') : two('View from above', 'Above'); viewB.setAttribute('aria-pressed', String(S.above)); }
  function reset(dir) {
    S.dir = dir; S.t = 0; S.mode = 'intro'; stage.classList.remove('done'); result.hidden = true; introC.hidden = false;
    var d = DRIVES[dir];
    $('intro-body').textContent = 'You are on the ' + d.from + '. To reach the ' + d.to + ', drive away from it to the gap in the median, turn, and come back.';
    playB.textContent = 'Drive'; skipB.disabled = true; makeTraffic(dir === 'ba'); makePins(dir); setPressed('c-dir', dir); hud(0, 0);
  }
  function hud(s, kmh) { $('h-dist').textContent = fmtM(s); $('h-clock').textContent = fmtClock(S.t); $('h-spd').textContent = Math.round(kmh); $('h-rate').textContent = 'Replayed ' + S.rate + '× faster'; }
  function finish() {
    S.mode = 'done'; S.t = PACE[S.dir].T; stage.classList.add('done'); playB.textContent = 'Drive again'; skipB.disabled = true;
    var d = DRIVES[S.dir], o = DRIVES[S.dir === 'ab' ? 'ba' : 'ab'];
    $('r-head').textContent = '13 m across. ' + (d.m / 1000).toFixed(2) + ' km and ' + fmtDur(d.s) + ' to get there.';
    $('r-body').textContent = 'That is the drive we made on 1 Nov 2026 from the ' + d.from + ' to the ' + d.to + '. The other way, ' + o.from + ' to ' + o.to + ', took ' + fmtDur(o.s) + ' for ' + (o.m / 1000).toFixed(2) + ' km. One drive each way, at one time of day: another hour will differ.';
    var km = (DRIVES.ab.m + DRIVES.ba.m - 2 * STRAIGHT) / 1000 * COST.days, secs = (DRIVES.ab.s + DRIVES.ba.s) * COST.days;
    $('r-month').textContent = 'Crossing once each way every working day: about ' + Math.round(km) + ' km and ' + fmtDur(secs) + ' of driving a month, and about ₹' + Math.round(km / COST.tw * COST.petrol) + ' of petrol on a two-wheeler or ₹' + Math.round(km / COST.car * COST.petrol) + ' in a car.';
    $('r-ev').textContent = d.ev; $('r-cost').href = d.cost;
    $('r-other').textContent = 'Drive the other way'; result.hidden = false;
  }
  function play() {
    if (S.mode === 'done') { reset(S.dir); }
    if (S.mode === 'intro' || S.mode === 'paused') { S.mode = 'driving'; introC.hidden = true; playB.textContent = 'Pause'; skipB.disabled = false; }
    else if (S.mode === 'driving') { S.mode = 'paused'; playB.textContent = 'Resume'; }
    kick();
  }
  playB.addEventListener('click', play);
  skipB.addEventListener('click', function () { finish(); kick(); });
  viewB.addEventListener('click', function () { S.above = !S.above; updateViewBtn(); kick(); });
  $('r-other').addEventListener('click', function () { reset(S.dir === 'ab' ? 'ba' : 'ab'); play(); });
  Array.prototype.forEach.call($('c-dir').querySelectorAll('button'), function (b) { b.addEventListener('click', function () { reset(b.getAttribute('data-v')); kick(); }); });
  Array.prototype.forEach.call($('c-rate').querySelectorAll('button'), function (b) { b.addEventListener('click', function () { S.rate = +b.getAttribute('data-v'); setPressed('c-rate', S.rate); hud(sAt(PACE[S.dir], S.t), 0); }); });
  stage.addEventListener('keydown', function (e) { if (e.code === 'Space') { e.preventDefault(); play(); } });

  // ---------------- traffic step ----------------
  var o3 = new T3.Object3D();
  function stepTraffic(dtReal, simT, p, pv, heavy) {
    var hw = 2.2 + Math.min(9, pv * 0.8);
    var pc = p.x < 0 ? 0 : 1, floor = heavy ? 1.6 : 6, nominal = heavy ? 3.2 + 2.6 * Math.max(0, Math.sin(simT * 0.045)) : 9.5;
    var i, v;
    for (i = 0; i < VEH.length; i++) {
      v = VEH[i];
      var base = v.c === pc ? (v.l === 0 ? pv : Math.max(pv, floor)) : nominal;
      v.z += dirOf(v.c) * base * v.f * (1 + 0.06 * Math.sin(simT * 0.2 + v.ph)) * dtReal;
      if (v.z - p.z > WIN) v.z -= 2 * WIN; else if (v.z - p.z < -WIN) v.z += 2 * WIN;
    }
    // keep every lane free of overlaps; the player is a fixed obstacle in the lane it occupies
    for (var c = 0; c < 2; c++) for (var l = 0; l < 3; l++) {
      var lane = VEH.filter(function (q) { return q.c === c && q.l === l; }), dz = dirOf(c);
      lane.sort(function (a, b) { return (b.z - a.z) * dz; });              // front first
      var inLane = (p.x < 0 ? 0 : 1) === c && Math.abs(Math.abs(p.x) - LANES[l]) < 1.7;
      if (inLane) {
        var ahead = lane.filter(function (q) { return (q.z - p.z) * dz >= 0; }).reverse(), behind = lane.filter(function (q) { return (q.z - p.z) * dz < 0; });
        var edge = 2.05;                                                       // half the player's length
        ahead.forEach(function (q, j) { var need = edge + (j ? 2.2 : hw) + q.len / 2; if ((q.z - p.z) * dz < need) q.z = p.z + dz * need; edge = (q.z - p.z) * dz + q.len / 2; });
        edge = 2.05;
        behind.forEach(function (q) { var need = edge + 2.2 + q.len / 2; if ((p.z - q.z) * dz < need) q.z = p.z - dz * need; edge = (p.z - q.z) * dz + q.len / 2; });
      } else {
        for (i = 1; i < lane.length; i++) { var a = lane[i - 1], b = lane[i], gap = (a.z - b.z) * dz - (a.len + b.len) / 2; if (gap < 1.8 && gap > -40) b.z = a.z - dz * ((a.len + b.len) / 2 + 1.8); }
      }
    }
    VARIANTS.forEach(function (va) { if (!va.mesh) return; for (var k = 0; k < va.list.length; k++) { var q = va.list[k]; o3.position.set(q.x, 0, q.z); o3.rotation.set(0, q.c ? Math.PI : 0, 0); o3.updateMatrix(); va.mesh.setMatrixAt(k, o3.matrix); } va.mesh.instanceMatrix.needsUpdate = true; });
  }

  // ---------------- loop ----------------
  var last = 0, running = false, visible = true, lastS = 0;
  function size() { var w = host.clientWidth, h = host.clientHeight; if (!w || !h) return; R.setSize(w, h, false); cam.aspect = w / h; cam.fov = w / h < 1 ? 72 : 60; cam.updateProjectionMatrix(); }
  function frame(now) {
    running = false; if (!visible) return;
    var dt = Math.min(0.05, last ? (now - last) / 1000 : 0.016); last = now;
    tick(dt, now); kick();
  }
  function tick(dt, now) {
    var P = PACE[S.dir], r = RT[S.dir];
    if (S.mode === 'driving') { S.t += dt * S.rate; if (S.t >= P.T) finish(); }
    var s = sAt(P, S.t), p = at(r, s);
    var kmh = S.mode === 'driving' ? Math.max(0, (sAt(P, S.t + 0.75) - sAt(P, S.t - 0.75)) / 1.5 * 3.6) : 0;
    var pv = kmh / 3.6;
    stepTraffic(S.mode === 'driving' ? dt * S.rate : (S.mode === 'paused' ? 0 : dt), S.t, p, S.mode === 'intro' ? 0 : pv, S.dir === 'ba');
    player.position.set(p.x, 0, p.z); player.rotation.y = Math.atan2(-p.hx, -p.hz);
    var ahead = at(r, s + 22);
    if (S.mode === 'intro') {
      S.orbit += RM ? 0 : dt * 0.1;
      var st = S.dir === 'ab' ? A : B;
      tmpP.set(Math.sin(S.orbit) * 34, 24, Math.cos(S.orbit) * 34); tmpL.set(-Math.cos(S.orbit) * 9, 1, Math.sin(S.orbit) * 9);
      player.visible = true; cockpit.visible = false;
    } else if (S.above || S.mode === 'done') {
      tmpP.set(p.x - p.hx * 30 + 6, 30, p.z - p.hz * 30); tmpL.set(p.x + p.hx * 18, 0, p.z + p.hz * 18);
      player.visible = true; cockpit.visible = false;
    } else {
      tmpP.set(p.x + p.hx * 0.2, 1.25, p.z + p.hz * 0.2); tmpL.set(ahead.x, 1.05, ahead.z);
      player.visible = false; cockpit.visible = true;
    }
    var k = 1 - Math.exp(-dt * (S.mode === 'intro' ? 2 : 4.5));
    camPos.lerp(tmpP, k); camLook.lerp(tmpL, k);
    if (!S.above && S.mode !== 'intro' && S.mode !== 'done' && camPos.distanceTo(tmpP) < 3) camPos.copy(tmpP);
    cam.position.copy(camPos); cam.lookAt(camLook);
    pins.forEach(function (g) { g.children[1].scale.setScalar(1 + 0.08 * Math.sin(now / 400)); });
    if (S.mode !== 'intro' || Math.abs(s - lastS) > 0.01 || !lastS) hud(s, kmh); lastS = s;
    drawStrip(S.dir, s);
    R.render(scene, cam);
  }
  function kick() { if (!running && visible) { running = true; requestAnimationFrame(frame); } }
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting && !document.hidden; if (visible) { last = 0; kick(); } }).observe(host);
  document.addEventListener('visibilitychange', function () { visible = !document.hidden; if (visible) { last = 0; kick(); } });
  if ('ResizeObserver' in window) new ResizeObserver(size).observe(host); else window.addEventListener('resize', size);
  size(); updateViewBtn(); reset('ab'); kick();
  window.__arcroadDrive = { S: S, RT: RT, PACE: PACE, DRIVES: DRIVES, play: play,   // hooks for tests and the home-page preview render
    capture: function () { visible = false; host.classList.add('capture'); },
    frame: function (dt, now) { tick(dt, now); return R.domElement.toDataURL('image/jpeg', 0.92); } };
})();
