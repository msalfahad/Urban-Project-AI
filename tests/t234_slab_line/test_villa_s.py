"""T-234 CONC.SLAB whole-line rules on a hand-calculated non-Alsenan fixture (villa S, one roof sheet).

Villa S roof sheet, general note: 'slabs 15 cm unless otherwise stated'; beams 0.20 wide, D 0.50 (full depth, C1).
  P1 4.00 x 3.00 between beam faces, tag 'T 20'                       12.00 x 0.20 = 2.400 m3
  P2 3.00 x 3.00, duct opening 0.80 x 0.50 drawn in it               (9.00 - 0.40) x 0.15 = 1.290 m3
  P3 2.00 x 2.50 sunken (hatch; drop not printed), thickness by note   5.00 x 0.15 = 0.750 m3
  line                                                                 4.440 m3 (hand)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t234"))
sys.path.insert(0, str(ROOT))
import slab_line as SL  # noqa: E402
from engine.source import concrete_overlap_ownership as OV  # noqa: E402

NOTE = 0.15


def rect(x0, y0, w, h):
    return [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]


def rot(points, deg, mirror=False):
    a = math.radians(deg)
    out = []
    for x, y in points:
        if mirror:
            x = -x
        out.append((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)))
    return out


def villa(transform=lambda p: p, unit="m", k=1.0):
    s = lambda pts: [(x * k, y * k) for x, y in transform(pts)]  # noqa: E731
    return [
        dict(id="P1", storey="R1", outline=s(rect(0.2, 0.2, 4.0, 3.0)), unit=unit, t_basis="TAG", t_m=0.20),
        dict(id="P2", storey="R1", outline=s(rect(4.4, 0.2, 3.0, 3.0)), unit=unit, t_basis="GENERAL_NOTE",
             openings=[dict(id="DUCT-1", outline=s(rect(5.0, 1.0, 0.8, 0.5)), unit=unit)]),
        dict(id="P3", storey="R1", outline=s(rect(0.2, 3.4, 2.0, 2.5)), unit=unit, t_basis="GENERAL_NOTE",
             sunken=True, depth_basis="FULL"),
    ]


CENSUS = {"DUCT-1": "IN_PANEL"}


def test_hand_total_and_panels():
    r = SL.slab_line(villa(), NOTE, CENSUS)
    m3 = {p["id"]: p["m3"] for p in r["panels"]}
    assert m3["P1"] == pytest.approx(2.400, abs=1e-9)
    assert m3["P2"] == pytest.approx(1.290, abs=1e-9)
    assert m3["P3"] == pytest.approx(0.750, abs=1e-9)
    assert r["measured_m3"] == pytest.approx(4.440, abs=1e-9)
    assert r["status"] == "CLOSABLE" and r["held"] == [] and r["openings_not_deducted"] == []


@pytest.mark.parametrize("deg,mirror", [(0, False), (30, False), (90, True), (217.5, True)])
def test_rotation_and_mirror_invariant(deg, mirror):
    r = SL.slab_line(villa(lambda p: rot(p, deg, mirror)), NOTE, CENSUS)
    assert r["measured_m3"] == pytest.approx(4.440, abs=1e-9)


def test_millimetre_input_declared():
    r = SL.slab_line(villa(unit="mm", k=1000.0), NOTE, CENSUS)
    assert r["measured_m3"] == pytest.approx(4.440, abs=1e-9)


def test_unknown_unit_refused():
    with pytest.raises(ValueError, match="unknown length unit"):
        SL.slab_line(villa(unit="in"), NOTE, CENSUS)


def test_thickness_in_cm_refused():
    v = villa()
    v[0]["t_m"] = 20
    with pytest.raises(ValueError, match="outside"):
        SL.slab_line(v, NOTE, CENSUS)


# ---- adverse cases named by the task row

def test_opening_deducted_twice_in_one_panel_refused():
    v = villa()
    v[1]["openings"].append(dict(v[1]["openings"][0]))
    with pytest.raises(ValueError, match="deducted twice"):
        SL.slab_line(v, NOTE, CENSUS)


def test_opening_deducted_in_two_panels_refused():
    v = villa()
    v[2]["openings"] = [dict(v[1]["openings"][0])]
    with pytest.raises(ValueError, match="deducted in"):
        SL.slab_line(v, NOTE, CENSUS)


def test_census_opening_not_deducted_keeps_line_open():
    v = villa()
    v[1]["openings"] = []
    r = SL.slab_line(v, NOTE, CENSUS)
    assert r["status"] == "NOT_CLOSABLE" and r["openings_not_deducted"] == ["DUCT-1"]


def test_sunken_panel_at_reduced_depth_refused():
    v = villa()
    v[2]["depth_basis"] = "REDUCED_BY_DROP"
    with pytest.raises(ValueError, match="sunken"):
        SL.slab_line(v, NOTE, CENSUS)


def test_finished_level_as_structural_top_refused():
    v = villa()
    v[0]["top_datum"] = "FFL"
    with pytest.raises(ValueError, match="finished floor level"):
        SL.slab_line(v, NOTE, CENSUS)
    v = villa()
    v[1]["t_basis"] = "FROM_LEVELS"
    with pytest.raises(ValueError, match="finished levels"):
        SL.slab_line(v, NOTE, CENSUS)


def test_tag_spread_to_untagged_panel_refused():
    """The released route G 'SHEET_UNIFORM' rule: P1's 'T 20' given to P2 / P3 would make 4.440 -> 4.873 m3."""
    v = villa()
    v[1]["t_basis"] = "SHEET_UNIFORM"
    v[1]["t_m"] = 0.20
    with pytest.raises(ValueError, match="general note"):
        SL.slab_line(v, NOTE, CENSUS)


