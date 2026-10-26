/* arcroad representation kit — page behaviour (v1).
 * DOM and canvas only. No network, no storage: tests/test_kit.py enforces it.
 * Text from the pair record and the form is always set with textContent.
 */
(function () {
  'use strict';
  var K = window.ArcKit;
  var $ = function (id) { return document.getElementById(id); };
  var params = new URLSearchParams(location.search);

  // Feature flag: the kit stays closed unless the staging flag is set.
  if (params.get('kit') !== '1') { $('off').hidden = false; return; }

  var pairs = window.ARCROAD_PAIRS || {};
  var pair = pairs[params.get('pair') || 'sample'];
  if (!pair) { $('off').hidden = false; $('off').querySelector('p').textContent = 'That location is not in the kit yet.'; return; }

  var st = K.status(pair);
  var a = K.authority(pair.ref);
  $('lede').hidden = false; $('steps').hidden = false;
  $('across').textContent = K.formatDistance(pair.straight_m) + ' across.';
  $('byroad').textContent = K.formatDistance(pair.network_m) + ' by road.';
  $('where').textContent = 'Two points on opposite sides of ' + [pair.ref, pair.area ? 'at ' + pair.area : ''].join(' ').trim() +
    '. Getting from one to the other on the mapped road network takes the longer distance.';
  $('f-road').textContent = pair.ref || '—';
  $('f-extract').textContent = pair.extract_date;
  $('f-status').textContent = st.label;
  $('f-status').classList.add(pair.status in { verified: 1, candidate: 1, under_review: 1, sample: 1 } ? pair.status : 'under_review');
  if (st.watermark) { $('mark').hidden = false; $('mark').textContent = st.watermark + '. Every output carries this line.'; }
  $('authnote').textContent = 'Addressed to: ' + a.to + ', ' + a.office + '. ' + a.note;

  var outs = ['b-letter', 'b-email', 'b-card'];
  function setStep(id, state) { var el = $(id); el.classList.remove('cur', 'done'); if (state) el.classList.add(state); }
  $('ack').addEventListener('change', function () {
    var on = $('ack').checked;
    outs.forEach(function (b) { $(b).disabled = !on; });
    setStep('s1', on ? 'done' : 'cur'); setStep('s2', on ? 'cur' : ''); setStep('s3', on ? 'cur' : '');
    if (!on) { $('pv-letter').hidden = true; $('pv-card').hidden = true; }
  });

  function who() { return { name: $('who-name').value, address: $('who-addr').value, phone: $('who-phone').value }; }
  function today() { return new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function lines(parent, arr) { arr.forEach(function (t, i) { if (i) parent.appendChild(document.createElement('br')); parent.appendChild(document.createTextNode(t)); }); }
  function say(t) { $('msg').textContent = t; }

  var current = null;
  function renderLetter() {
    var L = K.letter(pair, who(), today());
    current = L;
    var p = $('letter'); p.replaceChildren();
    if (L.watermark) p.appendChild(el('div', 'wm', L.watermark));
    var from = el('p', 'blk'); from.appendChild(el('span', 'lab', 'From')); from.appendChild(document.createElement('br')); lines(from, L.from); p.appendChild(from);
    p.appendChild(el('p', 'blk', 'Date: ' + L.date));
    var to = el('p', 'blk'); to.appendChild(el('span', 'lab', 'To')); to.appendChild(document.createElement('br')); lines(to, L.to); p.appendChild(to);
    p.appendChild(el('p', 'blk subj', 'Subject: ' + L.subject));
    var t = el('table'); L.glance.forEach(function (g) { var tr = el('tr'); tr.appendChild(el('td', null, g[0])); tr.appendChild(el('td', null, g[1])); t.appendChild(tr); }); p.appendChild(t);
    L.body.forEach(function (b) { p.appendChild(el('p', 'blk', b)); });
    var ol = el('ol'); ol.setAttribute('type', 'a'); L.options.forEach(function (o) { ol.appendChild(el('li', null, o)); }); p.appendChild(ol);
    L.close.forEach(function (c) { p.appendChild(el('p', 'blk', c)); });
    var so = el('p', 'blk'); lines(so, L.signoff); p.appendChild(so);
    var cc = el('p', 'blk'); cc.appendChild(el('span', 'lab', 'Copy to')); var ccl = el('ol'); L.copyTo.forEach(function (c) { ccl.appendChild(el('li', null, c)); }); p.appendChild(cc); p.appendChild(ccl);
    p.appendChild(el('p', 'blk', 'Enclosure: ' + L.enclosure));
    p.appendChild(el('p', 'foot', L.footer));
    $('pv-letter').hidden = false; $('pv-card').hidden = true;
    setStep('s3', 'done');
    $('pv-letter').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }
  $('b-letter').addEventListener('click', renderLetter);
  ['who-name', 'who-addr', 'who-phone'].forEach(function (id) { $(id).addEventListener('input', function () { if (!$('pv-letter').hidden) renderLetter(); }); });
  $('b-print').addEventListener('click', function () { window.print(); });
  $('b-copy').addEventListener('click', function () {
    var text = K.letterText(current || K.letter(pair, who(), today()));
    var done = function () { say('Copied.'); };
    var fallback = function () {
      var ta = el('textarea'); ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { say('Select the letter text and copy it by hand.'); }
      ta.remove();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  });

  $('b-email').addEventListener('click', function () {
    say('Your mail app should open. The office address is left for you to add, and attachments cannot be added this way: the email links to the evidence page instead.');
    window.location.href = K.mailto(pair);
  });

  function drawCard() {
    var c = K.card(pair), cv = $('card'), g = cv.getContext('2d'), W = 1080, H = 1350;
    var css = getComputedStyle(document.documentElement);
    var col = function (n) { return css.getPropertyValue(n).trim(); };
    g.fillStyle = col('--bg'); g.fillRect(0, 0, W, H);
    g.textBaseline = 'alphabetic';
    g.fillStyle = col('--fg2'); g.font = '600 44px Inter, system-ui, sans-serif'; g.fillText('arcroad', 90, 140);
    g.fillStyle = col('--faint'); g.font = '400 30px Inter, system-ui, sans-serif'; g.fillText('Hyderabad', 290, 140);
    g.fillStyle = col('--fg2'); g.font = '600 118px Inter, system-ui, sans-serif'; g.fillText(c.across, 90, 380);
    g.fillStyle = col('--accent'); g.fillText(c.byRoad, 90, 520);
    g.fillStyle = col('--mut'); g.font = '400 40px Inter, system-ui, sans-serif'; g.fillText(c.where, 90, 600);
    // schematic: two points close together, and the long way round
    var y = 830, x1 = 470, x2 = 610;
    g.strokeStyle = col('--mut'); g.lineWidth = 4; g.setLineDash([2, 16]); g.lineCap = 'round';
    g.beginPath(); g.moveTo(x1, y); g.bezierCurveTo(x1 - 330, y + 260, x2 + 330, y + 260, x2, y); g.stroke(); g.setLineDash([]);
    g.strokeStyle = col('--accent'); g.lineWidth = 4; g.beginPath(); g.moveTo(x1 + 18, y); g.lineTo(x2 - 18, y); g.stroke();
    [x1, x2].forEach(function (x) { g.fillStyle = col('--fg2'); g.beginPath(); g.arc(x, y, 14, 0, Math.PI * 2); g.fill(); });
    g.fillStyle = col('--faint'); g.font = '400 28px "JetBrains Mono", monospace'; g.fillText(c.status.toUpperCase() + ' · ' + c.meta, 90, 1150);
    g.font = '400 24px Inter, system-ui, sans-serif'; g.fillText(c.credit, 90, 1196);
    if (c.watermark) {
      g.fillStyle = '#2A1A10'; g.fillRect(0, 1240, W, 110);
      g.fillStyle = col('--soft'); g.font = '500 28px "JetBrains Mono", monospace'; g.fillText(c.watermark.toUpperCase(), 90, 1305);
    }
    $('b-save').href = cv.toDataURL('image/png');
  }
  $('b-card').addEventListener('click', function () {
    var go = function () { drawCard(); $('pv-card').hidden = false; $('pv-letter').hidden = true; setStep('s3', 'done'); $('pv-card').scrollIntoView(); };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(go); else go();
  });
})();
