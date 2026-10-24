"""T-252 BEAM_LEDGER_R2 on a hand-calculated synthetic villa that is NOT Alsenan ('Villa Q').

Villa Q, one roof slab (metres unless stated; every value by hand):

(a) Carrier K: an oblique beam 0.30 wide at 30 degrees to the x axis. Its lower face is y = 4.000 + x tan30; its upper
    face lies 0.30 / cos30 = 0.346410 higher: y = 4.346410 + x tan30.
    Q1 (0.25 x 0.60) runs north from the face y = 0 of its support and stops on K's LOWER face; edges x = 0 / x = 0.25:
       La = 4.000000, Lb = 4.000000 + 0.25 tan30 = 4.144338; mean 4.072169; plan 0.25 x 4.072169 = 1.018042 m2;
       end triangle 0.25 x 0.144338 / 2 = 0.018042 m2; volume 1.018042 x 0.60 = 0.610825 m3.
       Billed to the short edge only (4.000): 0.25 x 0.60 x 4.000 = 0.600000 -> ONE_FACE_END, short by 0.010825 m3.
    Q2 (0.25 x 0.60) runs south from the face y = 8.000 of its support and stops on K's UPPER face:
       La = 8.000 - 4.346410 = 3.653590, Lb = 3.653590 - 0.144338 = 3.509252; mean 3.581421; plan 0.895355 m2.
(b) Ring R: a quarter ring between two arcs about (0, 0), outer R 1.25, inner R 1.00 (drawn width 0.25 = schedule),
    closed by the faces x = 0 and y = 0 of the two members it frames into; D 0.50:
       plan pi / 4 x (1.25^2 - 1.00^2) = 0.441786 m2, volume 0.220893 m3.
       The same ring banded as 6 chords per arc: 3 x sin 15deg x 0.5625 = 0.436757 m2 (under-covers by 0.005029 m2).
    A full annulus R 2.0 / void R 1.8: pi x (4.00 - 3.24) = 2.387610 m2.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t252"))
import beam_ledger_r2 as R2  # noqa: E402

T30 = math.tan(math.radians(30))


def _tf(p, k=1.0, rot=0.0, mirror=False, shift=(0.0, 0.0)):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ((c * x - s * y + shift[0]) * k, (s * x + c * y + shift[1]) * k)


def q1(k=1.0, rot=0.0, mirror=False, shift=(0.0, 0.0)):
    t = lambda p: _tf(p, k, rot, mirror, shift)  # noqa: E731
    ea = (t((0.0, 0.0)), t((0.0, 4.0)))
    eb = (t((0.25, 0.0)), t((0.25, 4.0 + 0.25 * T30)))
    start = (t((-1.0, 0.0)), t((1.0, 0.0)))
    carrier = (t((-1.0, 4.0 - T30)), t((1.0, 4.0 + T30)))
    return ea, eb, start, carrier


def q2():
    up = 4.0 + 0.30 / math.cos(math.radians(30))
    ea = ((0.0, 8.0), (0.0, up))
    eb = ((0.25, 8.0), (0.25, up + 0.25 * T30))
    return ea, eb, ((-1.0, 8.0), (1.0, 8.0)), ((-1.0, up - T30), (1.0, up + T30))


# ------------------------------------------------------------------------------------------ (a) oblique carrier
def test_lower_face_trapezoid_by_hand():
    r = R2.run_between_faces(*q1(), b_schedule=0.25, depth=0.60)
    assert r["b_drawn_m"] == pytest.approx(0.25, abs=1e-9)
    assert r["La_m"] == pytest.approx(4.000000, abs=1e-6)
    assert r["Lb_m"] == pytest.approx(4.144338, abs=1e-6)
    assert r["mean_length_m"] == pytest.approx(4.072169, abs=1e-6)
    assert r["plan_m2"] == pytest.approx(1.018042, abs=1e-6)
    assert r["end_triangle_m2"] == pytest.approx(0.018042, abs=1e-6)
    assert r["m3"] == pytest.approx(0.610825, abs=1e-6)


def test_upper_face_of_the_same_carrier():
    r = R2.run_between_faces(*q2(), depth=0.60)
    assert r["La_m"] == pytest.approx(3.653590, abs=1e-6)
    assert r["Lb_m"] == pytest.approx(3.509252, abs=1e-6)
    assert r["plan_m2"] == pytest.approx(0.895355, abs=1e-6)
    # the short edge is now edge b: a one-face end on the upper face is caught the same way
    c = R2.check_billed_end(3.509252, r)
    assert c["result"] == "ONE_FACE_END" and c["delta_length_m"] == pytest.approx(0.072169, abs=1e-6)


@pytest.mark.parametrize("unit,k", [("m", 1.0), ("cm", 100.0), ("mm", 1000.0)])
@pytest.mark.parametrize("rot,mirror", [(0.0, False), (30.0, False), (-47.5, True), (90.0, False), (180.0, True)])
def test_units_rotation_mirror_invariant(unit, k, rot, mirror):
    ea, eb, s, c = q1(k, rot, mirror, shift=(12.5, -3.0))
    r = R2.run_between_faces(ea, eb, s, c, unit=unit, depth=0.60 * k)
    assert r["plan_m2"] == pytest.approx(1.018042, abs=1e-6)
    assert r["m3"] == pytest.approx(0.610825, abs=1e-6)
    assert sorted((r["La_m"], r["Lb_m"])) == pytest.approx([4.0, 4.144338], abs=1e-6)


def test_one_face_end_refused_and_correction_named():
    r = R2.run_between_faces(*q1(), depth=0.60)
    c = R2.check_billed_end(4.000, r)
    assert c["result"] == "ONE_FACE_END"
    assert c["delta_length_m"] * 0.25 * 0.60 == pytest.approx(0.010825, abs=1e-6)
    with pytest.raises(R2.Refused, match="ONE_FACE_END"):
        R2.accept_billed_end(4.000, r)
    # the long edge only is a one-face end too (the triangle billed twice)
    assert R2.check_billed_end(4.144338, r)["result"] == "ONE_FACE_END"
    assert R2.accept_billed_end(4.072169, r)["result"] == "PASS"


def test_unexplained_length_is_not_corrected():
    r = R2.run_between_faces(*q1())
    c = R2.check_billed_end(3.90, r)
    assert c["result"] == "MISMATCH"
    with pytest.raises(R2.Refused, match="LENGTH_MISMATCH"):
        R2.accept_billed_end(3.90, r)


def test_square_end_has_no_triangle():
    ea, eb = ((0.0, 0.0), (0.0, 4.0)), ((0.25, 0.0), (0.25, 4.0))
    r = R2.run_between_faces(ea, eb, ((-1, 0), (1, 0)), ((-1, 4.0), (1, 4.0)))
    assert r["end_triangle_m2"] == pytest.approx(0.0, abs=1e-12)
    assert R2.check_billed_end(4.0, r)["result"] == "PASS"


def test_edge_stopping_short_of_the_face_refused():
    ea, eb, s, c = q1()
    eb = (eb[0], (0.25, 4.0))          # drawn edge b stops 0.144 m before the carrier face
    with pytest.raises(R2.Refused, match="EDGE_STOPS_SHORT_OF_FACE"):
        R2.run_between_faces(ea, eb, s, c)


def test_non_parallel_edges_and_parallel_face_refused():
    ea, eb, s, c = q1()
    with pytest.raises(R2.Refused, match="EDGES_NOT_PARALLEL"):
        R2.run_between_faces(ea, ((0.25, 0.0), (0.35, 4.0 + 0.35 * T30)), s, c)
    with pytest.raises(R2.Refused, match="EDGE_PARALLEL_TO_FACE"):
        R2.run_between_faces(ea, eb, ((0.0, 0.0), (0.0, 1.0)), c)


def test_width_conflict_not_collapsed():
    with pytest.raises(R2.Refused, match="WIDTH_CONFLICT"):
        R2.run_between_faces(*q1(), b_schedule=0.20)


# ------------------------------------------------------------------------------------------------ (b) curved ring
def quarter_ring(k=1.0):
    return [("line", (1.00 * k, 0.0), (1.25 * k, 0.0)), ("arc", (0.0, 0.0), 1.25 * k, 0.0, 90.0),
            ("line", (0.0, 1.25 * k), (0.0, 1.00 * k)), ("arc", (0.0, 0.0), 1.00 * k, 90.0, 0.0, "cw")]


@pytest.mark.parametrize("unit,k", [("m", 1.0), ("cm", 100.0), ("mm", 1000.0)])
def test_quarter_ring_area_by_hand(unit, k):
    r = R2.curved_member_area(quarter_ring(k), unit=unit, annuli=[(1.25 * k, 1.00 * k)], b_schedule=0.25 * k)
    assert r["area_m2"] == pytest.approx(0.441786, abs=1e-6)
    assert r["area_m2"] * 0.50 == pytest.approx(0.220893, abs=1e-6)
    assert r["widths_m"] == pytest.approx([0.25])


def test_loop_sense_does_not_matter():
    rev = [("arc", (0.0, 0.0), 1.00, 0.0, 90.0), ("line", (0.0, 1.00), (0.0, 1.25)),
           ("arc", (0.0, 0.0), 1.25, 90.0, 0.0, "cw"), ("line", (1.25, 0.0), (1.00, 0.0))]
    assert R2.loop_area(rev)[0] == pytest.approx(0.441786, abs=1e-6)


def test_full_annulus_with_void():
    outer = [("arc", (5.0, 5.0), 2.0, 0.0, 360.0)]
    void = [("arc", (5.0, 5.0), 1.8, 0.0, 360.0)]
    assert R2.curved_member_area(outer, [void])["area_m2"] == pytest.approx(2.387610, abs=1e-6)


def test_ring_banded_as_chords_refused_and_shown_short():
    n = 6
    chords = []
    for R in (1.25,):
        for i in range(n):
            a0, a1 = math.radians(90 * i / n), math.radians(90 * (i + 1) / n)
            chords.append(("chord", (R * math.cos(a0), R * math.sin(a0)), (R * math.cos(a1), R * math.sin(a1))))
    with pytest.raises(R2.Refused, match="CURVED_MEMBER_AS_CHORDS"):
        R2.loop_area([("line", (1.0, 0.0), (1.25, 0.0))] + chords)
    # what the chord bands would give (hand): under-covers the drawn ring
    chord_area = 0.5 * n * math.sin(math.radians(90 / n)) * (1.25 ** 2 - 1.0 ** 2)
    assert chord_area == pytest.approx(0.436757, abs=1e-6)
    once = R2.ring_counted_once(0.441786, chord_area, 0.0)
    assert once["missed_m2"] == pytest.approx(0.005029, abs=1e-6)


def test_ring_area_also_in_slab_refused():
    with pytest.raises(R2.Refused, match="RING_ALSO_IN_SLAB"):
        R2.ring_counted_once(0.441786, 0.40, slab_ledger_in_ring_m2=0.0418)


def test_ring_in_another_beam_refused_slivers_named():
    with pytest.raises(R2.Refused, match="RING_ALSO_IN_ANOTHER_BEAM"):
        R2.ring_counted_once(0.441786, 0.40, 0.0, other_beam_bands_in_ring_m2=0.02)
    ok = R2.ring_counted_once(0.441786, 0.40, 0.0, other_beam_bands_in_ring_m2=0.002)
    assert ok["sliver_residual_m2"] == pytest.approx(0.002) and ok["missed_m2"] == pytest.approx(0.041786)
    with pytest.raises(R2.Refused, match="BANDS_EXCEED_RING"):
        R2.ring_counted_once(0.441786, 0.46, 0.0)


def test_open_loop_inverted_annulus_void_outside_refused():
    bad = quarter_ring()
    bad[0] = ("line", (1.005, 0.0), (1.25, 0.0))     # 5 mm gap at the inner arc's end
    with pytest.raises(R2.Refused, match="LOOP_NOT_CLOSED"):
        R2.loop_area(bad)
    with pytest.raises(R2.Refused, match="ANNULUS_INVERTED"):
        R2.curved_member_area(quarter_ring(), annuli=[(1.0, 1.25)])
    with pytest.raises(R2.Refused, match="WIDTH_CONFLICT"):
        R2.curved_member_area(quarter_ring(), annuli=[(1.25, 1.0)], b_schedule=0.20)
    with pytest.raises(R2.Refused, match="VOID_NOT_INSIDE"):
        R2.curved_member_area(quarter_ring(), [[("arc", (0, 0), 3.0, 0.0, 360.0)]])
    with pytest.raises(R2.Refused, match="UNIT_UNKNOWN"):
        R2.loop_area(quarter_ring(), unit="in")


# ------------------------------------------------------------------------------------------- ledger revision
def _rows():
    return [dict(run="Q1", storey="L1", status="CALCULATED", m3=0.6, m3_low=0.6, m3_high=0.6),
            dict(run="R-a", storey="L1", status="CALCULATED", m3=0.10, m3_low=0.10, m3_high=0.10),
            dict(run="R-b", storey="L1", status="HELD", m3=None, m3_low=0.02, m3_high=0.06),
            dict(run="Y", storey="L1", status="CONFLICT", m3=None, m3_low=0.46, m3_high=0.555),
            dict(run="U", storey="L1", status="HELD", m3=None, m3_low=None, m3_high=None)]


def test_revision_supersedes_never_edits_and_totals():
    corr = [dict(kind="replace_length", run="Q1", length_m=4.072169, b=0.25, depth=0.60, basis="both faces"),
            dict(kind="supersede", runs=["R-a", "R-b"], basis="ring",
                 new=dict(run="R.r2", storey="L1", status="CALCULATED", m3=0.220893, m3_low=0.220893,
                          m3_high=0.220893))]
    r2 = R2.revise(_rows(), corr)
    by = {r["run"]: r for r in r2}
    assert by["Q1"]["status"] == "SUPERSEDED_R2" and by["Q1"]["m3"] == 0.6      # r1 value kept, not edited
    assert by["Q1.r2"]["m3"] == pytest.approx(0.610825, abs=1e-6)
    t = R2.totals(r2)["L1"]
    assert t["measured_m3"] == pytest.approx(0.610825 + 0.220893, abs=1e-6)
    assert t["superseded"] == 3 and t["held_n"] == 1 and t["held_no_value"] == ["U"]
    assert (t["conflict_low"], t["conflict_high"]) == (0.46, 0.555)


def test_revision_adverse():
    with pytest.raises(R2.Refused, match="CORRECTION_ON_UNMEASURED"):
        R2.revise(_rows(), [dict(kind="replace_length", run="R-b", length_m=1, b=0.2, depth=0.5, basis="x")])
    with pytest.raises(R2.Refused, match="CORRECTION_TARGET"):
        R2.revise(_rows(), [dict(kind="supersede", runs=["Q1"], basis="x", new=dict(run="n1", storey="L1")),
                            dict(kind="supersede", runs=["Q1"], basis="x", new=dict(run="n2", storey="L1"))])
    with pytest.raises(R2.Refused, match="RUN_TWICE"):
        R2.revise(_rows() + [_rows()[0]], [])
    bad = _rows()
    bad[2]["m3"] = 0.0                         # a HELD run shown as 0
    with pytest.raises(R2.Refused, match="HELD_WITH_VALUE"):
        R2.totals(bad)
