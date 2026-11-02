/* arcroad street search. Type a road, area or place number; see what crossing it costs.
   Data: globe/data/places.json (model + drives) and globe/data/road_names.json (OpenStreetMap names, ODbL).
   Markup: <div class="rs" data-base="./"> with an input.rs-in and a div.rs-out inside. */
(function () {
  "use strict";
  var boxes = document.querySelectorAll(".rs");
  if (!boxes.length) return;

  function norm(s) {
    return String(s || "").toLowerCase()
      .replace(/\broad\b/g, "rd").replace(/\bstreet\b/g, "st").replace(/\bhighway\b/g, "hwy")
      .replace(/\bnational\s+hwy\b/g, "nh").replace(/[^a-z0-9ఀ-౿]+/g, " ").trim();
  }
  function km(m) { return m < 1000 ? Math.round(m) + " m" : (m / 1000).toFixed(1) + " km"; }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  function load(base) {
    var get = function (u) { return fetch(base + u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); };
    return Promise.all([get("globe/data/places.json"), get("globe/data/road_names.json")]).then(function (d) {
      var places = d[0], names = (d[1] && d[1].spots) || {};
      if (!places) return null;
      return places.spots.map(function (s) {
        var n = names[s.id] || {}, roads = n.roads || [], refs = n.refs || [];
        var label = roads[0] || refs[0] || "Unnamed road";
        var hay = norm([s.id, label].concat(roads, refs, [n.area || "", "hyderabad"]).join(" "));
        return { s: s, label: label, area: n.area || "", hay: hay };
      });
    });
  }

  function card(r, base) {
    var s = r.s, ways = [s.ab, s.ba].filter(function (x) { return x != null; });
    var worst = ways.length ? Math.max.apply(null, ways) : null;
    var extra = worst != null ? Math.max(0, worst - s.straight) : null;
    var dv = s.driven || {}, dkey = worst === s.ab ? "ab" : "ba", drv = dv[dkey];
    var status = s.driven ? "Driven by arcroad" : "Modelled, not yet driven";
    var href = base + "cost/?place=" + encodeURIComponent(s.id) + "&veh=car";
    if (extra != null) {
      var xkm = (drv ? Math.max(0, drv.m - s.straight) : extra) / 1000;
      href += "&km=" + xkm.toFixed(2);
      if (drv && drv.s) href += "&min=" + Math.max(1, Math.round(drv.s / 60));
    }
    var small = extra != null && extra < 60;
    var line = extra == null ? "No legal route found by the model."
      : small ? "Barely any detour here: " + km(extra) + " extra."
      : km(s.straight) + " straight across · " + km(drv ? drv.m : worst) + (drv ? " the long way round, driven" : " the long way round");
    return '<li class="rs-r"><p class="rs-t">' + esc(r.label) + (r.area ? ' <span class="rs-a">' + esc(r.area) + "</span>" : "") + "</p>" +
      '<p class="rs-l">' + esc(line) + "</p>" +
      '<p class="rs-m"><span class="rs-s' + (s.driven ? " d" : "") + '">' + status + "</span> · place " + esc(s.id) + "</p>" +
      '<p class="rs-k">' + (extra != null && !small ? '<a href="' + href + '">What it costs you</a>' : "") +
      '<a href="' + base + "globe/?spot=" + encodeURIComponent(s.id) + '">See it on the globe</a></p></li>';
  }

  boxes.forEach(function (box) {
    var base = box.getAttribute("data-base") || "./";
    var inp = box.querySelector(".rs-in"), out = box.querySelector(".rs-out");
    var rows = null, ready = load(base).then(function (r) { rows = r; });
    function run() {
      var q = norm(inp.value);
      if (!q) { out.innerHTML = ""; return; }
      if (!rows) { out.innerHTML = '<p class="rs-n">Loading places…</p>'; ready.then(run); return; }
      var toks = q.split(" ");
      var hits = rows.filter(function (r) { return toks.every(function (t) { return r.hay.indexOf(t) !== -1; }); });
      hits.sort(function (a, b) { return Math.max(b.s.ab || 0, b.s.ba || 0) - Math.max(a.s.ab || 0, a.s.ba || 0); });
      if (!hits.length) {
        out.innerHTML = '<p class="rs-n">No measured crossing on that road yet. ' + rows.length +
          ' places in Hyderabad are measured so far, and more are added as volunteers drive them. <a href="' + base + 'volunteer/">Help add your road</a></p>';
        return;
      }
      out.innerHTML = '<p class="rs-c">' + hits.length + (hits.length === 1 ? " place" : " places") + "</p><ul>" +
        hits.slice(0, 6).map(function (r) { return card(r, base); }).join("") + "</ul>" +
        (hits.length > 6 ? '<p class="rs-n">Showing the 6 longest. Add a word to narrow it down.</p>' : "");
    }
    var t = null;
    inp.addEventListener("input", function () { clearTimeout(t); t = setTimeout(run, 120); });
    box.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  });
})();
