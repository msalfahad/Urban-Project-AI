"""M9 S6 Phase 1 - the real plan (skipped unless URBAN_REAL_PLAN_DXF is set). Structural assertions only - classes,
gates, conservation, line identity - never a figure of the drawing and never a benchmark quantity: ARCH_TAKEOFF_V2 is
admitted, passes the completeness gate on every floor, keeps every V1 line unchanged, adds only lines without a
quantity, and every fill on the column layer lies on a measured column; V1 behind --strict-admission is admitted."""

from __future__ import annotations

import json
import os

import pytest

DXF = os.environ.get("URBAN_REAL_PLAN_DXF")
pytestmark = pytest.mark.skipif(not DXF, reason="real plan not provided (URBAN_REAL_PLAN_DXF)")


@pytest.fixture(scope="module")
def runs():
    from tools import urban_boq_m9 as M9
    v1 = M9.arch_compute(DXF, method="ARCH_TAKEOFF_V1")
    v2 = M9.arch_compute(DXF, method="ARCH_TAKEOFF_V2", intake=v1[2])
    return v1, v2


def test_v2_admitted_and_complete_on_every_floor(runs):
    _, (room, arch, _) = runs
    g = arch["discovery"]["gates"]
    assert g["architectural_boq_may_run"] and g["fatal"] == 0 and not g["stopping"]
    assert arch["coverage"] and all(c["gate"] == "PASS" and not c["unaccounted"] for c in arch["coverage"])
    for c in arch["coverage"]:
        pr = c["physical_regions"]
        assert pr["covered_m2"] == pytest.approx(pr["faces_m2"], abs=0.05)


def test_v2_keeps_every_v1_line_and_adds_none_with_a_quantity(runs):
    (r1, a1, _), (r2, a2, _) = runs
    by2 = {ln["line_id"]: ln for ln in r2["lines"]}
    for ln in r1["lines"]:
        assert json.dumps(by2.get(ln["line_id"]), sort_keys=True) == json.dumps(ln, sort_keys=True)
    ids1 = {ln["line_id"] for ln in r1["lines"]}
    added = [ln for ln in r2["lines"] if ln["line_id"] not in ids1]
    assert added and all(ln["measured_net"] is None for ln in added)
    assert sorted((r["room_id"], r["area_m2"]) for r in a1["rooms"]) == sorted((r["room_id"], r["area_m2"])
                                                                               for r in a2["rooms"])


def test_every_strip_is_reviewed_and_every_column_fill_is_measured(runs):
    _, (_, arch, _) = runs
    for fa in arch["floor_areas"]:
        assert sum(s["area_m2"] for s in fa["strips"]) == pytest.approx(fa["categories_m2"].get("DOORWAY_STRIPS", 0.0),
                                                                         abs=1e-3)       # categories at 4 dp
        assert all(s["disposition"] == "BLOCKED_RFI" for s in fa["strips"])
    ev = arch["discovery"]["stages"]["6_geometry_readiness"]["column_evidence"]
    assert ev and all(c["column_layers"] and c["unmeasured"] == 0 for c in ev)


def test_v1_strict_admits_the_real_plan():
    from tools import urban_boq_m9 as M9
    _, arch, _ = M9.arch_compute(DXF, method="ARCH_TAKEOFF_V1", strict=True)
    assert arch["discovery"]["gates"]["architectural_boq_may_run"]
