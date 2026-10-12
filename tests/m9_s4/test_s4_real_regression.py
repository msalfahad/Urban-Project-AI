"""M9 S4 - regression on the REAL plan drawing for the exact rooms S2 / S3 lost (skipped unless the drawing and the
frozen Round-5 registers are given; neither is in the repository):

    URBAN_REAL_PLAN_DXF   the architectural plan DXF of the reference project
    URBAN_R5_REGISTERS    the directory of the frozen Round-5 registers (PHYSICAL_SPACE_REGISTER.json,
                          FLOOR_AREA_CONSERVATION_REGISTER.json)

The expected values are READ from the frozen registers at run time (no project figure is written here): each room
below is the S4 face at the Round-5 space's centroid, and must equal the Round-5 physical space within 0.01 m2.
The ids are the Round-5 register keys (content hashes of the source linework)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from engine.source import member_detection as MD

DXF = os.environ.get("URBAN_REAL_PLAN_DXF")
R5 = os.environ.get("URBAN_R5_REGISTERS")
pytestmark = pytest.mark.skipif(not (DXF and R5 and Path(DXF).is_file() and Path(R5).is_dir()),
                                reason="real plan drawing / Round-5 registers not given (URBAN_REAL_PLAN_DXF, "
                                       "URBAN_R5_REGISTERS)")

# the rooms S2 / S3 measured wrong (root causes in research/urban_m9_s4/ROOT_CAUSE_REGISTER.md)
LOST_ROOMS = {
    "PS:1F:SITE-22b96446836c3d8d": "RC-1 + RC-2: a door swing made the archway a door; the vestibule split off",
    "PS:GF:SITE-88d9dbffd47c417a": "RC-1 + RC-2: the lobby door's swing served another gap; the lobby split off",
    "PS:GF:SITE-dda89794d15dfb61": "RC-3 + RC-4: wall bodies leaked in; the bathroom door's doorway piece joined",
    "PS:GF:SITE-0e9a7a85e795446f": "RC-3 + RC-4: a wall body strip and the doorway piece joined",
    "PS:1F:SITE-c46cb88cea7decbb": "RC-4: the doorway piece of a one-face door closure joined",
}
SHAFTS = ("PS:GF:SITE-0bb9132c5c034229", "PS:1F:SITE-195dbe4bca9e732e", "PS:2F:SITE-fd5fd08ac9eb9313")


@pytest.fixture(scope="module")
def run():
    from tools import urban_boq_m9 as M9
    room, arch, _E = M9.arch_compute(DXF, method="ARCH_TAKEOFF_V1")
    ps = {r["space_id"]: r for r in json.loads((Path(R5) / "PHYSICAL_SPACE_REGISTER.json").read_text())["rows"]}
    fc = json.loads((Path(R5) / "FLOOR_AREA_CONSERVATION_REGISTER.json").read_text())
    return room, arch, ps, fc


def _at(arch, floor, p):
    for r in arch["rooms"]:
        if r["floor"] == floor and MD.point_in_poly(p[0], p[1], r["polygon"]) and \
                not any(MD.point_in_poly(p[0], p[1], h) for h in r.get("hole_polygons") or ()):
            return r
    return None


@pytest.mark.parametrize("sid", sorted(LOST_ROOMS))
def test_the_lost_room_is_recovered(run, sid):
    _room, arch, ps, _fc = run
    ref = ps[sid]
    r = _at(arch, ref["floor"], ref["centroid"])
    assert r is not None and r["class"] == "ROOM", LOST_ROOMS[sid]
    assert r["area_m2"] == pytest.approx(ref["area_m2"], abs=0.01), LOST_ROOMS[sid]


@pytest.mark.parametrize("sid", SHAFTS)
def test_the_stacked_shaft_is_a_shaft(run, sid):
    _room, arch, ps, _fc = run
    ref = ps[sid]
    r = _at(arch, ref["floor"], ref["centroid"])
    assert r is not None and r["codes"] == ["SHAFT"] and r["area_m2"] == pytest.approx(ref["area_m2"], abs=0.01)


def test_the_outlined_void_is_never_floor(run):
    _room, arch, _ps, fc = run
    r5 = sum(c["area_m2"] for c in fc["components"] if c["class"] == "VOID" and c["floor"] == "1F")
    s4 = next(f for f in arch["floor_areas"] if f["floor"] == "1F")
    in_r5_room = [c["area_m2"] for c in fc["components"] if c["class"] == "VOID" and c["floor"] == "1F"
                  and c["component"] == "VOID"]
    assert s4["categories_m2"]["VOID"] == pytest.approx(max(in_r5_room), abs=0.01)
    assert s4["categories_m2"]["VOID"] <= r5 + 1e-6


def test_every_floor_balances(run):
    _room, arch, _ps, _fc = run
    for fa in arch["floor_areas"]:
        assert all(c["state"] == "BALANCED" for c in fa["checks"]), (fa["floor"], fa["checks"])
