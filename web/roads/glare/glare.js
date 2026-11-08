/* arcroad · Blinded by the light: an oncoming high beam, seen from the driver's seat.
 *
 * The glare is not painted by eye. Every frame, for every pixel, the veil of scattered light in the
 * eye is computed with the CIE General Disability Glare Equation (CIE 146:2002):
 *   Lveil / Eeye = 10/θ³ + (5/θ² + 0.1·p/θ)·(1 + (A/62.5)⁴) + 0.0025·p
 * θ in degrees between the line of sight and each headlamp, A the driver's age, p = 0.5 (brown eyes).
 * Eeye = I / d² from each lamp's luminous intensity towards the eye: typical values, high beam
 * 30,000 cd a lamp, dipped beam 500 cd a lamp towards an oncoming driver.
 * The person's visibility is their luminance contrast with glare, divided by the same contrast without it:
 *   C = (Lo − Lb) / (Lb + Lveil)
 * An illustration built on published equations, not a measurement of any road.
 * Three.js r147 (MIT), self-hosted. No network, no storage, no tracking.
 */
(function () {
  'use strict';
  var T3 = window.THREE;
  var host = document.getElementById('stage');
  if (!T3 || !host) return;
  var $ = function (id) { return document.getElementById(id); };
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------------- settings (the controls change these) ----------------
  var S = { beam: 'high', age: 35, kmh: 60, wet: false };
  var I_LAMP = { high: 30000, low: 500 };   // cd towards the eye, one lamp
  var P_PIG = 0.5;                           // iris pigmentation: brown
  var T_MEET = 7.6;                          // seconds until the oncoming car draws level
  var GAP_AT_MEET = 26;                      // metres to the person when it does

  // ---------------- renderer, scene, camera ----------------
  var R = new T3.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  var SMALL = Math.min(screen.width, screen.height) < 700;
  R.setPixelRatio(Math.min(window.devicePixelRatio || 1, SMALL ? 1.5 : 2));
  R.outputEncoding = T3.sRGBEncoding;
  host.insertBefore(R.domElement, host.firstChild);
  R.domElement.setAttribute('aria-hidden', 'true');
  var scene = new T3.Scene();
  scene.background = new T3.Color(0x05070b);
  scene.fog = new T3.FogExp2(0x070a10, 0.0105);
  var FOV = 62;
  var cam = new T3.PerspectiveCamera(FOV, 16 / 9, 0.1, 900);

  // Indian roads drive on the left: our carriageway is on the left of the median, oncoming on the right.
  var X_US = -2.1, X_THEM = 2.1, EYE_H = 1.2;

  function mat(c, opts) { return new T3.MeshLambertMaterial(Object.assign({ color: c }, opts || {})); }
  function box(w, h, d, m) { return new T3.Mesh(new T3.BoxGeometry(w, h, d), m); }

  // ground and road
  var LEN = 1400;
  var ground = new T3.Mesh(new T3.PlaneGeometry(400, LEN), mat(0x0b0d0c));
  ground.rotation.x = -Math.PI / 2; ground.position.set(0, -0.02, -LEN / 2 + 60); scene.add(ground);
  var asphalt = mat(0x1a1c20);
  [[-4.05, 7.0], [4.05, 7.0]].forEach(function (c) {
    var r = new T3.Mesh(new T3.PlaneGeometry(c[1], LEN), asphalt); r.rotation.x = -Math.PI / 2; r.position.set(c[0], 0, -LEN / 2 + 60); scene.add(r);
  });
  var wetMat = new T3.MeshStandardMaterial({ color: 0x0e1014, roughness: 0.12, metalness: 0.6, transparent: true, opacity: 0 });
  var wet = new T3.Mesh(new T3.PlaneGeometry(15.2, LEN), wetMat); wet.rotation.x = -Math.PI / 2; wet.position.set(0, 0.005, -LEN / 2 + 60); scene.add(wet);

  // lane markings (instanced dashes) and edge lines
  var white = new T3.MeshLambertMaterial({ color: 0xdedfe2, emissive: 0x16171a });
  var dashG = new T3.PlaneGeometry(0.14, 3), dashes = new T3.InstancedMesh(dashG, white, 2 * Math.ceil(LEN / 9)), m4 = new T3.Matrix4(), q = new T3.Quaternion().setFromEuler(new T3.Euler(-Math.PI / 2, 0, 0)), one = new T3.Vector3(1, 1, 1), k = 0;
  for (var z = 50; z > -LEN + 60; z -= 9) {
    [-4.05, 4.05].forEach(function (x) { m4.compose(new T3.Vector3(x, 0.01, z), q, one); dashes.setMatrixAt(k++, m4); });
  }
  dashes.count = k; scene.add(dashes);
  [-7.4, 7.4].forEach(function (x) { var l = new T3.Mesh(new T3.PlaneGeometry(0.15, LEN), white); l.rotation.x = -Math.PI / 2; l.position.set(x, 0.01, -LEN / 2 + 60); scene.add(l); });

  // median: kerb with painted face, and a gap where people cross
  var kerbMat = mat(0x3a3b36), paint = mat(0x8f8a60);
  function kerb(z0, z1) {
    var len = z0 - z1, k1 = box(1.2, 0.28, len, kerbMat); k1.position.set(0, 0.14, (z0 + z1) / 2); scene.add(k1);
    [-0.61, 0.61].forEach(function (x) { var f = box(0.02, 0.26, len, paint); f.position.set(x, 0.14, (z0 + z1) / 2); scene.add(f); });
  }
  var GAP_Z = { a: 0, b: 0 }; // set when the scenario is placed
  var medianGroup = new T3.Group(); scene.add(medianGroup);

  // street lights on the median: dark poles, few working (as on the corridor at night)
  var poleMat = mat(0x2b2e33), lampOn = new T3.MeshBasicMaterial({ color: 0xffb35c }), lampOff = mat(0x22252a);
  var lamps = [];
  for (var zz = 20, i = 0; zz > -LEN + 80; zz -= 42, i++) {
    var p = box(0.14, 9, 0.14, poleMat); p.position.set(0, 4.5, zz); scene.add(p);
    var on = (i % 3 !== 1);
    [-1, 1].forEach(function (s) {
      var arm = box(1.6, 0.08, 0.08, poleMat); arm.position.set(s * 0.8, 8.9, zz); scene.add(arm);
      var head = box(0.5, 0.12, 0.25, on ? lampOn : lampOff); head.position.set(s * 1.55, 8.82, zz); scene.add(head);
      if (on) lamps.push(new T3.Vector3(s * 1.55, 8.7, zz));
    });
  }
  var poolLights = [0, 1, 2].map(function () { var l = new T3.PointLight(0xff9f45, 2.2, 34, 2); scene.add(l); return l; });

  // far skyline: a few lit windows, so the night has depth
  var winMat = new T3.MeshBasicMaterial({ color: 0x8a6a3c });
  for (var b = 0; b < 40; b++) {
    var bx = (b % 2 ? 1 : -1) * (42 + Math.random() * 70), bz = -80 - Math.random() * 700, bh = 6 + Math.random() * 28;
    var bl = box(10 + Math.random() * 14, bh, 10 + Math.random() * 10, mat(0x0c0e12)); bl.position.set(bx, bh / 2, bz); scene.add(bl);
    for (var w = 0; w < 6; w++) { var wi = box(0.9, 0.6, 0.05, winMat); wi.position.set(bx + (Math.random() - 0.5) * 8, 2 + Math.random() * (bh - 3), bz + (bx > 0 ? -6 : 6) * 0 + 5.2); if (Math.random() < 0.6) scene.add(wi); }
  }

  // our headlights: dipped, as the law asks
  scene.add(new T3.AmbientLight(0x2a3346, 0.55));
  var ourBeams = [-0.75, 0.75].map(function (dx) {
    var s = new T3.SpotLight(0xfff3dd, 5.5, 95, 0.38, 0.55, 1.4); s.position.set(dx, 0.75, 0); s.target.position.set(dx * 0.6, 0, -40); scene.add(s); scene.add(s.target); return s;
  });

  // the oncoming car
  var car = new T3.Group();
  var bodyM = mat(0x16181c), glassM = mat(0x0a0c10);
  var body = box(1.8, 0.75, 4.3, bodyM); body.position.y = 0.6; car.add(body);
  var cabin = box(1.6, 0.6, 2.2, glassM); cabin.position.set(0, 1.25, 0.2); car.add(cabin);
  var lampM = new T3.MeshBasicMaterial({ color: 0xffffff });
  var headL = [-0.62, 0.62].map(function (dx) { var h = box(0.32, 0.14, 0.05, lampM); h.position.set(dx, 0.72, 2.16); car.add(h); return h; });
  var carBeam = new T3.SpotLight(0xf4f6ff, 10, 160, 0.3, 0.5, 1.2); carBeam.position.set(0, 0.75, 2.2); car.add(carBeam);
  var carBeamT = new T3.Object3D(); carBeamT.position.set(0, -0.6, 40); car.add(carBeamT); carBeam.target = carBeamT;
  scene.add(car);

  // the person: generic figure, dark clothes, no face, no detail
  var person = new T3.Group();
  var cloth = mat(0x15171b), skin = mat(0x2e241e);
  var torso = new T3.Mesh(new T3.CylinderGeometry(0.2, 0.17, 0.62, 10), cloth); torso.position.y = 1.18; person.add(torso);
  var headM = new T3.Mesh(new T3.SphereGeometry(0.12, 12, 10), skin); headM.position.y = 1.62; person.add(headM);
  var legs = [-0.09, 0.09].map(function (dx) { var l = new T3.Mesh(new T3.CylinderGeometry(0.075, 0.065, 0.86, 8), cloth); l.position.set(dx, 0.43, 0); l.geometry.translate(0, -0.0, 0); person.add(l); return l; });
  var arms = [-0.25, 0.25].map(function (dx) { var a = new T3.Mesh(new T3.CylinderGeometry(0.05, 0.045, 0.6, 8), cloth); a.position.set(dx, 1.15, 0); person.add(a); return a; });
  scene.add(person);
  var ring = new T3.Mesh(new T3.RingGeometry(0.6, 0.72, 40), new T3.MeshBasicMaterial({ color: 0xe8a87c, transparent: true, opacity: 0, side: T3.DoubleSide, depthTest: false }));
  ring.rotation.x = -Math.PI / 2; scene.add(ring);

  // our bonnet, so it feels like a seat, not a camera
  var bonnet = new T3.Mesh(new T3.CircleGeometry(1.05, 48, 0, Math.PI), new T3.MeshBasicMaterial({ color: 0x07080a }));
  bonnet.rotation.x = -1.5; scene.add(bonnet);

  // ---------------- post: the eye ----------------
  var rt = new T3.WebGLRenderTarget(16, 16, { samples: SMALL ? 2 : 4 });
  var NL = 8;
  var post = new T3.ShaderMaterial({
    uniforms: {
      tScene: { value: rt.texture }, tanHalf: { value: new T3.Vector2(1, 1) }, res: { value: new T3.Vector2(1, 1) },
      lDir: { value: Array.from({ length: NL }, function () { return new T3.Vector3(0, 0, -1); }) },
      lE: { value: new Array(NL).fill(0) }, lRefl: { value: new Array(NL).fill(0) },
      ageK: { value: 1 }, pig: { value: P_PIG }, adapt: { value: 0 }, after: { value: new T3.Vector3(0, 0, 0) }, time: { value: 0 }, Lb: { value: 0.6 }
    },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: [
      'precision highp float;',
      'varying vec2 vUv; uniform sampler2D tScene; uniform vec2 tanHalf, res;',
      'uniform vec3 lDir[' + NL + ']; uniform float lE[' + NL + ']; uniform float lRefl[' + NL + '];',
      'uniform float ageK, pig, adapt, time, Lb; uniform vec3 after;',
      // CIE general disability glare equation, theta in degrees: Lveil per lux at the eye
      'float cie(float th){ th = max(th, 0.1); return 10.0/(th*th*th) + (5.0/(th*th) + 0.1*pig/th)*ageK + 0.0025*pig; }',
      'float hash(float n){ return fract(sin(n)*43758.5453); }',
      'void main(){',
      '  vec2 ndc = vUv*2.0-1.0; vec3 ray = normalize(vec3(ndc.x*tanHalf.x, ndc.y*tanHalf.y, -1.0));',
      '  vec3 col = texture2D(tScene, vUv).rgb;',
      '  float Lv = 0.0; vec3 rays = vec3(0.0);',
      '  float asp = res.x/res.y;',
      '  for (int i = 0; i < ' + NL + '; i++) {',
      '    if (lE[i] <= 0.0) continue;',
      '    float th = degrees(acos(clamp(dot(ray, lDir[i]), -1.0, 1.0)));',
      '    Lv += lE[i]*cie(th);',
      // starburst: diffraction-like spikes from the eyelashes and lens, scaled by the light at the eye
      '    vec2 lp = vec2(lDir[i].x/(-lDir[i].z)/tanHalf.x, lDir[i].y/(-lDir[i].z)/tanHalf.y);',
      '    if (lDir[i].z < 0.0) {',
      '      vec2 d = (ndc - lp)*vec2(asp,1.0); float r = length(d); float a = atan(d.y, d.x);',
      '      float sp = pow(abs(cos(a*6.0 + float(i))), 90.0) + 0.5*pow(abs(cos(a*11.0+1.7+float(i))), 160.0) + 0.08*hash(floor(a*64.0)+float(i));',
      '      float len = 0.03 + 0.045*log(1.0 + lE[i]);',
      '      rays += vec3(1.0,0.96,0.88)*sp*exp(-r/len)*pow(min(lE[i],40.0),0.7)*0.06 + vec3(1.0,0.98,0.94)*exp(-r*r/(0.0003+0.00008*lE[i]))*min(lE[i],40.0)*0.05;',
      // ghosts: faint reflections in the windscreen and lens, along the line through the centre
      '      for (int g = 1; g < 4; g++) { vec2 gp = -lp*(0.35*float(g)); float gr = length((ndc-gp)*vec2(asp,1.0)); rays += vec3(0.5,0.7,1.0)*smoothstep(0.04*float(g),0.0,gr)*min(lE[i],40.0)*0.0025; }',
      '    }',
      // wet road: each lamp stretches into a long streak below it
      '    if (lRefl[i] > 0.0 && lDir[i].z < 0.0) { float dx = (ndc.x - lp.x)*asp; float below = lp.y - ndc.y; if (below > 0.0) { float s = exp(-abs(dx)/0.012)*exp(-below/0.55); rays += vec3(1.0,0.93,0.82)*s*lRefl[i]*0.05; Lv += lRefl[i]*s*0.6; } }',
      '  }',
      // the veil: scattered light the eye cannot separate from the scene, compared with what the eye is adapted to
      '  float veil = 1.0 - exp(-Lv/7.0);',
      '  vec3 vcol = mix(vec3(1.0,0.97,0.9), vec3(0.85,0.9,1.0), 0.3);',
      '  col = col*(1.0-0.45*veil) + vcol*veil*0.85 + rays;',
      // photostress: after the light passes the eye stays dazzled; contrast and colour come back slowly
      '  float g = dot(col, vec3(0.299,0.587,0.114)); col = mix(col, vec3(g)*0.55, adapt*0.75);',
      '  if (after.z > 0.0) { float ar = length((ndc-after.xy)*vec2(asp,1.0)); col += vec3(0.32,0.12,0.42)*after.z*exp(-ar*ar/0.012); col *= 1.0 - 0.25*after.z*exp(-ar*ar/0.05); }',
      '  col = col/(1.0+0.15*col);',
      '  float v = smoothstep(1.35, 0.35, length(ndc*vec2(1.0,0.85))); col *= mix(0.55, 1.0, v);',
      '  gl_FragColor = vec4(pow(max(col, 0.0), vec3(1.0/2.2)), 1.0);',
      '}'
    ].join('\n'),
    depthTest: false, depthWrite: false
  });
  var quad = new T3.Mesh(new T3.PlaneGeometry(2, 2), post), postScene = new T3.Scene(), postCam = new T3.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  postScene.add(quad);

  // ---------------- the model ----------------
  function cie(th) { th = Math.max(th, 0.1); return 10 / (th * th * th) + (5 / (th * th) + 0.1 * P_PIG / th) * ageK() + 0.0025 * P_PIG; }
  function ageK() { return 1 + Math.pow(S.age / 62.5, 4); }
  function v() { return S.kmh / 3.6; }
  function stopDist() { return v() * 1.5 + v() * v() / (2 * 7); } // 1.5 s to react, 7 m/s² braking on a dry road
  function recoveryTau() { return 1.2 * (1 + Math.pow(S.age / 55, 3)); } // illustrative: recovery slows with age

  var t = 0, playing = false, last = 0, adapt = 0, afterG = 0, afterPos = new T3.Vector2(), spottedAt = null, spotDist = null, ended = false, peakLv = 0, minVis = 1;
  var zMeet, zPerson, tWalk;

  function place() {
    var vu = v(), vo = 60 / 3.6;
    zMeet = -vu * T_MEET; zPerson = zMeet - GAP_AT_MEET; tWalk = T_MEET - 1.4;
    GAP_Z.a = zPerson + 4; GAP_Z.b = zPerson - 4;
    while (medianGroup.children.length) medianGroup.remove(medianGroup.children[0]);
    // rebuild median with the gap at the crossing point
    scene.children.filter(function (o) { return o.userData.kerb; }).forEach(function (o) { scene.remove(o); });
    var before = scene.children.length;
    kerb(60, GAP_Z.a); kerb(GAP_Z.b, -LEN + 60);
    scene.children.slice(before).forEach(function (o) { o.userData.kerb = true; });
    car.userData.z0 = zMeet - vo * T_MEET; car.userData.vo = vo;
  }

  function personX(tt) { return tt < tWalk ? 0.2 : Math.max(-6.2, 0.2 - 1.3 * (tt - tWalk)); }

  var tmp = new T3.Vector3(), camDirInv = new T3.Matrix4();
  function frame(dt) {
    var vu = v(), zUs = -vu * t;
    cam.position.set(X_US, EYE_H, zUs);
    cam.lookAt(X_US + 0.05, EYE_H - 0.12, zUs - 30);
    cam.updateMatrixWorld();
    bonnet.position.set(X_US, 0.84, zUs - 0.35);
    ourBeams.forEach(function (s, j) { s.position.set(X_US + (j ? 0.75 : -0.75), 0.75, zUs - 1.8); s.target.position.set(X_US + (j ? 0.4 : -0.4), 0, zUs - 42); });
    // nearest working street lights carry the three moving pools
    var ahead = lamps.filter(function (l) { return l.z < zUs + 10 && l.z > zUs - 160; }).slice(0, 3);
    poolLights.forEach(function (pl, j) { var l = ahead[j]; if (l) { pl.position.copy(l); pl.intensity = 2.2; } else pl.intensity = 0; });
    // oncoming car, its beam aimed at us: high stays up, dipped points down and to its left
    var zc = car.userData.z0 + car.userData.vo * t;
    car.position.set(X_THEM, 0, zc);
    var high = S.beam === 'high';
    carBeam.intensity = high ? 14 : 4; carBeamT.position.set(high ? -1.6 : 1.2, high ? 0.6 : -0.8, 40);
    // person: walks out from the median gap into our lane
    var px = personX(t), walking = t >= tWalk && px > -6.2;
    person.position.set(px, 0, zPerson);
    person.rotation.y = Math.PI / 2;
    var sw = walking ? Math.sin(t * 7.5) * 0.45 : 0;
    legs[0].rotation.x = sw; legs[1].rotation.x = -sw; arms[0].rotation.x = -sw * 0.8; arms[1].rotation.x = sw * 0.8;
    ring.position.set(px, 0.03, zPerson);

    // light at the eye from each lamp, and its direction in view space
    var lampsVis = [], Etotal = 0;
    var view = cam.matrixWorldInverse;
    headL.forEach(function (h) {
      h.getWorldPosition(tmp);
      var d = tmp.distanceTo(cam.position), behind = tmp.z > cam.position.z - 1;
      var E = behind ? 0 : 2 * I_LAMP[S.beam] / 2 / (d * d); // each lamp: I/d²
      lampsVis.push({ p: tmp.clone(), E: E });
    });
    ahead.forEach(function (l) { var d = l.distanceTo(cam.position); lampsVis.push({ p: l.clone(), E: 220 / (d * d), street: true }); });
    var U = post.uniforms;
    for (var j = 0; j < NL; j++) {
      var L = lampsVis[j];
      if (!L) { U.lE.value[j] = 0; U.lRefl.value[j] = 0; continue; }
      U.lDir.value[j].copy(L.p).applyMatrix4(view).normalize();
      U.lE.value[j] = L.E; U.lRefl.value[j] = S.wet && !L.street ? L.E * 0.8 : (S.wet ? L.E * 0.3 : 0);
      if (!L.street) Etotal += L.E;
    }
    // what the person looks like through the veil
    tmp.set(px, 1.1, zPerson);
    var toP = tmp.clone().sub(cam.position), dP = toP.length(); toP.normalize();
    var Lv = 0;
    lampsVis.forEach(function (L) { if (L.street) return; var toL = L.p.clone().sub(cam.position).normalize(); var th = T3.MathUtils.radToDeg(Math.acos(Math.min(1, Math.max(-1, toL.dot(toP))))); Lv += L.E * cie(th) * (S.wet && !L.street ? 1.25 : 1); });
    var Lb = Math.min(2.0, Math.max(0.08, 1.6 * Math.pow(18 / Math.max(dP, 5), 2))) + (ahead.length ? 0.15 : 0);
    var Lo = Lb * 0.35, C0 = Math.abs(Lo - Lb) / Lb, C = Math.abs(Lo - Lb) / (Lb + Lv);
    var vis = Math.max(0, Math.min(1, C / C0)) * (1 - 0.7 * adapt);
    if (t > tWalk - 0.5) { minVis = Math.min(minVis, vis); peakLv = Math.max(peakLv, Lv); }
    // photostress: the dazzle builds while the light is in the eye and fades with age-dependent slowness
    var target = Math.min(1, Etotal / 18);
    adapt = target > adapt ? adapt + (target - adapt) * Math.min(1, dt * 3) : adapt * Math.exp(-dt / recoveryTau());
    if (Etotal > 4) { var hp = lampsVis[0].p.clone().project(cam); afterPos.set(hp.x, hp.y); afterG = Math.min(1, afterG + dt * 0.9); } else afterG *= Math.exp(-dt / (recoveryTau() * 1.4));
    U.adapt.value = adapt; U.after.value.set(afterPos.x, afterPos.y, afterG * 0.9); U.ageK.value = ageK(); U.Lb.value = 0.6 + (ahead.length ? 0.2 : 0); U.time.value = t;

    // HUD
    var onRoad = t >= tWalk;
    $('h-vis').textContent = onRoad ? Math.round(vis * 100) + '%' : 'Not on the road yet';
    $('h-visbar').style.setProperty('--v', (onRoad ? vis * 100 : 100).toFixed(0) + '%');
    $('h-veil').textContent = Lv < 0.05 ? '0' : Lv < 10 ? Lv.toFixed(1) : Math.round(Lv);
    $('h-car').textContent = Math.max(0, Math.round(-(zc - zUs))) + ' m';
    $('h-dist').textContent = Math.max(0, Math.round(-(zPerson - zUs))) + ' m';
    $('h-spd').textContent = S.kmh;
    ring.material.opacity = ended ? 0.9 : 0;

    var distToPerson = -(zPerson - zUs);
    if (!ended && (distToPerson < stopDist() * 0.42 || distToPerson < 9)) end(distToPerson);
  }

  function render() {
    var w = host.clientWidth, h = host.clientHeight;
    if (R.domElement.width !== Math.round(w * R.getPixelRatio()) || R.domElement.height !== Math.round(h * R.getPixelRatio())) {
      R.setSize(w, h, false); rt.setSize(Math.round(w * R.getPixelRatio()), Math.round(h * R.getPixelRatio()));
      cam.aspect = w / h; cam.updateProjectionMatrix();
    }
    post.uniforms.tanHalf.value.set(Math.tan(T3.MathUtils.degToRad(FOV / 2)) * cam.aspect, Math.tan(T3.MathUtils.degToRad(FOV / 2)));
    post.uniforms.res.value.set(w, h);
    R.setRenderTarget(rt); R.render(scene, cam); R.setRenderTarget(null); R.render(postScene, postCam);
  }

  function loop(now) {
    var dt = Math.min(0.05, (now - last) / 1000 || 0); last = now;
    if (playing) t += dt;
    frame(playing ? dt : 0.016);
    render();
    requestAnimationFrame(loop);
  }

  // ---------------- the story ----------------
  function reset() {
    place(); t = 0; adapt = 0; afterG = 0; spottedAt = null; spotDist = null; ended = false; peakLv = 0; minVis = 1;
    $('result').hidden = true; $('spot').disabled = false; $('spot').textContent = 'I see someone';
    host.classList.remove('done');
  }
  function play() { reset(); playing = true; $('play').textContent = 'Restart'; host.focus({ preventScroll: true }); }
  function end(d) {
    ended = true; playing = false; host.classList.add('done');
    var sd = stopDist(), msg;
    if (spotDist == null) msg = 'You did not see them. They were in your lane, ' + Math.round(d) + ' m ahead, when the frame froze.';
    else msg = 'You saw them at ' + Math.round(spotDist) + ' m.';
    var need = 'At ' + S.kmh + ' km/h a driver needs about ' + Math.round(sd) + ' m to stop: ' + Math.round(v() * 1.5) + ' m to react and ' + Math.round(sd - v() * 1.5) + ' m to brake.';
    var verdict = spotDist == null ? 'No time to stop.' : spotDist >= sd ? 'Enough room to stop.' : 'Not enough room to stop: ' + Math.round(sd - spotDist) + ' m short.';
    $('r-head').textContent = verdict;
    $('r-body').textContent = msg + ' ' + need;
    $('r-glare').textContent = 'At its worst the oncoming ' + (S.beam === 'high' ? 'high beam' : 'dipped beam') + ' cut what you could see of the person to ' + Math.round(minVis * 100) + '% of normal. After it passed, your eyes took roughly ' + (recoveryTau() * 3).toFixed(0) + ' s to come back (a simplified model): about ' + Math.round(v() * recoveryTau() * 3) + ' m driven half-blind.';
    $('r-again').textContent = S.beam === 'high' ? 'Try again: oncoming car on dipped beam' : 'Try again: oncoming car on high beam';
    $('result').hidden = false; $('spot').disabled = true;
  }
  $('play').addEventListener('click', play);
  $('spot').addEventListener('click', function () {
    if (!playing || spottedAt != null) return;
    spottedAt = t; spotDist = -(zPerson + v() * t);
    if (t < tWalk - 0.2) { $('spot').textContent = 'No one on the road yet. Keep looking'; spottedAt = null; spotDist = null; return; }
    $('spot').textContent = 'Seen at ' + Math.round(spotDist) + ' m'; $('spot').disabled = true;
  });
  host.addEventListener('keydown', function (e) { if (e.code === 'Space') { e.preventDefault(); $('spot').click(); } });
  $('r-again').addEventListener('click', function () { setBeam(S.beam === 'high' ? 'low' : 'high'); play(); });

  function seg(id, key, parse, after) {
    [].forEach.call(document.querySelectorAll('#' + id + ' button'), function (b) {
      b.addEventListener('click', function () {
        S[key] = parse(b.dataset.v);
        [].forEach.call(document.querySelectorAll('#' + id + ' button'), function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        if (after) after();
      });
    });
  }
  function setBeam(bv) { S.beam = bv; [].forEach.call(document.querySelectorAll('#c-beam button'), function (x) { x.setAttribute('aria-pressed', x.dataset.v === bv ? 'true' : 'false'); }); }
  seg('c-beam', 'beam', String);
  seg('c-age', 'age', Number);
  seg('c-speed', 'kmh', Number, function () { if (!playing) reset(); });
  seg('c-road', 'wet', function (x) { return x === 'wet'; }, function () { wetMat.opacity = S.wet ? 0.55 : 0; });

  var qs = new URLSearchParams(location.search), qt = parseFloat(qs.get('t'));
  if (isFinite(qt)) { if (qs.get('beam')) setBeam(qs.get('beam')); if (qs.get('age')) S.age = +qs.get('age'); if (qs.get('wet')) { S.wet = true; wetMat.opacity = 0.55; } reset(); for (var st = 0; st <= qt; st += 0.02) { t = st; frame(0.02); } requestAnimationFrame(function () { (function hold() { frame(0.0); render(); requestAnimationFrame(hold); })(); }); return; }
  // start: a still frame of the moment of worst glare, so the first view already tells the story
  reset();
  t = T_MEET - 0.9; frame(0.016); t = RM ? T_MEET - 0.9 : 0;
  if (RM) { $('play').textContent = 'Play'; }
  requestAnimationFrame(function (n) { last = n; loop(n); });
  if (!RM) { t = T_MEET - 0.9; }
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-90b96dfc9f57");
