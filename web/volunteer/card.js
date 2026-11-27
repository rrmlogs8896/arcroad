/* Volunteer card (26 Nov 2026). Saved straight to arcroad with no email step and no personal details:
   a random code made here, the area typed, the ways chosen, the time offered and the ticked starter tasks.
   A copy stays on this device so progress shows instantly, even offline. "Remove" deletes both copies. */
(function () {
  "use strict";
  var KEY = "arcroad.volunteer.v1", API = "/api/volunteer";
  var form = document.querySelector("form[data-intake=volunteer]"), box = document.getElementById("vcard");
  if (!form || !box) return;
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
  function keep(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); return true; } catch (e) { return false; } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function code() { var d = new Date(), p = function (n) { return (n < 10 ? "0" : "") + n; }; return "AR-V-" + String(d.getFullYear()).slice(2) + p(d.getMonth() + 1) + p(d.getDate()) + "-" + Math.random().toString(36).slice(2, 6).toUpperCase().replace(/[^A-Z0-9]/g, "X").padEnd(4, "X"); }
  var TASKS = [["check", "Check one crossing near you", "/uturns/"], ["map", "Fix one road on OpenStreetMap", "https://www.openstreetmap.org/"], ["report", "Report one opening that opened or closed", "/report/"], ["tell", "Tell your resident association or college", "/moves/"], ["cost", "Work out your own crossing's cost", "/cost/"]];
  var state = "";
  function sync(v) {
    state = "saving"; paint(v);
    return fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(v), keepalive: true })
      .then(function (r) { state = r.ok ? "saved" : "local"; }).catch(function () { state = "local"; }).then(function () { v.synced = state === "saved"; keep(v); paint(v); });
  }
  function paint(v) {
    if (!v) { box.hidden = true; form.hidden = false; return; }
    form.hidden = true; box.hidden = false;
    var done = TASKS.filter(function (t) { return v.tasks && v.tasks[t[0]]; }).length;
    var st = state === "saving" ? "Saving to arcroad…" : (state === "saved" || v.synced) ? "Saved with arcroad" : "Saved on this device; arcroad could not be reached, it will retry";
    box.innerHTML = '<p class="note" style="margin:0 0 6px">Your volunteer card · <span style="color:' + ((state === "saved" || v.synced) ? "#7CC5A0" : "#9AA0A6") + '">' + st + '</span></p>'
      + '<h3 style="margin:0 0 4px;font-size:20px">Thank you' + (v.area ? ", " + esc(v.area) : "") + '.</h3>'
      + '<p style="margin:0 0 12px;color:#C9CDD2">Your code <b style="font-family:ui-monospace,monospace">' + esc(v.code) + '</b> · ' + done + ' of ' + TASKS.length + ' starter tasks done</p>'
      + '<div style="height:6px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;margin:0 0 14px"><div style="height:100%;width:' + Math.round(done / TASKS.length * 100) + '%;background:#7CC5A0;transition:width .4s ease"></div></div>'
      + '<ul style="list-style:none;margin:0;padding:0;display:grid;gap:6px">' + TASKS.map(function (t) {
        var on = v.tasks && v.tasks[t[0]];
        return '<li style="display:flex;gap:10px;align-items:center;min-height:44px"><input type="checkbox" data-t="' + t[0] + '"' + (on ? " checked" : "") + ' id="vt-' + t[0] + '" style="width:20px;height:20px;accent-color:#7CC5A0"><label for="vt-' + t[0] + '" style="flex:1;transition:color .2s ease' + (on ? ';color:#9AA0A6;text-decoration:line-through' : '') + '">' + esc(t[1]) + '</label><a href="' + t[2] + '"' + (t[2].indexOf("http") === 0 ? ' rel="noopener" target="_blank"' : '') + '>Go</a></li>';
      }).join("") + '</ul>'
      + '<p class="note" style="margin:14px 0 0">Keep your code if you want us to find your sign-up later. <a href="#" data-a="clear">Remove my sign-up</a> deletes it from arcroad and from this device.</p>';
  }
  var t = null;
  box.addEventListener("change", function (e) {
    var k = e.target.getAttribute("data-t"); if (!k) return; var v = load(); v.tasks = v.tasks || {}; v.tasks[k] = e.target.checked; keep(v); paint(v);
    clearTimeout(t); t = setTimeout(function () { sync(load()); }, 600);
  });
  box.addEventListener("click", function (e) {
    if (!e.target.getAttribute || e.target.getAttribute("data-a") !== "clear") return; e.preventDefault();
    var v = load(); if (v) fetch(API + "?code=" + encodeURIComponent(v.code), { method: "DELETE" }).catch(function () {});
    try { localStorage.removeItem(KEY); } catch (x) {} state = ""; paint(null);
  });
  form.addEventListener("submit", function (e) {
    e.preventDefault(); e.stopImmediatePropagation();
    var v = { code: code(), area: (form.elements.area.value || "").trim().slice(0, 80), help: [], time: form.elements.time.value, tasks: {}, src: "volunteer" };
    Array.prototype.forEach.call(form.querySelectorAll("input[type=checkbox]:checked"), function (c) { v.help.push(c.value); });
    keep(v); sync(v); box.scrollIntoView({ behavior: "smooth", block: "start" });
  }, true);
  var v0 = load(); paint(v0); if (v0 && !v0.synced) sync(v0);
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-9a41d2c7e605");
(function () { var el = document.getElementById("vcount"); if (!el) return;
  fetch("/api/volunteer").then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (j && typeof j.count === "number" && j.count > 0) el.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#7CC5A0;margin-right:8px;vertical-align:middle"></span>' + j.count.toLocaleString("en-IN") + (j.count === 1 ? " person has" : " people have") + " signed up so far. Only the number is shown.";
  }).catch(function () {}); })();
