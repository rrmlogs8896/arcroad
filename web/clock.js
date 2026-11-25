/* Detour clock: a live estimate that runs only in this browser, from the cost calculator's own example.
   50,000 petrol two-wheeler commuters, a 1.75 km detour twice a day, 300 days: Rs 63.5 crore and 2,426 tonnes
   of CO2 a year (web/cost/), spread evenly over the year. Nothing is sent or stored; it starts at zero on every visit. */
(function () {
  "use strict";
  var el = document.getElementById("clock");
  if (!el) return;
  var RS_PER_S = 635000000 / (365 * 86400), G_PER_S = 2426e6 / (365 * 86400);
  el.innerHTML = '<span class="ck-dot" aria-hidden="true"></span><span><b>Live estimate.</b> Since you opened this page, a city group of 50,000 two-wheeler commuters has spent about <b class="ck-rs">₹0</b> and <b class="ck-co">0 kg</b> of CO₂ on detours like these. <a href="/cost/">How it is worked out</a></span>';
  var rs = el.querySelector(".ck-rs"), co = el.querySelector(".ck-co"), t0 = Date.now();
  function tick() {
    var s = (Date.now() - t0) / 1000;
    rs.textContent = "₹" + Math.round(s * RS_PER_S).toLocaleString("en-IN");
    var g = s * G_PER_S; co.textContent = g < 1000 ? Math.round(g) + " g" : (g / 1000).toFixed(1) + " kg";
  }
  tick(); setInterval(function () { if (!document.hidden) tick(); }, 1000);
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-98cb123c311f");
