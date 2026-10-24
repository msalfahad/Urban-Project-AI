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
    assert SUM["boundary_length_m"] == pytest.approx(422.2075, abs=1e-4)        # r2 (r1 424.9337, see below)
    # every boundary closes (check_closure ran in main) and no 1 mm step lies more than 0.5 mm from its member
    assert TRACE["source"]["step_mm"] == 1.0 and TRACE["snap_tol_mm"] == 1.0
    assert max(b["max_step_to_member_mm"] for b in TRACE["boundaries"]) <= 0.5
    parts = (77.8053 + SUM["gb_faces_held"]["length_m"] + SUM["gb_faces_excluded_above_ground"]["length_m"]
             + SUM["lift_ring_faces_excluded_m"] + SUM["neck_faces_in_beam_zone_m"])
    assert parts == pytest.approx(SUM["boundary_length_m"], abs=2e-3)


def test_drawing_confirmed_total_and_reconciliation_to_t263():
    g = SUM["gb_faces_drawing_confirmed"]
    assert g["m2"] == pytest.approx(45.4682, abs=1e-6)
    assert g["by_kind"]["ARC"] == [2, pytest.approx(5.017465)]
    dc_len = sum(r.readings["length_m"] for r in ROWS if r.member == "GROUND_BEAM" and r.status == W.DC)
    assert dc_len == pytest.approx(77.8053, abs=1e-3)
    # T-263 35.404365 -> r1 46.520845: + ring 5.30298 + newly traced panel pieces (109+7CB#2 GS-09 2.29449, 7D0+FC#2
    # GS-05 1.80574, 7D0+FC#3 GS-15 2.634235) + COL:255 GAP piece 0.59483 - faces under tees, the pool-court end and
    # span overlaps 1.515795
    r1 = SUM["t263_dc_m2"] + 5.30298 + 2.29449 + 1.80574 + 2.634235 + 0.59483 - 1.515795
    assert r1 == pytest.approx(46.520845, abs=1e-5)
    # r1 -> r2 (Checker 20:59), each to its physical cause: COL:255 'strip' is a 0.05 mm offset = the column's own face
    # (neck) -0.59483; ring GS-23 earth pocket closed (177+7CD frames into ARC 158 on both edges) -0.30787; band
    # 182+183 frames into the re-entrant corner over 170+7C3#2 side A on GS-22 -0.21666; the 5 mm closing no longer
    # fills the acute wedge ARC 158 / LINE 7C3 +0.02236 (arc, GS-10) +0.01377 (7C3, GS-10); 1 mm steps and sub-mm
    # slivers no longer owners +0.030585 over 26 faces, none above 0.007 m2
    assert r1 - 0.59483 - 0.30787 - 0.21666 + 0.02236 + 0.01377 + 0.030585 == pytest.approx(g["m2"], abs=1e-5)


def test_ring_building_side_is_the_convex_face():
    arc = [r for r in ROWS if r.element.startswith("ARC:157+158")]
    dc = {r.element.split(" | ")[1]: r for r in arc if r.status == W.DC}
    assert set(dc) == {"GS-10", "GS-23"} and all("convex" in r.face for r in dc.values())
    # Checker own (20:59, analytic on ARC 158): GS-10 4.2490, GS-23 1.6565 = 5.9055 m; traced 4.2460 + 1.6569 = 5.9029
    assert dc["GS-10"].readings["length_m"] == pytest.approx(4.2490, rel=1e-3)
    assert dc["GS-23"].readings["length_m"] == pytest.approx(1.6565, abs=1e-3)
    assert sum(r.readings["length_m"] for r in dc.values()) == pytest.approx(5.9055, rel=1e-3)
    out = [r for r in arc if r.status == W.EXCLUDED]
    assert len(out) == 1 and "concave" in out[0].face and out[0].readings["length_m"] == pytest.approx(6.5670)


def test_faces_under_tees_are_not_earth_faces():
    s = SIDE[("7D0+FC#1", "B")]
    assert s["run_L"] == 2.975 and s["traced_L"] == pytest.approx(2.675, abs=2e-3)   # Checker own 2.675
    assert json.loads(s["beyond_face_line"])["SPAN:109+7CB#1"] == pytest.approx(0.30)
    s = SIDE[("170+7C3#3", "A")]
    assert json.loads(s["beyond_face_line"]) == {"PANEL:GS-10": 0.82, "PANEL:GS-17": 2.1, "SPAN:175+7DE#1": 0.3,
                                                 "SPAN:176+7E6#1": 0.13}
    s = SIDE[("170+7C3#4", "A")]
    assert json.loads(s["beyond_face_line"])["OUTER"] == pytest.approx(0.3009)   # beside the pool court, not a panel
    # (r2: side A now runs to its closed end on column 1E8 / 17C0, so 0.30 m beside the court instead of r1's 0.28)


