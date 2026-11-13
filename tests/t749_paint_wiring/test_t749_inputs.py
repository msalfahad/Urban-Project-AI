"""T-749 development-villa pins (no drawing needed): the committed entries equal their builder on the pinned merged
ledgers; every opening once; the projection by hand equals the merged ledgers' own totals; the committed V3.0.77 line
index differs from the V3.0.76 index of record only on the named lines."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t749"))

import t749_inputs as L  # noqa: E402

OUT = ROOT / "research/agents_t749/out"


def _doc():
    return json.loads((OUT / "T749_ENTRIES.json").read_text(encoding="utf-8"))


def test_entries_equal_their_builder():
    assert (OUT / "T749_ENTRIES.json").read_text(encoding="utf-8") == L.text(L.build())


def test_projection_equals_the_merged_ledgers():
    p = _doc()["projection"]
    assert p["PAINT_RESTATE:RANGE"]["n"] == 5
    assert (p["RETURN_LM:EDGE"]["n"], p["RETURN_LM:EDGE_BLANK"]["n"]) == (27, 3)
    assert (D(p["RETURN_LM:EDGE"]["low"]), D(p["RETURN_LM:EDGE"]["high"])) == (D(0), D("33.8"))      # T-746 0 .. 33.800
    assert (p["EXT_EDGE:OPENING"]["n"], p["EXT_EDGE:OPENING_BLANK"]["n"]) == (26, 3)
    assert D(p["EXT_EDGE:OPENING"]["low"]) == D(p["EXT_EDGE:OPENING"]["high"]) == D("103.682251")     # T-751 after
    c = p["EXT_EDGE:CORNER"]
    assert c["n"] == 9 and (D(c["low"]), D(c["high"])) == (D("179.535812"), D("180.735812"))         # T-751 physical
    # T-751 hosted total 178.135812 .. 179.335812 + the NO_HOST mouth arris 1.40 on its own line
    assert D(c["low"]) - D("1.4") == D("178.135812") and D(c["high"]) - D("1.4") == D("179.335812")


def test_every_opening_once_and_doors_under_their_returns():
    d = _doc()["inputs"]
    ops = [e["opening"] for e in d["entries"] if e.get("opening")]
    assert len(ops) == len(set(ops)) == 30 + 29
    doors = d["exterior_doors_counted_once"]
    ret = {e["opening"]: e for e in d["entries"] if e["piece"] == "RETURN_LM"}
    assert len(doors) == 7 and sum(D(x["lm"][1]) for x in doors) == D("12.2")                         # T-751 0 .. 12.20
    for x in doors:
        assert ret[x["opening"]]["line_id"] == x["under"]
        assert (D(x["lm"][0]), D(x["lm"][1])) == (D(str(ret[x["opening"]]["low"])), D(str(ret[x["opening"]]["high"])))


def test_restated_paint_inside_plaster_and_held():
    for e in _doc()["inputs"]["entries"]:
        if e["piece"] == "PAINT_RESTATE":
            assert 0 < e["low"] <= e["high"] <= e["plaster"][1] and e["low"] <= e["plaster"][0]
            assert e["expect"]["class"] == "HELD" and e["status"] == "HELD"


def test_line_index_v3_0_77_only_named_lines_moved():
    p = OUT / "LINE_INDEX_V3_0_77.json"
    i76 = {x["line_id"]: x for x in json.loads((ROOT / L.INDEX).read_text(encoding="utf-8"))["lines"]}
    i77 = {x["line_id"]: x for x in json.loads(p.read_text(encoding="utf-8"))["lines"]}
    ents = _doc()["inputs"]["entries"]
    named = {e["line_id"] for e in ents if e.get("line_id")}
    changed = {k for k in i76 if i76[k] != i77.get(k)}
    added = set(i77) - set(i76)
    assert changed == named and len(added) == 30 + 38 and not (set(i76) - set(i77))
    assert {i77[k]["item_code"] for k in added} == {"FIN.PAINT.EDGE", "FIN.EXT.PAINT.EDGE"}
    assert all(i77[k]["class"] == "HELD" for k in added)
    for e in ents:
        if e["piece"] == "RETURN_LM":
            assert i77[e["line_id"]]["class"] == "EXCLUDED"
        elif e["piece"] == "PAINT_RESTATE":
            x = i77[e["line_id"]]
            assert x["class"] == "HELD" and abs(x["held_low"] - e["low"]) < 1e-9 and abs(x["held_high"] - e["high"]) < 1e-9
    rel76 = sum(D(str(x["measured_net"])) for x in i76.values() if x["class"] == "RELEASED")
    rel77 = sum(D(str(x["measured_net"])) for x in i77.values() if x["class"] == "RELEASED")
    assert rel76 == rel77                                                                       # nothing released moved
