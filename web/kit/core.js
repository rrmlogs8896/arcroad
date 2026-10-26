/* arcroad representation kit — core logic (v1, 26 Oct 2026).
 *
 * Pure functions only: no DOM, no network, no storage. Everything a citizen
 * generates is built from the pair record and what they type, in their own
 * browser. tests/test_kit.py runs these functions under Node and scans this
 * directory for any network or storage call; either failing blocks CI.
 *
 * Ledger: 36.29 (Act on this), 36.30 (representation kit), 36.31
 * (acknowledgement), 36.56 (build step 3; decisions: authority category with
 * blank address lines, PDF + copy text now, no cost figure, English first).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ArcKit = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var KIT_VERSION = 'kit-v1';

  // Status decides the watermark printed on every output. Nothing is ever
  // generated without one unless the figure has been checked against a drive.
  var STATUS = {
    verified: { label: 'Verified', watermark: '' },
    candidate: { label: 'Candidate', watermark: 'DRAFT: candidate figure, not for submission' },
    under_review: { label: 'Under review', watermark: 'PREVIEW: figure under review, not for submission' },
    sample: { label: 'Sample', watermark: 'SAMPLE: invented figures for layout, not a real location' },
  };

  function status(pair) {
    return STATUS[pair.status] || STATUS.under_review; // unknown never reads as verified
  }

  function formatDistance(m) {
    var v = Number(m);
    if (!isFinite(v) || v < 0) return '—';
    if (Math.round(v) < 1000) return Math.round(v) + ' m'; // round first: 999.6 m reads 1.0 km, not 1000 m
    return (Math.round(v / 100) / 10).toFixed(1) + ' km';
  }

  // Who to write to, by road class. Category only: postal addresses come from
  // the officials directory (build step 4) once verified from official sources.
  function authority(ref) {
    var r = String(ref || '').toUpperCase().replace(/\s+/g, '');
    if (/^NH/.test(r)) {
      return {
        key: 'nhai',
        to: 'The Project Director',
        office: 'Project Implementation Unit, National Highways Authority of India',
        note: 'National highway. Find the Project Implementation Unit for this stretch on the official NHAI website.',
      };
    }
    if (/^SH/.test(r)) {
      return {
        key: 'rnb',
        to: 'The Executive Engineer',
        office: 'Roads and Buildings Department, Government of Telangana',
        note: 'State highway. Find the division office on the official Roads and Buildings Department website.',
      };
    }
    return {
      key: 'local',
      to: 'The Commissioner',
      office: 'Municipal body responsible for this road',
      note: 'City or local road. Confirm which body maintains it (GHMC, HMDA or the municipality) before sending.',
    };
  }

  function place(pair) {
    var bits = [];
    if (pair.ref) bits.push(pair.ref);
    if (pair.area) bits.push('at ' + pair.area);
    return bits.join(' ');
  }

  function coords(pair) {
    if (pair.lat == null || pair.lon == null) return 'the marked location';
    return Number(pair.lat).toFixed(4) + ', ' + Number(pair.lon).toFixed(4);
  }

  function quickGlance(pair) {
    var s = status(pair);
    return [
      ['Location', place(pair) + ' (near ' + coords(pair) + ')'],
      ['Distance across the road', formatDistance(pair.straight_m)],
      ['Distance by road', formatDistance(pair.network_m) + ' on the mapped network (OpenStreetMap extract of ' + pair.extract_date + ')'],
      ['Status of the figure', s.label],
      ['Request', 'Examine whether a safe crossing here is feasible under the applicable standards'],
    ];
  }

  // The options are questions for the authority, never prescriptions:
  // engineers decide under the applicable standards (36.29 item 4).
  var OPTIONS = [
    'an at-grade crossing or median opening with signals or other safety measures',
    'a foot overbridge',
    'a vehicular or pedestrian underpass',
    'a service-road connection to an existing crossing',
  ];

  function blank(v, width) {
    var s = String(v || '').trim();
    return s ? s : new Array(width || 28).join('_');
  }

  function letter(pair, who, today) {
    who = who || {};
    var a = authority(pair.ref);
    var s = status(pair);
    var subject = 'Request to examine a safe crossing on ' + place(pair) + ' (near ' + coords(pair) + ')';
    var body = [
      'Respected Sir or Madam,',
      'I am writing about the stretch of ' + place(pair) + ' near ' + coords(pair) + '. Two points on opposite sides of the road here are ' +
        formatDistance(pair.straight_m) + ' apart. On the mapped road network, travelling from one to the other by vehicle takes ' +
        formatDistance(pair.network_m) + '.',
      'These figures come from arcroad, an independent citizen project that measures road distances from open map data (OpenStreetMap, extract of ' +
        pair.extract_date + '). They are estimates of distance, not engineering or legal findings. The method is published at ' + pair.evidence_url + '.',
      'I request that your office examine whether a safe crossing at this location is feasible under the applicable standards, and consider whether any of the following would be suitable:',
    ];
    var close = [
      'I would be grateful to be informed of the decision and of any work planned at this location.',
      'Thank you for your attention.',
    ];
    return {
      watermark: s.watermark,
      from: [blank(who.name), blank(who.address), blank(who.phone, 18)],
      date: today,
      to: [a.to, a.office, blank('', 34), blank('', 34)],
      authorityNote: a.note,
      subject: subject,
      glance: quickGlance(pair),
      body: body,
      options: OPTIONS.slice(),
      close: close,
      copyTo: [
        'The Member of the Legislative Assembly for this constituency',
        'The Member of Parliament for this constituency',
        'The elected representative of the local body for this ward',
      ],
      enclosure: 'Evidence page with the map and the method: ' + pair.evidence_url,
      signoff: ['Yours faithfully,', '', blank(who.name), 'Signature: ' + blank('', 22)],
      footer: 'Prepared with the arcroad representation kit (' + KIT_VERSION + '). Figures: ' + s.label.toLowerCase() +
        ', OpenStreetMap extract ' + pair.extract_date + ', build ' + pair.commit + '. Map data © OpenStreetMap contributors (ODbL).',
    };
  }

  function letterText(L) {
    var out = [];
    if (L.watermark) out.push('[' + L.watermark + ']', '');
    out.push('From:'); out = out.concat(L.from); out.push('', 'Date: ' + L.date, '', 'To:'); out = out.concat(L.to);
    out.push('', 'Subject: ' + L.subject, '');
    L.glance.forEach(function (g) { out.push(g[0] + ': ' + g[1]); });
    out.push('');
    out = out.concat(L.body.map(function (p) { return p + '\n'; }));
    L.options.forEach(function (o, i) { out.push('(' + String.fromCharCode(97 + i) + ') ' + o); });
    out.push('');
    out = out.concat(L.close.map(function (p) { return p + '\n'; }));
    out = out.concat(L.signoff);
    out.push('', 'Copy to:');
    L.copyTo.forEach(function (c, i) { out.push((i + 1) + '. ' + c); });
    out.push('', 'Enclosure: ' + L.enclosure, '', L.footer);
    return out.join('\n');
  }

  // A mailto link carries no attachments and no recipient until the officials
  // directory verifies one. Kept short: some mail apps truncate long bodies.
  function mailto(pair) {
    var s = status(pair);
    var lines = [];
    if (s.watermark) lines.push('[' + s.watermark + ']', '');
    lines.push('Respected Sir or Madam,', '');
    quickGlance(pair).forEach(function (g) { lines.push(g[0] + ': ' + g[1]); });
    lines.push('', 'The map, figures and method are at: ' + pair.evidence_url, '', 'Yours faithfully,');
    var subject = 'Request to examine a safe crossing on ' + place(pair);
    return 'mailto:?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
  }

  function card(pair) {
    var s = status(pair);
    return {
      across: formatDistance(pair.straight_m) + ' across.',
      byRoad: formatDistance(pair.network_m) + ' by road.',
      where: place(pair),
      status: s.label,
      watermark: s.watermark,
      meta: 'OpenStreetMap extract ' + pair.extract_date + ' · arcroad',
      credit: 'Map data © OpenStreetMap contributors (ODbL). Schematic, not to scale.',
    };
  }

  return {
    KIT_VERSION: KIT_VERSION,
    status: status,
    formatDistance: formatDistance,
    authority: authority,
    quickGlance: quickGlance,
    letter: letter,
    letterText: letterText,
    mailto: mailto,
    card: card,
  };
});
