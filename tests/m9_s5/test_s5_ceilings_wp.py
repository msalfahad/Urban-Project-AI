"""M9 S5 - ceilings under a void (double height, across two plans) and the waterproofing doorway piece of a door
between two wet rooms (counted once), on hand-built plans (tools/arch_synth.s5_double_height / s5_wet_pair; every
expected value derived by hand from the rectangles)."""

from __future__ import annotations

import pytest

from engine.source import arch_measure as AM
from engine.source import arch_rooms as AR
from tools import arch_synth as AS

U = 0.001
TOL = 1e-6


def _ceil(M):
    out = {}
    for ln in M["lines"]:
        if ln["item_code"] == "FIN.CEILING":
            t = ln["calculation"]["inputs"].get("ceiling_type")
            out[t] = out.get(t, 0.0) + (ln["measured_net"] or 0.0)
    return out


@pytest.fixture(scope="module")
def two_plans():
    (lo, up), roles, T = AS.s5_double_height()
    S_lo = AR.spaces(lo, roles, U, region_id="GF")
    S_up = AR.spaces(up, roles, U, region_id="1F")
    dh = AR.voids_above([("GF", S_lo["column_boxes"], S_lo["faces"], S_lo["voids"], lo["segments"]),
                         ("1F", S_up["column_boxes"], S_up["faces"], S_up["voids"], up["segments"])], U)
    M_lo = AM.measure(S_lo, floor="GF", project_id="P", revision_set_sha256="0" * 64)
    M_up = AM.measure(S_up, floor="1F", project_id="P", revision_set_sha256="0" * 64)
    return dh, M_lo, M_up, T


def test_the_void_is_carried_onto_the_plan_below(two_plans):
    dh, _, _, T = two_plans
    assert len(dh) == 1 and dh[0]["state"] == "APPLIED" and dh[0]["onto"] == "GF"
    assert sum(x["m2"] for x in dh[0]["in_spaces"]) == pytest.approx(T["void_m2"], abs=TOL)
    assert any(c.startswith("X_RECT_ON_GF") for c in dh[0]["corroborated_by"])   # the lower plan draws the opening


def test_double_height_ceiling_counted_once(two_plans):
    _, M_lo, M_up, T = two_plans
    lo, up = _ceil(M_lo), _ceil(M_up)
    assert lo == {"NORMAL_LEVEL": pytest.approx(T["room_m2"] - T["void_m2"], abs=TOL)}    # none under the void
    assert up["NORMAL_LEVEL"] == pytest.approx(T["room_m2"] - T["void_m2"], abs=TOL)
    assert up["DOUBLE_HEIGHT"] == pytest.approx(T["void_m2"], abs=TOL)                  # over the void, on 1F
    # one ceiling per m2 of plan, once: the two plans less the lower part open to the void above
    assert sum(lo.values()) + sum(up.values()) == pytest.approx(2 * T["room_m2"] - T["void_m2"], abs=TOL)


def test_floors_are_unchanged_by_the_ceiling_rule(two_plans):
    _, M_lo, M_up, T = two_plans
    f_lo = [x["measured_net"] for x in M_lo["lines"] if x["item_code"] == "FIN.FLOOR.PORCELAIN"]
    f_up = [x["measured_net"] for x in M_up["lines"] if x["item_code"] == "FIN.FLOOR.PORCELAIN"]
    assert f_lo == [pytest.approx(T["room_m2"], abs=TOL)]                   # the lower floor exists under the void
    assert f_up == [pytest.approx(T["room_m2"] - T["void_m2"], abs=TOL)]    # the void is never floor


def test_plans_without_a_common_grid_are_not_aligned():
    (lo, up), roles, _ = AS.s5_double_height()
    S_lo = AR.spaces(lo, roles, U, region_id="GF")
    S_up = AR.spaces(up, roles, U, region_id="1F")
    dh = AR.voids_above([("GF", [], S_lo["faces"], S_lo["voids"]), ("1F", S_up["column_boxes"], S_up["faces"],
                                                                      S_up["voids"])], U)
    assert [d["state"] for d in dh] == ["PLANS_NOT_ALIGNED"]
    assert not any(f.get("double_height_m2") for f in S_lo["faces"])        # never applied by guess


def test_a_door_between_two_wet_rooms_has_one_doorway_piece():
    ents, roles, T = AS.s5_wet_pair()
    S = AR.spaces(ents, roles, U, region_id="T")
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64)
    dw = [x for x in M["lines"] if x["item_code"] == "FIN.WP.DOORWAY"]
    assert len(dw) == 1 and dw[0]["measured_net"] == pytest.approx(T["doorway_m2"], abs=TOL)
    ups = [x for x in M["lines"] if x["item_code"] == "FIN.WP.UPTURN"]
    assert len(ups) == 2 and sum("SHARED_WET_DOORWAY" in (x.get("notes") or "") for x in ups) == 1
    floors = [x["measured_net"] for x in M["lines"] if x["item_code"] == "FIN.WP.FLOOR"]
    assert floors == [pytest.approx(T["room_m2"], abs=TOL)] * 2


def test_stair_room_has_a_blocked_stairwell_ceiling():
    ents = AS._s4_ents({"ST": [(200, 200), (3200, 200), (3200, 5200), (200, 5200)]},
                       [(0, 0), (3400, 0), (3400, 5400), (0, 5400)], [], texts=(("STAIR", (1700, 2700)),))
    S = AR.spaces(ents, dict(AS.S4_ROLES), U, region_id="T")
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64)
    c = [x for x in M["lines"] if x["item_code"] == "FIN.CEILING"]
    assert len(c) == 1 and c[0]["evidence_state"] == "BLOCKED_RFI" and c[0]["measured_net"] is None
    r = next(u["reason"] for u in M["unresolved"] if u["item"] == "FIN.CEILING")
    assert AM.flag({"reason": r}, drawing="d")["cause"] == "SOURCE"


def test_flight_sides_wall_or_open():
    # a straight flight 1.0 m wide (tread lines along x) beside a 0.2 m wall whose face is 0.05 m off its left side
    fl = {"kind": "STRAIGHT", "footprint": [(1000.0, 0.0), (2000.0, 0.0), (2000.0, 3000.0), (1000.0, 3000.0)]}
    walls = [{"centreline": [(850.0, -500.0), (850.0, 3500.0)], "t_m": 0.2}]
    sides = AM.flight_sides(fl, walls, U)
    assert [(x["side"], x["kind"]) for x in sides] == [("side_a", "WALL"), ("side_b", "OPEN")]
    assert [x["plan_lm"] for x in sides] == [pytest.approx(3.0), pytest.approx(3.0)]


def test_repairs_are_logged_never_moved():
    ents, roles, _ = AS.s5_wet_pair()
    drawn = {s["id"]: (s["a"], s["b"]) for s in ents["segments"]}
    S = AR.spaces(ents, roles, U, region_id="T")
    assert {s["id"]: (s["a"], s["b"]) for s in ents["segments"]} == drawn          # no drawn entity is changed
    for r in S["repairs"]:
        assert r["kind"] in ("WALL_CAP", "DOOR_CLOSURE") and r["rule"] and r["reason"] and r["a"] and r["b"]
