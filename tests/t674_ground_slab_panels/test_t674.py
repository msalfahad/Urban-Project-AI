"""T-674: a ground-slab panel is bounded only by drawn geometry (R-T674-1 .. 4). Villa V674 (hand fixture, not the
development villa), metres, slab T = 0.10 printed.

(1) Corner bay 4.00 x 3.00 between two carrier beam faces x = 0 (west) and y = 0 (south). An oblique ground beam
    0.25 wide crosses the corner at 45 deg: face A x + y = 0.80, face B x + y = 0.80 + 0.25 sqrt2 = 1.153553; face B is
    drafted 0.10 m short of the south carrier. Strip to the carriers = (kB^2 - kA^2) / 2 = (1.330686 - 0.64) / 2 =
    0.345343 m2 (= square-cut band 0.80 sqrt2 x 0.25 = 0.282843 + two end triangles 0.25^2 / 2 = 0.0625). The corner
    triangle beyond face A is a slab panel 0.80^2 / 2 = 0.320 m2. Bay panel = 12.000 - 0.320 - 0.345343 = 11.334657 m2
    -> 1.133466 m3.
(2) Curved beam inner face: arc centre (10, 5), r = 2.00, a straight beam y = 3.85 .. 4.15 (0.30) from x = 5 ends ON
    the arc. The panels south (y 2 .. 3.85) and north (y 4.15 .. 7) of it are two panels with the strip between them;
    an arc flattened to 64 chords without noding merges panel + strip + panel into one false face.
(3) Junction box next to a drawn pit wall: drawn panel 2.00 m2, engine cell 1.90 m2 (the box took 0.10 m2 beyond the
    wall face) -> 2.00 m2.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t674"))
import t674_rules as R  # noqa: E402

S2 = math.sqrt(2.0)
KA, KB = 0.80, 0.80 + 0.25 * S2


def _corner(rot_deg=0.0, mirror=False, scale=1.0):
    """the V674 corner geometry, optionally rotated / mirrored / in other units: (faceA, faceB, west, south)."""
    th = math.radians(rot_deg)

    def T(p):
        x, y = p
        if mirror:
            x = -x
        x, y = x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th)
        return (x * scale, y * scale)
    face_a = (T((0.0, KA)), T((KA, 0.0)))
    face_b = (T((0.0, KB)), T((KB - 0.10, 0.10)))                 # drafted 0.10 m short of the south carrier
    west = (T((0.0, 0.0)), T((0.0, 3.0)))
    south = (T((0.0, 0.0)), T((4.0, 0.0)))
    return face_a, face_b, west, south


# ---------------- R-T674-1 normal

def test_strip_to_carriers_hand_figure():
    _, a = R.strip_to_carriers(*_corner())
    assert a == pytest.approx(0.345343, abs=1e-6)
    assert a == pytest.approx(0.80 * S2 * 0.25 + 2 * 0.25 ** 2 / 2, abs=1e-6)


def test_bay_panel_and_volume():
    _, strip = R.strip_to_carriers(*_corner())
    panel = 12.0 - KA ** 2 / 2 - strip
    assert panel == pytest.approx(11.334657, abs=1e-6)
    assert R.volume(panel, 0.10) == pytest.approx(1.133466, abs=1e-6)


@pytest.mark.parametrize("rot,mirror", [(30.0, False), (0.0, True), (117.0, True)])
def test_strip_invariant_under_rotation_and_mirror(rot, mirror):
    _, a = R.strip_to_carriers(*_corner(rot, mirror))
    assert a == pytest.approx(0.345343, abs=1e-6)


def test_units_millimetres_converted_not_guessed():
    fa, fb, w, s = _corner(scale=1000.0)
    m = lambda seg: tuple(R.to_m([p], 0.001)[0] for p in seg)       # noqa: E731
    _, a = R.strip_to_carriers(m(fa), m(fb), m(w), m(s))
    assert a == pytest.approx(0.345343, abs=1e-6)
    with pytest.raises(R.RefusedT674):
        R.to_m([(1.0, 1.0)], 0.0254)


def test_short_face_is_a_drafting_gap_not_the_member_end():
    fa, fb, w, s = _corner()
    assert R.face_gap(fb[1], s) == pytest.approx(0.10, abs=1e-9)
    # the strip is defined by the face LINES and the carriers: the short face does not shorten it
    _, a = R.strip_to_carriers(fa, fb, w, s)
    assert a == pytest.approx(0.345343, abs=1e-6)


def test_deduction_of_drawn_band_accepted():
    assert R.deduction_basis([{"member": "OB1", "kind": "BAND", "area_m2": 0.282843,
                               "drawn_faces": ["A", "B"]}]) == pytest.approx(0.282843)


# ---------------- R-T674-1 adverse

def test_deduction_with_no_drawn_member_refused():
    with pytest.raises(R.RefusedT674):
        R.deduction_basis([{"member": "X", "kind": "BAND", "area_m2": 0.2367, "drawn_faces": ["A"]}])
    with pytest.raises(R.RefusedT674):
        R.deduction_basis([{"member": "Y", "kind": "COLUMN", "area_m2": 0.25, "drawn_faces": []}])
    with pytest.raises(R.RefusedT674):
        R.deduction_basis([{"member": "Z", "kind": "BAND", "area_m2": None, "drawn_faces": ["A", "B"]}])


def test_non_parallel_faces_refused():
    fa, _, w, s = _corner()
    with pytest.raises(R.RefusedT674):
        R.strip_to_carriers(fa, ((0.0, 1.2), (1.0, 0.0)), w, s)


# ---------------- R-T674-2 normal and adverse

def _court_lines():
    c, r = (10.0, 5.0), 2.0
    xs = 10.0 - math.sqrt(r * r - 1.15 ** 2)   # y = 3.85 meets the arc
    xn = 10.0 - math.sqrt(r * r - 0.85 ** 2)   # y = 4.15 meets the arc
    return c, r, (xs, 3.85), (xn, 4.15)


def test_line_end_on_true_arc_is_a_node():
    c, r, ps, pn = _court_lines()
    assert R.node_on_arc(ps, c, r) and R.node_on_arc(pn, c, r)
    assert not R.node_on_arc((ps[0] - 0.002, ps[1]), c, r)          # 2 mm off the arc: not a node


def test_polygonisation_with_and_without_arc_nodes():
    shapely = pytest.importorskip("shapely")
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    c, r, ps, pn = _court_lines()
    frame = [((5.0, 2.0), (5.0, 7.0)), ((5.0, 7.0), (10.0, 7.0)), ((5.0, 2.0), (10.0, 2.0))]
    beam = [((5.0, 3.85), ps), ((5.0, 4.15), pn)]
    a0, a1 = 90.0, 270.0                                            # the west half circle, from (10, 7) to (10, 3)
    tail = [((10.0, 3.0), (10.0, 2.0))]

    def faces(noded):
        pts, nd = R.arc_points(c, r, a0, a1, 64, [ps, pn] if noded else [])
        g = [LineString(s) for s in frame + beam + tail] + [LineString(pts)]
        return sorted(round(f.area, 4) for f in polygonize(unary_union(g)) if f.area > 1e-6), nd
    merged, _ = faces(False)
    split, nd = faces(True)
    assert len(nd) == 2
    assert len(split) == len(merged) + 2                            # panel + strip + panel instead of one face
    assert sum(split) == pytest.approx(sum(merged), abs=5e-3)       # noding moves no area (chord flattening only)
    smallest = min(split)
    n = 20000                                                       # strip = integral of (x_arc(y) - 5) dy, 3.85 .. 4.15
    hand = sum((10.0 - math.sqrt(r * r - (3.85 + 0.30 * (i + 0.5) / n - 5.0) ** 2) - 5.0) * 0.30 / n for i in range(n))
    assert smallest == pytest.approx(hand, abs=1e-3)                # ~0.981 m2
    v = R.split_basis([x for x in split if x != smallest], max(merged), True, smallest)
    assert v["verdict"] == "ENGINE_RIGHT"


def test_split_on_undrawn_line_refused():
    with pytest.raises(R.RefusedT674):
        R.split_basis([6.0, 3.0], 9.0, split_drawn=False)
    with pytest.raises(R.RefusedT674):
        R.split_basis([6.0, None], 9.0, split_drawn=True)


def test_split_residual_named_when_not_closing():
    v = R.split_basis([6.0, 3.0], 9.75, True, 0.30)
    assert v["verdict"] == "UNRESOLVED" and v["residual_m2"] == pytest.approx(0.45)


# ---------------- R-T674-3 / -4

def test_junction_box_returns_area_beyond_drawn_support():
    c = R.junction_clip(2.00, 1.90, support_drawn=True)
    assert c["corrected_m2"] == pytest.approx(2.00) and c["returned_m2"] == pytest.approx(0.10)


def test_junction_box_without_drawn_support_stands_and_is_reported():
    c = R.junction_clip(2.00, 1.90, support_drawn=False)
    assert c["corrected_m2"] == pytest.approx(1.90) and c["lost_m2_reported"] == pytest.approx(0.10)


def test_junction_engine_larger_than_drawn_refused():
    with pytest.raises(R.RefusedT674):
        R.junction_clip(1.90, 2.00, support_drawn=True)


def test_missing_never_zero():
    with pytest.raises(R.RefusedT674):
        R.volume(2.0, None)
    with pytest.raises(R.RefusedT674):
        R.volume(None, 0.10)
    with pytest.raises(R.RefusedT674):
        R.volume(2.0, 10.0)                                         # 10 (cm) typed as metres
