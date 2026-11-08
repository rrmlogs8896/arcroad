// arcroad globe: orbit to street, built on MapLibre GL (BSD-3) with OpenFreeMap vector tiles (OpenStreetMap data).
// No Google data, no API keys, no cookies. Every road distance shown is a model value (a candidate) until a drive confirms it.
import * as maplibregl from './vendor/maplibre/maplibre-gl.mjs';

const RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
const STYLE_URL = 'https://tiles.openfreemap.org/styles/dark';
const $ = (id) => document.getElementById(id);
const km = (m) => (m == null ? null : m >= 1000 ? (m / 1000).toFixed(1) + ' km' : Math.round(m) + ' m');

const FALLBACK = {
  version: 8,
  sources: { world: { type: 'geojson', data: 'data/world-in.geojson', attribution: 'Natural Earth (public domain), India point of view' } },
  layers: [
    { id: 'bg', type: 'background', paint: { 'background-color': '#0B0D10' } },
    { id: 'land', type: 'fill', source: 'world', paint: { 'fill-color': '#171C23' } },
    { id: 'coast', type: 'line', source: 'world', paint: { 'line-color': '#2A3038', 'line-width': 0.6 } },
    { id: 'india-edge', type: 'line', source: 'world', filter: ['==', ['get', 'iso'], 'IND'], paint: { 'line-color': '#8B939C', 'line-width': 1 } }
  ]
};

// Whole globe in view: its diameter is about 512·2^zoom/π px, so fit it to 80% of the shorter side.
function startZoom() { const d = 0.8 * Math.min(window.innerWidth, window.innerHeight); return Math.max(0.3, Math.min(2.4, Math.log2(d * Math.PI / 512))); }
let DATA = null, spinOn = !RM, userBusy = false, touring = false, styleOk = false, usingFallback = false;

const map = new maplibregl.Map({
  container: 'map',
  style: STYLE_URL,
  center: [78.9, 21],
  zoom: startZoom(),
  pitch: 0,
  maxPitch: 70,
  attributionControl: { compact: true },
  canvasContextAttributes: { antialias: true }
});
map.addControl(new maplibregl.NavigationControl({ visualizePitch: true, showCompass: true }), 'bottom-right');

const fallbackTimer = setTimeout(() => { if (!styleOk) useFallback(); }, 10000);
map.on('error', (e) => { if (!styleOk && !usingFallback) useFallback(); else console.warn('map:', e && e.error && e.error.message); });

function useFallback() {
  usingFallback = true;
  $('status').textContent = 'The detailed map could not load, so this shows simple outlines. Street-level 3D needs the detailed map.';
  requestAnimationFrame(layoutPhone);
  map.setStyle(FALLBACK);
}

map.on('style.load', async () => {
  styleOk = true; clearTimeout(fallbackTimer);
  try { map.setProjection({ type: 'globe' }); } catch (e) { /* older renderer: stays flat */ }
  try {
    map.setSky({ 'sky-color': '#0B0D10', 'horizon-color': '#1E2B3C', 'fog-color': '#0B0D10', 'sky-horizon-blend': 0.6, 'horizon-fog-blend': 0.5, 'fog-ground-blend': 0.6, 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 0.28, 5, 0.15, 8, 0] });
  } catch (e) { /* sky not supported */ }
  restyle();
  indiaBorders();
  add3dBuildings();
  if (!DATA) DATA = await fetch('data/places.json').then((r) => r.json());
  addOurLayers();
  buildList();
  const want = new URLSearchParams(location.search).get('spot');
  if (want && DATA.spots.some((s) => s.id === want)) { spinOn = false; $('spin').setAttribute('aria-pressed', 'false'); $('spin').textContent = 'Turning: off'; setTimeout(() => selectSpot(want), 600); }
  else setTimeout(spinStep, 4000);
});

