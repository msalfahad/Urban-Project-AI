"""Phase 2B-7 acceptance (written before the engine change): ARCH_TAKEOFF_V2.7 keeps a curved wall curved - the
room polygon follows the arc (chords of sagitta <= 1 mm, vertices on the arc), the waterproofing boundary types the
arc as WALL (V2.6: an OPEN edge, a false 3.0 m termination), and a curved wall band joins the wall run on its
centreline with all three bases published. Truth from the B10 coordinates (bench_cases B10): inner face r 2.50 m,
outer face r 2.70 m about (2.2, 1.7), the inner sweep 2 asin(0.6)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402

T = F.B10


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_arcs")


@pytest.fixture(scope="module")
def b10(work):
    return R.run(F.arc_room(work / "B10.dxf"), work / "o_b10", facts=True)


def test_room_polygon_follows_the_arc(b10):
    """area and perimeter were exact already (13.021882 m2, 14.217506 m); the polygon now is too: its shoelace area
    within 0.003 m2 of the exact area (the flattening bound (2/3) x 1 mm x the 3.22 m arc), every vertex of the arc
    side at r 2.50 m from the centre (1e-6), every chord's sagitta <= 1 mm. V2.6: one chord, shoelace 12.00 m2."""
    r = R.room(b10, "Bathroom")[0]
    assert abs(r["area_m2"] - T["area_m2"]) < 1e-6 and abs(r["perimeter_lm"] - T["perimeter_m"]) < 1e-6
    poly = r["polygon_m"]
    assert abs(R.shoelace(poly) - T["area_m2"]) < 0.003
    # the arc side: x >= 4.2 m (the west corners (0.2, 0.2) and (0.2, 3.2) are 2.5 m from the centre too)
    on_arc = [p for p in poly if abs(math.dist(p, (2.2, 1.7)) - 2.5) < 1e-6 and p[0] >= 4.2 - 1e-6]
    assert len(on_arc) >= 3
    for p, q in zip(on_arc, on_arc[1:]):
        c = math.dist(p, q)
        assert 2.5 - math.sqrt(2.5 ** 2 - (c / 2) ** 2) <= 0.001 + 1e-9


def test_waterproofing_types_the_arc_as_wall(b10):
    """the bathroom's upturn boundary: the arc 2.5 x 2 asin(0.6) = 3.217506 m is WALL with the three straight walls
    (10.20 m); the door is the only break (the single door block is a DOOR in V2.7). No OPEN edge, no termination of
    kind OTHER (V2.6: WALL 10.20 + OTHER 3.00 and a false 3.00 m termination)."""
    up = [ln for ln in R.lines(b10) if ln["item_code"] == "FIN.WP.WALL_UPTURN"]
    assert len(up) == 1
    by = up[0]["calculation"]["inputs"]["by_role_lm"]
    assert "OTHER" not in by
    assert abs(by["WALL"] - (10.2 + T["arc_inner_m"])) < 1e-3
    assert abs(up[0]["measured_net"] - (T["perimeter_m"] - 0.8) * 0.2) < 1e-3
    assert not [ln for ln in R.lines(b10) if ln["item_code"] == "FIN.WP.TERMINATION" and
                ln["calculation"]["inputs"].get("kind") == "OTHER"]


def test_curved_wall_band(b10):
    """the east wall is two concentric wall arcs 0.20 m apart over the inner arc's sweep: one curved band, the run
    on its centreline r 2.60 m: 2.6 x 1.287002 = 3.346206 m (MIN_RADIUS_ARC 3.217506, MAX_RADIUS_ARC 3.474906
    published), strip sweep x (2.7^2 - 2.5^2) / 2 = 0.669241 m2 = run x t. The straight walls are unchanged."""
    walls = R.load(b10, "ARCH_WALLS.json")
    w = [x for fl in walls["floors"] for x in fl["walls"]] if "floors" in walls else \
        [x for fl in walls["walls"] for x in fl["walls"]]
    cv = [x for x in w if x.get("curved")]
    assert len(cv) == 1
    c = cv[0]
    assert abs(c["t_m"] - 0.2) < 1e-6
    assert abs(c["gross_lm"] - T["arc_mid_m"]) < 1e-6 and abs(c["net_lm"] - T["arc_mid_m"]) < 1e-6
    assert abs(c["curved"]["bases_lm"]["MIN_RADIUS_ARC"] - T["arc_inner_m"]) < 1e-6
    assert abs(c["curved"]["bases_lm"]["MAX_RADIUS_ARC"] - T["arc_outer_m"]) < 1e-6
    assert c["curved"]["basis"] == "MID_BAND_ARC"
    assert abs(c["strip_m2"] - T["strip_m2"]) < 1e-6 and abs(c["strip_m2"] - c["net_lm"] * 0.2) < 1e-6
    straight = sum(x["net_lm"] for x in w if not x.get("curved"))
    assert abs(R.net(b10, "ARCH.WALL_RUN") - (straight + T["arc_mid_m"])) < 1e-6


def test_curved_band_against_v26(work, b10):
    """V2.6 left the curved band out of the run: the difference is exactly the curved run (no other wall moves)."""
    a = R.run(work / "B10.dxf", work / "o_b10_26", facts=True, method=R.V26)
    assert abs(R.net(b10, "ARCH.WALL_RUN") - R.net(a, "ARCH.WALL_RUN") - T["arc_mid_m"]) < 1e-6


@pytest.mark.parametrize("kind", ["rot30", "mirror", "metres", "translate", "nest"])
def test_arc_room_invariant(work, b10, kind):
    out = R.run(F.variant(work / "B10.dxf", work / f"B10_{kind}.dxf", kind), work / f"o_b10_{kind}", facts=True)
    assert R.invariant(b10, out, tol=1e-5), R.diff(b10, out, 1e-5)
