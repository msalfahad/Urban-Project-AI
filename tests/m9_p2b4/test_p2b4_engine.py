"""Phase 2B-4 constructability audit: the V2.5 engine against the independent piece-level rebuild. Every V2.5
quantity of the three audited rooms is reproduced (PASS); the findings are pinned as what V2.5 does - frozen, not
changed by this audit."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import construct_cases as CC                                  # noqa: E402
import construct_engine as CE                                 # noqa: E402
import construct_reference as CR                              # noqa: E402

AS_PLANNED = {"WP-B": CC.WPB_A1, "WP-E": CC.WPE_A1, "WP-D": CC.WPD_A1}


def _cuts(plan):
    return sorted(ln for roll in plan["rolls"] for _, ln in roll)


def test_every_v2_5_quantity_is_reproduced_by_the_rebuild():
    for rid, case in AS_PLANNED.items():
        eng = CE.engine_record(rid)
        res = CR.verify(CC.ROOMS[rid], CR.URBAN, case["plan"])
        q = CR.summary(res)
        assert eng["direction"] == "ALONG_" + case["plan"]["along"]
        assert sorted(sum(([ln for ln, _ in r] for r in eng["rolls"]), [])) == _cuts(case["plan"]), rid
        assert sorted(eng["band_pieces_mm"]) == sorted(ln for b in res["band"] for _, ln, _ in b["pieces"]), rid
        assert abs(eng["consumed_m2"] - q["consumed_m2"]) < 1e-6 and abs(eng["B_m2"] - q["installed_m2"]) < 1e-6
        assert abs(eng["waste_m2"] - q["true_waste_m2"] - q["reusable_m2"]) < 1e-6, rid
        assert abs(eng["laps_m2"] - q["laps_total_m2"]) < 1e-6 and eng["rolls_n"] == q["rolls"], rid
        assert abs(eng["components"]["upturn"] - q["laps_junction_m2"] - q["laps_band_end_m2"]) < 1e-6
        assert abs(eng["components"]["floor"] - q["laps_side_m2"]) < 1e-6
        assert abs(eng["components"]["doorway"] - q["laps_doorway_m2"]) < 1e-6


def test_finding_f01_the_floor_to_wall_junction_is_assumed_not_listed():
    """V2.5 laps the upturn onto the floor with the 0.10 m joint lap of UP-WP-002 and lists the doorway, corners and
    penetrations as open - never the floor-to-wall junction itself."""
    for rid in AS_PLANNED:
        eng = CE.engine_record(rid)
        assert eng["junction_lap_m"] == 0.1 and eng["seams"]["upturn_end_laps"]["lap_m"] == 0.1
        assert not any("JUNCTION" in w.upper() or "FLOOR_WALL" in w.upper() for w in eng["not_included"]), rid


def test_finding_f02_the_cutting_record_is_not_a_cutting_plan():
    """roll records name a length and a purpose only: no rip, lane, piece id, destination or joint position; the
    L-shape's cut-off corner (a 1.00 x 0.80 m piece) is recorded as an area-equivalent 0.27 x 3.00 m 'shaped trim'."""
    for rid in AS_PLANNED:
        assert CE.engine_record(rid)["segment_keys"] == ["for", "length_m"]
    scrap = CE.engine_record("WP-D")["scrap"]
    assert (267, 3000, "trim at the wall line (shaped; area-equivalent width)") in scrap
    res = CR.verify(CC.ROOM_D, CR.URBAN, CC.WPD_A1["plan"])
    assert [(o["w"], o["l"], o["state"]) for o in res["offcuts"] if o["id"] == "S3.o1"] == \
        [(800, 1000, "REUSABLE_SUBJECT_TO_N7")]


def test_finding_f03_joint_positions_are_not_checked():
    """as listed by V2.5: two WP-B joints sit on floor-seam ends, a WP-E joint ends 0.02 m short of a corner, a WP-D
    piece starts on a corner; the same pieces rearranged clear them (WPB / WPE / WPD -ARR plans)."""
    b = CR.summary(CR.verify(CC.ROOM_B, CR.URBAN, CC.WPB_A1["plan"]))
    e = CR.summary(CR.verify(CC.ROOM_E, CR.URBAN, CC.WPE_A1["plan"]))
    d = CR.summary(CR.verify(CC.ROOM_D, CR.URBAN, CC.WPD_A1["plan"]))
    assert b["joints_stacked_on_seam_ends"] == 2 and e["min_joint_corner_m"] == 0.02
    assert d["min_joint_corner_m"] == 0.0 and d["piece_edges_at_corners"] == 1
    assert CE.engine_record("WP-B")["band_pieces_mm"] == [3000, 2000, 2800, 2800, 2800]


def test_finding_f09_the_roll_sensitivity_ignores_the_junction():
    """V2.5 says the roll count does not change (doorway alternatives only); a separate upstand with a 0.16 m flange
    needs 3 rolls."""
    sens = CE.engine_record("WP-B")["roll_sensitivity"]
    assert sens["rolls_as_computed"] == 2 and sens["changes_roll_count"] is False
    row = CR.sweep(CC.ROOM_B, CR.URBAN, [160])[0]
    assert row["V25"][1] == 3 and row["RULE"][1] == 3


def test_v2_5_withholds_every_open_detail_it_names():
    for rid in AS_PLANNED:
        eng = CE.engine_record(rid)
        assert eng["final_material_state"] == "PROVISIONAL_DETAILS_OPEN"
        assert eng["corners"]["state"] == "WITHHELD" and eng["corners"]["quantity"] is None
        assert any(w.startswith("DOOR_THRESHOLD_TRANSITION") for w in eng["not_included"])
    pen = CE.engine_record("WP-E")["penetrations"]
    assert pen["count"] == 1 and pen["treatment"] is None and pen["quantity"] is None
