"""R8.0 F01 / F04 / F06 / F13 — block base points, non-uniform scale, MINSERT, anonymous blocks.

Current Al Rashed exposure for base points and MINSERT is ZERO. The defect
is still a defect and these fixtures stay (R8.0 brief §17, §18, §25).
"""

from __future__ import annotations

import pytest

from . import libredwg_builder as B, scenes as S, targets
from .geometry import (close, compare_arc, compare_bulge, compare_segment, current_realised,
                       failed_fields, match_segment_sets)

BP = {c[1]: c for c in S.BASE_POINT_CASES}
MI = {c[1]: c for c in S.MINSERT_CASES}


# ------------------------------------------------------------- F01 base point

@pytest.mark.parametrize("sid", list(BP))
def test_base_point_current_engine(sid):
    t = S.base_point_truth(BP[sid])
    cur = current_realised(B.build(BP[sid][3]))
    bad = failed_fields(compare_arc(t["arc"], cur["arcs"][0]))
    bad += ["bulge." + f for f in failed_fields(compare_bulge(t["bulge"], cur["bulges"][0]))]
    bad += ["line." + f for f in failed_fields(compare_segment(t["line"], cur["segments"][0]))]
    assert bad == [], f"{sid}: base point offset not realised: {bad}"


@pytest.mark.parametrize("sid", list(BP))
def test_base_point_k1_acceptance(sid):
    t = S.base_point_truth(BP[sid])
    got = targets.call("K1_REALISE", B.build(BP[sid][3]))
    bad = failed_fields(compare_arc(t["arc"], got["arcs"][0]))
    bad += failed_fields(compare_bulge(t["bulge"], got["bulges"][0]))
    bad += failed_fields(compare_segment(t["line"], got["segments"][0]))
    assert bad == []


# ------------------------------------------------------------------ F06 MINSERT

@pytest.mark.parametrize("sid", list(MI))
def test_minsert_current_engine_realises_every_cell(sid):
    cur = current_realised(B.build(MI[sid][3]))
    ok, missing, extra = match_segment_sets(MI[sid][4], cur["segments"])
    assert ok, f"{sid}: {len(missing)} of 6 grid cells not realised; unexpected {extra}"


@pytest.mark.parametrize("sid", list(MI))
def test_minsert_never_silently_disappears_current_engine(sid):
    """Today's engine does not expand MINSERT but it DOES count it as
    UNHANDLED type 8, so the omission is visible. This is the floor the
    new engine may not go below (regression guard; passes today)."""
    nd = current_realised(B.build(MI[sid][3]))["normalized"]
    realised_cells = len(nd.segments())
    assert realised_cells == 6 or nd.unhandled.get("8", 0) >= 1


@pytest.mark.parametrize("sid", list(MI))
def test_minsert_never_one_instance_for_many(sid):
    """An unexpanded MINSERT must never be reported as ONE placed instance."""
    nd = current_realised(B.build(MI[sid][3]))["normalized"]
    cell_instances = [i for i in nd.instances if i.block_name == "CELL"]
    assert len(cell_instances) in (0, 6)


@pytest.mark.parametrize("sid", list(MI))
def test_minsert_k1_acceptance(sid):
    got = targets.call("K1_REALISE", B.build(MI[sid][3]))
    assert match_segment_sets(MI[sid][4], got["segments"])[0]


# ---------------------------------------------------- F04 non-uniform scale

def test_non_uniform_scale_arc_current_engine():
    """scale (2,1) turns the quarter circle into an elliptical arc. The
    current engine keeps a CIRCLE of radius 500*scale_x centred at (2000,0),
    whose end point is (2000,1000) instead of (2000,500)."""
    cur = current_realised(B.build(S.F04_SCENE))
    arcs = cur["arcs"]
    pts = {"START_POINT": None, "MID_SWEEP_POINT": None, "END_POINT": None}
    if arcs:
        a = arcs[0]
        pts = {"START_POINT": a["P0"], "MID_SWEEP_POINT": a["PM"], "END_POINT": a["P1"]}
    bad = [k for k, v in S.F04_TRUTH_POINTS.items() if not close(v, pts[k])]
    assert bad == [], f"elliptical arc realised as a circle: {bad}"


def test_non_uniform_scale_k1_acceptance():
    """R8 K1: realise the elliptical arc (or refuse it with a visible
    NON_UNIFORM_SCALE_CURVE finding); never a circle through the wrong points."""
    got = targets.call("K1_REALISE", B.build(S.F04_SCENE))
    ell = got.get("elliptical_arcs", [])
    if ell:
        e = ell[0]
        assert all(close(S.F04_TRUTH_POINTS[k], e[k]) for k in S.F04_TRUTH_POINTS)
        assert not got["arcs"]
    else:
        assert any(f["code"] == "NON_UNIFORM_SCALE_CURVE" for f in got["findings"])
        assert not got["arcs"]


# ---------------------------------------------------- F13 anonymous blocks

F13_SCENE = {"blocks": {"*U7": {"entities": [{"kind": "LINE", "a": (0, 0), "b": (500, 0)}]}},
             "entities": [{"kind": "INSERT", "block": "*U7", "at": (1000.0, 0.0), "scale": (1.0, 1.0), "rot": 0.0}]}


def test_anonymous_block_realised_once_current_engine():
    """Anonymous (*U) block content is placed through its INSERT exactly once
    and never also at the definition origin (passes today)."""
    cur = current_realised(B.build(F13_SCENE))
    assert match_segment_sets([((1000.0, 0.0), (1500.0, 0.0))], cur["segments"])[0]


def test_anonymous_block_correlated_by_handle_across_routes():
    """R8: D1 and D2 may name the same anonymous block differently (*U7 vs
    *U12); reconciliation correlates by block-record handle and PASSES."""
    r = targets.call("RECONCILE", route_a={"decode": B.build(F13_SCENE), "rename": {}},
                     route_b={"decode": B.build(F13_SCENE), "rename": {"*U7": "*U12"}})
    assert r["verdict"] == "PASS" and r["correlated_by"] == "BLOCK_RECORD_HANDLE"
