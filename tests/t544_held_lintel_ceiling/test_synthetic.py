"""R-T544-1 on a synthetic villa (not the development villa).

Fixture K544 (metres, band along x, wall t 0.20, faces y = +-0.10):
  RC column across the band x 0.30 .. 0.70; window W-A jambs x 1.50 / 2.70 (w 1.20); the band runs into a cross wall
  whose far face is x 4.20 (end of masonry). Lintel D 0.20 (B = 0.20 = host t), head NOT established (HELD).
  START a = 1.50 - 0.70 = 0.800 (COLUMN); END a = 4.20 - 2.70 = 1.500 (END_OF_MASONRY)
  L_ceil = 1.20 + 0.800 + 1.500 = 3.500 m -> face [0, 0.20 x 3.500] = [0, 0.700] m2.
  Host 0.20 white, net 20.000 m2, glue 4.5 kg/m2: base [19.300, 20.000] m2 -> glue [86.850, 90.000] kg.
  The T-453 'max' D x (w + 0.80) = 0.400 m2 is a LOWER bound of a built lintel: as a ceiling -> refused.
Shared pier: two 0.60 m windows on one host separated by a 0.875 m pier, outer ends 0.725 / 1.012 (column faces) ->
joint span 3.812 m, the pier once; individually 2.200 + 2.487 = 4.687 m (the pier twice: not buildable).
Long run: END 4.300 m to a column -> the merged 3.0 m search stops (SEARCH_LIMIT); the extended search reads 4.300.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t544", "agents_t527", "agents_t519", "agents_t537"):
    sys.path.insert(0, str(ROOT / "research" / p))
import held_lintel_ceiling as H  # noqa: E402
import lintel_bearing_v2 as V2  # noqa: E402
import lintel_bearing_v3 as V3  # noqa: E402
import r_t498_2 as R  # noqa: E402

HALF = 0.10


def rect(x0, x1, h=HALF):
    return Polygon([(x0, -h), (x1, -h), (x1, h), (x0, h)])


def k544(transform=lambda g: g):
    col = transform(rect(0.30, 0.70, 0.20))
    win = transform(rect(1.50, 2.70, HALF + 0.01))
    M = transform(rect(0.0, 4.20)).difference(unary_union([win, col]))
    return M, [col], [("W-A", win)]


def ends_k544(transform=lambda g: g, a=(0.0, 0.0), u=(1.0, 0.0)):
    M, cols, gaps = k544(transform)
    out = {}
    for side, jamb, sign in (("START", 1.50, -1), ("END", 2.70, +1)):
        e, capped, stop, sid = V3.reach_v3(M, a, u[0], u[1], jamb, sign, HALF, cols, gaps, [])
        out[side] = {"side": side, "a_m": e, "stopper": stop, "basis": "MEASURED", "capped": capped}
    return out


def test_k544_hand_ceilings():
    e = ends_k544()
    assert e["START"]["stopper"] == "COLUMN" and abs(e["START"]["a_m"] - 0.80) < 2e-5
    assert e["END"]["stopper"] == "END_OF_MASONRY" and abs(e["END"]["a_m"] - 1.50) < 2e-5
    f = H.held_face("W-A", [0.20, 0.20], 1.20, list(e.values()), 0.20)
    assert f["ceilings_m"] == {"START": 0.800, "END": 1.500} and f["L_ceil_m"] == 3.500
    assert f["face_m2"] == [0.0, 0.7] and not f["open"]


def test_k544_host_material_range():
    f = H.held_face("W-A", [0.20, 0.20], 1.20, list(ends_k544().values()), 0.20)
    base = R.material_base(20.0, [f])
    glue = R.material_line(base, 4.5, "kg")
    assert base["state"] == "RANGE" and base["base_m2"] == [19.3, 20.0]
    assert glue["state"] == "BOUNDED_EXPOSURE" and glue["range"] == [86.85, 90.0]


@pytest.mark.parametrize("deg", [30.0, 117.0, -45.0])
def test_rotation_invariant(deg):
    tr = lambda g: rotate(g, deg, origin=(0, 0), use_radians=False)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    e = ends_k544(tr, u=(c, s))
    assert abs(e["START"]["a_m"] - 0.80) < 3e-5 and abs(e["END"]["a_m"] - 1.50) < 3e-5
    assert (e["START"]["stopper"], e["END"]["stopper"]) == ("COLUMN", "END_OF_MASONRY")


def test_mirror_invariant():
    tr = lambda g: scale(g, xfact=-1.0, yfact=1.0, origin=(0, 0))
    M, cols, gaps = k544(tr)
    e1, _c, s1, _ = V3.reach_v3(M, (0.0, 0.0), -1.0, 0.0, 1.50, -1, HALF, cols, gaps, [])
    e2, _c, s2, _ = V3.reach_v3(M, (0.0, 0.0), -1.0, 0.0, 2.70, +1, HALF, cols, gaps, [])
    assert abs(e1 - 0.80) < 2e-5 and abs(e2 - 1.50) < 2e-5 and (s1, s2) == ("COLUMN", "END_OF_MASONRY")


def test_ceiling_rounds_up_to_the_mm():
    assert H.ceil_mm(0.4933) == 0.494 and H.ceil_mm(1.2322) == 1.233 and H.ceil_mm(4.2188) == 4.219
    assert H.ceil_mm(0.725000) == 0.725 and H.ceil_mm(0.875) == 0.875
    assert H.ceil_mm(0.7249999) == 0.725          # a float hair below the mm is that mm, never one below


def test_min_bearing_figure_refused_as_ceiling():
    e = ends_k544()
    e["END"] = {"side": "END", "a_m": 0.40, "stopper": "COLUMN", "basis": "MIN_BEARING"}
    with pytest.raises(R.RuleError):
        H.held_face("W-A", [0.20, 0.20], 1.20, list(e.values()), 0.20)
    # and the T-453 legacy 'max' D x (w + 0.80) stays OPEN under R-T498-2 (never a ceiling)
    f = R.lintel_face({"opening_id": "W-A", "state": "HELD_FACE", "face_max_m2": 0.40,
                       "face_max_basis": "MIN_BEARING_LENGTH"}, 0.20)
    assert f["open"] and f["face_m2"] == [0.0, None]


def test_search_limit_end_opens_the_face_and_holds_the_material():
    M = rect(0.0, 9.0).difference(unary_union([rect(1.50, 2.70, 0.11), rect(7.00, 7.40, 0.20)]))
    cols = [rect(7.00, 7.40, 0.20)]
    e, capped, stop, _ = V3.reach_v3(M, (0, 0), 1, 0, 2.70, +1, HALF, cols, [], [])
    assert capped and stop == "SEARCH_LIMIT" and e == 3.0
    ends = [{"side": "START", "a_m": 0.80, "stopper": "COLUMN", "basis": "MEASURED"},
            {"side": "END", "a_m": e, "stopper": stop, "basis": "MEASURED"}]
    f = H.held_face("W-A", [0.20, 0.20], 1.20, ends, 0.20)
    assert f["open"] and f["face_m2"] == [0.0, None]
    g = R.material_line(R.material_base(20.0, [f]), 4.5, "kg")
    assert g["state"] == "HELD" and g["value"] is None and g["at_most_beside"] == 90.0     # never 0
    # extended search (R-T544-1 (1)): the same reach to 20 m reads the column at 4.300
    e2, capped2 = V2.reach(M, (0, 0), 1, 0, 2.70, +1, HALF, search=20.0)
    assert not capped2 and abs(e2 - 4.30) < 2e-5
    ends[1] = {"side": "END", "a_m": e2, "stopper": "COLUMN", "basis": "MEASURED"}
    f2 = H.held_face("W-A", [0.20, 0.20], 1.20, ends, 0.20)
    assert f2["L_ceil_m"] == 6.3 and f2["face_m2"] == [0.0, 1.26]


def test_joint_pier_counted_once():
    out = lambda a, stop="COLUMN": {"side": "X", "a_m": a, "stopper": stop, "basis": "MEASURED"}
    m1 = {"opening_id": "W-B", "D_m": 0.20, "w_gap_m": 0.60, "face_lo_m2": 0.0,
          "outer": dict(out(0.7249999), side="START"), "pier_m": 0.875}
    m2 = {"opening_id": "W-C", "D_m": 0.20, "w_gap_m": 0.60, "face_lo_m2": 0.0, "outer": dict(out(1.011731), side="END")}
    j = H.joint_face([m1, m2], {"W-B": "H1", "W-C": "H1"})
    assert list(j) == ["W-B+W-C"] and j["W-B+W-C"]["L_ceil_m"] == 3.812
    assert j["W-B+W-C"]["face_m2"] == [0.0, 0.7624]
    indiv = (0.725 + 0.60 + 0.875) + (0.875 + 0.60 + 1.012)
    assert abs(indiv - 4.687) < 1e-9 and indiv - 3.812 == pytest.approx(0.875)


def test_pair_on_two_hosts_opens_both():
    m1 = {"opening_id": "W-B", "D_m": 0.20, "w_gap_m": 0.60, "face_lo_m2": 0.0,
          "outer": {"side": "START", "a_m": 0.7, "stopper": "COLUMN", "basis": "MEASURED"}, "pier_m": 0.875}
    m2 = {"opening_id": "W-C", "D_m": 0.20, "w_gap_m": 0.60, "face_lo_m2": 0.0,
          "outer": {"side": "END", "a_m": 1.0, "stopper": "COLUMN", "basis": "MEASURED"}}
    j = H.joint_face([m1, m2], {"W-B": "H1", "W-C": "H2"})
    assert set(j) == {"W-B", "W-C"} and all(v["open"] and v["face_m2"] == [0.0, None] for v in j.values())


def test_partial_depth_and_bad_units_refused_or_open():
    e = list(ends_k544().values())
    assert H.held_face("W-A", [0.15, 0.20], 1.20, e, 0.20)["open"]
    with pytest.raises(R.RuleError):
        H.held_face("W-A", [0.20, 200.0], 1.20, e, 0.20)          # millimetres
    with pytest.raises(R.RuleError):
        H.held_face("W-A", [0.20, 0.20], -1.20, e, 0.20)          # negative
    with pytest.raises(R.RuleError):
        H.held_face("W-A", [0.20, 0.20], 1.20, e[:1], 0.20)       # one end missing
    bad = dict(e[0], a_m=None)
    with pytest.raises(R.RuleError):
        H.held_face("W-A", [0.20, 0.20], 1.20, [bad, e[1]], 0.20)  # missing reach is never 0


def test_held_face_never_zero_hi():
    f = H.held_face("W-A", [0.20, 0.20], 1.20, list(ends_k544().values()), 0.20)
    assert f["face_m2"][1] > 0 and f["face_m2"][0] == 0.0
