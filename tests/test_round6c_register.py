"""Round 6C: 69 polygons are not 69 rooms.

Every test here is about the difference between measuring a polygon and
knowing what it is. The four numbers stay four numbers, a container of
rooms is not a room, sheet content is not a room, the strip in front of a
fitting is not a room, and a label belongs to the room it names rather
than to the smallest box around the text.
"""

from __future__ import annotations

import io
import tokenize

import pytest
from shapely.geometry import box

from engine import drawing_role as drole
from engine import round6c_fixtures as fx
from engine import round6c_selftest as r6c
from engine import space_register as sreg


def _code(module):
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


def _rows(*specs):
    out = []
    for i, (poly, label, basis) in enumerate(specs, start=1):
        out.append({"space_id": f"PS-T-{i:03d}", "region_id": "DR-T",
                    "polygon": poly, "area_m2": round(poly.area / 1e6, 4),
                    "basis": basis, "label_raw": label,
                    "principal_dims_mm": [], "blockers": [],
                    "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
                    "identity_authority": "", "geometry_authority": "",
                    "normalized_identity": label, "wall_band_ids": [],
                    "face_contacts": [], "cad_provenance": []})
    return out


class _Region:
    region_id, x0, y0, x1, y1 = "DR-T", 0.0, 0.0, 100000.0, 100000.0

    def contains(self, x, y):
        return True


# --------------------------------------------------- §14 the fourteen cases

@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_every_round_6c_case_holds(case):
    res = r6c.check(case)
    assert res.passed, f"{case.name}: {res.failures} observed={res.observed}"


def test_the_round_6c_requirements_are_frozen():
    rep = r6c.assert_frozen()
    assert rep["cases"] == 14
    assert rep["passed"] == 14


# ------------------------------------------- §1 four numbers, not one number

def test_the_four_areas_are_four_different_numbers():
    reg = sreg.build(_rows(
        (box(0, 0, 6000, 4000), "MAJLIS", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(7000, 0, 9000, 1000), "", "CLEAR_FACE_NOT_ESTABLISHED"),
    ), [_Region()])
    areas = reg.areas()
    assert areas["MEASURED_CANDIDATE_AREA_M2"] == 24.0
    assert areas["PHYSICAL_SPACE_AREA_M2"] == 24.0
    assert areas["RELEASE_ELIGIBLE_GEOMETRY_AREA_M2"] == 24.0
    assert areas["TRADE_MEASUREMENT_AREA_M2"] is None


def test_a_measured_candidate_is_not_a_released_one():
    """A polygon with a basis that nothing calls a space releases nothing."""
    reg = sreg.build(_rows(
        (box(0, 0, 2000, 500), "", "CLEAR_FACE_NOT_ESTABLISHED"),
    ), [_Region()])
    a = reg.areas()
    assert a["RELEASE_ELIGIBLE_GEOMETRY_AREA_M2"] == 0.0
    assert a["PHYSICAL_SPACE_AREA_M2"] == 0.0


# --------------------------------------------- §5 a parent and its children

def test_a_parent_of_spaces_never_releases_with_them():
    rows = _rows(
        (box(0, 0, 12000, 6000), "", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(0, 0, 4000, 6000), "BED ONE", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(4200, 0, 8000, 6000), "BED TWO", "CLEAR_INTERNAL_FINISH_FACE"),
    )
    reg = sreg.build(rows, [_Region()])
    by = {e.space_id: e for e in reg.entries}
    plate = by["PS-T-001"]
    assert plate.candidate_role == sreg.SUPER_REGION
    assert not plate.may_release
    assert all(by[c].may_release for c in ("PS-T-002", "PS-T-003"))
    assert reg.areas()["RELEASE_ELIGIBLE_GEOMETRY_AREA_M2"] == 24.0 + 22.8


def test_a_container_of_nothing_that_is_a_space_is_still_a_room():
    """A rectangle drawn in a room does not turn the room into a plate."""
    rows = _rows(
        (box(0, 0, 6000, 5000), "MAJLIS", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(2000, 2000, 3200, 2800), "", "CLEAR_FACE_NOT_ESTABLISHED"),
    )
    reg = sreg.build(rows, [_Region()])
    room = reg.entries[0]
    assert room.relation == sreg.REL_PARENT
    assert room.candidate_role == sreg.PHYSICAL_ROOM
    assert room.may_release


# ----------------------------------------------- §4 repeated sheet geometry

def test_geometry_in_three_regions_is_sheet_content():
    class _R:
        def __init__(self, rid, x0):
            self.region_id, self.x0, self.y0 = rid, x0, 0.0
            self.x1, self.y1 = x0 + 50000.0, 50000.0

        def contains(self, x, y):
            return True

    regions = [_R(f"DR-{i}", i * 100000.0) for i in range(3)]
    rows = []
    for i, r in enumerate(regions, start=1):
        rows.append({"space_id": f"PS-{i}", "region_id": r.region_id,
                     "polygon": box(r.x0 + 1000, 1000, r.x0 + 15000, 3000),
                     "area_m2": 28.0, "basis": "CLEAR_INTERNAL_FINISH_FACE",
                     "label_raw": "", "principal_dims_mm": [],
                     "blockers": [], "release_status":
                     "RELEASE_ELIGIBLE_GEOMETRY", "identity_authority": "",
                     "geometry_authority": "", "normalized_identity": "",
                     "wall_band_ids": [], "face_contacts": [],
                     "cad_provenance": []})
    reg = sreg.build(rows, regions)
    assert all(e.candidate_role == sreg.DRAWING_ARTIFACT
               for e in reg.entries)
    assert reg.areas()["RELEASE_ELIGIBLE_GEOMETRY_AREA_M2"] == 0.0


