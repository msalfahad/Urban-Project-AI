"""T-400: the development-villa inputs of V3.0.35 are built ONLY from the Checker-merged T-396 / T-403 / T-404 / T-361
files (sha256-pinned) and pass the module's own validation: 41 rows (40 lines: 5 valued + 35 blank; 1 held bound),
plane 97.9705 m2 = north 83.1305 + street 14.840 (T-396), faces 165.201 m2 = 83.1305 + 82.0705 (T-404), upper G.B
high 3.5256 m3 = 44.07 x 0.20 x 0.40 (T-403), both gates as one held leaf line each (G-02 = D-GF-15), and no
coordinate or client text in the committed inputs. Adverse: an edited merged file stops the build."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "agents_t400")]

from engine.source import arch_v3035 as A  # noqa: E402
import t400_inputs as T  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return A.load_inputs(T.build("development-villa-t131"), "development-villa-t131")


def test_rows_and_verified_totals(doc):
    rows = doc["_rows"]
    assert len(rows) == 40 and sum(r["action"] == "FENCE_VALUE" for r in rows) == 5
    v = {r["element_id"]: r["value"] for r in rows if r["action"] == "FENCE_VALUE"}
    assert v == {"FENCE:F-NORTH:WALL_PLANE": 83.1305, "FENCE:F-STREET:WALL_PLANE": 14.84,
                 "FENCE:F-NORTH:FACE:OUTSIDE": 83.1305, "FENCE:F-NORTH:FACE:PLOT": 82.0705, "FENCE:F-NORTH:TOP": 31.37}
    assert doc["checks"]["plane_total_m2"] == 97.9705 and doc["checks"]["faces_dc_total_m2"] == 165.201
    r = doc["_restates"][0]
    assert r["high"] == 3.5256 and abs(44.07 * 0.20 * 0.40 - r["high"]) < 1e-9 and r["low"] == 0.0


def test_held_bounds_beside(doc):
    b = {r["element_id"]: r.get("beside") for r in doc["_rows"] if r["action"] == "FENCE_HELD"}
    assert b["FENCE:BAND:MASONRY_BELOW_NG"] == {"kind": "AT_LEAST", "value": 17.628, "unit": "m2"}
    assert b["FENCE:F-SEA:WALL_PLANE"]["kind"] == "COMPARISON_ONLY" and b["FENCE:F-SEA:WALL_PLANE"]["value"] == 6.36
    assert b["FENCE:F-STREET:FACE:OUTSIDE"]["value"] == 15.37 and b["FENCE:F-STREET:FACE:PLOT"]["value"] == 14.84
    assert b["FENCE:G-01:LEAF"]["value"] == 2.5 and b["FENCE:G-02:LEAF"]["value"] == 1.0
    assert b["FENCE:F-LOWER:WALL_PLANE"] is None


def test_gates_once_and_bindings(doc):
    assert doc["checks"]["gate_ids"] == {"G-01": "FENCE_GATE_LINE", "G-02": "FENCE_GATE_LINE"}
    assert doc["checks"]["gate_alias"] == {"G-02": "D-GF-15"}
    assert [b["line_id"] for b in doc["_bindings"]] == ["L-6290a9f3d93f38cd46d6", "L-78babf2c6da600cb800e",
                                                         "L-56acf34557c315f65bb1"]
    assert {r["status"] for r in doc["_records"]} == {"NOT_DRAWN", "OTHER_OWNER"}


def test_no_coordinates_or_names_in_the_inputs(doc):
    text = json.dumps(T.build("x"), ensure_ascii=False)
    for bad in ("-80", "-805", "Alsenan", "alsenan"):
        assert bad not in text


def test_adverse_edited_merged_file_stops(monkeypatch):
    monkeypatch.setitem(T.PINS, T.L396, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build("x")
