"""T-331: the development villa's URBAN_V3022_INPUTS_V1 built from the merged T-329 / T-312 ledgers only (no private
file): pins, closure, the module's own load, no coordinate. Adverse: an edited ledger value stops the build."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t331"))

import t331_inputs as L  # noqa: E402
from engine.source import arch_v3022 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return L.build("PID")


def test_loads_and_pins(doc):
    A.load_inputs(doc)
    fills = [r for r in doc["records"] if r["kind"] == "FILL"]
    held = [r for r in doc["records"] if r["kind"] == "HELD"]
    assert len(fills) == 12 and len(held) == 6
    assert round(sum(r["value"] for r in fills), 4) == 340.3038
    assert sorted(r["room"] for r in held) == ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11"]
    assert {r["line_id"] for r in doc["records"]}.isdisjoint({k["line_id"] for k in doc["keep"]})
    assert [n["line_id"] for n in doc["note_fixes"]] == ["L-af6fb2d3474c5fbdb80a", "L-71e2e002a3af624097f0"]
    pantry = next(r for r in fills if r["room"] == "GF-07")
    assert pantry["line_id"] == "L-721a0f1441436193978c" and pantry["tile_line_id"] == "L-f5c5a1a9c9ee2b644cb5"
    assert pantry["value"] == 32.3422


def test_every_face_backing_equals_tile_and_band_held(doc):
    for r in doc["records"]:
        assert r["band"]["owner_m2"] == 0.0 and r["band"]["status"] == "HELD" and r["band"]["drawing_high"] > 0
        for f in r.get("faces") or ():
            assert f["net_m2"] == f["tile_net_m2"]
            assert abs(f["length_m"] * f["height_m"] - sum(o["m2"] for o in f["openings"]) - f["net_m2"]) <= 1e-4
    assert round(sum(r["band"]["drawing_high"] for r in doc["records"]), 4) == 23.0970


def test_hand_check_1f_12(doc):
    # 8.70 m x 3.35 = 29.145 - D-1F-10 0.80 x 2.20 = 1.760 - W18 0.50 x (3.00 - 0.84) = 1.080 -> 26.305 m2
    r = next(r for r in doc["records"] if r["room"] == "1F-12")
    assert round(sum(f["length_m"] for f in r["faces"]), 4) == 8.70
    assert sorted((o["id"], o["m2"]) for f in r["faces"] for o in f["openings"]) == [("D-1F-10", 1.76), ("W18", 1.08)]
    assert abs(r["value"] - 26.305) <= 1e-4


def test_no_coordinates_or_names_in_the_inputs(doc):
    import json
    txt = json.dumps(doc, ensure_ascii=False)
    assert not re.search(r"\d{5,}\.\d+", txt)            # no drawing coordinates


def test_edited_ledger_value_stops_the_build(monkeypatch):
    rows = L._rows

    def edited(p):
        out = rows(p)
        if p == L.LMAP:
            for r in out:
                if r["proposal"] == "FILL":
                    r["proposed_m2"] = str(float(r["proposed_m2"]) + 0.5)
                    break
        return out
    monkeypatch.setattr(L, "_rows", edited)
    with pytest.raises(SystemExit):
        L.build("PID")
