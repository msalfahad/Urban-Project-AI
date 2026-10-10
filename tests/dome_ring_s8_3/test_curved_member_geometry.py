"""Curved member geometry: synthetic known answers only, no project data.

Arcs turn counter-clockwise in world coordinates whatever their OCS or block transform; an end angle below the start
is a sweep across 0 degrees. Repeated or overlapping arcs on one circle are covered once. A band segment exists where
both edges are drawn. Disk / rectangle overlaps are exact. A spherical shell is the difference of two concentric caps
above one springing plane, and a drawn profile is only called spherical when it is circular and centred on its axis.
Every closed form is checked against an independent reference: ezdxf's own OCS and block explode, shapely, or a
numerical integral."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import curved_member_geometry as G


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# ------------------------------------------------------------------ arcs: direction, zero crossing, mirrors
@pytest.mark.parametrize("a0, a1, sweep", [(10, 100, 90), (334.094, 25.906, 51.812), (350, 10, 20), (270, 0, 90),
                                           (0.5, 0.25, 359.75), (-90, 0, 90)])
def test_sweep_is_ccw_and_crosses_zero(a0, a1, sweep):
    assert G.sweep_deg(a0, a1) == pytest.approx(sweep)
    arc = G.world_arc((0, 0), 2.0, a0, a1)
    assert 0 < arc["sweep"] < 360 and arc["start"] == pytest.approx(G.norm_deg(a0))


def test_equal_angles_are_not_a_circle_unless_stated():
    with pytest.raises(G.CurvedGeometryError):
        G.sweep_deg(45, 45)
    assert G.world_arc((0, 0), 1.0, full=True)["sweep"] == 360.0


def test_negative_extrusion_matches_ezdxf():
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new()
    msp = doc.modelspace()
    rnd = random.Random(7)
    for _ in range(25):
        c = (rnd.uniform(-50, 50), rnd.uniform(-50, 50))
        r, a0, a1 = rnd.uniform(0.5, 9), rnd.uniform(0, 360), rnd.uniform(0, 360)
        e = msp.add_arc(c, r, a0, a1, dxfattribs={"extrusion": (0, 0, -1)})
        w = G.world_arc(c, r, a0, a1, extrusion=(0, 0, -1))
        s_ref, e_ref = e.start_point, e.end_point                 # ezdxf world points (OCS -> WCS)
        ps, pe = G.arc_end_points(w)
        # the world arc runs CCW, so its start is the image of the OCS end and its end the image of the OCS start
        assert math.dist(ps, (e_ref.x, e_ref.y)) < 1e-6 and math.dist(pe, (s_ref.x, s_ref.y)) < 1e-6
        mid = math.radians(w["start"] + w["sweep"] / 2)
        ocs_mid = math.radians(a0 + G.sweep_deg(a0, a1) / 2)
        wc = e.ocs().to_wcs((c[0] + r * math.cos(ocs_mid), c[1] + r * math.sin(ocs_mid), 0))
        assert math.dist((w["c"][0] + r * math.cos(mid), w["c"][1] + r * math.sin(mid)), (wc.x, wc.y)) < 1e-6
    with pytest.raises(G.CurvedGeometryError):
        G.world_arc((0, 0), 1, 0, 90, extrusion=(0, 1, 0))


def test_mirrored_block_insert_matches_ezdxf_explode():
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new()
    blk = doc.blocks.new("A")
    blk.add_arc((3, 1), 2.0, 300, 40)                             # crosses 0 degrees inside the block
    msp = doc.modelspace()
    for xs, rot, at in ((-1, 0, (10, 5)), (1, 30, (0, 0)), (-1, 75, (-4, 2)), (2, 0, (1, 1))):
        ins = msp.add_blockref("A", at, dxfattribs={"xscale": xs, "yscale": abs(xs), "rotation": rot})
        (v,) = [x for x in ins.virtual_entities() if x.dxftype() == "ARC"]
        w_ref = G.world_arc((v.dxf.center.x, v.dxf.center.y), v.dxf.radius, v.dxf.start_angle, v.dxf.end_angle,
                            extrusion=tuple(v.dxf.extrusion))
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        m = (xs * ca, -abs(xs) * sa, xs * sa, abs(xs) * ca, at[0], at[1])
        w = G.transform_arc(G.world_arc((3, 1), 2.0, 300, 40), m)
        assert math.dist(w["c"], w_ref["c"]) < 1e-6 and w["r"] == pytest.approx(w_ref["r"])
        assert w["sweep"] == pytest.approx(w_ref["sweep"])
        gap = G.norm_deg(w["start"] - w_ref["start"])
        assert min(gap, 360.0 - gap) == pytest.approx(0, abs=1e-6)
        assert all(math.dist(p, q) < 1e-6 for p, q in zip(G.arc_end_points(w), G.arc_end_points(w_ref)))
    with pytest.raises(G.CurvedGeometryError):
        G.transform_arc(G.world_arc((0, 0), 1, 0, 90), (2, 0, 0, 1, 0, 0))     # non-uniform scale


def test_chord_versus_true_arc_length():
    q = G.world_arc((0, 0), 1.0, 0, 90)
    assert G.arc_length(q) == pytest.approx(math.pi / 2) and G.chord_length(q) == pytest.approx(math.sqrt(2))
    half = G.world_arc((0, 0), 3.0, 90, 270)
    assert G.chord_length(half) == pytest.approx(6.0) and G.arc_length(half) == pytest.approx(3 * math.pi)
    tiny = G.world_arc((0, 0), 5.0, 10, 10.5)
    assert G.chord_length(tiny) < G.arc_length(tiny) and G.chord_length(tiny) == pytest.approx(G.arc_length(tiny), rel=1e-5)


# ------------------------------------------------------------------ coverage: closed / partial, repeats, overlaps
def test_repeated_and_overlapping_arcs_are_covered_once():
    assert G.coverage_deg([(10, 30), (10, 30)]) == pytest.approx(30)             # a repeated outline
    assert G.coverage_deg([(0, 100), (50, 100)]) == pytest.approx(150)
    assert G.merge_intervals([(350, 20), (5, 10)]) == [(350.0, pytest.approx(25.0))]     # across 0 degrees
    assert G.is_closed([(0, 180), (180, 180)]) and G.is_closed([(300, 90), (30, 280)])
    assert not G.is_closed([(0, 90), (100, 250)]) and G.coverage_deg([(0, 90), (100, 250)]) == pytest.approx(340)


def test_band_segments_where_both_edges_are_drawn():
    inner = [G.world_arc((5, 5), 2.0, full=True)]
    outer = [G.world_arc((5, 5), 2.2, a, b) for a, b in ((20, 70), (110, 160), (200, 250), (290, 340))]
    segs = G.band_segments(inner, outer)
    assert [round(s["sweep"], 9) for s in segs] == [50.0] * 4
    s = segs[0]
    assert s["area"] == pytest.approx(math.radians(50) / 2 * (2.2 ** 2 - 2.0 ** 2))
    assert s["centreline_length"] == pytest.approx(2.1 * math.radians(50))
    assert s["chord_centreline"] < s["centreline_length"]
    # an inner edge broken across 0 degrees: the zero-crossing outer arc keeps its full overlap
    inner2 = [G.world_arc((0, 0), 2.0, 330, 30), G.world_arc((0, 0), 2.0, 60, 300)]
    outer2 = [G.world_arc((0, 0), 2.2, 340, 20)]
    assert [(round(a, 6), round(b, 6)) for a, b in ((x["start"], x["sweep"]) for x in G.band_segments(inner2, outer2))] == [(340.0, 40.0)]
    with pytest.raises(G.CurvedGeometryError):
        G.band_segments(inner, [G.world_arc((9, 9), 2.2, 0, 10)])                # not concentric


# ------------------------------------------------------------------ disk / rectangle overlaps
def _numeric_disk_rect(c, R, x0, y0, x1, y1, n=20000):
    lo, hi = max(x0, c[0] - R), min(x1, c[0] + R)
    if hi <= lo:
        return 0.0
    h = (hi - lo) / n
    tot = 0.0
    for i in range(n):
        x = lo + (i + 0.5) * h
        dy = math.sqrt(max(0.0, R * R - (x - c[0]) ** 2))
        tot += max(0.0, min(y1, c[1] + dy) - max(y0, c[1] - dy)) * h
    return tot


def test_disk_rect_area_known_answers():
    R = 2.0
    assert G.disk_rect_area((0, 0), R, G.axis_rect(-5, -5, 5, 5)) == pytest.approx(math.pi * R * R)
    assert G.disk_rect_area((0, 0), R, G.axis_rect(0, 0, 9, 9)) == pytest.approx(math.pi * R * R / 4)
    assert G.disk_rect_area((0, 0), R, G.axis_rect(-9, 1.2, 9, 9)) == pytest.approx(G.circle_segment_area(R, 1.2))
    assert G.disk_rect_area((0, 0), R, G.axis_rect(3, 3, 4, 4)) == 0.0
    assert G.circle_segment_area(R, 0) == pytest.approx(math.pi * R * R / 2)


def test_disk_rect_area_against_numeric_and_shapely():
    rnd = random.Random(11)
    shp = None
    try:
        from shapely.geometry import Point, box
        shp = (Point, box)
    except Exception:
        pass
    for _ in range(30):
        c, R = (rnd.uniform(-1, 1), rnd.uniform(-1, 1)), rnd.uniform(0.5, 3)
        x0, y0 = rnd.uniform(-3, 2), rnd.uniform(-3, 2)
        x1, y1 = x0 + rnd.uniform(0.1, 4), y0 + rnd.uniform(0.1, 4)
        exact = G.disk_rect_area(c, R, G.axis_rect(x0, y0, x1, y1))
        assert exact == pytest.approx(_numeric_disk_rect(c, R, x0, y0, x1, y1), abs=2e-6)
        if shp:
            ref = shp[0](c).buffer(R, quad_segs=2048).intersection(shp[1](x0, y0, x1, y1)).area
            assert exact == pytest.approx(ref, abs=1e-5 * R * R)


def test_rotated_rectangle_is_rotation_invariant():
    c, R = (0.3, -0.2), 1.7
    base = G.axis_rect(-0.4, 0.8, 2.5, 1.6)
    for deg in (0, 17, 90, 133, 271):
        t = math.radians(deg)
        u = (math.cos(t), math.sin(t))
        # rotate the disk centre with the frame: same relative geometry, same area
        cr = (c[0] * u[0] - c[1] * u[1], c[0] * u[1] + c[1] * u[0])
        rect = {"o": (0.0, 0.0), "u": u, "u0": base["u0"], "u1": base["u1"], "v0": base["v0"], "v1": base["v1"]}
        assert G.disk_rect_area(cr, R, rect) == pytest.approx(G.disk_rect_area(c, R, base))


def test_annulus_junction_with_a_tangent_straight_member():
    r1, r2 = 2.0, 2.2
    # a straight member whose inner face is tangent to the inner edge: the overlap is the outer cap beyond the face
    a = G.annulus_rect_area((0, 0), r1, r2, G.axis_rect(-5, r1, 5, r1 + 0.25))
    assert a == pytest.approx(G.circle_segment_area(r2, r1) - G.circle_segment_area(r2, r1 + 0.25))
    assert G.annulus_rect_area((0, 0), r1, r2, G.axis_rect(-5, -5, 5, 5)) == pytest.approx(math.pi * (r2 ** 2 - r1 ** 2))


# ------------------------------------------------------------------ spherical caps and shells
def test_cap_known_answers():
    R = 1.5
    assert G.cap_radius(2 * R, R) == pytest.approx(R)                            # hemisphere
    assert G.cap_volume(R, R) == pytest.approx(2 / 3 * math.pi * R ** 3) and G.cap_area(R, R) == pytest.approx(2 * math.pi * R * R)
    assert G.cap_volume(R, 2 * R) == pytest.approx(4 / 3 * math.pi * R ** 3)
    c, h = 4.0, 1.0
    Rc = G.cap_radius(c, h)
    assert math.sqrt(Rc ** 2 - (Rc - h) ** 2) == pytest.approx(c / 2)            # the chord is recovered


def _numeric_shell(r_out, h_out, t, n=200000):
    d = r_out - h_out
    r_in = r_out - t
    tot, dz = 0.0, h_out / n
    for i in range(n):
        z = d + (i + 0.5) * dz                     # height above the centre
        ro2 = max(0.0, r_out * r_out - z * z)
        ri2 = max(0.0, r_in * r_in - z * z)
        tot += math.pi * (ro2 - ri2) * dz
    return tot


@pytest.mark.parametrize("chord, rise, t", [(4.0, 1.5, 0.1), (4.4, 2.2, 0.1), (3.0, 0.6, 0.12), (4.0, 2.6, 0.15)])
def test_shell_between_caps_against_a_solid_of_revolution(chord, rise, t):
    R = G.cap_radius(chord, rise)
    s = G.shell_between_caps(R, rise, t)
    assert s["volume"] == pytest.approx(_numeric_shell(R, rise, t), rel=1e-6)
    assert s["springing_radius_out"] == pytest.approx(chord / 2)
    assert s["volume"] == pytest.approx(s["area_mid"] * t, rel=0.01)              # thin-shell check
    assert s["h_out"] - s["h_in"] == pytest.approx(t)
    with pytest.raises(G.CurvedGeometryError):
        G.shell_between_caps(R, rise, R + 1)


def test_a_flat_cap_needs_its_inner_surface_above_the_springing_plane():
    R = G.cap_radius(4.0, 0.05)
    with pytest.raises(G.CurvedGeometryError):
        G.shell_between_caps(R, 0.05, 0.1)


# ------------------------------------------------------------------ profiles
def test_profile_check_spherical_only_on_axis():
    R, cx, cy = 2.2, 10.0, -0.3
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(15, 166, 10)]
    assert G.profile_check(pts, 1e-6, axis_x=cx, axis_tol=1e-6)["state"] == "SPHERICAL_ABOUT_AXIS"
    assert G.profile_check(pts, 1e-6, axis_x=cx + 0.5, axis_tol=0.01)["state"] == "CIRCULAR"
    ell = [(cx + R * math.cos(math.radians(a)), cy + 0.7 * R * math.sin(math.radians(a))) for a in range(15, 166, 10)]
    assert G.profile_check(ell, 0.01, axis_x=cx, axis_tol=0.01)["state"] == "NOT_CIRCULAR"


def test_a_polyline_inscribed_in_a_circle_fits_it_exactly():
    R = 3.0
    pts = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in range(0, 181, 9)]
    c, r, res = G.circle_fit(pts)
    assert r == pytest.approx(R) and res < 1e-9 and math.dist(c, (0, 0)) < 1e-9


# ------------------------------------------------------------------ lengths at a spacing; concentric circles
def test_hoop_and_meridian_densities_both_equal_area_over_spacing():
    R, h = 2.0, 1.4
    d = R - h
    area = G.cap_area(R, h)
    # hoops at spacing s along the meridian (arc length), each a full circle of radius rho
    phi0 = math.acos(d / R)                       # half-angle of the cap from the axis
    n = 5000
    s = R * phi0 / n                              # the spacing divides the meridian exactly
    hoops = sum(2 * math.pi * R * math.sin((i + 0.5) * s / R) for i in range(n))
    assert hoops == pytest.approx(G.length_at_spacing(area, s), rel=1e-4)
    # meridians spaced s along each hoop: density 2 pi rho / s per unit meridian length
    mer = sum(2 * math.pi * R * math.sin((i + 0.5) * s / R) / s * s for i in range(n))
    assert mer == pytest.approx(hoops)
    with pytest.raises(G.CurvedGeometryError):
        G.length_at_spacing(1.0, 0)


def test_symmetric_offsets_cancel_in_a_total_circumference():
    t = G.concentric_circle_total(2.3, [-0.066, 0.0, 0.066])
    assert t["symmetric"] and t["total"] == pytest.approx(t["n_times_centreline"]) == pytest.approx(3 * 2 * math.pi * 2.3)
    u = G.concentric_circle_total(2.3, [-0.07, 0.0, 0.05])
    assert not u["symmetric"] and u["total"] != pytest.approx(u["n_times_centreline"])
