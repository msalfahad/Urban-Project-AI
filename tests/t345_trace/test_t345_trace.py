"""T-345 trace of a stair-residue floor line: synthetic villa VG-345 (hand-calculated; not the development villa).

Hand villa VG-345, first-floor open face 10.00 x 6.00 = 60.000 m2, metres (unit_m 1.0):
  void V1 x 6..10, y 0..3                                           = 12.000
  own flight A, 5 straight treads 1.00 x 0.30 (x 0..1, y 0..1.5)    =  1.500  (base 1.500)
  own flight B, one concave winder quad (2,0) (4,0) (3,0.5) (3,2)   =  1.250  (base clipped as convex: 1.000)
  below flight C, x 0..2, y 4..5                                    =  2.000  (base 2.000)
  below flight D, x 1.5..3.5, y 4..5, overlaps C by 0.5 x 1.0       =  1.500  (base sums it again: 2.000)
  below flight E, x 5..7, y 1..2, half of it inside the void        =  1.000  (base 1.000)
  residue cells R01 VOID_RESIDUE 0.600, R02 STAIR_FOOTPRINT 0.900; held foot 0.400 settled as tread 0.300 (NOT_FLOOR)
  + nosing 0.100 (FLOOR); landing split out 3.000.
  floor before residue 60 - 12 - 2.75 - 4.5 = 40.750; range low 40.75 - 0.6 - 0.9 - 0.4 = 38.850;
  settled + 0.100 = 38.950; net after the landing 35.950.
  base list 1.5 + 1.0 (treads) + 12 (void) + 5.0 (below) = 19.500; step face - base - (3.0 + 0.3) - net = 1.250
  = B +0.250 + D -0.500 + R01 0.600 + R02 0.900.
"""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t345_trace", ROOT / "research" / "agents_t345" / "t345_trace.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)
from tools import t330_deductions_check as C  # noqa: E402

FLIGHTS = [("VG:A", "own", 1.5, 1.5, 1.5), ("VG:B", "own", 1.25, 1.25, 1.0), ("VG:C", "below", 2.0, 2.0, 2.0),
           ("VG:D", "below", 1.5, 2.0, 2.0), ("VG:E", "below", 1.0, 2.0, 1.0)]


def record(**kw):
    rec = {"policy": "STAIR_FLOOR_RESIDUE_V1", "face_id": "VG-F1", "room_id": "1F-VG1", "face_m2": 60.0,
           "void_m2": 12.0, "stair_flights_m2": 2.75, "stair_below_seen_m2": 4.5, "scope": "STAIR_PASSES_THROUGH_SLAB",
           "void_residue_m2": 0.6, "stair_footprint_m2": 0.9, "held_m2": 0.4, "floor_before_residue_m2": 40.75,
           "voids": [{"void_id": "V1"}],
           "pieces": [{"piece": "R01", "category": "VOID_RESIDUE", "m2": 0.6, "touches_flights": ["VG:E"]},
                      {"piece": "R02", "category": "STAIR_FOOTPRINT", "m2": 0.9, "touches_flights": ["VG:A", "VG:B"]}],
           "held": [{"piece": "FOOT:VG:A:start", "m2": 0.4}]}
    rec.update(kw)
    return rec


def line(net=35.95, pieces=True, **kw):
    v30 = {k: record()[k] for k in ("scope", "face_m2", "void_m2", "void_residue_m2", "stair_footprint_m2", "held_m2",
                                    "floor_before_residue_m2")}
    v30["conservation"] = {"face_m2": 60.0}
    fs = {"id": "VG-SETTLED", "split_out": {"part": "landing", "area_m2": 3.0, "decision": "landing with the stair"}}
    if pieces:
        fs["pieces"] = [{"piece": "foot tread", "area_m2": 0.3, "to": "NOT_FLOOR", "why": "a tread"},
                        {"piece": "foot nosing", "area_m2": 0.1, "to": "FLOOR", "why": "landing nosing"}]
    ln = {"line_id": "L-VG345", "trade": "FIN", "item_code": "FIN.FLOOR.PORCELAIN", "unit": "m2", "gross": net,
          "measured_net": net, "location": {"floor": "1F", "element_id": "1F-VG1:floor", "room_id": "1F-VG1"},
          "deductions": [{"what": T.BASE_TREADS + " (marble)", "m2": 2.5}, {"what": T.BASE_VOID, "m2": 12.0},
                         {"what": T.BASE_BELOW + " (counted once)", "m2": 5.0}],
          "calculation": {"formula": "", "inputs": {"v3_0": v30, "floor_scope_v3014": fs}}}
    ln.update(kw)
    return ln


def test_normal_trace_closes_and_names_the_step():
    ln = line()
    before = copy.deepcopy(ln)
    rec, rows = T.trace_line(ln, record(), FLIGHTS)
    assert ln == before                                       # input never modified
    assert rec["status"] == "TRACED", rec
    assert rec["gross_used"] == 60.0 and abs(rec["residual"]) <= T.TOL
    assert rec["trace_sum"] == pytest.approx(24.05, abs=1e-9)
    assert rec["step_named"] == pytest.approx(1.25, abs=1e-9)
    step = T.step_decomposition(rows, {})
    assert sum(x[2] for x in step) == pytest.approx(1.25, abs=1e-9)
    assert {(i, round(a, 6)) for i, _c, a in step} == {("VG:B", 0.25), ("VG:D", -0.5), ("VG-F1:R01", 0.6),
                                                     ("VG-F1:R02", 0.9)}
    nose = [r for r in rows if "nosing" in str(r["item_id"])]
    assert nose == []                                         # a piece settled as FLOOR stays in the net


