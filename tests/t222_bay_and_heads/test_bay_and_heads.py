"""T-222: curved-bay ends and leafless-opening heads (research/agents_t222/bay_and_heads.py). Villa T222-F, NOT
Alsenan. Hand truth (metres):

F1  Arc band only: centre (0, 0), faces r 1.90 / 2.10 (t 0.20, r_mid 2.00); full caps at 150 and 210 deg, the glazing
    sector between them through 180 deg (60 deg = pi / 3: glazing on the mid circle 2.00 x pi / 3 = 2.094395 m).
    Window = the wedge 120 .. 240 deg. Masonry = the two 30 deg ends: each (pi / 6) x (2.10^2 - 1.90^2) / 2 =
    0.209440 m2 -> 0.209440 / 0.20 = 1.047198 m (= r_mid x pi / 6). Zones: y > 0 under a member, h 3.00; elsewhere a
    slab, h 4.00 -> gross = (0.209440 x 3.00 + 0.209440 x 4.00) / 0.20 = 7.330383 m2.
F2  L corner of two straight 0.20 bands (as T-215 F1): A x -1.90 .. 0.20, y 0 .. 0.20; B x 0 .. 0.20, y -1.40 ..
    0.20; drawn masonry 2.10 x 0.20 + 0.20 x 1.60 - 0.04 = 0.700 m2; most-central split = the mitre:
    A 0.400 m2 (2.000 m), B 0.300 m2 (1.500 m).
F3  Stem against a through arc: the stem's band reaches the arc's face; a point in both bands goes to the through
    arc (the stem stops on its face).
F4  Leafless opening 1.20 wide, 0.20 lintel; levels above its own floor: head 2.50, member soffit 4.90 ->
    1.20 x (4.90 - 2.70) = 2.640 m2. No head -> HELD (0 .. 1.20 x 4.70 = 5.640), never a value. Heads 2.10 .. 2.50
    (a CONFLICT) -> RANGE (2.640 .. 3.120).
F5  Views: a section looking at a wall 1.00 m behind the cut that carries a leafed door and a solid face over the
    whole range of an opening in a wall 3.25 m behind -> OCCLUDED (no evidence, no conflict); the same door drawn on
    the opening's own plane -> CONFLICT; a head line on the own plane -> HEAD.
"""
import math
import sys
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale, translate
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t222"))
import bay_and_heads as B  # noqa: E402

H = 0.0005


def pol(deg, r=2.10):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def wedge(a0, a1, R=5.0, n=400):
    return Polygon([(0, 0)] + [(R * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                                R * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)])


def f1():
    arc = B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10)
    glz, span = B.glazing_sector(arc, (pol(150, 1.90), pol(150, 2.10)), (pol(210, 1.90), pol(210, 2.10)),
                                 through=(-1.0, 0.0))
    return arc, glz, span


def test_f1_glazing_between_full_caps():
    arc, glz, span = f1()
    assert span == pytest.approx(math.pi / 3, abs=1e-9)
    assert arc.r_mid * span == pytest.approx(2.094395, abs=1e-6)
    assert glz.area == pytest.approx((math.pi / 3) * (2.10 ** 2 - 1.90 ** 2) / 2, rel=1e-4)


def test_f1_end_masonry_hand_truth_and_heights():
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    assert m.area == pytest.approx(2 * 0.209440, rel=2e-4)
    zones = [B.Zone("slab", box(-5, -5, 5, 5), 4.00), B.Zone("member", box(-5, 0, 5, 5), 3.00)]
    al = B.allocate(m, [arc], zones=zones, h=H)
    w = al.by_wall["BAY"]
    assert w["length_m"] == pytest.approx(2 * 1.047198, abs=0.003)
    assert w["gross_m2"] == pytest.approx(7.330383, abs=0.01)
    assert al.unassigned_m2 == pytest.approx(0.0, abs=1e-5)