// arcroad's own map look: our palette and label hierarchy, English names, fewer labels as you zoom out.
const PAL = { land: '#161B22', water: '#0B1118', town: '#1A1F27', green: '#17201D' };
const EN = ['coalesce', ['get', 'name:en'], ['get', 'name:latin'], ['get', 'name']];
const LABEL_RULES = {
  place_other: { minzoom: 15, color: '#7D858E' }, place_suburb: { minzoom: 13, color: '#7D858E' },
  place_village: { minzoom: 12, color: '#7D858E' }, place_town: { minzoom: 9, color: '#8B939C' },
  place_city: { minzoom: 6, color: '#C9CED4' }, place_city_large: { minzoom: 4, color: '#E6E8EB' },
  place_country_other: { minzoom: 3, color: '#AEB4BB' }, place_country_minor: { minzoom: 2.6, color: '#AEB4BB' }, place_country_major: { minzoom: 1.6, color: '#C9CED4' },   // B: at whole-globe zoom on phones, labels near the limb were drawn outside the sphere
  water_name: { color: '#4E6A85' }, highway_name_other: { color: '#7C858F' }
};
function restyle() {
  const set = (fn) => { try { fn(); } catch (e) { /* property not on this layer */ } };
  for (const l of map.getStyle().layers) {
    if (l.type === 'background') set(() => map.setPaintProperty(l.id, 'background-color', PAL.land));
    else if (l.type === 'fill' && l['source-layer'] === 'water') set(() => map.setPaintProperty(l.id, 'fill-color', PAL.water));
    else if (l.id === 'landuse_residential') set(() => map.setPaintProperty(l.id, 'fill-color', PAL.town));
    else if (l.id === 'landuse_park' || l.id === 'landcover_wood') set(() => map.setPaintProperty(l.id, 'fill-color', PAL.green));
    else if (l.id === 'building') set(() => map.setLayerZoomRange(l.id, 12, 14));   // flat footprints only until the 3D buildings take over
    if (l.type === 'symbol') {
      const tf = l.layout && l.layout['text-field'];
      if (Array.isArray(tf) && tf[0] === 'case') set(() => map.setLayoutProperty(l.id, 'text-field', EN));
      const r = LABEL_RULES[l.id];
      if (r) {
        if (r.minzoom != null) set(() => map.setLayerZoomRange(l.id, r.minzoom, l.maxzoom == null ? 24 : l.maxzoom));
        set(() => map.setPaintProperty(l.id, 'text-color', r.color));
        set(() => map.setPaintProperty(l.id, 'text-halo-color', 'rgba(11,13,16,0.9)'));
        if (/^place_(other|suburb|village|town|city)$/.test(l.id)) set(() => map.setLayoutProperty(l.id, 'text-transform', 'none'));
      }
    }
  }
}

// India's borders as officially depicted by India (Jammu and Kashmir and Ladakh in full), shown to every visitor.
// The tile map's own country lines follow international de facto data, so they are hidden everywhere and replaced
// with Natural Earth's India point-of-view boundaries. State-level region labels are hidden for the same reason.
function indiaBorders() {
  if (usingFallback) return;
  for (const l of map.getStyle().layers) {
    const isBoundary = l['source-layer'] === 'boundary' || /boundary|admin|border/i.test(l.id);
    const isRegionLabel = l.type === 'symbol' && /state|province|region/i.test(l.id);
    if (isBoundary || isRegionLabel) { try { map.setLayoutProperty(l.id, 'visibility', 'none'); } catch (e) { /* ignore */ } }
  }
  if (!map.getSource('arc-world')) map.addSource('arc-world', { type: 'geojson', data: 'data/world-in.geojson', attribution: 'Borders: Natural Earth (public domain), India point of view' });
  if (!map.getLayer('arc-borders')) map.addLayer({ id: 'arc-borders', type: 'line', source: 'arc-world', maxzoom: 9, paint: { 'line-color': '#3A424E', 'line-width': ['interpolate', ['linear'], ['zoom'], 1, 0.5, 6, 1] } }, firstSymbolId());
  if (!map.getLayer('arc-india')) map.addLayer({ id: 'arc-india', type: 'line', source: 'arc-world', maxzoom: 9, filter: ['==', ['get', 'iso'], 'IND'], paint: { 'line-color': '#8B939C', 'line-width': ['interpolate', ['linear'], ['zoom'], 1, 0.8, 6, 1.6] } }, firstSymbolId());
}

