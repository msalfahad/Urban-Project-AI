"""T-258 STAIR_DOME_LINE_V1 on synthetic Villa D (not the development villa; hand values below).

Villa D: storey +0.00 -> +3.00, 20 risers r 0.15, going g 0.28, flight width 1.00, waist T 0.15 (printed).
  d = t / cos = 0.15 x hypot(0.28, 0.15) / 0.28 = 0.170168; k = r / g = 0.535714
  L1 lower flight, 10 riser lines (9 goings), 10 step triangles: steps 10 x 1/2 x 0.15 x 0.28 x 1.0 = 0.210000;
     waist 0.15 x hypot(2.52, 1.35) = 0.15 x 2.858828 = 0.428824; arrival wedge into the half landing (T 0.15 >= r,
     whole triangle) 0.021000; foot: first riser line 0.10 inside a ground beam billed full depth:
     (d a - k a^2 / 2) w = 0.0170168 - 0.0026786 = 0.0143383 (ground beam's) -> L1 net 0.6034859
  LD half landing +1.50: 2.10 x 1.00 x 0.15 = 0.315; its back 0.20 strip is a beam band billed full depth:
     stair 2.10 x 0.80 x 0.15 = 0.252, beam 0.063
  U1 upper flight, head 0.10 inside the floor beam: (a/g)^2 x 0.021 + a d w = 0.0026786 + 0.0170168 = 0.0196954, the
     arrival wedge (into the beam) 0.021 -> U1 net 0.21 + 0.428824 - 0.021 - 0.0196954 = 0.5981289
  floor arrival landing at +3.00 inside the floor-slab panel: slab (R-STAIR-LAND-1), never stair
  winder turn W (3 winders, no soffit drawn): HELD 0.05 .. 0.06; curved flight C (helicoid soffit not drawn): HELD
  dome shell, chord 4.00, rise 1.00, T 0.08: R_o = (2^2 + 1) / 2 = 2.5, R_i 2.42, h_i 0.92,
     V = pi/3 [1 x (7.5 - 1) - 0.8464 x (7.26 - 0.92)] = pi/3 x 1.133824 = 1.187338
  closable total 0.6034859 + 0.252 + 0.5981289 + 1.187338 = 2.6409528
  plate thinner than the riser: wedge into a 0.12 plate = 0.021 x (1 - (0.03 / 0.15)^2) = 0.02016
"""

import importlib.util
import itertools
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_p = ROOT / "research" / "agents_t258" / "t258_stair_dome_line.py"
_s = importlib.util.spec_from_file_location("t258_stair_dome_line", _p)
SD = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t258_stair_dome_line", SD)
_s.loader.exec_module(SD)

R, G, W, T = 0.15, 0.28, 1.00, 0.15
SLAB = ("SLAB:D-ARR",)


def villa_d():
    C = SD.component
    l1 = SD.flight_m3(10, R, G, 9, W, T, wedges=[0.15], foot_a=0.10)
    u1 = SD.flight_m3(10, R, G, 9, W, T, wedges=[None], head_a=0.10)
    return [
        C("L1", "ST-D", "lower flight", "CLOSABLE", "DRAWING-CONFIRMED", "STAIR", value=l1["net"], source="plan + section"),
        C("L1-FOOT", "ST-D", "foot in ground beam", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "GROUND_BEAM",
          value=l1["foot_owned_elsewhere"]),
        C("LD", "ST-D", "half landing net of the beam band", "CLOSABLE", "DRAWING-CONFIRMED", "STAIR",
          value=SD.landing_m3(2.10, 0.80, T), source="plan"),
        C("LD-BEAM", "ST-D", "landing strip inside the beam band", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "BEAM",
          value=SD.landing_m3(2.10, 0.20, T)),
        C("U1", "ST-D", "upper flight", "CLOSABLE", "VERIFIED", "STAIR", value=u1["net"], source="plan + section"),
        C("U1-HEAD", "ST-D", "head in floor beam", "OWNED_ELSEWHERE", "VERIFIED", "BEAM",
          value=u1["head_owned_elsewhere"]),
        C("ARR", "ST-D", "floor arrival landing", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "SLAB", region="SLAB:D-ARR",
          floor_level_landing=True),
        C("W", "ST-W", "winder turn", "HELD", "HELD", "STAIR", bound=[0.05, 0.06], geometry_drawn=False,
          blocker="no winder soffit drawn"),
        C("C", "ST-C", "curved flight", "HELD", "HELD", "STAIR", bound=None, geometry_drawn=False,
          blocker="helicoid soffit not drawn"),
        C("DOME", "DOME-D", "shell", "CLOSABLE", "DRAWING-CONFIRMED", "DOME", value=SD.shell_m3(4.0, 1.0, 0.08),
          source="dome detail"),
    ]


