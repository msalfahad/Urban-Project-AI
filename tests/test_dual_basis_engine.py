"""Synthetic checks for the dual-basis layer, the contractor convention and
the CAD-trace registration. No P7757 value."""

from __future__ import annotations

import pytest

from engine import cad_trace_registration as R
from engine import contractor_measurement as C
from engine import quantity_layers as Q
from engine import wall_face_set as FS
from engine import wall_treatment_engine as E
from tests.test_wall_treatment_engine import _face, _reg

PL = "NORMAL_INTERNAL_PLASTER"


def _rulebook():
    return {
        "HEIGHT_GROUND": C.rule("HEIGHT_GROUND", 3.6, "m", source_type="SITE_RECORD",
                                reference="synthetic record", scope="ground rooms"),
        "OPENING_DEDUCTION_RULE": C.rule("OPENING_DEDUCTION_RULE", "HALF_OPENING_DEDUCTION",
                                         None, source_type="CONTRACTOR_MEASUREMENT_RULE",
                                         reference="synthetic record", scope="all openings"),
        "DOOR_WIDTH": C.rule("DOOR_WIDTH", 1.0, "m", source_type="SITE_RECORD", reference="r", scope="doors"),
        "DOOR_HEIGHT": C.rule("DOOR_HEIGHT", 2.3, "m", source_type="SITE_RECORD", reference="r", scope="doors"),
        "DOOR_REVEAL_DEPTH": C.rule("DOOR_REVEAL_DEPTH", 0.2, "m", source_type="SITE_RECORD", reference="r", scope="doors"),
    }


def _set_with_door():
    door = {"OPENING_ID": "D1", "TYPE": "DOOR", "HOSTED_IN": "A"}
    return FS.build_face_set(set_id="S", faces=[_face("A", 10.0)], openings=[door],
                             trade=PL, basis="WALL_FACE_SET", floor="GROUND")


def test_contractor_rule_refuses_engineering_source_types():
    with pytest.raises(ValueError):
        C.rule("X", 1, "m", source_type="DRAWING", reference="r", scope="s")


def test_two_bases_coexist_and_differ_by_convention_only():
    fs = _set_with_door()
    eng = E.calculate(fs, _reg(3.0), treatment=PL, floor="GROUND")
    con = C.calculate_contractor(fs, _rulebook(), treatment=PL, floor="GROUND")
    # engineering: 10 x 3.0 - 1.0 x 2.2 = 27.8 ; contractor: 10 x 3.6 - 0.5 x (1.0 x 2.3) = 34.85
    assert eng["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 27.8
    assert con["RESULT"]["CONTRACTOR_MEASUREMENT_QUANTITY_M2"] == 34.85
    assert con["THIS_IS_A_COMMERCIAL_CONVENTION_NOT_GEOMETRY"] is True
    dec = C.decompose(fs, eng, _reg(3.0), _rulebook(), treatment=PL, floor="GROUND",
                      engine_calculate=E.calculate)
    assert dec["DECOMPOSABLE"] is True
    assert dec["DRIVERS"]["HEIGHT"] == 6.0            # 10 x 0.6
    assert dec["DRIVERS"]["DOOR_DIMENSION"] == -0.1   # 2.3 vs 2.2 deducted in full
    assert dec["DRIVERS"]["OPENING_DEDUCTION"] == 1.15  # half of 2.3 not deducted
    assert dec["DRIVERS"]["OTHER"] == 0.0
    assert dec["SUM_OF_DRIVERS_M2"] == dec["DELTA_M2"]


def test_layered_item_keeps_every_layer_and_flags_basis_difference():
    item = Q.layered_item(item_id="I", trade=PL, unit="m2",
                          physical={"LENGTH_M": 10.0, "STATUS": "ESTABLISHED"},
                          measured_net={"VALUE": 27.8, "STATE": "OWNER_PARAMETRIC_QUANTITY"},
                          contractor={"VALUE": 34.85, "RULES": ["HALF_OPENING_DEDUCTION"],
                                      "SOURCE_TYPE": "SITE_RECORD"},
                          waste_factor=0.05, rate=None)
    assert item["OWNER_PARAMETRIC_QUANTITY"] == 27.8
    assert item["PROVISIONAL_DEFAULT_QUANTITY"] is None
    assert item["PROCUREMENT_QUANTITY"] == 29.19
    assert item["RATE"]["STATUS"] == "NO_RATE_QUOTED" and item["AMOUNT"]["VALUE"] is None
    assert item["DIFFERENCE_CLASS"] == "MEASUREMENT_BASIS_DIFFERENCE"
    assert item["NOT_AN_APPROVED_BOQ"] is True


def test_registration_fits_from_pairs_and_links_by_geometry():
    # 20 mm per pixel, x offset 100 px, y flipped
    xp = [(-10000, 100 - 500), (0, 100), (10000, 600)]
    yp = [(-20000, 1400), (0, 400), (10000, -100)]
    reg = R.Registration(xp, yp)
    assert abs(reg.x["MM_PER_PX"] - 20.0) < 1e-6 and abs(reg.y["MM_PER_PX"] + 20.0) < 1e-6
    run = {"AXIS": "H", "FIXED_MM": -20000, "FROM_MM": 0, "TO_MM": 10000}
    ok = R.link_status(reg, run, [[100, 1400], [600, 1400]])
    assert ok["CAD_TRACE_LINK_STATUS"] == "ESTABLISHED"
    off = R.link_status(reg, run, [[100, 1300], [600, 1300]])      # 100 px away
    assert off["CAD_TRACE_LINK_STATUS"] == "NOT_ESTABLISHED"
    short = R.link_status(reg, run, [[100, 1400], [400, 1400]])    # one end matches
    assert short["CAD_TRACE_LINK_STATUS"] == "PROVISIONAL"