def test_no_printed_thickness_is_held_never_zero():
    v = villa()
    v[2]["t_basis"] = "HELD"
    r = SL.slab_line(v, NOTE, CENSUS)
    assert r["status"] == "NOT_CLOSABLE"
    assert r["measured_m3"] == pytest.approx(3.690, abs=1e-9)
    (pid, (lo, hi)), = r["held"]
    assert pid == "P3" and lo > 0 and hi > lo


def test_panel_listed_twice_refused():
    v = villa()
    v.append(dict(v[0]))
    with pytest.raises(ValueError, match="twice"):
        SL.slab_line(v, NOTE, CENSUS)


# ---- slab / beam ownership: each intersection once

def faces(billed_band):
    return [dict(id="P1", cls="SLAB", area_m2=12.0, billed_by=["CONC.SLAB"]),
            dict(id="B-S", cls="BEAM", area_m2=0.88, billed_by=billed_band),
            dict(id="DUCT-1", cls="OPENING", area_m2=0.40, billed_by=[])]


def test_partition_normal():
    assert SL.face_partition_check(faces(["CONC.BEAM"]))["status"] == "PASS"


def test_partition_band_in_slab_and_beam_refused():
    r = SL.face_partition_check(faces(["CONC.BEAM", "CONC.SLAB"]))
    assert r["status"] == "FAIL" and r["double"][0][0] == "B-S"


def test_partition_band_billed_by_nobody_is_gap():
    r = SL.face_partition_check(faces([]))
    assert r["status"] == "FAIL" and r["gap"][0][0] == "B-S"


def test_partition_band_billed_as_slab_is_wrong_owner():
    r = SL.face_partition_check(faces(["CONC.SLAB"]))
    assert r["status"] == "FAIL" and r["wrong_owner"][0][:2] == ("B-S", "CONC.SLAB")


def _beams(z0, z1, billed_z0=None):
    """Four bands round P1 (0.20 wide), full depth z0..z1; billed from billed_z0 (downstand) when given."""
    out = []
    for i, (x0, x1, y0, y1) in enumerate([(0.0, 4.4, 0.0, 0.2), (0.0, 4.4, 3.2, 3.4),
                                          (0.0, 0.2, 0.2, 3.2), (4.2, 4.4, 0.2, 3.2)]):
        phys = OV.box(x0, x1, y0, y1, z0, z1)
        billed = None if billed_z0 is None else OV.box(x0, x1, y0, y1, z0, billed_z0)
        out.append(OV.Element("B%d" % i, "BEAM", phys, billed))
    return out


def test_3d_c1_each_intersection_once():
    slab = OV.Element("P1", "SLAB", OV.box(0.2, 4.2, 0.2, 3.2, 3.30, 3.50))
    r = OV.check_ownership([slab] + _beams(3.00, 3.50))
    assert r["status"] == "PASS"
    assert r["elements"]["P1"]["billed_m3"] == pytest.approx(2.400, abs=1e-6)


def test_3d_plate_over_beams_with_full_depth_beams_is_double():
    """Adverse: the slab billed as the plate over the beams (C2) while the beams keep their full depth (C1)."""
    plate = OV.Element("P1", "SLAB", OV.box(0.0, 4.4, 0.0, 3.4, 3.30, 3.50))
    r = OV.check_ownership([plate] + _beams(3.00, 3.50))
    assert r["status"] == "FAIL"
    assert r["double_m3"] == pytest.approx((4.4 * 3.4 - 12.0) * 0.20, abs=1e-6)   # band area 2.96 m2 x t


def test_3d_c2_consistent_and_same_total_as_c1():
    plate = OV.Element("P1", "SLAB", OV.box(0.0, 4.4, 0.0, 3.4, 3.30, 3.50))
    beams = _beams(3.00, 3.50, billed_z0=3.30)
    prec = dict(OV.PRECEDENCE_ROUTE_G, SLAB=45)
    est = dict(OV.ESTABLISHED_PAIRS_ROUTE_G)
    est[frozenset(("BEAM", "SLAB"))] = "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1: plate over the beams"
    r2 = OV.check_ownership([plate] + beams, prec, est)
    assert r2["status"] == "PASS"
    r1 = OV.check_ownership([OV.Element("P1", "SLAB", OV.box(0.2, 4.2, 0.2, 3.2, 3.30, 3.50))] + _beams(3.00, 3.50))
    assert r2["billed_sum_m3"] == pytest.approx(r1["billed_sum_m3"], abs=1e-6)
    s2, moved = SL.convention("C2_PLATE_OVER_BEAMS", 2.400, [(4.4 * 3.4 - 12.0, 0.20)])
    assert s2 == pytest.approx(r2["elements"]["P1"]["billed_m3"], abs=1e-6) and moved == pytest.approx(0.592)


def test_compare_needs_one_stated_convention():
    a = dict(convention="C1_PANEL_BETWEEN_BEAM_FACES", m3=4.440)
    with pytest.raises(ValueError, match="state the slab"):
        SL.compare(a, dict(m3=4.4))
    with pytest.raises(ValueError, match="convert one side"):
        SL.compare(a, dict(convention="C2_PLATE_OVER_BEAMS", m3=5.0))
    assert SL.compare(a, dict(a, m3=4.0))["diff_m3"] == pytest.approx(0.44)


def test_reconcile_names_the_residual():
    r = SL.reconcile(61.0, 60.0, [("a", 0.6), ("b", 0.3)])
    assert r["residual_m3"] == pytest.approx(0.1) and not r["closed"]
