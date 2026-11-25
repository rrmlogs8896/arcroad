/* Ask arcroad: an on-device helper. It answers from this site's own pages (ask-index.json) and a few checked
   answers below. Everything runs in the visitor's browser: what is typed is never sent or stored, no cookies.
   The tone line adapts to the words typed, on this device only. A separate, opt-in sound button sits beside it. */
(function () {
  "use strict";
  if (window.__akLoaded) return; window.__akLoaded = true;
  var d = document, reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var css = d.createElement("link"); css.rel = "stylesheet"; css.href = "/ask.css"; d.head.appendChild(css);

  /* ---------- checked answers ---------- */
  var FAQ = [
    { q: "What is arcroad?", p: [/what is (arcroad|this)/, /\babout (arcroad|this site|this project)\b/, /what (do|does) (you|arcroad) do/, /\bexplain\b.*(arcroad|site|project)/], a: "<p>arcroad measures what crossing your own road really costs. On a divided road the place you want can be metres across, but the legal way round is a long detour. We model every crossing from open map data, then drive it to check.</p>", l: [["/", "Start here"], ["/drive/", "Ride the detour we drove"]] },
    { q: "What did you find?", p: [/what did you (find|learn)/, /\b(results?|findings?)\b/, /\b(accurate|accuracy|verified|proof|prove)\b/, /10 of 10|7 strict|did it match/], a: "<p>All 10 comparable directions we drove matched the model, and none failed. 7 were judged under rules written down before driving; 3 under rules added afterwards, which are dated and shown.</p>", l: [["/field/", "See every drive"]] },
    { q: "What does a detour cost me?", p: [/\bcost\b/, /how much/, /\b(money|rupees?|fuel|petrol|price|spend|expensive|calculator)\b/, /\b(co2|carbon|emissions?)\b/], a: "<p>The calculator's starting example is a 1.75 km detour, twice a day, 300 days a year, on a petrol two-wheeler: about ₹12,699 a year, counting fuel, wear and your time. Set the value of time to zero to see fuel and wear alone. Every number can be changed.</p>", l: [["/cost/", "Open the calculator"]] },
    { q: "What are you asking the city?", p: [/\b(loop|one[- ]way)\b/, /hi-?tech|hitec/, /biodiversity|ikea|mindspace|knowledge city|dallas/, /cyberabad moves|what do you (want|ask)|asking the city|\bthe ask\b/], a: "<p>Cyberabad Police have proposed a one-way loop through Biodiversity Junction, IKEA, Mindspace, Knowledge City and Dallas Center. We have today's distances for all 20 trips between those five points, 18 of 20 confirmed by two independent route-checkers, and publish no loop figures until the route is confirmed.</p><p><b>Our ask:</b> share one draft loop map, and we return the before-and-after detours promptly, to the city first.</p>", l: [["/moves/", "The entry and the ask"]] },
    { q: "Why did you withdraw the first loop estimate?", p: [/withdr[ae]w/, /first (trace|estimate|try)/, /\b(mistake|wrong)\b.*(loop|estimate)/], a: "<p>On 11 November our first try at working out the loop from a list of landmarks failed our own check: the route doubled back on itself. We withdrew it before it was shown anywhere, rather than publish a guess.</p>", l: [["/moves/", "Read how"]] },
    { q: "Is my data collected?", p: [/\b(privacy|private|cookies?|track(ing|ed)?|spy|collect|personal data|store)\b/], a: "<p>This helper runs entirely in your browser. What you type is not sent anywhere and not stored. The site sets no cookies and runs no analytics.</p>", l: [["/privacy/", "Privacy"]] },
    { q: "Who made arcroad?", p: [/\bwho\b.*(made|built|runs?|behind|created|are you)/, /\b(team|founder|author|sponsor|funded|funding)\b/], a: "<p>arcroad is a self-funded civic project from Hyderabad, made by Rohit and Team arcroad. No sponsors. The data is open (ODbL) and the code is open (MIT).</p>", l: [["/reuse/", "What you may reuse"]] },
    { q: "Is there an app?", p: [/\bapp\b/, /\b(download|install|play ?store|app ?store)\b/, /\b(roadmap|future|next|phase|plans?|bengaluru|bangalore|other cities)\b/], a: "<p>No app to install: arcroad works in your browser, and you can save it to your home screen. Planned next, open to pilot partners: a citizen web tool to check any proposed U-turn, and a no-install sandbox for traffic teams to test a diversion before barriers go down. Then Bengaluru and other cities.</p>", l: [["/roadmap/", "What comes next"], ["#ak-home", "Save to home screen"]] },
    { q: "How can I help?", p: [/\b(help|volunteer|join|contribute|participate|sign ?up)\b/, /\breport\b/], a: "<p>Two ways to help: tell us when a median opening opens or closes near you, or sign up to measure your own area.</p>", l: [["/report/", "Report a change"], ["/volunteer/", "Volunteer"]] },
    { q: "What is night glare?", p: [/\b(glare|high ?beam|headlights?|dazzl|blind(ed)?)\b/], a: "<p>Oncoming high beams wash out what a driver can see. At 60 km/h, each second dazzled is about 17 m driven blind.</p>", l: [["/roads/glare/", "See it from the driver's seat"]] },
    { q: "Is arcroad shortlisted?", p: [/shortlist|t-?hub|exhibition|\bevent\b|\baward\b/], a: "<p>arcroad is shortlisted in the Citizens Innovation Challenge at Cyberabad Moves 2026, on display at T-Hub, Raidurg, from 26 to 28 November.</p>", l: [["/moves/", "See the entry"]] },
    { q: "How do I contact you?", p: [/\b(contact|e-?mail|write to|reach you|phone)\b/], a: "<p>Write to hello@arcroad.org, or use the feedback form.</p>", l: [["/help/#feedback", "Feedback form"]] }
  ];
  var CHIPS = ["Show me around", "What did you find?", "What does a detour cost me?", "What are you asking the city?", "Is my data collected?", "Save to home screen"];
  var TOUR = [["/", "The problem", "A place you can see, but can't reach without a long detour."], ["/drive/", "Ride the detour", "The real drive at KPHB Colony: 13 m across, 1.58 km to drive."], ["/field/", "What we found", "Every drive, including the misses."], ["/cost/", "Your cost", "Fuel, wear and time, with your own numbers."], ["/moves/", "The ask", "The Hi-Tech City loop, measured before it opens."]];

  /* ---------- mood, on this device only ---------- */
  var MOOD = {
    upset: [/\b(angry|hate|worst|terrible|awful|frustrat\w*|annoy\w*|useless|pathetic|ridiculous|fed up|sick of|ugh+|nightmare)\b/, /stuck (in|for)|waste of time|every day this/],
    doubt: [/\b(really|seriously|fake|biased|trust|doubt\w*|reliable|accurate)\b\??/, /how do (you|we) know|are you sure|prove it|source\??$/],
    glad: [/\b(thanks?|thank you|great|love|awesome|brilliant|helpful|nice|well done|amazing|wow)\b/]
  };
  var TONE = { upset: "That frustration is exactly why arcroad exists. Here is what we know.", doubt: "Fair to ask. Here is the evidence, and where to check it.", glad: "Glad it helps." };
  function mood(q) { var best = null, n = 0; Object.keys(MOOD).forEach(function (m) { var c = 0; MOOD[m].forEach(function (r) { if (r.test(q)) c++; }); if (c > n) { n = c; best = m; } }); return best; }

  /* ---------- search over the site's own pages ---------- */
  var STOP = {}; ("a an the is are was were be been of to in on at for and or but what how why who when where which do does did i me my we you your it its this that these those with can could would should about from by as any some there their them they he she his her not no yes so if then than too very just also into over up out more most much many please tell show give find know want need get like").split(" ").forEach(function (w) { STOP[w] = 1; });
  function norm(s) { return String(s || "").toLowerCase().replace(/[’']/g, "").replace(/[^a-z0-9₹.ఀ-౿]+/g, " ").replace(/\s+/g, " ").trim(); }
  function terms(s) { return norm(s).split(" ").filter(function (t) { return t.length > 1 && !STOP[t]; }).map(function (t) { return t.length > 4 ? t.replace(/(ing|es|s)$/, "") : t; }); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var idx = null, docs = [], df = {}, N = 0;
  var SKIP = /₹0\s?per|Your message It is mostly|First name \(optional\)|Choose one/;
  function loadIdx() {
    if (idx) return Promise.resolve(idx);
    return fetch("/ask-index.json").then(function (r) { return r.ok ? r.json() : { pages: [] }; }).catch(function () { return { pages: [] }; }).then(function (j) {
      idx = j; docs = [];
      j.pages.forEach(function (p) { p.s.forEach(function (s) {
        if (SKIP.test(s.t)) return;
        var ht = terms(p.title + " " + s.h), bt = terms(s.t), seen = {};
        ht.concat(bt).forEach(function (t) { if (!seen[t]) { seen[t] = 1; df[t] = (df[t] || 0) + 1; } });
        docs.push({ p: p, s: s, ht: ht, bt: bt });
      }); });
      N = docs.length; return idx;
    });
  }
  function count(arr, t) { var c = 0; for (var i = 0; i < arr.length; i++) if (arr[i] === t || (t.length > 3 && arr[i].indexOf(t) === 0)) c++; return c; }
  var SYN = { closur: ["close", "closed"], close: ["closed", "closure"], closed: ["close", "closure"], traffic: ["crawl", "slow", "queue"], jam: ["crawl", "queue"], uturn: ["u-turn", "turn"], accident: ["crash", "death"], crash: ["accident"], walk: ["pedestrian", "foot"], pedestrian: ["walk", "foot"], fuel: ["petrol"], petrol: ["fuel"], time: ["minute"], far: ["km", "distance"], distance: ["km"] };
  function search(q) {
    var qt = terms(q).map(function (t) { return t.replace(/-/g, ""); }); if (!qt.length || !N) return [];
    var w = qt.map(function (t) { return Math.log(1 + N / (1 + (df[t] || 0))); }), wsum = w.reduce(function (a, b) { return a + b; }, 0);
    var hits = [];
    docs.forEach(function (dd) {
      var sc = 0, gotw = 0;
      qt.forEach(function (t, i) {
        var h = count(dd.ht, t), b = Math.min(3, count(dd.bt, t));
        if (!h && !b && SYN[t]) SYN[t].some(function (y) { h = count(dd.ht, y); b = Math.min(3, count(dd.bt, y)); return h || b; });
        if (h || b) { gotw += w[i]; sc += w[i] * (h * 2.5 + b); }
      });
      var cov = gotw / wsum;
      if (cov >= 0.55) hits.push({ sc: sc * cov, dd: dd });
    });
    hits.sort(function (a, b) { return b.sc - a.sc; });
    if (!hits.length || hits[0].sc < 2) return [];
    var seen = {}, out = [];
    hits.forEach(function (h) {
      if (out.length >= 3 || h.sc < hits[0].sc * 0.35) return;
      var sents = h.dd.s.t.split(/(?<=[.!?])\s+/), best = sents[0] || "", bs = -1;
      sents.forEach(function (x) { var c = 0, nx = norm(x); qt.forEach(function (t) { if (nx.indexOf(t) > -1) c++; }); if (c > bs) { bs = c; best = x; } });
      if (best.length > 230) best = best.slice(0, 227) + "…";
      var key = norm(best).slice(0, 80); if (seen[key]) return; seen[key] = 1;
      out.push({ u: h.dd.p.u + (h.dd.s.id ? "#" + h.dd.s.id : ""), title: h.dd.s.h || h.dd.p.title, snip: best });
    });
    return out;
  }
  function faq(q) {
    var best = null, n = 0;
    FAQ.forEach(function (f) { var c = 0; f.p.forEach(function (r) { if (r.test(q)) c++; }); if (norm(f.q) === q) c += 5; if (c > n) { n = c; best = f; } });
    return n ? best : null;
  }
  function homeScreen() {
    var ua = navigator.userAgent || "";
    if (/iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && "ontouchend" in d)) return "<p>On iPhone or iPad: tap <b>Share</b> in Safari, then <b>Add to Home Screen</b>.</p>";
    if (/Android/.test(ua)) return "<p>On Android: open the browser menu (⋮), then tap <b>Add to Home screen</b> or <b>Install app</b>.</p>";
    return "<p>On a computer: bookmark it with Ctrl+D (Cmd+D on a Mac). On a phone, use the browser's <b>Add to Home screen</b>.</p>";
  }
  function tour() { return "<p>Five stops, about a minute each:</p><ol class=\"ak-ol\">" + TOUR.map(function (t) { return "<li><a href=\"" + t[0] + "\">" + esc(t[1]) + "</a>: " + esc(t[2]) + "</li>"; }).join("") + "</ol>"; }

  /* ---------- suggestions as you type ---------- */
  var SUGG = FAQ.map(function (f) { return f.q; }).concat(["Show me around", "Save to home screen", "Muthangi", "Hafeezpet", "KPHB Colony", "Wrong-side driving", "Night glare", "Road works and diversions", "What comes next"]);
  function addHeadings() { if (!idx) return; idx.pages.forEach(function (p) { p.s.forEach(function (s) { if (s.h && s.h.length > 6 && s.h.length < 60 && SUGG.indexOf(s.h) < 0) SUGG.push(s.h); }); }); }

  /* ---------- UI ---------- */
  var fab = d.createElement("button");
  fab.className = "ak-fab"; fab.type = "button"; fab.setAttribute("aria-expanded", "false"); fab.setAttribute("aria-controls", "ak-panel");
  fab.innerHTML = "<span class=\"ak-dot\" aria-hidden=\"true\"></span>Ask arcroad";
  var snd = d.createElement("button");
  snd.className = "ak-snd-fab"; snd.type = "button"; snd.setAttribute("aria-pressed", "false"); snd.setAttribute("aria-label", "Soft background sound, off");
  snd.title = "Soft background sound (off until you tap)";
  snd.innerHTML = "<svg viewBox=\"0 0 24 24\" width=\"18\" height=\"18\" aria-hidden=\"true\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M9 18V5l11-2v13\"/><circle cx=\"6\" cy=\"18\" r=\"3\"/><circle cx=\"17\" cy=\"16\" r=\"3\"/></svg><span class=\"ak-eq\" aria-hidden=\"true\"><i></i><i></i><i></i></span>";
  var panel = d.createElement("section");
  panel.className = "ak-panel"; panel.id = "ak-panel"; panel.hidden = true; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Ask arcroad");
  panel.innerHTML = "<div class=\"ak-head\"><div><b>Ask arcroad</b><span>Answers from this site, worked out on your device</span></div><button class=\"ak-x\" type=\"button\" aria-label=\"Close\">×</button></div>"
    + "<div class=\"ak-log\" aria-live=\"polite\"></div><div class=\"ak-chips\"></div>"
    + "<form class=\"ak-form\" autocomplete=\"off\"><div class=\"ak-field\"><label for=\"ak-in\" class=\"ak-sr\">Your question</label><input class=\"ak-in\" id=\"ak-in\" enterkeyhint=\"send\" placeholder=\"Type a question, a road or an area…\" maxlength=\"200\" role=\"combobox\" aria-autocomplete=\"list\" aria-expanded=\"false\" aria-controls=\"ak-sug\"><ul class=\"ak-sug\" id=\"ak-sug\" role=\"listbox\" hidden></ul></div><button class=\"ak-go\" type=\"submit\">Ask</button></form>"
    + "<p class=\"ak-note\">Nothing you type leaves this device or is kept.</p>";
  var log = panel.querySelector(".ak-log"), chips = panel.querySelector(".ak-chips"), input = panel.querySelector(".ak-in"), sug = panel.querySelector(".ak-sug");
  CHIPS.forEach(function (c) { var b = d.createElement("button"); b.type = "button"; b.className = "ak-chip"; b.textContent = c; b.addEventListener("click", function () { ask(c); }); chips.appendChild(b); });

  function say(html, me) {
    var m = d.createElement("div"); m.className = "ak-msg " + (me ? "ak-me" : "ak-bot");
    if (me) m.textContent = html; else m.innerHTML = html;
    log.appendChild(m);
    requestAnimationFrame(function () { m.classList.add("in"); log.scrollTo({ top: log.scrollHeight, behavior: reduce ? "auto" : "smooth" }); });
  }
  function thinking() { var t = d.createElement("div"); t.className = "ak-msg ak-bot ak-typing in"; t.innerHTML = "<i></i><i></i><i></i>"; log.appendChild(t); log.scrollTop = log.scrollHeight; return t; }
  function links(l) { return l && l.length ? "<p class=\"ak-links\">" + l.map(function (x) { return "<a href=\"" + x[0] + "\">" + esc(x[1]) + " →</a>"; }).join("") + "</p>" : ""; }
  function ask(raw) {
    raw = String(raw || "").trim(); var q = norm(raw); if (!q) return;
    hideSug(); say(raw, true); input.value = "";
    var m = mood(q), pre = m ? "<p class=\"ak-tone ak-" + m + "\">" + esc(TONE[m]) + "</p>" : "";
    var t = thinking();
    loadIdx().then(function () {
      setTimeout(function () {
        t.remove();
        if (/show me around|\btour\b|guide me|walk me|where (do i|should i) start/.test(q)) return say(pre + tour());
        if (/home ?screen|shortcut|save (it|this|arcroad)|bookmark|add to home/.test(q)) return say(pre + homeScreen());
        var f = faq(q), hits = search(raw), more = "";
        if (hits.length) more = (f ? "<p class=\"ak-sub\">Also on the site</p>" : "") + hits.slice(0, f ? 2 : 3).map(function (h) { return "<a class=\"ak-hit\" href=\"" + esc(h.u) + "\"><b>" + esc(h.title) + "</b><small>" + esc(h.snip) + "</small></a>"; }).join("");
        if (f) return say(pre + f.a + links(f.l) + more);
        if (more) return say(pre + "<p>Here is where the site covers that:</p>" + more);
        if (m === "upset") return say(pre + "<p>I could not find that exact thing on the site, but two things help most: tell us about the place, or send the people responsible a ready letter.</p>" + links([["/report/", "Report a change"], ["/act.html", "Write to the people responsible"]]));
        say(pre + "<p>I could not find that on this site. Try a road or area name, or one of the suggestions below. For anything else, write to hello@arcroad.org.</p>");
      }, reduce ? 0 : 260);
    });
  }
  /* suggestions */
  var active = -1;
  function hideSug() { sug.hidden = true; input.setAttribute("aria-expanded", "false"); active = -1; }
  function showSug() {
    var v = norm(input.value); if (v.length < 2) return hideSug();
    var list = SUGG.filter(function (s) { var n = norm(s); return n.indexOf(v) > -1 || v.split(" ").every(function (w) { return n.indexOf(w) > -1; }); }).slice(0, 5);
    if (!list.length) return hideSug();
    sug.innerHTML = list.map(function (s, i) { return "<li role=\"option\" id=\"ak-o" + i + "\" data-v=\"" + esc(s) + "\">" + esc(s) + "</li>"; }).join("");
    sug.hidden = false; input.setAttribute("aria-expanded", "true"); active = -1;
  }
  input.addEventListener("input", function () { loadIdx().then(function () { if (SUGG.length < 40) addHeadings(); showSug(); }); });
  input.addEventListener("keydown", function (e) {
    var items = sug.querySelectorAll("li"); if (sug.hidden || !items.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); active = (active + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length; Array.prototype.forEach.call(items, function (li, i) { li.setAttribute("aria-selected", String(i === active)); }); input.setAttribute("aria-activedescendant", "ak-o" + active); }
    else if (e.key === "Enter" && active > -1) { e.preventDefault(); ask(items[active].getAttribute("data-v")); }
    else if (e.key === "Escape") { e.stopPropagation(); hideSug(); }
  });
  sug.addEventListener("mousedown", function (e) { var li = e.target.closest("li"); if (li) { e.preventDefault(); ask(li.getAttribute("data-v")); } });
  input.addEventListener("blur", function () { setTimeout(hideSug, 120); });
  panel.querySelector(".ak-form").addEventListener("submit", function (e) { e.preventDefault(); ask(input.value); });
  log.addEventListener("click", function (e) { var a = e.target.closest && e.target.closest("a[href='#ak-home']"); if (a) { e.preventDefault(); say(homeScreen()); } });

  var hideT = null;
  function open(v) {
    clearTimeout(hideT); fab.setAttribute("aria-expanded", String(v));
    if (v) {
      panel.hidden = false; requestAnimationFrame(function () { requestAnimationFrame(function () { panel.classList.add("show"); }); });
      if (!log.childNodes.length) say("<p>Hello. Ask me anything about arcroad: type a question, a road or an area, or pick one below.</p>");
      loadIdx(); setTimeout(function () { input.focus({ preventScroll: true }); }, reduce ? 0 : 180);
    } else {
      panel.classList.remove("show"); hideT = setTimeout(function () { panel.hidden = true; }, reduce ? 0 : 200); fab.focus();
    }
  }
  fab.addEventListener("click", function () { open(panel.hidden || !panel.classList.contains("show")); });
  panel.querySelector(".ak-x").addEventListener("click", function () { open(false); });
  d.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) open(false); });

  /* ---------- soft sound: made in the browser, nothing fetched, off until tapped, never autoplays ---------- */
  var ac = null, master = null;
  function soundOn() {
    var C = window.AudioContext || window.webkitAudioContext; if (!C) return false;
    ac = new C(); master = ac.createGain(); master.gain.value = 0;
    var lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 900; master.connect(lp); lp.connect(ac.destination);
    [196, 246.94, 293.66, 392].forEach(function (f, i) {
      var o = ac.createOscillator(), g = ac.createGain(), l = ac.createOscillator(), lg = ac.createGain();
      o.type = i % 2 ? "triangle" : "sine"; o.frequency.value = f; o.detune.value = (i - 1.5) * 4;
      g.gain.value = 0.045; l.frequency.value = 0.04 + i * 0.021; lg.gain.value = 0.03;
      l.connect(lg); lg.connect(g.gain); o.connect(g); g.connect(master); o.start(); l.start();
    });
    master.gain.linearRampToValueAtTime(0.45, ac.currentTime + 3); return true;
  }
  function soundOff() { if (!ac) return; var a = ac; master.gain.cancelScheduledValues(a.currentTime); master.gain.setValueAtTime(master.gain.value, a.currentTime); master.gain.linearRampToValueAtTime(0, a.currentTime + 0.8); setTimeout(function () { a.close(); }, 900); ac = null; }
  snd.addEventListener("click", function () {
    var on = snd.getAttribute("aria-pressed") !== "true";
    if (on && !soundOn()) return; if (!on) soundOff();
    snd.setAttribute("aria-pressed", String(on)); snd.setAttribute("aria-label", "Soft background sound, " + (on ? "on" : "off"));
  });
  d.addEventListener("visibilitychange", function () { if (ac) { if (d.hidden) ac.suspend(); else ac.resume(); } });

  d.body.appendChild(panel); d.body.appendChild(snd); d.body.appendChild(fab);
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-17c4bccb827c");
