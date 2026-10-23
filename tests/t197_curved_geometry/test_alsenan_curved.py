"""T-197 on the development villa: the committed curved-geometry ledger reproduces from repository files, and the four
known cases are found by the check itself (not typed into the outputs):
  1. pool wall ring, curved half lost (T-183): engine A's 1.240 m2 wall band and 6.045 m2 base are PARTIAL against the
     drawn D (2.3567 / 10.9356 m2); the T-183 r2 ledger lines (band, centreline 11.784, both faces, base) are clean.
  2. W17 three bases (T-194, Q-39 C): V2.9 COP-001 3.2895 = OUTER_ARC clean; the NW elevation chord 2.6915 = the r 1.935
     face chord, identity, clean; the facade deduction 2.977 (T-159) and the sill 3.290 (T-175) name no basis (2.977 is
     the inner arc 2.9767 AND the outer chord 2.9736 within 1 cm: the ledger must say which).
  3. 1F-11 contour +0.20 m (T-128 r2): OVER_OUTLINE 0.1993 m past the drawn faces 22.1507; r3 22.149 clean.
  4. West dome ring (T-179 / T-160): released route bands PARTIAL (1.1244 of 1.5105 m2), V3.0.4 + the T-160 ring
     DOUBLE_ARC four times, V3.0.5 (bands superseded) clean.
Geometry values are re-derived here from the DXF entities and match the merged verdicts: ring 1.5105 m2 (T-160,
Checker 0.7553 m3 / 0.50), route bands 0.2588 / 0.3034 m2, contour 22.1507 m and 19.0915 m2 (Checker T-128 r3)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t197"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import alsenan_t197 as A                                        # noqa: E402


def _issues(scenario=None):
    rows = list(csv.DictReader(open(HERE / "ISSUES_T197.csv", encoding="utf-8")))
    return [r for r in rows if scenario is None or r["scenario"] == scenario]


def _line(scenario, lid):
    for r in csv.DictReader(open(HERE / "LINES_T197.csv", encoding="utf-8")):
        if r["scenario"] == scenario and r["line_id"] == lid:
            return r
    raise KeyError(lid)


def _el():
    return {e["element_id"]: e for e in json.loads((HERE / "ELEMENTS_T197.json").read_text(encoding="utf-8"))}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_input_holds_no_absolute_coordinate():
    data = json.loads((HERE / "ALSENAN_T197_INPUT.json").read_text(encoding="utf-8"))
    for e in data["elements"]:
        for p in e["pieces"]:
            for k in ("centre",):
                if k in p:
                    assert max(abs(v) for v in p[k]) < 10.0
            for q in p.get("line", []):
                assert max(abs(v) for v in q) < 10.0


def test_geometry_matches_the_merged_verdicts():
    e = _el()
    assert e["DOME-1F-W-RING"]["area_candidates"]["TRUE:AREA"] == pytest.approx(1.5105, abs=1e-4)
    assert e["DOME-1F-W-BAND-NE"]["area_candidates"]["TRUE:AREA"] == pytest.approx(0.2588, abs=1e-4)
    assert e["DOME-1F-W-BAND-NW"]["area_candidates"]["TRUE:AREA"] == pytest.approx(0.3034, abs=1e-4)
    assert e["1F-11"]["length_candidates"]["ARC:FACE"] == pytest.approx(22.1507, abs=1e-4)
    assert e["1F-11"]["area_candidates"]["TRUE:AREA"] == pytest.approx(19.0915, abs=1e-4)
    assert e["POOL-GF-WALL"]["area_candidates"]["TRUE:AREA"] == pytest.approx(2.356726, abs=1e-6)
    assert e["POOL-GF-WALL"]["length_candidates"]["ARC:CENTRELINE"] == pytest.approx(11.7836, abs=1e-4)
    assert e["POOL-GF-BASE"]["area_candidates"]["TRUE:AREA"] == pytest.approx(10.935564, abs=1e-6)
    w = e["W17"]["length_candidates"]
    assert (w["ARC:OUTER"], w["ARC:INNER"], w["CHORD:INNER"]) == pytest.approx((3.2895, 2.9767, 2.6917), abs=1e-4)


def test_case1_pool_curved_half_lost():
    for sc, pre in (("RELEASED_V29_ROUTEG", "REL"), ("CANDIDATE_V305", "C305")):
        assert "PARTIAL" in _line(sc, f"{pre}:POOL-WALL-BAND")["codes"]
        assert "PARTIAL" in _line(sc, f"{pre}:POOL-BASE")["codes"]
    for lid in ("T183:WALL-BAND", "T183:WALL-AXIS", "T183:FORM-OUT", "T183:FORM-WATER", "T183:BASE"):
        assert _line("LEDGERS_MERGED", lid)["codes"] == ""


def test_case2_w17_bases():
    assert _line("RELEASED_V29_ROUTEG", "REL:W17-COP-001")["codes"] == ""
    assert _line("LEDGERS_MERGED", "T194:W17-NW-CHORD")["codes"] == ""
    assert _line("LEDGERS_MERGED", "T150:W17")["codes"] == ""
    ded = _line("LEDGERS_MERGED", "T159:W17-DEDUCT")
    assert ded["codes"] == "BASIS_UNNAMED" and ded["matches"] == "ARC:INNER;CHORD:OUTER"
    sill = _line("LEDGERS_MERGED", "T175:W17-SILL")
    assert sill["codes"] == "BASIS_UNNAMED" and sill["matches"] == "ARC:OUTER"


def test_case3_room_contour_leak():
    r2 = _line("LEDGERS_MERGED", "T128R2:1F-11")
    assert "OVER_OUTLINE" in r2["codes"]
    assert any("by 0.1993 m" in i["detail"] for i in _issues("LEDGERS_MERGED") if i["line_ids"] == "T128R2:1F-11")
    assert _line("LEDGERS_MERGED", "T128R3:1F-11")["codes"] == ""


def test_case4_dome_ring():
    rel = [i for i in _issues("RELEASED_V29_ROUTEG") if i["element_id"] == "DOME-1F-W-RING"]
    assert [i["code"] for i in rel] == ["PARTIAL"] and "+0.3861 m2 short" in rel[0]["detail"]
    dbl = [i for i in _issues("CANDIDATE_V304_PLUS_RING") if i["code"] == "DOUBLE_ARC"]
    assert len(dbl) == 4 and all("CAND:DOME-RING-W" in i["line_ids"] for i in dbl)
    assert not [i for i in _issues("CANDIDATE_V305") if "DOME" in i["element_id"]]
