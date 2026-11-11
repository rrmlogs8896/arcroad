"""The roadside study tool, end to end on made-up labels in a temporary folder (no private data)."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import roadside_study as t
from test_roadside import rec


def test_sample_agree_run(tmp_path, monkeypatch):
    recs = [rec(i, i % 10 < 7, True) for i in range(80)] + [rec(i, i % 10 < 3, False) for i in range(100, 180)]
    lab = tmp_path / "a.jsonl"
    lab.write_text("\n".join(json.dumps(r) for r in recs) + "\n" + json.dumps({"file": "x", "error": "unparsed"}) + "\n")
    monkeypatch.setattr(t, "LABELS", [lab])
    out = tmp_path / "out"
    out.mkdir()
    t.sample(out)
    rows = list(csv.reader(open(out / "label-check.csv")))
    assert len(rows) == 52 and rows[1][0] == "(choices)"
    model = {r["file"]: r["labels"] for r in recs}
    with open(out / "label-check.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows[:2])
        for r in rows[2:]:
            w.writerow([r[0]] + [model[r[0]][k] for k in t.FIELDS])
    t.agree(out)
    assert all(v["passes"] for v in json.loads((out / "label-check-result.json").read_text()).values())
    t.run(out)
    res = json.loads(next(out.glob("roadside-*.json")).read_text())
    assert res["photos_unparsed"] == 1 and res["result"]["verdict"] == "supported"
    assert res["status"] == "CANDIDATE, NOT PUBLISHED"
