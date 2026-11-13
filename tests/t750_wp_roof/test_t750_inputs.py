"""T-750: the inputs builder (research/agents_t750/t750_inputs.py) against the pinned merged ledgers and the V3.0.79 line
index: 36 entries (5 points, 13 bounds, 4 added points, 1 added blank, 3 screed lower ends, 10 causes named), the
penetration total 19 .. 31 pcs (T-691 low_pcs / high_pcs), the falls-screed lower ends 10.628996 m3 (= 3.324832 +
4.791492 + 2.512672, the T-646 AT_LEAST 10.63), every CHANGE binding a HELD V3.0.79 line, no released line named, the
pantry pieces in one room only, and the wire table file equal to a rebuild."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t750"))

import t750_inputs as B  # noqa: E402
from engine.source import arch_v3080 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return B.inputs()


def test_counts_and_hand_totals(doc):
    d = A.load_inputs(doc, B.PID)
    acts = {}
    for e in d["_entries"]:
        acts[e["action"]] = acts.get(e["action"], 0) + 1
    assert acts == {"POINT": 5, "BOUND": 13, "ADD_POINT": 4, "ADD_NAMED": 1, "AT_LEAST": 3, "NAMED": 10}
    pen = [e for e in doc["entries"] if (e.get("expect") or {}).get("item_code", e.get("item_code")) ==
           "FIN.WP.PENETRATION"]
    lo = sum(e.get("value", e.get("low", 0)) for e in pen)
    hi = sum(e.get("value", e.get("high", 0)) for e in pen)
    assert (lo, hi) == (19.0, 31.0)
    scr = sum(e["value"] for e in doc["entries"] if e["action"] == "AT_LEAST")
    assert scr == pytest.approx(3.324832 + 4.791492 + 2.512672, abs=1e-9)


def test_every_change_binds_a_held_v3079_line(doc):
    ix = {x["line_id"]: x for x in json.loads((ROOT / B.INDEX).read_text(encoding="utf-8"))["lines"]}
    for e in doc["entries"]:
        if e["action"] in A.ADDS:
            assert e["line_id"] if "line_id" in e else True
            assert e["room"] == B.PANTRY and e["host_line_id"] in ix
            assert not any(x["item_code"] == e["item_code"] and x["element_id"].startswith(B.PANTRY + ":")
                           and x["class"] != "EXCLUDED" for x in ix.values())
            continue
        x = ix[e["line_id"]]
        assert x["class"] == "HELD" and x["measured_net"] is None
        assert e["expect"]["element_id"] == x["element_id"]


def test_ignored_small_and_released_rows_stay_statements(doc):
    named = {e.get("line_id") for e in doc["entries"]}
    for lid in B.IGNORED_SMALL:
        assert lid not in named
        assert any(s["line_id"] == lid and s["action"] == "IGNORED_SMALL" for s in doc["statements"])
    assert "L-636fd3ff1784a12e653b" not in named          # the roof membrane band is already carried (V3.0.76)


def test_wire_table_file_is_a_rebuild():
    assert B.main(["--check"]) == 0


def test_stale_pin_refused(monkeypatch):
    monkeypatch.setitem(B.PINS, B.T691, "0000000000000000")
    with pytest.raises(B.InputsError, match="stale input"):
        B.inputs()