function firstSymbolId() {
  const s = map.getStyle().layers.find((l) => l.type === 'symbol');
  return s ? s.id : undefined;
}

function add3dBuildings() {
  if (usingFallback || !map.getSource('openmaptiles') || map.getLayer('arc-3d')) return;
  // Buildings rise as you come in to street level: stylised, not satellite.
  map.addLayer({
    id: 'arc-3d', type: 'fill-extrusion', source: 'openmaptiles', 'source-layer': 'building', minzoom: 14,
    paint: {
      'fill-extrusion-color': ['interpolate', ['linear'], ['coalesce', ['get', 'render_height'], 6], 0, '#1C2129', 30, '#2A313B', 90, '#3A424E'],
      'fill-extrusion-height': ['interpolate', ['linear'], ['zoom'], 14, 0, 15.2, ['coalesce', ['get', 'render_height'], 6]],
      'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
      'fill-extrusion-opacity': 0.92
    }
  }, firstSymbolId());
}

function textFont() {
  const s = map.getStyle().layers.find((l) => l.type === 'symbol' && l.layout && l.layout['text-font']);
  return s ? s.layout['text-font'] : null;
}

function addOurLayers() {
  if (map.getSource('arc-cities')) return;
  const cities = { type: 'FeatureCollection', features: DATA.cities.map((c) => ({ type: 'Feature', properties: { id: c.id, name: c.name }, geometry: { type: 'Point', coordinates: c.c } })) };
  const spotsA = { type: 'FeatureCollection', features: DATA.spots.map((s) => ({ type: 'Feature', properties: { id: s.id }, geometry: { type: 'Point', coordinates: s.a } })) };
  const spotsB = { type: 'FeatureCollection', features: DATA.spots.map((s) => ({ type: 'Feature', properties: { id: s.id }, geometry: { type: 'Point', coordinates: s.b } })) };
  const lines = { type: 'FeatureCollection', features: DATA.spots.map((s) => ({ type: 'Feature', properties: { id: s.id }, geometry: { type: 'LineString', coordinates: [s.a, s.b] } })) };
  map.addSource('arc-cities', { type: 'geojson', data: cities });
  map.addSource('arc-a', { type: 'geojson', data: spotsA });
  map.addSource('arc-b', { type: 'geojson', data: spotsB });
  map.addSource('arc-line', { type: 'geojson', data: lines });

  map.addLayer({ id: 'city-halo', type: 'circle', source: 'arc-cities', maxzoom: 9.5, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 6, 6, 12], 'circle-color': '#E2743B', 'circle-opacity': 0.18 } });
  map.addLayer({ id: 'city-dot', type: 'circle', source: 'arc-cities', maxzoom: 9.5, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 2.6, 6, 5], 'circle-color': '#E2743B', 'circle-stroke-color': '#0B0D10', 'circle-stroke-width': 1 } });
  const font = textFont();
  if (font && map.getStyle().glyphs) {
    map.addLayer({ id: 'city-label', type: 'symbol', source: 'arc-cities', minzoom: 3.6, maxzoom: 9.5,
      layout: { 'text-field': ['get', 'name'], 'text-font': font, 'text-size': 12, 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true },
      paint: { 'text-color': '#E6E8EB', 'text-halo-color': '#0B0D10', 'text-halo-width': 1.4 } });
  }
  map.addLayer({ id: 'spot-line', type: 'line', source: 'arc-line', minzoom: 13, paint: { 'line-color': '#F5F6F7', 'line-width': 2, 'line-dasharray': [1.5, 1.5] } });
  map.addLayer({ id: 'spot-b', type: 'circle', source: 'arc-b', minzoom: 13, paint: { 'circle-radius': 4, 'circle-color': '#F0C2A0' } });
  map.addLayer({ id: 'spot-ring', type: 'circle', source: 'arc-a', minzoom: 8,
    paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 3, 13, 7, 17, 11], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#F0C2A0', 'circle-stroke-width': 2 } });

  map.addSource('arc-pulse', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({ id: 'spot-pulse', type: 'circle', source: 'arc-pulse', minzoom: 12,
    paint: { 'circle-radius': 12, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#F0C2A0', 'circle-stroke-width': 1.5, 'circle-stroke-opacity': 0.6, 'circle-pitch-alignment': 'map' } }, 'spot-ring');

  for (const id of ['city-dot', 'spot-ring']) {
    map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; });
  }
  map.on('click', 'city-dot', (e) => selectCity(e.features[0].properties.id));
  map.on('click', 'spot-ring', (e) => selectSpot(e.features[0].properties.id));
}

// ---- the selected place breathes: a ring that slowly expands and fades, and the straight-across line flows ----
let pulseRaf = null;
const DASH = [[0, 1.5, 1.5], [0.5, 1.5, 1], [1, 1.5, 0.5], [1.5, 1.5, 0]];
function startPulse(s) {
  stopPulse();
  if (RM || !map.getSource('arc-pulse')) return;
  map.getSource('arc-pulse').setData({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: s.a } }] });
  map.setFilter('spot-line', ['==', ['get', 'id'], s.id]);
  const t0 = performance.now();
  let lastStep = -1;
  const tick = (t) => {
    const k = ((t - t0) % 2400) / 2400;                       // one breath every 2.4 s
    map.setPaintProperty('spot-pulse', 'circle-radius', 10 + 26 * k);
    map.setPaintProperty('spot-pulse', 'circle-stroke-opacity', 0.65 * (1 - k));
    const step = Math.floor((t - t0) / 120) % DASH.length;     // dashes march from one side to the other
    if (step !== lastStep) { lastStep = step; const d = DASH[step]; map.setPaintProperty('spot-line', 'line-dasharray', d[0] === 0 ? [d[1], d[2]] : [d[0], d[1], d[2], d[1] - d[0] + 0.0001]); }
    pulseRaf = requestAnimationFrame(tick);
  };
  pulseRaf = requestAnimationFrame(tick);
}
function stopPulse() {
  if (pulseRaf) cancelAnimationFrame(pulseRaf); pulseRaf = null;
  if (map.getSource('arc-pulse')) map.getSource('arc-pulse').setData({ type: 'FeatureCollection', features: [] });
  if (map.getLayer('spot-line')) { map.setFilter('spot-line', null); map.setPaintProperty('spot-line', 'line-dasharray', [1.5, 1.5]); }
}

