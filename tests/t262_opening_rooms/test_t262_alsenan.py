"""T-262: the development villa's committed geometric opening-to-room join (research only, nothing applied).

Invariants: all 59 inventory openings (T-249: 29 windows, 27 doors, 1 gate, 2 arches) joined by their handles; every
side settled (no SPLIT); every door / gate / arch has two settled sides; the census labels give 5 LABEL_WRONG
(W06, W19, W20, D-1F-01, D-1F-04), 1 LABEL_INCOMPLETE (W03 also serves GF-08) and 2 AGREE_OPEN_ZONE (D-1F-02,
D-1F-03); the T-128 r3 per-room opening table agrees on 32 / 32 rooms (so the per-room plaster / paint / wet-tile
deductions sit in the right rooms); the T-237 crosswalk has exactly the 4 swapped west-bath joins; the T-209 wet-tile
input names W19 / W20 in each other's room with equal values; GF-16's region covers three wall strips and the D-GF-14
reveal. No drawing coordinate is committed. The byte-for-byte rebuild needs the private DXF (URBAN_P7757_DXF).
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t262"


def _rows(name):
    with open(HERE / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_every_inventory_opening_joined_by_its_handles():
    rows = _rows("OPENING_ROOMS_T262.csv")
    inv = {r["ID"]: r for r in csv.DictReader(open(ROOT / "research/agents_t249/OPENINGS_T249.csv", encoding="utf-8"))}
    assert len(rows) == 59 and {r["ID"] for r in rows} == set(inv)
    for r in rows:
        assert r["HANDLES_T249"] == inv[r["ID"]]["HANDLES"]
        assert "SPLIT" not in (r["SIDE_A_STATE"], r["SIDE_B_STATE"])
        if r["KIND"] in ("DOOR", "GATE", "OPENING"):
            assert r["DOOR_PAIR"] == "TWO_SIDES"


def test_census_label_verdicts():
    rows = {r["ID"]: r for r in _rows("OPENING_ROOMS_T262.csv")}
    wrong = sorted(k for k, r in rows.items() if r["VERDICT"] == "LABEL_WRONG")
    assert wrong == ["D-1F-01", "D-1F-04", "W06", "W19", "W20"]
    assert [k for k, r in rows.items() if r["VERDICT"] == "LABEL_INCOMPLETE"] == ["W03"]
    assert sorted(k for k, r in rows.items() if r["VERDICT"] == "AGREE_OPEN_ZONE") == ["D-1F-02", "D-1F-03"]
    assert sum(1 for r in rows.values() if r["VERDICT"] == "AGREE") == 51
    # the geometric rooms of the five
    assert rows["W06"]["ROOMS_GEO"] == "GF-13" and rows["W19"]["ROOMS_GEO"] == "1F-03"
    assert rows["W20"]["ROOMS_GEO"] == "1F-02"
    assert rows["D-1F-01"]["ROOMS_GEO"] == "1F-01 1F-03" and rows["D-1F-04"]["ROOMS_GEO"] == "1F-02 1F-04"
    assert rows["W03"]["SIDE_B_STATE"] == "MULTI_ROOM" and rows["W03"]["ROOMS_GEO"] == "GF-08 GF-15"
    assert "REVEAL_IN_REGION:GF-16" in rows["D-GF-14"]["FLAGS"] and rows["D-GF-14"]["ROOMS_GEO"] == "GF-15 GF-16"


def test_t128_per_room_table_agrees_everywhere():
    t = _rows("T128_ROOM_CHECK_T262.csv")
    assert len(t) == 32 and all(r["RESULT"] == "AGREE" for r in t)


def test_t237_and_t209_joins():
    t237 = [r for r in _rows("T237_JOIN_CHECK_T262.csv") if r["RESULT"] == "JOIN_WRONG"]
    assert sorted((r["T237_ROOM"], r["CENSUS_ID"]) for r in t237) == [
        ("1F-02", "D-1F-01"), ("1F-02", "W19"), ("1F-03", "D-1F-04"), ("1F-03", "W20")]
    t209 = {(r["ROOM"], r["WINDOW_ID"]): r for r in _rows("T209_WINDOW_CHECK_T262.csv")}
    bad = sorted(k for k, r in t209.items() if r["RESULT"] != "AGREE")
    assert bad == [("1F-02", "W19"), ("1F-03", "W20")]
    a, b = t209[("1F-02", "W19")], t209[("1F-03", "W20")]
    # the swap moves 0 m2 only because the two windows are equal: stated from the values, never assumed
    assert (a["W"], a["SILL"], a["HEAD"]) == (b["W"], b["SILL"], b["HEAD"])


def test_gf16_region_over_wall_strips():
    ov = _rows("REGION_OVERLAP_T262.csv")
    strips = {r["HANDLES"]: float(r["OVERLAP_M2"]) for r in ov if r["KIND"] == "WALL_STRIP"}
    assert {r["ROOM"] for r in ov} == {"GF-16"}
    assert strips == {"2DD 2DE": 0.3, "2E5 2E7": 0.0418, "324 325": 0.1805}
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["walked_area_m2"]["GF-16"] == pytest.approx(4.4203)


def test_no_drawing_coordinate_committed():
    for p in HERE.iterdir():
        if p.suffix in (".csv", ".json"):
            nums = [float(x) for x in re.findall(r"-?\d+\.\d+", p.read_text(encoding="utf-8"))]
            assert all(abs(x) < 100 for x in nums), p.name


@pytest.mark.skipif(not os.environ.get("URBAN_P7757_DXF"), reason="private DXF not available (URBAN_P7757_DXF)")
def test_rebuild_from_the_drawing(tmp_path):
    cap = tmp_path / "t262_capture.pkl"
    py = sys.executable
    subprocess.run([py, "-I", str(HERE / "capture_t262.py"), os.environ["URBAN_P7757_DXF"], "--out", str(cap)],
                   check=True, capture_output=True)
    r = subprocess.run([py, "-I", str(HERE / "alsenan_t262.py"), str(cap), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
