"""Officials directory and road ownership (pipeline/directory.py)."""

import datetime as dt

from pipeline.directory import LADDER, is_fresh, ladder_for, owner, road_class, usable, validate

TODAY = dt.date(2026, 10, 27)


def office(**kw):
    e = {
        "id": "sample-pd",
        "level": "L1",
        "body": "Sample Authority",
        "designation": "Project Director",
        "jurisdiction": {"refs": ["NH65"]},
        "mailbox": "pd-sample@example.gov.in",
        "postal_address": "Sample Office, Sample Road",
        "source_url": "https://example.gov.in/contacts",
        "last_verified": "2026-10-20",
    }
    e.update(kw)
    return e


def test_a_complete_sourced_office_is_valid():
    assert validate(office()) == []


def test_mobile_numbers_are_refused_in_any_contact_field():
    for field in ("phone", "mailbox", "postal_address", "name_as_published"):
        assert any("mobile" in p for p in validate(office(**{field: "call 98480 12345"}))), field
    assert any("mobile" in p for p in validate(office(phone="+91-9848012345")))


def test_office_landline_is_allowed():
    assert validate(office(phone="040-2345 6789")) == []


def test_webmail_mailbox_is_refused():
    assert any("webmail" in p for p in validate(office(mailbox="someone@gmail.com")))


def test_entry_without_source_or_date_is_invalid():
    probs = validate(office(source_url="", last_verified=""))
    assert "missing source_url" in probs and "missing last_verified" in probs


def test_http_source_is_refused():
    assert any("https" in p for p in validate(office(source_url="http://example.gov.in")))


def test_stale_entry_is_withheld_not_guessed():
    assert usable(office(last_verified="2026-10-20"), TODAY)
    assert not usable(office(last_verified="2026-01-01"), TODAY)


def test_future_or_garbled_verification_date_counts_as_stale():
    assert not is_fresh(office(last_verified="2027-01-01"), TODAY)
    assert not is_fresh(office(last_verified="soon"), TODAY)


def test_road_class_is_a_hint():
    assert [road_class(r) for r in ("NH65", "nh 44", "SH1", "", None)] == ["nh", "nh", "sh", "local", "local"]


def test_nh_ref_alone_never_confirms_nhai():
    o = owner("NH65", [], TODAY)
    assert o["confirmed"] is False
    assert "Roads and Buildings NH wing" in o["suggestion"]


def test_only_a_fresh_sourced_segment_confirms_the_owner():
    seg = {"ref": "NH 65", "owner_office_id": "sample-pd", "source_url": "https://example.gov.in/projects", "last_verified": "2026-10-20"}
    assert owner("NH65", [seg], TODAY)["confirmed"] is True
    assert owner("NH65", [dict(seg, last_verified="2025-01-01")], TODAY)["confirmed"] is False
    assert owner("NH65", [dict(seg, source_url="")], TODAY)["confirmed"] is False
    assert owner("NH44", [seg], TODAY)["confirmed"] is False


def test_ladder_keeps_order_and_reports_withheld_entries():
    directory = {"a": office(id="a"), "b": office(id="b", last_verified="2025-01-01")}
    rungs = ladder_for({"L1": ["a", "b"]}, directory, TODAY)
    assert [r["level"] for r in rungs] == [k for k, _ in LADDER]
    assert [e["id"] for e in rungs[0]["entries"]] == ["a"] and rungs[0]["withheld"] == 1
    assert rungs[1]["entries"] == [] and rungs[1]["withheld"] == 0