// ---- motion ----
function fly(opts) {
  return new Promise((resolve) => {
    if (RM) { map.jumpTo(opts); resolve(); return; }
    map.once('moveend', () => resolve());
    map.flyTo({ ...opts, essential: false, speed: 0.9, curve: 1.5 });
  });
}

function spinStep() {
  if (!spinOn || RM || userBusy || touring || map.getZoom() > 3.5) return;
  const c = map.getCenter();
  map.easeTo({ center: [c.lng - 4, c.lat], duration: 1000, easing: (n) => n });
}
map.on('moveend', () => { if (!touring) spinStep(); });
for (const ev of ['mousedown', 'touchstart', 'wheel', 'dragstart']) {
  map.on(ev, () => { userBusy = true; touring = false; });
}
map.on('mouseup', () => { userBusy = false; });
map.on('touchend', () => { userBusy = false; });

$('spin').setAttribute('aria-pressed', String(spinOn));
$('spin').textContent = spinOn ? 'Turning: on' : 'Turning: off';
$('spin').addEventListener('click', function () {
  spinOn = !spinOn; this.setAttribute('aria-pressed', String(spinOn)); this.textContent = spinOn ? 'Turning: on' : 'Turning: off';
  if (spinOn) spinStep();
});
if (RM) $('spin').hidden = true;

