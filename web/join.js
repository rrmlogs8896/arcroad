/* Join strip (27 Nov 2026): the volunteer loop placed where a reader has just seen the problem.
   One field, one tap, no name, email or phone. It shares the volunteer page's sign-up (same code, same
   device copy), so joining here and on /volunteer/ is the same thing. After joining it shows the next
   starter task and a "bring one neighbour" share, and sharing ticks the "tell" task. */
(function () {
  "use strict";
  var KEY = "arcroad.volunteer.v1", API = "/api/volunteer";
  var slots = document.querySelectorAll("[data-join]");
  if (!slots.length) return;
  var COPY = {
    home: ["Your crossing is probably on no list yet.", "Add your area and we start measuring it with you."],
    cost: ["That cost is real, and it is fixable.", "Join and help us measure the crossing you just priced."],
    roads: ["You have seen what the road invites.", "Help us photograph and time one place near you."],
    field: ["Every place here was driven and timed.", "Add your area and the next drive could be yours."],
    moves: ["A prize is a start. Your street is the point.", "Join the people measuring their own crossings."],
    uturns: ["Know a U-turn like these?", "Add your area and help us time it."],
    report: ["Thank you for looking closely.", "Join and we will send you the next place to check."],
    globe: ["Know a crossing like this one?", "Add your area and help us measure it."]
  };
  var TASKS = [["check", "Check one crossing near you", "/uturns/"], ["map", "Fix one road on OpenStreetMap", "https://www.openstreetmap.org/"], ["report", "Report one opening that opened or closed", "/report/"], ["tell", "Tell your resident association or college", "/moves/"], ["cost", "Work out your own crossing's cost", "/cost/"]];
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
  function keep(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function code() { var d = new Date(), p = function (n) { return (n < 10 ? "0" : "") + n; }; return "AR-V-" + String(d.getFullYear()).slice(2) + p(d.getMonth() + 1) + p(d.getDate()) + "-" + Math.random().toString(36).slice(2, 6).toUpperCase().replace(/[^A-Z0-9]/g, "X").padEnd(4, "X"); }
  function sync(v) { return fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(v), keepalive: true }).then(function (r) { v.synced = r.ok; keep(v); }).catch(function () { v.synced = false; keep(v); }); }
  var count = null;
  fetch(API).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { if (j && typeof j.count === "number" && j.count > 0) { count = j.count; paintAll(); } }).catch(function () {});

  var css = document.createElement("style");
  css.textContent = ".jn{margin:40px auto;width:calc(100% - 32px);max-width:720px;box-sizing:border-box;padding:22px 22px 20px;border:1px solid rgba(230,232,235,.1);border-radius:18px;background:linear-gradient(180deg,rgba(124,197,160,.06),rgba(11,14,19,.0) 70%);color:#E6E8EB;font:15px/1.6 Inter,system-ui,-apple-system,sans-serif}"
    + ".jn-k{margin:0 0 8px;font:500 12px/1.4 ui-monospace,SFMono-Regular,monospace;letter-spacing:.08em;text-transform:uppercase;color:#8B939C;display:flex;align-items:center;gap:8px}"
    + ".jn-k i{width:8px;height:8px;border-radius:50%;background:#7CC5A0;box-shadow:0 0 0 0 rgba(124,197,160,.5);animation:jnp 2.4s ease-out infinite}"
    + "@keyframes jnp{0%{box-shadow:0 0 0 0 rgba(124,197,160,.45)}70%,100%{box-shadow:0 0 0 8px rgba(124,197,160,0)}}"
    + ".jn h3{margin:0 0 4px;font-size:20px;line-height:1.3;font-weight:600;color:#F5F6F7}.jn p{margin:0}.jn .jn-s{color:#C9CDD2}"
    + ".jn form{display:flex;gap:8px;margin:14px 0 8px;flex-wrap:wrap}.jn input{flex:1 1 220px;min-width:0;min-height:44px;padding:8px 14px;border-radius:999px;border:1px solid rgba(230,232,235,.16);background:#0B0E13;color:#E6E8EB;font:inherit}"
    + ".jn input:focus-visible,.jn button:focus-visible,.jn a:focus-visible{outline:2px solid #7CC5A0;outline-offset:2px}"
    + ".jn button,.jn .jn-b{min-height:44px;padding:0 18px;border-radius:999px;border:1px solid #7CC5A0;background:#7CC5A0;color:#06110B;font:600 15px/1 Inter,system-ui,sans-serif;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;text-decoration:none;touch-action:manipulation;transition:transform .15s ease,background .2s ease}"
    + ".jn button:hover,.jn .jn-b:hover{transform:translateY(-1px)}.jn .jn-g{background:transparent;color:#7CC5A0}"
    + ".jn-f{font-size:13px;color:#8B939C}.jn-f a{color:#8FB4D9}"
    + ".jn-bar{height:6px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;margin:12px 0 14px}.jn-bar i{display:block;height:100%;background:#7CC5A0;transition:width .5s ease}"
    + ".jn-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}"
    + "@media (prefers-reduced-motion:reduce){.jn-k i{animation:none}.jn button,.jn .jn-b,.jn-bar i{transition:none}}@media print{.jn{display:none}}";
  document.head.appendChild(css);

  function kicker() { return '<p class="jn-k"><i aria-hidden="true"></i>' + (count ? count.toLocaleString("en-IN") + (count === 1 ? " citizen has" : " citizens have") + " joined" : "Citizens measuring their roads") + '</p>'; }
  function paint(el) {
    var ctx = el.getAttribute("data-join"), c = COPY[ctx] || COPY.home, v = load();
    if (!v) {
      el.innerHTML = kicker() + '<h3>' + esc(c[0]) + '</h3><p class="jn-s">' + esc(c[1]) + '</p>'
        + '<form novalidate><label class="sr" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)" for="jn-a-' + ctx + '">Your area or locality</label><input id="jn-a-' + ctx + '" name="area" maxlength="80" autocomplete="address-level2" placeholder="Your area, e.g. Miyapur" enterkeyhint="go"><button type="submit">Join in 10 seconds</button></form>'
        + '<p class="jn-f">No name, phone or email. Remove it any time. <a href="/volunteer/">More ways to help</a></p>';
      return;
    }
    var done = TASKS.filter(function (t) { return v.tasks && v.tasks[t[0]]; }).length, next = TASKS.filter(function (t) { return !(v.tasks && v.tasks[t[0]]); })[0];
    el.innerHTML = kicker() + '<h3>' + (el._fresh ? "You're in" : "Welcome back") + (v.area ? ", " + esc(v.area) : "") + '.</h3>'
      + '<p class="jn-s">' + (next ? 'Your next step: <b style="color:#F5F6F7">' + esc(next[1]) + '</b>' : "All five starter tasks done. Thank you.") + '</p>'
      + '<div class="jn-bar" role="progressbar" aria-valuemin="0" aria-valuemax="' + TASKS.length + '" aria-valuenow="' + done + '" aria-label="Starter tasks done"><i style="width:' + Math.round(done / TASKS.length * 100) + '%"></i></div>'
      + '<div class="jn-row">' + (next ? '<a class="jn-b" href="' + next[2] + '"' + (next[2].indexOf("http") === 0 ? ' rel="noopener" target="_blank"' : '') + '>Start this step</a>' : '') + '<button type="button" class="jn-g" data-a="share">Bring one neighbour</button><a class="jn-b jn-g" href="/volunteer/#signup">Your card · ' + done + ' of ' + TASKS.length + '</a></div>';
  }
  function paintAll() { Array.prototype.forEach.call(slots, function (el) { paint(el); }); }

  Array.prototype.forEach.call(slots, function (el) {
    el.classList.add("jn"); el.setAttribute("aria-live", "polite");
    if (!el.getAttribute("aria-label")) el.setAttribute("aria-label", "Join arcroad");
    el.addEventListener("submit", function (e) {
      e.preventDefault(); e.stopImmediatePropagation();
      var v = load() || { code: code(), help: [], time: "", tasks: {} };
      v.area = ((e.target.elements.area && e.target.elements.area.value) || "").trim().slice(0, 80);
      v.src = el.getAttribute("data-join"); keep(v); sync(v); el._fresh = true; paintAll();
      var h = el.querySelector("h3"); if (h) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); }
    }, true);
    el.addEventListener("click", function (e) {
      var b = e.target.closest && e.target.closest("[data-a=share]"); if (!b) return;
      var url = "https://arcroad.org/volunteer/", text = "I'm helping measure the detours on Hyderabad's roads. Add your area in 10 seconds:";
      var mark = function () { var v = load(); if (!v) return; v.tasks = v.tasks || {}; if (!v.tasks.tell) { v.tasks.tell = true; keep(v); sync(v); paintAll(); } };
      if (navigator.share) navigator.share({ title: "arcroad", text: text, url: url }).then(mark).catch(function () {});
      else { window.open("https://wa.me/?text=" + encodeURIComponent(text + " " + url), "_blank", "noopener"); mark(); }
    });
  });
  paintAll();
  window.addEventListener("storage", function (e) { if (e.key === KEY) paintAll(); });
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-3c8e1f0a4b27");
