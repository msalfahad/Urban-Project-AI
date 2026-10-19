"""T-048: CONCRETE_CURVED_STRIPS_V1 - wall strips from concentric curved edges (engine.source.concrete_curved_strips).

Synthetic pools (not a client drawing). Hand truth, worked on paper from the drawn radii, never from engine output:

  D pool, 0.20 m wall: inner edge = straight side y = 0 plus a semicircle r 2.00 about (0, 0) (bulge 1);
    outer edge = straight side y = -0.20 plus a semicircle r 2.20.
    curved strip area   = pi / 2 x (2.20^2 - 2.00^2) = pi / 2 x 0.84 = 1.319469 m2
    centreline length   = pi x 2.10                                  = 6.597345 m
  Round pool, 0.30 m wall: circles r 1.50 and r 1.80 about (5, 5).
    area = pi x (1.80^2 - 1.50^2) = pi x 0.99 = 3.110177 m2; centreline = 2 pi x 1.65 = 10.367256 m
  Partial pair: inner arc r 1.00 over 0..180 deg, outer arc r 1.25 over 0..120 deg (concentric).
    strip 120 deg: area = (2 pi / 3) / 2 x (1.25^2 - 1.00^2) = pi / 3 x 0.5625 = 0.589049 m2
    inner 120..180 deg HELD unpaired: length = 1.00 x pi / 3 = 1.047198 m
  Lone arc r 3.00 over 0..90 deg: HELD unpaired, length = 3 x pi / 2 = 4.712389 m
"""

from __future__ import annotations

import math

import pytest

from engine.source import concrete_curved_strips as CS

W = (0.10, 0.45)                         # strip width range passed in, as a profile's STRIP_WIDTH_M would be

D_AREA, D_LEN = 1.319469, 6.597345
C_AREA, C_LEN = 3.110177, 10.367256


def _xf(p, rot_deg=0.0, mirror=False, scale=1.0, shift=(0.0, 0.0)):
    x, y = p[0], p[1]
    if mirror:
        x = -x
    a = math.radians(rot_deg)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (x * scale + shift[0], y * scale + shift[1])


def _poly(pts, closed=True, **kw):
    mirror = kw.get("mirror", False)
    out = []
    for p in pts:
        x, y = _xf(p, **kw)
        b = p[2]
        out.append((x, y, -b if mirror else b))     # a mirror reverses the turning direction
    return {"type": "LWPOLYLINE", "points": out, "closed": closed}


def d_pool(**kw):
    inner = _poly([(-2.0, 0.0, 0.0), (2.0, 0.0, 1.0)], **kw)
    outer = _poly([(-2.2, -0.2, 0.0), (2.2, -0.2, 0.0), (2.2, 0.0, 1.0), (-2.2, 0.0, 0.0)], **kw)
    inner.update(id="d_in", layer="POOL WALL")
    outer.update(id="d_out", layer="POOL WALL")
    return [inner, outer]


def round_pool(scale=1.0, rot_deg=0.0, mirror=False):
    c = _xf((5.0, 5.0), rot_deg=rot_deg, mirror=mirror, scale=scale)
    return [{"type": "CIRCLE", "id": "c_in", "layer": "S-WALL", "c": c, "r": 1.5 * scale},
            {"type": "CIRCLE", "id": "c_out", "layer": "S-WALL", "c": c, "r": 1.8 * scale}]


def _approx(v, ref, tol=0.001):
    return abs(v - ref) <= tol


# ------------------------------------------------------------------ D pool, round pool, transforms, units
@pytest.mark.parametrize("rot", [0.0, 37.0])
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("unit", ["m", "mm"])
def test_d_pool_curved_strip(rot, mirror, unit):
    scale, u = (1000.0, 0.001) if unit == "mm" else (1.0, 1.0)
    res = CS.curved_strips(d_pool(rot_deg=rot, mirror=mirror, scale=scale), u, W)
    assert len(res["strips"]) == 1 and not res["held"] and not res["unsupported"]
    s = res["strips"][0]
    assert _approx(s["area_m2"], D_AREA) and _approx(s["strip_length_m"], D_LEN)
    assert _approx(s["strip_width_m"], 0.20) and _approx(s["sweep_deg"], 180.0, 1e-6)
    assert res["straight_segments"] == 1 + 3          # left to the straight-line builder, counted, not measured here
    assert s["edges"] == ["d_in", "d_out"]