def test_hand_values():
    l1 = SD.flight_m3(10, R, G, 9, W, T, wedges=[0.15], foot_a=0.10)
    assert l1["steps"] == pytest.approx(0.21, abs=1e-9)
    assert l1["waist"] == pytest.approx(0.428824, abs=1e-6)
    assert l1["wedges"] == pytest.approx(0.021, abs=1e-9)
    assert l1["foot_owned_elsewhere"] == pytest.approx(0.0143383, abs=1e-6)
    assert l1["net"] == pytest.approx(0.6034859, abs=1e-6)
    u1 = SD.flight_m3(10, R, G, 9, W, T, wedges=[None], head_a=0.10)
    assert u1["head_owned_elsewhere"] == pytest.approx(0.0196954, abs=1e-6)
    assert u1["net"] == pytest.approx(0.5981289, abs=1e-6)
    assert SD.shell_m3(4.0, 1.0, 0.08) == pytest.approx(1.187338, abs=1e-6)
    assert SD.wedge_in_plate_m3(R, G, W, 0.12) == pytest.approx(0.02016, abs=1e-9)


def test_line_totals_and_once():
    comps = villa_d()
    assert SD.check_line(comps, SLAB)
    t = SD.totals(comps)
    assert t["closable_total"] == pytest.approx(2.6409528, abs=1e-6)
    assert t["closable"]["VERIFIED"] == pytest.approx(0.5981289, abs=1e-6)
    assert t["owned_elsewhere"]["BEAM"] == pytest.approx(0.063 + 0.0196954, abs=1e-6)
    assert t["owned_elsewhere"]["GROUND_BEAM"] == pytest.approx(0.0143383, abs=1e-6)
    assert t["held_low"] == pytest.approx(0.05) and t["held_high"] == pytest.approx(0.06)
    assert t["held_open"] == ["C"]
    assert t["line_closable"] is False
    # landing + beam strip re-add to the drawn landing; flight + owned parts re-add to the owner-method flight
    assert SD.landing_m3(2.10, 0.80, T) + SD.landing_m3(2.10, 0.20, T) == pytest.approx(0.315)


def test_metamorphic_order_and_units():
    base = SD.totals(villa_d())["closable_total"]
    for perm in itertools.islice(itertools.permutations(villa_d()), 0, 50, 7):
        assert SD.totals(list(perm))["closable_total"] == pytest.approx(base, abs=1e-12)
    mm = SD.flight_m3(10, SD.to_m(150, "mm"), SD.to_m(28, "cm"), 9, SD.to_m(1000, "mm"), SD.to_m(15, "cm"),
                      wedges=[SD.to_m(150, "mm")], foot_a=SD.to_m(100, "mm"))
    assert mm["net"] == pytest.approx(0.6034859, abs=1e-6)
    with pytest.raises(SD.LedgerError):
        SD.to_m(150, "in")


# ---------------- adverse cases

def test_landing_in_both_slab_and_stair_refused():
    comps = villa_d() + [SD.component("ARR-AS-STAIR", "ST-D", "arrival landing billed as stair", "CLOSABLE",
                                      "DRAWING-CONFIRMED", "STAIR", value=2.5 * 1.0 * 0.15, region="SLAB:D-ARR",
                                      source="plan")]
    with pytest.raises(SD.LedgerError, match="counted twice"):
        SD.check_line(comps, SLAB)
    lone = [c for c in villa_d() if c["id"] != "ARR"] + [comps[-1]]
    with pytest.raises(SD.LedgerError, match="slab ledger"):
        SD.check_line(lone, SLAB)
    with pytest.raises(SD.LedgerError, match="R-STAIR-LAND-1"):
        SD.component("ARR2", "ST-D", "floor landing", "CLOSABLE", "DRAWING-CONFIRMED", "STAIR", value=0.375,
                     source="plan", floor_level_landing=True)


