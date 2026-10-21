"""Phase 2A P2-01 / P2-01b / P2-02 (ARCH_TAKEOFF_V2.1): the robust predicate at the three reviewed band-path sites,
the AT_THRESHOLD / UNDECIDABLE records, the mean-axis face lines, the equivalence of the frozen geometry with the
legacy path, and the metamorphic suite. Synthetic only (round 2 acceptance tests AT-Q1-01 .. 05, 08)."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine.source import arch_plan as AP                      # noqa: E402
from engine.source import lintel_measure as LM                 # noqa: E402
from engine.source import opening_census as OC                 # noqa: E402
from engine.source import robust_geometry as RG                # noqa: E402

import p2a_helpers as H                                         # noqa: E402

UNITS = {"mm": 1e-3, "cm": 1e-2, "m": 1.0, "in": 0.0254}
KEEP = (0.0, 1e-9, 1e-6, 1e-3)
DROP = (-1e-2, -1e-3, -1e-4, -1e-5, -2e-6)
rng = random.Random(20261013)
ROTS = (0.0, 90.0, 30.0, 45.0) + tuple(rng.uniform(0.0, 360.0) for _ in range(6))


def _place(rot, at_mm, k):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return lambda x, y: ((x * c - y * s) * k + at_mm[0] * k, (x * s + y * c) * k + at_mm[1] * k)


def _site(kind, unit_m, rot, at_mm, delta, depth=1, geom=None):
    """True when the drafted T + delta (mm) is kept at the site."""
    k = 1e-3 / unit_m
    g = geom or RG.Geometry(unit_m)
    P = _place(rot, at_mm, k)
    if kind == "PIECE":
        segs = [("P", P(0, 0), P(100 + delta, 0), depth)]
        fl = g.face_lines(segs, ang_res_deg=0.5, off_tol=2 * k, join_tol=5 * k, min_len=100 * k)
        return any("P" in ids for ln in fl for *_x, ids in ln["cover"])
    if kind == "OVERLAP":
        segs = [("A", P(0, 0), P(1000, 0), depth), ("B", P(700 - delta, 200), P(1700, 200), depth)]
    else:
        segs = [("A1", P(0, 0), P(1000, 0), depth), ("A2", P(1500 + delta, 0), P(3000, 0), depth),
                ("B1", P(0, 200), P(1000, 200), depth), ("B2", P(1500 + delta, 200), P(3000, 200), depth)]
    bands, mg = g.bands([{"id": s[0], "a": s[1], "b": s[2], "path": ["x"] * depth, "layer": "W"} for s in segs])
    if kind == "OVERLAP":
        return bool(bands)
    return any(g.band_gaps(b, min_gap=0.5 / unit_m, mg=mg, jamb_tol=0.03 / unit_m, merge_tol=1e-3 / unit_m)
               for b in bands)                       # the unit-relative merge of V2 / V2.1


@pytest.mark.parametrize("kind", ["PIECE", "OVERLAP", "GAP"])
@pytest.mark.parametrize("unit", list(UNITS))
def test_boundary_sweep_keeps_every_drafted_value_and_drops_every_short_one(kind, unit):
    """AT-Q1-01: delta >= 0 kept in 100 % of placements, delta <= -2e-6 mm dropped in 100 % (offsets <= 1e7 mm)."""
    unit_m = UNITS[unit]
    bad = []
    for rot in ROTS:
        for off in (0.0, 1e5, 1e6, 1e7):
            at = (off + 123.456, -off + 789.012)
            for depth in (1, 3):
                for d in KEEP:
                    if not _site(kind, unit_m, rot, at, d, depth):
                        bad.append(("dropped", rot, off, depth, d))
                for d in DROP:
                    if _site(kind, unit_m, rot, at, d, depth):
                        bad.append(("kept", rot, off, depth, d))
    assert not bad, bad[:10]


def test_frozen_strict_comparison_loses_drafted_exact_values_the_robust_one_keeps():
    """the defect the margin fixes (round 2 Q1): the frozen strict comparison drops some delta = 0 placements."""
    lost = sum(not _site("PIECE", 1.0, rot, (off, off), 0.0, geom=RG.Geometry.frozen(1.0))
               for rot in ROTS for off in (0.0, 1e5, 1e6))
    kept = sum(_site("PIECE", 1.0, rot, (off, off), 0.0) for rot in ROTS for off in (0.0, 1e5, 1e6))
    assert lost > 0 and kept == len(ROTS) * 3


def test_at_threshold_records_count_exactly_the_seeded_near_threshold_values():
    """AT-Q1-02: one record per value within the margin; none for values farther away."""
    g = RG.Geometry(1e-3)
    segs = [(f"E{i}", (0.0, 1000.0 * i), (100.0, 1000.0 * i)) for i in range(3)] + \
           [(f"N{i}", (0.0, 5000.0 + 1000.0 * i), (100.0 + 5e-7, 5000.0 + 1000.0 * i)) for i in range(2)] + \
           [(f"F{i}", (0.0, 9000.0 + 1000.0 * i), (100.5, 9000.0 + 1000.0 * i)) for i in range(4)] + \
           [("S", (0.0, 20000.0), (99.99, 20000.0))]
    g.face_lines(segs, off_tol=2.0, join_tol=5.0, min_len=100.0)
    recs = g.decisions()
    assert sorted(r["ids"][0] for r in recs) == ["E0", "E1", "E2", "N0", "N1"]
    assert all(r["site"] == "FACE_PIECE" and r["state"] == RG.AT_THRESHOLD and r["decision"] == "KEPT" for r in recs)
    assert all(abs(r["delta_mm"]) <= r["margin_mm"] for r in recs)


def test_overlap_and_gap_sites_write_their_records():
    g = RG.Geometry(1e-3)
    for kind in ("OVERLAP", "GAP"):
        assert _site(kind, 1e-3, 0.0, (0.0, 0.0), 0.0, geom=g)
    sites = {r["site"] for r in g.decisions()}
    assert {"BAND_OVERLAP", "OPENING_GAP"} <= sites


def test_large_coordinates_widen_the_band_and_beyond_1e_3_mm_the_decision_is_undecidable():
    """AT-Q1-03: at 3.3e9 mm delta >= 0 is kept and a PRECISION_WIDENED review names the band; where the float bound
    exceeds 1e-3 mm the recorded decision is UNDECIDABLE (kept, with a REVIEW finding), never silent."""
    for kind in ("PIECE", "OVERLAP", "GAP"):
        g = RG.Geometry(1e-3)
        assert _site(kind, 1e-3, 30.0, (3.3e9, 3.3e9), 0.0, geom=g)
        w = [f for f in g.findings if f["code"] == "PRECISION_WIDENED"]
        assert w and w[0]["band_mm"] > RG.EPS_ABS_MM and not w[0]["undecidable"]
    g = RG.Geometry(1e-3)
    assert _site("PIECE", 1e-3, 0.0, (3e11, 3e11), 0.0, geom=g)
    recs = g.decisions()
    assert recs and all(r["state"] == RG.UNDECIDABLE for r in recs)
    assert any(f["code"] == "UNDECIDABLE_THRESHOLD" and f["level"] == "REVIEW" for f in g.findings)


def _measured(kind, rot, off):
    """the measured value (mm) of a drafted-exact site at an arbitrary angle, or None when it is not found."""
    unit_m, k = 1e-3, 1.0
    g = RG.Geometry(unit_m)
    P = _place(rot, (off, off), k)
    if kind == "PIECE":
        fl = g.face_lines([("P", P(0, 0), P(100, 0))], off_tol=2.0, join_tol=5.0, min_len=100.0)
        return (fl[0]["hi"] - fl[0]["lo"]) if fl else None
    if kind == "OVERLAP":
        segs = [("A", P(0, 0), P(1000, 0)), ("B", P(700, 200), P(1700, 200))]
        bands, _ = g.bands([{"id": s[0], "a": s[1], "b": s[2], "layer": "W"} for s in segs])
        return (bands[0]["hi"] - bands[0]["lo"]) if bands else None
    segs = [("A1", P(0, 0), P(1000, 0)), ("A2", P(1500, 0), P(3000, 0)),
            ("B1", P(0, 200), P(1000, 200)), ("B2", P(1500, 200), P(3000, 200))]
    bands, mg = g.bands([{"id": s[0], "a": s[1], "b": s[2], "layer": "W"} for s in segs])
    gaps = [x for b in bands for x in g.band_gaps(b, min_gap=500.0, mg=mg, jamb_tol=30.0)]
    return gaps[0]["width"] if gaps else None


@pytest.mark.parametrize("kind,T", [("PIECE", 100.0), ("OVERLAP", 300.0), ("GAP", 500.0)])
def test_mean_axis_finds_every_site_at_arbitrary_angles_with_its_drafted_value(kind, T):
    """AT-Q1-04: 100 % found; |measured - drafted| <= 1e-6 mm at offsets <= 1e6 mm and <= 1e-5 mm at 3.3e9 mm."""
    r = random.Random(4)
    for off, tol in ((0.0, 1e-6), (1e6, 1e-6), (3.3e9, 1e-5)):
        for _ in range(60):
            v = _measured(kind, r.uniform(0.0, 360.0), off)
            assert v is not None and abs(v - T) <= tol, (kind, off, v)


def test_the_frozen_bin_axis_loses_gaps_at_arbitrary_angles():
    """finding F-3 reproduced: the frozen 0.5-degree bin axis loses a drafted 500 mm gap at off-grid angles."""
    r = random.Random(4)
    found = 0
    for _ in range(60):
        rot = r.uniform(0.0, 360.0)
        g = RG.Geometry.frozen(1e-3)
        P = _place(rot, (0.0, 0.0), 1.0)
        segs = [("A1", P(0, 0), P(1000, 0)), ("A2", P(1500, 0), P(3000, 0)),
                ("B1", P(0, 200), P(1000, 200)), ("B2", P(1500, 200), P(3000, 200))]
        bands, _ = g.bands([{"id": s[0], "a": s[1], "b": s[2], "layer": "W"} for s in segs])
        found += any(g.band_gaps(b, min_gap=500.0, jamb_tol=30.0) for b in bands)
    assert found < 30


def test_mean_axis_keeps_the_bin_half_plane():
    """near 0 / 180 degrees the mean direction never flips against the bin's own axis."""
    for ang in (0.1, 179.9, 179.76, 0.24, 90.1, 89.9):
        th = math.radians(ang)
        segs = [("A", (0.0, 0.0), (1000 * math.cos(th), 1000 * math.sin(th)))]
        ln = RG.face_lines_mean_axis(segs, ang_res_deg=0.5, off_tol=2.0, join_tol=5.0, min_len=100.0)[0]
        uk, _ = OC.frame_of(ln["ang"])
        assert ln["u"][0] * uk[0] + ln["u"][1] * uk[1] > 0
        assert abs((ln["hi"] - ln["lo"]) - 1000.0) <= 1e-9


