/* arcroad · 13 metres across: ride the detour we drove at S18.
 *
 * Every number shown comes from a field drive by arcroad:
 *   S18 a→b (west side to east side): 1,579.5 m in 193 s; b→a: 1,546.0 m in 692 s; straight 13.1 m (data/field/2026-11-01-results.json)
 *   S12 a→b (north side to south side): 1,951.2 m in 245 s, after dark; straight 17.4 m (data/field/2026-11-02-results.json)
 * Only places with a matched drive can be chosen; every other place is listed as not driven yet.
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
  var PLACES = {
    S18: { road: 'HITEC City–Kukatpally Main Road', area: 'APHB Colony', straight: 13.1, day: '1 Nov 2026', night: false,
      owner: 'The road owner is Cyberabad Municipal Corporation; signals are with the traffic police.',
      drives: {
        ab: { m: 1579.5, s: 193, model: 1571.7, from: 'west side', to: 'east side', ev: 'Driven by arcroad · 1 Nov 2026 · matched the model (1.57 km) · single pass, candidate until repeated',
              cost: '../cost/?place=S18%20west%20to%20east&veh=tw&km=1.57&min=3' },
        ba: { m: 1546.0, s: 692, model: 1378.3, from: 'east side', to: 'west side', ev: 'Driven by arcroad · 1 Nov 2026 · matched the model (1.38 km) · backed by photos',
              cost: '../cost/?place=S18%20east%20to%20west&veh=tw&km=1.53&min=12' } } },
    S12: { road: 'Hafeezpet Flyover', area: 'Hafeezpet', straight: 17.4, day: '2 Nov 2026', night: true, flyover: true,
      owner: 'The road owner is Cyberabad Municipal Corporation (Serilingampally zone); signals are with the traffic police.',
      drives: {
        ab: { m: 1951.2, s: 245, model: 2028.9, from: 'north side', to: 'south side', ev: 'Driven by arcroad · 2 Nov 2026, after dark · matched the model (2.03 km) · single pass, candidate until repeated · counted under a pairing rule changed on 2 Nov',
              cost: '../cost/?place=S12%20north%20to%20south&veh=tw&km=1.93&min=4' } } }
  };
  var PID = (location.search.match(/[?&]place=(S\d+)/) || [])[1]; if (!PLACES[PID]) PID = 'S18';
  var PL = PLACES[PID], STRAIGHT = PL.straight, DRIVES = PL.drives, SM = Math.round(STRAIGHT) + ' m';
  function heavyDir(dir) { var d = DRIVES[dir]; return !!d && d.m / d.s < 4; }   // slower than 4 m/s on average: a crowded pass
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
  // after dark: one soft round light used for lamps, headlights and their pools on the road
  var LIGHT = { night: !!PL.night, glare: false };
  var GLOW = (function () { var c = document.createElement('canvas'); c.width = c.height = 128; var g = c.getContext('2d');
    var gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.2, 'rgba(255,255,255,.55)');
    gr.addColorStop(0.5, 'rgba(255,255,255,.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return new T3.CanvasTexture(c); })();
  function glowPts(hex, size) { return new T3.PointsMaterial({ map: GLOW, color: col(hex), size: size, transparent: true, blending: T3.AdditiveBlending, depthWrite: false, sizeAttenuation: true }); }
  var lampHeadM = glowPts('#FFB868', 5.5), poolM = new T3.MeshBasicMaterial({ map: GLOW, color: col('#FF9E45'), transparent: true, opacity: 0.34, blending: T3.AdditiveBlending, depthWrite: false });
  var poolG = new T3.PlaneGeometry(24, 24); poolG.rotateX(-Math.PI / 2);

  // ---------------- road layout (metres; x east, -z north) ----------------
  var MED = 1.25;                       // half median width
  var LANES = [3.0, 6.5, 10.0];         // lane centres from the road axis
  var EDGE = 11.75, WALK = 15.25, FRONT = 17;
  var A = [-STRAIGHT / 2, 0], B = [STRAIGHT / 2, 0];      // as measured

  // Route a→b: merge to the inner lane, run to the gap, U-turn round the median end, come back.
  function route(L) {
    var px = [], pz = [], step = 0.25, z, t, f, sh = Math.min(60, Math.max(3, L * 0.45));
    for (z = 0; z > -sh; z -= step) { px.push(A[0] + (-LANES[0] - A[0]) * smooth(-z / sh)); pz.push(z); }
    for (z = -sh; z > -L; z -= step) { px.push(-LANES[0]); pz.push(z); }
    for (f = Math.PI; f > 0; f -= step / LANES[0]) { px.push(LANES[0] * Math.cos(f)); pz.push(-L - LANES[0] * Math.sin(f)); }
    for (z = -L; z < -sh; z += step) { px.push(LANES[0]); pz.push(z); }
    for (z = -sh; z <= 0.001; z += step) { t = (z + sh) / sh; px.push(LANES[0] + (B[0] - LANES[0]) * smooth(t)); pz.push(z); }
    var ps = [0], i; for (i = 1; i < px.length; i++) ps.push(ps[i - 1] + Math.hypot(px[i] - px[i - 1], pz[i] - pz[i - 1]));
    return { x: px, z: pz, s: ps, len: ps[ps.length - 1], L: L };
  }
  function fit(target) { var lo = 70, hi = 2000, r, k; for (k = 0; k < 40; k++) { var mid = (lo + hi) / 2; r = route(mid); if (r.len > target) hi = mid; else lo = mid; } return route((lo + hi) / 2); }
  var RT = { ab: fit(DRIVES.ab.m), ba: null };
  if (DRIVES.ba) (function () { var r = fit(DRIVES.ba.m); // b→a is the mirror (start at B heading south, gap to the south)
    r.x = r.x.map(function (v) { return -v; }); r.z = r.z.map(function (v) { return -v; }); RT.ba = r; })();
  var GAP_N = -RT.ab.L - LANES[0], GAP_S = (RT.ba || RT.ab).L + LANES[0];     // centres of the two median gaps
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
    var r = RT[dir], S = Math.ceil(r.len), T = DRIVES[dir].s, heavy = heavyDir(dir);
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
  var PACE = { ab: pace('ab'), ba: DRIVES.ba ? pace('ba') : null };
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
  var hemi = new T3.HemisphereLight(col('#dce8ff'), col('#7d6d55'), 0.85); scene.add(hemi);
  var sun = new T3.DirectionalLight(col('#ffe0b5'), 0.95); sun.position.set(-0.6, 1, 0.35); scene.add(sun);

  // ---------------- the world ----------------
  var LEN = ZMAX - ZMIN, ZMID = (ZMAX + ZMIN) / 2;
  function flat(w, d, hex, x, y, z, mat) { var m = new T3.Mesh(new T3.PlaneGeometry(w, d), mat || new T3.MeshLambertMaterial({ color: col(hex) })); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); scene.add(m); return m; }
  function noiseTex(base, spread, rep) {
    var c = document.createElement('canvas'); c.width = c.height = 128; var g = c.getContext('2d'), d = g.createImageData(128, 128), r = rng(7);
    for (var i = 0; i < d.data.length; i += 4) { var v = base + (r() - 0.5) * spread; d.data[i] = v; d.data[i + 1] = v; d.data[i + 2] = v + 3; d.data[i + 3] = 255; }
    g.putImageData(d, 0, 0); var t = new T3.CanvasTexture(c); t.wrapS = t.wrapT = T3.RepeatWrapping; t.repeat.set(rep[0], rep[1]); t.encoding = T3.sRGBEncoding; t.anisotropy = 4; return t;
  }
  var lineMat = null;
  var groundMesh = flat(7000, LEN + 7000, '#9a8c74', 0, -0.3, ZMID);                                            // ground
  var asphalt = new T3.MeshLambertMaterial({ map: noiseTex(66, 26, [3, LEN / 10]) });
  flat(EDGE - MED, LEN, null, -(EDGE + MED) / 2, 0, ZMID, asphalt);
  flat(EDGE - MED, LEN, null, (EDGE + MED) / 2, 0, ZMID, asphalt);
  // footpaths and kerbs
  var walkM = new T3.MeshLambertMaterial({ color: col('#a49a8a') });
  [-1, 1].forEach(function (sd) {
    var fp = new T3.Mesh(new T3.BoxGeometry(WALK - EDGE, 0.18, LEN), walkM);
    fp.position.set(sd * (EDGE + WALK) / 2, 0.09, ZMID); scene.add(fp);
  });
  // lines: edge lines (white outside, yellow by the median) and lane dashes
  (function () {
    var lineM = lineMat = new T3.MeshBasicMaterial({ color: col('#e9e6dc') }), yel = new T3.MeshBasicMaterial({ color: col('#d9b43c') });
    [-1, 1].forEach(function (sd) { flat(0.15, LEN, null, sd * (EDGE - 0.35), 0.03, ZMID, lineM); });
    var dashG = new T3.PlaneGeometry(0.14, 3); dashG.rotateX(-Math.PI / 2);
    var per = Math.floor(LEN / 9), dash = new T3.InstancedMesh(dashG, lineM, per * 4), o = new T3.Object3D(), n = 0;
    [-4.75, -8.25, 4.75, 8.25].forEach(function (x) { for (var i = 0; i < per; i++) { o.position.set(x, 0.03, ZMIN + i * 9); o.updateMatrix(); dash.setMatrixAt(n++, o.matrix); } });
    scene.add(dash);
  })();
  // median segments with striped kerb, soil, shrubs, lights; rebuilt when an option opens a new gap
  var medianG = null, kerbTex = (function () { var c = document.createElement('canvas'); c.width = 64; c.height = 8; var g = c.getContext('2d');
    g.fillStyle = '#f0c419'; g.fillRect(0, 0, 32, 8); g.fillStyle = '#1b1b1b'; g.fillRect(32, 0, 32, 8); return c; })();
  var lampGeo = new Parts().box(0, 4.5, 0, 0.16, 9, 0.16, '#7c8085').box(0, 8.9, 0, 4.4, 0.12, 0.12, '#7c8085').box(2.1, 8.75, 0, 0.6, 0.18, 0.3, '#d9d6cc').box(-2.1, 8.75, 0, 0.6, 0.18, 0.3, '#d9d6cc').build();
  var shrubG = new T3.IcosahedronGeometry(0.75, 0), shrubM = new T3.MeshLambertMaterial({ color: 0xffffff, flatShading: true });
  var soilM = new T3.MeshLambertMaterial({ color: col('#6b5a43') }), capM = new T3.MeshLambertMaterial({ color: col('#1b1b1b') });
  function buildMedian(gaps) {
    if (medianG) { scene.remove(medianG); medianG.traverse(function (m) { if (m.geometry && m.geometry !== shrubG && m.geometry !== lampGeo) m.geometry.dispose(); }); }
    medianG = new T3.Group(); scene.add(medianG);
    var R1 = rng(4242), o = new T3.Object3D(), cuts = gaps.slice().sort(function (a, b) { return a - b; }), segs = [], z0 = ZMIN;
    cuts.forEach(function (z) { if (z - 7 > z0) segs.push([z0, z - 7]); z0 = z + 7; }); segs.push([z0, ZMAX]);
    cuts.forEach(function (z) { var m = new T3.Mesh(new T3.PlaneGeometry(MED * 2 + 0.2, 14), asphalt); m.rotation.x = -Math.PI / 2; m.position.set(0, 0.01, z); medianG.add(m); });
    var shrubN = 0; segs.forEach(function (s) { shrubN += Math.floor((s[1] - s[0]) / 2.6); });
    var shrubs = new T3.InstancedMesh(shrubG, shrubM, Math.max(1, shrubN)), sc = 0, greens = ['#4f7a3a', '#5d8a42', '#3f6a33', '#6b8f45'];
    segs.forEach(function (s) {
      var len = s[1] - s[0], mid = (s[0] + s[1]) / 2;
      var tx = new T3.CanvasTexture(kerbTex); tx.wrapS = T3.RepeatWrapping; tx.repeat.set(len / 2, 1); tx.encoding = T3.sRGBEncoding;
      var km = new T3.MeshLambertMaterial({ map: tx }); km.userData.dim = true; if (LIGHT.night) km.color.copy(col('#4A4A4A'));
      var kerb = new T3.Mesh(new T3.BoxGeometry(MED * 2, 0.3, len), [km, km, soilM, soilM, capM, capM]);
      kerb.position.set(0, 0.15, mid); medianG.add(kerb);
      for (var z = s[0] + 1.3; z < s[1] - 1; z += 2.6) {
        var k = 0.7 + 0.55 * R1(); o.position.set((R1() - 0.5) * 0.7, 0.45 + 0.3 * k, z); o.scale.set(k, k * (0.8 + 0.4 * R1()), k); o.rotation.set(0, R1() * 6, 0); o.updateMatrix();
        shrubs.setMatrixAt(sc, o.matrix); shrubs.setColorAt(sc, col(greens[Math.floor(R1() * 4)])); sc++;
      }
    });
    shrubs.count = sc; medianG.add(shrubs);
    var lights = []; segs.forEach(function (s) { for (var z = s[0] + 10; z < s[1] - 6; z += 34) lights.push(z); });
    var lamps = new T3.InstancedMesh(lampGeo, VC, Math.max(1, lights.length)); o.scale.set(1, 1, 1); o.rotation.set(0, 0, 0);
    lights.forEach(function (z, i) { o.position.set(0, 0.3, z); o.updateMatrix(); lamps.setMatrixAt(i, o.matrix); }); lamps.count = lights.length; medianG.add(lamps);
    var lp = []; lights.forEach(function (z) { lp.push(-2.1, 8.7, z, 2.1, 8.7, z); });
    var lg = new T3.BufferGeometry(); lg.setAttribute('position', new T3.Float32BufferAttribute(lp.length ? lp : [0, -99, 0], 3));
    var heads = new T3.Points(lg, lampHeadM); heads.userData.night = 1; medianG.add(heads);
    var pools = new T3.InstancedMesh(poolG, poolM, Math.max(1, lights.length * 2)); pools.userData.night = 1;
    lights.forEach(function (z, i) { [-1, 1].forEach(function (sd, j) { o.position.set(sd * 5.6, 0.05, z); o.updateMatrix(); pools.setMatrixAt(i * 2 + j, o.matrix); }); });
    pools.count = lights.length * 2; medianG.add(pools);
    medianG.children.forEach(function (c) { if (c.userData.night) c.visible = LIGHT.night && !(typeof SOL !== 'undefined' && SOL.on); });
  }
  var BASE_GAPS = [GAP_N, GAP_S];
  buildMedian(BASE_GAPS);
  // buildings, window bands, shop awnings, trees (all instanced, all made up)
  var cityMeshes = [], nightCity = [];
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
    B.forEach(function (b, i) { o.position.set(b[0], 0, b[1]); o.scale.set(b[4], b[3], b[2]); o.updateMatrix(); bm.setMatrixAt(i, o.matrix); bm.setColorAt(i, col(b[5])); }); scene.add(bm); cityMeshes.push(bm);
    var wm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: col('#45515c') }), W.length);
    W.forEach(function (b, i) { o.position.set(b[0], b[1], b[2]); o.scale.set(0.12, b[4], b[3]); o.updateMatrix(); wm.setMatrixAt(i, o.matrix); }); scene.add(wm); cityMeshes.push(wm);
    var cells = [], RW = rng(9090); W.forEach(function (b) { var n = Math.max(1, Math.floor(b[3] / 2.4)); for (var q = 0; q < n; q++) if (RW() < 0.4) cells.push([b[0] + (b[0] < 0 ? 0.04 : -0.04), b[1], b[2] - b[3] / 2 + (q + 0.5) * b[3] / n, b[3] / n * 0.7, b[4] * 0.85, RW()]); });
    var lit = new T3.InstancedMesh(box, new T3.MeshBasicMaterial({ color: 0xffffff }), Math.max(1, cells.length)), wc = ['#FFC98A', '#FFB86B', '#FFE4BD', '#BFD4FF', '#FFD9A0'];
    cells.forEach(function (c, i) { o.position.set(c[0], c[1], c[2]); o.scale.set(0.12, c[4], c[3]); o.updateMatrix(); lit.setMatrixAt(i, o.matrix); lit.setColorAt(i, col(wc[Math.floor(c[5] * 5)]).multiplyScalar(0.35 + 0.6 * c[5])); });
    lit.visible = false; scene.add(lit); nightCity.push(lit);
    var sm = new T3.InstancedMesh(box, new T3.MeshLambertMaterial({ color: 0xffffff }), S.length);
    S.forEach(function (b, i) { o.position.set(b[0], b[1], b[2]); o.scale.set(2.0, 0.35, b[3]); o.updateMatrix(); sm.setMatrixAt(i, o.matrix); sm.setColorAt(i, col(b[4])); }); scene.add(sm); cityMeshes.push(sm);
    var P = new Parts(); P.box(0, 1.2, 0, 0.32, 2.4, 0.32, '#6a5039').geo(new T3.IcosahedronGeometry(2.3, 0), 0, 4.0, 0, '#557d3d').geo(new T3.IcosahedronGeometry(1.6, 0), 0.9, 5.2, 0.5, '#4a7035');
    var tg = P.build(), tm = new T3.InstancedMesh(tg, new T3.MeshLambertMaterial({ vertexColors: true, flatShading: true }), Tr.length);
    Tr.forEach(function (t, i) { o.position.set(t[0], 0.18, t[1]); o.scale.set(t[2], t[2] * rr(0.9, 1.15), t[2]); o.rotation.y = rr(0, 6); o.updateMatrix(); tm.setMatrixAt(i, o.matrix); }); scene.add(tm); cityMeshes.push(tm);
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
  function makeTraffic(dir) {
    var heavy = heavyDir(dir);
    VEH = []; VARIANTS.forEach(function (v) { v.list = []; v.mesh = null; });
    meshes.forEach(function (m) { scene.remove(m); m.dispose && m.dispose(); }); meshes = [];
    var start = dir === 'ba' ? B : A, cs = start[0] < 0 ? 0 : 1;
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
    if (heads) { scene.remove(heads); heads.geometry.dispose(); } if (tails) { scene.remove(tails); tails.geometry.dispose(); }
    heads = lightCloud(VEH.length * 2, headM); tails = lightCloud(VEH.length * 2, tailM); heads.visible = tails.visible = LIGHT.night;
    VARIANTS.forEach(function (v) { if (!v.list.length) return; var m = new T3.InstancedMesh(v.g, VC, v.list.length); m.instanceMatrix.setUsage(T3.DynamicDrawUsage); m.frustumCulled = false; v.mesh = m; scene.add(m); meshes.push(m); });
  }
  var player = new T3.Mesh(vCar('#d9dde2'), VC); scene.add(player);
  var headM = glowPts('#FFFFFF', 1.9), tailM = glowPts('#FFFFFF', 1.0), heads = null, tails = null; headM.vertexColors = tailM.vertexColors = true;
  function lightCloud(n, m) { var g = new T3.BufferGeometry(); g.setAttribute('position', new T3.BufferAttribute(new Float32Array(Math.max(1, n) * 3), 3)); g.setAttribute('color', new T3.BufferAttribute(new Float32Array(Math.max(1, n) * 3), 3)); var p = new T3.Points(g, m); p.frustumCulled = false; scene.add(p); return p; }
  var beam = new T3.Mesh(new T3.PlaneGeometry(8, 30), new T3.MeshBasicMaterial({ map: GLOW, color: col('#FFF0D0'), transparent: true, opacity: 0.3, blending: T3.AdditiveBlending, depthWrite: false }));
  beam.rotation.x = -Math.PI / 2; beam.visible = false; scene.add(beam);

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
    [[st, 'You are here', '#9AA0A6', 0x9aa0a6], [en, 'Where you need to be · ' + SM, '#E8A87C', 0xe8a87c]].forEach(function (q) {
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
    [-1, 1].forEach(function (sd) { sg.beginPath(); sg.moveTo(X(sd * STRAIGHT / 2), Y(top)); sg.lineTo(X(sd * STRAIGHT / 2), Y(bot)); sg.stroke(); });
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

  // ---------------- page text for the chosen place ----------------
  (function () {
    if (PID === 'S18') return;
    var d = DRIVES.ab, set = function (id, t) { var e = $(id); if (e) e.textContent = t; };
    document.title = 'arcroad · ' + Math.round(STRAIGHT) + ' metres across at ' + PID;
    set('p-h1', Math.round(STRAIGHT) + ' metres across.');
    set('p-lead', PL.road + ', ' + PL.area + '. The other side is ' + SM + ' away, and there is no way across. Take the wheel for the detour we drove on ' + PL.day + (PL.night ? ' after dark' : '') + ', on its real clock.');
    set('h-straight', SM); set('intro-h', 'The other side is ' + SM + ' away, across the median.');
    set('s-who', 'Illustration, not a design: distances are measured on this drawing. ' + PL.owner);
    var act = $('s-act'); if (act) act.href = '../act.html?pair=' + PID;
    var f = $('facts'); if (f) f.innerHTML = '<div><b>' + SM + '</b><span>Straight across, on OpenStreetMap. The median has no gap at this point.</span></div>' +
      '<div><b>' + (d.m / 1000).toFixed(2) + ' km · ' + fmtDur(d.s) + '</b><span>' + d.from.charAt(0).toUpperCase() + d.from.slice(1) + ' to ' + d.to + ', as we drove it on ' + PL.day + (PL.night ? ', after dark' : '') + '. The model said ' + (d.model / 1000).toFixed(2) + ' km.</span></div>' +
      '<div><b>Not driven yet</b><span>' + d.to.charAt(0).toUpperCase() + d.to.slice(1) + ' to ' + d.from + '. We publish it once it has been driven.</span></div>' +
      '<div><b>Evidence level 1</b><span>Driven and matched the model, counted under a pairing rule changed on 2 Nov after this drive was seen. <a href="../field/">Every pass we drove</a></span></div>';
    var n1 = $('n-clock'); if (n1) n1.textContent = 'The distance and the clock are from our drive on ' + PL.day + ', after dark (22:55–23:49 IST, a Monday): one driver, one car, phone GPS once a second (about ±50 m). Night times are shorter than at peak hours. Where the car slows and stops is illustrated; the total time is what we measured.';
    var n2 = $('n-road'); if (n2) n2.textContent = 'The road is drawn straight, level and to scale in length; the real road here is a flyover and bends, and its exact U-turn points may sit a little nearer or further. The vehicles, buildings and trees are made up for illustration. No photo, person or number plate from the drive appears anywhere.';
    Array.prototype.forEach.call($('c-dir').querySelectorAll('button'), function (b) { var k = b.getAttribute('data-v');
      if (!DRIVES[k]) b.hidden = true; else b.textContent = DRIVES[k].from.charAt(0).toUpperCase() + DRIVES[k].from.slice(1) + ' to ' + DRIVES[k].to; });
  })();

  // ---------------- state ----------------
  var S = { dir: 'ab', rate: 8, mode: 'intro', t: 0, above: RM, orbit: 0.6 };
  var camPos = new T3.Vector3(30, 26, 30), camLook = new T3.Vector3(0, 0, 0), tmpP = new T3.Vector3(), tmpL = new T3.Vector3();
  var stage = host, playB = $('play'), skipB = $('skip'), viewB = $('view'), introC = $('intro'), result = $('result');
  function setPressed(groupId, v) { Array.prototype.forEach.call($(groupId).querySelectorAll('button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === String(v))); }); }
  function two(lg, sm) { return '<span class="lg">' + lg + '</span><span class="sm">' + sm + '</span>'; }
  function updateViewBtn() { viewB.innerHTML = S.above ? two("Driver's view", 'Driver') : two('View from above', 'Above'); viewB.setAttribute('aria-pressed', String(S.above)); }
  function reset(dir) {
    if (SOL && SOL.on) closeSol();
    S.dir = dir; S.t = 0; S.mode = 'intro'; stage.classList.remove('done'); result.hidden = true; introC.hidden = false;
    var d = DRIVES[dir];
    $('intro-body').textContent = 'You are on the ' + d.from + '. To reach the ' + d.to + ', drive away from it to the gap in the median, turn, and come back.';
    playB.textContent = 'Drive'; skipB.disabled = true; makeTraffic(dir); makePins(dir); setPressed('c-dir', dir); hud(0, 0);
  }
  function hud(s, kmh) { $('h-dist').textContent = fmtM(s); $('h-clock').textContent = fmtClock(S.t); $('h-spd').textContent = Math.round(kmh); $('h-rate').textContent = 'Replayed ' + S.rate + '× faster'; }
  function finish() {
    S.mode = 'done'; S.t = PACE[S.dir].T; stage.classList.add('done'); playB.textContent = 'Drive again'; skipB.disabled = true;
    var d = DRIVES[S.dir], o = DRIVES[S.dir === 'ab' ? 'ba' : 'ab'];
    $('r-head').textContent = SM + ' across. ' + (d.m / 1000).toFixed(2) + ' km and ' + fmtDur(d.s) + ' to get there.';
    $('r-body').textContent = 'That is the drive we made on ' + PL.day + (PL.night ? ', after dark,' : '') + ' from the ' + d.from + ' to the ' + d.to + '. ' +
      (o ? 'The other way, ' + o.from + ' to ' + o.to + ', took ' + fmtDur(o.s) + ' for ' + (o.m / 1000).toFixed(2) + ' km. One drive each way, at one time of day: another hour will differ.' : 'The other way has not been driven yet. One drive, at one time of day: another hour will differ.');
    var both = !!o, km = (d.m + (o ? o.m : 0) - (both ? 2 : 1) * STRAIGHT) / 1000 * COST.days, secs = (d.s + (o ? o.s : 0)) * COST.days;
    $('r-month').textContent = (both ? 'Crossing once each way every working day' : 'Crossing this way once every working day') + ': about ' + Math.round(km) + ' km and ' + fmtDur(secs) +
      ' of driving a month, and about ₹' + Math.round(km / COST.tw * COST.petrol) + ' of petrol on a two-wheeler or ₹' + Math.round(km / COST.car * COST.petrol) + ' in a car.';
    $('r-ev').textContent = d.ev; $('r-cost').href = d.cost;
    $('r-other').hidden = !both;
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
    if (LIGHT.night && heads) {
      var hp = heads.geometry.attributes.position.array, tp = tails.geometry.attributes.position.array;
      for (i = 0; i < VEH.length; i++) { v = VEH[i]; var dz = dirOf(v.c), w = v.len < 2.2 ? 0 : 0.62, f = v.z + dz * (v.len / 2 + 0.1), b = v.z - dz * (v.len / 2 + 0.1);
        hp[i * 6] = v.x - w; hp[i * 6 + 1] = 0.75; hp[i * 6 + 2] = f; hp[i * 6 + 3] = v.x + w; hp[i * 6 + 4] = 0.75; hp[i * 6 + 5] = f;
        tp[i * 6] = v.x - w; tp[i * 6 + 1] = 0.8; tp[i * 6 + 2] = b; tp[i * 6 + 3] = v.x + w; tp[i * 6 + 4] = 0.8; tp[i * 6 + 5] = b; }
      var hc = heads.geometry.attributes.color.array, tc = tails.geometry.attributes.color.array;
      for (i = 0; i < VEH.length; i++) { var mine = VEH[i].c === pc, hk = mine ? 0.18 : (LIGHT.glare ? 1.6 : 1), tk = mine ? 1 : 0.25;
        for (var j = 0; j < 2; j++) { hc.set([0.95 * hk, 0.97 * hk, hk], i * 6 + j * 3); tc.set([tk, 0.09 * tk, 0.05 * tk], i * 6 + j * 3); } }
      heads.geometry.attributes.position.needsUpdate = true; tails.geometry.attributes.position.needsUpdate = true;
      heads.geometry.attributes.color.needsUpdate = true; tails.geometry.attributes.color.needsUpdate = true;
    }
  }


  // ---------------- what could fix this (illustrations, not designs) ----------------
  var SOL = { on: false, k: 'nearer', L: 375, tSol: 0, grow: 0 };
  var solG = new T3.Group(); scene.add(solG);
  var mOld = new T3.MeshBasicMaterial({ color: col('#9AA0A6'), transparent: true, opacity: 0.55, depthWrite: false, side: T3.DoubleSide });
  var chev = (function () { var c = document.createElement('canvas'); c.width = 64; c.height = 64; var g = c.getContext('2d');
    g.fillStyle = '#E8935A'; g.fillRect(0, 0, 64, 64); g.strokeStyle = '#FFE2C8'; g.lineWidth = 7; g.lineCap = 'round'; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(18, 14); g.lineTo(40, 32); g.lineTo(18, 50); g.stroke();
    var t = new T3.CanvasTexture(c); t.wrapS = t.wrapT = T3.RepeatWrapping; t.encoding = T3.sRGBEncoding; t.anisotropy = 4; return t; })();
  var mNew = new T3.MeshBasicMaterial({ map: chev, transparent: true, opacity: 0.98, depthWrite: false, side: T3.DoubleSide });
  var ghostFill = new T3.MeshBasicMaterial({ color: col('#E8A87C'), transparent: true, opacity: 0.1, depthWrite: false, side: T3.DoubleSide });
  var ghostLine = new T3.LineBasicMaterial({ color: col('#F0C2A0'), transparent: true, opacity: 0.85 });
  function mirrored(r) { if (S.dir === 'ba') { r.x = r.x.map(function (v) { return -v; }); r.z = r.z.map(function (v) { return -v; }); } return r; }
  function ribbon(r, ys, mat, w, lift) {
    var pts = [], i, n = r.x.length;
    for (i = 0; i < n; i += 4) pts.push(i); if (pts[pts.length - 1] !== n - 1) pts.push(n - 1);
    var pos = new Float32Array(pts.length * 6), uv = new Float32Array(pts.length * 4), idx = [];
    pts.forEach(function (i, k) {
      uv.set([r.s[i] / w, 0, r.s[i] / w, 1], k * 4);
      var j = Math.min(n - 1, i + 4), h = Math.max(0, i - 4), dx = r.x[j] - r.x[h], dz = r.z[j] - r.z[h], d = Math.hypot(dx, dz) || 1;
      var nx = -dz / d * w / 2, nz = dx / d * w / 2, y = (ys ? ys(r.s[i]) : 0) + lift;
      pos.set([r.x[i] + nx, y, r.z[i] + nz, r.x[i] - nx, y, r.z[i] - nz], k * 6);
      if (k) { var a = (k - 1) * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    });
    var g = new T3.BufferGeometry(); g.setAttribute('position', new T3.BufferAttribute(pos, 3)); g.setAttribute('uv', new T3.BufferAttribute(uv, 2)); g.setIndex(idx);
    var m = new T3.Mesh(g, mat); m.renderOrder = 5; m.userData.total = idx.length; return m;
  }
  function ghostBox(w, h, d, x, y, z) {
    var g = new T3.BoxGeometry(w, h, d), grp = new T3.Group();
    grp.add(new T3.Mesh(g, ghostFill)); grp.add(new T3.LineSegments(new T3.EdgesGeometry(g), ghostLine)); grp.position.set(x, y, z); return grp;
  }
  function signalPole(x, z, face) {
    var grp = new T3.Group(), dark = new T3.MeshLambertMaterial({ color: col('#2a2d31') });
    var pole = new T3.Mesh(new T3.CylinderGeometry(0.09, 0.11, 5.2, 10), dark); pole.position.y = 2.6; grp.add(pole);
    var head = new T3.Mesh(new T3.BoxGeometry(0.42, 1.2, 0.36), dark); head.position.set(0, 4.7, 0); grp.add(head);
    ['#e2463a', '#e8b13a', '#4cc38a'].forEach(function (c, i) {
      var lamp = new T3.Mesh(new T3.SphereGeometry(0.13, 12, 8), new T3.MeshBasicMaterial({ color: col(c) }));
      lamp.position.set(0, 5.05 - i * 0.36, face * 0.19); lamp.userData.lamp = i; grp.add(lamp);
    });
    grp.position.set(x, 0, z); return grp;
  }
  var OPT = {
    nearer: { n: 1, title: 'A U-turn opening nearer',
      lead: function (o) { return 'On this drawing the nearest U-turn is about ' + o.cur + ' m away, which is why crossing ' + SM + ' took ' + o.today + '. Bring an opening to ' + o.L + ' m and the crossing becomes about ' + o.nw + '.'; },
      guide: 'Guidance: India\'s access-control guidelines keep median openings to intersections with public roads, at least 750 m apart on highways (IRC:62). An IIT course text gives 500 m as the closest on other highways.',
      trade: 'Trade-off: every opening is another place where turning and through traffic meet. Studies abroad find openings that allow only U-turns have fewer crashes overall than full openings, though the U-turns pile up further along.' },
    jturn: { n: 2, title: 'A signal-free U-turn with a bay',
      lead: function (o) { return 'No signal and no full opening: a U-turn-only opening about ' + JT + ' m away, with a widened bay (a "loon") so turning vehicles do not stop the through lanes. The crossing becomes about ' + o.nw + '.'; },
      guide: 'Guidance: known in the US as a J-turn or restricted crossing U-turn; the US Federal Highway Administration lists it as a proven safety countermeasure, and a Missouri study found 35% fewer crashes and 54% fewer injury crashes (FHWA-HRT-17-082). In India, IRC:62 keeps median openings to intersections, so where it fits is the road owner\'s call.',
      trade: 'Trade-off: longer than a full opening at this spot, it needs room on the far side for the bay, and buses and trucks need a wider one. Traffic keeps moving, which is the point.' },
    signal: { n: 3, title: 'A signal-controlled crossing here',
      lead: function (o) { return 'Open the median at this place and control it with a signal. The crossing becomes about ' + o.nw + ', plus the wait at the light.'; },
      guide: 'Guidance: signals in India follow IRC:93, which asks for a traffic study showing a signal is warranted before one is installed.',
      trade: 'Trade-off: through traffic stops more often, and a signal needs that study, power and upkeep.' },
    under: { n: 4, title: 'A U-turn underpass',
      lead: function (o) { return 'Turn under the road instead of across it. In this layout the crossing is about ' + o.nw + ', with no conflict with through traffic.'; },
      guide: 'Guidance: India\'s six-lane highway standard provides vehicular underpasses or overpasses at major crossings, with service roads instead of direct access (IRC:SP:87).',
      trade: 'Trade-off: the costliest option, with land, drainage and years of works. It suits heavy flows, not every street.' },
    why: { n: 5, title: 'Why not a gap every hundred metres?',
      lead: function () { return 'Because each opening is a new point where turning and through traffic cross. That is why the guidance keeps openings few and at intersections.'; },
      guide: 'Guidance: median openings limited to intersections, their number kept to a minimum (IRC:62).',
      trade: 'Which option fits this place depends on its traffic, and that study is the road owner\'s. arcroad measures what the detour costs; it does not choose the fix.' }
  };
  function nearDist() { return Math.round(RT[S.dir].L); }
  var JT = 300;   // J-turn spacing on the drawing: US practice puts the U-turn about 300-450 m from the junction
  function solPath() {
    if (SOL.k === 'jturn') return { r: mirrored(route(JT)), gap: JT + LANES[0], loon: true };
    if (SOL.k === 'nearer') return { r: mirrored(route(SOL.L)), gap: SOL.L + LANES[0] };
    if (SOL.k === 'signal') return { r: mirrored(route(7)), gap: 7 + LANES[0] };
    if (SOL.k === 'under') return { r: mirrored(route(110)), gap: 110 + LANES[0], under: true };
    return { r: null };
  }
  var undY = null, dayBg = scene.background, dayFog = scene.fog.color.clone(), dayGround = groundMesh.material.color.clone();
  var nightBg = (function () { var c = document.createElement('canvas'); c.width = 4; c.height = 256; var g = c.getContext('2d');
    var gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#05070B'); gr.addColorStop(1, '#10141B'); g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
    var t = new T3.CanvasTexture(c); t.encoding = T3.sRGBEncoding; return t; })();
  function blueprint(on) {
    cityMeshes.forEach(function (m) { m.visible = !on; }); nightCity.forEach(function (m) { m.visible = !on && LIGHT.night; });
    if (!on) { applyLight(); return; }
    scene.background = on ? nightBg : dayBg; scene.fog.color.copy(on ? col('#0B0E13') : dayFog);
    groundMesh.material.color.copy(on ? col('#151A21') : dayGround); walkM.color.copy(col(on ? '#3b3833' : '#a49a8a'));
  }
  function setXray(on) {
    [asphalt, groundMesh.material].forEach(function (m) { m.transparent = on; m.opacity = on ? 0.32 : 1; m.depthWrite = !on; m.needsUpdate = true; });
  }
  function buildSolution() {
    while (solG.children.length) { var c = solG.children.pop(); c.traverse(function (m) { if (m.geometry) m.geometry.dispose(); }); }
    var sp = solPath(), sg = S.dir === 'ab' ? -1 : 1, today = RT[S.dir];
    setXray(!!sp.under);
    var W = SOL.w || 1.5;
    solG.add(ribbon(today, null, mOld, W * 0.7, 0.06));
    if (!sp.r) {
      buildMedian(BASE_GAPS);
      for (var z = 40; z < nearDist() - 30; z += 100) { var ring = new T3.Mesh(new T3.RingGeometry(1.6, 2.3, 40), new T3.MeshBasicMaterial({ color: col('#ff5a4a'), transparent: true, opacity: 0.9, depthWrite: false, depthTest: false })); ring.renderOrder = 7; ring.rotation.x = -Math.PI / 2; ring.position.set(0, 0.7, sg * z); ring.userData.base = Math.max(1, W / 1.2); ring.scale.setScalar(ring.userData.base); ring.userData.pulse = z; solG.add(ring); }
      var t = label('Each opening: a conflict point', '#ff5a4a'); var lk2 = Math.max(1, (SOL.d || 120) / 70); t.scale.set(12 * lk2, 2 * lk2, 1); t.position.set(0, 8 * lk2, sg * Math.min(240, nearDist() / 2)); solG.add(t);
      SOL.route = null; return;
    }
    buildMedian(BASE_GAPS.concat(sp.under ? [] : [sg * sp.gap]));
    var L = sp.r.L, arc0 = L, arc1 = L + Math.PI * LANES[0];
    undY = sp.under ? function (s) { var d = s < arc0 ? (s - (arc0 - 45)) / 45 : (s > arc1 ? 1 - (s - arc1) / 45 : 1); return -4.6 * smooth(d); } : null;
    var nr = ribbon(sp.r, undY, mNew, W, 0.09); nr.geometry.setDrawRange(0, 0); solG.add(nr); SOL.ribbon = nr;
    if (sp.under) {
      var zc = sg * (L + 1.5);
      solG.add(ghostBox(22, 4.4, 15, 0, -2.6, zc));
      [-1, 1].forEach(function (x) {
        var rg = new T3.PlaneGeometry(3.8, 46); var rm = new T3.Mesh(rg, ghostFill); rm.rotation.x = -Math.PI / 2 + Math.atan2(4.6, 46) * (sg < 0 ? 1 : -1); rm.position.set(x * LANES[0], -2.3, sg * (L - 22)); solG.add(rm);
        var re = new T3.LineSegments(new T3.EdgesGeometry(rg), ghostLine); re.rotation.copy(rm.rotation); re.position.copy(rm.position); solG.add(re);
      });
    }
    if (SOL.k === 'signal') { solG.add(signalPole(-EDGE - 0.6, sg * (sp.gap + 9), -sg)); solG.add(signalPole(EDGE + 0.6, sg * (sp.gap - 9), sg)); }
    var lk = Math.max(1, (SOL.d || 120) / 70);
    function tag(text, accent, z, y) { var t = label(text, accent ? '#E8A87C' : '#9AA0A6'); t.scale.set(12 * lk, 2 * lk, 1); t.position.set(0, y || 6 * lk, z); solG.add(t); }
    if (SOL.k === 'nearer') { tag('New opening · ' + SOL.L + ' m', true, sg * sp.gap); if (nearDist() - SOL.L > 60) tag('Today\'s U-turn · ' + nearDist() + ' m', false, sg * (nearDist() + 3)); }
    if (SOL.k === 'signal') tag('Signal-controlled opening', true, sg * sp.gap, 9);
    if (SOL.k === 'jturn') { var bx = (S.dir === 'ab' ? 1 : -1) * (EDGE + 1.6); solG.add(ghostBox(3.2, 0.25, 34, bx, 0.12, sg * sp.gap)); tag('U-turn only · bay · ' + JT + ' m', true, sg * sp.gap); }
    if (SOL.k === 'under') tag('U-turn underpass', true, sg * (sp.gap - 2), 7);
    SOL.route = sp.r; SOL.grow = 0;
  }
  function solNumbers() {
    var sp = solPath(), d = DRIVES[S.dir], o = { cur: nearDist(), L: SOL.L, today: (d.m / 1000).toFixed(2) + ' km' };
    if (sp.r) { var m = sp.r.len; o.nwM = m; o.nw = m >= 1000 ? (m / 1000).toFixed(2) + ' km' : Math.round(m / 10) * 10 + ' m'; }
    return o;
  }
  function renderSol() {
    var t = OPT[SOL.k], o = solNumbers();
    $('s-eyebrow').textContent = 'Option ' + t.n + ' of 5 · illustration, not a design';
    $('s-title').textContent = t.title;
    $('s-lead').textContent = t.lead(o);
    $('s-guide').textContent = t.guide; $('s-trade').textContent = t.trade;
    var nums = $('s-nums');
    if (o.nw) {
      nums.hidden = false; $('s-today').textContent = o.today; $('s-new').textContent = o.nw;
      var save = (DRIVES[S.dir].m - o.nwM) / 1000;
      $('s-save').textContent = 'about ' + save.toFixed(2) + ' km shorter each time'; $('s-save').hidden = false;
    } else { nums.hidden = true; $('s-save').hidden = true; }
    $('s-range').hidden = SOL.k !== 'nearer';
    var rg = $('s-L'); rg.max = Math.max(150, nearDist() - 20); $('s-Lv').textContent = SOL.L + ' m';
    Array.prototype.forEach.call(document.querySelectorAll('#s-tabs button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-k') === SOL.k)); });
  }
  function openSol(k) {
    if (S.mode === 'driving') { S.mode = 'paused'; playB.textContent = 'Resume'; }
    AUTO.on = k === 'auto'; AUTO.t = 0; if (AUTO.on) k = randomKind(); autoBtn();
    SOL.on = true; SOL.k = k || SOL.k; SOL.tSol = 0; stage.classList.add('sol'); scene.fog.near = 400; scene.fog.far = 3000; blueprint(true);
    solView(); buildSolution(); renderSol(); kick(); host.focus({ preventScroll: true });
  }
  function closeSol() {
    SOL.on = false; cam.clearViewOffset(); stage.classList.remove('sol'); scene.fog.near = 60; scene.fog.far = 205; setXray(false); blueprint(false);
    while (solG.children.length) { var c = solG.children.pop(); c.traverse(function (m) { if (m.geometry) m.geometry.dispose(); }); }
    buildMedian(BASE_GAPS); kick();
  }
  Array.prototype.forEach.call(document.querySelectorAll('#s-tabs button[data-k]'), function (b) { b.addEventListener('click', function () { stopAuto(); SOL.k = b.getAttribute('data-k'); solView(); buildSolution(); renderSol(); kick(); }); });
  if ($('s-auto')) $('s-auto').addEventListener('click', function () { AUTO.on = !AUTO.on; AUTO.t = AUTO.every; autoBtn(); kick(); });
  Array.prototype.forEach.call(document.querySelectorAll('[data-sol]'), function (b) { b.addEventListener('click', function (e) { e.preventDefault(); openSol(b.getAttribute('data-sol')); if (b.closest('.fixes')) host.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'center' }); }); });
  $('s-back').addEventListener('click', closeSol);
  $('s-more').addEventListener('click', function () { var p = $('solp'), f = p.classList.toggle('full'); this.setAttribute('aria-expanded', String(f)); this.textContent = f ? 'Less' : 'Guidance and trade-off'; });
  var lTimer = 0;
  $('s-L').addEventListener('input', function (e) { stopAuto(); SOL.L = +e.target.value; $('s-Lv').textContent = SOL.L + ' m'; renderSol(); clearTimeout(lTimer); lTimer = setTimeout(function () { solView(); buildSolution(); SOL.grow = 1; if (SOL.ribbon) SOL.ribbon.geometry.setDrawRange(0, SOL.ribbon.userData.total); kick(); }, 60); });
  // frame the option: road across the free part of the stage (the panel takes the left side on wide screens)
  function solView() {
    var sg = S.dir === 'ab' ? -1 : 1, sp = solPath(), wide = (cam.aspect || 1.7) >= 1;
    var span = SOL.k === 'signal' ? 60 : (SOL.k === 'under' ? 170 : (sp.r ? sp.r.L + 70 : Math.min(520, nearDist() + 40)));
    var zc = SOL.k === 'under' ? sg * (sp.r.L - 45) : sg * (span / 2 - 22);
    var d = Math.max(48, span * (wide ? 0.78 : 1.05));
    SOL.d = d; SOL.w = Math.max(1.4, Math.min(6, d / 85));
    SOL.look = new T3.Vector3(0, SOL.k === 'under' ? -2 : 0, zc);
    SOL.pos = wide ? new T3.Vector3(0.62 * d, (SOL.k === 'under' ? 0.42 : 0.6) * d, zc - sg * 0.5 * d) : new T3.Vector3(0.2 * d, 0.9 * d, zc - sg * 0.55 * d);
    var w = host.clientWidth, h = host.clientHeight;
    if (wide) cam.setViewOffset(w, h, -Math.min(260, w * 0.21), 0, w, h); else cam.setViewOffset(w, h, 0, Math.round(h * 0.2), w, h);
  }
  function solFrame(dt, now) {
    autoStep(dt); SOL.tSol += dt; var sg = S.dir === 'ab' ? -1 : 1;
    if (SOL.ribbon && SOL.grow < 1) { SOL.grow = Math.min(1, SOL.grow + dt / (RM ? 0.01 : 1.1)); SOL.ribbon.geometry.setDrawRange(0, Math.floor(SOL.ribbon.userData.total * smooth(SOL.grow) / 3) * 3); }
    solG.children.forEach(function (c) {
      if (c.userData.pulse) c.scale.setScalar(c.userData.base * (1 + 0.15 * Math.sin(now / 280 + c.userData.pulse)));
      c.traverse && c.traverse(function (m) { if (m.userData.lamp !== undefined) { var ph = Math.floor(SOL.tSol / 2.2) % 3; m.material.color.setHex(m.userData.lamp === [0, 2, 1][ph] ? [0xff5a4a, 0xffc24a, 0x5ff0a6][m.userData.lamp] : 0x26292d); } });
    });
    var r = SOL.route || RT[S.dir], len = r.len, spd = Math.max(len / 7, 8), s = (SOL.tSol * spd) % (len + spd * 1.2);
    s = Math.min(s, len); var p = at(r, s);
    player.position.set(p.x, SOL.route && undY ? undY(s) : 0, p.z); player.rotation.y = Math.atan2(-p.hx, -p.hz); player.visible = true; cockpit.visible = false;
    var drift = RM ? 0 : Math.sin(SOL.tSol * 0.18) * 0.06;
    tmpP.copy(SOL.pos).sub(SOL.look).applyAxisAngle(cam.up, drift).add(SOL.look); tmpL.copy(SOL.look);
    chev.offset.x = -(SOL.tSol * 0.9) % 1;
  }

  // ---------------- day and night ----------------
  var dayHemi = hemi.intensity, daySun = sun.intensity, WHITE = new T3.Color(1, 1, 1);
  var nightSky = (function () { var c = document.createElement('canvas'); c.width = 4; c.height = 256; var g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, '#02040A'); gr.addColorStop(0.6, '#0C1220'); gr.addColorStop(1, '#231E29'); g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
    var t = new T3.CanvasTexture(c); t.encoding = T3.sRGBEncoding; return t; })();
  var cityDay = cityMeshes.map(function (m) { return m.material.color.clone(); }), cityNight = ['#2B2E35', '#0F1217', '#3A3633', '#26332A'];
  var beamG = new T3.Group(); scene.remove(beam); beam.position.set(0, 0.06, -17); beamG.add(beam); scene.add(beamG);
  function applyLight() {
    var n = LIGHT.night;
    if (!n) LIGHT.glare = false;
    if (!SOL.on) {
      scene.background = n ? nightSky : dayBg; scene.fog.color.copy(n ? col('#0B0E16') : dayFog); scene.fog.near = n ? 40 : 60; scene.fog.far = n ? 260 : 205;
      groundMesh.material.color.copy(n ? col('#0D0E11') : dayGround); walkM.color.copy(col(n ? '#2A2826' : '#a49a8a'));
    }
    hemi.intensity = n ? 0.2 : dayHemi; sun.intensity = n ? 0.03 : daySun;
    asphalt.color.copy(n ? col('#55585F') : WHITE); if (lineMat) lineMat.color.copy(col(n ? '#7B7D83' : '#e9e6dc')); VC.color.copy(n ? col('#4A4D54') : WHITE);
    cityMeshes.forEach(function (m, i) { m.material.color.copy(n ? col(cityNight[i]) : cityDay[i]); });
    nightCity.forEach(function (m) { m.visible = n && !SOL.on; });
    shrubM.color.copy(n ? col('#3A3F3A') : WHITE);
    if (medianG) medianG.traverse(function (o) { (Array.isArray(o.material) ? o.material : [o.material]).forEach(function (m) { if (m && m.userData.dim) m.color.copy(n ? col('#4A4A4A') : WHITE); }); });
    if (medianG) medianG.children.forEach(function (c) { if (c.userData.night) c.visible = n && !SOL.on; });
    if (heads) heads.visible = tails.visible = n; headM.size = LIGHT.glare ? 3.2 : 1.9; beam.visible = n;
    stage.classList.toggle('night', n);
    setPressed('c-light', n ? 'night' : 'day');
    var gb = $('c-glare'); if (gb) { gb.disabled = !n; gb.setAttribute('aria-pressed', String(LIGHT.glare)); }
    var gn = $('glare-note'); if (gn) gn.hidden = !LIGHT.glare;
    if (!LIGHT.glare) clearGlare();
  }
  // Glare from oncoming high beams, from the driver's seat. Same equation as /roads/glare/ (CIE 146:2002, young-eye term):
  //   veil luminance Lveil = 10 · Eeye / θ²   with Eeye = I / d² from two high-beam lamps of 30,000 cd each.
  // Drawn as light scattered across the view; an illustration on a published equation, not a measurement of this road.
  var gc = $('glare'), gx = gc && gc.getContext('2d'), gDirty = false, vt = new T3.Vector3(), fwd = new T3.Vector3();
  function clearGlare() { if (gx && gDirty) { gx.clearRect(0, 0, gc.width, gc.height); gDirty = false; } }
  function drawGlare(p) {
    if (!gx) return;
    var w = gc.clientWidth, h = gc.clientHeight, dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (gc.width !== Math.round(w * dpr) || gc.height !== Math.round(h * dpr)) { gc.width = Math.round(w * dpr); gc.height = Math.round(h * dpr); }
    gx.setTransform(dpr, 0, 0, dpr, 0, 0); gx.clearRect(0, 0, w, h); gDirty = true;
    cam.getWorldDirection(fwd);
    var pc = p.x < 0 ? 0 : 1, list = [], i;
    for (i = 0; i < VEH.length; i++) { var v = VEH[i]; if (v.c === pc) continue;
      var dz = dirOf(v.c), fz = v.z + dz * v.len / 2; if ((camPos.z - fz) * dz <= 0) continue;
      vt.set(v.x, 0.75, fz).sub(camPos); var d = vt.length(); if (d > 180 || d < 2) continue; vt.normalize();
      var th = Math.acos(Math.max(-1, Math.min(1, vt.dot(fwd)))) * 180 / Math.PI; if (th > 70) continue;
      var E = 2 * 30000 / (d * d), L = 10 * E / Math.pow(Math.max(th, 1), 2);
      list.push({ x: v.x, z: fz, L: L }); }
    list.sort(function (a, b) { return b.L - a.L; });
    var tot = 0;
    list.slice(0, 6).forEach(function (q) {
      vt.set(q.x, 0.75, q.z).project(cam); if (vt.z > 1) return;
      var x = (vt.x + 1) / 2 * w, y = (1 - vt.y) / 2 * h, a = 0.85 * (1 - Math.exp(-q.L / 2)), R = Math.max(w, h) * (0.08 + 0.36 * a); tot += q.L;
      var g = gx.createRadialGradient(x, y, 0, x, y, R);
      g.addColorStop(0, 'rgba(255,252,244,' + a.toFixed(3) + ')'); g.addColorStop(0.06, 'rgba(255,248,236,' + (a * 0.7).toFixed(3) + ')');
      g.addColorStop(0.32, 'rgba(225,232,255,' + (a * 0.16).toFixed(3) + ')'); g.addColorStop(1, 'rgba(225,232,255,0)');
      gx.fillStyle = g; gx.fillRect(0, 0, w, h);
    });
    var veil = 1 - Math.exp(-tot / 20); if (veil > 0.01) { gx.fillStyle = 'rgba(210,220,245,' + (veil * 0.14).toFixed(3) + ')'; gx.fillRect(0, 0, w, h); }
  }
  Array.prototype.forEach.call($('c-light').querySelectorAll('button[data-v]'), function (b) { b.addEventListener('click', function () { LIGHT.night = b.getAttribute('data-v') === 'night'; applyLight(); kick(); }); });
  $('c-glare').addEventListener('click', function () { if (!LIGHT.night) return; LIGHT.glare = !LIGHT.glare; if (LIGHT.glare && S.above) { S.above = false; updateViewBtn(); } applyLight(); kick(); });

  // ---------------- place picker: driven places can be chosen; the rest are listed as not driven yet ----------------
  (function () {
    var sel = $('c-place'); if (!sel) return;
    sel.innerHTML = ''; var g1 = document.createElement('optgroup'); g1.label = 'Driven by arcroad';
    Object.keys(PLACES).forEach(function (k) { g1.appendChild(new Option(k + ' · ' + PLACES[k].area + ', ' + PLACES[k].road, k)); });
    sel.appendChild(g1); sel.value = PID;
    sel.addEventListener('change', function () { location.search = sel.value === 'S18' ? '' : '?place=' + sel.value; });
    if (!window.fetch) return;
    fetch('../globe/data/places.json').then(function (r) { return r.json(); }).then(function (d) {
      var g2 = document.createElement('optgroup'); g2.label = 'Not driven yet · help drive one';
      (d.spots || []).forEach(function (sp) { if (PLACES[sp.id]) return; var o = new Option(sp.id + ' · not driven yet', sp.id); o.disabled = true; g2.appendChild(o); });
      if (g2.children.length) sel.appendChild(g2);
    }).catch(function () {});
  })();

  // ---------------- the fixes play by themselves, in random order, until you choose one ----------------
  var AUTO = { on: false, t: 0, every: 9 }, KINDS = ['nearer', 'jturn', 'signal', 'under', 'why'];
  function autoBtn() { var b = $('s-auto'); if (b) { b.setAttribute('aria-pressed', String(AUTO.on)); b.textContent = AUTO.on ? 'Auto · on' : 'Auto'; } }
  function randomKind(not) { var k; do { k = KINDS[Math.floor(Math.random() * KINDS.length)]; } while (k === not); return k; }
  function autoStep(dt) {
    if (!AUTO.on || RM) return; AUTO.t += dt; if (AUTO.t < AUTO.every) return; AUTO.t = 0;
    SOL.k = randomKind(SOL.k);
    if (SOL.k === 'nearer') { var mx = Math.max(150, nearDist() - 20); SOL.L = Math.round((120 + Math.random() * (mx - 120)) / 10) * 10; $('s-L').value = SOL.L; }
    solView(); buildSolution(); renderSol();
  }
  function stopAuto() { AUTO.on = false; autoBtn(); }

  // ---------------- dive into 3D: full screen, drag to look around ----------------
  var DIVE = { on: false, yaw: 0, pitch: 0, drag: null, idle: 0 }, vLook = new T3.Vector3(), UPV = new T3.Vector3(0, 1, 0);
  var diveB = $('dive'), diveX = $('dive-x');
  function enterDive() {
    if (DIVE.on) return;
    DIVE.on = true; DIVE.yaw = DIVE.pitch = 0; stage.classList.add('dive'); document.body.classList.add('diving'); diveB.classList.remove('pulse');
    var fs = host.requestFullscreen || host.webkitRequestFullscreen;
    if (fs) { try { var pr = fs.call(host); if (pr && pr.catch) pr.catch(function () {}); } catch (e) { /* the CSS full-window view still applies */ } }
    if (SOL.on) closeSol();
    if (S.above) { S.above = false; updateViewBtn(); }
    if (S.mode !== 'driving') play();
    var h = $('dhint'); h.classList.add('on'); setTimeout(function () { h.classList.remove('on'); }, 3500);
    setTimeout(size, 60); kick();
  }
  function exitDive() {
    if (!DIVE.on) return;
    DIVE.on = false; DIVE.yaw = DIVE.pitch = 0; DIVE.drag = null; stage.classList.remove('dive'); document.body.classList.remove('diving');
    var d = document; if (d.fullscreenElement || d.webkitFullscreenElement) { var ex = d.exitFullscreen || d.webkitExitFullscreen; if (ex) { try { ex.call(d); } catch (e) { /* already out */ } } }
    setTimeout(size, 60); kick();
  }
  diveB.addEventListener('click', enterDive); diveX.addEventListener('click', exitDive);
  ['fullscreenchange', 'webkitfullscreenchange'].forEach(function (t) { document.addEventListener(t, function () { if (!(document.fullscreenElement || document.webkitFullscreenElement) && DIVE.on && host.requestFullscreen) exitDive(); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && DIVE.on) exitDive(); });
  host.addEventListener('pointerdown', function (e) {
    if (!DIVE.on || SOL.on || (e.target.closest && e.target.closest('button,a,input'))) return;
    DIVE.drag = { x: e.clientX, y: e.clientY, yaw: DIVE.yaw, pitch: DIVE.pitch };
  });
  host.addEventListener('pointermove', function (e) {
    if (!DIVE.drag) return;
    DIVE.yaw = DIVE.drag.yaw - (e.clientX - DIVE.drag.x) * 0.006;
    DIVE.pitch = Math.max(-0.6, Math.min(0.5, DIVE.drag.pitch - (e.clientY - DIVE.drag.y) * 0.004)); DIVE.idle = 0; kick();
  });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (t) { host.addEventListener(t, function () { DIVE.drag = null; }); });

  // ---------------- links from the home page films ----------------
  (function () {
    var q = location.search;
    if (/[?&]light=night/.test(q)) LIGHT.night = true;
    if (/[?&]light=day/.test(q)) LIGHT.night = false;
    if (/[?&]dive=1/.test(q)) { diveB.classList.add('pulse'); setTimeout(function () { host.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'center' }); }, 300); }
    if (/[?&]fix=auto/.test(q)) setTimeout(function () { openSol('auto'); host.scrollIntoView({ block: 'center' }); }, 400);
  })();

  // ---------------- loop ----------------
  var last = 0, running = false, visible = true, lastS = 0;
  function size() { var w = host.clientWidth, h = host.clientHeight; if (!w || !h) return; R.setSize(w, h, false); cam.aspect = w / h; cam.fov = w / h < 1 ? 72 : 60; cam.updateProjectionMatrix(); if (typeof SOL !== 'undefined' && SOL.on) { solView(); buildSolution(); } }
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
    stepTraffic(S.mode === 'driving' ? dt * S.rate : (S.mode === 'paused' ? 0 : dt), S.t, p, S.mode === 'intro' ? 0 : pv, heavyDir(S.dir));
    if (!SOL.on) { player.position.set(p.x, 0, p.z); player.rotation.y = Math.atan2(-p.hx, -p.hz); beamG.position.copy(player.position); beamG.rotation.y = player.rotation.y; }
    beamG.visible = LIGHT.night && !SOL.on;
    var ahead = at(r, s + 22);
    if (SOL.on) {
      solFrame(dt, now);
    } else if (S.mode === 'intro') {
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
    var k = 1 - Math.exp(-dt * (SOL.on ? (RM ? 60 : 1.6) : (S.mode === 'intro' ? 2 : 4.5)));
    camPos.lerp(tmpP, k); camLook.lerp(tmpL, k);
    if (!SOL.on && !S.above && S.mode !== 'intro' && S.mode !== 'done' && camPos.distanceTo(tmpP) < 3) camPos.copy(tmpP);
    cam.position.copy(camPos);
    if (DIVE.on && !SOL.on) {   // look around from wherever the camera is; ease back to the road after a pause
      if (!DIVE.drag) { DIVE.idle += dt; if (DIVE.idle > 2.5) { var fk = Math.exp(-dt * 1.2); DIVE.yaw *= fk; DIVE.pitch *= fk; } }
      vLook.copy(camLook).sub(camPos).applyAxisAngle(UPV, DIVE.yaw);
      vLook.y += Math.hypot(vLook.x, vLook.z) * Math.tan(DIVE.pitch);
      cam.lookAt(vLook.add(camPos));
    } else cam.lookAt(camLook);
    pins.forEach(function (g) { g.children[1].scale.setScalar(1 + 0.08 * Math.sin(now / 400)); });
    if (!SOL.on) { if (S.mode !== 'intro' || Math.abs(s - lastS) > 0.01 || !lastS) hud(s, kmh); lastS = s; drawStrip(S.dir, s); }
    if (LIGHT.glare && !SOL.on && !S.above && S.mode !== 'intro' && S.mode !== 'done') drawGlare(p); else clearGlare();
    R.render(scene, cam);
  }
  function kick() { if (!running && visible) { running = true; requestAnimationFrame(frame); } }
  if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting && !document.hidden; if (visible) { last = 0; kick(); } }).observe(host);
  document.addEventListener('visibilitychange', function () { visible = !document.hidden; if (visible) { last = 0; kick(); } });
  if ('ResizeObserver' in window) new ResizeObserver(size).observe(host); else window.addEventListener('resize', size);
  size(); updateViewBtn(); reset('ab'); applyLight(); kick();
  window.__arcroadDrive = { dbg: function () { return { n: solG.children.length, kinds: solG.children.map(function (c) { return c.type + (c.geometry && c.geometry.drawRange ? ':' + c.geometry.drawRange.count + '/' + (c.userData.total || '') : ''); }), w: SOL.w, pos: SOL.pos && SOL.pos.toArray().map(Math.round), look: SOL.look && SOL.look.toArray().map(Math.round) }; }, SOL: function () { return SOL; }, openSol: function (k) { openSol(k); }, S: S, RT: RT, PACE: PACE, DRIVES: DRIVES, play: play, LIGHT: LIGHT, AUTO: AUTO, applyLight: applyLight, PID: PID,   // hooks for tests and the home-page preview render
    capture: function () { visible = false; host.classList.add('capture'); },
    frame: function (dt, now) { tick(dt, now); return R.domElement.toDataURL('image/jpeg', 0.92); } };
})();