$('home').addEventListener('click', async () => {
  touring = false; hidePanel();
  await fly({ center: [78.9, 21], zoom: startZoom(), pitch: 0, bearing: 0 });
  spinStep();
});

$('tour').addEventListener('click', async () => {
  if (!DATA) return;
  hidePanel(); touring = true; userBusy = false;
  const s01 = DATA.spots.find((s) => s.id === 'S01');
  const s24 = DATA.spots.find((s) => s.id === 'S24');
  // The journey: each stop says one thing, in plain words. Any touch or drag ends it.
  const steps = [
    { view: { center: [78.9, 21], zoom: startZoom(), pitch: 0, bearing: 0 }, cap: ['1 of 6', 'Earth, from orbit', 'Every orange dot is an Indian city whose roads we measured from open map data.'] },
    { view: { center: [80, 22], zoom: 3.9, pitch: 10, bearing: 0 }, cap: ['2 of 6', '29 cities', 'The state and union territory capitals, plus the big metros. Hill capitals are left out: steep roads break the method.'] },
    { view: { center: [78.4, 17.45], zoom: 10.4, pitch: 40, bearing: -10 }, cap: ['3 of 6', 'Hyderabad, west corridor', 'Each ring is a place where the other side of the road is close, but getting there legally is not.'] },
    { spot: s01, view: { center: s01.a, zoom: 17.2, pitch: 62, bearing: 25 }, cap: ['4 of 6', 'Street level: 47 metres across', 'Here the far side is a short walk away. The map says a car needs 2.8 km to reach it.'] },
    { spot: s24, view: { center: s24.a, zoom: 16.8, pitch: 60, bearing: -30 }, cap: ['5 of 6', 'One way: 1.6 km. The other: 10.5 km', 'Direction matters. Coming back can be a very different trip.'] },
    { view: { center: [78.36, 17.5], zoom: 11.2, pitch: 35, bearing: 0 }, cap: ['10 of 10', 'Not yet confirmed', 'These are the map\'s numbers. Each place is being checked against a real drive before anything is called a finding. Tap any ring to explore.'] }
  ];
  for (const st of steps) {
    if (!touring) break;
    caption(st.cap); if (st.spot) startPulse(st.spot); else stopPulse(); await fly(st.view);
    if (!touring) break;
    await new Promise((r) => setTimeout(r, RM ? 4500 : 3200));
  }
  caption(null); touring = false;
});

function caption(c) {
  const el = $('cap');
  if (!c) { el.hidden = true; return; }
  el.querySelector('.eyebrow').textContent = 'Journey · ' + c[0];
  el.querySelector('h2').textContent = c[1];
  el.querySelector('p:last-of-type').textContent = c[2];
  el.hidden = false;
}
$('cap-stop').addEventListener('click', () => { touring = false; caption(null); map.stop(); });
for (const ev of ['mousedown', 'touchstart', 'wheel']) map.on(ev, () => { if (!$('cap').hidden) caption(null); });

// ---- panel: layered, with what is unusual and what is uncertain ----
function hidePanel() { $('panel').hidden = true; stopPulse(); }
$('close').addEventListener('click', hidePanel);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hidePanel(); });

function showPanel({ eyebrow, title, hook, facts, caveat, spot }) {
  if (window.innerWidth < 700) document.querySelector('.list').open = false;
  costSpot = spot || null; renderCost();
  $('p-eyebrow').textContent = eyebrow; $('p-title').textContent = title; $('p-hook').textContent = hook || '';
  const dl = $('p-facts'); dl.textContent = '';
  for (const [k, v] of facts) { const dt = document.createElement('dt'); dt.textContent = k; const dd = document.createElement('dd'); dd.textContent = v; dl.append(dt, dd); }
  $('p-caveat').textContent = caveat || '';
  $('panel').hidden = false;
}

