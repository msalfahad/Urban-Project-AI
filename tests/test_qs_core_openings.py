"""An opening belongs to one wall, or to none.

The defect these tests exist to prevent shared a floor's openings out across wall-thickness bands in proportion
to wall length.  That keeps the floor total and corrupts the split between two separately priced lines, which is
the worst kind of error: invisible in the summary, wrong in the tender.
"""

from __future__ import annotations

import random

import pytest

from engine.qs_core import geom, identity, invariants, openings as op
from engine.qs_core.entities import HOST_ASSIGNED, HOST_WALL_UNRESOLVED
from engine.qs_core.synthetic import TOL, opening, wall_band


def band_x(ref, y0, thickness, x0=0.0, x1=6.0):
    return wall_band(ref, (x0, y0, x1, y0 + thickness), thickness, geom.AXIS_X)


def band_y(ref, x0, thickness, y0=0.0, y1=6.0):
    return wall_band(ref, (x0, y0, x0 + thickness, y1), thickness, geom.AXIS_Y)


def door_through_x_band(ref, band, at, width=0.90):
    b = band.bbox
    return opening(ref, (at, b.y0, at + width, b.y1), geom.AXIS_X, width, 2.10)


# ------------------------------------------------------------------ the plain cases
def test_a_door_wholly_inside_a_150_band_is_hosted_by_it():
    thin, thick = band_x("W-150", 0.0, 0.15), band_x("W-200", 3.0, 0.20)
    o = door_through_x_band("OP-1", thin, 1.0)
    op.assign_opening_host(o, [thin, thick], TOL)
    assert o.host_status == HOST_ASSIGNED
    assert o.host_component_ref == "W-150" and o.host_thickness == 0.15
    assert o.host_evidence[0].rule == "HOST_PROVED_BY_GEOMETRY"


def test_a_door_wholly_inside_a_200_band_is_hosted_by_it():
    thin, thick = band_x("W-150", 0.0, 0.15), band_x("W-200", 3.0, 0.20)
    o = door_through_x_band("OP-1", thick, 1.0)
    op.assign_opening_host(o, [thin, thick], TOL)
    assert o.host_status == HOST_ASSIGNED and o.host_thickness == 0.20


def test_several_openings_each_go_to_their_own_band():
    thin, thick, side = band_x("W-150", 0.0, 0.15), band_x("W-200", 3.0, 0.20), band_y("W-100", 8.0, 0.10)
    ops = [door_through_x_band("OP-1", thin, 1.0), door_through_x_band("OP-2", thin, 3.0),
           door_through_x_band("OP-3", thick, 2.0),
           opening("OP-4", (8.0, 1.0, 8.10, 1.9), geom.AXIS_Y, 0.90, 2.10)]
    reg = op.build_opening_register(ops, [thin, thick, side], TOL)
    hosts = {o["OPENING_REF"]: o["HOST_COMPONENT_REF"] for o in reg["REGISTER"]}
    assert hosts == {"OP-1": "W-150", "OP-2": "W-150", "OP-3": "W-200", "OP-4": "W-100"}
    assert reg["DEDUCTION_BY_THICKNESS_M2"] == {"0.1": pytest.approx(1.89), "0.15": pytest.approx(3.78),
                                                "0.2": pytest.approx(1.89)}


def test_an_opening_near_a_junction_still_has_one_proved_host():
    along_x = band_x("W-X", 0.0, 0.15, x0=0.0, x1=6.0)
    along_y = band_y("W-Y", 6.0, 0.20, y0=0.0, y1=5.0)
    o = door_through_x_band("OP-1", along_x, 4.9)          # ends 20 cm short of the corner
    op.assign_opening_host(o, [along_x, along_y], TOL)
    assert o.host_status == HOST_ASSIGNED and o.host_component_ref == "W-X"


def test_a_band_with_no_openings_keeps_its_gross_area():
    thin, thick = band_x("W-150", 0.0, 0.15), band_x("W-200", 3.0, 0.20)
    reg = op.build_opening_register([door_through_x_band("OP-1", thin, 1.0)], [thin, thick], TOL)
    rows = {r["COMPONENT_REF"]: r for r in op.wall_band_quantities([thin, thick], reg, 3.0, True)}
    assert rows["W-200"]["OPENING_DEDUCTION_M2"] == 0.0
    assert rows["W-200"]["NET_AREA_M2"] == rows["W-200"]["GROSS_AREA_M2"]
    assert rows["W-150"]["NET_AREA_M2"] < rows["W-150"]["GROSS_AREA_M2"]


