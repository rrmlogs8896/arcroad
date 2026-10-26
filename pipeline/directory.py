"""Road ownership and the officials directory (build step 4; ledger 36.29, 36.34).

Who owns a road, and which public office a citizen should write to about it.

Rules this module enforces, each because the alternative would put a wrong
or unsafe address in front of a citizen:

* Office before person. An entry is a designation and an official office
  mailbox or landline. A name appears only as the official page publishes it.
* Official sources only. Every entry carries its source URL and the date a
  person last checked it against that source.
* Stale is hidden, never guessed. An entry past its allowance is withheld,
  and the kit falls back to the blank address lines it already prints.
* No personal contact data. Mobile numbers and webmail addresses are refused
  outright, whatever the source shows.
* Road class is a suggestion, not an owner. A national-highway ref does not
  prove NHAI maintains it (some NH stretches in Telangana sit with the state
  Roads and Buildings NH wing). Only a sourced segment entry names an owner.
"""

from __future__ import annotations

import datetime as dt
import re

# The escalation ladder for one road (36.34 item 3). Order is the order a
# citizen should use; every party is treated the same.
LADDER = (
    ("L1", "Office that owns and maintains the road"),
    ("L2", "Regional head of that office"),
    ("L3", "Elected representatives (copy to)"),
    ("L4", "Public grievance portals"),
    ("L5", "Right to Information: Public Information Officer, then appellate authority"),
)
LEVELS = {k for k, _ in LADDER}

# Days an entry stays usable after a person last checked it at its source.
# Postings change often; elected representatives change at elections.
ALLOWANCE_DAYS = {"L1": 90, "L2": 90, "L3": 180, "L4": 180, "L5": 90}

_MOBILE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_WEBMAIL = re.compile(r"@(gmail|yahoo|outlook|hotmail|rediffmail|ymail|icloud|proton(mail)?)\.", re.I)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED = ("id", "level", "body", "designation", "jurisdiction", "source_url", "last_verified")


def validate(entry: dict) -> list[str]:
    """Return every problem with a directory entry; an empty list means usable in principle."""
    problems = [f"missing {k}" for k in REQUIRED if not entry.get(k)]
    if entry.get("level") and entry["level"] not in LEVELS:
        problems.append(f"unknown level {entry['level']!r}")
    src = str(entry.get("source_url", ""))
    if src and not src.startswith("https://"):
        problems.append("source_url must be an https URL to the official page")
    lv = str(entry.get("last_verified", ""))
    if lv and not _ISO_DATE.match(lv):
        problems.append("last_verified must be YYYY-MM-DD")
    contact_text = " ".join(str(entry.get(k, "")) for k in ("mailbox", "phone", "postal_address", "name_as_published"))
    if _MOBILE.search(contact_text):
        problems.append("contains a mobile number: office landlines and mailboxes only")
    if _WEBMAIL.search(str(entry.get("mailbox", ""))):
        problems.append("mailbox is a personal webmail address: official mailboxes only")
    if not (entry.get("mailbox") or entry.get("postal_address") or entry.get("portal_url")):
        problems.append("no official way to reach the office (mailbox, postal address or portal)")
    return problems


def is_fresh(entry: dict, today: dt.date) -> bool:
    """True while the entry is inside its allowance. Unparseable dates are stale."""
    try:
        checked = dt.date.fromisoformat(str(entry.get("last_verified")))
    except ValueError:
        return False
    days = ALLOWANCE_DAYS.get(entry.get("level"), 90)
    return 0 <= (today - checked).days <= days


def usable(entry: dict, today: dt.date) -> bool:
    return not validate(entry) and is_fresh(entry, today)


def road_class(ref: str | None) -> str:
    """'nh', 'sh' or 'local' from an OSM ref tag. A hint about the owner, never proof."""
    r = re.sub(r"\s+", "", str(ref or "")).upper()
    if r.startswith("NH"):
        return "nh"
    if r.startswith("SH"):
        return "sh"
    return "local"


SUGGESTED_BODY = {
    "nh": "National Highways Authority of India, or the state Roads and Buildings NH wing, depending on the stretch",
    "sh": "Roads and Buildings Department, Government of Telangana",
    "local": "The municipal body or development authority that maintains the road",
}


def owner(ref: str | None, segments: list[dict], today: dt.date) -> dict:
    """Who owns the road at this place.

    `segments` are sourced entries that name the owner of a stretch:
    {"ref", "owner_office_id", "source_url", "last_verified", ...}. Only a
    fresh, sourced segment for the same ref gives a confirmed owner. Anything
    else returns the road-class suggestion, marked unconfirmed.
    """
    cls = road_class(ref)
    norm = re.sub(r"\s+", "", str(ref or "")).upper()
    for seg in segments:
        if re.sub(r"\s+", "", str(seg.get("ref", ""))).upper() != norm or not norm:
            continue
        if not str(seg.get("source_url", "")).startswith("https://"):
            continue
        if not is_fresh({"level": "L1", "last_verified": seg.get("last_verified")}, today):
            continue
        return {"confirmed": True, "road_class": cls, "office_id": seg["owner_office_id"], "source_url": seg["source_url"]}
    return {"confirmed": False, "road_class": cls, "suggestion": SUGGESTED_BODY[cls]}


def ladder_for(office_ids_by_level: dict[str, list[str]], directory: dict[str, dict], today: dt.date) -> list[dict]:
    """The escalation ladder with only usable entries; a level with none says so instead of guessing."""
    out = []
    for level, label in LADDER:
        entries = [directory[i] for i in office_ids_by_level.get(level, []) if i in directory]
        good = [e for e in entries if usable(e, today)]
        out.append({"level": level, "label": label, "entries": good, "withheld": len(entries) - len(good)})
    return out
