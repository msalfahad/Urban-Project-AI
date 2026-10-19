"""T-062 hand check of roof_trace.py on a synthetic plan (no private drawing; not Alsenan).

Hand truth (millimetres before the variant transform; layer names unlike any project):
  block   A-WALL shell 4.40 x 3.40 m (0.20 m walls), one closed BEDROOM inside (in a room: never traced).
  roof    A-ROOF parapet drawn as two lines 0.25 m apart round three sides of the block (the roof of the floor below):
          inner face x -3.00 .. 7.40, y -2.00 .. 3.40; the block (x 0 .. 4.40, y 0 .. 3.40) cuts into its north edge.
          Drafting gap: both inner parapet lines stop 0.10 m short of the block's wall faces; a 0.45 m end line on
          another layer (A-FRM) touches their ends, so the roof leaks to the outside through a 0.10 m strip.
          A dome circle r = 0.80 m on A-ROOF stands inside the roof.
          A filled = 10.40 x 5.40 - 4.40 x 3.40 = 56.16 - 14.96 = 41.200 m2; dome = pi x 0.80^2 = 2.011 m2;
          A net = 39.189 m2; perimeter: parapet edges 2.90 + 5.40 + 10.40 + 5.40 + 2.90 = 27.00 m, closures 2 x 0.10 m,
          building edges 3.40 + 4.40 + 3.40 = 11.20 m. Band width measured 0.25 m on every parapet edge.
          B filled = 10.90 x 5.90 - 4.40 x 3.65 = 64.31 - 16.06 = 48.250 m2; B net = 46.239 m2;
          B outer perimeter = 2 x (10.90 + 5.90) - 4.40 + (3.65 + 4.40 + 3.65) = 40.900 m. Two ROOF labels, one face.
  pool    A-ROOF D-shape: rectangle 1.00 x 2.00 m + half circle r = 1.00 m: 2.000 + pi / 2 = 3.571 m2, perimeter
          1 + 2 + 1 + pi = 7.142 m; no parallel line: B = A. Label "SWIMMING POOL" (vocabulary code POOL).
  void    A-VOID rectangle 1.50 x 1.00 m = 1.500 m2, label VOID.
  missing a BALCONY label with no line drawn round it: reported with no bounding layer and no area (never 0).
Variants: millimetres, metres, rotated 37 degrees, mirrored, rotated + mirrored in metres.

Run: python research/agents_t062/synthetic_check.py  (or pytest on this file)."""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import roof_trace as RT  # noqa: E402

C = (2200.0, 1700.0)
ROLES = {"A-WALL": "WALL", "A-ROOF": "OTHER", "A-VOID": "OTHER", "A-FRM": "OTHER"}
HAND = {"ROOF": {"A_filled_m2": 41.200, "A_net_m2": 41.200 - math.pi * 0.64, "dome_m2": math.pi * 0.64,
                 "own_layer_edge": 27.0, "closure": 0.2, "building": 11.2, "band": 0.25,
                 "B_filled_m2": 48.25, "B_net_m2": 48.25 - math.pi * 0.64, "B_perimeter": 40.9},
        "POOL": {"A_net_m2": 2.0 + math.pi / 2, "own_layer_edge": 4.0 + math.pi},
        "VOID": {"A_net_m2": 1.5, "own_layer_edge": 5.0}}


def _xf(p, deg, mirror):
    x, y = p
    if mirror:
        x = 2 * C[0] - x
    a = math.radians(deg)
    dx, dy = x - C[0], y - C[1]
    return (C[0] + dx * math.cos(a) - dy * math.sin(a), C[1] + dx * math.sin(a) + dy * math.cos(a))