# ------------------------------------------------------------------ equivalence with the frozen legacy path
@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    return H.villa_regions(tmp_path_factory.mktemp("villa"))


@pytest.mark.parametrize("tol", ["LEGACY", "UNIT_RELATIVE"])
def test_frozen_geometry_reproduces_lintel_measure_openings_and_layer_roles(villa, tol):
    regs, u = villa
    for floor, ents in regs.items():
        for f, sc in ((lambda p: p, 1.0), (H.rot(37.37), 1.0), (lambda p: (p[0] * 1e-3, p[1] * 1e-3), 1e-3)):
            e = H.transform(ents, f, scale=sc)
            um = u / sc
            L0 = AP.layer_roles(e, um, tol=tol)
            assert AP.layer_roles(e, um, tol=tol, geom=RG.Geometry.frozen(um)) == L0
            walls = sorted(l for l, r in L0["roles"].items() if r == AP.WALL)
            ref = LM.openings(e["segments"], um, walls, (), tol=tol)
            assert RG.openings(e["segments"], um, walls, (), tol=tol, geom=RG.Geometry.frozen(um)) == ref


def test_v2_1_equals_v2_on_the_drafted_exact_villa(villa):
    regs, u = villa
    for ents in regs.values():
        assert H.fingerprint(H.run(ents, u, "V2")[0]) == H.fingerprint(H.run(ents, u, "V2.1")[0])