# ------------------------------------------------------------------ the cases that must NOT be resolved
def test_an_opening_straddling_two_collinear_bands_is_unresolved():
    left = wall_band("W-A", (0.0, 0.0, 3.0, 0.15), 0.15, geom.AXIS_X)
    right = wall_band("W-B", (3.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    o = opening("OP-1", (2.55, 0.0, 3.45, 0.15), geom.AXIS_X, 0.90, 2.10)
    op.assign_opening_host(o, [left, right], TOL)
    assert o.host_status == HOST_WALL_UNRESOLVED
    assert o.host_component_ref is None and o.host_thickness is None
    assert len(o.host_candidates) == 2


def test_two_bands_drawn_over_each_other_leave_the_host_ambiguous():
    a = wall_band("W-A", (0.0, 0.0, 6.0, 0.16), 0.16, geom.AXIS_X)
    b = wall_band("W-B", (0.0, 0.0, 6.0, 0.17), 0.17, geom.AXIS_X)
    o = opening("OP-1", (1.0, 0.0, 1.9, 0.165), geom.AXIS_X, 0.90, 2.10)
    op.assign_opening_host(o, [a, b], TOL)
    assert o.host_status == HOST_WALL_UNRESOLVED
    assert o.host_evidence[0].rule == "HOST_AMBIGUOUS"
    assert "apportioning" in o.host_evidence[0].detail["WHY"]


def test_an_opening_with_no_wall_anywhere_near_it_is_unresolved():
    band = band_x("W-150", 0.0, 0.15)
    o = opening("OP-1", (1.0, 9.0, 1.9, 9.15), geom.AXIS_X, 0.90, 2.10)
    op.assign_opening_host(o, [band], TOL)
    assert o.host_status == HOST_WALL_UNRESOLVED
    assert o.host_evidence[0].rule == "NO_HOST_CANDIDATE"


def test_an_opening_that_crosses_its_candidate_rather_than_running_along_it_is_unresolved():
    band = band_y("W-Y", 3.0, 0.20, y0=0.0, y1=6.0)
    o = opening("OP-1", (2.6, 2.0, 3.5, 2.15), geom.AXIS_X, 0.90, 2.10)
    op.assign_opening_host(o, [band], TOL)
    assert o.host_status == HOST_WALL_UNRESOLVED


# ------------------------------------------------------------------ duplicates, rotation, and the register
def test_duplicate_opening_geometry_is_reported_rather_than_quietly_doubled():
    band = band_x("W-150", 0.0, 0.15)
    a = door_through_x_band("OP-1", band, 1.0)
    b = door_through_x_band("OP-2", band, 1.0)
    report = identity.assign_identity([a, b], "R1")
    assert report["DUPLICATE_GEOMETRY_FINGERPRINTS"]
    reg = op.build_opening_register([a, b], [band], TOL)
    assert reg["OPENING_COUNT"] == 2 and reg["ASSIGNED_COUNT"] == 2
    assert reg["TOTAL_OPENING_AREA_M2"] == pytest.approx(2 * 0.90 * 2.10)


def test_the_same_plan_rotated_ninety_degrees_gives_the_same_answer():
    flat = band_x("W-150", 0.0, 0.15)
    o1 = door_through_x_band("OP-1", flat, 1.0)
    op.assign_opening_host(o1, [flat], TOL)
    upright = band_y("W-150", 0.0, 0.15)
    o2 = opening("OP-1", (0.0, 1.0, 0.15, 1.9), geom.AXIS_Y, 0.90, 2.10)
    op.assign_opening_host(o2, [upright], TOL)
    assert o1.host_status == o2.host_status == HOST_ASSIGNED
    assert o1.host_thickness == o2.host_thickness == 0.15
    assert o1.host_confidence == o2.host_confidence


def test_the_register_reconciles_and_blocks_the_floor_that_holds_an_unresolved_opening():
    left = wall_band("W-A", (0.0, 0.0, 3.0, 0.15), 0.15, geom.AXIS_X)
    right = wall_band("W-B", (3.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    clear = opening("OP-1", (0.5, 0.0, 1.4, 0.15), geom.AXIS_X, 0.90, 2.10)
    straddling = opening("OP-2", (2.55, 0.0, 3.45, 0.15), geom.AXIS_X, 0.90, 2.10)
    reg = op.build_opening_register([clear, straddling], [left, right], TOL)
    rows = op.wall_band_quantities([left, right], reg, 3.0, True)
    assert reg["ASSIGNED_AREA_M2"] + reg["UNRESOLVED_AREA_M2"] == pytest.approx(reg["TOTAL_OPENING_AREA_M2"])
    assert all(r["STATUS"] == "BLOCKED_BY_UNRESOLVED_OPENING" for r in rows)
    assert invariants.deductions_reconcile(reg, rows, 1e-9)["PASS"]
    assert invariants.unresolved_never_allocated(reg, rows, 1e-9)["PASS"]
    assert sum(r["OPENING_DEDUCTION_M2"] for r in rows) == pytest.approx(clear.area)


# ------------------------------------------------------------------ a property, over many random plans
@pytest.mark.parametrize("seed", range(12))
def test_whatever_the_plan_no_deduction_is_ever_divided(seed):
    rnd = random.Random(seed)
    bands, ops = [], []
    for i in range(rnd.randint(2, 5)):
        t = rnd.choice([0.10, 0.15, 0.20, 0.25])
        y = i * 3.0
        bands.append(wall_band(f"W-{i}", (0.0, y, rnd.uniform(4.0, 9.0), y + t), t, geom.AXIS_X))
    for j in range(rnd.randint(1, 6)):
        b = rnd.choice(bands).bbox
        w = rnd.uniform(0.7, 1.2)
        at = rnd.uniform(-1.0, b.x1)
        ops.append(opening(f"OP-{j}", (at, b.y0, at + w, b.y1), geom.AXIS_X, w, 2.10))
    reg = op.build_opening_register(ops, bands, TOL)
    rows = op.wall_band_quantities(bands, reg, 3.0, True)
    assert reg["ASSIGNED_AREA_M2"] + reg["UNRESOLVED_AREA_M2"] == pytest.approx(reg["TOTAL_OPENING_AREA_M2"])
    assert sum(r["OPENING_DEDUCTION_M2"] for r in rows) == pytest.approx(reg["ASSIGNED_AREA_M2"])
    for o in reg["REGISTER"]:
        assert o["HOST_COMPONENT_REF"] is None or isinstance(o["HOST_COMPONENT_REF"], str)
    assert invariants.one_host_per_opening(reg)["PASS"]