@pytest.mark.parametrize("rot", [0.0, 37.0])
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("unit", ["m", "mm"])
def test_round_pool_full_ring(rot, mirror, unit):
    scale, u = (1000.0, 0.001) if unit == "mm" else (1.0, 1.0)
    res = CS.curved_strips(round_pool(scale, rot, mirror), u, W)
    assert len(res["strips"]) == 1 and not res["held"]
    s = res["strips"][0]
    assert _approx(s["area_m2"], C_AREA) and _approx(s["strip_length_m"], C_LEN)
    assert _approx(s["strip_width_m"], 0.30) and _approx(s["sweep_deg"], 360.0, 1e-6)


def test_both_pools_together_and_extrusion_mirror():
    # the same D pool written in a -Z OCS (a mirrored insert): points as stored, world = (-x, y), turning reversed
    ocs = d_pool()
    for c in ocs:
        c["extrusion"] = (0.0, 0.0, -1.0)
    res = CS.curved_strips(ocs + round_pool(), 1.0, W)
    assert len(res["strips"]) == 2 and not res["held"]
    assert _approx(res["totals"]["strip_area_m2"], D_AREA + C_AREA)
    assert _approx(res["totals"]["strip_length_m"], D_LEN + C_LEN)
    d = min(res["strips"], key=lambda s: s["area_m2"])
    assert _approx(d["start_deg"], 0.0, 1e-6) and _approx(d["sweep_deg"], 180.0, 1e-6)  # mirror of the top half


def test_mirror_keeps_the_half_on_the_drawn_side():
    """a mirror about y must keep the semicircle above the straight side (sweep 0..180), not flip it below."""
    s = CS.curved_strips(d_pool(mirror=True), 1.0, W)["strips"][0]
    assert _approx(s["start_deg"], 0.0, 1e-6) and _approx(s["sweep_deg"], 180.0, 1e-6)


# ------------------------------------------------------------------ partial, unpaired, ambiguous
def test_partial_pair_holds_the_uncovered_part():
    arcs = [{"type": "ARC", "id": "in", "layer": "W", "c": (1.0, 1.0), "r": 1.0, "start": 0.0, "end": 180.0},
            {"type": "ARC", "id": "out", "layer": "W", "c": (1.0, 1.0), "r": 1.25, "start": 0.0, "end": 120.0}]
    res = CS.curved_strips(arcs, 1.0, W)
    assert len(res["strips"]) == 1
    assert _approx(res["strips"][0]["area_m2"], 0.589049)
    assert len(res["held"]) == 1
    h = res["held"][0]
    assert h["reason"] == "CURVED_STRIP_UNPAIRED" and h["id"] == "in"
    assert _approx(h["length_m"], 1.047198) and _approx(h["start_deg"], 120.0, 1e-6)


def test_lone_arc_is_held_never_dropped_or_zero():
    res = CS.curved_strips([{"type": "ARC", "id": "lone", "layer": "W", "c": (0, 0), "r": 3.0,
                             "start": 0.0, "end": 90.0}], 1.0, W)
    assert res["strips"] == [] and len(res["held"]) == 1
    h = res["held"][0]
    assert h["status"] == "HELD" and h["reason"] == "CURVED_STRIP_UNPAIRED"
    assert _approx(h["length_m"], 4.712389)


def test_lone_arc_in_mm_and_wider_than_strip_is_held():
    """two concentric arcs 0.60 m apart (wider than any wall width passed in) are not a strip: both HELD."""
    arcs = [{"type": "ARC", "id": "a", "layer": "W", "c": (0, 0), "r": 2000.0, "start": 10.0, "end": 100.0},
            {"type": "ARC", "id": "b", "layer": "W", "c": (0, 0), "r": 2600.0, "start": 10.0, "end": 100.0}]
    res = CS.curved_strips(arcs, 0.001, W)
    assert res["strips"] == [] and {h["id"] for h in res["held"]} == {"a", "b"}
    assert _approx(res["held"][0]["length_m"] + res["held"][1]["length_m"], (2.0 + 2.6) * math.pi / 2)


def test_three_concentric_radii_are_ambiguous_not_guessed():
    circles = [{"type": "CIRCLE", "id": f"r{r}", "layer": "W", "c": (0, 0), "r": r} for r in (1.0, 1.2, 1.4)]
    res = CS.curved_strips(circles, 1.0, W)
    assert res["strips"] == []
    assert sorted(h["id"] for h in res["held"]) == ["r1.0", "r1.2", "r1.4"]
    assert {h["reason"] for h in res["held"]} == {"CURVED_STRIP_AMBIGUOUS"}


