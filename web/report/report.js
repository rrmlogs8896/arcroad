/* Report a change: built in the browser, sent from the citizen's own email. No storage, no network. */
(function () {
  'use strict';
  var REPORT_TO = ''; // set to the project address once hello@arcroad.org is live
  var $ = function (id) { return document.getElementById(id); };
  var pos = null;
  function text() {
    var lines = ['Report to arcroad', '', 'What changed: ' + ($('what').value || '(not chosen)'), 'Road and landmark: ' + ($('road').value || '(not given)'),
      'Noticed on: ' + ($('when').value || '(not given)')];
    if (pos) lines.push('Location: ' + pos.lat.toFixed(5) + ', ' + pos.lon.toFixed(5) + ' (accuracy about ' + Math.round(pos.acc) + ' m)',
      'Map: https://www.openstreetmap.org/?mlat=' + pos.lat.toFixed(6) + '&mlon=' + pos.lon.toFixed(6) + '#map=19/' + pos.lat.toFixed(6) + '/' + pos.lon.toFixed(6));
    if ($('more').value.trim()) lines.push('', 'Details: ' + $('more').value.trim());
    lines.push('', 'Sent from the arcroad report form.');
    return lines.join('\n');
  }
  function render() { $('out').textContent = text(); }
  ['what', 'road', 'when', 'more'].forEach(function (id) { $(id).addEventListener('input', render); });
  $('geo').addEventListener('click', function () {
    if (!navigator.geolocation) { $('loc').textContent = 'Location is not available in this browser'; return; }
    $('loc').textContent = 'Finding you…';
    navigator.geolocation.getCurrentPosition(function (p) {
      pos = { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy };
      $('loc').textContent = pos.lat.toFixed(5) + ', ' + pos.lon.toFixed(5) + ' · about ' + Math.round(pos.acc) + ' m'; render();
    }, function () { $('loc').textContent = 'Location not shared. Describe the landmark instead.'; }, { enableHighAccuracy: true, timeout: 15000 });
  });
  $('f').addEventListener('submit', function (e) {
    e.preventDefault();
    if (!$('what').value) { $('msg').textContent = 'Choose what changed first.'; $('what').focus(); return; }
    render();
    $('msg').textContent = REPORT_TO ? 'Your mail app should open. Attach a photo there if you have one.' : 'Your mail app should open. arcroad\'s address goes live very soon; until then, copy the report and keep it.';
    location.href = 'mailto:' + REPORT_TO + '?subject=' + encodeURIComponent('arcroad report: ' + $('what').value) + '&body=' + encodeURIComponent(text());
  });
  $('copy').addEventListener('click', function () {
    render();
    var t = text();
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { $('msg').textContent = 'Copied.'; }, function () { $('msg').textContent = 'Select the report and copy it by hand.'; });
    else $('msg').textContent = 'Select the report and copy it by hand.';
  });
  render();
})();
;(globalThis.__ar=globalThis.__ar||[]).push("ar-b48ce5796622");
