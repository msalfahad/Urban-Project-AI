"""T-387 rules on a hand-made villa T387-K (not Alsenan; every figure calculated by hand below).

Villa T387-K, one floor: slab panel 4.00 x 4.00 (x, y -2 .. 2), t 0.15; beam B1 0.25 wide on the x axis from x -2 to 2,
depth 0.60 (full depth through the slab); column C1 0.30 x 0.30 at the origin, storey interval 3.00 (billed through).
  column plan        0.30 x 0.30                                 = 0.0900 m2
  beam drawn plan    4.00 x 0.25                                 = 1.0000 m2; inside the column 0.30 x 0.25 = 0.0750
  beam owned plan    1.0000 - 0.0750                             = 0.9250 m2   (COLUMN > BEAM)
  slab owned plan    16.000 - (1.0000 + 0.0900 - 0.0750)         = 14.985 m2   (BEAM, COLUMN > SLAB)
  column / beam shared  0.0750 m2 x min(0.60, 3.00)              = 0.0450 m3
  beam / slab shared    (1.0000 - 0.0750) m2 x min(0.60, 0.15)   = 0.13875 m3
Adverse 1: the beam line bills 1.0000 m2 (column not deducted): DOUBLE 0.0750 m2 x 0.60 = 0.0450 m3.
Adverse 2: the slab line bills its gross 16.000 m2: DOUBLE 1.0150 m2 x 0.15 = 0.15225 m3.
Adverse 3: two crossing beams B1 / B2 (B2 0.25 wide on the y axis, -2 .. 2, no column) both deduct the 0.0625 m2 junction:
GAP 0.0625 m2 x 0.60 = 0.0375 m3.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t387"))
import t387_rules as R  # noqa: E402


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def villa(beam_billed=0.925, slab_billed=14.985, scale=1.0, rot=0.0):
    def tf(p):
        c, s = math.cos(rot), math.sin(rot)
        return [((x * c - y * s) / scale, (x * s + y * c) / scale) for x, y in p]
    return [
        {"id": "C1", "kind": "COLUMN", "polygon": tf(rect(-0.15, -0.15, 0.15, 0.15)), "billed_m2": 0.09,
         "depth_m": 3.00, "line_ids": ["L-C1"]},
        {"id": "B1", "kind": "BEAM", "polygon": tf(rect(-2, -0.125, 2, 0.125)), "billed_m2": beam_billed,
         "depth_m": 0.60, "line_ids": ["L-B1"]},
        {"id": "S1", "kind": "SLAB", "polygon": tf(rect(-2, -2, 2, 2)), "billed_m2": slab_billed, "depth_m": 0.15,
         "line_ids": ["L-S1"]},
    ]


def pair(res, kind):
    return next(p for p in res["pairs"] if p["kind"] in (kind, "/".join(reversed(kind.split("/")))))


def test_normal_column_through_slab_and_beam_billed_once():
    res = R.level_band_check(villa())
    assert res["status"] == "PASS"
    assert res["double_m2"] == pytest.approx(0, abs=1e-9) and res["gap_m2"] == pytest.approx(0, abs=1e-9)
    cb = pair(res, "COLUMN/BEAM")
    assert cb["shared_m2"] == pytest.approx(0.075) and cb["shared_m3"] == pytest.approx(0.045) and cb["owner"] == "C1"
    bs = pair(res, "BEAM/SLAB")
    assert bs["shared_m3"] == pytest.approx(1.0 * 0.15) and bs["owner"] == "B1"   # drawn band inside the panel
    owned = {m["id"]: m["owned_m2"] for m in res["members"]}
    assert owned == pytest.approx({"C1": 0.09, "B1": 0.925, "S1": 14.985})


def test_adverse_column_not_deducted_from_beam_is_a_double():
    res = R.level_band_check(villa(beam_billed=1.0))
    assert res["status"] == "FAIL"
    assert res["double_m2"] == pytest.approx(0.075) and res["double_m3"] == pytest.approx(0.045)
    bad = [m for m in res["members"] if m["residual_m2"] > 1e-4]
    assert [m["line_ids"] for m in bad] == [["L-B1"]]


def test_adverse_slab_at_gross_is_a_double():
    res = R.level_band_check(villa(slab_billed=16.0))
    assert res["double_m2"] == pytest.approx(1.015) and res["double_m3"] == pytest.approx(0.15225)


def test_adverse_junction_deducted_by_both_beams_is_a_gap():
    m = [{"id": "B1", "kind": "BEAM", "polygon": rect(-2, -0.125, 2, 0.125), "billed_m2": 1.0 - 0.0625,
          "depth_m": 0.60, "line_ids": ["L-B1"]},
         {"id": "B2", "kind": "BEAM", "polygon": rect(-0.125, -2, 0.125, 2), "billed_m2": 1.0 - 0.0625,
          "depth_m": 0.60, "line_ids": ["L-B2"]}]
    res = R.level_band_check(m)
    assert res["gap_m2"] == pytest.approx(0.0625) and res["gap_m3"] == pytest.approx(0.0375)
    m[0]["billed_m2"] = 1.0                       # B1 owns the junction: once
    assert R.level_band_check(m)["status"] == "PASS"


@pytest.mark.parametrize("scale,rot", [(0.001, 0.0), (1.0, math.radians(37)), (0.001, math.radians(-120))])
def test_units_and_rotation_invariant(scale, rot):
    res = R.level_band_check(villa(beam_billed=1.0, scale=scale, rot=rot), scale=scale)
    assert res["double_m3"] == pytest.approx(0.045, abs=1e-6)


def test_mirror_invariant():
    m = villa(beam_billed=1.0)
    for e in m:
        e["polygon"] = [(-x, y) for x, y in e["polygon"]][::-1]
    assert R.level_band_check(m)["double_m3"] == pytest.approx(0.045)


def test_held_member_never_zero():
    m = villa()
    m[2]["billed_m2"] = None                       # slab HELD
    res = R.level_band_check(m)
    assert res["status"] == "PASS_HELD" and res["held_members"] == ["S1"]
    assert pair(res, "BEAM/SLAB")["status"] == "UNDETERMINED"
    assert res["billed_m2"] == pytest.approx(0.09 + 0.925)       # the held slab adds nothing, not 0 as a value
    assert res["union_valued_m2"] == pytest.approx(0.09 + 0.925)


def test_unknown_kind_refused():
    m = villa()
    m[0]["kind"] = "WALL"
    with pytest.raises(R.Refused):
        R.level_band_check(m)


def line(lid, code, eid, v, state="DRAWING_CONFIRMED"):
    return {"line_id": lid, "item_code": code, "element_id": eid, "measured_net": v, "evidence_state": state}


def test_bind_unbound_line_never_ok():
    rows = R.bind([line("L1", "STR.CONC.COLUMN", "COL:GF:C1", 0.27), line("L2", "STR.CONC.COLUMN", None, 0.27),
                   line("L3", "STR.CONC.WALLX", "W:1", 0.5), line("L4", "STR.CONC.COLUMN", "COL:GF:C1", 0.27)])
    st = {r["line_id"]: r["binding"] for r in rows}
    assert st == {"L1": "BOUND", "L2": "UNBOUND", "L3": "UNBOUND", "L4": "UNBOUND"}
    assert [r["line_id"] for r in R.ok_rows(rows)] == ["L1"]
    assert "already billed by L1" in rows[3]["binding_reason"]


def test_bind_split_parts_allowed():
    rows = R.bind([line("L1", "STR.CONC.BEAM", "BEAMS:GF:BAND0001.1", 0.2),
                   line("L2", "STR.CONC.BEAM", "BEAMS:GF:BAND0001.2", 0.3)])
    assert all(r["binding"] == "BOUND" for r in rows)


def test_downgrade_holds_the_figure_and_held_never_summed():
    rows = R.bind([line("L1", "STR.CONC.FOOTING", "F:1", 1.2), line("L2", "STR.CONC.FOOTING", "F:2", 0.8),
                   line("L3", "STR.CONC.FOOTING", "F:3", None, "BLOCKED_RFI")],
                  [{"downgrade_id": "DG-x", "line_ids": ["L2"]}])
    by = {r["line_id"]: r for r in rows}
    assert by["L2"]["status"] == "HELD" and by["L2"]["valued_m3"] is None and by["L2"]["audit_m3"] == 0.8
    assert by["L3"]["status"] == "HELD" and by["L3"]["audit_m3"] is None
    t = R.totals(rows)["FOOTING"]
    assert t["valued_m3"] == pytest.approx(1.2) and t["held_lines"] == 2


def test_resolved_downgrade_no_longer_holds():
    rows = R.bind([line("L2", "STR.CONC.FOOTING", "F:2", 0.8)],
                  [{"downgrade_id": "DG-x", "line_ids": ["L2"], "resolved": True}])
    assert rows[0]["status"] == "VALUED"


def test_stacked_neck_column():
    assert R.stacked_check(0.0, 0.0, 0.09)["status"] == "OK"
    d = R.stacked_check(0.0, -0.10, 0.09)          # column billed from 0.10 below the neck top
    assert d["status"] == "DOUBLE" and d["m3"] == pytest.approx(0.009)
    g = R.stacked_check(-0.10, 0.0, 0.09)
    assert g["status"] == "GAP" and g["m3"] == pytest.approx(0.009)
    assert R.stacked_check(None, 0.0, 0.09) == {"status": "UNDETERMINED", "m3": None}


def test_carried_pair_reopens_on_a_moved_line():
    cand = {"L1": {"measured_net": 1.0}, "L2": {"measured_net": None}}
    assert R.carried_pair({"L1": 1.0, "L2": None}, cand)["status"] == "CARRIED_OK"
    assert R.carried_pair({"L1": 1.1, "L2": None}, cand)["status"] == "RECHECK"
    assert R.carried_pair({"L1": 1.0, "L3": 0.5}, cand)["moved"] == [("L3", "missing")]


def test_exact_drawn_area_overrides_a_chord_polygon():
    # slab panel whose outline has an arc: the source gives 16.200 m2, the chord polygon 16.000; the beam inside it
    # is still measured on the polygon: owned 16.200 - 1.015 = 15.185 m2
    m = villa(slab_billed=15.185)
    m[2]["drawn_m2"] = 16.2
    res = R.level_band_check(m)
    assert res["status"] == "PASS"
    m[2]["billed_m2"] = 16.2                       # gross billed: double 1.015 m2
    assert R.level_band_check(m)["double_m2"] == pytest.approx(1.015)


def test_junction_owner_read_from_the_lines_either_band():
    # the junction billed once by the HIGHER id band is still once (route G: one band owns it, which one is the line's)
    m = [{"id": "B1", "kind": "BEAM", "polygon": rect(-2, -0.125, 2, 0.125), "billed_m2": 1.0 - 0.0625,
          "depth_m": 0.60, "line_ids": ["L-B1"]},
         {"id": "B2", "kind": "BEAM", "polygon": rect(-0.125, -2, 0.125, 2), "billed_m2": 1.0,
          "depth_m": 0.60, "line_ids": ["L-B2"]}]
    res = R.level_band_check(m)
    assert res["status"] == "PASS" and res["pairs"][0]["owner"] == "B2"
    m[0]["billed_m2"] = 1.0                       # both keep it: DOUBLE 0.0625 x 0.60
    assert R.level_band_check(m)["double_m3"] == pytest.approx(0.0375)


def test_rounding_of_a_stored_plan_is_within_tolerance_not_a_double():
    m = villa(beam_billed=0.9264)                 # line stores 0.9264 for 0.9250 (0.0014 m2 x 0.60 = 0.00084 m3)
    res = R.level_band_check(m)
    assert res["status"] == "PASS"
    m = villa(beam_billed=0.9280)                 # 0.0030 m2 x 0.60 = 0.0018 m3 > 0.001: a finding
    assert R.level_band_check(m)["status"] == "FAIL"


def test_arc_chord_face_measured_on_its_exact_outline():
    # quarter-ring slab face inside a curved beam of inner radius 2.00: exact area 0.8584 m2 (2.00^2 - pi 2.00^2 / 4),
    # chord polygon (straight line across the arc) 2.00 x 2.00 / 2 + ... given as polygon 2.0000 m2 here: excess
    # 1.1416; the polygon overlaps the ARC band by 1.1416 - 0.0000 (all chord): true overlap 0
    owned, true_ov = R.arc_chord_owned(exact_m2=0.858407, polygon_m2=2.0, polygon_loss_m2=1.141593 + 0.0625,
                                       arc_overlap_m2=1.141593)
    assert true_ov == pytest.approx(0.0, abs=1e-9)
    assert owned == pytest.approx(0.858407 - 0.0625)          # the 0.0625 m2 column corner still goes out


def test_arc_chord_real_overlap_beyond_the_excess_is_kept():
    owned, true_ov = R.arc_chord_owned(exact_m2=0.858407, polygon_m2=2.0, polygon_loss_m2=1.241593,
                                       arc_overlap_m2=1.241593)
    assert true_ov == pytest.approx(0.1) and owned == pytest.approx(0.758407)


def test_arc_chord_refused_without_excess():
    with pytest.raises(R.Refused):
        R.arc_chord_owned(exact_m2=2.0, polygon_m2=2.0, polygon_loss_m2=0.1, arc_overlap_m2=0.1)


def test_not_applicable_line_is_not_held_and_bills_nothing():
    rows = R.bind([line("L1", "STR.CONC.BEAM", "BEAMS:GF:BAND0009", None, "NOT_APPLICABLE_WITH_EVIDENCE")])
    assert rows[0]["status"] == "NOT_APPLICABLE" and rows[0]["valued_m3"] is None
    rows = R.bind([line("L1", "STR.CONC.BEAM", "BEAMS:GF:BAND0009", None, "NOT_APPLICABLE_WITH_EVIDENCE")],
                  [{"downgrade_id": "DG-y", "line_ids": ["L1"]}])
    assert rows[0]["status"] == "HELD"            # a downgrade record still holds it


# R-T387-7 (T-392): a documented deduction below the 0.001 m3 tolerance is named, never called rounding.
# Hand: villa T387-K beam B1 owned 0.9250 m2 x 0.60 = 0.555000 m3; its merged ledger deducts a named sliver
# 0.000667 m2 x 0.60 = 0.000400 m3 ('ledger X: sliver against ring R'); the line bills 0.554600 m3: residual -0.000400.
def test_documented_sub_tolerance_deduction_is_reported_by_name():
    res = R.classify_residual(0.554600 - 0.555000, [("ledger X: sliver against ring R", -0.000400)])
    assert res["verdict"] == "DOCUMENTED_ADJUSTMENT"
    assert res["named"] == ["ledger X: sliver against ring R"]
    assert abs(res["unexplained_m3"]) < 1e-9


def test_documented_sub_tolerance_deduction_called_rounding_is_refused():
    with pytest.raises(R.Refused, match="DOCUMENTED_NOT_ROUNDING"):
        R.classify_residual(-0.000400, [("ledger X: sliver against ring R", -0.000400)], label="OK_ROUNDING")


def test_rounding_only_when_no_document_explains_it():
    assert R.classify_residual(-0.000400, [])["verdict"] == "OK_ROUNDING"
    # a documented item that does NOT explain the residual leaves it UNEXPLAINED (never rounding)
    res = R.classify_residual(-0.000400, [("ledger Y: end cut", -0.000100)])
    assert res["verdict"] == "UNEXPLAINED" and res["unexplained_m3"] == pytest.approx(-0.000300)


def test_every_ledger_counts_and_unnamed_or_missing_refused():
    # two ledgers wrote the line: T-229-like end cut +0.002000 and T-146-like sliver -0.000400 -> residual +0.001600
    res = R.classify_residual(0.001600, [("ledger A: end cut", 0.002000), ("ledger B: sliver", -0.000400)])
    assert res["verdict"] == "DOCUMENTED_ADJUSTMENT" and len(res["named"]) == 2
    with pytest.raises(R.Refused, match="UNNAMED"):
        R.classify_residual(-0.0004, [("", -0.0004)])
    with pytest.raises(R.Refused, match="RESIDUAL_MISSING"):
        R.classify_residual(None, [])
