"""R8.0 F02 / F03 / F05 — curved geometry in WCS under reflection and OCS.

Tests PHYSICAL geometry, never representations. For every transform case:
    ARC   : CENTER, START_POINT, MID_SWEEP_POINT, END_POINT, SWEEP_DIRECTION, RADIUS
    BULGE : VERTEX_A, ARC_MIDPOINT, VERTEX_B, SIDE_OF_CHORD, SWEEP_DIRECTION, CENTER
    LINE  : both end points

Current engine = production engine/cad_adapter.normalize, unmodified.
R8 K1 = the future engine/source kernel (TARGET_NOT_IMPLEMENTED today).
Expected failures are frozen in registers/R8_0_EXPECTED_FAILURES.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from . import libredwg_builder as B, scenes as S, targets
from .geometry import compare_arc, compare_bulge, compare_segment, current_realised, failed_fields

IDS = [c[1] for c in S.CURVE_CASES]
CASE = {c[1]: c for c in S.CURVE_CASES}
REG = Path(__file__).parent / "registers" / "R8_0_EXPECTED_FAILURES.json"


def _truth(sid):
    return S.curve_case_truth(CASE[sid])


def _current(sid):
    return current_realised(B.build(CASE[sid][3]))


def _one(items, what):
    assert len(items) == 1, f"expected exactly one realised {what}, got {len(items)}"
    return items[0]


@pytest.mark.parametrize("sid", IDS)
def test_arc_current_engine(sid):
    bad = failed_fields(compare_arc(_truth(sid)["arc"], _one(_current(sid)["arcs"], "ARC")))
    assert bad == [], f"{sid}: ARC wrong in WCS on {bad}"


@pytest.mark.parametrize("sid", IDS)
def test_bulge_current_engine(sid):
    bad = failed_fields(compare_bulge(_truth(sid)["bulge"], _one(_current(sid)["bulges"], "bulge span")))
    assert bad == [], f"{sid}: bulge span wrong in WCS on {bad}"


@pytest.mark.parametrize("sid", IDS)
def test_line_current_engine(sid):
    bad = failed_fields(compare_segment(_truth(sid)["line"], _one(_current(sid)["segments"], "LINE")))
    assert bad == [], f"{sid}: LINE wrong in WCS"


@pytest.mark.parametrize("sid", IDS)
def test_k1_acceptance(sid):
    """The R8 kernel must realise every case exactly (all fields, all kinds)."""
    got = targets.call("K1_REALISE", B.build(CASE[sid][3]))
    t = _truth(sid)
    bad = failed_fields(compare_arc(t["arc"], _one(got["arcs"], "ARC")))
    bad += failed_fields(compare_bulge(t["bulge"], _one(got["bulges"], "bulge")))
    bad += failed_fields(compare_segment(t["line"], _one(got["segments"], "LINE")))
    assert bad == []


def _signatures():
    rows = json.loads(REG.read_text())["defect_signatures"]
    return {r["scene"]: r for r in rows if r["file"] == "test_r8_0_curves.py"}


SIG_IDS = sorted(_signatures())


@pytest.mark.parametrize("sid", SIG_IDS)
def test_defect_signature_is_exactly_as_predicted(sid):
    """The current engine fails on EXACTLY the fields predicted analytically
    (03_EXPECTED_FAILURES.md) — no more, no fewer. Passes today; must be
    updated in the same change that fixes the engine."""
    sig = _signatures()[sid]
    cur, t = _current(sid), _truth(sid)
    got = {"arc": failed_fields(compare_arc(t["arc"], cur["arcs"][0])),
           "bulge": failed_fields(compare_bulge(t["bulge"], cur["bulges"][0])),
           "line": failed_fields(compare_segment(t["line"], cur["segments"][0]))}
    assert got == sig["failing_fields"]
