"""Phase N10 - the facade of a floor (ARCH_TAKEOFF_V2.9, UP-FACADE-001 draft), against hand truth (n10_truth.py).

The facade run is the exterior outline of the floor's wall network: the outer cycle of the plan topology, where
every opening is closed on its outer wall face, so the run includes the openings. A wall network standing inside a
room (a free-standing column) is an island, never a facade. The facade area of a floor runs from its F.F.L. to the
next floor's F.F.L. (both read from the floor's section band; a stated project fact otherwise): gross = run x
height, each opening on the outline deducted by width x its own band. The exterior finish is a separate item: without
a stated specification it is held. A second outline on the floor is reported, never added; an outline around the
building (a boundary wall) holds the facade."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tools"))

import arch_change_verify as V                                # noqa: E402
import n10_fixtures as F                                      # noqa: E402
import n10_run as R                                           # noqa: E402
import n10_truth as T                                         # noqa: E402

A = 1e-6
FINISH = {"facade": {"finish": {"value": "PLASTER_AND_PAINT", "authority": "OWNER_PROJECT_FACT: synthetic"}}}


@pytest.fixture(scope="module")
def ex(tmp_path_factory):
    cache, root = {}, tmp_path_factory.mktemp("n10_fac")

    def get(section="FACADE", facts=None, method=R.V29, roles=None, **kw):
        key = (section, repr(facts), method, roles, tuple(sorted(kw.items())))
        if key not in cache:
            name = f"f{len(cache)}"
            dxf = F.masonry_room(root / f"{name}.dxf", section=section, **kw)
            cache[key] = R.run_facts(dxf, root / f"o_{name}", facts, method=method, roles=roles) if facts else \
                R.run(dxf, root / f"o_{name}", method=method, roles=roles)
        return cache[key]
    return get


def _fac(out):
    return R.load(out, "FACADE.json")["floors"][0]


def test_hand_truth_is_consistent():
    assert T.FAC_NET == pytest.approx(50.60, abs=1e-9) and T.FAC_RUN == pytest.approx(15.60, abs=1e-9)
    assert T.CUR_FAC_RUN == pytest.approx(12.226548, abs=1e-6)


def test_facade_run_and_area_from_floor_to_floor(ex):
    out = ex()
    rec = _fac(out)
    assert rec["state"] == "ONE_OUTLINE" and rec["islands"] == 0
    o = rec["outlines"][0]
    assert o["perimeter_m"] == pytest.approx(T.FAC_RUN, abs=A)
    assert o["plate_m2"] == pytest.approx(T.FAC_PLATE, abs=A)
    assert sorted(round(x["width_m"], 6) for x in o["openings"]) == [1.0, 1.5]
    assert rec["height"]["state"] == "ESTABLISHED" and rec["height"]["height_m"] == pytest.approx(T.FAC_H, abs=A)
    run = R.the(out, "ARCH.FACADE_RUN", "facade")
    assert run["measured_net"] == pytest.approx(T.FAC_RUN, abs=A) and run["unit"] == "lm"
    fac = R.the(out, "ARCH.FACADE", "facade")
    assert fac["measured_net"] == pytest.approx(T.FAC_NET, abs=A) and fac["unit"] == "m2"
    assert fac["calculation"]["inputs"]["gross_m2"] == pytest.approx(T.FAC_GROSS, abs=A)
    ded = {d["opening_id"]: d for d in fac["calculation"]["inputs"]["openings"]}
    assert sorted(d["deducted_m2"] for d in ded.values()) == pytest.approx(sorted([T.FAC_DOOR, T.FAC_WIN]), abs=A)


def test_exterior_finish_is_held_without_a_specification(ex):
    out = ex()
    fin = R.the(out, "FIN.EXT.FINISH", "facade")
    assert fin["measured_net"] is None and "EXTERIOR_FINISH_NOT_SPECIFIED" in fin["rfi"]["question"]
    assert fin["calculation"]["inputs"]["facade_net_m2"] == pytest.approx(T.FAC_NET, abs=A)   # exposure, not summed


def test_exterior_finish_takes_the_facade_when_specified(ex):
    out = ex(facts=FINISH)
    fin = R.the(out, "FIN.EXT.FINISH", "facade")
    assert fin["measured_net"] == pytest.approx(T.FAC_NET, abs=A)
    assert fin["material_state"] == "PROJECT_OWNER_FACT"


@pytest.mark.parametrize("section", ["TOS", None])
def test_facade_area_held_without_floor_to_floor(ex, section):
    out = ex(section=section)
    assert R.net(out, "ARCH.FACADE_RUN", "facade") == pytest.approx(T.FAC_RUN, abs=A)
    fac = R.the(out, "ARCH.FACADE", "facade")
    assert fac["measured_net"] is None and "FACADE_HEIGHT_NOT_IN_THE_DRAWING" in fac["rfi"]["question"]
    assert _fac(out)["height"]["state"] == "NOT_ESTABLISHED"


def test_stated_facade_height_is_used_and_labelled(ex):
    facts = {"facade": {"*": {"height_m": {"value_m": 3.50, "authority": "OWNER_PROJECT_FACT: synthetic"}}}}
    out = ex(section=None, facts=facts)
    assert R.net(out, "ARCH.FACADE", "facade") == pytest.approx(T.FAC_NET, abs=A)
    assert _fac(out)["height"]["kind"] == "PROJECT_RULE"


def test_masonry_is_unchanged_by_the_facade_levels(ex):
    no_beams = {"masonry": {"*": {"beams_over_walls": {"state": "NONE", "authority": "OWNER_PROJECT_FACT: synthetic"}}}}
    out = ex(facts=no_beams)
    assert R.the(out, "ARCH.WALL_PANEL", "walls t=0.20")["measured_net"] == pytest.approx(T.MAS_AREA, abs=A)


def test_free_standing_column_is_an_island_not_a_facade(ex):
    out = ex(column=True, roles=F.ROLES)                     # a lone square is not a column layer by itself
    rec = _fac(out)
    assert rec["state"] == "ONE_OUTLINE" and rec["islands"] == 1
    assert R.net(out, "ARCH.FACADE_RUN", "facade") == pytest.approx(T.FAC_RUN, abs=A)


def test_second_outline_is_reported_never_added(ex):
    out = ex(annex=True)
    rec = _fac(out)
    assert rec["state"] == "SEVERAL_OUTLINES"
    assert sorted(round(o["perimeter_m"], 6) for o in rec["outlines"]) == [T.FAC_ANNEX_RUN, round(T.FAC_RUN, 6)]
    run = R.the(out, "ARCH.FACADE_RUN", "facade")
    assert run["measured_net"] == pytest.approx(T.FAC_RUN, abs=A)                   # the largest outline only
    other = R.the(out, "ARCH.FACADE_RUN", "facade outline 2")
    assert other["measured_net"] is None and "ANOTHER_EXTERIOR_OUTLINE" in other["rfi"]["question"]
    assert other["calculation"]["inputs"]["perimeter_m"] == pytest.approx(T.FAC_ANNEX_RUN, abs=A)


def test_outline_around_the_building_holds_the_facade(ex):
    out = ex(enclosure=True)
    rec = _fac(out)
    assert rec["state"] == "ENCLOSED_BUILDING"
    run = R.the(out, "ARCH.FACADE_RUN", "facade")
    assert run["measured_net"] is None and "ENCLOSED_BUILDING" in run["rfi"]["question"]
    assert R.the(out, "ARCH.FACADE", "facade")["measured_net"] is None


def test_curved_facade_runs_on_the_outer_arc(tmp_path):
    dxf = F.curved_room(tmp_path / "c.dxf", opening="WINDOW")
    out = R.run(dxf, tmp_path / "o", roles=F.ROLES)
    o = _fac(out)["outlines"][0]
    assert o["perimeter_m"] == pytest.approx(T.CUR_FAC_RUN, abs=A)
    assert sorted(round(x["width_m"], 6) for x in o["openings"]) == [round(x, 6) for x in T.CUR_FAC_OPENINGS]


def test_lower_methods_have_no_facade(ex):
    out = ex(method=R.V28)
    assert not R.all_of(out, "ARCH.FACADE_RUN") and not (Path(out) / "FACADE.json").exists()


def test_facade_run_is_independently_verified(tmp_path):
    dxf = F.masonry_room(tmp_path / "m.dxf", section="FACADE")
    before, after = R.run(dxf, tmp_path / "v28", method=R.V28), R.run(dxf, tmp_path / "v29")
    rep = V.Verifier(before, after, dxf, {}, dict(x.split("=", 1) for x in F.ROLES)).report()
    assert rep["summary"]["UNEXPLAINED"] == 0 and rep["summary"]["CONTRADICTED"] == 0
    row = next(r for r in rep["differences"] if r["item_code"] == "ARCH.FACADE_RUN")
    assert row["status"] == "VERIFIED" and row["verification"]["method"] == "INDEPENDENT_OUTLINE"
    assert row["verification"]["independent"] == pytest.approx(T.FAC_RUN, abs=1e-4)
    json.dumps(rep)