def test_applied_trace_passes_the_t330_check():
    ln = line()
    rec, rows = T.trace_line(ln, record(), FLIGHTS)
    assert C.check_line(ln)["category"] != "OK"               # the stale base list does not explain the net
    out = T.apply_trace([ln], [rec], rows)
    assert out[0]["gross"] == 60.0 and ln["gross"] == 35.95
    assert C.check_lines(out)["flagged"] == 0 and C.check_lines(out)["refused"] == 0


def test_adverse_range_low_taken_as_net_is_not_filled():
    ln = line(net=38.85)                                     # the piece's range low, not the line's settled net
    rec, rows = T.trace_line(ln, record(), FLIGHTS)
    assert rec["status"] == "TRACED_RESIDUAL"
    assert rec["residual"] == pytest.approx(60 - 24.05 - 38.85, abs=1e-9)   # -2.900 named, never forced
    assert T.apply_trace([ln], [rec], rows)[0] is ln


def test_adverse_cell_deducted_twice_is_refused():
    rec_ = record(pieces=record()["pieces"] + [record()["pieces"][0]], void_residue_m2=0.6)
    rec, rows = T.trace_line(line(), rec_, FLIGHTS)
    assert rec["status"] == "REFUSED" and "listed twice" in rec["cause"]


def test_adverse_held_piece_never_zero():
    ln = line(pieces=False)                                  # no settlement of the 0.400 held foot
    rec, _rows = T.trace_line(ln, record(), FLIGHTS)
    assert rec["status"] == "NOT_TRACEABLE" and "stays HELD" in rec["cause"]
    ln2 = line(measured_net=None)
    rec2, _ = T.trace_line(ln2, record(), FLIGHTS)
    assert rec2["status"] == "NOT_TRACEABLE" and rec2["residual"] is None   # never 0


def test_adverse_record_of_another_face_refused():
    rec, rows = T.trace_line(line(), record(void_m2=11.0), FLIGHTS)
    assert rec["status"] == "REFUSED" and "void_m2" in rec["cause"] and rows == []
    rec2, _ = T.trace_line(line(), None, FLIGHTS)
    assert rec2["status"] == "NOT_TRACEABLE"


def _room(tf=lambda x, y: (x, y), unit=1.0):
    s = 1.0 / unit
    pt = lambda x, y: tuple(c * s for c in tf(x, y))            # drawing units
    rect = lambda x0, y0, x1, y1: [pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)]
    treads = lambda x0, x1, y0, n, d: [rect(x0, y0 + k * d, x1, y0 + (k + 1) * d) for k in range(n)]
    room = {"polygon": rect(0, 0, 10, 6), "hole_polygons": [], "voids": [{"void_id": "V1"}],
            "polygon_m": [tf(0, 0), tf(10, 0), tf(10, 6), tf(0, 6)], "hole_polygons_m": [],
            "symbols_inside": {"stair_flights": [
                {"flight_id": "VG:A", "tread_quads": treads(0, 1, 0, 5, 0.3)},
                {"flight_id": "VG:B", "tread_quads": [[pt(2, 0), pt(4, 0), pt(3, 0.5), pt(3, 2)]]},
                {"flight_id": "VG:C", "drawn_on_plan_below": True, "tread_quads": [rect(0, 4, 2, 5)]},
                {"flight_id": "VG:D", "drawn_on_plan_below": True, "tread_quads": [rect(1.5, 4, 3.5, 5)]},
                {"flight_id": "VG:E", "drawn_on_plan_below": True, "tread_quads": [rect(5, 1, 7, 2)]}]}}
    voids = [{"void_id": "V1", "corners": rect(6, 0, 10, 3)}]
    return room, voids


@pytest.mark.parametrize("tf,unit", [(lambda x, y: (x, y), 1.0),          # as drawn, metres
                                     (lambda x, y: (-x, y), 1.0),         # mirror
                                     (lambda x, y: (-y, x), 1.0),         # rotation 90 deg
                                     (lambda x, y: (x, y), 0.001)])       # millimetre drawing
def test_flight_split_geometry_hand(tf, unit):
    room, voids = _room(tf, unit)
    got = {f: (k, round(m2, 4), round(q, 4)) for f, k, m2, q, _b in T.flight_split(room, voids, unit)}
    assert got == {"VG:A": ("own", 1.5, 1.5), "VG:B": ("own", 1.25, 1.25), "VG:C": ("below", 2.0, 2.0),
                   "VG:D": ("below", 1.5, 2.0), "VG:E": ("below", 1.0, 2.0)}
    base = {f: b for f, _k, _m, _q, b in T.flight_split(room, voids, unit)}
    assert base["VG:D"] == pytest.approx(2.0, abs=1e-4)      # the base sums the C / D overlap a second time
    assert base["VG:A"] == pytest.approx(1.5, abs=1e-4)
    assert base["VG:B"] < 1.25 - T.TOL                        # the concave winder quad is under-deducted by the base