def test_f1_mirror_and_rotation_invariant():
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    base = B.allocate(m, [arc], h=H).by_wall["BAY"]["length_m"]
    for ang in (90, 37):
        arc_r = B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10)
        mr = rotate(m, ang, origin=(0, 0))
        assert B.allocate(mr, [arc_r], h=H).by_wall["BAY"]["length_m"] == pytest.approx(base, abs=0.003)
    mm = scale(m, xfact=-1, origin=(0, 0))
    assert B.allocate(mm, [arc], h=H).by_wall["BAY"]["length_m"] == pytest.approx(base, abs=0.003)
    mt = translate(m, 3.0, -2.0)
    arc_t = B.ArcBand("BAY", (3.0, -2.0), 1.90, 2.10)
    assert B.allocate(mt, [arc_t], h=H).by_wall["BAY"]["length_m"] == pytest.approx(base, abs=0.003)


def test_partial_cap_is_a_frame_line_refused():
    arc = B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10)
    with pytest.raises(ValueError, match="frame line"):
        B.glazing_sector(arc, (pol(150, 1.98), pol(150, 2.10)), (pol(210, 1.90), pol(210, 2.10)))


def test_non_radial_cap_refused():
    arc = B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10)
    with pytest.raises(ValueError, match="not radial"):
        B.glazing_sector(arc, (pol(150, 1.90), pol(153, 2.10)), (pol(210, 1.90), pol(210, 2.10)))


def test_f2_l_corner_mitre_split():
    A = B.StraightBand("A", (0.20, 0.10), (-1.90, 0.10), 0.20, through=True)
    Bb = B.StraightBand("B", (0.10, 0.20), (0.10, -1.40), 0.20, through=True)
    m = box(-1.90, 0.0, 0.20, 0.20).union(box(0.0, -1.40, 0.20, 0.20))
    assert m.area == pytest.approx(0.700, abs=1e-9)
    al = B.allocate(m, [A, Bb], h=H)
    assert al.by_wall["A"]["length_m"] == pytest.approx(2.000, abs=0.005)
    assert al.by_wall["B"]["length_m"] == pytest.approx(1.500, abs=0.005)


def test_f3_stem_stops_on_the_through_arc():
    _, glz, _ = f1()
    arc = B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10, through=True)
    stem = B.StraightBand("STEM", (-3.0, -1.00), (-1.70, -1.00), 0.15)   # runs into the arc band from the left
    m = B.bay_masonry(arc, [], glz, wedge(200, 260), extra=[stem.polygon().difference(glz)])
    al = B.allocate(m, [arc, stem], h=H)
    # every point of the arc band stays the arc's: its share equals the arc-only share in the same window
    m_arc = B.bay_masonry(arc, [], glz, wedge(200, 260))
    alone = B.allocate(m_arc, [arc], h=H).by_wall["BAY"]["area_m2"]
    assert al.by_wall["BAY"]["area_m2"] == pytest.approx(alone, abs=1e-3)
    outside = stem.polygon().difference(glz).difference(arc.annulus()).intersection(wedge(200, 260)).area
    assert al.by_wall["STEM"]["area_m2"] == pytest.approx(outside, abs=1e-3)
    # adverse: without the through mark the most-central rule hands part of the arc's band to the stem
    loose = B.allocate(m, [B.ArcBand("BAY", (0.0, 0.0), 1.90, 2.10), stem], h=H)
    assert loose.by_wall["STEM"]["area_m2"] > al.by_wall["STEM"]["area_m2"] + 1e-3


def test_counted_strip_skipped_once():
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    counted = wedge(120, 135)
    al = B.allocate(m, [arc], counted=counted, h=H)
    piece = (math.pi / 12) * (2.10 ** 2 - 1.90 ** 2) / 2
    assert al.counted_skipped_m2 == pytest.approx(piece, abs=2e-4)
    assert al.by_wall["BAY"]["area_m2"] == pytest.approx(2 * 0.209440 - piece, abs=2e-4)


def test_masonry_in_no_band_is_held_not_dropped():
    arc, glz, _ = f1()
    stray = box(-1.0, -0.1, -0.8, 0.1)                       # inside the arc's inner face: in no band
    m = B.bay_masonry(arc, [], glz, wedge(120, 240), extra=[stray])
    al = B.allocate(m, [arc], h=H)
    assert al.status == "PARTLY_HELD"
    assert al.unassigned_m2 == pytest.approx(0.04, abs=2e-4)