async function selectCity(id) {
  const c = DATA.cities.find((x) => x.id === id); if (!c) return;
  if ($('p-write')) $('p-write').hidden = true;
  stopPulse();
  touring = false;
  await fly({ center: c.c, zoom: id === 'hyderabad' ? 10.4 : 10.8, pitch: 40, bearing: -10 });
  if (id === 'hyderabad') {
    showPanel({ eyebrow: 'City · measured', title: c.name, hook: '24 places on the west corridor where crossing the road takes a long way round.',
      facts: [['Places checked', '24'], ['Confirmed by a drive so far', String(DATA.spots.filter((x) => x.driven).length)]],
      caveat: 'Places marked driven were driven by arcroad on 1 Nov 2026 and matched the model. The rest are candidates: modelled from OpenStreetMap (extract of 25 Oct 2026). Tap a ring to see one.' });
  } else {
    showPanel({ eyebrow: 'City · measured', title: c.name, hook: 'Road network measured from the same open map data.',
      facts: [['Measured', '28 Oct 2026'], ['Places shown here', 'next']],
      caveat: 'Places worth a closer look in this city are being picked next. Nothing here is a confirmed finding yet.' });
  }
}

function drovenOn(s) { const ds = Object.values(s.driven || {}).map((d) => d.date).filter(Boolean).sort(); const f = (d) => { const [y, m, dd] = d.split('-'); return `${+dd} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+m - 1]} ${y}`; }; return ds.length ? f(ds[0]) : ''; }
function spotHook(s) {
  const worst = (x) => Math.max(x.ab || 0, x.ba || 0);
  const ranked = [...DATA.spots].sort((p, q) => worst(q) - worst(p));
  const rank = ranked.findIndex((x) => x.id === s.id) + 1;
  if (s.ba == null) return 'In one direction, no legal way back was found on the map at all.';
  if (rank === 1) return 'The longest way round of all 24 places checked.';
  const lo = Math.min(s.ab, s.ba), hi = Math.max(s.ab, s.ba);
  if (lo > 0 && hi / lo >= 5) return `Going one way is ${Math.round(hi / lo)} times longer than coming back.`;
  if (rank <= 5) return `One of the five longest ways round of the 24 places checked (number ${rank}).`;
  return `About ${Math.round(worst(s) / s.straight)} times the distance straight across.`;
}

let ROADS = null;
async function roadNames() {
  if (!ROADS) ROADS = await fetch('data/road_names.json').then((r) => (r.ok ? r.json() : {})).then((d) => d.spots || {}).catch(() => ({}));
  return ROADS;
}

async function selectSpot(id, move = true) {
  const s = DATA.spots.find((x) => x.id === id); if (!s) return;
  if (move) { touring = false; await fly({ center: s.a, zoom: 17.2, pitch: 62, bearing: 25 }); }
  const worst = Math.max(s.ab || 0, s.ba || 0);
  const dv = s.driven || {};
  const way = (d) => (dv[d] ? `${km(dv[d].m)} driven (model ${km(s[d])})` : (s[d] == null ? 'no legal route found' : km(s[d])));
  startPulse(s);
  const wr = $('p-write'); if (wr) { wr.hidden = Math.max(s.ab || 0, s.ba || 0) - s.straight < 60; $('p-write-a').href = '../act.html?pair=' + encodeURIComponent(s.id); }
  const rn = await roadNames(), road = rn[s.id] && ((rn[s.id].roads || [])[0] || (rn[s.id].refs || [])[0]);
  showPanel({
    eyebrow: `${road ? road + ' · ' : 'Hyderabad · '}place ${s.id} · ${s.driven ? 'driven ' + drovenOn(s) : 'candidate'}`, title: `${km(s.straight)} across, ${km(worst)} around`,
    hook: spotHook(s),
    facts: [['Straight across', km(s.straight)], ['By road, one way', way('ab')], ['By road, the other way', way('ba')], ['Times longer than crossing', '×' + Math.round(worst / s.straight)]],
    spot: s,
    caveat: s.driven ? `Driven by arcroad on ${drovenOn(s)} with a GPS recording, in ${Object.keys(dv).length === 2 ? 'both directions' : 'one direction'}; the drive matched the model within the pre-set tolerance. One drive so far: it becomes triangulated after a repeat on another day or a usable photo. Times include waits at signals and U-turn queues.${s.note ? ' ' + s.note : ''}` : 'Candidate, not a finding. Modelled from OpenStreetMap (extract of 25 Oct 2026) and not yet confirmed by a drive. A new gap in the median that the map has not caught up with would make the real trip shorter.'
  });
}

