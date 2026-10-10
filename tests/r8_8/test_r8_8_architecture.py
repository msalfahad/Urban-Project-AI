"""R8.8 addendum: architecture review. Authored gaps of 0.5 / 1 / 2 / 5 mm, the band edges, the independent GEOS
cross-check (agree, curve not applicable, grid-phase robustness, injected TS01 defects) and the isolation of
legacy project rules from the generic topology."""

from __future__ import annotations

import inspect
import math
import re
from pathlib import Path

import pytest

from engine.source import room_topology as RT, topology as T, topology_crosscheck as XC, topology_policy as TP
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]
MM = 1.0                                       # these fixtures are drawn in millimetres: eps_r = 1.0 unit exactly


def run(parts, texts=()):
    return RT.run(H.inp(parts, texts=texts, unit=MM), frame_insert=None)


def two_rooms_mm(gap_mm):
    """Two 5000 x 4000 mm rooms; the partition at x = 5000 stops `gap_mm` short of the top wall."""
    return [H.seg(100, 0, 0, 10000, 0), H.seg(101, 10000, 0, 10000, 4000), H.seg(102, 10000, 4000, 0, 4000),
            H.seg(103, 0, 4000, 0, 0), H.seg(104, 5000, 0, 5000, 4000 - gap_mm)]


def corner_gap_room_mm(gap_mm):
    """One 5000 x 4000 mm room whose right wall stops `gap_mm` short of the top wall (the gap opens outside)."""
    return [H.seg(100, 0, 0, 5000, 0), H.seg(101, 5000, 0, 5000, 4000 - gap_mm), H.seg(102, 5000, 4000, 0, 4000),
            H.seg(103, 0, 4000, 0, 0)]


LABELS = [H.text(5, "A", 2500, 2000), H.text(6, "B", 7500, 2000)]


@pytest.mark.parametrize("gap_mm", [0.5, 1.0, 2.0, 5.0])
def test_authored_gap_between_two_rooms(gap_mm):
    r = run(two_rooms_mm(gap_mm), LABELS)
    assert r["tolerances"]["eps_r"] == 1.0
    if gap_mm <= 1.0:          # inside the ambiguous band (closed end at eps_r): never a silent room either way
        assert r["sites"] and all(T.TOLERANCE_SENSITIVE in s["issues"] for s in r["sites"])
        assert all(s["status"] == T.REVIEW_REQUIRED for s in r["sites"])
    else:                      # authored: a real opening; one space with two labels, explicitly
        assert len(r["sites"]) == 1 and r["sites"][0]["issues"] == [T.MULTIPLE_SEMANTIC_LABELS]
        assert not [f for f in r["findings"] if f["code"] == T.SITE_ONLY_IN_AUTHORED_BUILD]


@pytest.mark.parametrize("gap_mm", [0.5, 1.0, 2.0, 5.0])
def test_authored_gap_to_the_outside(gap_mm):
    r = run(corner_gap_room_mm(gap_mm), [H.text(5, "A", 2500, 2000)])
    assert not [s for s in r["sites"] if s["status"] == T.CERTIFIED]           # never a measured room
    only_r = [f for f in r["findings"] if f["code"] == T.SITE_ONLY_IN_AUTHORED_BUILD]
    assert [f["code"] for f in r["findings"] if f["code"] == "LABEL_OUTSIDE_EVERY_SITE"] == ["LABEL_OUTSIDE_EVERY_SITE"]
    if gap_mm <= 1.0:          # the room exists only if the band is closed: stated, not silently absent
        assert len(only_r) == 1 and abs(only_r[0]["area"] - 5000 * 4000) <= 1.0 * 18000   # eps_r x perimeter
    else:
        assert only_r == []


