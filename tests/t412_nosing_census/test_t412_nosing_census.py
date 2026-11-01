"""T-412 nosing / tread / riser census: hand fixture 'Villa K412' (not Alsenan) with normal and adverse cases.

Villa K412 (hand-drawn, metres): a dog-leg stair, storey 2.720 m = 16 risers of 0.170.
  Flight A: 8 risers, going 0.250, front edges at s = 0, 0.25 .. 1.75, width 1.000 between a wall and a string;
            a column 0.040 proud of the wall over s [0.30, 0.80): the edges at s 0.50 and 0.75 lose 0.040 each;
            the 8th edge is the half-landing edge (a nosing, not a tread).
  Flight B: 8 risers from the landing to the floor, width 1.000; edges 1..7 drawn, the 8th is the floor edge (drawn).
  Hand: A = 8 x 1.000 - 2 x 0.040 = 7.920 lm (step basis 7 x 1.000 - 0.080 = 6.920; landing edge 1.000);
        B = 8 x 1.000 = 8.000 (step basis 7.000; floor edge 1.000); treads 7 + 7 = 14; risers 16; nosings 16.
  Curved front edge (a fan step): radius 1.500, 30 deg: arc 0.785398 lm; its chord 0.776457 is refused.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t412"))
import nosing_census as N  # noqa: E402


def _flight_a(**over):
    edges = []
    for i in range(8):
        s = 0.25 * i
        kw = dict(eid=f"A{i + 1}", flight="A", riser_no=i + 1, kind=N.LANDING_EDGE if i == 7 else N.TREAD,
                  status=N.CONFIRMED, length_m=1.000, notch_m=N.notch_on_edge(s, 0.30, 0.80, 0.040),
                  binds=(f"B7-05:A{i + 1}",))
        edges.append(N.Edge(**kw))
    return N.FlightCensus(flight="A", stair="K", risers=8, risers_source="section", edges=edges)


def _flight_b():
    edges = [N.Edge(eid=f"B{i}", flight="B", riser_no=i, kind=N.FLOOR_EDGE if i == 8 else N.TREAD,
                    status=N.CONFIRMED, length_m=1.000) for i in range(1, 9)]
    return N.FlightCensus(flight="B", stair="K", risers=8, risers_source="section", edges=edges)


def test_hand_fixture_flight_a():
    s = _flight_a().summary()
    assert s["nosing_lm_confirmed"] == pytest.approx(7.920, abs=1e-9)
    assert s["nosing_lm_confirmed_in_step_basis"] == pytest.approx(6.920, abs=1e-9)
    assert s["nosing_lm_confirmed_landing_floor"] == pytest.approx(1.000, abs=1e-9)
    assert (s["risers"], s["treads"], s["landing_edges"], s["floor_edges"]) == (8, 7, 1, 0)


def test_hand_fixture_flight_b_and_stair_totals():
    a, b = _flight_a().summary(), _flight_b().summary()
    assert b["nosing_lm_confirmed"] == pytest.approx(8.000) and b["floor_edges"] == 1 and b["treads"] == 7
    assert a["risers"] + b["risers"] == 16 and a["treads"] + b["treads"] == 14
    assert a["nosings_confirmed"] + b["nosings_confirmed"] == 16


def test_notch_interval_is_half_open():
    # downhill face of the column on the edge line blocks the tread behind it; uphill face does not
    assert N.notch_on_edge(0.30, 0.30, 0.80, 0.04) == 0.04
    assert N.notch_on_edge(0.80, 0.30, 0.80, 0.04) == 0.0
    assert N.notch_on_edge(0.25, 0.30, 0.80, 0.04) == 0.0
    with pytest.raises(N.NosingInputError):
        N.notch_on_edge(0.5, 0.8, 0.3, 0.04)


def test_curved_front_edge_on_the_arc():
    e = N.Edge(eid="F1", flight="F", riser_no=1, kind=N.TREAD, status=N.CONFIRMED, shape=N.ARC, radius_m=1.5,
               angle_deg=30.0)
    N.validate_edge(e)
    assert e.qty_lm == pytest.approx(1.5 * math.pi / 6, abs=1e-12)
    assert N.chord(1.5, 30.0) == pytest.approx(0.776457, abs=1e-6)


def test_adverse_curved_edge_on_the_chord_refused():
    e = N.Edge(eid="F1", flight="F", riser_no=1, kind=N.TREAD, status=N.CONFIRMED, shape=N.ARC, radius_m=1.5,
               angle_deg=30.0, length_m=N.chord(1.5, 30.0))
    with pytest.raises(N.NosingInputError, match="chord"):
        N.validate_edge(e)


def test_adverse_landing_counted_as_a_tread_refused():
    c = _flight_a()
    c.edges[3] = N.Edge(eid="A4", flight="A", riser_no=4, kind=N.LANDING_EDGE, status=N.CONFIRMED, length_m=1.0)
    with pytest.raises(N.NosingInputError, match="landing"):
        c.check()


def test_adverse_generated_winder_refused():
    e = N.Edge(eid="W1", flight="W", riser_no=1, kind=N.WINDER, status=N.CONFIRMED, length_m=1.3, source="generated")
    with pytest.raises(N.NosingInputError, match="generated"):
        N.validate_edge(e)


def test_drawn_winder_radial_edge_confirmed_and_section_only_refused():
    ok = N.Edge(eid="W1", flight="W", riser_no=1, kind=N.WINDER, status=N.CONFIRMED, length_m=1.414)
    N.validate_edge(ok)
    assert ok.qty_lm == pytest.approx(1.414)
    bad = N.Edge(eid="W2", flight="W", riser_no=2, kind=N.WINDER, status=N.CONFIRMED, length_m=1.0, source="section")
    with pytest.raises(N.NosingInputError, match="winder"):
        N.validate_edge(bad)


def test_adverse_count_mismatch_refused():
    c = _flight_a()
    c.edges.pop()
    with pytest.raises(N.NosingInputError, match="exactly one nosing"):
        c.check()
    c = _flight_a()
    c.risers = 9                     # a riser with no edge, drawn or held: never treads + 1 by arithmetic
    with pytest.raises(N.NosingInputError):
        c.check()


def test_held_is_blank_never_zero_and_names_its_cause():
    e = N.Edge(eid="H1", flight="A", riser_no=8, kind=N.FLOOR_EDGE, status=N.HELD, beside_lm=1.0,
               cause="edge not drawn")
    N.validate_edge(e)
    assert e.qty_lm is None
    with pytest.raises(N.NosingInputError, match="cause"):
        N.validate_edge(N.Edge(eid="H2", flight="A", riser_no=8, kind=N.FLOOR_EDGE, status=N.HELD))
    c = _flight_a()
    c.edges[7] = e
    s = c.summary()
    assert s["nosings_held"] == 1 and s["nosing_lm_confirmed"] == pytest.approx(6.920)
    assert s["held_beside_lm"] == pytest.approx(1.0)


def test_adverse_millimetres_as_metres_refused():
    with pytest.raises(N.NosingInputError, match="millimetres"):
        N.validate_edge(N.Edge(eid="M", flight="A", riser_no=1, kind=N.TREAD, status=N.CONFIRMED, length_m=1000.0))
    with pytest.raises(N.NosingInputError):
        N.straight_edges_from_segments([((0, 0), (1000, 0))], "m")
    with pytest.raises(N.NosingInputError, match="unit"):
        N.straight_edges_from_segments([((0, 0), (100, 0))], "cm")


def test_one_edge_one_item():
    a = _flight_a()
    N.overlap_check(a.edges, {"B7-09 RL-1": {"A-side-W"}, "B7-07 S1": {"A.W1"}})
    with pytest.raises(N.NosingInputError, match="one edge, one item"):
        N.overlap_check(a.edges, {"B7-09 RL-1": {"A3"}})
    with pytest.raises(N.NosingInputError, match="B7-05 only"):
        N.validate_edge(N.Edge(eid="A1", flight="A", riser_no=1, kind=N.TREAD, status=N.CONFIRMED, length_m=1.0,
                               binds=("B7-06:step-1",)))


def test_step_basis_split():
    e = _flight_a().edges
    assert [x.in_step_basis for x in e] == [True] * 7 + [False]


@pytest.mark.parametrize("deg,mirror", [(0, False), (37, False), (123, True), (270, True)])
def test_rotation_mirror_and_mm_invariance(deg, mirror):
    base = [((0.0, 250.0 * i), (1000.0, 250.0 * i)) for i in range(8)]
    t = math.radians(deg)

    def tr(p):
        x, y = p
        if mirror:
            x = -x
        return (x * math.cos(t) - y * math.sin(t) + 5000.0, x * math.sin(t) + y * math.cos(t) - 300.0)

    got = N.straight_edges_from_segments([(tr(a), tr(b)) for a, b in base], "mm")
    assert [round(s, 6) for s, _ in got] == [0.25 * i for i in range(8)]
    assert all(abs(ln - 1.0) < 1e-9 for _, ln in got)
    got_m = N.straight_edges_from_segments([((a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000))
                                            for a, b in base], "m")
    assert got_m == N.straight_edges_from_segments(base, "mm")


def test_non_parallel_edge_refused():
    with pytest.raises(N.NosingInputError, match="parallel"):
        N.straight_edges_from_segments([((0, 0), (1000, 0)), ((0, 250), (1000, 300))], "mm")


def test_piece_reconciliation_quantities_only():
    r = {x["stair"]: x for x in N.piece_reconciliation({"S1": 10, "S2": 5}, {"S1": 12, "S3": 4})}
    assert r["S1"]["his_minus_ours"] == 2 and r["S1"]["pct_of_ours"] == 20.0
    assert r["S2"]["his"] is None and r["S3"]["ours"] is None
