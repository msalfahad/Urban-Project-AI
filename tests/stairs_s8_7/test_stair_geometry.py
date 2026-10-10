"""engine/source/stair_geometry.py - synthetic known answers and an independent shapely construction (no project
data)."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import stair_geometry as SG

shapely = pytest.importorskip("shapely")
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402


def envelope_area(n, r, g, t, bottom=None, top=None):
    """the same solid built another way: the stepped top surface, cut by half-planes (waist soffit, landing soffits)."""
    run, slope, drop = (n - 1) * g, r / g, t * math.hypot(g, r) / g
    top_pts = ([(-bottom[0], 0)] if bottom else []) + [(0, 0)]
    for i in range(n - 1):
        top_pts += [(i * g, (i + 1) * r), ((i + 1) * g, (i + 1) * r)]
    if top:
        top_pts += [(run, n * r), (run + top[0], n * r)]
    T = Polygon(top_pts + [(top_pts[-1][0], -1e5), (top_pts[0][0], -1e5)])
    H = Polygon([(-1e5, -slope * 1e5 - drop), (1e5, slope * 1e5 - drop), (1e5, 1e6), (-1e5, 1e6)])
    A = H
    if bottom:
        A = A.intersection(box(-1e5, -bottom[1], 1e5, 1e6))
    if top:
        A = A.union(box(-1e5, n * r - top[1], 1e5, 1e6))
    return T.intersection(A).area


# ------------------------------------------------------------------ straight flights
def test_riser_going_arithmetic():
    f = SG.straight_flight(12, 2000 / 12, 300, 1200, 160)
    assert f["run"] == 3300 and abs(f["rise"] - 2000) < 1e-9
    assert f["PLAN_PROJECTED_AREA"] == 3300 * 1200
    assert abs(f["FINISHING_TREAD_AREA"] - 11 * 300 * 1200) < 1e-6
    assert abs(f["FINISHING_RISER_AREA"] - 12 * 2000 / 12 * 1200) < 1e-6
    assert abs(f["HANDRAIL_PATH_LENGTH"] - math.hypot(3300, 11 * 2000 / 12)) < 1e-9
    assert SG.riser_height(4500, 27) == pytest.approx(166.6666667)
    assert SG.blondel(175, 280) == 630
    assert SG.inclined_length(3000, 4000) == 5000


def test_sloping_waist_between_plumb_cuts():
    """no landings: the soffit runs from the first to the last riser line; its length is run / cos(pitch)."""
    n, r, g, t = 10, 170.0, 290.0, 150.0
    f = SG.straight_flight(n, r, g, 1000, t)
    run = (n - 1) * g
    assert abs(f["inclined_waist_length"] - run * math.hypot(g, r) / g) < 1e-6
    # monolithic steps: n - 1 step triangles (g x r / 2) above the root line, and the waist parallelogram below it
    # (run x the vertical depth t / cos(pitch))
    waist = run * t * math.hypot(g, r) / g
    steps = (n - 1) * g * r / 2
    assert abs(f["profile_area"] - (waist + steps)) < 1e-6
    assert abs(f["profile_area"] - envelope_area(n, r, g, t)) < 1e-6


@pytest.mark.parametrize("seed", range(4))
def test_flight_matches_an_independent_construction(seed):
    rnd = random.Random(seed)
    k = 0
    while k < 60:
        n = rnd.randint(3, 18)
        r, g, t = rnd.uniform(140, 200), rnd.uniform(250, 320), rnd.uniform(100, 220)
        b = (rnd.uniform(300, 1500), rnd.uniform(100, 250)) if rnd.random() < 0.6 else None
        tp = (rnd.uniform(300, 1500), rnd.uniform(100, 250)) if rnd.random() < 0.6 else None
        try:
            f = SG.straight_flight(n, r, g, 1000, t, bottom=b, top=tp)
        except SG.StairGeometryError:
            continue
        k += 1
        assert abs(f["profile_area"] - envelope_area(n, r, g, t, b, tp)) <= 1e-6 * f["profile_area"]
        assert Polygon(f["outline"]).is_valid


def test_flight_landing_union_has_no_double_prism():
    """the waist and a landing share the wedge under the kink once: less than the sum of the separate prisms."""
    n, r, g, t, L, tl = 12, 2000 / 12, 300.0, 160.0, 1200.0, 160.0
    alone = SG.straight_flight(n, r, g, 1, t)["profile_area"]
    joined = SG.straight_flight(n, r, g, 1, t, bottom=(L, tl))["profile_area"]
    plate = L * tl
    assert joined < alone + plate
    assert abs(joined - envelope_area(n, r, g, t, (L, tl))) < 1e-6
    s_bot, _ = SG.straight_flight(n, r, g, 1, t, bottom=(L, tl))["soffit_turning_points"]
    assert s_bot > 0          # the soffits meet under the first step: the plate stays a full rectangle


def test_multi_flight_with_a_half_landing_counts_the_landing_once():
    """unfolded section of a dog-leg: flight 1, the half-landing, flight 2. The two flights' outlines share the plate;
    their union (shapely) equals flight 1 + flight 2 - one plate."""
    from shapely import affinity
    n1, n2, r, g, t, L = 13, 12, 166.6667, 300.0, 160.0, 1200.0
    f1 = SG.straight_flight(n1, r, g, 1, t, top=(L, t))
    f2 = SG.straight_flight(n2, r, g, 1, t, bottom=(L, t))
    P1 = Polygon(f1["outline"])
    P2 = affinity.translate(Polygon(f2["outline"]), xoff=f1["run"] + L, yoff=f1["rise"])
    plate = L * t
    assert abs(P1.intersection(P2).area - plate) < 1e-6
    assert abs(unary_union([P1, P2]).area - (f1["profile_area"] + f2["profile_area"] - plate)) < 1e-6


def test_landing_beam_intersection_taken_out_once():
    f = SG.straight_flight(8, 175, 280, 1, 150, top=(1000, 160))
    beam = (f["run"] + 800, f["rise"] - 400, f["run"] + 1000, f["rise"])      # landing beam at the landing end
    net, cut = SG.profile_area_outside(f["outline"], [beam])
    P = Polygon(f["outline"])
    assert abs(cut - P.intersection(box(*beam)).area) < 1e-6
    assert abs(net - P.difference(box(*beam)).area) < 1e-6
    with pytest.raises(SG.StairGeometryError):
        SG.profile_area_outside(f["outline"], [beam, beam])


def test_landing_with_a_void():
    outer = [(0, 0), (2500, 0), (2500, 1200), (0, 1200)]
    void = [(1000, 300), (1600, 300), (1600, 900), (1000, 900)]
    assert SG.polygon_area(outer) - SG.polygon_area(void) == pytest.approx(
        Polygon(outer, [void]).area)


def test_winder_kites_tile_the_quarter():
    c = (0.0, 0.0)
    corner = [(-1300.0, 0.0), (-1300.0, 1150.0), (0.0, 1150.0)]
    kites = [[c, (-1300.0, 0.0), (-1300.0, 511.0)], [c, (-1300.0, 511.0), (-1300.0, 1150.0)],
             [c, (-1300.0, 1150.0), (-662.0, 1150.0)], [c, (-662.0, 1150.0), (0.0, 1150.0)]]
    assert sum(SG.polygon_area(k) for k in kites) == pytest.approx(SG.polygon_area([c] + corner))


def test_invalid_flights_are_refused():
    with pytest.raises(SG.StairGeometryError):
        SG.straight_flight(1, 170, 300, 1000, 150)
    with pytest.raises(SG.StairGeometryError):
        SG.straight_flight(10, 170, 300, 1000, 0)
    with pytest.raises(SG.StairGeometryError):
        SG.straight_flight(10, 170, 300, 1000, 150, bottom=(0, 150))


# ------------------------------------------------------------------ curved flights
def test_annular_flight_plan_and_helicoid():
    f = SG.annular_flight(1500, 2750, math.radians(90), 12, 170, 2125)
    assert f["PLAN_PROJECTED_AREA"] == pytest.approx(math.pi / 4 * (2750 ** 2 - 1500 ** 2))
    assert f["walking_line_length"] == pytest.approx(math.pi / 2 * 2125)
    flat = SG.annular_flight(1500, 2750, math.radians(90), 2, 1e-6)["HELICOID_SOFFIT_AREA"]
    assert flat == pytest.approx(math.pi / 4 * (2750 ** 2 - 1500 ** 2), rel=1e-6)
    # numerical surface of the helicoid z = c * theta between the two radii
    c = 12 * 170 / math.radians(90)
    steps = 4000
    num = sum(math.radians(90) * math.sqrt(rho * rho + c * c) * (1250 / steps)
              for rho in (1500 + (k + 0.5) * 1250 / steps for k in range(steps)))
    assert f["HELICOID_SOFFIT_AREA"] == pytest.approx(num, rel=1e-6)
    with pytest.raises(SG.StairGeometryError):
        SG.annular_flight(2000, 1500, 1.0, 10, 170)


# ------------------------------------------------------------------ bars
def test_rate_integration():
    assert SG.rate_density_length(8, 1200, 1200) == pytest.approx(11.52)
    assert SG.rate_count(8, 1200) == 10 and SG.rate_count(5, 1000) == 5
    # two directions over one plate: twice the equivalent length, never the same bar twice
    assert 2 * SG.rate_density_length(8, 1200, 1200) == pytest.approx(23.04)
    assert 16 ** 2 / 162 == pytest.approx(1.580246914)


# ------------------------------------------------------------------ plan evidence
def test_tread_runs_and_distractors():
    treads = [(f"T{i}", (0.0, 1000.0 + 300 * i), (1150.0, 1000.0 + 300 * i)) for i in range(12)]
    wall = [("W1", (0.0, 5000.0), (1150.0, 5000.0)), ("W2", (0.0, 5200.0), (1150.0, 5200.0))]
    other = [(f"V{i}", (3000.0 + 300 * i, 0.0), (3000.0 + 300 * i, 2800.0)) for i in range(5)]
    short = [("S1", (0.0, 9000.0), (400.0, 9000.0)), ("S2", (0.0, 9300.0), (400.0, 9300.0))]
    runs = SG.detect_tread_runs(treads + wall + other + short, min_lines=3)
    got = sorted((r["angle"], r["count"]) for r in runs)
    assert got == [(0.0, 12), (90.0, 5)]
    assert all(abs(p - 300) < 1e-9 for r in runs for p in r["pitches"])


def test_fan_centre_of_radial_treads():
    c = (500.0, -200.0)
    segs = [(f"R{k}", (c[0] + 1500 * math.cos(a), c[1] + 1500 * math.sin(a)),
             (c[0] + 2700 * math.cos(a), c[1] + 2700 * math.sin(a))) for k, a in enumerate((0.3, 0.6, 0.9, 1.3))]
    (x, y), miss = SG.fan_centre(segs)
    assert abs(x - c[0]) < 1e-6 and abs(y - c[1]) < 1e-6 and miss < 1e-6


def test_tiling_has_no_double_count():
    """a dog-leg bay: two flights, a winder quadrant and a half-landing tile the bay with no overlap."""
    bay = box(0, 0, 2500, 4300)
    parts = [box(0, 0, 1200, 3150), box(1300, 0, 2500, 3100),
             Polygon([(0, 3150), (1200, 3150), (1200, 3100), (1300, 3100), (1300, 4300), (0, 4300)]),
             box(1300, 3100, 2500, 4300), box(1200, 0, 1300, 3100)]
    assert abs(sum(p.area for p in parts) - bay.area) < 1e-6
    assert abs(unary_union(parts).area - bay.area) < 1e-6
