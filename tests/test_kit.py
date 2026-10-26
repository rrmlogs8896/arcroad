"""Representation kit v1 (web/act.html, web/kit/): guards that must hold for it to ship.

1. Nothing a citizen types leaves their browser: the kit's code makes no
   network call and touches no storage (ledger 36.30, 36.31).
2. Every non-verified figure carries its watermark on every output.
3. The letter states facts and asks; it never characterises anyone's motives
   (AGENTS.md, "Nothing about intent").
4. The public repository holds no real individual figure before the
   verification gate (AGENTS.md, "No absolute Detour Index value").

The behaviour checks run core.js under Node; CI runners have it. Without Node
they are skipped locally, but the static guards always run.
"""

import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
KIT_FILES = [*sorted((WEB / "kit").glob("*.js")), WEB / "act.html"]

FORBIDDEN = [
    r"\bfetch\s*\(",
    r"XMLHttpRequest",
    r"sendBeacon",
    r"WebSocket",
    r"EventSource",
    r"localStorage",
    r"sessionStorage",
    r"indexedDB",
    r"document\.cookie",
    r"clipboard\.read",
    r"\bimport\s*\(",
    r"new\s+Image\s*\(",
    r"geolocation",
]


def test_kit_files_exist():
    names = {p.name for p in KIT_FILES}
    assert {"core.js", "act.js", "pairs.js", "act.html"} <= names


@pytest.mark.parametrize("path", KIT_FILES, ids=lambda p: p.name)
def test_kit_makes_no_network_or_storage_call(path):
    text = path.read_text()
    hits = [pat for pat in FORBIDDEN if re.search(pat, text)]
    assert not hits, f"{path.name} uses {hits}: the kit must not send or store anything"


def test_act_page_loads_only_its_own_scripts():
    html = (WEB / "act.html").read_text()
    srcs = re.findall(r'<script[^>]*\bsrc="([^"]+)"', html)
    assert srcs, "act.html loads no scripts"
    assert all(not re.match(r"^[a-z]+:|^//", s) for s in srcs), f"external script in act.html: {srcs}"


NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")

PROBE = r"""
const K = require(process.argv[1] + '/web/kit/core.js');
const vm = require('vm'); const fs = require('fs');
const ctx = { window: {} }; vm.runInNewContext(fs.readFileSync(process.argv[1] + '/web/kit/pairs.js', 'utf8'), ctx);
const base = { ref: 'NH65', area: 'Sample Nagar', lat: 17.5, lon: 78.2, straight_m: 21, network_m: 2344,
               extract_date: '2026-10-25', commit: 'abc1234', evidence_url: 'https://arcroad.org/#method' };
const out = {};
for (const s of ['verified', 'candidate', 'under_review', 'sample', 'bogus']) {
  const p = Object.assign({}, base, { status: s });
  out[s] = { text: K.letterText(K.letter(p, {}, '26 October 2026')), mail: decodeURIComponent(K.mailto(p)), card: K.card(p) };
}
out.fmt = [K.formatDistance(21), K.formatDistance(999.6), K.formatDistance(2344), K.formatDistance(-1), K.formatDistance('x')];
out.auth = [K.authority('NH65').key, K.authority('nh 44').key, K.authority('SH1').key, K.authority('').key];
out.pairs = Object.values(ctx.window.ARCROAD_PAIRS).map(p => p.status);
out.who = K.letterText(K.letter(Object.assign({}, base, { status: 'verified' }), { name: 'A Citizen' }, 'x'));
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def probe():
    if NODE is None:
        pytest.skip("node not installed")
    res = subprocess.run([NODE, "-e", PROBE, str(ROOT)], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


@needs_node
def test_distances_format_for_reading(probe):
    assert probe["fmt"] == ["21 m", "1.0 km", "2.3 km", "—", "—"]


@needs_node
def test_authority_follows_road_class(probe):
    assert probe["auth"] == ["nhai", "nhai", "rnb", "local"]


@needs_node
@pytest.mark.parametrize("status", ["candidate", "under_review", "sample", "bogus"])
def test_unverified_figure_is_watermarked_everywhere(probe, status):
    o = probe[status]
    assert "not for submission" in o["text"] or "not a real location" in o["text"]
    assert o["card"]["watermark"] and o["card"]["watermark"] in o["text"]
    assert o["card"]["watermark"] in o["mail"]


@needs_node
def test_unknown_status_never_reads_as_verified(probe):
    assert "Verified" not in probe["bogus"]["text"]
    assert probe["bogus"]["card"]["status"] != "Verified"


@needs_node
def test_verified_figure_carries_no_watermark(probe):
    assert probe["verified"]["card"]["watermark"] == ""
    assert "not for submission" not in probe["verified"]["text"]


@needs_node
def test_letter_states_extract_date_status_and_method(probe):
    t = probe["candidate"]["text"]
    for needle in ["2026-10-25", "Candidate", "https://arcroad.org/#method", "© OpenStreetMap contributors (ODbL)", "21 m", "2.3 km"]:
        assert needle in t, needle


INTENT_WORDS = ["negligen", "corrupt", "callous", "apath", "failed to", "failure of", "illegal", "unlawful",
                "deliberate", "demand", "must immediately", "shame", "incompeten", "careless"]


@needs_node
@pytest.mark.parametrize("status", ["verified", "candidate"])
def test_letter_never_characterises_intent(probe, status):
    t = (probe[status]["text"] + probe[status]["mail"]).lower()
    hits = [w for w in INTENT_WORDS if w in t]
    assert not hits, f"letter wording implies intent or blame: {hits}"


@needs_node
def test_typed_details_appear_only_where_put(probe):
    assert probe["who"].count("A Citizen") == 2  # From block and signature, nowhere else


@needs_node
def test_public_pairs_are_samples_until_the_gate_opens(probe):
    assert probe["pairs"] and all(s == "sample" for s in probe["pairs"]), (
        "web/kit/pairs.js holds a non-sample pair: no real individual figure is published before the verification gate"
    )


# Regression, 26 Oct 2026: the page's own `display:flex` on .preview beat the
# `hidden` attribute, so the card panel and its Save button showed under the
# letter on phones.
def test_hidden_sections_stay_hidden_despite_display_rules():
    css = (WEB / "act.html").read_text()
    assert "[hidden]{display:none!important}" in css.replace(" ", "")


# Regression, 26 Oct 2026: 999.6 m printed as "1000 m" because the unit was
# chosen before rounding.
@needs_node
def test_999_6_m_reads_1_0_km_not_1000_m(probe):
    assert probe["fmt"][1] == "1.0 km"