def test_two_regions_are_not_enough_to_call_it_sheet_content():
    """Two identical flats are two flats. Three is the sheet."""
    assert sreg.REPEAT_MIN_REGIONS >= 3


# ------------------------------------------------- a fitting is not a wall

def test_only_the_front_face_of_a_lining_blocks_a_candidate():
    st = sreg.StackedBand("LIN", "WALL", "H", shared_face_mm=1000.0,
                          far_face_mm=1500.0)
    front = {"face_contacts": [("LIN", 1500.0)]}
    behind = {"face_contacts": [("LIN", 1000.0)]}
    assert sreg.stops_at_a_fitting(front, {"LIN": st})
    assert not sreg.stops_at_a_fitting(behind, {"LIN": st})


# --------------------------------------------------- §6 a label to one room

def test_a_label_never_takes_the_smallest_box_around_it():
    rows = _rows(
        (box(0, 0, 6000, 5000), "", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(1000, 1000, 2000, 1600), "", "CLEAR_FACE_NOT_ESTABLISHED"),
    )
    reg = sreg.build(rows, [_Region()])
    reg = sreg.reconcile_labels(reg, [r6c._Label("MAJLIS", 1500, 1300)],
                                rows)
    v = reg.labels[0]
    assert v.status == sreg.LABEL_ONE_SPACE
    assert v.space_id == "PS-T-001"


def test_two_claimants_that_do_not_contain_each_other_resolve_to_neither():
    rows = _rows(
        (box(0, 0, 6000, 4000), "", "CLEAR_INTERNAL_FINISH_FACE"),
        (box(4000, 0, 10000, 4000), "", "CLEAR_INTERNAL_FINISH_FACE"),
    )
    reg = sreg.build(rows, [_Region()])
    reg = sreg.reconcile_labels(reg, [r6c._Label("DINING", 5000, 2000)],
                                rows)
    v = reg.labels[0]
    assert v.status == sreg.LABEL_EXCEPTION
    assert v.why == sreg.WHY_SEVERAL


# -------------------------------------------------- §3 what a region shows

def test_only_a_plan_of_an_established_floor_may_release_rooms():
    assert set(drole.BOQ_ELIGIBLE_ROLES) <= set(drole.ROLES)
    for role in drole.ROLES:
        r = drole.RegionRole(region_id="DR-1", drawing_role=role,
                             floor_level="GROUND")
        assert r.may_release_rooms == (role in drole.BOQ_ELIGIBLE_ROLES)
    r = drole.RegionRole(region_id="DR-1", drawing_role=drole.FLOOR_PLAN)
    assert r.floor_level == drole.FLOOR_NOT_ESTABLISHED
    assert not r.may_release_rooms


def test_unknown_is_not_a_floor_plan_by_default():
    r = drole.RegionRole(region_id="DR-1", drawing_role=drole.UNKNOWN,
                         floor_level="GROUND")
    assert not r.may_release_rooms


def test_a_site_plan_is_read_as_a_site_plan_not_as_a_plan():
    """The longest matched word wins, or SITE PLAN is a floor plan."""
    class _T:
        value, height, x, y = "SITE PLAN", 600.0, 0.0, 0.0

    hits = drole._title_hits([_T()], 250.0)
    assert hits and hits[0][0] == drole.SITE_PLAN


def test_a_room_stamp_can_never_retitle_a_drawing():
    class _T:
        value, height, x, y = "PLAN ROOM", 250.0, 10.0, 20.0

    assert drole._title_hits([_T()], 250.0, [(10.0, 20.0)]) == []


# ------------------------------------------------ what this round is not

def test_no_region_id_and_no_project_geometry_is_hardcoded():
    for module in (sreg, drole, fx):
        code = _code(module)
        assert "DR-002" not in code
        assert "7757" not in code
        assert "9.675" not in code
        assert "28.2688" not in code


def test_round_6c_implements_no_trade_layer():
    code = _code(sreg) + " " + _code(drole)
    for banned in ("FunctionalZone", "TradeMeasurementZone", "ceramic",
                   "waste", "price"):
        assert banned not in code


def test_a_stair_is_a_space_and_not_a_room_area():
    assert sreg.STAIR in sreg.SPACE_ROLES
    assert sreg.STAIR in sreg.NOT_RELEASED_AS_A_ROOM
    e = sreg.Entry(space_id="S", candidate_role=sreg.STAIR)
    assert e.is_space and not e.may_release
