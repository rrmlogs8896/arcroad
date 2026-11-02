/* Live cost ticker (prototype, 3 Nov 2026). One person, one crossing, honest numbers only.
   Every input is a measured or stated figure; nothing is estimated for the city. No network, no storage. */
(function () {
  'use strict';
  var root = document.getElementById('ticker');
  if (!root) return;
  // S18, HITEC City-Kukatpally Main Road at APHB Colony: driven by arcroad on 1 Nov 2026 (field page).
  var DRIVE = { ab: { m: 1579.5, s: 193 }, ba: { m: 1546.0, s: 692 }, straight: 13.1 };
  // Same constants as the representation kit (web/kit/core.js): petrol Rs 116.15/litre on 16 Oct 2026.
  var COST = { petrol: 116.15, kmpl: { tw: 45, car: 15 } };
  var extraKm = (DRIVE.ab.m + DRIVE.ba.m - 2 * DRIVE.straight) / 1000;        // per round trip
  var minutes = (DRIVE.ab.s + DRIVE.ba.s) / 60;                                // per round trip, as driven
  var veh = 'tw';
  var perDay = function () { return extraKm / COST.kmpl[veh] * COST.petrol; };  // one round trip a day
  var $ = function (id) { return root.querySelector('#' + id); };
  var inr = function (n) { return '₹' + Math.round(n).toLocaleString('en-IN'); };
  var start = new Date(new Date().getFullYear(), 0, 1).getTime();
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function draw() {
    var days = (Date.now() - start) / 864e5;
    $('t-rs').textContent = inr(perDay() * days);
    $('t-h').textContent = Math.floor(minutes * days / 60).toLocaleString('en-IN');
    $('t-km').textContent = Math.round(extraKm * days).toLocaleString('en-IN');
    $('t-day').textContent = inr(perDay()) + ' and ' + Math.round(minutes) + ' minutes a day';
    $('t-year').textContent = inr(perDay() * 365) + ' and ' + Math.round(minutes * 365 / 60) + ' hours a year';
  }
  root.querySelectorAll('button[data-v]').forEach(function (b) {
    b.addEventListener('click', function () {
      veh = b.getAttribute('data-v');
      root.querySelectorAll('button[data-v]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      draw();
    });
  });
  draw();
  if (!reduce) setInterval(draw, 1000);
})();
