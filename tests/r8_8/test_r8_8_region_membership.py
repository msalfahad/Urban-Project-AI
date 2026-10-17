"""R8.8 §4-§5: region membership is EXACT for curves. No sampler can miss a crossing."""

from __future__ import annotations

import math

from engine.source import canonical_build as CB, canonical_input as CI, region_membership as RM
from engine.source import observations as O
from engine.source.cad import kernel
from tests.r8_8 import helpers as H


def r87_sampled_state(kind, g, box):
    """The R8.7 sampler, reproduced verbatim in spirit: 5 points per curve."""
    if kind == "ARC":
        cx, cy, r, a0, a1 = g
        sw = (a1 - a0) % (2 * math.pi)
        pts = [(cx + r * math.cos(a0 + sw * k / 4), cy + r * math.sin(a0 + sw * k / 4)) for k in range(5)]
    else:
        cx, cy, ux, uy, vx, vy, t0, t1 = g
        pts = [(cx + math.cos(t) * ux + math.sin(t) * vx, cy + math.cos(t) * uy + math.sin(t) * vy)
               for t in (t0 + (t1 - t0) * k / 4 for k in range(5))]
    x0, y0, x1, y1 = box
    ins = [x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts]
    return "INSIDE" if all(ins) else "OUTSIDE" if not any(ins) else "REVIEW"


def test_A_arc_crossing_missed_by_sparse_sampling_is_caught():
    arc = (0.0, 0.0, 10.0, math.radians(10), math.radians(100))       # true top y = 10 at 90 deg, between samples
    box = (-20.0, -20.0, 20.0, 9.9)
    assert r87_sampled_state("ARC", arc, box) == "INSIDE"               # the R8.7 defect, reproduced
    assert RM.classify("ARC", arc, box) == RM.CROSSES_BOUNDARY
    p = H.part(1, "ARC", arc, path=("50",))
    assert CB.membership(p, box) == CI.REVIEW_REQUIRED


def test_B_ellipse_crossing_between_sampled_parameters_is_caught():
    # x(t) = 20 cos t: the extremum 20 is at t = 0, between the R8.7 samples at -10 and +10 deg (x = 19.70)
    ell = (0.0, 0.0, 20.0, 0.0, 0.0, 5.0, math.radians(-50), math.radians(30))
    box = (-30.0, -30.0, 19.8, 30.0)
    assert r87_sampled_state("ELLIPTICAL_ARC", ell, box) == "INSIDE"
    assert RM.classify("ELLIPTICAL_ARC", ell, box) == RM.CROSSES_BOUNDARY
    assert CB.membership(H.part(2, "ELLIPTICAL_ARC", ell, path=("51",)), box) == CI.REVIEW_REQUIRED


def test_C_tangent_circle_policy_is_frozen():
    assert RM.POLICY["tangent_rule"].startswith("RM-TANGENT-1")
    box = (0.0, 0.0, 100.0, 100.0)
    assert RM.classify("CIRCLE", (50.0, 10.0, 10.0), box) == RM.FULLY_INSIDE        # touches y = 0 from inside
    assert RM.classify("CIRCLE", (50.0, -10.0, 10.0), box) == RM.CROSSES_BOUNDARY   # touches from outside
    assert RM.classify("CIRCLE", (50.0, -10.5, 10.0), box) == RM.FULLY_OUTSIDE
    assert RM.classify("CIRCLE", (50.0, 50.0, 200.0), box) == RM.FULLY_OUTSIDE      # encloses the box, never meets it


def _doc(insert):
    blk = O.BlockDefinition("HB", "SYM", (0.0, 0.0), (
        O.SourceEntityObservation("D1:20", "20", "T:ARC", O.ARC, O.ArcGeom((0.0, 0.0), 10.0, math.radians(10),
                                                                           math.radians(100)), "WALL"),))
    ins = O.SourceEntityObservation("D1:30", "30", "T:INSERT", O.INSERT, insert, "0")
    return O.SourceDocument(O.SourceRevisionAnchor(None, "T", "T"), (ins,), {"HB": blk})


def test_D_rotated_and_reflected_occurrences_get_the_answer_of_their_physical_geometry():
    for rot, sx in ((0.0, 1.0), (math.pi / 2, 1.0), (math.pi / 3, -1.0), (math.pi, -1.0)):
        real = kernel.realise(_doc(O.InsertGeom("HB", (100.0, 100.0), (sx, 1.0, 1.0), rot)))
        a = real.arcs[0]
        p = CB.parts_from_realised("R", real, lambda path: (), None)[0]
        bb = RM.exact_bbox("ARC", p.geometry)
        # the true world extent: dense evaluation of the realised world arc (test oracle only)
        st, en = (a.start, a.end) if a.direction == "CCW" else (a.end, a.start)
        a0 = math.atan2(st[1] - a.center[1], st[0] - a.center[0])
        sw = (math.atan2(en[1] - a.center[1], en[0] - a.center[0]) - a0) % (2 * math.pi)
        dense = [(a.center[0] + a.radius * math.cos(a0 + sw * k / 20000), a.center[1] + a.radius * math.sin(a0 + sw * k / 20000))
                 for k in range(20001)]
        assert abs(bb[2] - max(x for x, _ in dense)) < 1e-6 and abs(bb[3] - max(y for _, y in dense)) < 1e-6
        tight = (bb[0], bb[1], bb[2], bb[3])
        assert RM.classify("ARC", p.geometry, tight) == RM.FULLY_INSIDE
        shaved = (bb[0], bb[1], bb[2] - 0.05, bb[3])
        assert RM.classify("ARC", p.geometry, shaved) == RM.CROSSES_BOUNDARY


def test_E_no_quantity_can_depend_on_a_sampler_missing_the_crossing():
    arc = H.part(1, "ARC", (0.0, 0.0, 10.0, math.radians(10), math.radians(100)), path=("50",))
    other = H.seg(2, -5, -5, 5, -5, path=("50",))
    i = CB.assemble(H.rev(), H.REGION, (-20.0, -20.0, 20.0, 9.9), "F", 10.0, "U", [arc, other], [], [])
    assert i.parts == () and len(i.region_review) == 2            # the whole occurrence is held, never cut
    c = CI.MethodContract("M", "1", part_fields=("source_part_id",))
    assert CI.validate(i, c)["state"] == CI.METHOD_INPUT_INCOMPLETE


def test_segment_and_text_membership_are_exact_too():
    box = (0.0, 0.0, 10.0, 10.0)
    assert RM.classify("SEGMENT", (-5, 5, -1, 5), box) == RM.FULLY_OUTSIDE
    assert RM.classify("SEGMENT", (-5, 5, 15, 5), box) == RM.CROSSES_BOUNDARY          # both ends out, passes through
    assert RM.classify("SEGMENT", (1, 1, 9, 9), box) == RM.FULLY_INSIDE
    assert CB.membership(H.text(5, "X", 5.0, 5.0), box) == CI.IN_REGION
    assert CB.membership(H.text(6, "X", None, None), box) == CI.REVIEW_REQUIRED