def test_band_edges_match_the_builds():
    e_n, e_r = 1e-6, 1.0
    assert TP.band(e_n, e_n, e_r) == TP.NOISE
    assert TP.band(math.nextafter(e_n, 1), e_n, e_r) == TP.AMBIGUOUS
    assert TP.band(e_r, e_n, e_r) == TP.AMBIGUOUS                               # merged by the eps_r build (<=)
    assert TP.band(math.nextafter(e_r, 2), e_n, e_r) == TP.AUTHORED


def test_the_frozen_policy_numbers_are_unchanged_by_the_addendum():
    import json
    rec = TP.record()
    assert rec["digest"] == json.load(open(ROOT / "tests/r8_8/registers/TOPOLOGY_TOLERANCE_POLICY.json"))["digest"]
    assert (TP.NOISE_RELATIVE, TP.AUTHORED_PRECISION_MM, TP.JAMB_ALLOWANCE_RATIO) == (2.0 ** -30, 1.0, 0.25)


# ---------------------------------------------------------------- independent GEOS cross-check
def test_crosscheck_agrees_on_straight_sites_with_provenance():
    r = run(two_rooms_mm(0.0), LABELS)
    assert r["crosscheck"]["state"] == XC.AGREES and r["crosscheck"]["counts"][XC.AGREES] == 2
    assert all(s["crosscheck"] == XC.AGREES and s["status"] == T.CERTIFIED for s in r["sites"])
    assert r["crosscheck"]["geos"]["geos"]


def test_crosscheck_never_flattens_a_curve():
    parts = [H.seg(1, 0, 0, 4000, 0), H.seg(2, 4000, 0, 4000, 3000), H.seg(3, 0, 3000, 0, 0),
             H.part(4, "ARC", (2000, 3000, 2000, 0.0, math.pi))]               # a semicircular top wall
    r = run(parts, [H.text(5, "A", 2000, 1500)])
    (s,) = r["sites"]
    assert s["crosscheck"] == XC.NOT_APPLICABLE_CURVE and s["status"] == T.CERTIFIED
    assert abs(s["area"] - (4000 * 3000 + math.pi * 2000 ** 2 / 2)) < 1e-6      # TS01's exact arc area stands
    src = inspect.getsource(XC)
    for flatten in ("segmentize", "interpolate(", "linspace", "quad_segs"):
        assert flatten not in src


def test_crosscheck_is_robust_to_grid_lines_through_route_noise():
    # two end points 1 ULP apart with a phase-0 rounding boundary of the eps_n grid between them: phase 0
    # snaps them one cell apart (the right room leaks); another phase keeps them together
    e_n = run(two_rooms_mm(0.0), LABELS)["tolerances"]["eps_n"]
    line = (math.floor(5000.0 / e_n) + 0.5) * e_n                              # set_precision rounds at k + 1/2
    a, b = math.nextafter(line, 0), math.nextafter(line, 1e9)
    parts = [H.seg(100, 0, 0, a, 0), H.seg(105, b, 0, 10000, 0), H.seg(101, 10000, 0, 10000, 4000),
             H.seg(102, 10000, 4000, 0, 4000), H.seg(103, 0, 4000, 0, 0), H.seg(104, a, 0, a, 4000)]
    r = run(parts, LABELS)
    assert all(s["status"] == T.CERTIFIED for s in r["sites"]) and len(r["sites"]) == 2
    # SUPERSEDED by R8.9 §19 (cross-check V2): an answer that depends on the grid origin is reported as
    # PHASE_SENSITIVE_INCONCLUSIVE, never as agreement; TS01's own certificate still decides (sites CERTIFIED)
    assert r["crosscheck"]["state"] == XC.PHASE_SENSITIVE_INCONCLUSIVE
    assert XC.PHASE_SENSITIVE_INCONCLUSIVE in {s["crosscheck"] for s in r["sites"]}


def _mutating(monkeypatch, mutate):
    real = T.analyse

    def wrapped(*a, **kw):
        res = real(*a, **kw)
        mutate(res)
        return res
    monkeypatch.setattr(T, "analyse", wrapped)


