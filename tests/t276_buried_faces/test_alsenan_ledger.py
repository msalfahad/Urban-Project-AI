"""T-276 development-villa ledger (Alsenan; not an accuracy claim): re-run from the committed values-only face trace
(ALSENAN_FACE_TRACE.json) and the merged T-263 / T-242 / T-253 / T-205 inputs, without writing; pins the engineering
results and the committed LEDGER_T276.csv / summary.json."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t276"
sys.path.insert(0, str(HERE))
import t276_alsenan_check as C  # noqa: E402

W = C.W
ROWS, SIDES, NECKS, SUM = C.main(write=False)
TRACE = json.loads((HERE / "ALSENAN_FACE_TRACE.json").read_text(encoding="utf-8"))
SIDE = {(s["span"], s["side"]): s for s in SIDES}


def test_trace_source_and_closure():
    assert TRACE["source"]["structural_sha256"].startswith("9f9d1179")
    assert TRACE["source"]["t242_panels_reproduced"] == 29
    assert SUM["boundaries"] == 32                                   # 29 panels + main house + annex + lift pit
    assert SUM["boundary_length_m"] == pytest.approx(424.9337, abs=1e-4)
    # every boundary closes (check_closure ran in main) and no step lies more than 3 mm from its member
    assert max(b["max_step_to_member_mm"] for b in TRACE["boundaries"]) <= 3.0
    parts = (79.0318 + SUM["gb_faces_held"]["length_m"] + SUM["gb_faces_excluded_above_ground"]["length_m"]
             + SUM["lift_ring_faces_excluded_m"] + SUM["neck_faces_in_beam_zone_m"])
    assert parts == pytest.approx(SUM["boundary_length_m"], abs=2e-3)


def test_drawing_confirmed_total_and_reconciliation_to_t263():
    g = SUM["gb_faces_drawing_confirmed"]
    assert g["m2"] == pytest.approx(46.520845, abs=1e-6)
    assert g["by_kind"]["ARC"] == [2, pytest.approx(5.30298)]
    dc_len = sum(r.readings["length_m"] for r in ROWS if r.member == "GROUND_BEAM" and r.status == W.DC)
    assert dc_len == pytest.approx(79.0318, abs=1e-3)
    # T-263 35.404365 -> 46.520845: + ring 5.30298 + newly traced panel pieces (109+7CB#2 GS-09 2.29449, 7D0+FC#2
    # GS-05 1.80574, 7D0+FC#3 GS-15 2.634235) + COL:255 GAP piece 0.59483 - faces under tees, the pool-court end and span overlaps 1.515795
    assert SUM["t263_dc_m2"] + 5.30298 + 2.29449 + 1.80574 + 2.634235 + 0.59483 - 1.515795 == pytest.approx(
        g["m2"], abs=1e-5)


def test_ring_building_side_is_the_convex_face():
    arc = [r for r in ROWS if r.element.startswith("ARC:157+158")]
    dc = {r.element.split(" | ")[1]: r for r in arc if r.status == W.DC}
    assert set(dc) == {"GS-10", "GS-23"} and all("convex" in r.face for r in dc.values())
    assert sum(r.readings["length_m"] for r in dc.values()) == pytest.approx(6.2388, abs=1e-4)
    out = [r for r in arc if r.status == W.EXCLUDED]
    assert len(out) == 1 and "concave" in out[0].face and out[0].readings["length_m"] == pytest.approx(6.5648)


def test_faces_under_tees_are_not_earth_faces():
    s = SIDE[("7D0+FC#1", "B")]
    assert s["run_L"] == 2.975 and s["traced_L"] == pytest.approx(2.6744, abs=1e-4)
    assert json.loads(s["beyond_face_line"])["SPAN:109+7CB#1"] == pytest.approx(0.30)
    s = SIDE[("170+7C3#3", "A")]
    assert json.loads(s["beyond_face_line"]) == {"PANEL:GS-10": 0.82, "PANEL:GS-17": 2.1, "SPAN:175+7DE#1": 0.3,
                                                 "SPAN:176+7E6#1": 0.13}
    s = SIDE[("170+7C3#4", "A")]
    assert json.loads(s["beyond_face_line"])["OUTER"] == pytest.approx(0.28)     # beside the pool court, not a panel


def test_held_and_excluded_never_zero():
    gb = [r for r in ROWS if r.member == "GROUND_BEAM"]
    assert all(r.qty is None for r in gb if r.status != W.DC)
    assert SUM["gb_faces_held"] == {"pieces": 125, "length_m": pytest.approx(245.3391, abs=1e-4)}
    assert SUM["gb_faces_excluded_above_ground"]["pieces"] == 18
    assert all(r.qty is not None and r.status == W.HELD for r in ROWS if r.member == "NECK")   # lengths, held


def test_neck_beam_zone_deductions():
    nd = SUM["neck_deduction"]
    assert nd == {"dc_necks": 14, "dc_m2": pytest.approx(18.853, abs=1e-6), "held_necks": 18, "excluded_lift": 4}
    n = {x["column"]: x for x in NECKS}
    # C11 COL:220: panel 0.80 x 0.10 + outside 1.40 x 0.95 + two beams 0.30 x 0.95 each = 0.08 + 1.33 + 0.57
    assert n["COL:220"]["deduction_m2"] == pytest.approx(1.98)
    assert n["COL:204"]["gb_plan_differs_from_section"] and n["COL:204"]["status"] == W.HELD


def test_committed_files_match():
    with open(HERE / "LEDGER_T276.csv", encoding="utf-8") as fh:
        committed = list(csv.DictReader(fh))
    assert len(committed) == len(ROWS)
    for c, r in zip(committed, ROWS):
        d = r.as_dict()
        assert c["element"] == d["element"] and c["status"] == d["status"]
        assert (c["qty"] or None) == (None if d["qty"] is None else str(d["qty"]))
    assert json.loads((HERE / "summary.json").read_text(encoding="utf-8")) == json.loads(json.dumps(SUM))
