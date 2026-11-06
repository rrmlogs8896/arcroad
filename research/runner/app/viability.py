"""Weekly viability research: how arcroad can last, reach the people who can act on it, and pay its way.

Approved by Rohit on 6 Nov 2026, with a hard cap of USD 10 a month.

Runs three nights a week (Sunday, Tuesday, Thursday; 6 Nov 2026, "time is of the essence"), one theme per run in rotation, as a single Claude request with web search.
The cap is held in two places:
  1. the API key: VIABILITY_API_KEY belongs to its own Claude Console workspace, whose monthly spend limit
     is set to USD 10. Anthropic refuses requests above it. This is the real cap.
  2. this file: each run stops at RUN_BUDGET_USD (estimated from the usage the API reports), so the at most 14 run nights in a month
     stay under the cap before the workspace limit is ever reached.
It never falls back to the nightly ANTHROPIC_API_KEY: without its own key it does nothing.

It is tied to the constitution and the secret sauce: each run reads AGENT-BRIEF.md (the condensed
constitution and standing rules) and SECRET-SAUCE.md from arcroad-internal and works inside them. Its briefs
are filed only to arcroad-internal (nights/<date>/viability.json), because which ideas pay is secret sauce.
Nothing private goes into a search query: searches name public topics only.

It researches only. It contacts no one, sends nothing, signs up for nothing, and names organisations and
public roles, never private individuals. Every claim needs a source link. Ideas that would let money change
a finding are out of scope (AGENTS.md, the five reporting rules).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request

ANTHROPIC = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5-5"
MAX_SEARCHES = 8
MAX_TOKENS = 4000
RUN_BUDGET_USD = 0.70
MAX_TURNS = 3  # the API pauses long searches with stop_reason "pause_turn"; we continue at most this often
# Conservative assumed prices, USD per million tokens and per search. The Console limit is the real cap; these
# only stop a run early. If the actual price is lower, the run simply stops sooner than it needs to.
PRICE_IN, PRICE_OUT, PRICE_SEARCH = 3.0, 15.0, 0.01

THEMES = [
    ("funding", "Grants, fellowships, CSR programmes and civic-tech funds open to an independent Indian road-"
                "safety and urban-mobility data project run by one volunteer. For each: who funds, typical size, "
                "eligibility (individual, trust, Section 8 company), deadline or cycle, and what they ask in return."),
    ("stakeholders", "The public bodies, research groups, NGOs, newsrooms and civic groups in Hyderabad and Bengaluru "
                     "that work on road design, U-turns, medians, wrong-side driving or traffic enforcement, and that "
                     "have used or asked for open data before. For each: what they do, why arcroad's findings would "
                     "matter to them, and their public channel for proposals or data (no private contacts)."),
    ("revenue", "Ways comparable open civic-data projects earn money without letting money change a finding: data "
                "licensing for commercial use, paid audits or briefings, sponsorship with no editorial control, "
                "memberships, donations. Real examples with what they charge and what they disclose."),
    ("attention", "Awards, conferences, open calls, hackathons, journalism partnerships and academic collaborations "
                  "in 2026 and 2027 where an independent Indian road-data project could be seen by people who can act "
                  "on it. For each: dates, cost to enter, and what a submission needs."),
]

SYSTEM = (
    "You are a research assistant for arcroad, an independent open-data project on road detours in Indian cities "
    "(Hyderabad first, Bengaluru as a candidate). You research only. Never contact anyone, never draft messages to "
    "be sent, never sign up for anything. Name organisations and public roles only, never private individuals. "
    "Every factual line needs a source URL; if you cannot source it, leave it out or mark it UNVERIFIED. Prefer "
    "official pages and recent sources, and give the date you saw for anything time-bound. Leave out any idea "
    "that would let a funder or customer change, delay or soften a finding. Be concrete and short: a decision-"
    "ready brief for one busy volunteer, at most 600 words, ending with the three most doable next steps. "
    "Work inside the project's constitution and secret-sauce index given below. Never put anything from them, "
    "or any private detail (drives, routes, calibration, prices, people), into a search query; search public "
    "topics only. Where an idea touches the secret sauce, say which asset it relies on and keep it in this brief. "
    "You may suggest a change to the constitution, marked PROPOSAL; only Rohit adopts one."
)


RUN_DAYS = (6, 1, 3)  # Sunday, Tuesday, Thursday. The night starts at 16:30 UTC (22:00 IST), so the UTC
# date is the IST date.


def is_run_day(day: dt.date) -> bool:
    return day.weekday() in RUN_DAYS


def _run_number(day: dt.date) -> int:
    week = (day.toordinal() + 1) // 7  # weeks that start on Sunday
    return week * len(RUN_DAYS) + RUN_DAYS.index(day.weekday())


def theme_for(day: dt.date):
    return THEMES[_run_number(day) % len(THEMES)]


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


def run(log, previous: str = "", rules: str = "", today: dt.date | None = None, post=_post) -> bytes:
    today = today or dt.datetime.now(dt.UTC).date()
    out = {"job": "viability", "version": 1, "date": today.isoformat(), "model": MODEL}
    key = os.environ.get("VIABILITY_API_KEY", "")
    if not key:
        log("viability: no VIABILITY_API_KEY, skipped (it never uses the nightly key)")
        return json.dumps({**out, "status": "SKIPPED", "reason": "no key"}, indent=1).encode()
    name, ask = theme_for(today)
    prompt = f"This week's theme: {name}.\n\n{ask}"
    if previous:
        prompt += ("\n\nLast week's brief is below. Do not repeat it; build on it or go deeper.\n\n"
                   + previous[:3000])
    messages = [{"role": "user", "content": prompt}]
    if not rules:
        log("viability: could not read the constitution and secret-sauce files, skipped")
        return json.dumps({**out, "status": "SKIPPED", "reason": "rules unavailable"}, indent=1).encode()
    body = {"model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM + "\n\n" + rules[:20000], "messages": messages,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}]}
    spent, content, stop = 0.0, [], None
    for turn in range(MAX_TURNS):
        r = post(key, body)
        spent += cost(r.get("usage") or {})
        content += r.get("content") or []
        stop = r.get("stop_reason")
        log(f"viability: turn {turn + 1}, stop {stop}, about ${spent:.2f}")
        if stop != "pause_turn" or spent >= RUN_BUDGET_USD:
            break
        messages.append({"role": "assistant", "content": r.get("content") or []})
    brief = _text(content)
    status = "OK" if brief and stop == "end_turn" else ("STOPPED_AT_BUDGET" if spent >= RUN_BUDGET_USD else "PARTIAL")
    return json.dumps({**out, "status": status, "theme": name, "estimated_cost_usd": round(spent, 3),
                       "brief": brief, "sources": _sources(content)}, indent=1).encode()
