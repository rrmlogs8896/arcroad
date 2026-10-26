/* arcroad M2 access to hospitals — staging preview with an INVENTED sample area.
 * No network, no storage. The sample is a small made-up model: one divided road
 * crossable at two openings, hospitals on both sides, streets ~30% longer than a
 * straight line. It shows how the measure will read; it measures nothing.
 */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  if (new URLSearchParams(location.search).get('m2') !== '1') { $('off').hidden = false; return; }
  ['lede', 'map', 'sum', 'how'].forEach(function (id) { $(id).hidden = false; });

  var NS = 'http://www.w3.org/2000/svg';
  var CELL = 250, COLS = 14, ROWS = 9, ROAD_Y = 1000, STREET = 1.3;
  var OPENINGS = [{ x: 500, y: ROAD_Y }, { x: 3000, y: ROAD_Y }];
  var GAPS = { r0c0: 1, r8c13: 1, r7c0: 1 };
  var HOSP = {
    government: [{ id: 'G1', name: 'Sample Area Hospital', x: 1750, y: 1600 }, { id: 'G2', name: 'Sample Community Health Centre', x: 3250, y: 2000 }],
    private: [{ id: 'P1', name: 'Sample Private Hospital A', x: 1000, y: 500 }, { id: 'P2', name: 'Sample Private Hospital B', x: 2600, y: 1900 }]
  };
  var BANDS = [
    { lo: 0, hi: 500, c: 'var(--b0)', label: 'under 500 m' },
    { lo: 500, hi: 1000, c: 'var(--b1)', label: '500 m – 1 km' },
    { lo: 1000, hi: 2000, c: 'var(--b2)', label: '1 – 2 km' },
    { lo: 2000, hi: 5000, c: 'var(--b3)', label: '2 – 5 km' },
    { lo: 5000, hi: Infinity, c: 'var(--b4)', label: '5 km or more' }
  ];

  function d(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
  function side(p) { return p.y < ROAD_Y ? 0 : 1; }
  function route(c, h) {
    if (side(c) === side(h)) return { m: STREET * d(c, h), via: null };
    var best = null;
    OPENINGS.forEach(function (o) {
      var m = STREET * (d(c, o) + d(o, h));
      if (!best || m < best.m) best = { m: m, via: o };
    });
    return best;
  }
  function fmt(m) {
    if (m == null) return '—';
    var r = Math.round(m / 10) * 10;
    return r < 1000 ? r + ' m' : (Math.round(r / 100) / 10).toFixed(1) + ' km';
  }
  function people(n) { return Math.round(n).toLocaleString('en-IN'); }

  // Seeded population so the sample is the same on every load.
  var seed = 7;
  function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  var cells = [];
  for (var r = 0; r < ROWS; r++) for (var c = 0; c < COLS; c++) {
    var pop = rnd() < 0.08 ? 0 : Math.round(80 + rnd() * 820);
    cells.push({ id: 'r' + r + 'c' + c, r: r, c: c, x: (c + 0.5) * CELL, y: (r + 0.5) * CELL, pop: pop });
  }

  function measure(cell, layer) {
    if (GAPS[cell.id]) return { status: 'gap' };
    if (!cell.pop) return { status: 'empty' };
    var hs = HOSP[layer], line = null, road = null;
    hs.forEach(function (h) {
      var s = d(cell, h); if (!line || s < line.m) line = { h: h, m: s };
      var rt = route(cell, h); if (!road || rt.m < road.m) road = { h: h, m: rt.m, via: rt.via };
    });
    var straight = d(cell, road.h);
    return { status: 'measured', line: line, road: road, straight: straight, extra: Math.max(0, road.m - line.m) };
  }
  function band(x) { for (var i = 0; i < BANDS.length; i++) if (x < BANDS[i].hi) return BANDS[i]; return BANDS[BANDS.length - 1]; }

  var layer = 'government', sel = 'r2c7';
  var svg = $('svg');
  function el(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    (parent || svg).appendChild(e); return e;
  }

  // Hatch for squares the road map cannot reach.
  var defs = el('defs', {});
  var pat = el('pattern', { id: 'hatch', width: 40, height: 40, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
  el('rect', { width: 40, height: 40, fill: '#0F1216' }, pat);
  el('line', { x1: 0, y1: 0, x2: 0, y2: 40, stroke: '#2A3038', 'stroke-width': 12 }, pat);

  var cellG = el('g', {}), roadG = el('g', {}), routeG = el('g', {}), hospG = el('g', {});
  var rects = {};
  cells.forEach(function (cell) {
    var rect = el('rect', { x: cell.c * CELL + 6, y: cell.r * CELL + 6, width: CELL - 12, height: CELL - 12, rx: 18, class: 'cell' }, cellG);
    rect.addEventListener('click', function () { sel = cell.id; render(); });
    rects[cell.id] = rect;
  });

  // The divided road: two carriageways, a median broken only at the openings.
  el('rect', { x: 0, y: ROAD_Y - 34, width: 3500, height: 68, fill: '#262B33' }, roadG);
  var cuts = [0].concat(OPENINGS.map(function (o) { return o.x; })).concat([3500]);
  for (var i = 0; i < cuts.length - 1; i++) {
    var a = cuts[i] + (i === 0 ? 0 : 60), b = cuts[i + 1] - (i === cuts.length - 2 ? 0 : 60);
    el('line', { x1: a, y1: ROAD_Y, x2: b, y2: ROAD_Y, stroke: '#8B939C', 'stroke-width': 10 }, roadG);
  }
  OPENINGS.forEach(function (o) {
    var t = el('text', { x: o.x, y: ROAD_Y + 100, 'text-anchor': 'middle', fill: '#8B939C', 'font-size': 64, 'font-family': 'Inter, sans-serif' }, roadG);
    t.textContent = 'opening';
  });

  function drawHospitals() {
    hospG.textContent = '';
    ['private', 'government'].forEach(function (L) {
      var on = L === layer;
      HOSP[L].forEach(function (h) {
        var g = el('g', { opacity: on ? 1 : 0.28 }, hospG);
        el('circle', { cx: h.x, cy: h.y, r: 78, fill: '#0B0D10', stroke: on ? '#F5F6F7' : '#8B939C', 'stroke-width': 10 }, g);
        el('path', { d: 'M' + (h.x - 34) + ' ' + h.y + 'h68M' + h.x + ' ' + (h.y - 34) + 'v68', stroke: on ? '#F5F6F7' : '#8B939C', 'stroke-width': 16, 'stroke-linecap': 'round' }, g);
      });
    });
  }

  function render() {
    var rows = cells.map(function (cell) { return { cell: cell, m: measure(cell, layer) }; });
    rows.forEach(function (x) {
      var rect = rects[x.cell.id];
      var fill = x.m.status === 'measured' ? band(x.m.extra).c : x.m.status === 'gap' ? 'url(#hatch)' : '#0F1216';
      rect.setAttribute('fill', fill);
      rect.setAttribute('stroke', x.cell.id === sel ? '#F5F6F7' : 'none');
      rect.setAttribute('stroke-width', x.cell.id === sel ? 14 : 0);
    });
    drawHospitals();

    var cur = rows.find(function (x) { return x.cell.id === sel; });
    routeG.textContent = '';
    var m = cur.m;
    if (m.status === 'measured') {
      var h = m.road.h, pts = [cur.cell];
      if (m.road.via) pts.push(m.road.via);
      pts.push(h);
      el('polyline', { points: pts.map(function (p) { return p.x + ',' + p.y; }).join(' '), fill: 'none', stroke: '#F5F6F7', 'stroke-width': 12, 'stroke-linejoin': 'round', 'stroke-dasharray': '1 26', 'stroke-linecap': 'round' }, routeG);
      el('line', { x1: cur.cell.x, y1: cur.cell.y, x2: m.line.h.x, y2: m.line.h.y, stroke: '#F0C2A0', 'stroke-width': 6, opacity: 0.8 }, routeG);
      $('h-line').textContent = fmt(m.line.m) + ' on the map.';
      $('h-road').textContent = fmt(m.road.m) + ' by road.';
      var kind = layer === 'government' ? 'government' : 'private';
      $('h-where').textContent = m.line.h.id === h.id
        ? 'From this square, the nearest ' + kind + ' hospital is ' + h.name + '. The road has to go round the median to reach it.'
        : 'From this square, ' + m.line.h.name + ' looks nearest, but it is ' + fmt(route(cur.cell, m.line.h).m) +
          ' away by road. The nearest ' + kind + ' hospital you can actually drive to is ' + h.name + '.';
      $('f-line').textContent = fmt(m.line.m);
      $('f-road').textContent = fmt(m.road.m);
      $('f-extra').textContent = fmt(m.extra);
    } else {
      $('h-line').textContent = m.status === 'gap' ? 'No road on the map.' : 'No one lives here.';
      $('h-road').textContent = m.status === 'gap' ? 'Not measured.' : 'Not measured.';
      $('h-where').textContent = m.status === 'gap'
        ? 'The open map has no drivable road near this square, so it is counted as a gap and checked, never given a figure.'
        : 'The population estimate puts no one in this square, so it is left out of the people counts.';
      $('f-line').textContent = '—'; $('f-road').textContent = '—'; $('f-extra').textContent = '—';
    }
    $('f-pop').textContent = cur.cell.pop ? '~' + people(cur.cell.pop) : '0';
    $('l-gov').setAttribute('aria-pressed', String(layer === 'government'));
    $('l-pri').setAttribute('aria-pressed', String(layer === 'private'));
    summary(rows);
  }

  function summary(rows) {
    var meas = rows.filter(function (x) { return x.m.status === 'measured'; });
    var gapPop = rows.filter(function (x) { return x.m.status === 'gap'; }).reduce(function (s, x) { return s + x.cell.pop; }, 0);
    var total = meas.reduce(function (s, x) { return s + x.cell.pop; }, 0);
    var pairs = meas.map(function (x) { return [x.m.extra, x.cell.pop]; }).sort(function (a, b) { return a[0] - b[0]; });
    var acc = 0, med = null;
    for (var i = 0; i < pairs.length; i++) { acc += pairs[i][1]; if (acc >= total / 2) { med = pairs[i][0]; break; } }
    $('t-pop').textContent = people(total);
    $('t-pop-s').textContent = people(gapPop) + ' more live in squares the map cannot reach by road';
    $('t-med').textContent = fmt(med);
    var ge2 = pairs.filter(function (p) { return p[0] >= 2000; }).reduce(function (s, p) { return s + p[1]; }, 0);
    $('t-2k').textContent = Math.round(100 * ge2 / total) + '%';
    var bars = $('bars'); bars.textContent = '';
    BANDS.forEach(function (b) {
      var w = pairs.filter(function (p) { return p[0] >= b.lo && p[0] < b.hi; }).reduce(function (s, p) { return s + p[1]; }, 0);
      var pc = Math.round(100 * w / total);
      var row = document.createElement('div'); row.className = 'bar';
      var l = document.createElement('span'); l.textContent = b.label;
      var t = document.createElement('span'); t.className = 't';
      var f = document.createElement('span'); f.className = 'f'; f.style.width = pc + '%'; f.style.display = 'block'; t.appendChild(f);
      var p = document.createElement('span'); p.className = 'p m'; p.textContent = pc + '%';
      row.appendChild(l); row.appendChild(t); row.appendChild(p); bars.appendChild(row);
    });
  }

  var lg = $('legend');
  BANDS.forEach(function (b) {
    var s = document.createElement('span'); var sw = document.createElement('i'); sw.className = 'sw'; sw.style.background = b.c;
    s.appendChild(sw); s.appendChild(document.createTextNode(b.label)); lg.appendChild(s);
  });
  var g = document.createElement('span'); var gs = document.createElement('i'); gs.className = 'sw';
  gs.style.background = 'repeating-linear-gradient(45deg,#2A3038 0 3px,#0F1216 3px 7px)';
  g.appendChild(gs); g.appendChild(document.createTextNode('no road on the map')); lg.appendChild(g);

  $('l-gov').addEventListener('click', function () { layer = 'government'; render(); });
  $('l-pri').addEventListener('click', function () { layer = 'private'; render(); });
  svg.addEventListener('keydown', function (e) {
    var cur = cells.find(function (x) { return x.id === sel; });
    var r = cur.r, c = cur.c;
    if (e.key === 'ArrowUp') r = Math.max(0, r - 1);
    else if (e.key === 'ArrowDown') r = Math.min(ROWS - 1, r + 1);
    else if (e.key === 'ArrowLeft') c = Math.max(0, c - 1);
    else if (e.key === 'ArrowRight') c = Math.min(COLS - 1, c + 1);
    else return;
    e.preventDefault(); sel = 'r' + r + 'c' + c; render();
  });
  render();
})();