# ------------------------------------------------------------------ metamorphic suite (P2-02, AT-Q1-05)
CASES = {
    "translate_1e5": (lambda p: (p[0] + 1e5, p[1] - 1e5), 1.0, False),
    "translate_1e6": (lambda p: (p[0] - 1e6, p[1] + 1e6), 1.0, False),
    "translate_1e7": (lambda p: (p[0] + 1e7, p[1] + 1e7), 1.0, False),
    "rotate_90": (H.rot(90.0), 1.0, False),
    "rotate_30": (H.rot(30.0), 1.0, False),
    "rotate_37_37": (H.rot(37.37), 1.0, False),
    "rotate_random_far": (H.rot(random.Random(9).uniform(0.0, 360.0), (3e5, -2e5)), 1.0, False),
    "mirror": (lambda p: (-p[0], p[1]), 1.0, True),
    "mm_to_m": (lambda p: (p[0] * 1e-3, p[1] * 1e-3), 1e-3, False),
}
ROTATED = ("rotate_30", "rotate_37_37", "rotate_random_far")


@pytest.mark.parametrize("case", list(CASES))
def test_v2_1_openings_are_invariant(villa, case):
    regs, u = villa
    f, sc, mir = CASES[case]
    for floor, ents in regs.items():
        base = H.fingerprint(H.run(ents, u, "V2.1")[0])
        got = H.fingerprint(H.run(H.transform(ents, f, scale=sc, mirror=mir), u / sc, "V2.1")[0])
        assert H.same({"openings": base["openings"], "spaces": [], "doors": base["doors"]},
                      {"openings": got["openings"], "spaces": [], "doors": got["doors"]}), (floor, case)


