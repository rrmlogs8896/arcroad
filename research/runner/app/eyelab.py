"""Weekly research scan for 13point8: colour, visual speed, the visual brain and why people return.

Approved by Rohit on 15 Nov 2026, with a hard cap of USD 5 a month.

Runs on Saturday nights, one theme per run in rotation, as a single Claude request with web search.
The cap is held in two places (same pattern as viability.py):
  1. the API key: EYELAB_API_KEY belongs to its own Claude Console workspace, whose monthly spend limit
     is set to USD 5. Anthropic refuses requests above it. This is the real cap.
  2. this file: each run stops at RUN_BUDGET_USD, so at most 5 Saturdays a month stay under USD 4.50.
It never falls back to the nightly ANTHROPIC_API_KEY: without its own key it does nothing.

It researches public, peer-reviewed literature only. Nothing about 13point8's visitors, code or plans goes into
a search query. It contacts no one and sends nothing. Every claim needs a source link, and it keeps to the
standing rule that 13point8 does not use addictive-design patterns (variable rewards, streaks, infinite autoplay).
The full first report is the doc "What the eye craves: research for 13point8" (15 Nov 2026).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request

ANTHROPIC = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5-5"
MAX_SEARCHES = 10
MAX_TOKENS = 6000
RUN_BUDGET_USD = 0.90
MAX_TURNS = 3
PRICE_IN, PRICE_OUT, PRICE_SEARCH = 3.0, 15.0, 0.01

THEMES = [
    ("colour", "New peer-reviewed work (last 18 months first) on colour and emotion, arousal and preference: hue, "
               "saturation, lightness, colour on dark backgrounds and screens, cross-cultural and Indian findings, "
               "and replications or failed replications of well-known colour effects."),
    ("speed", "New peer-reviewed work on how fast people grasp images and judge visual appeal, interaction latency "
              "and perceived smoothness (frame rate, input delay, motion), and first impressions of web pages."),
    ("brain", "New peer-reviewed work in neuroaesthetics: which brain areas respond to visual beauty, scale, depth, "
              "motion and awe (especially space and nature imagery), and how pleasure changes with repetition."),
    ("return", "New peer-reviewed work on curiosity, novelty and intrinsic motivation in learning and digital "
               "experiences, and on ethical engagement versus addictive design. Include findings that cut against "
               "engagement tactics."),
]

SYSTEM = (
    "You are a research assistant for 13point8, an independent educational website of 3D space journeys "
    "(planets, a black hole, Voyager), dark interface with one gold accent. You research only, from public "
    "sources. Prefer peer-reviewed papers, reviews and meta-analyses; label preprints, theory articles and "
    "industry guidance as such. Every factual line needs a source URL; if you cannot source it, leave it out or "
    "mark it UNVERIFIED. Report effect sizes and sample sizes where given, and say when a finding failed to "
    "replicate. Never recommend addictive-design patterns (variable rewards, streaks, infinite autoplay, guilt "
    "prompts); if a finding points that way, say so and give the healthy alternative. Output: at most 500 words: "
    "what is new this week with sources; whether any of it changes the standing recommendations (mark PROPOSAL); "
    "and one small, testable change for the site. If a finding justifies a new or changed colour palette, end "
    "with a line PALETTE PROPOSAL: name; five hex colours in the order background, surface, text, muted, accent; "
    "the feeling it targets; the source URL. The 13point8 palette library adds it after review."
)

RUN_DAYS = (5,)  # Saturday; the night starts at 16:30 UTC (22:00 IST), so the UTC date is the IST date.


def is_run_day(day: dt.date) -> bool:
    return day.weekday() in RUN_DAYS


def theme_for(day: dt.date):
    return THEMES[(day.toordinal() // 7) % len(THEMES)]


def previous_run_day(day: dt.date) -> dt.date:
    d = day - dt.timedelta(days=1)
    while not is_run_day(d):
        d -= dt.timedelta(days=1)
    return d


def cost(usage: dict) -> float:
    searches = (usage.get("server_tool_use") or {}).get("web_search_requests", 0)
    tokens_in = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + \
        usage.get("cache_read_input_tokens", 0)
    return tokens_in / 1e6 * PRICE_IN + usage.get("output_tokens", 0) / 1e6 * PRICE_OUT + searches * PRICE_SEARCH


def _post(key, body):
    req = urllib.request.Request(ANTHROPIC, data=json.dumps(body).encode(), headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}") from None


def _text(content):
    return "".join(b.get("text", "") for b in content if b.get("type") == "text").strip()


def _sources(content):
    seen = []
    for b in content:
        for c in b.get("citations") or []:
            u = c.get("url")
            if u and u not in seen:
                seen.append(u)
    return seen


def run(log, previous: str = "", today: dt.date | None = None, post=_post) -> bytes:
    today = today or dt.datetime.now(dt.UTC).date()
    out = {"job": "eyelab", "version": 1, "date": today.isoformat(), "model": MODEL}
    key = os.environ.get("EYELAB_API_KEY", "")
    if not key:
        log("eyelab: no EYELAB_API_KEY, skipped (it never uses the nightly key)")
        return json.dumps({**out, "status": "SKIPPED", "reason": "no key"}, indent=1).encode()
    name, ask = theme_for(today)
    prompt = f"This week's theme: {name}.\n\n{ask}"
    if previous:
        prompt += "\n\nLast week's brief is below. Do not repeat it.\n\n" + previous[:3000]
    messages = [{"role": "user", "content": prompt}]
    body = {"model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM, "messages": messages,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}]}
    spent, content, stop = 0.0, [], None
    for turn in range(MAX_TURNS):
        r = post(key, body)
        spent += cost(r.get("usage") or {})
        content += r.get("content") or []
        stop = r.get("stop_reason")
        log(f"eyelab: turn {turn + 1}, stop {stop}, about ${spent:.2f}")
        if stop != "pause_turn" or spent >= RUN_BUDGET_USD:
            break
        messages.append({"role": "assistant", "content": r.get("content") or []})
    brief = _text(content)
    status = "OK" if brief and stop == "end_turn" else ("STOPPED_AT_BUDGET" if spent >= RUN_BUDGET_USD else "PARTIAL")
    return json.dumps({**out, "status": status, "theme": name, "estimated_cost_usd": round(spent, 3),
                       "brief": brief, "sources": _sources(content)}, indent=1).encode()