def test_crosscheck_catches_a_wrong_ts01_area(monkeypatch):
    def grow(res):
        s = max(res["sites"], key=lambda z: z["area"])
        s["area"] *= 1.01
    _mutating(monkeypatch, grow)
    r = run(two_rooms_mm(0.0), LABELS)
    bad = [s for s in r["sites"] if s["crosscheck"] == XC.DISAGREES]
    assert len(bad) == 1 and bad[0]["status"] == T.REVIEW_REQUIRED and XC.GEOS_CROSSCHECK_DISAGREES in bad[0]["issues"]
    assert all("area" in why for why in r["crosscheck"]["disagreements"][bad[0]["site_id"]]["reasons"])


def test_crosscheck_catches_a_wrong_boundary_provenance(monkeypatch):
    def drop(res):
        s = res["sites"][0]
        s["boundary_source_ids"] = s["boundary_source_ids"][1:]
    _mutating(monkeypatch, drop)
    r = run(two_rooms_mm(0.0), LABELS)
    bad = [s for s in r["sites"] if s["crosscheck"] == XC.DISAGREES]
    assert len(bad) == 1 and bad[0]["status"] == T.REVIEW_REQUIRED
    assert all("provenance" in why for why in r["crosscheck"]["disagreements"][bad[0]["site_id"]]["reasons"])


def test_crosscheck_unavailable_is_recorded_not_assumed(monkeypatch):
    monkeypatch.setattr(XC, "_geos", lambda: None)
    r = run(two_rooms_mm(0.0), LABELS)
    assert r["crosscheck"]["state"] == XC.UNAVAILABLE and all(s["crosscheck"] == XC.UNAVAILABLE for s in r["sites"])


# ---------------------------------------------------------------- legacy rules stay out of the generic topology
GENERIC = ["topology.py", "topology_policy.py", "topology_crosscheck.py", "room_topology.py", "geometry_role.py",
           "region_membership.py"]


def test_no_legacy_project_rule_reaches_the_generic_topology():
    for name in GENERIC:
        src = (ROOT / "engine/source" / name).read_text()
        code = "\n".join(l.split("#")[0] for l in src.splitlines())
        # room-function words decide nothing in topology (labels are attributes; rows live in the lab)
        for word in ("BATH", "PAINTRY", "PANTRY", "KITCHEN", "BED.ROOM", "HALL", "QORTUBA", "P7757", "RASHED"):
            assert not re.search(rf"['\"]{re.escape(word)}['\"]", code), (name, word)
        # no legacy module is imported, so no legacy threshold can leak in
        for legacy in ("wall_solid", "free_space", "planar_faces", "floor_regions", "snap_tolerance"):
            assert not re.search(rf"import .*{legacy}|from .*{legacy}", code), (name, legacy)
        # no raster, no grid snap as authority, no area / width threshold for room roles
        for tok in ("ndimage", "CELL_MM", "NODE_SNAP_GRID", "MIN_ROOM_AREA", "MAX_SHAFT_AREA", "MIN_HABITABLE", "600"):
            assert tok not in code, (name, tok)


# ---------------------------------------------------------------- the noise / authored separation is measured
def test_separation_is_measured_per_drawing_not_assumed():
    r = run(two_rooms_mm(0.0), LABELS)
    assert r["separation"]["separated"] and r["separation"]["near_eps_n"] == 0
    e_n = r["tolerances"]["eps_n"]
    parts = two_rooms_mm(0.0)
    parts[4] = H.seg(104, 5000, 0, 5000, 4000 - e_n / 4)                      # merged, but near the eps_n cliff
    r2 = run(parts, LABELS)
    assert r2["separation"]["near_eps_n"] == 1 and not r2["separation"]["separated"]
    assert [f for f in r2["findings"] if f["code"] == T.NOISE_NEAR_EPS_N]
    assert all(s["status"] == T.CERTIFIED for s in r2["sites"])               # stated, the topology is unchanged