// ---- what the detour costs one person (an estimate, with every assumption shown) ----
const COST = { petrol: 116.15, priceDate: '16 Oct 2026', kmpl: { tw: 45, car: 15 }, kmh: 20 };
let costVehicle = 'tw', costTrips = 10, costSpot = null;
function renderCost() {
  const s = costSpot, box = $('p-cost');
  if (!s || s.ba == null) { box.hidden = true; return; }
  const extraKm = (s.ab + s.ba - 2 * s.straight) / 1000;          // one round trip, beyond crossing straight over
  const perMonth = extraKm * costTrips * 52 / 12;
  const rupees = perMonth / COST.kmpl[costVehicle] * COST.petrol;
  const minutes = perMonth / COST.kmh * 60;
  const dl = $('c-out'); dl.textContent = '';
  for (const [k, v] of [['Extra distance a month', perMonth.toFixed(1) + ' km'], ['Extra time a month', Math.round(minutes) + ' min'], ['Extra fuel a month', '₹' + Math.round(rupees).toLocaleString('en-IN')], ['Over a year', '₹' + Math.round(rupees * 12).toLocaleString('en-IN')]]) {
    const dt = document.createElement('dt'); dt.textContent = k; const dd = document.createElement('dd'); dd.textContent = v; dl.append(dt, dd);
  }
  $('c-trips').textContent = costTrips;
  $('c-assume').textContent = `Estimate. Assumes petrol at ₹${COST.petrol}/litre (Hyderabad, ${COST.priceDate}), ${COST.kmpl[costVehicle]} km per litre for a ${costVehicle === 'tw' ? 'two-wheeler' : 'car'}, ${COST.kmh} km/h in traffic, and the model's road distances, which are not yet confirmed.`;
  const calc = $('c-calc'); calc.textContent = '';
  calc.append('Work it out with your own numbers, one direction at a time: ');
  const dv = s.driven || {};
  [['ab', 'A → B'], ['ba', 'B → A']].forEach(([d, label], i) => {
    if (s[d] == null) return;
    const m = dv[d] ? dv[d].m : s[d], extra = Math.max(0, m - s.straight) / 1000;
    let href = `../cost/?place=${encodeURIComponent(s.id + ' ' + label.replace(' → ', ' to '))}&veh=${costVehicle}&km=${extra.toFixed(2)}`;
    if (dv[d] && dv[d].s) href += `&min=${Math.max(1, Math.round(dv[d].s / 60))}`;
    const a = document.createElement('a'); a.href = href; a.textContent = `${label}, ${extra.toFixed(2)} km extra${dv[d] ? ' (driven)' : ' (modelled)'}`;
    if (i && calc.lastChild && calc.lastChild.tagName === 'A') calc.append(' · ');
    calc.append(a);
  });
  box.hidden = false;
}
document.querySelectorAll('#p-cost .seg button').forEach((b) => b.addEventListener('click', () => {
  costVehicle = b.dataset.v; document.querySelectorAll('#p-cost .seg button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); renderCost();
}));
document.querySelectorAll('#p-cost .trips button').forEach((b) => b.addEventListener('click', (e) => {
  e.preventDefault(); costTrips = Math.max(1, Math.min(42, costTrips + Number(b.dataset.d))); renderCost();
}));

// ---- the same information as plain text (for any device, reader or connection) ----
function buildList() {
  const host = $('list'); if (host.childElementCount) return;
  const h1 = document.createElement('h3'); h1.textContent = `Hyderabad · 24 places (${DATA.spots.filter((x) => x.driven).length} driven, the rest candidates)`; host.append(h1);
  const t = document.createElement('table');
  t.innerHTML = '<thead><tr><th>Place</th><th class="n">Across</th><th class="n">One way</th><th class="n">Other way</th></tr></thead>';
  const tb = document.createElement('tbody');
  for (const s of DATA.spots) {
    const tr = document.createElement('tr');
    const td = (v, n) => { const c = document.createElement('td'); if (n) c.className = 'n'; c.textContent = v; return c; };
    const b = document.createElement('button'); b.type = 'button'; b.className = 'tap'; b.textContent = s.driven ? s.id + ' ✓' : s.id; if (s.driven) b.setAttribute('aria-label', s.id + ', driven by arcroad'); b.style.padding = '1px 8px'; b.addEventListener('click', () => selectSpot(s.id));
    const c0 = document.createElement('td'); c0.append(b);
    tr.append(c0, td(km(s.straight), 1), td(km(s.ab), 1), td(s.ba == null ? 'none' : km(s.ba), 1));
    tb.append(tr);
  }
  t.append(tb); host.append(t);
  const h2 = document.createElement('h3'); h2.textContent = '29 cities measured'; host.append(h2);
  const p = document.createElement('p'); p.style.margin = '0';
  DATA.cities.forEach((c, i) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'tap'; b.textContent = c.name; b.style.cssText = 'padding:1px 8px;margin:2px 4px 2px 0;font-size:12px';
    b.addEventListener('click', () => selectCity(c.id)); p.append(b);
  });
  host.append(p);
}