def test_winder_released_without_drawn_geometry_refused():
    with pytest.raises(SD.LedgerError, match="without drawn geometry"):
        SD.component("W", "ST-W", "winder turn", "CLOSABLE", "DRAWING-CONFIRMED", "STAIR", value=0.055,
                     source="plan", geometry_drawn=False)


def test_missing_waist_never_zero():
    with pytest.raises(SD.LedgerError, match="never computed with 0"):
        SD.flight_m3(5, R, G, 4, W, None)
    with pytest.raises(SD.LedgerError, match="silent 0"):
        SD.component("WA", "ST-D", "waist", "HELD", "HELD", "STAIR", bound=[0.0, 0.0], blocker="not printed")
    with pytest.raises(SD.LedgerError, match="positive value"):
        SD.component("WA", "ST-D", "waist", "CLOSABLE", "DRAWING-CONFIRMED", "STAIR", value=0.0, source="plan")
    with pytest.raises(SD.LedgerError, match="no released value"):
        SD.component("WA", "ST-D", "waist", "HELD", "HELD", "STAIR", value=0.0, blocker="not printed")


def test_conflict_never_collapsed():
    rd = {"plan": 0.80, "section": 0.95}
    ok = SD.component("MS", "ST-D", "flight", "CONFLICT", "HELD", "STAIR", readings=rd, bound=[0.80, 0.95],
                      blocker="designer")
    assert SD.totals([ok])["conflict"] == [0.80, 0.95]
    with pytest.raises(SD.LedgerError, match="never collapsed"):
        SD.component("MS", "ST-D", "flight", "CONFLICT", "HELD", "STAIR", readings=rd, bound=[0.80, 0.95],
                     value=0.95, blocker="designer")
    with pytest.raises(SD.LedgerError, match="exactly"):
        SD.component("MS", "ST-D", "flight", "CONFLICT", "HELD", "STAIR", readings=rd, bound=[0.95, 0.95],
                     blocker="designer")
    with pytest.raises(SD.LedgerError, match="two or more"):
        SD.component("MS", "ST-D", "flight", "CONFLICT", "HELD", "STAIR", readings={"plan": 0.8}, bound=[0.8, 0.8],
                     blocker="designer")


def test_dome_without_detail_held_and_rise_not_radius():
    with pytest.raises(SD.LedgerError):
        SD.shell_m3(4.0, 1.0, None)
    hemi_of_radius = 2 * math.pi * 2.0 ** 2 * 0.08  # rise = radius convention, outer area x t
    assert abs(hemi_of_radius - SD.shell_m3(4.0, 1.0, 0.08)) > 0.5


def test_landing_edge_overlap_refused():
    # a landing read from the other flight's first riser line, 0.05 short of the arriving flight's last riser line
    r = SD.resolve_landing_edge(0.0, 0.05, 1.00)
    assert r["accepted"] is False and r["overlap_m2"] == pytest.approx(0.05)
    assert SD.resolve_landing_edge(0.05, 0.05, 1.00)["accepted"] is True


def test_head_and_foot_ranges():
    with pytest.raises(SD.LedgerError):
        SD.head_in_member_m3(0.30, R, G, W, T)  # a >= g: not a head inside one tread
    with pytest.raises(SD.LedgerError):
        SD.foot_in_member_m3(0.40, R, G, W, T)  # beyond the waist below the floor
    assert SD.head_in_member_m3(0.0, R, G, W, T) == 0.0


def test_owned_elsewhere_must_name_another_line():
    with pytest.raises(SD.LedgerError, match="owned elsewhere"):
        SD.component("X", "ST-D", "x", "OWNED_ELSEWHERE", "VERIFIED", "STAIR", value=0.01)
    with pytest.raises(SD.LedgerError, match="owned by"):
        SD.component("X", "ST-D", "x", "CLOSABLE", "VERIFIED", "BEAM", value=0.01, source="plan")
