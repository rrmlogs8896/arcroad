"""One-off research brief for 13point8: where to share it for the most reach, and each community's rules.

Approved by Rohit on 16 Nov 2026 ("$2 agent today"), one night only: 17 Nov 2026, 22:00 IST (moved from 16 Nov), first in the queue.
Hard cap held in two places: the EYELAB_API_KEY workspace's USD 5 monthly limit (Anthropic refuses above it) and
RUN_BUDGET_USD below. It researches public pages only, contacts no one, posts nothing, and never puts anything
private about 13point8 (visitor data, code, plans) into a search. Every claim needs a source link.
"""
from __future__ import annotations

import datetime as dt
import json
import os

import eyelab  # reuse its request, cost and citation helpers

RUN_NIGHT = "2026-11-17"
MODEL = "claude-sonnet-5-5"
MAX_SEARCHES = 30
MAX_TOKENS = 14000
RUN_BUDGET_USD = 2.00
MAX_TURNS = 8

SYSTEM = (
    "You are an outreach researcher for 13point8 (13point8.in), a free, independent, ad-free educational website of "
    "interactive 3D space journeys built from public NASA/ESA data: Voyager (one light-day from Earth on 18 Nov 2026), "
    "a black hole, Mars terrain, space junk, pulsars, the galaxy. It is not affiliated with or endorsed by any space "
    "agency; never suggest implying that. Its owner shares it himself, one community at a time, disclosing it is his.\n"
    "Research, from public sources only, where it can reach the most genuinely interested people, and the exact rules "
    "of each place. Cover: Reddit (space, science, education, design and web-showcase subreddits, plus India-focused "
    "ones), Quora (questions and Spaces), Hacker News (Show HN), Product Hunt, X, LinkedIn, Threads, Bluesky, Mastodon "
    "(astronomy instances), YouTube Shorts and Instagram Reels, Pinterest, Facebook groups, Discord and astronomy "
    "forums (e.g. Cloudy Nights), teacher and planetarium communities, newsletters that feature web finds, and Indian "
    "platforms. For each: audience size and fit (with evidence), self-promotion rules quoted briefly with the rule's "
    "URL, link and account-age/karma requirements, AI-content or 'made with AI' policies, best format (link, image, "
    "short video, text), best posting times with time zone, removal or ban risk, effort, and what made similar "
    "space/visualisation posts succeed or fail there. Respect Reddit's and each platform's spam rules: no "
    "vote-asking, no sockpuppets, no cross-posting the same text everywhere, no automation of posting.\n"
    "Every factual line needs a source URL; mark anything unsourced UNVERIFIED and anything older than 2025 as "
    "possibly outdated.\nOutput, in this order: 1) a ranked table of the top 15 places (score out of 10 for reach, "
    "fit, rule-safety, effort, with one-line reason); 2) per place: the rules that matter, format, timing, a sample "
    "honest title idea; 3) a 4-week calendar from 18 Nov 2026 that spaces communities a few days apart and pairs each "
    "journey with its best-fit community; 4) red flags: places to avoid and why; 5) sources. Plain words, under "
    "2,500 words."
)


def is_run_night(night: str) -> bool:
    return night == RUN_NIGHT


def run(log, post=None) -> bytes:
    post = post or eyelab._post
    out = {"job": "socialreach", "version": 1, "date": dt.datetime.now(dt.timezone.utc).date().isoformat(), "model": MODEL}
    key = os.environ.get("EYELAB_API_KEY", "")
    if not key:
        log("socialreach: no EYELAB_API_KEY, skipped")
        return json.dumps({**out, "status": "SKIPPED", "reason": "no key"}, indent=1).encode()
    messages = [{"role": "user", "content": "Write the outreach research brief now."}]
    body = {"model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM, "messages": messages,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}]}
    spent, content, stop = 0.0, [], None
    for turn in range(MAX_TURNS):
        r = post(key, body)
        spent += eyelab.cost(r.get("usage") or {})
        content += r.get("content") or []
        stop = r.get("stop_reason")
        log(f"socialreach: turn {turn + 1}, stop {stop}, about ${spent:.2f}")
        if stop != "pause_turn" or spent >= RUN_BUDGET_USD:
            break
        messages.append({"role": "assistant", "content": r.get("content") or []})
    brief = eyelab._text(content)
    status = "OK" if brief and stop == "end_turn" else ("STOPPED_AT_BUDGET" if spent >= RUN_BUDGET_USD else "PARTIAL")
    return json.dumps({**out, "status": status, "estimated_cost_usd": round(spent, 3), "brief": brief,
                       "sources": eyelab._sources(content)}, indent=1).encode()