@pytest.mark.parametrize("case", [c for c in CASES if c not in ROTATED])
def test_v2_1_rooms_and_quantities_are_invariant(villa, case):
    regs, u = villa
    f, sc, mir = CASES[case]
    for floor, ents in regs.items():
        base = H.fingerprint(H.run(ents, u, "V2.1")[0])
        got = H.fingerprint(H.run(H.transform(ents, f, scale=sc, mirror=mir), u / sc, "V2.1")[0])
        assert H.same(base, got), (floor, case)


@pytest.mark.parametrize("case", ROTATED)
def test_v2_1_rooms_are_invariant_at_any_angle_on_a_plan_without_columns(villa, case):
    regs, u = villa
    f, sc, mir = CASES[case]
    ents = regs["1F"]
    assert H.same(H.fingerprint(H.run(ents, u, "V2.1")[0]),
                  H.fingerprint(H.run(H.transform(ents, f, scale=sc, mirror=mir), u, "V2.1")[0]))


@pytest.mark.xfail(strict=True, reason="finding F-9: column outlines are found as axis-aligned rectangles only "
                                       "(DM.closed_rectangles); a rotated plan loses its columns - outside P2-01")
def test_rotated_columns_are_found():
    regs, u = H.villa_regions(Path(__import__("tempfile").mkdtemp()))
    ents = regs["GF"]
    S0, _ = H.run(ents, u, "V2.1")
    S1, _ = H.run(H.transform(ents, H.rot(37.37)), u, "V2.1")
    assert S1["columns"] == S0["columns"]


def test_v2_1_fixes_an_arbitrary_rotation_that_v2_gets_wrong(villa):
    """the reason for P2-01b: on the plan without columns V2 changes under a 37.37 degree rotation, V2.1 does not."""
    regs, u = villa
    ents, e2 = regs["1F"], H.transform(regs["1F"], H.rot(37.37))
    assert not H.same(H.fingerprint(H.run(ents, u, "V2")[0]), H.fingerprint(H.run(e2, u, "V2")[0]))
    assert H.same(H.fingerprint(H.run(ents, u, "V2.1")[0]), H.fingerprint(H.run(e2, u, "V2.1")[0]))


def test_threshold_census_lists_the_three_reviewed_sites_only_as_robust():
    c = RG.threshold_census()
    robust = {(r["function"], r["site"]) for r in c if r["decision"] == "ROBUST_MARGIN"}
    assert {s for _f, s in robust} == set(RG.SITES)
    assert all(r["decision"].startswith("UNCHANGED") for r in c if r["site"] not in RG.SITES)


def test_robust_geometry_is_stdlib_only_and_never_edits_the_frozen_census():
    import ast
    src = Path(RG.__file__).read_text(encoding="utf-8")
    mods = {n.module for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom)} | \
           {a.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}
    assert mods <= {"__future__", "math", "collections", "engine.source"}