// Phones: stack the bottom controls, the key and the map credit so none overlaps another (Safari, Chrome, Firefox),
// whatever the wrap of the buttons or the browser's toolbars. Measured, not guessed.
function layoutPhone() {
  const phone = window.innerWidth <= 700;
  const ctl = document.querySelector('.ctl'), key = document.querySelector('.key'), list = document.querySelector('.list');
  const top = document.querySelector('header.top'), attrib = document.querySelector('.maplibregl-ctrl-bottom-right');
  if (!phone) { [key, list, attrib, document.getElementById('status')].forEach((e) => e && e.style.removeProperty(e === key || e === attrib ? 'bottom' : 'top')); return; }
  const gap = 8;
  const ctlTop = ctl ? ctl.getBoundingClientRect().top : window.innerHeight;
  const keyBottom = window.innerHeight - ctlTop + gap;
  if (key) key.style.bottom = keyBottom + 'px';
  const keyTop = key ? key.getBoundingClientRect().top : ctlTop;
  if (attrib) attrib.style.bottom = (window.innerHeight - keyTop + gap) + 'px';
  const status = document.getElementById('status');
  let below = top ? top.getBoundingClientRect().bottom + gap : 96;
  if (status) { status.style.top = Math.round(below) + 'px'; if (status.textContent.trim()) below = status.getBoundingClientRect().bottom + gap; }
  if (list) list.style.top = Math.round(below) + 'px';
}
['resize', 'orientationchange'].forEach((ev) => window.addEventListener(ev, () => requestAnimationFrame(layoutPhone)));
if (window.visualViewport) window.visualViewport.addEventListener('resize', () => requestAnimationFrame(layoutPhone));
map.on('load', layoutPhone);
requestAnimationFrame(layoutPhone);
setTimeout(layoutPhone, 600);
;(globalThis.__ar=globalThis.__ar||[]).push("ar-f0a1f9d2ea8d");
