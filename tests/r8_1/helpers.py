"""Shared helpers for R8.1 tests (test side only)."""

from __future__ import annotations

from tests.r8_0 import libredwg_builder as B, scenes as S
from tests.r8_0.geometry import compare_arc, compare_bulge, compare_segment, failed_fields
from tests.r8_0.k1_harness import realise_decode

CURVE = {c[1]: c for c in S.CURVE_CASES}
BP = {c[1]: c for c in S.BASE_POINT_CASES}
MI = {c[1]: c for c in S.MINSERT_CASES}
REFLECTING = sorted(k for k, c in CURVE.items() if S.curve_case_truth(c)["orientation_sign"] < 0)
NON_REFLECTING = sorted(k for k, c in CURVE.items() if S.curve_case_truth(c)["orientation_sign"] > 0)


def k1(scene):
    return realise_decode(B.build(scene))


def curve_failures(truth, got):
    bad = []
    if len(got["arcs"]) != 1:
        return ["ARC_COUNT"]
    if len(got["bulges"]) != 1:
        return ["BULGE_COUNT"]
    bad += failed_fields(compare_arc(truth["arc"], got["arcs"][0]))
    bad += ["bulge." + f for f in failed_fields(compare_bulge(truth["bulge"], got["bulges"][0]))]
    bad += ["line." + f for f in failed_fields(compare_segment(truth["line"], got["segments"][0]))]
    return bad


def curve_scene_failures(sid):
    return curve_failures(S.curve_case_truth(CURVE[sid]), k1(CURVE[sid][3]))


def base_point_failures(sid):
    return curve_failures(S.base_point_truth(BP[sid]), k1(BP[sid][3]))