def plan(path, *, scale=1.0, deg=0.0, mirror=False):
    import ezdxf
    from ezdxf.math import ConstructionArc
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4 if scale == 1.0 else 6
    for n in ("A-WALL", "A-ROOF", "A-VOID", "A-FRM", "A-TEXT", "A-FRAME", "A-TITLE"):
        doc.layers.add(n)
    msp = doc.modelspace()
    s = lambda p: tuple(v * scale for v in _xf(p, deg, mirror))     # noqa: E731

    def line(a, b, layer):
        msp.add_line(s(a), s(b), dxfattribs={"layer": layer})

    def poly(pts, layer):
        for a, b in zip(pts, pts[1:]):
            line(a, b, layer)
    box = [(-12000, -12000), (18000, -12000), (18000, 14000), (-12000, 14000)]
    msp.add_lwpolyline([(x * scale, y * scale) for x, y in box], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text("GROUND FLOOR PLAN", dxfattribs={"layer": "A-TITLE", "height": 500 * scale}).set_placement(
        (-10000 * scale, -11000 * scale))
    poly([(0, 0), (4400, 0), (4400, 3400), (0, 3400), (0, 0)], "A-WALL")
    poly([(200, 200), (4200, 200), (4200, 3200), (200, 3200), (200, 200)], "A-WALL")
    poly([(-100, 3400), (-3000, 3400), (-3000, -2000), (7400, -2000), (7400, 3400), (4500, 3400)], "A-ROOF")
    poly([(-100, 3650), (-3250, 3650), (-3250, -2250), (7650, -2250), (7650, 3650), (4500, 3650)], "A-ROOF")
    line((-100, 3300), (-100, 3750), "A-FRM")
    line((4500, 3300), (4500, 3750), "A-FRM")
    msp.add_circle(s((-1500, 0)), 800 * scale, dxfattribs={"layer": "A-ROOF"})
    poly([(10000, -1000), (11000, -1000), (11000, 1000), (10000, 1000)], "A-ROOF")
    st, mid, en = s((10000, 1000)), s((9000, 0)), s((10000, -1000))
    arc = ConstructionArc.from_3p(st, en, mid)                  # counter-clockwise from st to en ...
    am = math.degrees(math.atan2(mid[1] - arc.center.y, mid[0] - arc.center.x)) % 360
    if (am - arc.start_angle) % 360 > (arc.end_angle - arc.start_angle) % 360:   # ... unless mirrored: swap
        arc = ConstructionArc.from_3p(en, st, mid)
    msp.add_arc(arc.center, arc.radius, arc.start_angle, arc.end_angle, dxfattribs={"layer": "A-ROOF"})
    poly([(-9000, 0), (-7500, 0), (-7500, 1000), (-9000, 1000), (-9000, 0)], "A-VOID")
    for txt, p in (("BEDROOM", (2200, 1700)), ("ROOF", (2200, -1000)), ("ROOF", (6000, 1500)),
                   ("SWIMMING POOL", (10300, 0)), ("VOID", (-8250, 500)), ("BALCONY", (12500, 6000))):
        msp.add_text(txt, dxfattribs={"layer": "A-TEXT", "height": 150 * scale}).set_placement(s(p))
    doc.saveas(str(path))
    return path


VARIANTS = {"mm": {}, "metres": {"scale": 0.001}, "rot37": {"deg": 37.0}, "mirror": {"mirror": True},
            "rot37_mirror_m": {"deg": 37.0, "mirror": True, "scale": 0.001}}


def check(name, tmp):
    res, cap = RT.capture(plan(Path(tmp) / f"{name}.dxf", **VARIANTS[name]), layer_roles=ROLES)
    rep = RT.trace(res, cap)
    by = {}
    for r in rep["labels"]:
        by.setdefault(r["code"], []).append(r)
    assert sorted(by) == ["BALCONY", "POOL", "ROOF", "VOID"], sorted(by)   # BEDROOM is in a room: not traced
    assert by["BALCONY"][0]["layers_that_bound_it"] == {}      # missing data: no line round it -> no area, never 0
    assert len(by["ROOF"]) == 2
    for r in rep["labels"]:
        assert r["engine_boundary_face"] is None and r["stage"].startswith("UNBOUNDED_FACE"), r
    tol = 0.01
    for r in by["ROOF"]:
        c = r["layers_that_bound_it"]["A-ROOF"]
        h = HAND["ROOF"]
        assert c["face_without_closure_m2"] is None or c["face_without_closure_m2"] > 60, c   # leaks before closure
        assert [x["length_m"] for x in c["closures_on_face"]] == [0.1, 0.1], c["closures_on_face"]
        assert abs(c["A_filled_m2"] - h["A_filled_m2"]) < tol, c
        assert abs(c["A_net_m2"] - h["A_net_m2"]) < tol, c
        assert abs(c["shapes_inside_A_m2"] - h["dome_m2"]) < tol, c
        assert abs(c["A_perimeter_lm"]["own_layer_edge"] - h["own_layer_edge"]) < tol, c
        assert abs(c["A_perimeter_lm"]["closure"] - h["closure"]) < tol, c
        assert abs(c["A_perimeter_lm"]["building"] - h["building"]) < tol, c
        assert c["dominant_band_width_m"] == h["band"], c
        assert abs(c["B_dominant_width_outer_m2"] - h["B_net_m2"]) < tol, c
        assert abs(c["B_dominant_width_outer_perimeter_lm"] - h["B_perimeter"]) < tol, c
        assert len(c["labels_in_face"]) == 2
        assert "A-FRM" not in r["layers_that_bound_it"] or "A_net_m2" not in r["layers_that_bound_it"]["A-FRM"] or \
            r["layers_that_bound_it"]["A-FRM"]["A_net_m2"] != c["A_net_m2"]
    p = by["POOL"][0]["layers_that_bound_it"]["A-ROOF"]
    assert abs(p["A_net_m2"] - HAND["POOL"]["A_net_m2"]) < tol, p
    assert abs(p["A_perimeter_lm"]["own_layer_edge"] - HAND["POOL"]["own_layer_edge"]) < 0.02, p
    assert p["dominant_band_width_m"] is None and abs(p["B_dominant_width_outer_m2"] - p["A_net_m2"]) < tol, p
    v = by["VOID"][0]["layers_that_bound_it"]["A-VOID"]
    assert abs(v["A_net_m2"] - HAND["VOID"]["A_net_m2"]) < tol and abs(v["A_perimeter_lm"]["own_layer_edge"] - 5.0) < tol
    return {"variant": name, "roof_A_net": by["ROOF"][0]["layers_that_bound_it"]["A-ROOF"]["A_net_m2"],
            "roof_B_net": by["ROOF"][0]["layers_that_bound_it"]["A-ROOF"]["B_dominant_width_outer_m2"],
            "pool_A": p["A_net_m2"], "void_A": v["A_net_m2"]}


def test_variants(tmp_path):
    for name in VARIANTS:
        check(name, tmp_path)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        for name in VARIANTS:
            print(check(name, d))
    print("hand check: all variants pass")
