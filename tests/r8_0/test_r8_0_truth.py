"""R8.0 — the truth is independent of every implementation under test.

1. every hand-written point map agrees with ezdxf 1.4.4 (a separate code base);
2. every stated orientation sign agrees with the map itself;
3. the test-side reference realiser (used for mutation tests) agrees with
   the hand truth, so a mutant that fails a fixture fails for its mutation;
4. literal spot values for the headline case are written out in full.
"""

from __future__ import annotations

import math

import pytest

from . import ezdxf_oracle, reference_realiser as RR, scenes as S
from .geometry import (close, compare_arc, compare_bulge, compare_segment, failed_fields,
                       match_segment_sets, orientation_of)

CURVE_IDS = [c[1] for c in S.CURVE_CASES]
BP_IDS = [c[1] for c in S.BASE_POINT_CASES]
MI_IDS = [c[1] for c in S.MINSERT_CASES]


def _curve(sid):
    return next(c for c in S.CURVE_CASES if c[1] == sid)


def _bp(sid):
    return next(c for c in S.BASE_POINT_CASES if c[1] == sid)


def _mi(sid):
    return next(c for c in S.MINSERT_CASES if c[1] == sid)


def _all_ok(truth, got):
    bad = failed_fields(compare_arc(truth["arc"], got["arcs"][0]))
    bad += ["bulge." + f for f in failed_fields(compare_bulge(truth["bulge"], got["bulges"][0]))]
    bad += ["line." + f for f in failed_fields(compare_segment(truth["line"], got["segments"][0]))]
    return bad


@pytest.mark.parametrize("sid", CURVE_IDS)
def test_curve_truth_agrees_with_ezdxf(sid):
    case = _curve(sid)
    assert _all_ok(S.curve_case_truth(case), ezdxf_oracle.realise(case[3])) == []


@pytest.mark.parametrize("sid", BP_IDS)
def test_base_point_truth_agrees_with_ezdxf(sid):
    case = _bp(sid)
    assert _all_ok(S.base_point_truth(case), ezdxf_oracle.realise(case[3])) == []


@pytest.mark.parametrize("sid", MI_IDS)
def test_minsert_truth_agrees_with_ezdxf(sid):
    case = _mi(sid)
    ok, missing, extra = match_segment_sets(case[4], ezdxf_oracle.realise(case[3])["segments"])
    assert ok, f"missing {missing} unexpected {extra}"


@pytest.mark.parametrize("sid", CURVE_IDS)
def test_stated_orientation_matches_the_map(sid):
    t = S.curve_case_truth(_curve(sid))
    a = t["arc"]
    assert orientation_of(a["START_POINT"], a["MID_SWEEP_POINT"], a["END_POINT"], a["CENTER"]) == a["SWEEP_DIRECTION"]


@pytest.mark.parametrize("sid", CURVE_IDS)
def test_reference_realiser_matches_truth_curves(sid):
    case = _curve(sid)
    r = RR.realise(case[3])
    assert _all_ok(S.curve_case_truth(case), {"arcs": r.arcs, "bulges": r.bulges, "segments": r.segments}) == []


@pytest.mark.parametrize("sid", BP_IDS)
def test_reference_realiser_matches_truth_base_point(sid):
    case = _bp(sid)
    r = RR.realise(case[3])
    assert _all_ok(S.base_point_truth(case), {"arcs": r.arcs, "bulges": r.bulges, "segments": r.segments}) == []


@pytest.mark.parametrize("sid", MI_IDS)
def test_reference_realiser_matches_truth_minsert(sid):
    case = _mi(sid)
    assert match_segment_sets(case[4], RR.realise(case[3]).segments)[0]


def test_headline_literals_mirror_x():
    """F02 X mirror, written out: nothing computed by any engine."""
    t = S.curve_case_truth(_curve("F02_MIRROR_X"))["arc"]
    h = 500.0 * math.sqrt(0.5)
    assert close(t["CENTER"], (-1000.0, 0.0))
    assert close(t["START_POINT"], (-1500.0, 0.0))
    assert close(t["MID_SWEEP_POINT"], (-1000.0 - h, h))
    assert close(t["END_POINT"], (-1000.0, 500.0))
    assert t["SWEEP_DIRECTION"] == "CW"
    b = S.curve_case_truth(_curve("F02_MIRROR_X"))["bulge"]
    assert close(b["VERTEX_A"], (-1500.0, 0.0)) and close(b["VERTEX_B"], (-1000.0, 500.0))
    assert close(b["ARC_MIDPOINT"], (-1000.0 - h, h)) and b["SIDE_OF_CHORD"] == "LEFT"


def test_bulge_local_truth_is_a_quarter_circle():
    """The bulge value and the local centre/midpoint are consistent by construction."""
    theta = 4.0 * math.atan(S.BULGE_Q)
    assert abs(math.degrees(theta) - 90.0) < 1e-12
    b = S.LOCAL["bulge"]
    for p in (b["VERTEX_A"], b["VERTEX_B"], b["ARC_MIDPOINT"]):
        assert abs(math.hypot(p[0] - b["CENTER"][0], p[1] - b["CENTER"][1]) - 500.0) < 1e-9
