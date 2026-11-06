"""The weekly viability brief: capped spend, research only, tied to the constitution and secret sauce.

6 Nov 2026: Rohit approved a research agent on arcroad's sustainability with a USD 10 monthly limit, connected
to the constitution and the secret sauce. These checks hold the promises made to him.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "runner" / "app"))
import viability

SUNDAY = dt.date(2026, 11, 8)
RULES = "AGENT-BRIEF text\n\nSECRET-SAUCE text"


def reply(stop="end_turn", text="Brief.", searches=3, tin=20000, tout=1500):
    return {"stop_reason": stop, "content": [{"type": "text", "text": text,
                                              "citations": [{"url": "https://example.org/a"}]}],
            "usage": {"input_tokens": tin, "output_tokens": tout,
                      "server_tool_use": {"web_search_requests": searches}}}


def test_never_uses_the_nightly_key(monkeypatch):
    monkeypatch.delenv("VIABILITY_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "nightly")
    out = json.loads(viability.run(lambda m: None, "", RULES, SUNDAY,
                                   post=lambda *a: (_ for _ in ()).throw(AssertionError("called"))))
    assert out["status"] == "SKIPPED"


def test_skips_without_the_constitution_and_secret_sauce(monkeypatch):
    monkeypatch.setenv("VIABILITY_API_KEY", "k")
    out = json.loads(viability.run(lambda m: None, "", "", SUNDAY,
                                   post=lambda *a: (_ for _ in ()).throw(AssertionError("called"))))
    assert out["status"] == "SKIPPED" and out["reason"] == "rules unavailable"


def test_rules_reach_the_model_and_searches_are_capped(monkeypatch):
    monkeypatch.setenv("VIABILITY_API_KEY", "k")
    seen = {}

    def post(key, body):
        seen.update(body)
        return reply()

    out = json.loads(viability.run(lambda m: None, "last week", RULES, SUNDAY, post=post))
    assert out["status"] == "OK" and out["sources"] == ["https://example.org/a"]
    assert "SECRET-SAUCE text" in seen["system"] and "AGENT-BRIEF text" in seen["system"]
    assert seen["tools"][0]["max_uses"] == viability.MAX_SEARCHES <= 12
    assert "last week" in seen["messages"][0]["content"]


def test_a_run_stops_at_its_budget(monkeypatch):
    monkeypatch.setenv("VIABILITY_API_KEY", "k")
    calls = []

    def post(key, body):
        calls.append(1)
        return reply(stop="pause_turn", tin=700_000)  # about USD 2.1 a turn at the assumed prices

    out = json.loads(viability.run(lambda m: None, "", RULES, SUNDAY, post=post))
    assert len(calls) == 1 and out["status"] == "STOPPED_AT_BUDGET"


def test_a_month_fits_the_ten_dollar_cap():
    assert viability.RUN_BUDGET_USD * 5 <= 10  # at most five Sundays in a month


def test_sundays_only_and_themes_rotate():
    assert viability.is_run_day(SUNDAY) and not viability.is_run_day(SUNDAY + dt.timedelta(days=1))
    names = {viability.theme_for(SUNDAY + dt.timedelta(weeks=w))[0] for w in range(4)}
    assert names == {"funding", "stakeholders", "revenue", "attention"}


def test_research_only_and_private_details_stay_out_of_searches():
    s = viability.SYSTEM
    assert "Never contact anyone" in s and "never private individuals" in s
    assert "into a search query" in s and "only Rohit adopts" in s
    assert "change, delay or soften a finding" in s


def test_files_only_to_the_private_repo():
    import filer
    assert filer.REPO == "rrmlogs8896/arcroad-internal"
