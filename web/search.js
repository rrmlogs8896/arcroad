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
  // Everyday names for road numbers, so "Mumbai Highway" also finds a place tagged only NH65.
  var ALIAS = { "nh65": "Mumbai Highway Pune Highway Old Bombay Road", "nh44": "Bengaluru Highway Nagpur Highway",
    "nh163": "Warangal Highway", "nh765": "Srisailam Highway", "outer ring road": "ORR Nehru Outer Ring Road" };
  var COMMON = { "nh65": "Mumbai Highway", "nh44": "Bengaluru Highway" };
  function tidy(n) { n = String(n || "").replace(/\s+/g, " ").trim(); return n === n.toLowerCase() ? n.replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); }) : n; }
  function km(m) { return m < 1000 ? Math.round(m) + " m" : (m / 1000).toFixed(1) + " km"; }

  function load(base) {
    var get = function (u) { return fetch(base + u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); };
    return Promise.all([get("globe/data/places.json"), get("globe/data/road_names.json")]).then(function (d) {
      var places = d[0], names = (d[1] && d[1].spots) || {};
      if (!places) return null;
      return places.spots.map(function (s) {
        var n = names[s.id] || {}, roads = (n.roads || []).map(tidy), refs = n.refs || [];
        var key = function (r) { return r.toLowerCase().replace(/\s+(?=\d)/g, ""); };
        var label = roads[0] || (refs[0] ? refs[0] + (COMMON[key(refs[0])] ? " · " + COMMON[key(refs[0])] : "") : "Unnamed road");
        var extra = refs.concat(roads).map(function (r) { return ALIAS[key(r)] || ""; });
        var hay = norm([s.id, label].concat(roads, refs, extra, [n.area || "", "hyderabad"]).join(" "));
        return { s: s, label: label, area: tidy(n.area), hay: hay };
      });
    });
  }

  function h(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function link(href, text) { var a = h("a", null, text); a.href = href; return a; }

  function card(r, base) {
    var s = r.s, ways = [s.ab, s.ba].filter(function (x) { return x != null; });
    var worst = ways.length ? Math.max.apply(null, ways) : null;
    var extra = worst != null ? Math.max(0, worst - s.straight) : null;
    var dv = s.driven || {}, dkey = worst === s.ab ? "ab" : "ba", drv = dv[dkey];
    var href = base + "cost/?place=" + encodeURIComponent(s.id) + "&veh=car";
    if (extra != null) {
      href += "&km=" + ((drv ? Math.max(0, drv.m - s.straight) : extra) / 1000).toFixed(2);
      if (drv && drv.s) href += "&min=" + Math.max(1, Math.round(drv.s / 60));
    }
    var small = extra != null && extra < 60;
    var line = extra == null ? "No legal route found by the model."
      : small ? "Barely any detour here: " + km(extra) + " extra."
      : km(s.straight) + " straight across · " + km(drv ? drv.m : worst) + (drv ? " the long way round, driven" : " the long way round");
    var li = h("li", "rs-r"), t = h("p", "rs-t", r.label);
    if (r.area) { t.append(" "); t.append(h("span", "rs-a", r.area)); }
    var m = h("p", "rs-m"); m.append(h("span", "rs-s" + (s.driven ? " d" : ""), s.driven ? "Driven by arcroad" : "Modelled, not yet driven")); m.append(" · place " + s.id);
    var k = h("p", "rs-k");
    if (extra != null && !small) k.append(link(href, "What it costs you"));
    k.append(link(base + "globe/?spot=" + encodeURIComponent(s.id), "See it on the globe"));
    li.append(t, h("p", "rs-l", line), m, k);
    return li;
  }

  boxes.forEach(function (box) {
    var base = box.getAttribute("data-base") === "../" ? "../" : "./";
    var inp = box.querySelector(".rs-in"), out = box.querySelector(".rs-out");
    var rows = null, ready = load(base).then(function (r) { rows = r; });
    function say(text, href, label) {
      var p = h("p", "rs-n", text); if (href) { p.append(" "); p.append(link(href, label)); } return p;
    }
    function run() {
      var q = norm(inp.value);
      out.textContent = "";
      if (!q) return;
      if (!rows) { out.append(say("Loading places…")); ready.then(run); return; }
      var toks = q.split(" ");
      var hits = rows.filter(function (r) { return toks.every(function (t) { return r.hay.indexOf(t) !== -1; }); });
      hits.sort(function (a, b) { return Math.max(b.s.ab || 0, b.s.ba || 0) - Math.max(a.s.ab || 0, a.s.ba || 0); });
      if (!hits.length) {
        out.append(say("No measured crossing on that road yet. " + rows.length + " places in Hyderabad are measured so far, and more are added as volunteers drive them.", base + "volunteer/", "Help add your road"));
        return;
      }
      out.append(h("p", "rs-c", hits.length + (hits.length === 1 ? " place" : " places")));
      var ul = h("ul"); hits.slice(0, 6).forEach(function (r) { ul.append(card(r, base)); }); out.append(ul);
      if (hits.length > 6) out.append(say("Showing the 6 longest. Add a word to narrow it down."));
    }
    var t = null;
    inp.addEventListener("input", function () { clearTimeout(t); t = setTimeout(run, 120); });
    box.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  });
})();