def test_height_under_no_zone_is_held():
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    with pytest.raises(ValueError, match="HELD"):
        B.allocate(m, [arc], zones=[B.Zone("member", box(-5, 0, 5, 5), 3.00)], h=H)


def test_deepest_member_governs_where_zones_overlap():
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    zones = [B.Zone("slab", box(-5, -5, 5, 5), 4.00), B.Zone("deep", box(-5, -5, 5, 5), 3.00)]
    al = B.allocate(m, [arc], zones=zones, h=H)
    assert al.by_wall["BAY"]["gross_m2"] == pytest.approx(2 * 1.047198 * 3.00, abs=0.01)


def test_units_and_duplicates_refused():
    with pytest.raises(ValueError, match="metres"):
        B.StraightBand("A", (0, 0), (1000, 0), 200)
    with pytest.raises(ValueError, match="metres"):
        B.ArcBand("A", (0, 0), 1900, 2100)
    arc, glz, _ = f1()
    m = B.bay_masonry(arc, [], glz, wedge(120, 240))
    with pytest.raises(ValueError, match="twice"):
        B.allocate(m, [arc, B.ArcBand("BAY", (0, 0), 1.9, 2.1)], h=H)


def test_empty_masonry_is_held_never_zero():
    arc, glz, _ = f1()
    with pytest.raises(ValueError, match="HELD"):
        B.bay_masonry(arc, [], glz, wedge(170, 190))           # the window holds glazing only


# ----------------------------------------------------------------------------------------------- F4 / F5 heads

def test_f4_masonry_above_value_held_range():
    assert B.masonry_above(1.20, 4.90, head_level_m=2.50, lintel_depth_m=0.20) == ("VALUE", 2.640)
    st, b = B.masonry_above(1.20, 4.90, head_level_m=None, lintel_depth_m=0.20)
    assert st == "HELD" and b == (0.0, 5.64)               # a bound, never a value
    assert B.masonry_above(1.20, 4.90, head_range=(2.10, 2.50), lintel_depth_m=0.20) == ("RANGE", (2.64, 3.12))


def test_f4_occluding_soffit_refused_as_top():
    with pytest.raises(ValueError, match="occluding"):
        B.masonry_above(1.20, 4.55, head_level_m=2.50, lintel_depth_m=0.20, top_source_depth_m=0.0,
                        wall_depth_m=4.10)


def test_f5_nearer_wall_occludes_no_conflict():
    drawn = [B.Drawn("FACE", -3.0, 3.0, 1.00, ref="near wall"), B.Drawn("LEAFED_DOOR", 0.10, 1.00, 1.00, ref="D1")]
    kind, refs = B.view_evidence(0.0, 1.30, 3.25, drawn)
    assert kind == "OCCLUDED" and "D1" in refs


def test_f5_door_on_own_plane_is_conflict_never_a_value():
    drawn = [B.Drawn("LEAFED_DOOR", 0.10, 1.00, 3.25, ref="D1")]
    kind, refs = B.view_evidence(0.0, 1.30, 3.25, drawn)
    assert kind == "CONFLICT" and refs == ["D1"]


def test_f5_head_line_on_own_plane_and_partial_cover():
    assert B.view_evidence(0.0, 1.30, 3.25, [B.Drawn("HEAD_LINE", 0.0, 1.30, 3.26, level_m=2.40)]) == ("HEAD", 2.4)
    two = [B.Drawn("HEAD_LINE", 0.0, 0.6, 3.25, level_m=2.40), B.Drawn("HEAD_LINE", 0.6, 1.3, 3.25, level_m=2.60)]
    assert B.view_evidence(0.0, 1.30, 3.25, two)[0] == "CONFLICT"
    # a nearer door that covers only part of the opening and no face: the opening is NOT hidden, nor shown
    assert B.view_evidence(0.0, 1.30, 3.25, [B.Drawn("LEAFED_DOOR", 0.1, 0.5, 1.0)])[0] == "NOT_SHOWN"
