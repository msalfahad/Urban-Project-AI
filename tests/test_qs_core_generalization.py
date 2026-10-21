"""The same code, on a drawing it has never seen.

If the engine needed anything specific to the first plan, the second one would expose it: different shapes,
different thicknesses, an L-shaped room, a partition at 100 mm instead of 150 or 200.
"""

from __future__ import annotations

import pytest

from engine.qs_core import identity, invariants, pipeline, synthetic as syn
from engine.qs_core.entities import HOST_ASSIGNED


@pytest.mark.parametrize("plan_builder", [syn.small_plan, syn.second_plan])
def test_every_invariant_holds_on_both_plans(plan_builder):
    r = syn.run(plan_builder(), wall_height=3.0)
    assert r["INVARIANTS"]["ALL_PASS"], [c for c in r["INVARIANTS"]["CHECKS"] if not c["PASS"]]
    assert r["INVARIANTS"]["OF"] >= 11


def test_the_second_plan_assembles_its_own_rooms_and_hosts_its_own_door():
    r = syn.run(syn.second_plan(), wall_height=2.8)
    labels = sorted(s["LABEL"] for s in r["SPACES"])
    assert labels == ["OFFICE", "WORKSHOP"]
    door = r["OPENING_REGISTER"]["REGISTER"][0]
    assert door["HOST_ASSIGNMENT_STATUS"] == HOST_ASSIGNED
    assert door["HOST_THICKNESS_M"] == 0.10
    assert r["OPENING_REGISTER"]["DEDUCTION_BY_THICKNESS_M2"] == {"0.1": pytest.approx(0.9 * 2.10)}


def test_an_l_shaped_room_is_one_space_with_its_own_area():
    r = syn.run(syn.second_plan(), wall_height=2.8)
    workshop = next(s for s in r["SPACES"] if s["LABEL"] == "WORKSHOP")
    assert workshop["AREA_M2"] == pytest.approx(5.0 * 2.0 + 2.0 * 3.0 + 0.1 * 0.9)
    assert workshop["COMPONENT_REFS"] == ["X-1"]


def test_the_two_plans_share_no_identity_and_do_not_interfere():
    a = syn.run(syn.small_plan("R1"), wall_height=3.0)
    b = syn.run(syn.second_plan("S1"), wall_height=2.8)
    ids_a = {c["UID"] for c in a["MEASUREMENT_OBJECTS"] if c.get("UID")}
    ids_b = {c["UID"] for c in b["MEASUREMENT_OBJECTS"] if c.get("UID")}
    assert not (ids_a & ids_b)
    assert a["INVARIANTS"]["ALL_PASS"] and b["INVARIANTS"]["ALL_PASS"]


def test_unresolved_cases_surface_the_same_way_on_an_unfamiliar_plan():
    plan = syn.second_plan()
    # the partition drawn twice, once at 100 mm and once at 120 mm: the door is in one of them and the drawing
    # does not say which
    plan["COMPONENTS"].append(syn.wall_band("X-W-DUPLICATE", (2.0, 2.0, 2.12, 5.0), 0.12, syn.geom.AXIS_Y,
                                            revision="S1"))
    r = syn.run(plan, wall_height=2.8)
    hosts = r["HOST_REGISTER"]
    assert hosts["PHYSICAL_OPENINGS"] >= 1, "the door exists whatever the geometry says about its host"
    q = [x for x in r["QUESTIONS"]["ROOT_QUESTIONS"] if x["KIND"] == "HOST_WALL_UNRESOLVED"]
    if q:
        impacts = [i for i in r["QUESTIONS"]["DEPENDENCY_IMPACTS"]
                   if i["ROOT_QUESTION_ID"] == q[0]["ROOT_QUESTION_ID"]]
        assert impacts, "an open host question has to name the quantities it holds up"
        assert q[0]["DETAIL"]["THE_OPENING_EXISTS"] is True
    assert r["INVARIANTS"]["ALL_PASS"], r["INVARIANTS"]["CHECKS"]
    assert any(row["NET_AREA_M2"] is not None for row in r["WALL_ROWS"]), \
        "one open question does not hold up the walls it cannot affect"


def test_running_the_same_plan_twice_gives_byte_identical_registers():
    import json
    a = syn.run(syn.second_plan(), wall_height=2.8)
    b = syn.run(syn.second_plan(), wall_height=2.8)
    strip = lambda r: json.dumps({k: r[k] for k in ("OPENING_REGISTER", "MEMBERSHIP_REGISTER", "SPACES",
                                                    "WALL_ROWS", "MEASUREMENT_OBJECTS")},
                                 sort_keys=True, default=str)
    assert strip(a) == strip(b)
