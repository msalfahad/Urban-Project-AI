"""T-668: the URBAN_V3064_INPUTS_V1 builder (research/agents_t668/t668_inputs.py) on the committed, sha-pinned merged
files only (no drawing, no Drive): 5 beam pieces BOUND to L x 0.20 x 0.40 .. 1.20 on the drawn T-666 lengths (sum
0.6264 .. 1.8792 m3, re-added inside build), one owner per junction square (3 columns, 1 through span, 4 piece ends);
the band's RELEASED 7.2204 point restated to the T-659 bound 5.6392 .. 11.0328 under its applied one-line Checker
downgrade; ONE ADD line (pool blinding AT_LEAST 0.915529 = (11.851050 - 2.695761) x 0.10, netted against the pit
line); the pool steps and the 3 owner columns CONFIRM; every entry loads in arch_v3064. Adverse: an edited pinned file
stops the build; a band index that no longer carries the downgraded point stops the build."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t668"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3064 as A  # noqa: E402
import t668_inputs as I  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return I.build("P")


def test_entries_and_actions(doc):
    c = Counter((e.get("expect", e.get("add"))["item_code"], e["action"]) for e in doc["entries"])
    assert c == {("STR.CONC.BEAM", "BOUND"): 5, ("STR.CONC.BOUNDARY_WALL", "BOUND"): 1,
                 ("STR.CONC.BLINDING", "ADD_LOWER_ONLY"): 1, ("STR.CONC.POOL", "CONFIRM"): 1,
                 ("STR.CONC.COLUMN", "CONFIRM"): 3, ("STR.CONC.GROUND_BEAM", "LOWER_ONLY"): 1,
                 ("STR.CONC.GROUND_BEAM", "CONFIRM"): 2}
    A.load_inputs(json.loads(json.dumps(doc)), "P")


def test_pieces_by_hand(doc):
    ps = {e["line_id"][:10]: e for e in doc["entries"] if e.get("expect", {}).get("item_code") == "STR.CONC.BEAM"}
    want = {"L-dc8cbfc1": 1.40, "L-7c3edce2": 1.40, "L-d62d2fcf": 3.10, "L-8d031491": 1.13, "L-f83c4a46": 0.80}
    for k, L in want.items():
        a = ps[k]["after"]
        assert (round(a["low"], 6), round(a["high"], 6)) == (round(L * 0.2 * 0.4, 6), round(L * 0.2 * 1.2, 6)), k
    assert round(sum(e["after"]["low"] for e in ps.values()), 6) == 0.6264
    assert round(sum(e["after"]["high"] for e in ps.values()), 6) == 1.8792
    kinds = Counter(s["owner_kind"] for e in ps.values() for s in e["squares"])
    assert kinds == {"PIECE": 4, "COLUMN": 3, "THROUGH": 1}
    js = [s["junction"] for e in ps.values() for s in e["squares"]]
    assert len(js) == len(set(js))                                    # each physical square named once
    ex = sorted(x["high"] for e in ps.values() for x in e["exposures_beside"])
    assert ex == [0.014, 0.0405]


def test_band_downgrade_materialised(doc):
    b = next(e for e in doc["entries"] if e.get("line_id") == I.BAND)
    assert b["expect"]["class"] == "RELEASED" and (b["expect"]["low"], b["expect"]["high"]) == (7.2204, 7.2204)
    assert (b["after"]["low"], b["after"]["high"]) == (5.6392, 11.0328)
    assert round(70.49 * 0.2 * 0.4, 6) == 5.6392 and round(91.94 * 0.2 * 0.6, 6) == 11.0328
    assert b["downgrade"]["downgrade_id"] == I.BAND_DG and b["downgrade"]["line_ids"] == [I.BAND]
    assert b["downgrade"]["engine_qty"] == 7.2204


def test_pool_blinding_add(doc):
    p = next(e for e in doc["entries"] if e["action"] == "ADD_LOWER_ONLY")
    assert p["beside"]["value"] == 0.915529 and round((11.851050 - 2.695761) * 0.10, 6) == 0.915529
    assert p["netted_against"][0]["line_id"] == I.TEMPLATE and p["netted_against"][0]["value"] == 12.734438
    assert p["add"]["element_id"] == "P-C:PLAIN_CONCRETE:POOL:BLINDING_UNDER_POOL_BASE"
    assert any("0.915479" in x["m3"] for x in p["beside_also"])          # F-C-T667-1 named beside
    assert any(x["m3"] == "0.037000" for x in p["beside_also"])          # beyond the plot (D-14), not in the line


def test_corner_square_t669(doc):
    c = next(e for e in doc["entries"] if e.get("line_id") == I.CORNER)
    assert c["action"] == "LOWER_ONLY" and c["beside"]["value"] == 0.1125 == round(1.50 * 0.30 * 0.25, 6)
    assert c["squares"][0]["owner_line"] == I.CORNER and c["expect"]["element_id"].endswith("BAND0012.1")
    assert {e.get("line_id") for e in doc["entries"] if e["action"] == "CONFIRM"} >= set(I.CORNER_NEIGHBOURS)


def test_adverse_edited_pinned_file(monkeypatch):
    monkeypatch.setitem(I.PINS, I.T667, "0" * 64)
    with pytest.raises(SystemExit, match="edited file"):
        I.build("P")


def test_adverse_band_point_moved(monkeypatch):
    real = I._load

    def fake():
        t666, t659, t667, index, dgs, t669 = real()
        for ln in index["lines"]:
            if ln["line_id"] == I.BAND:
                ln["held_low"] = ln["held_high"] = 7.0
        return t666, t659, t667, index, dgs, t669
    monkeypatch.setattr(I, "_load", fake)
    with pytest.raises(SystemExit, match="downgraded point"):
        I.build("P")
