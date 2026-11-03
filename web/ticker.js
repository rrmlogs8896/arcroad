/* One crossing, one person: what crossing S18 costs a year at the rate we drove it.
   A static figure, not a running counter: we do not know how long this crossing has been closed,
   so nothing is counted "since" any date. Every input is measured or stated; no network, no storage.
   Fuel figures match the cost calculator (web/cost/): petrol Rs 116.15/litre (16 Oct 2026), 50 and 16 km a litre. */
(function () {
  'use strict';
  var root = document.getElementById('ticker');
  if (!root) return;
  var DRIVE = { ab: { m: 1579.5, s: 193 }, ba: { m: 1546.0, s: 692 }, straight: 13.1 };   // data/field/2026-11-01-results.json
  var COST = { petrol: 116.15, kmpl: { tw: 50, car: 16 }, daysPerYear: 22 * 12 };
  var extraKm = (DRIVE.ab.m + DRIVE.ba.m - 2 * DRIVE.straight) / 1000;   // per round trip
  var minutes = (DRIVE.ab.s + DRIVE.ba.s) / 60;                           // per round trip, as driven
  var veh = 'tw';
  var $ = function (id) { return root.querySelector('#' + id); };
  var inr = function (n) { return '₹' + Math.round(n).toLocaleString('en-IN'); };
  function draw() {
    var day = extraKm / COST.kmpl[veh] * COST.petrol, d = COST.daysPerYear;
    $('t-rs').textContent = inr(day * d);
    $('t-h').textContent = Math.round(minutes * d / 60).toLocaleString('en-IN');
    $('t-km').textContent = Math.round(extraKm * d).toLocaleString('en-IN');
    $('t-day').textContent = inr(day) + ' and ' + Math.round(minutes) + ' minutes';
  }
  Array.prototype.forEach.call(root.querySelectorAll('button[data-v]'), function (b) {
    b.addEventListener('click', function () {
      veh = b.getAttribute('data-v');
      Array.prototype.forEach.call(root.querySelectorAll('button[data-v]'), function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      draw();
    });
  });
  draw();
})();