def test_offset_centre_is_not_a_pair():
    arcs = [{"type": "CIRCLE", "id": "a", "layer": "W", "c": (0, 0), "r": 1.0},
            {"type": "CIRCLE", "id": "b", "layer": "W", "c": (0.01, 0), "r": 1.2}]       # 10 mm off centre
    res = CS.curved_strips(arcs, 1.0, W)
    assert res["strips"] == [] and len(res["held"]) == 2


def test_repeated_arc_on_one_circle_is_covered_once():
    arcs = [{"type": "CIRCLE", "id": "in", "layer": "W", "c": (0, 0), "r": 1.5},
            {"type": "CIRCLE", "id": "in_dup", "layer": "W", "c": (0, 0), "r": 1.5},
            {"type": "CIRCLE", "id": "out", "layer": "W", "c": (0, 0), "r": 1.8}]
    res = CS.curved_strips(arcs, 1.0, W)
    assert len(res["strips"]) == 1 and _approx(res["totals"]["strip_area_m2"], C_AREA)


# ------------------------------------------------------------------ input forms
def test_three_point_intake_arc_both_directions():
    ccw = {"type": "ARC", "id": "ccw", "c": (0, 0), "r": 1.0, "s": (1, 0), "m": (0, 1), "e": (-1, 0)}
    cw = {"type": "ARC", "id": "cw", "c": (0, 0), "r": 1.25, "s": (-1.25, 0), "m": (0, 1.25), "e": (1.25, 0)}
    res = CS.curved_strips([ccw, cw], 1.0, W)
    assert len(res["strips"]) == 1 and not res["held"]
    assert _approx(res["strips"][0]["area_m2"], math.pi / 2 * (1.25 ** 2 - 1.0))


def test_bulge_arc_quarter():
    a = CS.bulge_arc((1.0, 0.0), (0.0, 1.0), math.tan(math.radians(90) / 4))
    assert _approx(a["r"], 1.0, 1e-9) and math.dist(a["c"], (0, 0)) < 1e-9
    assert _approx(a["start"], 0.0, 1e-9) and _approx(a["sweep"], 90.0, 1e-9)
    b = CS.bulge_arc((0.0, 1.0), (1.0, 0.0), -math.tan(math.radians(90) / 4))     # same arc, drawn clockwise
    assert _approx(b["start"], 0.0, 1e-9) and _approx(b["sweep"], 90.0, 1e-9)


# ------------------------------------------------------------------ missing data never becomes 0
def test_missing_unit_is_unsupported_not_zero():
    res = CS.curved_strips(round_pool(), None, W)
    assert res["strips"] == [] and res["totals"] is None
    assert len(res["unsupported"]) == 2 and {u["reason"] for u in res["unsupported"]} == {"UNIT_UNKNOWN"}


def test_missing_strip_width_is_unsupported():
    res = CS.curved_strips(round_pool(), 1.0, None)
    assert res["totals"] is None and {u["reason"] for u in res["unsupported"]} == {"STRIP_WIDTH_UNKNOWN"}


def test_bad_curve_is_unsupported_and_others_still_measured():
    bad = [{"type": "ARC", "id": "no_r", "c": (0, 0), "r": None, "start": 0, "end": 90},
           {"type": "LWPOLYLINE", "id": "bad_v", "points": [(0, 0, 0.5), (None, 1, 0)]},
           {"type": "SPLINE", "id": "spl"}]
    res = CS.curved_strips(bad + round_pool(), 1.0, W)
    assert len(res["strips"]) == 1 and _approx(res["totals"]["strip_area_m2"], C_AREA)
    assert sorted(u["id"] for u in res["unsupported"]) == ["bad_v", "no_r", "spl"]
    assert {u["status"] for u in res["unsupported"]} == {"UNSUPPORTED"}


def test_every_curved_edge_reported_once():
    """conservation: the sweep of every input curve = sweep in strips (per edge) + sweep held."""
    curves = d_pool(rot_deg=37.0) + round_pool() + [
        {"type": "ARC", "id": "in", "layer": "W", "c": (20.0, 0.0), "r": 1.0, "start": 0.0, "end": 180.0},
        {"type": "ARC", "id": "out", "layer": "W", "c": (20.0, 0.0), "r": 1.25, "start": 0.0, "end": 120.0}]
    res = CS.curved_strips(curves, 1.0, W)
    drawn = 180.0 * 2 + 360.0 * 2 + 180.0 + 120.0
    in_strips = 2 * sum(s["sweep_deg"] for s in res["strips"])
    held = sum(h["sweep_deg"] for h in res["held"])
    assert _approx(in_strips + held, drawn, 1e-6)
