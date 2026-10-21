"""STAIR_FLIGHT_ONCE_V1 on hand-calculated synthetic fixtures (not Alsenan): a dog-leg stair over two storeys drawn on
both plans, a three-storey stair core, mismatched repeats, exposure copies; each in metres and in mm, mirrored and
rotated 90 deg, with the two plans placed apart on the sheet (the alignment offset carries the upper plan onto the lower).

Hand calculations (m, m2): one flight = 11 treads x going 0.28 x width 1.10:
    tread marble 11 x 0.28 x 1.10 = 3.388 m2; steps 11 x 1.10 = 12.10 lm; riser lines 12
DOG-LEG GF (+0.00) -> 1F (+3.60): west lane x 0 .. 1.10 rising north y 0 .. 3.08, well 0.20, east lane x 1.30 .. 2.40
falling back south y 3.08 .. 0 (the half landing north of y 3.08). GF plan: both flights (own). 1F plan: the same two
flights drawn again for orientation (no stair rises from 1F).
    released reading (STACKED): 4 flights counted = 13.552 m2 / 48.40 lm (twice the stair)
    once: GF 6.776 m2 / 24.20 lm counted; 1F 2 x SEEN_ABOVE (0, measured on GF); conservation 0
1F without level marks and without slab-above evidence: both 1F copies HELD 0 .. 6.776 / 0 .. 24.20 (never counted,
never dropped); a printed half-landing level +1.80 on the 1F plan sets the storey by itself.
CORE GF -> 1F -> 2F (+7.20), identical flights on every plan, 2F plan repeats the 1F flights: the 1F roof slab draws the
stair panel over the flights (DRAWN_AT) -> 1F flights are 1F's own (counted); the 2F roof slab draws none -> 2F copies
SEEN_ABOVE; counted 4 flights = 13.552 m2 / 48.40 lm, removed 6.776 / 24.20.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import stair_flight_once_v1 as SO  # noqa: E402

N, G, W, GAP = 11, 0.28, 1.10, 0.20
ONE_T, ONE_S = round(N * G * W, 6), round(N * W, 6)          # 3.388 m2, 12.10 lm


def make_T(scale=1.0, rot=0, mirror=False):
    """a drawing transform: metres -> drawing units (scale), then mirror x, then rotate by rot degrees."""
    a = math.radians(rot)

    def T(p):
        x, y = p
        if mirror:
            x = -x
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return (x * scale, y * scale)
    return T


def flight(fid, origin, up, n=N, going=G, width=W, T=None):
    """a straight flight, footprint [(u0,n0),(u1,n0),(u1,n1),(u0,n1)] as arch_rooms writes it. origin: the corner of
    its first tread line (metres); up = +1 runs +y, -1 runs -y; across always +x."""
    ox, oy = origin

    def P(u, v):
        return T((ox + u, oy + up * v))
    L = n * going
    quads = [[P(0, k * going), P(width, k * going), P(width, (k + 1) * going), P(0, (k + 1) * going)] for k in range(n)]
    return {"flight_id": fid, "kind": "STRAIGHT", "tread_lines": n + 1,
            "footprint": [P(0, 0), P(width, 0), P(width, L), P(0, L)], "tread_quads": quads,
            "tread_areas_m2": [round(going * width, 6)] * n, "step_widths_m": [width] * n}


def dogleg(prefix, T, shift=(0.0, 0.0), n_east=N, east_dy=0.0):
    sx, sy = shift
    return [flight(prefix + "W", (sx + 0.0, sy + 0.0), +1, T=T),
            flight(prefix + "E", (sx + W + GAP, sy + N * G + east_dy), -1, n=n_east, T=T)]


def mark(T, x, y, v):
    q = T((x, y))
    return {"x": q[0], "y": q[1], "value_m": v}


def two_storeys(T, unit_m, *, marks_1f=True, slab_1f=None, half_mark=False, n_east=N, east_dy=0.0, dx=40.0):
    """GF at origin, 1F plan placed dx metres east on the sheet; offset_to_below = T((dx, 0)) - T((0, 0))."""
    o = [a - b for a, b in zip(T((dx, 0.0)), T((0.0, 0.0)))]
    m1 = [mark(T, dx + 1.20, -1.00, 3.60)] if marks_1f else []
    if half_mark:
        m1.append(mark(T, dx + 1.20, N * G + 0.60, 1.80))
    return [{"floor": "GF", "level_m": 0.0, "flights": dogleg("GF:", T), "level_marks": [mark(T, 1.20, -1.00, 0.0)],
             "slab_above": {"state": "DRAWN", "source": "GF roof slab draws the stair"}, "offset_to_below": None},
            {"floor": "1F", "level_m": 3.60, "flights": dogleg("1F:", T, shift=(dx, 0.0), n_east=n_east,
                                                                 east_dy=east_dy),
             "level_marks": m1, "slab_above": slab_1f, "offset_to_below": tuple(o)}]


VARIANTS = [("m", 1.0, 0, False), ("mm", 1000.0, 0, False), ("mm mirrored", 1000.0, 0, True),
            ("m rotated 90", 1.0, 90, False), ("mm mirrored rotated 90", 1000.0, 90, True)]


@pytest.fixture(params=VARIANTS, ids=[v[0] for v in VARIANTS])
def drawing(request):
    _, scale, rot, mir = request.param
    return make_T(scale, rot, mir), 1.0 / scale


def by_id(rec):
    return {r["flight_id"]: r for r in rec["flights"]}


def test_hand_values_of_one_flight():
    assert ONE_T == pytest.approx(3.388) and ONE_S == pytest.approx(12.10)


def test_dogleg_top_storey_copies_are_seen_above_once(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, slab_1f={"state": "NONE_DRAWN", "source": "1F roof slab: no stair"}),
                          unit_m=u)
    R = by_id(rec)
    assert R["GF:W"]["state"] == R["GF:E"]["state"] == SO.COUNTED
    for k, low in (("1F:W", "GF:W"), ("1F:E", "GF:E")):
        assert R[k]["state"] == SO.SEEN_ABOVE and R[k]["storey"] == "GF" and R[k]["measured_on"] == f"GF {low}"
        assert R[k]["counted_tread_m2"] == 0.0 and R[k]["outline_shift_m"] <= 1e-6
    t = rec["totals"]
    assert t["before"]["tread_m2"] == pytest.approx(4 * ONE_T) and t["before"]["step_lm"] == pytest.approx(4 * ONE_S)
    assert t["after_counted"]["tread_m2"] == pytest.approx(2 * ONE_T)
    assert t["after_counted"]["step_lm"] == pytest.approx(2 * ONE_S)
    assert t["seen_above_removed"]["tread_m2"] == pytest.approx(2 * ONE_T)
    assert t["held_high"]["tread_m2"] == 0.0
    assert t["conservation_tread_m2"] == pytest.approx(0.0) and t["conservation_step_lm"] == pytest.approx(0.0)


def test_no_level_marks_and_no_slab_evidence_holds_never_counts_twice(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, marks_1f=False, slab_1f=None), unit_m=u)
    R = by_id(rec)
    for k in ("1F:W", "1F:E"):
        assert R[k]["state"] == SO.HELD and R[k]["counted_tread_m2"] is None
        assert R[k]["held"]["tread_m2"] == {"low": 0.0, "high": ONE_T}
        assert R[k]["reasons"][0].startswith("STOREY_NOT_SET")
    t = rec["totals"]
    assert t["after_range_tread_m2"] == pytest.approx([2 * ONE_T, 4 * ONE_T])
    assert t["after_range_step_lm"] == pytest.approx([2 * ONE_S, 4 * ONE_S])
    assert t["conservation_tread_m2"] == pytest.approx(0.0)


def test_floor_level_mark_alone_sets_nothing(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, marks_1f=True, slab_1f={"state": "NOT_READ"}), unit_m=u)
    assert {r["state"] for r in rec["flights"] if r["floor"] == "1F"} == {SO.HELD}


def test_printed_half_landing_level_sets_the_storey(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, half_mark=True, slab_1f=None), unit_m=u)
    R = by_id(rec)
    assert R["1F:W"]["state"] == R["1F:E"]["state"] == SO.SEEN_ABOVE
    assert "PRINTED_END_LEVEL +1.80 below this floor +3.60" in R["1F:W"]["evidence"][0]
    assert R["1F:W"]["end_levels_m"][1] == [1.8]          # the north end (end B of the west lane)


def test_step_count_differs_is_held_with_reason(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, n_east=N - 1, east_dy=-G,
                                      slab_1f={"state": "NONE_DRAWN"}), unit_m=u)
    R = by_id(rec)
    assert R["1F:W"]["state"] == SO.SEEN_ABOVE
    e = R["1F:E"]
    assert e["state"] == SO.HELD and e["storey"] == "GF"
    assert any(r.startswith("STEP_COUNT_DIFFERS: 10 treads here, 11 on GF") for r in e["reasons"])
    assert e["held"]["tread_m2"]["high"] == pytest.approx(10 * G * W)
    assert rec["totals"]["conservation_tread_m2"] == pytest.approx(0.0)


def test_outline_shift_beyond_one_centimetre_is_held(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, east_dy=0.02, slab_1f={"state": "NONE_DRAWN"}), unit_m=u)
    e = by_id(rec)["1F:E"]
    assert e["state"] == SO.HELD and any(r.startswith("OUTLINE_SHIFT 0.020 m") for r in e["reasons"])
    ok = SO.flights_once(two_storeys(T, u, east_dy=0.005, slab_1f={"state": "NONE_DRAWN"}), unit_m=u)
    assert by_id(ok)["1F:E"]["state"] == SO.SEEN_ABOVE


def test_three_storey_core_counts_each_storey_once(drawing):
    T, u = drawing
    dx = 40.0
    o = tuple(a - b for a, b in zip(T((dx, 0.0)), T((0.0, 0.0))))
    panel = [T(p) for p in ((dx - 0.1, -0.1), (dx + 2.5, -0.1), (dx + 2.5, N * G + 1.4), (dx - 0.1, N * G + 1.4))]
    plans = [{"floor": "GF", "level_m": 0.0, "flights": dogleg("GF:", T), "level_marks": [], "offset_to_below": None},
             {"floor": "1F", "level_m": 3.60, "flights": dogleg("1F:", T, shift=(dx, 0.0)), "level_marks": [],
              "slab_above": {"state": "DRAWN_AT", "polygons": [panel], "source": "1F roof slab stair panel"},
              "offset_to_below": o},
             {"floor": "2F", "level_m": 7.20, "flights": dogleg("2F:", T, shift=(2 * dx, 0.0)), "level_marks": [],
              "slab_above": {"state": "NONE_DRAWN", "source": "2F roof slab"}, "offset_to_below": o}]
    rec = SO.flights_once(plans, unit_m=u, section_risers={"GF": 24, "1F": 25})
    R = by_id(rec)
    assert R["1F:W"]["state"] == R["1F:E"]["state"] == SO.COUNTED and R["1F:W"]["storey"] == "1F"
    assert "STAIR_DRAWN_IN_SLAB_ABOVE_AT_THE_FLIGHT" in R["1F:W"]["evidence"][0]
    assert R["2F:W"]["measured_on"] == "1F 1F:W" and R["2F:E"]["measured_on"] == "1F 1F:E"
    t = rec["totals"]
    assert t["after_counted"]["tread_m2"] == pytest.approx(4 * ONE_T)
    assert t["seen_above_removed"]["step_lm"] == pytest.approx(2 * ONE_S)
    sc = {s["storey"]: s for s in rec["section_check"]}
    assert sc["GF"]["plan_riser_lines_of_own_flights"] == 24 and sc["GF"]["difference"] == 0
    assert sc["1F"]["difference"] == 1                       # listed only, nothing changed by it


def test_stair_panel_elsewhere_means_the_flight_is_below(drawing):
    T, u = drawing
    far = [T(p) for p in ((60, 60), (63, 60), (63, 66), (60, 66))]
    rec = SO.flights_once(two_storeys(T, u, slab_1f={"state": "DRAWN_AT", "polygons": [far]}), unit_m=u)
    assert {r["state"] for r in rec["flights"] if r["floor"] == "1F"} == {SO.SEEN_ABOVE}


def test_unlocated_stair_above_holds_an_exact_repeat_and_counts_a_different_flight(drawing):
    T, u = drawing
    rec = SO.flights_once(two_storeys(T, u, n_east=N - 1, east_dy=-G, slab_1f={"state": "DRAWN"}), unit_m=u)
    R = by_id(rec)
    assert R["1F:W"]["state"] == SO.HELD
    assert R["1F:W"]["reasons"][0].startswith("STAIR_DRAWN_IN_SLAB_ABOVE_NOT_LOCATED")
    assert R["1F:E"]["state"] == SO.COUNTED                  # 10 treads over 11: another flight, a stair rises


def test_lower_copy_not_counted_is_held(drawing):
    T, u = drawing
    plans = two_storeys(T, u, slab_1f={"state": "NONE_DRAWN"})
    plans[0]["flights"][1]["drawn_on_plan_below"] = {"floor": "B1", "flight_id": "x"}   # exposure on GF itself
    R = by_id(SO.flights_once(plans, unit_m=u))
    assert R["GF:E"]["state"] == SO.EXPOSURE
    assert R["1F:E"]["state"] == SO.HELD and any(r.startswith("LOWER_COPY_NOT_COUNTED") for r in R["1F:E"]["reasons"])
    assert R["1F:W"]["state"] == SO.SEEN_ABOVE


def test_two_copies_of_one_lower_flight_second_is_held(drawing):
    T, u = drawing
    plans = two_storeys(T, u, slab_1f={"state": "NONE_DRAWN"})
    plans[1]["flights"].append(dict(plans[1]["flights"][0], flight_id="1F:W2"))
    R = by_id(SO.flights_once(plans, unit_m=u))
    assert R["1F:W"]["state"] == SO.SEEN_ABOVE
    assert R["1F:W2"]["state"] == SO.HELD
    assert any(r.startswith("LOWER_FLIGHT_ALREADY_MATCHED") for r in R["1F:W2"]["reasons"])


def test_level_below_with_nothing_under_it_is_held(drawing):
    T, u = drawing
    plans = two_storeys(T, u, half_mark=True)
    plans[0]["flights"] = []                                  # the lower plan does not draw its own stair
    R = by_id(SO.flights_once(plans, unit_m=u))
    for k in ("1F:W", "1F:E"):                               # both lanes end on the +1.80 half landing
        assert R[k]["state"] == SO.HELD and R[k]["reasons"][0].startswith("NO_MATCH_BELOW")
    plans[1]["level_marks"] = plans[1]["level_marks"][:1]     # only the floor level: nothing under it, nothing set
    R = by_id(SO.flights_once(plans, unit_m=u))
    assert R["1F:W"]["state"] == R["1F:E"]["state"] == SO.COUNTED     # released reading kept


def test_level_above_counts_the_flight_as_own(drawing):
    T, u = drawing
    plans = two_storeys(T, u, slab_1f={"state": "NONE_DRAWN"})
    plans[1]["level_marks"].append(mark(T, 40.0 + 0.55, N * G + 0.60, 5.40))
    R = by_id(SO.flights_once(plans, unit_m=u))
    assert R["1F:W"]["state"] == SO.COUNTED and "above this floor" in R["1F:W"]["evidence"][0]


def test_unaligned_plans_keep_the_released_reading(drawing):
    T, u = drawing
    plans = two_storeys(T, u, slab_1f={"state": "NONE_DRAWN"})
    plans[1]["offset_to_below"] = None
    rec = SO.flights_once(plans, unit_m=u)
    assert {r["state"] for r in rec["flights"]} == {SO.COUNTED}
    assert rec["warnings"] and rec["warnings"][0].startswith("NOT_ALIGNED")


def test_module_names_no_project():
    src = (ROOT / "engine" / "source" / "stair_flight_once_v1.py").read_text(encoding="utf-8").lower()
    for w in ("alsenan", "7757", "rebar", "reinforc"):
        assert w not in src