def test_band_ends_closed_on_their_carriers():
    """r2 (Checker 20:59): every band whose two edges end at different stations closes on its carrier on each edge."""
    ends = {(e["band"], e["end"]): e for e in TRACE["band_end_closures"]}
    assert len(ends) == 8 and all(e["status"] == "CLOSED" and e["free_length_m"] == 0.0 for e in ends.values())
    ring = ends[("177+7CD", "end")]                                   # LINE 177 / 7CD end on ARC 158 219 mm apart
    assert ring["edge_stations_offset_mm"] == pytest.approx(-219.1) and ring["restored_plan_m2"] == pytest.approx(0.0313)
    assert ring["attached_to_spans"] == ["177+7CD#2"]
    assert ends[("180+181", "end")]["ray_gap_mm"] == {"B": 110.4}     # LINE 181 drawn 110 mm short of LINE 180D
    side = SIDE[("177+7CD#2", "A")]
    assert side["traced_L"] == pytest.approx(1.456, abs=1e-3)          # GS-03 0.6249 + GS-23 0.8309 (r1 0.6197)
    # no end face is left on a square cut: the only END row is 1811+1812#1's free end (edges end together)
    end_rows = [r for r in ROWS if r.face.startswith("end face")]
    assert [r.element for r in end_rows] == ["1811+1812#1 | OUTER-1"]
    for sid, sp in TRACE["spans"].items():
        assert all(v["closed"] for v in sp["ends"].values()), sid
    # the earth pocket left the panels: GS-23 -0.0312, GS-17 -0.0899, GS-25 -0.0450, GS-22 -0.0317, GS-20 -0.0241 m2
    ch = {p["panel"]: p["change_m2"] for p in TRACE["panel_area_change_vs_t242"]}
    assert ch == {"GS-06": 0.0001, "GS-10": 0.0002, "GS-17": -0.0899, "GS-20": -0.0241, "GS-22": -0.0317,
                  "GS-23": -0.0312, "GS-25": -0.045}


def test_sub_mm_offsets_are_not_members():
    """r2: the COL:255 'band strip' (0.05 mm drafting offset) is the column's own face: neck line, HELD."""
    assert not [r for r in ROWS if r.element.startswith("PIECE:7D0+FC@COL:255")]
    col = [r for r in ROWS if r.element == "COL:255 | GS-15"]
    assert len(col) == 1 and col[0].member == "NECK" and col[0].status == W.HELD
    assert col[0].readings["length_m"] == pytest.approx(0.70, abs=2e-3)   # Checker 0.700 (0.699 traced)
    sl = [s for s in TRACE["slivers_not_members"] if "COL:255" in s["against"]]
    assert len(sl) == 1 and sl[0]["plan_mm2"] < 0.7 * 1000 * 0.1        # thinner than 0.1 mm over 0.70 m


def test_held_and_excluded_never_zero():
    gb = [r for r in ROWS if r.member == "GROUND_BEAM"]
    assert all(r.qty is None for r in gb if r.status != W.DC)
    assert SUM["gb_faces_held"] == {"pieces": 118, "length_m": pytest.approx(244.2827, abs=1e-4)}
    assert SUM["gb_faces_excluded_above_ground"]["pieces"] == 17
    assert all(r.qty is not None and r.status == W.HELD for r in ROWS if r.member == "NECK")   # lengths, held


def test_neck_beam_zone_deductions():
    nd = SUM["neck_deduction"]
    assert nd == {"dc_necks": 13, "dc_m2": pytest.approx(16.560385, abs=1e-6), "held_necks": 19, "excluded_lift": 4}
    n = {x["column"]: x for x in NECKS}
    # C11 COL:220: panel 0.80 x 0.10 + outside 1.40 x 0.95 + two beams 0.30 x 0.95 each = 0.08 + 1.33 + 0.57
    assert n["COL:220"]["deduction_m2"] == pytest.approx(1.98, abs=1e-3)       # 1 mm steps: 1.98085
    # r2: COL:255's north face is free on GS-15 (the 0.05 mm 'strip' is not a member): slab zone only
    # 0.70 x 0.10 + outside 0.70 x 0.95 + two beams 0.30 x 0.95 = 0.07 + 0.665 + 0.57 = 1.305 (r1 1.90)
    assert n["COL:255"]["deduction_m2"] == pytest.approx(1.305, abs=1e-3)
    # r2: the r1 deduction at COL:238 rested on a 13.5 mm2 sliver's depth; the face is 114+115+7DF#1's (depth held)
    assert n["COL:238"]["status"] == W.HELD and "114+115+7DF#1" in n["COL:238"]["why"]
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
