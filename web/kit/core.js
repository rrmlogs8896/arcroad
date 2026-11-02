/* arcroad representation kit — core logic (v1, 26 Oct 2026).
 *
 * Pure functions only: no DOM, no network, no storage. Everything a citizen
 * generates is built from the pair record and what they type, in their own
 * browser. automated checks runs these functions under Node and scans this
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

  var KIT_VERSION = 'kit-v2';

  // Status decides the watermark printed on every output. Nothing is ever
  // generated without one unless the figure has been checked against a drive.
  var STATUS = {
    verified: { label: 'Verified', watermark: '' },
    candidate: { label: 'Candidate', watermark: 'DRAFT: candidate figure, not for submission' },
    under_review: { label: 'Under review', watermark: 'PREVIEW: figure under review, not for submission' },
    sample: { label: 'Sample', watermark: 'SAMPLE: invented figures for layout, not a real location' },
    // v0.2 public statuses. A modelled figure is sendable but always says how it was made.
    driven: { label: 'Driven by arcroad', watermark: '' },
    modelled: { label: 'Modelled from open map data, not yet driven', watermark: '',
                disclosure: 'These distances are modelled from open map data and have not yet been confirmed by a drive. A median opening the map has not caught up with would make the real trip shorter.' },
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

  // Sourced recipients (officials directory, v0.2) override the road-class category.
  function recipients(pair) {
    var r = pair.recipients || {};
    var a = authority(pair.ref);
    var to = (r.to || []).filter(function (x) { return x && x.designation; });
    return {
      to: to.length ? to : [{ designation: a.to, office: a.office, mailbox: '' }],
      cc: (r.cc || []).filter(function (x) { return x && x.designation; }),
      portals: (r.portals || []).filter(function (x) { return x && x.name; }),
      rti: r.rti || null,
      sourced: to.length > 0,
      note: to.length ? 'Addresses from official websites, checked ' + (r.checked || '') + '.' : a.note,
    };
  }

  function osm(lat, lon) {
    return 'https://www.openstreetmap.org/?mlat=' + Number(lat).toFixed(6) + '&mlon=' + Number(lon).toFixed(6) + '#map=19/' + Number(lat).toFixed(6) + '/' + Number(lon).toFixed(6);
  }

  // Monthly cost of the detour for one resident: every assumption is printed with it.
  var COST = { petrol: 116.15, priceDate: '16 Oct 2026', kmpl: { tw: 45, car: 15 }, trips: 10 };
  function monthlyCost(pair) {
    if (pair.ab == null || pair.ba == null || pair.straight_m == null) return null;
    var extraKm = (pair.ab + pair.ba - 2 * pair.straight_m) / 1000, perMonth = extraKm * COST.trips * 52 / 12;
    return { km: perMonth, tw: perMonth / COST.kmpl.tw * COST.petrol, car: perMonth / COST.kmpl.car * COST.petrol };
  }

  function place(pair) {
    var bits = [];
    if (pair.road) bits.push(pair.road);
    else if (pair.ref) bits.push(pair.ref);
    if (pair.area) bits.push('at ' + pair.area);
    return bits.join(' ');
  }

  function coords(pair) {
    if (pair.lat == null || pair.lon == null) return 'the marked location';
    return Number(pair.lat).toFixed(4) + ', ' + Number(pair.lon).toFixed(4);
  }

  function quickGlance(pair) {
    var s = status(pair);
    if (pair.a && pair.b) {
      var rows = [['Location', place(pair) + (pair.id ? ' (arcroad place ' + pair.id + ')' : '')],
        ['Side A', Number(pair.a[1]).toFixed(5) + ', ' + Number(pair.a[0]).toFixed(5) + '  ' + osm(pair.a[1], pair.a[0])],
        ['Side B', Number(pair.b[1]).toFixed(5) + ', ' + Number(pair.b[0]).toFixed(5) + '  ' + osm(pair.b[1], pair.b[0])],
        ['Straight across', formatDistance(pair.straight_m)]];
      var dv = pair.driven || {};
      var way = function (d) { return pair[d] == null ? 'no legal route found on the map' : (dv[d] ? formatDistance(dv[d].m) + ' driven on ' + dv[d].date + ' (model ' + formatDistance(pair[d]) + ')' : formatDistance(pair[d]) + ' on the mapped network'); };
      rows.push(['By road, side A to B (cars)', way('ab')]);
      rows.push(['By road, side B to A (cars)', way('ba')]);
      if (pair.tw_note) rows.push(['Two-wheelers', pair.tw_note]);
      var c = monthlyCost(pair);
      if (c) rows.push(['Cost to one resident', 'about ' + c.km.toFixed(0) + ' extra km a month at ' + COST.trips + ' round trips a week: about Rs ' + Math.round(c.tw).toLocaleString('en-IN') +
        ' a month in petrol on a two-wheeler, Rs ' + Math.round(c.car).toLocaleString('en-IN') + ' in a car (petrol Rs ' + COST.petrol + '/litre, ' + COST.priceDate + '; ' + COST.kmpl.tw + ' and ' + COST.kmpl.car + ' km a litre)']);
      if (pair.where) rows.push(['Constituency and local body', pair.where]);
      rows.push(['Status of the figure', s.label + (pair.extract_date ? ' (OpenStreetMap extract of ' + pair.extract_date + ')' : '')]);
      rows.push(['Request', 'Examine whether a safe crossing here is feasible under the applicable standards']);
      return rows;
    }
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

  // Draft translations (v0.2): to be reviewed by a native speaker before they are offered publicly.
  // Distances, names and coordinates stay as written; only the sentences change.
  var LANG = {
    hi: {
      dear: 'आदरणीय महोदय/महोदया,',
      subject: function (pl) { return pl + ' पर सुरक्षित क्रॉसिंग की जाँच हेतु अनुरोध'; },
      intro: function (pl, c, a, b) { return 'मैं ' + pl + ' (लगभग ' + c + ') के इस हिस्से के बारे में लिख रहा/रही हूँ। यहाँ सड़क के दोनों ओर के दो बिंदुओं के बीच सीधी दूरी ' + a + ' है, लेकिन मानचित्र पर उपलब्ध सड़क मार्ग से एक ओर से दूसरी ओर जाने में ' + b + ' तक लगते हैं।'; },
      source: function (d, u) { return 'ये आँकड़े arcroad से हैं, जो एक स्वतंत्र नागरिक परियोजना है और खुले मानचित्र डेटा (OpenStreetMap, ' + d + ' का संस्करण) से सड़क की दूरियाँ मापती है। ये दूरी के अनुमान हैं, अभियांत्रिकी या कानूनी निष्कर्ष नहीं। पद्धति यहाँ प्रकाशित है: ' + u; },
      disclosure: 'ये दूरियाँ खुले मानचित्र डेटा से अनुमानित हैं और अभी तक वाहन चलाकर इनकी पुष्टि नहीं हुई है। यदि कोई नया मीडियन ओपनिंग मानचित्र में दर्ज नहीं है, तो वास्तविक दूरी कम हो सकती है।',
      ask: 'मेरा अनुरोध है कि आपका कार्यालय लागू मानकों के अनुसार इस स्थान पर सुरक्षित क्रॉसिंग की संभावना की जाँच करे, और यह विचार करे कि निम्नलिखित में से कोई उपाय उपयुक्त होगा या नहीं:',
      options: ['सिग्नल या अन्य सुरक्षा उपायों के साथ समतल क्रॉसिंग या मीडियन ओपनिंग', 'पैदल पुल (फुट ओवरब्रिज)', 'वाहन या पैदल अंडरपास', 'किसी मौजूदा क्रॉसिंग से सर्विस रोड का जुड़ाव'],
      close: ['कृपया इस विषय में लिए गए निर्णय और इस स्थान पर प्रस्तावित किसी भी कार्य की जानकारी देने की कृपा करें।', 'आपके ध्यान के लिए धन्यवाद।'],
      yours: 'भवदीय,', signature: 'हस्ताक्षर', name: 'हिन्दी',
    },
    te: {
      dear: 'గౌరవనీయులైన అయ్యా/అమ్మా,',
      subject: function (pl) { return pl + ' వద్ద సురక్షితమైన క్రాసింగ్‌ను పరిశీలించాలని విజ్ఞప్తి'; },
      intro: function (pl, c, a, b) { return pl + ' (సుమారు ' + c + ') వద్ద ఉన్న ఈ రహదారి భాగం గురించి నేను రాస్తున్నాను. ఇక్కడ రహదారికి ఇరువైపులా ఉన్న రెండు ప్రదేశాల మధ్య నేరుగా దూరం ' + a + ' మాత్రమే, కానీ మ్యాప్‌లోని రహదారి మార్గంలో ఒక వైపు నుండి మరో వైపుకు వెళ్లడానికి ' + b + ' వరకు ప్రయాణించాల్సి వస్తుంది.'; },
      source: function (d, u) { return 'ఈ గణాంకాలు arcroad నుండి తీసుకున్నవి. ఇది ఓపెన్ మ్యాప్ డేటా (OpenStreetMap, ' + d + ' నాటి వెర్షన్) ఆధారంగా రహదారి దూరాలను కొలిచే స్వతంత్ర పౌర ప్రాజెక్ట్. ఇవి దూరం యొక్క అంచనాలు మాత్రమే, ఇంజనీరింగ్ లేదా చట్టపరమైన నిర్ణయాలు కావు. విధానం ఇక్కడ ప్రచురించబడింది: ' + u; },
      disclosure: 'ఈ దూరాలు ఓపెన్ మ్యాప్ డేటా ఆధారంగా అంచనా వేసినవి, ఇంకా వాహనంలో ప్రయాణించి నిర్ధారించలేదు. మ్యాప్‌లో నమోదు కాని కొత్త మీడియన్ ఓపెనింగ్ ఉంటే, నిజమైన దూరం తక్కువగా ఉండవచ్చు.',
      ask: 'వర్తించే ప్రమాణాల ప్రకారం ఈ ప్రదేశంలో సురక్షితమైన క్రాసింగ్ సాధ్యమేనా అని మీ కార్యాలయం పరిశీలించాలని, ఈ క్రింది వాటిలో ఏదైనా అనుకూలంగా ఉంటుందా అని పరిగణించాలని నేను కోరుతున్నాను:',
      options: ['సిగ్నల్స్ లేదా ఇతర భద్రతా ఏర్పాట్లతో సమతల క్రాసింగ్ లేదా మీడియన్ ఓపెనింగ్', 'పాదచారుల వంతెన (ఫుట్ ఓవర్ బ్రిడ్జ్)', 'వాహనాలు లేదా పాదచారుల కోసం అండర్‌పాస్', 'ఇప్పటికే ఉన్న క్రాసింగ్‌కు సర్వీస్ రోడ్ అనుసంధానం'],
      close: ['ఈ విషయంలో తీసుకున్న నిర్ణయాన్ని, ఈ ప్రదేశంలో ప్రణాళిక చేసిన పనుల వివరాలను నాకు తెలియజేయగలరని కోరుతున్నాను.', 'మీ శ్రద్ధకు ధన్యవాదాలు.'],
      yours: 'భవదీయుడు/భవదీయురాలు,', signature: 'సంతకం', name: 'తెలుగు',
    },
  };

  function letter(pair, who, today, lang) {
    who = who || {};
    var T = LANG[lang] || null;
    var a = authority(pair.ref), R = recipients(pair);
    var s = status(pair);
    var subject = 'Request to examine a safe crossing on ' + place(pair) + ' (near ' + coords(pair) + ')';
    var longest = pair.network_m != null ? pair.network_m : Math.max(pair.ab || 0, pair.ba || 0);
    var body = [
      'Respected Sir or Madam,',
      'I am writing about the stretch of ' + place(pair) + ' near ' + coords(pair) + '. Two points on opposite sides of the road here are ' +
        formatDistance(pair.straight_m) + ' apart. On the mapped road network, travelling from one to the other by vehicle takes up to ' +
        formatDistance(longest) + '.',
      'These figures come from arcroad, an independent citizen project that measures road distances from open map data (OpenStreetMap, extract of ' +
        pair.extract_date + '). They are estimates of distance, not engineering or legal findings. The method is published at ' + pair.evidence_url + '.',
    ];
    if (s.disclosure) body.push(s.disclosure);
    body = body.concat([
      'I request that your office examine whether a safe crossing at this location is feasible under the applicable standards, and consider whether any of the following would be suitable:',
    ]);
    var close = [
      'I would be grateful to be informed of the decision and of any work planned at this location.',
      'Thank you for your attention.',
    ];
    var options = OPTIONS.slice(), yours = 'Yours faithfully,', sig = 'Signature';
    if (T) {
      subject = T.subject(place(pair));
      body = [T.dear, T.intro(place(pair), coords(pair), formatDistance(pair.straight_m), formatDistance(longest)), T.source(pair.extract_date, pair.evidence_url)];
      if (s.disclosure) body.push(T.disclosure);
      body.push(T.ask);
      options = T.options.slice(); close = T.close.slice(); yours = T.yours; sig = T.signature;
    }
    return {
      watermark: s.watermark,
      from: [blank(who.name), blank(who.address), blank(who.phone, 18)],
      date: today,
      to: R.sourced ? R.to.map(function (t) { return [t.designation, t.office].filter(Boolean).join(', '); }).concat(R.to[0].postal ? [R.to[0].postal] : []) : [a.to, a.office, blank('', 34), blank('', 34)],
      authorityNote: R.note,
      subject: subject,
      glance: quickGlance(pair),
      body: body,
      options: options,
      close: close,
      lang: T ? lang : 'en',
      copyTo: R.cc.length ? R.cc.map(function (c) { return [c.designation, c.office].filter(Boolean).join(', '); }) : [
        'The Member of the Legislative Assembly for this constituency',
        'The Member of Parliament for this constituency',
        'The elected representative of the local body for this ward',
      ],
      enclosure: 'Evidence page with the map and the method: ' + pair.evidence_url,
      signoff: [yours, '', blank(who.name), sig + ': ' + blank('', 22)],
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
  function mailto(pair, lang) {
    if (LANG[lang]) {
      var L = letter(pair, {}, '', lang), R2 = recipients(pair), m2 = function (arr) { return arr.map(function (x) { return x.mailbox; }).filter(function (m) { return /^[^\s@,;]+@[^\s@,;]+\.[a-z]{2,}$/i.test(m || ''); }); };
      var t2 = m2(R2.sourced ? R2.to : []), c2 = m2(R2.cc), lines2 = [];
      if (L.watermark) lines2.push('[' + L.watermark + ']', '');
      L.glance.forEach(function (g) { lines2.push(g[0] + ': ' + g[1]); });
      lines2.push(''); lines2 = lines2.concat(L.body, L.options.map(function (o, i) { return '(' + String.fromCharCode(97 + i) + ') ' + o; }), [''], L.close, ['', L.signoff[0]]);
      return 'mailto:' + t2.map(encodeURIComponent).join(',') + '?' + (c2.length ? 'cc=' + c2.map(encodeURIComponent).join(',') + '&' : '') + 'subject=' + encodeURIComponent(L.subject) + '&body=' + encodeURIComponent(lines2.join('\n'));
    }
    var s = status(pair), R = recipients(pair);
    var lines = [];
    if (s.watermark) lines.push('[' + s.watermark + ']', '');
    lines.push('Respected Sir or Madam,', '');
    quickGlance(pair).forEach(function (g) { lines.push(g[0] + ': ' + g[1]); });
    if (s.disclosure) lines.push('', s.disclosure);
    lines.push('', 'I request that your office examine whether a safe crossing at this location is feasible under the applicable standards, and inform me of the decision.',
      '', 'The map, figures and method are at: ' + pair.evidence_url, '', 'Yours faithfully,');
    var subject = 'Request to examine a safe crossing on ' + place(pair);
    var mails = function (arr) { return arr.map(function (x) { return x.mailbox; }).filter(function (m) { return /^[^\s@,;]+@[^\s@,;]+\.[a-z]{2,}$/i.test(m || ''); }); };
    var to = mails(R.sourced ? R.to : []), cc = mails(R.cc);
    return 'mailto:' + to.map(encodeURIComponent).join(',') + '?' + (cc.length ? 'cc=' + cc.map(encodeURIComponent).join(',') + '&' : '') +
      'subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
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
    recipients: recipients,
    LANGS: Object.keys(LANG),
    monthlyCost: monthlyCost,
    osm: osm,
    card: card,
  };
});
