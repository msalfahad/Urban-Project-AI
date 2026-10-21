"""M9 S5 - the real plan (skipped unless URBAN_REAL_PLAN_DXF is set): the open space whose words need different
finishes is split along drawn lines only, every floor still balances, the void above is carried onto the plan below
(corroborated by the lower plan's own X-marked opening) and its ceiling is counted once. No client quantity is written
here: the assertions are structural (classes, conservation, shares), never figures of the drawing."""

from __future__ import annotations

import os

import pytest

DXF = os.environ.get("URBAN_REAL_PLAN_DXF")
pytestmark = pytest.mark.skipif(not DXF, reason="real plan not provided (URBAN_REAL_PLAN_DXF)")


@pytest.fixture(scope="module")
def run():
    from tools import urban_boq_m9 as M9
    room, arch, _E = M9.arch_compute(DXF, method="ARCH_TAKEOFF_V1")
    return room, arch


def test_merged_space_split_on_drawn_lines(run):
    _, arch = run
    recs = [z for fa in arch["floor_areas"] for z in fa.get("zones") or ()]
    split = [z for z in recs if z["state"] == "SPLIT"]
    assert split, "the merged open space is split along its drawn lines"
    for z in split:
        assert abs(sum(x["area_m2"] for x in z["zones"]) - z["area_m2"]) < 1e-3       # an exact partition
        fams = {x["class"] for x in z["zones"]}
        assert "MIXED" in fams and "ROOM" in fams
        left = sum(x["area_m2"] for x in z["zones"] if x["class"] == "MERGED")
        assert left < 0.05 * z["area_m2"]                                               # unallocated part is small


def test_every_floor_balances(run):
    _, arch = run
    for fa in arch["floor_areas"]:
        assert all(c["state"] == "BALANCED" for c in fa["checks"]), fa["floor"]


def test_void_above_corroborated_and_ceiling_once(run):
    room, arch = run
    dh = arch["run"]["double_height"]
    assert dh and all(d["state"] == "APPLIED" and d["corroborated_by"] for d in dh)
    up = sum(ln["measured_net"] or 0 for ln in room["lines"] if ln["item_code"] == "FIN.CEILING" and
             ln["calculation"]["inputs"].get("ceiling_type") == "DOUBLE_HEIGHT")
    below = sum(r["double_height_m2"] for r in arch["rooms"])
    assert up > 0 and abs(up - below) < 1e-3                       # removed below exactly as much as carried above


def test_shared_wet_doorways_counted_once(run):
    room, _ = run
    keys = [(ln["location"]["floor"], ln["physical_element"]) for ln in room["lines"]
            if ln["item_code"] == "FIN.WP.DOORWAY"]                 # opening ids are numbered per floor
    assert len(keys) == len(set(keys))
